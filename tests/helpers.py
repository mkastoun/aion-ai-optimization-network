from copy import deepcopy
from dataclasses import asdict
import hashlib
from pathlib import Path

from aion.models import CompilerInfo, ProcessResult

INFO = CompilerInfo("/local/clang++", "clang version 18.1.0", 18, "x86_64-linux-gnu")


def process(stdout="123\n", seconds=0.1, code=0):
    return ProcessResult(["test-only"], code, seconds, 10_000_000, stdout, "")


def evidence(run_id="discovery", seed=1):
    """Synthetic test data only; never saved as real benchmark evidence."""
    def entry(duration):
        return {"status": "measured", "verification": {"passed": True},
                "samples": [{"passed": True, "process": process(seconds=duration).to_dict()}
                            for _ in range(7)],
                "warmups": [{"passed": True}], "summary": None, "comparison": None}
    return {
        "schema_version": 1, "run_id": run_id, "status": "completed",
        "compiler": asdict(INFO), "environment": {
            "system": "Linux", "machine": "x86_64", "cpu": "test-only", "cpu_flags": []},
        "settings": {"iterations": 7, "warmups": 1, "seed": seed,
                     "noise_threshold": .05, "min_improvement": .02, "max_regression": .05},
        "limits": {"memory_mb": 1024},
        "configurations": [{"name": "baseline", "flags": ["-O3"]},
                           {"name": "o2", "flags": ["-O2"]}],
        "benchmarks": {"array": {"fingerprint": hashlib.sha256(b"test-only").hexdigest(),
                                    "configurations": {"baseline": entry(.1), "o2": entry(.08)}}},
    }


def confirmation(discovery):
    result = deepcopy(discovery)
    result["run_id"] = "confirmation"
    result["settings"]["seed"] += 1
    return result
