"""Single-threaded POSIX supervisor; never imported into the CLI process.

wait4 reports one child's peak RSS, rather than cumulative RUSAGE_CHILDREN.
Timing starts here, excluding the Python supervisor's interpreter startup.
"""

import json
import math
import os
from pathlib import Path
import resource
import sys
import time


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    started = time.perf_counter_ns()
    control_path = Path(sys.argv[2]).with_suffix(".controls.json")
    pid = os.fork()
    if pid == 0:
        try:
            requested = (spec.get("controls") or {}).get("requested_cpus")
            if requested is not None:
                if not sys.platform.startswith('linux'):
                    raise RuntimeError('CPU affinity is unsupported on this OS')
                os.sched_setaffinity(0, requested)
            effective = sorted(os.sched_getaffinity(0)) if sys.platform.startswith('linux') and hasattr(os, "sched_getaffinity") else None
            control_path.write_text(json.dumps({"requested_cpus": requested, "effective_cpus": effective,
                                               "verified_before_exec": effective == requested if requested is not None else None,
                                               "method": "sched_getaffinity in actual child PID immediately before exec"}), encoding="utf-8")
            if requested is not None and effective != requested:
                raise RuntimeError("effective CPU affinity differs from requested CPUs")
            limits = spec["limits"]
            if limits["memory_mb"] is not None:
                if sys.platform == 'darwin':
                    if spec.get('memory_policy') != 'resident-watchdog':
                        raise RuntimeError('macOS requires the parent resident-memory watchdog')
                else:
                    resource.setrlimit(resource.RLIMIT_AS, (limits["memory_mb"] * 1024 * 1024,) * 2)
            for key, value in (
                (resource.RLIMIT_CPU, max(1, math.ceil(limits["timeout_seconds"]))),
                (resource.RLIMIT_FSIZE, limits["output_bytes"]),
                (resource.RLIMIT_CORE, 0),
            ):
                resource.setrlimit(key, (value, value))
            os.execvpe(spec["command"][0], spec["command"], os.environ)
        except BaseException as exc:
            print(f"aion child: {exc}", file=sys.stderr, flush=True)
            os._exit(127)
    _, status, usage = os.wait4(pid, 0)
    elapsed = (time.perf_counter_ns() - started) / 1e9
    rss = usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    affinity = json.loads(control_path.read_text(encoding="utf-8")) if control_path.exists() else None
    result_path = Path(sys.argv[2])
    temporary = result_path.with_suffix(".tmp")
    temporary.write_text(json.dumps({
        "returncode": os.waitstatus_to_exitcode(status),
        "duration_seconds": elapsed,
        "peak_rss_bytes": rss,
        "affinity": affinity, "workload_pid": pid,
    }), encoding="utf-8")
    temporary.replace(result_path)


if __name__ == "__main__":
    main()
