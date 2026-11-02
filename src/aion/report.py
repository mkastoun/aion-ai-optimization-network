import statistics

from .errors import AionError


def _validate_run(run: dict):
    """Reject incomplete foreign JSON before walking the report structure."""
    try:
        if not isinstance(run["benchmarks"], dict) or not isinstance(run["configurations"], list):
            raise ValueError("invalid benchmark or configuration collection")
        for key in ("run_id", "purpose", "status", "notes"):
            run[key]
        for key in ("system", "machine", "cpu"):
            run["environment"][key]
        for key in ("version", "target"):
            run["compiler"][key]
        for key in ("iterations", "warmups", "seed"):
            run["settings"][key]
        for benchmark in run["benchmarks"].values():
            for entry in benchmark["configurations"].values():
                entry["status"]
                for sample in entry["samples"]:
                    sample["process"]["peak_rss_bytes"]
        for config in run["configurations"]:
            config["name"], config["flags"]
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise AionError(f"Invalid experiment JSON for reporting: {exc}") from exc


def _number(value: float | int | None, scale: float = 1) -> str:
    return "n/a" if value is None else f"{value * scale:.3f}"


def render_report(run: dict) -> str:
    if run.get('evidence_kind') in {'mvp-plan','mvp-report','mvp-run'}:
        from .mvp_report import render_markdown,build_report
        return render_markdown(build_report(run) if run['evidence_kind']=='mvp-run' else run)
    if run.get('evidence_kind')=='native-replication-report':
        from .native_report import render_native
        return render_native(run)
    if run.get('evidence_kind') in {'research-timing','research-study','research-report','research-diagnostics'}:
        from .research import render_research
        try:
            return render_research(run)
        except (KeyError,TypeError,ValueError,AttributeError) as exc:
            raise AionError(f"Invalid research evidence JSON for reporting: {exc}") from exc
    if run.get("evidence_kind", "primary-timing") != "primary-timing":
        from .diagnostic_report import render_diagnostic_report
        try:
            return render_diagnostic_report(run)
        except (KeyError,TypeError,ValueError,AttributeError) as exc:
            raise AionError(f"Invalid diagnostic evidence JSON for reporting: {exc}") from exc
    _validate_run(run)
    if run.get("methodology_version", 1) >= 2:
        return _reliable_report(run)
    machine, compiler = run["environment"], run["compiler"]
    lines = ["# AION performance comparison", "", f"Run: `{run['run_id']}` ({run['purpose']})",
             f"Status: **{run['status']}**", "",
             f"Compiler: {compiler['version']} — {compiler['target']}",
             f"Machine: {machine['system']} {machine['machine']} — {machine['cpu']}",
             f"Iterations: {run['settings']['iterations']}; warmups: {run['settings']['warmups']}; "
             f"schedule seed: {run['settings']['seed']}", "",
             "Positive time change means faster than -O3. Memory is median peak RSS per run.", "",
             "| Workload | Configuration | Median ms | CV % | Peak RSS MiB | Compile ms | Binary KiB | Time change | Outcome |",
             "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for workload, benchmark in run["benchmarks"].items():
        for name, entry in benchmark["configurations"].items():
            summary, build = entry.get("summary") or {}, entry.get("build") or {}
            memory = [sample["process"]["peak_rss_bytes"] for sample in entry["samples"]
                      if sample["process"]["peak_rss_bytes"] is not None]
            comparison = entry.get("comparison") or {}
            change = comparison.get("improvement_fraction")
            outcome = comparison.get("classification", entry["status"])
            if summary.get("noisy") or summary.get("too_short"):
                outcome += " (noisy/short)"
            lines.append("| " + " | ".join([
                workload, name, _number(summary.get("median_seconds"), 1000),
                _number(summary.get("coefficient_of_variation"), 100),
                _number(statistics.median(memory) if memory else None, 1 / 1024**2),
                _number(build.get("seconds"), 1000), _number(build.get("executable_bytes"), 1/1024),
                "baseline" if name == "baseline" else (_number(change, 100) + "%" if change is not None else "n/a"),
                outcome,
            ]) + " |")
    lines.extend(["", "## Configurations", ""])
    for config in run["configurations"]:
        lines.append(f"- `{config['name']}`: `{' '.join(config['flags'])}`")
    failures = []
    for workload, benchmark in run["benchmarks"].items():
        for name, entry in benchmark["configurations"].items():
            if entry["status"] in {"incorrect", "execution_failed", "compile_failed", "unsupported"}:
                failures.append(f"- {workload}/{name}: {entry['status']}; see raw JSON diagnostics.")
    if failures:
        lines.extend(["", "## Rejected or unavailable configurations", "", *failures])
    lines.extend(["", "## Measurement limits", "", *[f"- {note}" for note in run["notes"]],
                  "- Compile time is a single observation; it is not a statistically stable comparison.",
                  "- An improvement applies only to these workloads and this recorded environment.",
                  "- Preset promotion requires fresh builds and measurements with a different schedule seed.",
                  "- This runner executes trusted local code; resource limits are not a security sandbox.", ""])
    return "\n".join(lines)


def _reliable_report(run: dict) -> str:
    settings = run["settings"]
    lines = ["# AION Phase " + ("4" if run.get("methodology_version",2)>=4 else "3" if run.get("methodology_version", 2) >= 3 else "2") + " performance comparison", "",
             f"Run: `{run['run_id']}` ({run['purpose']}); status: **{run['status']}**", "",
             f"Compiler: {run['compiler']['version']} — {run['compiler']['target']}",
             f"Machine: {run['environment']['system']} — {run['environment']['cpu']}",
             f"Measured pairs per candidate: {settings['iterations']}; warmups: {settings['warmups']}; "
             f"schedule/bootstrap seed: {settings['seed']}.", "",
             f"Target compute time: {settings['target_min_seconds']*1000:.0f}–"
             f"{settings['target_max_seconds']*1000:.0f} ms per sample. "
             "Input generation, allocation of input buffers, and reset/copy work are excluded from compute time.", "",
             "A unit is one execution of the workload's fixed input/rounds. Each configuration calibrates its "
             "batch count separately; comparisons normalize by batches and use its adjacent -O3 partner. "
             "Insertion/rehash costs in hash maps and checksum scans remain timed.", "",
             "Positive paired improvement means faster. Both the reported gain and interval describe the median of paired effects. "
             "The raw JSON also retains the ratio of marginal medians used by the unchanged screening floor. Intervals use a Bonferroni "
             f"adjustment across {run['comparison_family_size']} declared comparisons "
             f"(nominal family confidence {settings['confidence']*100:.0f}%).", "",
             "| Workload | Config | Batches | Unit ms | Sample ms | CV % | Paired gain % | Adjusted interval % | Outcome |",
             "|---|---|---:|---:|---:|---:|---:|---|---|"]
    for workload, benchmark in run["benchmarks"].items():
        for name, entry in benchmark["configurations"].items():
            summary, comparison = entry.get("summary") or {}, entry.get("comparison") or {}
            uncertainty = comparison.get("uncertainty", {})
            interval = (f"[{uncertainty['improvement_ci_low']*100:.3f}, "
                        f"{uncertainty['improvement_ci_high']*100:.3f}]" if uncertainty else "n/a")
            flags = []
            partners = [summary, comparison.get("paired_baseline_summary", {}), comparison.get("paired_candidate_summary", {})]
            if any(s.get("noisy") for s in partners): flags.append("noisy")
            if any(s.get("drifting") for s in partners): flags.append("drift")
            if any(s.get("too_short") for s in partners): flags.append("short")
            outcome = comparison.get("classification", entry["status"])
            if flags: outcome += " (" + ", ".join(flags) + ")"
            lines.append("| " + " | ".join([
                workload, name, str((entry.get("calibration") or {}).get("batches", "n/a")),
                _number(summary.get("median_seconds"), 1000),
                _number(summary.get("physical_median_seconds"), 1000),
                _number(summary.get("coefficient_of_variation"), 100),
                "baseline" if name == "baseline" else _number(uncertainty.get("paired_improvement_fraction"), 100),
                interval, outcome,
            ]) + " |")
    lines.extend(["", "## Calibration and inputs", "",
                  "Pilots are discarded from statistics; all pilot outputs must pass correctness. "
                  "Measured samples are retained even when noisy or outside the target band.", "",
                  "| Workload | Input seed | Config | Pilots | Batches | Pilot median ms | Samples in target band |",
                  "|---|---:|---|---:|---:|---:|---:|"])
    for workload, benchmark in run["benchmarks"].items():
        for name, entry in benchmark["configurations"].items():
            calibration = entry.get("calibration") or {}
            within = sum(settings["target_min_seconds"] <= s["measurement"]["compute_seconds"] <= settings["target_max_seconds"]
                         for s in entry["samples"] if s.get("measurement"))
            lines.append(f"| {workload} | {benchmark['measurement_case']['args'][1]} | {name} | "
                         f"{len(calibration.get('pilots', []))} | {calibration.get('batches', 'n/a')} | "
                         f"{_number(calibration.get('median_compute_seconds'), 1000)} | {within}/{len(entry['samples'])} |")
    lines.extend(["", "## Resource comparison", "",
                  "Peak RSS covers the whole process, including prepared input buffers. Setup is not part of compute time. "
                  "Build time is one observation; PGO includes instrumented build, profile merge, and final build. "
                  "Training time is reported separately.", "",
                  "| Workload | Config | Peak RSS MiB | Setup ms/sample | Build ms | PGO training ms | Binary KiB |",
                  "|---|---|---:|---:|---:|---:|---:|"])
    for workload, benchmark in run["benchmarks"].items():
        for name, entry in benchmark["configurations"].items():
            build = entry.get("build") or {}
            pgo = build.get("pgo") or {}
            memory = [s["process"]["peak_rss_bytes"] for s in entry["samples"] if s["process"]["peak_rss_bytes"] is not None]
            setup = [s["measurement"]["setup_seconds"] for s in entry["samples"] if s.get("measurement")]
            training = sum(check["process"]["duration_seconds"] for check in pgo.get("training", []))
            lines.append("| " + " | ".join([
                workload, name, _number(statistics.median(memory) if memory else None, 1/1024**2),
                _number(statistics.median(setup) if setup else None, 1000),
                _number(pgo.get("total_build_seconds", build.get("seconds")), 1000),
                _number(training, 1000) if pgo else "n/a", _number(build.get("executable_bytes"), 1/1024),
            ]) + " |")
    lines.extend(["", "## Configurations and verification", ""])
    for config in run["configurations"]:
        lines.append(f"- `{config['name']}`: `{' '.join(config['flags'])}`; build mode `{config.get('build_mode', 'standard')}`.")
    for workload, benchmark in run["benchmarks"].items():
        for name, entry in benchmark["configurations"].items():
            if entry["status"] != "measured":
                lines.append(f"- {workload}/{name}: **{entry['status']}**; see raw JSON for probe, build, calibration, and correctness diagnostics.")
    lines.extend(["", "## Interpretation limits", "", *[f"- {note}" for note in run["notes"]],
                  "- Existing promotion floors remain: at least 2% and twice combined relative MAD; maximum 5% regression; CV at most 5% by default.",
                  "- Confidence bounds and drift checks add restrictions; they never relax those rules. No samples are dropped.",
                  "- Circular moving-block resampling retains adjacent pair dependence; its square-root block length is a heuristic. Coverage remains approximate with few pairs or nonstationarity.",
                  "- Fresh confirmation uses a different scheduling/bootstrap seed and a different held-out input seed with equal work per batch.",
                  "- PGO profiles are trained on separate inputs and regenerated for each experiment. They cannot become reusable flag-only application presets.",
                  "- Resource limits handle accidental runaway trusted local code; they are not a security sandbox.", ""])
    if run.get("methodology_version", 2) >= 3:
        lines.extend([render_host_summary(run), "## Gate audit", "",
                      "| Workload | Candidate | Failed gates |", "|---|---|---|"])
        for workload, benchmark in run["benchmarks"].items():
            for name, entry in benchmark["configurations"].items():
                if name != "baseline":
                    gates = entry.get("gate_outcomes")
                    lines.append(f"| {workload} | {name} | {', '.join(gates['failed']) or 'none' if gates else entry['status']} |")
        lines.append("")
    return "\n".join(lines)


def render_host_summary(run: dict) -> str:
    host = run.get("host_start") or {}
    end = run.get("host_end") or {}
    controls = run.get("execution_controls") or {}
    requested = controls.get("requested_cpus")
    samples = [s for b in run.get("benchmarks", {}).values() for e in b["configurations"].values() for s in e["samples"]]
    verified = sum((s.get("execution_controls") or {}).get("verified") is True for s in samples)
    methods = sorted({(s.get("execution_controls") or {}).get("method", "unavailable") for s in samples})
    observed_endpoints = [s for s in samples if (s.get("measurement") or {}).get("cpu_start", -1) >= 0
                          and (s.get("measurement") or {}).get("cpu_end", -1) >= 0]
    migrations = sum(s["measurement"]["cpu_start"] != s["measurement"]["cpu_end"] for s in observed_endpoints)
    summaries = [e["summary"] for b in run.get("benchmarks", {}).values() for e in b["configurations"].values() if e.get("summary")]
    return "\n".join(["", "## Host stability and effective controls", "",
        f"Evidence type: **{host.get('virtualization', {}).get('kind', 'legacy/unavailable')}**. "
        "WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.",
        f"Stable host fingerprint: `{host.get('host_fingerprint', 'unavailable')}`.",
        f"Environment classification: `{host.get('environment_classification','legacy-unclassified')}`; "
        f"session: `{run.get('session',{}).get('session_id','unavailable')}`. Session IDs alone do not establish independent host conditions.",
        "Measurement environment readiness is assessed separately by `aion quality`; compile/affinity validation alone is insufficient.",
        f"Requested affinity: `{requested if requested is not None else 'disabled'}`; verified pinned samples: {verified}/{len(samples)}. "
        "When disabled, an observed allowed mask does not mean CPU pinning was applied.",
        f"Recorded verification methods: `{methods}`. Verification is a snapshot, not exclusive CPU ownership.",
        f"Different CPU endpoints observed: {migrations}/{len(observed_endpoints)}; equal endpoints do not prove no intermediate migration.",
        f"Noisy configuration summaries: {sum(s['noisy'] for s in summaries)}/{len(summaries)}; "
        f"drifting: {sum(s.get('drifting', False) for s in summaries)}/{len(summaries)}.",
        f"Load average at start/end: `{host.get('load_average')}` / `{end.get('load_average')}`.",
        f"Unavailable observations: {', '.join(host.get('unavailable', [])) or 'none listed'}. "
        "Available values and their sysfs/proc origins are preserved in JSON.",
        "AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, "
        "and PGO profile hashes are recorded separately. No samples are pooled across runs.", ""])


def render_control_report(runs: list[dict]) -> str:
    lines = ["# AION measurement-system controls", "",
             "A/A uses a byte-identical baseline binary. The negative control uses the same binary and checksum "
             "plus an explicitly recorded 50 ms elapsed busy-loop delay inside each timed unit. "
             "This uses the steady clock, not a consumed-CPU-time clock. Controls can never become optimization presets.", "",
             "| Run | Input seed | CPU request | Workload | Control | Identical binary | Outcome |",
             "|---|---:|---|---|---|---|---|"]
    for run in runs:
        for row in run["control_diagnostics"]["rows"]:
            seed = run["benchmarks"][row["workload"]]["measurement_case"]["args"][1]
            lines.append(f"| {run['run_id']} | {seed} | {run['execution_controls']['requested_cpus']} | "
                         f"{row['workload']} | {row['control']} | {row['identical_baseline_binary']} | {row['verdict']} |")
    count = sum(len(run["control_diagnostics"]["false_positive_workloads"]) for run in runs)
    lines.extend(["", f"Observed A/A false-positive improvement classifications: **{count}**. "
                  "These classifications are audited even though publishing controls is prohibited. "
                  "A lack of observed false positives does not prove an engine-wide error rate or equivalence.",
                  "Known slowdowns are called verified only when all unchanged measurement-quality and regression gates permit it. "
                  "Noise, short durations, or drift remain inconclusive. Pinned/unpinned estimates are never pooled.", ""])
    for run in runs:
        lines.extend([f"## Run `{run['run_id']}`", render_host_summary(run)])
    return "\n".join(lines)


def render_run_comparison(first: dict, second: dict) -> str:
    _validate_run(first)
    _validate_run(second)
    from .reproducibility import compare_run_compatibility
    compatibility = compare_run_compatibility(first, second)
    lines = ["# AION independent-run comparison", "",
             f"Runs: `{first['run_id']}` / `{second['run_id']}`.",
             f"Compatible for independent confirmation: **{compatibility['compatible']}**.",
             "Raw samples are never pooled. Incompatible hosts or CPU controls are side-by-side diagnostics only.",
             "Reasons: " + ("; ".join(compatibility["reasons"]) or "no incompatible recorded fields"),
             "Unavailable provenance: " + (", ".join(compatibility["unavailable"]) or "none listed"), "",
             "| Workload | Candidate | First classification | Second classification |", "|---|---|---|---|"]
    for workload, benchmark in first.get("benchmarks", {}).items():
        other = second.get("benchmarks", {}).get(workload, {}).get("configurations", {})
        for name, entry in benchmark["configurations"].items():
            if name != "baseline":
                lines.append(f"| {workload} | {name} | {(entry.get('comparison') or {}).get('classification', entry['status'])} | "
                             f"{(other.get(name, {}).get('comparison') or {}).get('classification', 'unavailable')} |")
    lines.extend([render_host_summary(first), render_host_summary(second)])
    return "\n".join(lines)


def render_confirmation_report(discovery: dict, confirmation: dict) -> str:
    _validate_run(discovery)
    _validate_run(confirmation)
    if discovery.get("methodology_version", 1) >= 3 or confirmation.get("methodology_version", 1) >= 3:
        from .reproducibility import require_confirmation_compatible
        require_confirmation_compatible(discovery, confirmation)
    if discovery.get("methodology_version", 0) < 2 or confirmation.get("methodology_version", 0) < 2:
        raise AionError("Paired confirmation reports require Phase 2 experiments.")
    if (discovery["run_id"] == confirmation["run_id"]
            or discovery["settings"]["seed"] == confirmation["settings"]["seed"]
            or discovery["compiler"] != confirmation["compiler"]
            or discovery["environment"] != confirmation["environment"]):
        raise AionError("Independent confirmation requires fresh run IDs/seeds and the same compiler/machine.")
    for workload, benchmark in discovery["benchmarks"].items():
        other = confirmation["benchmarks"].get(workload)
        if other is None or other["fingerprint"] != benchmark["fingerprint"]:
            raise AionError("Confirmation workload fingerprints must match discovery.")
        first_case, second_case = benchmark["measurement_case"], other["measurement_case"]
        if first_case["args"][1] == second_case["args"][1] or first_case["args"][::2] != second_case["args"][::2]:
            raise AionError("Confirmation must use different input seeds and equal work per batch.")
    lines = ["# AION Phase " + ("4" if discovery.get("methodology_version",2)>=4 else "3" if discovery.get("methodology_version", 2) >= 3 else "2") + " performance report", "",
             f"Discovery: `{discovery['run_id']}`; confirmation: `{confirmation['run_id']}`.", "",
             f"Compiler: {discovery['compiler']['version']}. Machine: {discovery['environment']['cpu']}.",
             f"Scheduling/bootstrap seeds: {discovery['settings']['seed']} and {confirmation['settings']['seed']}.", "",
             "Inputs differ between runs; each configuration is compared only against its matched -O3 measurement within that run. "
             "A workload-level repeatable improvement does not by itself qualify a configuration for a suite-wide preset.", "",
             f"Each candidate has {discovery['settings']['iterations']} measured pairs per workload and "
             f"{discovery['settings']['bootstrap_resamples']} circular moving-block bootstrap resamples. "
             f"Intervals use nominal {discovery['settings']['confidence']*100:.0f}% family confidence across "
             f"{discovery['comparison_family_size']} declared comparisons "
             f"({(1-(1-discovery['settings']['confidence'])/discovery['comparison_family_size'])*100:.2f}% per interval). "
             "Coverage is approximate, especially for short or nonstationary series.", "",
             "A confidence interval away from zero does not override the unchanged CV, drift, duration, "
             "2%/combined-MAD improvement floor, or 5% regression checks. All measured samples are retained. "
             "PGO profiles remain program-specific research evidence, not reusable flag-only presets.", "",
             "| Workload | Candidate | Discovery paired gain % | Confirmation paired gain % | Discovery interval % | Confirmation interval % | Outcome |",
             "|---|---|---:|---:|---|---|---|"]
    for workload, benchmark in discovery["benchmarks"].items():
        other = confirmation["benchmarks"].get(workload, {}).get("configurations", {})
        for name, entry in benchmark["configurations"].items():
            if name == "baseline": continue
            first = entry.get("comparison") or {}
            second = other.get(name, {}).get("comparison") or {}
            intervals = []
            for comparison in (first, second):
                uncertainty = comparison.get("uncertainty") or {}
                intervals.append(f"[{uncertainty['improvement_ci_low']*100:.3f}, {uncertainty['improvement_ci_high']*100:.3f}]"
                                 if uncertainty else "n/a")
            warmed = min(discovery["settings"]["warmups"], confirmation["settings"]["warmups"]) >= 1
            repeatable = warmed and all(c.get("classification") == "improvement" and c.get("acceptable") for c in (first, second))
            repeated_regression = warmed and all(c.get("classification") == "regression" for c in (first, second))
            if repeatable:
                outcome = "verified improvement (repeatable improvement on this workload)" if discovery.get("methodology_version", 2) >= 3 else "repeatable improvement on this workload"
            elif repeated_regression:
                outcome = "verified regression on this workload"
            else:
                outcome = f"{first.get('classification', entry['status'])} / {second.get('classification', 'unavailable')}"
            recipe = next((c.get("build_mode", "standard") for c in discovery["configurations"] if c["name"] == name), "standard")
            if recipe.startswith("control-"):
                outcome = "experimental control only: " + outcome
            lines.append(f"| {workload} | {name} | {_number(first.get('uncertainty', {}).get('paired_improvement_fraction'), 100)} | "
                         f"{_number(second.get('uncertainty', {}).get('paired_improvement_fraction'), 100)} | {' | '.join(intervals)} | {outcome} |")
    lines.extend(["", "## Duration and correctness audit", "",
                  "| Run | Verified configurations | Median compute sample range ms | Measured samples inside 250–500 ms |",
                  "|---|---:|---:|---:|"])
    for run in (discovery, confirmation):
        entries = [e for b in run["benchmarks"].values() for e in b["configurations"].values()]
        medians = [e["summary"]["physical_median_seconds"]*1000 for e in entries if e.get("summary")]
        samples = [s for e in entries for s in e["samples"]]
        within = sum(.25 <= s["measurement"]["compute_seconds"] <= .5 for s in samples if s.get("measurement"))
        correct = sum(bool((e.get("verification") or {}).get("passed")) for e in entries)
        span = f"{min(medians):.1f}–{max(medians):.1f}" if medians else "n/a"
        lines.append(f"| {run['purpose']} | {correct}/{len(entries)} | {span} | {within}/{len(samples)} |")
    lines.extend(["", "Full raw samples, calibration pilots, physical durations, paired intervals, drift, resources, correctness checks, "
                  "and PGO provenance remain in each experiment's JSON and detailed Markdown report.", ""])
    if discovery.get("methodology_version", 2) >= 3:
        lines.extend(["**Evidence scope:** " + discovery.get("host_start", {}).get("virtualization", {}).get("kind", "unavailable") +
                      "; CPU affinity verifies guest/logical placement, not physical-host isolation. "
                      "Native Linux replications require their own host identity; incompatible samples are not pooled.",
                      "", "Discovery host:", render_host_summary(discovery), "Confirmation host:", render_host_summary(confirmation)])
    return "\n".join(lines)
