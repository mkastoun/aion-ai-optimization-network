from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from . import __version__
from .benchmarks import Benchmark
from .engine import candidate_assessment
from .errors import AionError
from .models import CompilerInfo
from .optimization import validate_flags
from .storage import atomic_json, read_json


def _digest(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False).encode()).hexdigest()


class PresetRegistry:
    def __init__(self, root: Path):
        self.root = root / "presets"

    def path(self, name: str) -> Path:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name):
            raise AionError("Preset names must be 1..64 lowercase letters, digits, or hyphens.")
        return self.root / f"{name}.json"

    def list_names(self) -> list[str]:
        return sorted(path.stem for path in self.root.glob("*.json"))

    def register(self, name: str, candidate_name: str, discovery: dict, confirmation: dict) -> Path:
        if any(r.get('research_panel') or r.get('declaration_sha256') for r in (discovery,confirmation)):
            raise AionError('Research hypotheses cannot create reusable compiler presets.')
        if any(run.get("evidence_kind", "primary-timing") != "primary-timing" for run in (discovery,confirmation)):
            raise AionError("Diagnostic profiling/sanitizer evidence cannot create presets.")
        path = self.path(name)
        if path.exists():
            raise AionError(f"Preset '{name}' already exists; choose a new versioned name.")
        if discovery.get("methodology_version", 1) >= 3 or confirmation.get("methodology_version", 1) >= 3:
            from .reproducibility import require_confirmation_compatible
            require_confirmation_compatible(discovery, confirmation)
        first = candidate_assessment(discovery, candidate_name)
        second = candidate_assessment(confirmation, candidate_name)
        if not first["eligible"] or not second["eligible"]:
            raise AionError("Preset rejected: discovery and independent confirmation must both pass.")
        if (discovery["run_id"] == confirmation["run_id"]
                or discovery["settings"]["seed"] == confirmation["settings"]["seed"]):
            raise AionError("Confirmation requires a fresh experiment and different scheduling seed.")
        if not set(first["improvements"]) & set(second["improvements"]):
            raise AionError("No workload improved in both discovery and confirmation.")
        if (discovery["compiler"] != confirmation["compiler"]
                or discovery["environment"] != confirmation["environment"]
                or discovery["limits"] != confirmation["limits"]):
            raise AionError("Confirmation compiler, environment, and resource limits must match discovery.")
        hashes = {key: value["fingerprint"] for key, value in discovery["benchmarks"].items()}
        if hashes != {key: value["fingerprint"] for key, value in confirmation["benchmarks"].items()}:
            raise AionError("Confirmation must cover the same workload sources and input cases.")
        if discovery.get("methodology_version", 1) != confirmation.get("methodology_version", 1):
            raise AionError("Confirmation must use the same measurement methodology.")
        if discovery.get("methodology_version", 1) >= 2:
            for workload, benchmark in discovery["benchmarks"].items():
                first_case = benchmark["measurement_case"]
                second_case = confirmation["benchmarks"][workload]["measurement_case"]
                if (first_case["args"][1] == second_case["args"][1]
                        or first_case["args"][::2] != second_case["args"][::2]):
                    raise AionError("Confirmation requires different input seeds and equal work per batch.")
        configs = []
        for run in (discovery, confirmation):
            config = next((c for c in run["configurations"] if c["name"] == candidate_name), None)
            if config is None:
                raise AionError("Missing candidate configuration.")
            if config.get("build_mode", "standard") != "standard":
                raise AionError("Workload-specific PGO profiles cannot be registered as reusable flag-only presets.")
            configs.append(validate_flags(config["flags"]))
        if configs[0] != configs[1]:
            raise AionError("Confirmation flags differ from discovery.")
        machine = discovery["environment"]
        data = {
            "schema_version": 1, "preset_version": 1, "aion_version": __version__, "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(), "flags": list(configs[0]),
            "compiler": discovery["compiler"],
            "hardware_requirements": {key: machine[key] for key in ("system", "machine", "cpu")},
            "required_cpu_flags": [], "benchmarks": hashes,
            "evidence": [{"run_id": run["run_id"], "sha256": _digest(run),
                          "candidate": candidate_name} for run in (discovery, confirmation)],
            "verification": {"independent_confirmation": True,
                             "methodology_version": discovery.get("methodology_version", 1),
                             "improved_workloads": sorted(set(first["improvements"]) & set(second["improvements"])),
                             "scope": "only the listed workloads, compiler, and machine"},
        }
        atomic_json(path, data)
        return path

    def load(self, name: str) -> dict:
        data = read_json(self.path(name))
        try:
            validate_flags(data["flags"])
            if (data["name"] != name or data["preset_version"] != 1
                    or not data["verification"]["independent_confirmation"]
                    or not data["benchmarks"] or len(data["evidence"]) != 2):
                raise ValueError("invalid preset metadata")
            for key in ("family", "version", "major", "target"):
                if key not in data["compiler"]:
                    raise ValueError("missing compiler compatibility")
            for key in ("system", "machine", "cpu"):
                if not isinstance(data["hardware_requirements"][key], str):
                    raise ValueError("invalid hardware requirement")
            if not isinstance(data["required_cpu_flags"], list):
                raise ValueError("invalid CPU requirements")
            if any(not isinstance(flag, str) for flag in data["required_cpu_flags"]):
                raise ValueError("invalid CPU feature")
        except (KeyError, TypeError, ValueError) as exc:
            raise AionError(f"Invalid local preset '{name}': {exc}") from exc
        return data

    def check_compatibility(self, preset: dict, compiler: CompilerInfo,
                            environment: dict, benchmarks: list[Benchmark]):
        current = asdict(compiler)
        for key in ("family", "version", "major", "target"):
            if preset["compiler"][key] != current[key]:
                raise AionError(f"Preset compiler mismatch: {key}. Run a new optimization experiment.")
        for key, value in preset["hardware_requirements"].items():
            if environment.get(key) != value:
                raise AionError(f"Preset hardware mismatch: {key}.")
        if not set(preset["required_cpu_flags"]).issubset(environment["cpu_flags"]):
            raise AionError("Preset requires unavailable CPU features.")
        if preset["benchmarks"] != {b.name: b.fingerprint for b in benchmarks}:
            raise AionError("Preset workload fingerprint mismatch; re-discover and verify the preset.")
