"""Bounded, shell-free execution of trusted local workloads."""

from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from .errors import AionError
from .models import Limits, ProcessResult
from .controls import ExecutionControls


def capabilities() -> dict:
    from .platform_support import platform_capabilities
    support = platform_capabilities()
    posix = support['posix_supervisor']
    return {
        "wall_timeout": True,
        "output_limit": True,
        "address_space_limit": support['address_space_limit'],
        "resident_memory_watchdog": support['resident_memory_watchdog'],
        "cpu_time_limit": posix,
        "peak_rss": posix,
        "timing": "fork/exec through wait4" if posix else "process launch through exit",
        "platform_capabilities": support,
    }


def _terminate_tree(process: subprocess.Popen):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        # No shell; /T also terminates descendants of this local process.
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=5, check=False)
        if process.poll() is None:
            process.kill()
    process.wait(timeout=5)


def run_process(command: list[str], limits: Limits | None = None,
                cwd: Path | None = None, *, env_overrides: dict[str, str] | None = None,
                controls: ExecutionControls | None = None) -> ProcessResult:
    from .budget import ACTIVE
    budget = ACTIVE.get()
    item = None
    if budget is not None:
        item, limits = budget.charge(command, limits)
    try:
        result = _run_process(command, limits, cwd, env_overrides=env_overrides, controls=controls)
        if item is not None:
            item.update(status="completed", result=result.to_dict())
        return result
    except BaseException as exc:
        if item is not None:
            item.update(status="failed", error={"type": type(exc).__name__, "message": str(exc)})
        raise


def _run_process(command: list[str], limits: Limits | None = None,
                cwd: Path | None = None, *, env_overrides: dict[str, str] | None = None,
                controls: ExecutionControls | None = None) -> ProcessResult:
    limits = limits or Limits()
    memory_reader = None
    if sys.platform == 'darwin' and limits.memory_mb is not None:
        from .darwin_memory import DarwinMemoryReader
        memory_reader = DarwinMemoryReader()  # Refuse before launching if protection is unavailable.
    if controls is not None:
        controls.validate()
    command = [str(part) for part in command]
    if not command:
        raise AionError("Cannot run an empty command.")
    with tempfile.TemporaryDirectory(prefix="aion-process-") as directory:
        root = Path(directory)
        stdout_path, stderr_path = root / "stdout", root / "stderr"
        result_path = root / "result.json"
        invocation = command
        if os.name == "posix":
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps({"command": command, "limits": asdict(limits),
                                             "memory_policy": 'resident-watchdog' if memory_reader else None,
                                             "controls": controls.to_dict() if controls else None}),
                                 encoding="utf-8")
            invocation = [sys.executable, str(Path(__file__).with_name("_worker.py")),
                          str(spec_path), str(result_path)]
        env = os.environ.copy()
        env.update({"LC_ALL": "C", "LANG": "C", "OMP_NUM_THREADS": "1"})
        env.update(env_overrides or {})
        timed_out = output_limited = memory_limited = False
        memory_observed = 0
        started = time.perf_counter()
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            try:
                process = subprocess.Popen(
                    invocation, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, start_new_session=os.name == "posix",
                )
            except OSError as exc:
                raise AionError(f"Cannot execute {command[0]}: {exc}") from exc
            try:
                while process.poll() is None:
                    if memory_reader is not None:
                        try:
                            memory_observed = max(memory_observed, memory_reader.group_resident_bytes(process.pid))
                        except AionError:
                            if process.poll() is not None:
                                break
                            raise
                        if memory_observed > limits.memory_mb * 1024 * 1024:
                            memory_limited = True
                            _terminate_tree(process)
                            break
                    if time.perf_counter() - started > limits.timeout_seconds:
                        timed_out = True
                        _terminate_tree(process)
                        break
                    if any(path.stat().st_size >= limits.output_bytes
                           for path in (stdout_path, stderr_path)):
                        output_limited = True
                        _terminate_tree(process)
                        break
                    # Windows wait returns as soon as the process exits, unlike
                    # sleep/poll timing, which quantizes fast workloads.
                    try:
                        process.wait(timeout=0.005)
                    except subprocess.TimeoutExpired:
                        pass
            except BaseException:
                _terminate_tree(process)
                raise
        elapsed = time.perf_counter() - started
        metadata = {}
        if result_path.exists():
            try:
                metadata = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                # A killed or failed supervisor must remain a process failure,
                # never turn a bounded workload into an orchestration traceback.
                metadata = {}
        output_limited |= any(path.stat().st_size >= limits.output_bytes
                              for path in (stdout_path, stderr_path))
        # A crashed supervisor is a failure even if a stale child status exists.
        code = metadata.get("returncode", process.returncode) if process.returncode == 0 else process.returncode
        if not metadata and os.name == "posix" and code == 0:
            code = 125
        with stdout_path.open("rb") as stdout, stderr_path.open("rb") as stderr:
            captured_stdout = stdout.read(limits.output_bytes).decode("utf-8", errors="replace")
            captured_stderr = stderr.read(limits.output_bytes).decode("utf-8", errors="replace")
        return ProcessResult(
            command, code, metadata.get("duration_seconds", elapsed),
            metadata.get("peak_rss_bytes"),
            captured_stdout, captured_stderr,
            timed_out, output_limited,
            metadata.get("affinity"), metadata.get("workload_pid"),
            memory_limited,
            ({'memory_policy': 'sampled aggregate process-group resident memory',
              'limit_bytes': limits.memory_mb * 1024 * 1024, 'observed_peak_bytes': memory_observed,
              'poll_interval_seconds': .005, 'allocation_ceiling': False,
              'caveat': 'Includes supervisor/descendants; transient peaks between observations can be missed; not a security sandbox.'}
             if memory_reader else {'memory_policy': 'explicitly uncapped for this invocation'} if sys.platform == 'darwin' else None),
        )
