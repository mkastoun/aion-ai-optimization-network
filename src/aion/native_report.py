"""Assess separate native replication sessions without pooling."""
from pathlib import Path
import uuid

from .benchmarks import load_benchmarks
from .engine import candidate_assessment,comparison_for,gate_outcomes
from .errors import AionError
from .provenance import file_sha256
from .quality import build_quality_report,is_control_run
from .reproducibility import compare_run_compatibility,stable_environment_controls
from .storage import read_json


def replication_report(stores):
    paths=[p for root in stores for p in sorted((root/'results').glob('*.json'))]
    runs=[read_json(p) for p in paths]
    controls=[(p,r) for p,r in zip(paths,runs) if is_control_run(r)]
    validations=[(p,r) for p,r in zip(paths,runs) if r.get('evidence_kind')=='sanitizer-validation' and len(r.get('benchmarks',{}))==10]
    if not controls or not validations:raise AionError('Replication report needs saved controls and all-ten validation.')
    validation_path,validation=validations[-1]
    quality=build_quality_report([r for p,r in controls],paths=[p for p,r in controls],validation=validation,validation_path=validation_path)
    timings=[r for r in runs if r.get('evidence_kind','primary-timing')=='primary-timing' and not is_control_run(r) and len(r.get('benchmarks',{}))==10]
    pairs=[]
    required={b.name for b in load_benchmarks()}
    for first in timings:
        if first.get('purpose')=='independent_confirmation':continue
        for second in timings:
            if second.get('purpose')!='independent_confirmation':continue
            compatibility=compare_run_compatibility(first,second)
            reasons=list(compatibility['reasons'])
            if not compatibility['different_sessions']:reasons.append('separate observation windows missing')
            if any(not r.get('session',{}).get('native_host_note') for r in (first,second)):
                reasons.append('operator physical-host and observation-window documentation missing')
            if first['settings']['seed']==second['settings']['seed']:reasons.append('different scheduling seeds missing')
            if set(first['benchmarks'])!=required or set(second['benchmarks'])!=required:reasons.append('all ten workloads required')
            if any(r['host_start'].get('environment_classification')!='native-linux' for r in (first,second)):
                reasons.append('unsupported environment: native bare-metal evidence pending')
            if first['created_at']>=second['created_at']:reasons.append('confirmation must follow discovery')
            if (first.get('host_end',{}).get('observed_at') or 'z') >= second.get('host_start',{}).get('observed_at',''):
                reasons.append('observation intervals overlap or end/start timestamps are missing')
            if any(stable_environment_controls(r['host_start'])!=stable_environment_controls(r.get('host_end')) for r in (first,second)):
                reasons.append('observed static conditions changed')
            for w in required:
                if first['benchmarks'][w]['measurement_case']['args'][1]==second['benchmarks'][w]['measurement_case']['args'][1]:
                    reasons.append(f'held-out input missing: {w}')
            names={c['name'] for c in first['configurations']} & {c['name'] for c in second['configurations']} - {'baseline'}
            if not {'o2','lto','pgo','pgo-lto'}<=names:reasons.append('full O3/O2/LTO/PGO/PGO-LTO comparisons missing')
            outcomes=[]
            for name in sorted(names):
                estimates=[]
                for run in (first,second):
                    for w in required:
                        try:
                            c=comparison_for(run,w,name)
                            b=run['benchmarks'][w]
                            view={**run,'benchmarks':{**run['benchmarks'],w:{**b,'configurations':{**b['configurations'],name:{**b['configurations'][name],'comparison':c}}}}}
                            g=gate_outcomes(view,w,name)
                            quality_keys={'correctness','complete_samples','minimum_samples','warmups','duration','variability','drift','effective_affinity'}
                            if any(v is False for k,v in g['gates'].items() if k in quality_keys):reasons.append(f'measurement quality failed: {run["run_id"]}/{w}/{name}')
                            estimates.append({'run_id':run['run_id'],'workload':w,'comparison':c,'gates':g})
                        except (AionError,KeyError,TypeError):reasons.append(f'incomplete comparison: {w}/{name}')
                outcomes.append({'candidate':name,'estimates':estimates,'discovery_assessment':candidate_assessment(first,name,performance_only=True),
                                 'confirmation_assessment':candidate_assessment(second,name,performance_only=True)})
            if not quality['readiness']['native_linux_control_study_passed']:reasons.append('native control quality not validated')
            matching_controls=[r for p,r in controls if all(
                r.get('compiler')==t.get('compiler') and r.get('build_provenance')==t.get('build_provenance')
                and r.get('host_start',{}).get('host_fingerprint')==t.get('host_start',{}).get('host_fingerprint')
                and r.get('execution_controls')==t.get('execution_controls') for t in (first,second))]
            if not matching_controls:reasons.append('controls do not match timing host/build/placement')
            else:
                matched_quality=build_quality_report(matching_controls,validation=validation)
                if not matched_quality['readiness']['measurement_quality_checks_passed'] or not matched_quality['readiness']['native_linux_control_study_passed']:
                    reasons.append('matched control strata contain incomplete or inconclusive quality evidence')
            if not quality['readiness']['validation_passed_on_available_environment']:reasons.append('all-ten compatible sanitizers not validated')
            pairs.append({'run_ids':[first['run_id'],second['run_id']],'compatible':compatibility,'validated':not reasons,
                          'failed_gates':sorted(set(reasons)),'outcomes':outcomes})
    return {'schema_version':1,'evidence_kind':'native-replication-report','run_id':'native-report-'+uuid.uuid4().hex,
            'status':'completed','promotion_eligible':False,'quality':quality,'pairs':pairs,
            'native_performance_validated':bool(pairs) and any(p['validated'] for p in pairs),
            'native_status':'validated for the recorded conditions' if any(p['validated'] for p in pairs) else 'pending: no qualifying independent native pair',
            'source_results':[{'path':str(p.resolve()),'sha256':file_sha256(p)} for p in paths],
            'pooling':'disabled; per-session estimates and compatibility boundaries remain separate',
            'operator_requirement':'Native classification is observational. Operator must verify physical host ownership, genuinely separate sessions and documented conditions.'}


def render_native(run):
    lines=['# AION native replication','',f"Native performance validated: **{run['native_performance_validated']}**. {run['native_status']}",'',run['pooling'],run['operator_requirement'],'']
    for pair in run['pairs']:
        lines += [f"Pair: {pair['run_ids']}; validated: {pair['validated']}",'',*[f'- {reason}' for reason in pair['failed_gates']],'']
    return '\n'.join(lines)+'\n'
