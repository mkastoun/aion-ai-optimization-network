"""Engine validation controls; no control can become a published preset."""

from dataclasses import replace

from .controls import ExecutionControls
from .engine import ExperimentSettings, candidate_assessment, run_experiment
from .models import Candidate
from .sessions import new_session


CONTROL_CANDIDATES = (
    Candidate("control-aa", ("-O3",), "Byte-identical baseline copy", "control-aa"),
    Candidate("control-slowdown", ("-O3",), "Same binary/checksum plus 50 ms elapsed busy-loop delay per unit", "control-slowdown"),
)


def distribution_benchmarks(benchmarks):
    """Use existing independently checked flat/hotspot and checker/sequential cases."""
    from .validation import validation_cases
    from .errors import AionError
    result=[]
    for benchmark in benchmarks:
        if benchmark.name not in {'image','kv'}:
            raise AionError("The distribution control suite selects only image and kv.")
        extra=validation_cases(benchmark)
        selected=[next(c for c in extra if c['name']==label) for label in
                  ('flat-or-hotspot','checkerboard-or-sequential')]
        cases=[{**c,'name':'ordinary-'+c['name']} if c['name'] in {'performance','confirmation'} else c for c in benchmark.cases]
        cases += [{**c,'name':role} for c,role in zip(selected,('performance','confirmation'))]
        result.append(replace(benchmark,cases=tuple(cases)))
    return result


def control_diagnostics(run: dict) -> dict:
    rows, false_positives = [], []
    for workload, benchmark in run["benchmarks"].items():
        for name in ("control-aa", "control-slowdown"):
            entry = benchmark["configurations"].get(name, {})
            comparison = entry.get("comparison") or {}
            classification = comparison.get("classification", entry.get("status", "unavailable"))
            build = entry.get("build") or {}
            baseline_hash = benchmark["configurations"].get("baseline", {}).get("build", {}).get("binary_sha256")
            identical = bool(baseline_hash and build.get("binary_sha256") == baseline_hash)
            if name == "control-aa":
                false_positive = classification == "improvement" and comparison.get("acceptable", False)
                if false_positive:
                    false_positives.append(workload)
                verdict = ("false_positive" if false_positive else "consistent_with_AA" if identical and
                           classification == "no_clear_change" and comparison.get("acceptable") else "inconclusive_or_unexpected")
            else:
                verdict = "verified_regression_control" if identical and classification == "regression" else "inconclusive"
            rows.append({"workload": workload, "control": name, "classification": classification,
                         "verdict": verdict, "identical_baseline_binary": identical,
                         "comparison": comparison})
    return {"rows": rows, "false_positive_workloads": false_positives,
            "aa_performance_gate": candidate_assessment(run, "control-aa", performance_only=True),
            "safe_to_promote_controls": False, "false_positive_check_passed": not false_positives,
            "note": "No A/A signal is not a proof of equivalence; noisy negative controls remain inconclusive."}


def run_control_series(adapter, benchmarks, settings: ExperimentSettings, limits,
                       controls: ExecutionControls, *, repetitions: int = 2,
                       compare_unpinned: bool = False, on_result=None, progress=None,
                       session: dict | None = None, distribution_suite: bool = False) -> list[dict]:
    from .errors import AionError
    if not settings.calibrate or not 2 <= repetitions <= 20:
        raise AionError("Control series require calibrated timing and 2..20 independent repetitions.")
    if compare_unpinned and controls.cpu_affinity is None:
        raise AionError("Pinned/unpinned controls require --cpus auto or explicit CPU IDs.")
    runs = []
    if distribution_suite:
        benchmarks=distribution_benchmarks(benchmarks)
    session = session or new_session(label="control series")
    modes = [ExecutionControls(), controls] if compare_unpinned else [controls]
    for repetition in range(repetitions):
        for placement in (modes if repetition % 2 == 0 else list(reversed(modes))):
            run = run_experiment(adapter, benchmarks, list(CONTROL_CANDIDATES),
                                 replace(settings, seed=settings.seed + repetition), limits,
                                 purpose="control" if repetition % 2 == 0 else "independent_confirmation",
                                 controls=placement, progress=progress, on_failure=on_result, session=session)
            run["experiment_kind"] = "control"
            if distribution_suite:
                run['control_input_design']='existing-validation-distributions-v1'
            run["control_diagnostics"] = control_diagnostics(run)
            runs.append(run)
            if on_result:
                on_result(run)
    return runs
