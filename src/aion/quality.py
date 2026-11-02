"""Stratified control outcomes/readiness; timing samples are never pooled."""
from collections import Counter
import json
import math
import statistics

from .engine import comparison_for, gate_outcomes
from .errors import AionError
from .evidence import evidence_header
from .provenance import file_sha256
from .reproducibility import compare_run_compatibility,stable_environment_controls


def is_control_run(run):
    return run.get('experiment_kind')=='control' or any(c.get('build_mode','').startswith('control-') for c in run.get('configurations',[]))


def descriptive_rate(successes: int, total: int) -> dict:
    if not 0 <= successes <= total: raise AionError("Invalid outcome counts.")
    if not total: return {"count":successes,"total":total,"fraction":None,"interval_95":None,"method":"Wilson descriptive interval"}
    z=1.959963984540054
    p=successes/total
    center=(p+z*z/(2*total))/(1+z*z/total)
    half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/(1+z*z/total)
    return {"count":successes,"total":total,"fraction":p,"interval_95":[max(0.,center-half),min(1.,center+half)],
            "method":"95% Wilson binomial descriptive approximation; correlated controls/sessions limit coverage"}


def _design(run):
    return {"input_design":run.get('control_input_design','original'),"settings":{k:v for k,v in run["settings"].items() if k!="seed"},
            "work_units":{w:b["measurement_case"]["args"][::2] for w,b in run["benchmarks"].items()}}


def _row(run, workload, name):
    benchmark=run["benchmarks"][workload]
    entry=benchmark["configurations"].get(name,{})
    try:
        comparison=comparison_for(run,workload,name)
        shadow={**run,"benchmarks":{**run["benchmarks"],workload:{**benchmark,"configurations":{
            **benchmark["configurations"],name:{**entry,"comparison":comparison}}}}}
        gates=gate_outcomes(shadow,workload,name)
    except (AionError,KeyError,TypeError,ValueError) as exc:
        return {"workload":workload,"control":name,"classification":"unavailable","quality_valid":False,
                "outcome":"inconclusive","reason":str(exc),"run_id":run["run_id"]}
    quality_keys={"correctness","complete_samples","minimum_samples","warmups","duration","variability","drift","effective_affinity"}
    quality_valid=run.get('status')=='completed' and all(v is not False for k,v in gates["gates"].items() if k in quality_keys)
    base_hash=benchmark["configurations"]["baseline"].get("build",{}).get("binary_sha256")
    identical=bool(base_hash and base_hash==entry.get("build",{}).get("binary_sha256"))
    classification=comparison["classification"]
    if not quality_valid or not identical: outcome="inconclusive"
    elif name=="control-aa":
        outcome=("false_positive_improvement" if classification=="improvement" and comparison.get("acceptable") else
                 "unexpected_regression" if classification=="regression" else
                 "consistent_with_AA" if classification=="no_clear_change" and comparison.get("acceptable") else "inconclusive")
    else: outcome="detected_slowdown" if classification=="regression" else "missed_slowdown"
    return {"run_id":run["run_id"],"workload":workload,"control":name,"classification":classification,
            "outcome":outcome,"quality_valid":quality_valid,"identical_baseline_binary":identical,
            "gates":gates,"comparison":comparison,
            "input_seed":benchmark["measurement_case"]["args"][1],"scheduling_seed":run["settings"]["seed"],
            "session_id":(run.get("session") or {}).get("session_id"),
            "sample_ids":[f"{run['run_id']}:{workload}:{name}:{s.get('pair_id')}" for s in entry.get("samples",[])]}


def _validation_matches(validation, run, workload, benchmark):
    checked=validation.get('benchmarks',{}).get(workload,{})
    if checked.get('fingerprint')==benchmark.get('fingerprint'):
        return True
    if run.get('control_input_design')!='existing-validation-distributions-v1' or workload not in {'image','kv'}:
        return False
    # Explicit extension: identical source closure and every input/expectation is
    # already in the all-ten sanitizer/differential evidence. Never waive checks.
    sources=lambda b:sorted((p['path'],p['sha256']) for p in b.get('source_provenance',[]))
    covered={(tuple(c['args']),c['expected']) for c in checked.get('cases',[])}
    return bool(sources(checked)) and sources(checked)==sources(benchmark) and all(
        (tuple(c['args']),c['expected']) in covered for c in benchmark.get('cases',[]))


def _distributions(rows, group):
    """Descriptive summaries only; do not pool timings or change any gates."""
    summaries=[s for row in rows for key in ('paired_baseline_summary','paired_candidate_summary')
               if (s:=row.get('comparison',{}).get(key))]
    def describe(values):
        values=sorted(v for v in values if isinstance(v,(int,float)) and math.isfinite(v))
        if not values:return {'count':0,'minimum':None,'median':None,'maximum':None}
        return {'count':len(values),'minimum':values[0],'median':statistics.median(values),'maximum':values[-1],
                'values':values,'scope':'descriptive distribution of per-comparison summaries; dependent observations'}
    samples=[s for run in group for b in run['benchmarks'].values() for e in b['configurations'].values() for s in e.get('samples',[])]
    durations=[(s.get('measurement') or {}).get('compute_seconds') for s in samples]
    return {'cv':describe([s.get('coefficient_of_variation') for s in summaries]),
            'drift':describe([s.get('drift_fraction') for s in summaries]),
            'drifting_summary_count':sum(s.get('drifting') is True for s in summaries),
            'duration_seconds':describe(durations),
            'measured_executions':len(samples),'correct_executions':sum(s.get('passed') is True for s in samples),
            'target_band_executions':sum(isinstance(d,(int,float)) and .25<=d<=.5 for d in durations)}


def build_quality_report(runs: list[dict], *, paths=None, validation=None, validation_path=None) -> dict:
    if not runs: raise AionError("Quality assessment needs at least one saved control run.")
    if len({r["run_id"] for r in runs})!=len(runs): raise AionError("Duplicate runs cannot increase the control sample count.")
    for run in runs:
        if not is_control_run(run) or run.get("evidence_kind","primary-timing")!="primary-timing":
            raise AionError("Measurement-quality studies require saved A/A and slowdown control runs.")
    groups=[]
    for run in runs:
        group=next((g for g in groups if compare_run_compatibility(g[0],run)["compatible"] and _design(g[0])==_design(run)),None)
        if group is None: groups.append([run])
        else: group.append(run)
    result=evidence_header("measurement-quality")
    result.update(strata=[],source_results=[{"run_id":r["run_id"],"path":str(p.resolve()) if p else None,
          "sha256":file_sha256(p) if p else None} for r,p in zip(runs,paths or [None]*len(runs))],
          pooling="disabled: no timing samples or effect estimates are pooled; outcome counts are stratified by compatible environment/design",
          uncertainty_caveat="Intervals describe observed control outcomes using a binomial approximation, not a universal false-positive rate. Workloads and runs within sessions are correlated.")
    for index,group in enumerate(groups):
        rows=[_row(r,w,name) for r in group for w in r["benchmarks"] for name in ("control-aa","control-slowdown")]
        aa=[r for r in rows if r["control"]=="control-aa"]
        negative=[r for r in rows if r["control"]=="control-slowdown"]
        sessions=sorted({r["session"]["session_id"] for r in group if r.get("session",{}).get("session_id")})
        seeds=sorted({r["settings"]["seed"] for r in group})
        input_seeds=sorted({r["input_seed"] for r in rows if "input_seed" in r})
        enough=len(sessions)>=2 and len(seeds)>=2 and len(input_seeds)>=2 and all(sum(r.get("session",{}).get("session_id")==s for r in group)>=2 for s in sessions)
        counts=Counter(r["outcome"] for r in rows)
        stable=all(r.get('host_end') and r['host_start'].get('host_fingerprint')==r['host_end'].get('host_fingerprint')
            and stable_environment_controls(r['host_start'])==stable_environment_controls(r['host_end']) for r in group)
        passed=enough and stable and all(r["outcome"] in {"consistent_with_AA","detected_slowdown"} for r in rows)
        quality_aa=[r for r in aa if r["quality_valid"]]
        quality_negative=[r for r in negative if r["quality_valid"]]
        def n(label,rs):return sum(r["outcome"]==label for r in rs)
        result["strata"].append({"stratum":index,"host_fingerprint":group[0].get("host_start",{}).get("host_fingerprint"),
            "environment_classification":group[0].get("host_start",{}).get("environment_classification","legacy-unclassified"),
            "requested_cpus":group[0].get("execution_controls",{}).get("requested_cpus"),
            "run_ids":[r["run_id"] for r in group],"session_ids":sessions,"scheduling_seeds":seeds,"input_seeds":input_seeds,
            "cross_session_design_complete":enough,"measurement_quality_checks_passed":passed,"outcome_counts":dict(counts),"rows":rows,
            "observed_static_environment_stable":stable,
            "descriptive_distributions":_distributions(rows,group),
            "rates":{"aa_false_positive_all":descriptive_rate(n("false_positive_improvement",aa),len(aa)),
                     "aa_false_positive_quality_valid":descriptive_rate(n("false_positive_improvement",quality_aa),len(quality_aa)),
                     "slowdown_detected_all":descriptive_rate(n("detected_slowdown",negative),len(negative)),
                     "slowdown_detected_quality_valid":descriptive_rate(n("detected_slowdown",quality_negative),len(quality_negative)),
                     "inconclusive_all":descriptive_rate(n("inconclusive",rows),len(rows))},
            "environment_observations":[{"run_id":r["run_id"],"start":r.get("host_start"),"end":r.get("host_end")} for r in group]})
    valid=bool(validation and validation.get("evidence_kind")=="sanitizer-validation" and validation.get("status")=="passed"
               and len(validation.get("benchmarks",{}))==10 and all(set(b["modes"])>={"address","undefined","differential-o3"} for b in validation["benchmarks"].values()))
    native=any(r.get("host_start",{}).get("environment_classification")=="native-linux" and r.get("status")=="completed"
               and any(e.get("samples") for b in r["benchmarks"].values() for e in b["configurations"].values()) for r in runs)
    quality=bool(result["strata"]) and all(s["measurement_quality_checks_passed"] for s in result["strata"])
    for stratum,group in zip(result["strata"],groups):
        stratum["validation_compatible"] = bool(valid and all(
            validation.get("host_start",{}).get("host_fingerprint")==r.get("host_start",{}).get("host_fingerprint")
            and validation.get("compiler")==r.get("compiler")
            and all((validation.get('build_provenance') or {}).get(k)==(r.get('build_provenance') or {}).get(k)
                    for k in ('compiler_binary_sha256','linker_binary_sha256','cxx_library_sha256'))
            and all(_validation_matches(validation,r,w,b) for w,b in r["benchmarks"].items()) for r in group))
    valid=valid and all(s["validation_compatible"] for s in result["strata"])
    result["readiness"]={"validation_passed_on_available_environment":valid,"native_linux_evidence_available":native,
        "measurement_quality_checks_passed":quality,"assessment":"measurement-quality checks passed for these tested controls" if valid and quality else "measurement environment not yet validated",
        "native_linux_control_study_passed":any(s["environment_classification"]=="native-linux" and s["measurement_quality_checks_passed"] and s["validation_compatible"] for s in result["strata"]),
        "native_linux_performance_validated":None if native else False,
        "native_linux_performance_status":"Full independent ten-workload native timing must be assessed separately; control-only reports cannot certify it." if native else "pending: no native Linux measurements in this study",
        "insufficient_or_inconclusive_evidence":not (valid and quality),
        "note":"Readiness is scoped to selected control workloads, hosts, placements, sessions and inputs. It is not proof of a universal error rate or blanket permission for AI optimization."}
    result["validation_evidence"]={"run_id":validation.get("run_id"),"path":str(validation_path.resolve()) if validation_path else None,
        "sha256":file_sha256(validation_path) if validation_path else None} if validation else None
    return result
