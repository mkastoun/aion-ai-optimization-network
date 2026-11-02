from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from pathlib import Path
import random
import tempfile
import shutil
from typing import Callable
import uuid
from contextlib import contextmanager

from . import __version__
from .benchmarks import Benchmark
from .compiler import CompilerAdapter
from .environment import machine_environment
from .errors import AionError
from .models import Candidate, Limits
from .optimization import BASELINE, validate_candidate
from .calibration import calibrate
from .process import run_process
from .statistics import compare, paired_comparison, summarize
from .verification import check_output, measure_binary, verify_binary
from .controls import ExecutionControls
from .host import collect_host_diagnostics
from .provenance import file_sha256
from .sessions import new_session


@contextmanager
def _preserve_failure(result: dict, on_failure):
    try:
        yield
    except BaseException as exc:
        result["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
        if on_failure is not None:
            on_failure(result)
        raise


@dataclass(frozen=True)
class ExperimentSettings:
    iterations: int = 11
    warmups: int = 2
    seed: int = 1729
    noise_threshold: float = 0.05
    min_improvement: float = 0.02
    max_regression: float = 0.05
    calibrate: bool = True
    target_min_seconds: float = .250
    target_max_seconds: float = .500
    bootstrap_resamples: int = 10000
    confidence: float = .95

    def __post_init__(self):
        if not 1 <= self.iterations <= 1000 or not 0 <= self.warmups <= 100:
            raise AionError("Iterations must be 1..1000 and warmups 0..100.")
        if any(not math.isfinite(value) or not 0 < value < 1 for value in
               (self.noise_threshold, self.min_improvement, self.max_regression)):
            raise AionError("Noise, improvement, and regression thresholds must be between 0 and 1.")
        if (not 0 < self.target_min_seconds < self.target_max_seconds <= 5
                or not 100 <= self.bootstrap_resamples <= 100000 or not .5 < self.confidence < 1):
            raise AionError("Invalid calibration or uncertainty settings.")


def _records(benchmark: dict, name: str, phase: str = "samples") -> tuple[list[dict], list[dict]]:
    entries = benchmark["configurations"]
    candidate = entries.get(name, {}).get(phase, [])
    baseline = entries.get("baseline", {}).get(phase, [])
    if any("pair_candidate" in r for r in baseline):
        baseline = [r for r in baseline if r.get("pair_candidate") == name]
    return baseline, candidate


def _summary(records: list[dict], settings: dict, timed: bool) -> dict:
    if timed:
        return summarize([r["measurement"]["seconds_per_batch"] for r in records], settings["noise_threshold"],
                         physical_seconds=[r["measurement"]["compute_seconds"] for r in records],
                         minimum_seconds=settings["target_min_seconds"])
    return summarize([r["process"]["duration_seconds"] for r in records], settings["noise_threshold"])


def comparison_for(run: dict, workload: str, name: str) -> dict:
    benchmark, settings = run["benchmarks"][workload], run["settings"]
    baseline, candidate = _records(benchmark, name)
    floor, regression = max(.02, settings["min_improvement"]), min(.05, settings["max_regression"])
    if benchmark.get("measurement_protocol") == "aion-compute-v1":
        if ([r.get("pair_id") for r in baseline] != [r.get("pair_id") for r in candidate]
                or len({r.get("pair_id") for r in baseline}) != len(baseline)):
            raise AionError("Missing, duplicated, or mismatched measurement pairs.")
        return paired_comparison(
            [r["measurement"]["seconds_per_batch"] for r in baseline],
            [r["measurement"]["seconds_per_batch"] for r in candidate],
            baseline_physical=[r["measurement"]["compute_seconds"] for r in baseline],
            candidate_physical=[r["measurement"]["compute_seconds"] for r in candidate],
            noise_threshold=min(.05, settings["noise_threshold"]), min_improvement=floor, max_regression=regression,
            minimum_seconds=max(.25, settings["target_min_seconds"]), confidence=max(.95, settings["confidence"]),
            comparisons=run["comparison_family_size"], resamples=settings["bootstrap_resamples"],
            seed=f"{settings['seed']}:{workload}:{name}",
        )
    strict_settings = {**settings, "noise_threshold": min(.05, settings["noise_threshold"])}
    return compare(_summary(baseline, strict_settings, False), _summary(candidate, strict_settings, False),
                   min_improvement=floor, max_regression=regression)


def run_experiment(adapter: CompilerAdapter, benchmarks: list[Benchmark],
                   candidates: list[Candidate], settings: ExperimentSettings | None = None,
                   limits: Limits | None = None, *, purpose: str = "experiment",
                   progress: Callable[[str], None] | None = None,
                   controls: ExecutionControls | None = None,
                   on_failure: Callable[[dict], None] | None = None,
                   session: dict | None = None, research_baseline: Candidate | None = None,
                   research_family_size: int | None = None) -> dict:
    settings, limits = settings or ExperimentSettings(), limits or Limits()
    host = collect_host_diagnostics()
    if session and (session.get("host_fingerprint") != host["host_fingerprint"] or session.get("boot_id_hash") != host.get("boot_id_hash")):
        raise AionError("Observation session no longer matches the current host/boot.")
    if controls is not None:
        controls.validate()
    control_kwargs = {"controls": controls} if controls is not None else {}
    research = getattr(adapter, "research_only", False)
    if (research_baseline is not None or research_family_size is not None) and not research:
        raise AionError("Reference overrides are restricted to the trusted research adapter.")
    if research_baseline is not None and research_baseline.name != "baseline":
        raise AionError("The research reference must be named baseline.")
    configurations = [research_baseline or BASELINE, *candidates]
    if len({c.name for c in configurations}) != len(configurations):
        raise AionError("Configuration names must be unique; 'baseline' is reserved.")
    for candidate in configurations:
        validate_candidate(candidate)
    emit = progress or (lambda message: None)
    result = {
        "schema_version": 1, "aion_version": __version__,
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:10],
        "created_at": datetime.now(timezone.utc).isoformat(), "purpose": purpose,
        "environment": machine_environment(), "compiler": asdict(adapter.info),
        "settings": asdict(settings), "limits": asdict(limits),
        "methodology_version": 4 if settings.calibrate else 1,
        "evidence_kind": "research-timing" if research else "primary-timing", "session": session or new_session(host),
        "execution_controls": (controls or ExecutionControls()).to_dict(),
        "host_start": host,
        "build_provenance": adapter.build_provenance() if hasattr(adapter, "build_provenance") else None,
        "comparison_family_size": max(1, len(benchmarks) * len(candidates), research_family_size or 1),
        "configurations": [{**asdict(c), "flags": list(c.flags)} for c in configurations],
        "probes": {}, "benchmarks": {}, "status": "completed",
        "notes": ["Compute timing excludes input generation and reset/copy work; checksums remain timed."
                  if settings.calibrate else "Wall time includes process startup and deterministic input generation.",
                  "Peak RSS is per-process maximum resident memory; null means unsupported.",
                  "Paired moving-block bootstrap intervals are empirical; short series and nonstationarity limit coverage. No outliers are removed."
                  if settings.calibrate else "Classification is a conservative screening heuristic, not statistical significance.",
                  "Correctness covers supplied deterministic cases, not arbitrary C++ programs."],
    }
    if research:
        result["promotion_eligible"] = False
    with _preserve_failure(result, on_failure):
        for candidate in configurations:
            emit(f"Probing {candidate.name}")
            result["probes"][candidate.name] = adapter.probe(candidate)
    with tempfile.TemporaryDirectory(prefix="aion-build-") as directory, _preserve_failure(result, on_failure):
        root = Path(directory)
        for benchmark in benchmarks:
            emit(f"Compiling and checking {benchmark.name}")
            entries, binaries = {}, {}
            role = "confirmation" if settings.calibrate and purpose in {"independent_confirmation", "verify"} else "performance"
            case = benchmark.case(role)
            result["benchmarks"][benchmark.name] = {
                "fingerprint": benchmark.fingerprint, "cases": list(benchmark.cases),
                "configurations": entries, "schedule": [],
                "measurement_protocol": "aion-compute-v1" if settings.calibrate else "process-wall-v1",
                "measurement_case": case,
                "category": benchmark.category,
                "source_provenance": [{"path": str(path.resolve()), "sha256": file_sha256(path)} for path in benchmark.source_files],
            }
            for index, candidate in enumerate(configurations):
                entry = {"status": "unsupported", "verification": None, "samples": [],
                         "warmups": [], "summary": None, "comparison": None}
                entries[candidate.name] = entry
                if not result["probes"][candidate.name]["supported"]:
                    continue
                # Filenames use indices, never names returned by a future generator.
                binary = root / f"{benchmark.name}-{index}.exe"
                if candidate.build_mode.startswith("control-"):
                    baseline_build = entries.get("baseline", {}).get("build") or {}
                    if not baseline_build.get("success"):
                        entry["status"] = "compile_failed"
                        continue
                    shutil.copy2(root / f"{benchmark.name}-0.exe", binary)
                    build = {**baseline_build, "binary_sha256": file_sha256(binary),
                             "control": {"kind": candidate.build_mode, "byte_identical_baseline": True,
                                         "baseline_binary_sha256": baseline_build.get("binary_sha256")}}
                else:
                    build = (adapter.compile_profiled(benchmark.compilation_input, binary, candidate,
                                                  [benchmark.case("training")], limits, **control_kwargs)
                             if candidate.build_mode == "pgo" else adapter.compile(benchmark.compilation_input, binary, candidate))
                sample_kwargs = {**control_kwargs, **({"control_delay_ns": 50000000}
                                 if candidate.build_mode == "control-slowdown" else {})}
                entry["build"] = build
                if not build["success"]:
                    entry["status"] = "compile_failed"
                    continue
                verification = verify_binary(binary, benchmark, limits, **control_kwargs)
                entry["verification"] = verification
                if not verification["passed"]:
                    entry["status"] = "incorrect"
                    continue
                if settings.calibrate:
                    emit(f"Calibrating {benchmark.name}/{candidate.name}")
                    calibration = calibrate(lambda batches: measure_binary(binary, case, batches, limits, **sample_kwargs),
                                            settings.target_min_seconds, settings.target_max_seconds)
                    entry["calibration"] = calibration
                    if not calibration["passed"]:
                        entry["status"] = "calibration_failed"
                        continue
                entry["status"] = "ready"
                binaries[candidate.name] = binary
            if "baseline" not in binaries:
                result["status"] = "baseline_failed"
                continue
            rng = random.Random(f"{settings.seed}:{benchmark.name}")
            emit(f"Measuring {benchmark.name}: {len(binaries)} configurations")
            for phase, count in (("warmup", settings.warmups), ("measurement", settings.iterations)):
                candidate_names = [name for name in binaries if name != "baseline"]
                directions = {}
                for name in candidate_names:
                    directions[name] = [bool(i % 2) for i in range(count)]
                    rng.shuffle(directions[name])
                for iteration in range(count):
                    pair_order = candidate_names.copy() or ["baseline"]
                    rng.shuffle(pair_order)
                    for paired_name in pair_order:
                        order = ["baseline"] if paired_name == "baseline" else ["baseline", paired_name]
                        if paired_name != "baseline" and directions[paired_name][iteration]:
                            order.reverse()
                        pair_id = f"{phase}:{iteration}:{paired_name}"
                        for name in order:
                            entry = entries[name]
                            if entry["status"] != "ready":
                                continue
                            if settings.calibrate:
                                recipe = next(c for c in configurations if c.name == name)
                                sample_kwargs = {**control_kwargs, **({"control_delay_ns": 50000000}
                                                 if recipe.build_mode == "control-slowdown" else {})}
                                check = measure_binary(binaries[name], case, entry["calibration"]["batches"], limits, **sample_kwargs)
                            else:
                                measured = run_process([str(binaries[name]), *case["args"]], limits, **control_kwargs)
                                check = check_output(measured, case["expected"])
                            result["benchmarks"][benchmark.name]["schedule"].append({
                                "phase": phase, "iteration": iteration, "configuration": name,
                                "pair_id": pair_id, "pair_candidate": paired_name,
                            })
                            record = {"sample_id": f"{result['run_id']}:{benchmark.name}:{name}:{pair_id}",
                                      "iteration": iteration, "pair_id": pair_id,
                                      "pair_candidate": paired_name, **check}
                            entry["warmups" if phase == "warmup" else "samples"].append(record)
                            if not check["passed"]:
                                entry["status"] = "execution_failed"
            for entry in entries.values():
                if entry["status"] == "ready":
                    entry["status"] = "measured"
                    entry["summary"] = _summary(entry["samples"], asdict(settings), settings.calibrate)
            baseline = entries["baseline"]
            if baseline["status"] != "measured":
                result["status"] = "baseline_failed"
                continue
            for name, entry in entries.items():
                if name != "baseline" and entry["summary"]:
                    entry["comparison"] = comparison_for(result, benchmark.name, name)
                    entry["gate_outcomes"] = gate_outcomes(result, benchmark.name, name)
    result["host_end"] = collect_host_diagnostics()
    return result


def gate_outcomes(run: dict, workload: str, name: str) -> dict:
    benchmark = run["benchmarks"][workload]
    entry = benchmark["configurations"][name]
    base = benchmark["configurations"]["baseline"]
    comparison = entry.get("comparison") or {}
    summaries = [comparison.get("paired_baseline_summary", base.get("summary") or {}),
                 comparison.get("paired_candidate_summary", entry.get("summary") or {})]
    uncertainty = comparison.get("uncertainty") or {}
    paired, warmups = _records(benchmark, name), _records(benchmark, name, "warmups")
    requested = run.get("execution_controls", {}).get("requested_cpus")
    gates = {
        "correctness": all((e.get("verification") or {}).get("passed", False) for e in (base, entry)),
        "complete_samples": all(len(records) == run["settings"]["iterations"] and all(r["passed"] for r in records) for records in paired),
        "minimum_samples": min(len(records) for records in paired) >= 5,
        "warmups": run["settings"]["warmups"] >= 1 and all(len(records) == run["settings"]["warmups"] and all(r["passed"] for r in records) for records in warmups),
        "duration": all(not s.get("too_short", True) for s in summaries),
        "variability": all(not s.get("noisy", True) for s in summaries),
        "drift": all(not s.get("drifting", False) for s in summaries),
        "acceptable_regression_bound": comparison.get("improvement_fraction", -1) >= -min(.05, run["settings"]["max_regression"])
             and uncertainty.get("improvement_ci_low", comparison.get("improvement_fraction", -1)) >= -min(.05, run["settings"]["max_regression"]),
        "improvement_floor_and_uncertainty": comparison.get("classification") == "improvement",
        "effective_affinity": all((r.get("execution_controls") or {}).get("verified") is True and
                                   r["execution_controls"].get("effective_cpus") == requested for records in paired for r in records)
                                   if requested is not None else None,
    }
    return {"gates": gates, "failed": [key for key, value in gates.items() if value is False],
            "not_requested": [key for key, value in gates.items() if value is None]}


def candidate_assessment(run: dict, name: str, *, performance_only: bool = False) -> dict:
    """Recompute promotion decisions from raw samples, not report labels."""
    if run.get("evidence_kind", "primary-timing") != "primary-timing":
        return {"eligible": False, "improvements": [], "reasons": ["profiling, sanitizer, and other diagnostic evidence cannot qualify for presets"]}
    improvements, reasons = [], []
    if run.get("status") != "completed" or not run.get("benchmarks"):
        return {"eligible": False, "improvements": [], "reasons": ["incomplete experiment"]}
    thresholds = run["settings"]
    for workload, benchmark in run["benchmarks"].items():
        entries = benchmark["configurations"]
        baseline, candidate = entries.get("baseline", {}), entries.get(name, {})
        valid = True
        timed = benchmark.get("measurement_protocol") == "aion-compute-v1"
        paired = _records(benchmark, name)
        paired_warmups = _records(benchmark, name, "warmups")
        for index, entry in enumerate((baseline, candidate)):
            if (entry.get("status") != "measured" or not (entry.get("verification") or {}).get("passed")
                    or len(paired[index]) != thresholds["iterations"]
                    or len(paired_warmups[index]) != thresholds["warmups"]
                    or not all(sample["passed"] for sample in paired[index])
                    or not all(sample["passed"] for sample in paired_warmups[index])):
                valid = False
            if timed and (not entry.get("calibration", {}).get("passed")
                          or any(not sample.get("measurement") for sample in paired[index])):
                valid = False
        if not valid:
            reasons.append(f"{workload}: missing or failed correctness/measurement evidence")
            continue
        if thresholds["warmups"] < 1:
            reasons.append(f"{workload}: preset promotion requires at least one warmup")
        try:
            comparison = comparison_for(run, workload, name)
        except (AionError, KeyError, TypeError):
            reasons.append(f"{workload}: invalid paired uncertainty evidence")
            continue
        if not comparison["acceptable"]:
            reasons.append(f"{workload}: noisy, short, insufficient, or regressed measurements")
        if comparison["classification"] == "improvement":
            improvements.append(workload)
    if not improvements:
        reasons.append("no measured improvement above the noise floor")
    config = next((c for c in run.get("configurations", []) if c["name"] == name), {})
    if config.get("build_mode", "standard").startswith("control-") and not performance_only:
        reasons.append("experimental controls are never eligible for optimization presets")
    elif config.get("build_mode", "standard") == "pgo" and not performance_only:
        reasons.append("PGO profiles are application-specific and cannot be reused as flag-only presets")
    return {"eligible": not reasons, "improvements": improvements, "reasons": reasons}
