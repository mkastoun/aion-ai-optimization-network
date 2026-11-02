from pathlib import Path
import json
import math

from .benchmarks import Benchmark
from .models import Limits, ProcessResult
from .process import run_process
from .controls import ExecutionControls


def check_output(result: ProcessResult, expected: str) -> dict:
    reasons = []
    if result.timed_out:
        reasons.append("wall timeout exceeded")
    if result.output_limited:
        reasons.append("output limit exceeded")
    if result.memory_limited:
        reasons.append('memory limit exceeded')
    if result.returncode != 0:
        reasons.append(f"process exited with status {result.returncode}")
    if result.stdout.strip() != expected:
        reasons.append("output differs from independent reference")
    if result.affinity and result.affinity.get("requested_cpus") is not None and not result.affinity.get("verified_before_exec"):
        reasons.append("requested workload affinity was not verified")
    return {"passed": not reasons, "reasons": reasons, "expected": expected,
            "process": result.to_dict()}


def verify_binary(binary: Path, benchmark: Benchmark, limits: Limits, *, controls: ExecutionControls | None = None) -> dict:
    checks = []
    for case in benchmark.cases:
        result = run_process([str(binary), *case["args"]], limits, **({"controls": controls} if controls else {}))
        checks.append({"case": case["name"], **check_output(result, case["expected"])})
    return {"passed": all(check["passed"] for check in checks), "checks": checks,
            "scope": "built-in deterministic cases; not a general equivalence proof"}


def measure_binary(binary: Path, case: dict, batches: int, limits: Limits, *, controls: ExecutionControls | None = None,
                   control_delay_ns: int = 0, env_overrides: dict[str, str] | None = None) -> dict:
    command = [str(binary), *case["args"], "--measure", str(batches)]
    if control_delay_ns:
        if not 0 < control_delay_ns <= 250000000:
            raise ValueError("Control delay must be 1..250000000 nanoseconds")
        command.extend(["--control-delay-ns", str(control_delay_ns)])
    result = run_process(command, limits,
                         **({"env_overrides": env_overrides} if env_overrides else {}),
                         **({"controls": controls} if controls else {}))
    expected = str((int(case["expected"]) * batches) & ((1 << 64) - 1))
    record = {"passed": False, "reasons": [], "expected": expected,
              "process": result.to_dict(), "measurement": None}
    try:
        data = json.loads(result.stdout)
        if (not isinstance(data, dict) or data.get("protocol") != "aion-compute-v1"
                or type(data.get("batches")) is not int or data["batches"] != batches
                or type(data.get("compute_ns")) is not int or data["compute_ns"] <= 0
                or type(data.get("setup_ns")) is not int or data["setup_ns"] < 0
                or data.get("checksum") != expected):
            raise ValueError("invalid timing protocol or checksum")
        seconds = data["compute_ns"] / 1e9
        setup = data["setup_ns"] / 1e9
        # A trusted workload still must not report impossible internal timings.
        if not math.isfinite(seconds) or seconds + setup > result.duration_seconds + 0.01:
            raise ValueError("internal timing exceeds process wall time")
        if data.get("control_delay_ns", 0) != control_delay_ns:
            raise ValueError("unexpected or missing negative-control delay")
        if control_delay_ns and (type(data.get("injected_control_ns")) is not int
                or not control_delay_ns*batches <= data["injected_control_ns"] <= data["compute_ns"]):
            raise ValueError("negative-control work is not reflected in compute time")
        record["measurement"] = {**data, "compute_seconds": seconds,
                                 "setup_seconds": setup, "seconds_per_batch": seconds / batches}
        if controls is not None:
            requested = controls.to_dict()["requested_cpus"]
            observed = data.get("affinity_start")
            after = data.get("affinity_end")
            worker = result.affinity or {}
            verified = requested is not None and worker.get("verified_before_exec") is True
            method = "child-before-exec; Linux exec preserves affinity" if verified else "not-requested"
            if observed is not None and after is not None:
                if requested is not None and (observed != requested or after != requested
                        or data.get("pid") != result.workload_pid):
                    raise ValueError("actual executable affinity or PID differs from the requested control")
                method = "actual executable sched_getaffinity before/after compute"
            if requested is not None and not verified:
                raise ValueError("workload child affinity was not verified")
            record["execution_controls"] = {"requested_cpus": requested,
                "effective_cpus": observed if observed is not None else worker.get("effective_cpus"),
                "verified": verified if requested is not None else None, "method": method,
                "workload_pid": result.workload_pid, "cpu_start": data.get("cpu_start"), "cpu_end": data.get("cpu_end")}
    except (ValueError, TypeError, OverflowError) as exc:
        record["reasons"].append(f"invalid workload measurement: {exc}")
    if not result.ok:
        record["reasons"].append("workload process failed, timed out, or exceeded output/memory bounds")
    record["passed"] = not record["reasons"]
    return record
