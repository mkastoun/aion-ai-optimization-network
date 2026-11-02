import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys

from . import __version__
from .benchmarks import load_benchmarks
from .compiler import ClangAdapter
from .engine import ExperimentSettings, candidate_assessment, run_experiment
from .environment import machine_environment
from .errors import AionError
from .models import Candidate, Limits
from .optimization import BASELINE, DeterministicGenerator
from .registry import PresetRegistry
from .report import render_report, render_confirmation_report
from .storage import ResultStore, read_json
from .controls import parse_cpus
from .host import collect_host_diagnostics
from .experiments import run_control_series
from .sessions import new_session, load_session, save_session


def _experiment_options(parser):
    parser.add_argument("--compiler", default="clang++", help="Clang C++ executable or path")
    parser.add_argument("--benchmark", default="all", help="all or comma-separated workload names")
    parser.add_argument("--iterations", type=int, default=11)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1729, help="measurement order seed")
    parser.add_argument("--timeout", type=float, default=15, help="per-execution wall timeout in seconds")
    parser.add_argument("--memory-mb", type=int, default=1024, help="POSIX address-space limit in MiB")
    parser.add_argument("--compile-timeout", type=float, default=60)
    parser.add_argument("--noise-threshold", type=float, default=0.05, help="maximum coefficient of variation")
    parser.add_argument("--min-improvement", type=float, default=0.02)
    parser.add_argument("--max-regression", type=float, default=0.05)
    parser.add_argument("--no-calibration", action="store_true", help="retain Phase 1 process-wall timing for diagnostics")
    parser.add_argument("--resamples", type=int, default=10000, help="paired bootstrap resamples")
    parser.add_argument("--cpus", default="none", help="workload affinity: none, auto, or IDs/ranges such as 2,4-5")
    parser.add_argument("--session-file", type=Path, help="existing preflight session record")


def _diagnostic_options(parser):
    parser.add_argument("--compiler",default="clang++")
    parser.add_argument("--compile-timeout",type=float,default=60)
    parser.add_argument("--cpus",default="none")
    parser.add_argument("--session-file",type=Path)
    parser.add_argument("--benchmark",default="all")
    parser.add_argument("--evidence",type=Path,default=Path(".aion/phase4-diagnostics"))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="aion", description="Measure and verify local compiler optimizations")
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument("--store", type=Path, default=Path(".aion"), help="local results/presets directory")
    commands = root.add_subparsers(dest="command", required=True)
    from .research_cli import configure
    configure(commands)
    from .mvp_cli import configure as configure_mvp
    configure_mvp(commands)
    doctor = commands.add_parser("doctor", help="inspect compiler and measurement capabilities")
    doctor.add_argument("--compiler", default="clang++")
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--cpus", default="none")
    preflight=commands.add_parser("preflight",help="read-only native/WSL replication checks and observation session")
    preflight.add_argument("--compiler",default="clang++")
    preflight.add_argument("--cpus",default="none")
    preflight.add_argument("--counters",action="store_true")
    preflight.add_argument("--require-native",action="store_true")
    preflight.add_argument("--session-file",type=Path)
    preflight.add_argument("--label",default="replication session")
    preflight.add_argument('--native-host-note',help='operator record of physical Linux host and observation window; cannot override detection')
    preflight.add_argument("--output",type=Path)
    preflight.add_argument("--json",action="store_true")
    profile=commands.add_parser("profile",help="separate optional counters for rebuilt saved timing configurations")
    _diagnostic_options(profile)
    profile.add_argument("--from-result",type=Path,required=True)
    profile.add_argument("--candidate",action="append")
    profile.add_argument("--samples",type=int,default=3)
    profile.add_argument("--codegen",action="store_true")
    profile.add_argument("--hotspots",action="store_true")
    sanitize=commands.add_parser("sanitize",help="separate ASan/UBSan and differential correctness checks")
    _diagnostic_options(sanitize)
    sanitize.add_argument("--sanitizer",choices=("address","undefined"),action="append")
    sanitize.add_argument("--no-differential",action="store_true")
    quality=commands.add_parser("quality",help="stratified cross-session control outcomes and benchmark readiness")
    quality.add_argument("--result",type=Path,action="append",default=[])
    quality.add_argument("--directory",type=Path,action="append",default=[])
    quality.add_argument("--validation",type=Path)
    quality.add_argument("--output",type=Path)
    symbols=commands.add_parser('symbols',help='audit retained profile IPs against verified ELF function ranges')
    symbols.add_argument('--from-profile',type=Path,required=True)
    for name in ("benchmark", "optimize"):
        command = commands.add_parser(name, help="run an experiment" if name == "benchmark" else "discover and independently confirm presets")
        _experiment_options(command)
        command.add_argument("--candidate", action="append", help="candidate name (repeatable); default: all")
        if name == "benchmark":
            command.add_argument("--baseline-only", action="store_true")
            command.add_argument("--input-role",choices=("performance","confirmation"),default="performance",
                                 help="held-out confirmation permits separate-session benchmark invocations")
        else:
            command.add_argument("--confirm-all", action="store_true",
                                 help="independently remeasure every successful candidate, including negative results")
    verify = commands.add_parser("verify", help="rebuild a preset and check correctness/performance")
    _experiment_options(verify)
    verify.add_argument("--preset", required=True)
    experiment_controls = commands.add_parser("controls", help="repeat A/A and known-slowdown engine controls")
    _experiment_options(experiment_controls)
    experiment_controls.add_argument("--repetitions", type=int, default=2)
    experiment_controls.add_argument("--compare-unpinned", action="store_true")
    experiment_controls.add_argument('--distribution-suite',action='store_true',help='image/kv flat/hotspot versus checker/sequential inputs')
    investigation = commands.add_parser("investigate", help="preserve codegen/profiles and independently retest suspected regressions")
    _experiment_options(investigation)
    investigation.set_defaults(benchmark="sorting,matrix")
    investigation.add_argument("--candidate", action="append")
    investigation.add_argument("--evidence", type=Path, default=Path(".aion/phase3-investigation"))
    investigation.add_argument("--phase2-wheel", type=Path,
                               default=Path(".aion/wheels/aion_network-0.2.0-py3-none-any.whl"))
    investigation.add_argument("--current-sources", action="store_true", help="explicitly investigate current sources instead of a frozen Phase 2 bundle")
    compile_command = commands.add_parser("compile", help="reuse a compatible local preset without AI")
    compile_command.add_argument("--preset", required=True)
    compile_command.add_argument("--source", type=Path, required=True)
    compile_command.add_argument("--output", type=Path, required=True)
    compile_command.add_argument("--compiler", default="clang++")
    compile_command.add_argument("--compile-timeout", type=float, default=60)
    report = commands.add_parser("report", help="render stored JSON as Markdown")
    choice = report.add_mutually_exclusive_group(required=True)
    choice.add_argument("--latest", action="store_true")
    choice.add_argument("--result", type=Path)
    report.add_argument("--output", type=Path)
    report.add_argument("--confirmation", type=Path, help="second run for a paired independent-confirmation report")
    report.add_argument("--comparison", type=Path, help="side-by-side comparison, labeling incompatible hosts/controls without pooling")
    report.add_argument("--audit-json", type=Path, help="write a source-hash-linked per-run promotion-gate audit without altering results")
    presets = commands.add_parser("presets", help="list or inspect verified local presets")
    presets.add_argument("name", nargs="?")
    return root


def _save(store: ResultStore, run: dict) -> Path:
    path = store.save(run)
    report_path = path.with_suffix(".md")
    report_path.write_text(render_report(run), encoding="utf-8")
    print(f"Results: {path}\nReport: {report_path}")
    return path


def _doctor(args) -> int:
    data = {"aion_version": __version__, "environment": machine_environment(),
            "host": collect_host_diagnostics(), "execution_controls": parse_cpus(args.cpus).to_dict(),
            "compiler": None, "ready": False}
    try:
        adapter = ClangAdapter(args.compiler)
        data["compiler"] = asdict(adapter.info)
        data["probe"] = adapter.probe(BASELINE, controls=parse_cpus(args.cpus))
        data["build_provenance"] = adapter.build_provenance()
        data["ready"] = data["probe"]["supported"]
        if not data["ready"]:
            data["error"] = "Clang was detected but the C++ compile/link/run probe failed. See probe diagnostics."
    except AionError as exc:
        data["error"] = str(exc)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"AION {__version__} — {data['environment']['system']}")
        print(f"Compiler: {data['compiler']['version'] if data['compiler'] else 'unavailable'}")
        print(f"Ready: {data['ready']}")
        if "error" in data:
            print(data["error"])
        print("Measurement capabilities: " + json.dumps(data["environment"]["measurement"]))
    return 0 if data["ready"] else 2


def _run(args) -> int:
    if args.command == "doctor":
        return _doctor(args)
    store, registry = ResultStore(args.store), PresetRegistry(args.store)
    if args.command == 'mvp':
        from .mvp_cli import execute
        return execute(args)
    if args.command == 'research':
        from .research_cli import execute
        return execute(args,store)
    progress=lambda message:print(message,file=sys.stderr,flush=True)
    if args.command=='symbols':
        from .profiling import resolve_profile_symbols
        data=resolve_profile_symbols(args.from_profile,read_json(args.from_profile))
        _save(store,data)
        return 0
    if args.command == "preflight":
        from .preflight import run_preflight
        from .storage import atomic_json
        if args.output and (args.output.exists() or args.output==args.session_file):
            raise AionError("Preflight output must be a new path distinct from the session file.")
        session=load_session(args.session_file) if args.session_file and args.session_file.exists() else new_session(label=args.label)
        if args.native_host_note:
            if args.session_file and args.session_file.exists():
                raise AionError('Use a new session file to record a native host observation note.')
            if not 1<=len(args.native_host_note)<=2000:raise AionError('Native host note must be 1..2000 characters.')
            session['native_host_note']=args.native_host_note
        data=run_preflight(args.compiler,args.cpus,session=session,counters=args.counters,require_native=args.require_native)
        if args.session_file and not args.session_file.exists(): save_session(args.session_file,session)
        _save(store,data)
        if args.output: atomic_json(args.output,data)
        if args.json: print(json.dumps(data,indent=2))
        return 0 if data["status"]=="passed" else 2
    if args.command in {"profile","sanitize"}:
        controls=parse_cpus(args.cpus)
        Limits(timeout_seconds=args.compile_timeout)
        session=load_session(args.session_file) if args.session_file else new_session(label=args.command)
        adapter=ClangAdapter(args.compiler,args.compile_timeout)
        if args.command=="profile":
            from .profiling import run_profiles
            source=read_json(args.from_result)
            data=run_profiles(adapter,args.from_result,source,args.benchmark,args.candidate,args.evidence,samples=args.samples,
                              controls=controls,session=session,codegen=args.codegen,hotspots=args.hotspots,progress=progress)
        else:
            from .validation import run_validation
            data=run_validation(adapter,load_benchmarks(args.benchmark),args.evidence,
                                modes=tuple(args.sanitizer or ["address","undefined"]),differential=not args.no_differential,
                                controls=controls,session=session,progress=progress)
        _save(store,data)
        return 0 if data["status"] in {"completed","passed","unsupported"} else 1
    if args.command=="quality":
        from .quality import build_quality_report,is_control_run
        paths=[*args.result,*[p for d in args.directory for p in sorted(d.glob("*.json")) if is_control_run(read_json(p))]]
        if not paths: raise AionError("Supply saved control results or their results directories.")
        if args.output and args.output.resolve() in [p.resolve() for p in [*paths,*([args.validation] if args.validation else [])]]:
            raise AionError("Quality report must not overwrite raw evidence.")
        data=build_quality_report([read_json(p) for p in paths],paths=paths,
                                 validation=read_json(args.validation) if args.validation else None,validation_path=args.validation)
        _save(store,data)
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(render_report(data),encoding="utf-8")
        return 0
    if args.command == "report":
        source_path = store.latest() if args.latest else args.result
        inputs = [path.resolve() for path in (source_path, args.confirmation, args.comparison) if path is not None]
        outputs = [path.resolve() for path in (args.output, args.audit_json) if path is not None]
        if any(path in inputs for path in outputs) or len(set(outputs)) != len(outputs):
            raise AionError("Report/audit outputs must be distinct and must not overwrite input result files.")
        data = read_json(source_path)
        if args.audit_json and data.get("evidence_kind","primary-timing")!="primary-timing":
            raise AionError("Promotion-gate audits require primary timing, not profiling or sanitizer evidence.")
        if args.confirmation and args.comparison:
            raise AionError("Choose either independent confirmation or side-by-side comparison.")
        from .report import render_run_comparison
        rendered = (render_confirmation_report(data, read_json(args.confirmation)) if args.confirmation else
                    render_run_comparison(data, read_json(args.comparison)) if args.comparison else render_report(data))
        if args.audit_json:
            from .provenance import file_sha256
            from .storage import atomic_json
            runs = [(source_path, data)]
            if args.confirmation or args.comparison:
                path = args.confirmation or args.comparison
                runs.append((path, read_json(path)))
            atomic_json(args.audit_json, {"schema_version": 1, "scope": "per-run proposal eligibility; independent confirmation and registry checks are also required",
                "runs": [{"run_id": run["run_id"], "source_path": str(path.resolve()), "source_sha256": file_sha256(path),
                          "assessments": {candidate["name"]: candidate_assessment(run, candidate["name"])
                                          for candidate in run["configurations"] if candidate["name"] != "baseline"}}
                         for path, run in runs]})
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(args.output)
        else:
            print(rendered)
        return 0
    if args.command == "presets":
        print(json.dumps(registry.load(args.name), indent=2) if args.name
              else "\n".join(registry.list_names()) or "No verified local presets.")
        return 0
    if args.command == "compile":
        Limits(timeout_seconds=args.compile_timeout)
        if not args.source.is_file() or args.source.resolve() == args.output.resolve():
            raise AionError("Choose an existing C++ source and a different output path.")
        adapter = ClangAdapter(args.compiler, args.compile_timeout)
        preset = registry.load(args.preset)
        benchmarks = load_benchmarks(",".join(preset["benchmarks"]))
        registry.check_compatibility(preset, adapter.info, machine_environment(), benchmarks)
        build = adapter.compile(args.source, args.output, Candidate("preset", tuple(preset["flags"])))
        if not build["success"]:
            raise AionError(f"Compilation failed: {build['process']['stderr'].strip()}")
        print(f"Compiled {args.output} using preset {args.preset}")
        return 0
    settings = ExperimentSettings(args.iterations, args.warmups, args.seed, args.noise_threshold,
                                  args.min_improvement, args.max_regression,
                                  calibrate=not args.no_calibration, bootstrap_resamples=args.resamples)
    if args.command=='benchmark' and args.input_role=='confirmation' and args.no_calibration:
        raise AionError("Held-out confirmation input selection requires calibrated timing.")
    limits = Limits(args.timeout, args.memory_mb)
    controls = parse_cpus(args.cpus)
    session = load_session(args.session_file) if args.session_file else new_session(label=args.command)
    # Validate compilation timeout even if no compiler is present.
    Limits(timeout_seconds=args.compile_timeout)
    benchmarks = load_benchmarks(args.benchmark)
    adapter = ClangAdapter(args.compiler, args.compile_timeout)
    if args.command == "investigate":
        if not args.current_sources and not args.phase2_wheel.is_file():
            raise AionError("Phase 2 source wheel is unavailable. Supply --phase2-wheel or explicitly choose --current-sources.")
        available = {candidate.name: candidate for candidate in DeterministicGenerator().generate()}
        names = args.candidate or ["o2", "pgo", "pgo-lto"]
        if len(set(names)) != len(names) or any(name not in available for name in names):
            raise AionError("Unknown or repeated investigation candidate.")
        from .investigation import run_investigation
        evidence = run_investigation(adapter, benchmarks, [available[name] for name in names], settings, limits,
                                    args.evidence, controls=controls,
                                    phase2_wheel=None if args.current_sources else args.phase2_wheel,
                                    on_result=lambda run: _save(store, run),
                                    progress=lambda message: print(message, file=sys.stderr, flush=True))
        print(f"Investigation evidence: {evidence['directory']}", flush=True)
        return 0
    if args.command == "controls":
        progress = lambda message: print(message, file=sys.stderr, flush=True)
        runs = run_control_series(adapter, benchmarks, settings, limits, controls,
                                  repetitions=args.repetitions, compare_unpinned=args.compare_unpinned,
                                  on_result=lambda run: _save(store, run), progress=progress, session=session,
                                  distribution_suite=args.distribution_suite)
        from .report import render_control_report
        path = args.store / "control-series.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_control_report(runs), encoding="utf-8")
        from .storage import atomic_json
        atomic_json(args.store / "control-series.json", {"schema_version": 1,
                    "experiment_kind": "control-series", "run_ids": [run["run_id"] for run in runs],
                    "diagnostics": [run["control_diagnostics"] for run in runs]})
        print(f"Control report: {path}", flush=True)
        return 0 if all(run["status"] == "completed" and run["control_diagnostics"]["false_positive_check_passed"] for run in runs) else 1
    if args.command == "verify":
        preset = registry.load(args.preset)
        recorded = ",".join(preset["benchmarks"])
        if args.benchmark == "all":
            benchmarks = load_benchmarks(recorded)
        registry.check_compatibility(preset, adapter.info, machine_environment(), benchmarks)
        candidates = [Candidate("preset", tuple(preset["flags"]))]
    else:
        available = {candidate.name: candidate for candidate in DeterministicGenerator().generate()}
        names = args.candidate or list(available)
        if len(names) != len(set(names)) or any(name not in available for name in names):
            raise AionError("Choose unique candidates from: " + ", ".join(available))
        candidates = [] if getattr(args, "baseline_only", False) else [available[name] for name in names]
    progress = lambda message: print(message, file=sys.stderr, flush=True)
    run = run_experiment(adapter, benchmarks, candidates, settings, limits,
                         purpose='independent_confirmation' if args.command=='benchmark' and args.input_role=='confirmation' else args.command,
                         progress=progress, controls=controls,
                         on_failure=lambda partial: _save(store, partial), session=session)
    if args.command == "verify":
        # A preset may cease to be faster but must still pass correctness, noise,
        # and regression checks. Always retain fresh verification evidence.
        passed = run["status"] == "completed" and all(
            benchmark["configurations"]["preset"]["status"] == "measured"
            and benchmark["configurations"]["preset"]["comparison"] is not None
            and benchmark["configurations"]["preset"]["comparison"]["acceptable"]
            for benchmark in run["benchmarks"].values())
        run["preset_verification"] = {"name": args.preset, "passed": passed}
        _save(store, run)
        print("Preset verification: " + ("passed" if passed else "failed or inconclusive"))
        return 0 if passed else 1
    _save(store, run)
    if args.command == "benchmark":
        return 0 if run["status"] == "completed" and all(
            entry["status"] in {"measured", "unsupported"}
            for benchmark in run["benchmarks"].values()
            for entry in benchmark["configurations"].values()) else 1
    eligible = [candidate for candidate in candidates if candidate_assessment(run, candidate.name)["eligible"]]
    confirmation_candidates = eligible
    if args.confirm_all:
        confirmation_candidates = [candidate for candidate in candidates if all(
            benchmark["configurations"][candidate.name]["status"] == "measured"
            for benchmark in run["benchmarks"].values())]
    if not confirmation_candidates:
        print("No preset promoted: no candidate met correctness, noise, and improvement requirements.")
        return 0 if run["status"] == "completed" else 1
    confirmation_settings = replace(settings, seed=settings.seed + 1)
    confirmation = run_experiment(adapter, benchmarks, confirmation_candidates, confirmation_settings, limits,
                                  purpose="independent_confirmation", progress=progress, controls=controls,
                                  on_failure=lambda partial: _save(store, partial), session=session)
    _save(store, confirmation)
    if not eligible:
        print("Independent confirmation recorded. No preset promoted: discovery did not meet strict requirements.")
    for candidate in eligible:
        try:
            name = f"{candidate.name}-{run['run_id'].lower()}"
            path = registry.register(name, candidate.name, run, confirmation)
            print(f"Verified preset: {path}")
        except AionError as exc:
            print(f"Candidate {candidate.name}: {exc}")
    return 0 if confirmation["status"] == "completed" else 1


def main(argv: list[str] | None = None) -> int:
    try:
        return _run(parser().parse_args(argv))
    except (AionError, OSError) as exc:
        print(f"aion: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("aion: interrupted", file=sys.stderr)
        return 130
