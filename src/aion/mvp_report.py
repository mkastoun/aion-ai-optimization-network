"""Honest JSON, Markdown and standalone HTML reports for the engineering preview."""
from dataclasses import asdict
import html
from pathlib import Path

from .errors import AionError
from .mvp_catalog import MVP_CATALOG
from .provenance import file_sha256
from .research import assess_pair,load_attempts,now
from .storage import atomic_json,read_json

NO_WINNER='No independently verified improvement found.'


def read_stage(job,name):
    stage=next((s for s in job.get('stages',[]) if s['name']==name),None)
    if not stage or not stage.get('evidence_path'):return None
    path=Path(stage['evidence_path'])
    if file_sha256(path)!=stage['evidence_sha256']:raise AionError('MVP stage evidence changed; report refuses to trust it.')
    return read_json(path)


def build_report(job):
    plan=job['plan'];catalog={p.name:p for p in MVP_CATALOG}
    validation=read_stage(job,'separate correctness validation')
    discovery=read_stage(job,'discovery');confirmation=read_stage(job,'confirmation')
    runs_a=load_attempts(discovery) if discovery else {};runs_b=load_attempts(confirmation) if confirmation else {}
    rows=[];correct=job['status']=='completed' and validation is not None and validation.get('status')=='passed'
    for decision in plan['decisions']:
        if not decision['selected']:continue
        proposal=decision['proposal'];name=proposal['panel_id'];panel=catalog[name]
        row={'panel_id':name,'proposal':proposal,'proposal_rank':decision['rank'],'reference':asdict(panel.reference),
             'candidate':asdict(panel.candidate),'status':'Inconclusive','correctness_passed':False,
             'observations':[],'raw_evidence':[],'independent_local_signal':False,'scientifically_verified':False}
        first,second=runs_a.get(name),runs_b.get(name)
        for role,run in (('discovery',first),('confirmation',second)):
            if run:
                b=next(iter(run['benchmarks'].values()))
                row['raw_evidence'].append({'role':role,'run_id':run['run_id'],'environment':run['host_start']['environment_classification'],
                    'session':run['session'],'compiler':run['compiler'],'build_provenance':run['build_provenance'],
                    'input':b['measurement_case'],'configurations':{n:{k:e.get(k) for k in ('status','build','verification','calibration')} for n,e in b['configurations'].items()}})
        if first and second:
            assessment=assess_pair(first,second);row.update(compatible=assessment['compatible'],compatibility_reasons=assessment['reasons'])
            row['observations']=[{'role':role,**o} for role,o in zip(('discovery','confirmation'),assessment['observations'])]
            row['correctness_passed']=all((e.get('verification') or {}).get('passed') is True and all(s.get('passed') is True for s in e.get('samples',[]))
                for run in (first,second) for b in run['benchmarks'].values() for e in b['configurations'].values())
            comparisons=[o.get('comparison',{}) for o in row['observations']]
            valid=assessment['compatible'] and all(o['valid'] for o in row['observations'])
            if valid and all(c.get('classification')=='regression' for c in comparisons):row['status']='Regression detected'
            elif valid and all(c.get('classification')=='improvement' for c in comparisons):
                row.update(status='Exploratory performance signal',independent_local_signal=True)
            elif valid and all(c.get('acceptable') and c.get('classification')=='no_clear_change' for c in comparisons):row['status']='Quality-valid local comparison'
        if not row['correctness_passed']:
            correct=False
            row['failure']='Correctness or complete independent execution is not established for both arms and roles.'
        rows.append(row)
    environments=sorted({e['environment'] for r in rows for e in r['raw_evidence']})
    validation_summary=None
    if validation:
        modes=[m for b in validation['benchmarks'].values() for m in b['modes'].values()]
        validation_summary={'status':validation['status'],'builds':len(modes),'checks':sum(len(m['checks']) for m in modes),
                            'passed':sum(c['passed'] for m in modes for c in m['checks']),
                            'compiler':validation['compiler'],'source_evidence':next(s['evidence_path'] for s in job['stages'] if s['name']=='separate correctness validation')}
    return {'schema_version':1,'evidence_kind':'mvp-report','milestone':job['milestone'],'run_id':job['run_id'],
        'created_at':now(),'status':job['status'],'headline':NO_WINNER,'workload_id':plan['workload_id'],
        'requested_strategy':plan['requested_strategy'],'actual_strategy':plan['actual_strategy'],'ai_usage':plan['ai_usage'],
        'plan_sha256':plan['plan_sha256'],'declaration_sha256':plan['declaration_sha256'],
        'implementation_status':'Implementation validated' if job['status']=='completed' else 'Execution incomplete or failed',
        'correctness_status':'Correctness passed' if correct else 'Correctness incomplete or failed',
        'measurement_environment_validated':False,'native_scientific_validation':'Native scientific validation pending',
        'phase6_scientific_ready':False,'promotion_eligible':False,'verified_winner':None,
        'environments':environments,'proposals':plan['decisions'],'candidates':rows,'validation':validation_summary,
        'family_comparisons':len(MVP_CATALOG),
        'budgets':{'planning':plan['planning_budget'],'execution':job.get('budget')},
        'stages':job['stages'],'error':job.get('error'),
        'evidence':{'plan':job['plan_path'],'plan_file_sha256':job['plan_file_sha256'],
                    'discovery_run_id':discovery['run_id'] if discovery else None,'confirmation_run_id':confirmation['run_id'] if confirmation else None},
        'limitations':['Engineering preview, not completed Phase 6 scientific validation.',
            'WSL2, virtual machines and local quality gates do not establish native or universal speedups.',
            'A demo does not run or validate a new measurement-control study. Environment readiness remains unvalidated.',
            'Separate automatic observation windows and held-out seeds do not prove independent physical host conditions.',
            'No raw timings or effects are pooled. Proposal order is an exploratory question ranking, not a verified winner.',
            'Finite independent cases and sanitizers do not prove general source equivalence.',
            'Bootstrap intervals are empirical and family-adjusted; short dependent series and nonstationarity limit coverage.',
            'Imported model identity and external use of other information cannot be authenticated by AION.',
            'No provider is contacted, model code executed, source rewritten, or production preset promoted.']}


def _text(value):return str(value).replace('|','\\|').replace('\n',' ')


def _estimate(observation):
    c=observation.get('comparison') or {};u=c.get('uncertainty') or {}
    if not u:return 'not measured'
    return f"{100*u['paired_improvement_fraction']:+.3f}% [{100*u['improvement_ci_low']:+.3f}, {100*u['improvement_ci_high']:+.3f}]"


def recipe_text(recipe):
    return ' '.join(recipe['flags'])+'; '+recipe['variant']+'; '+recipe['mode']


def render_markdown(report):
    if report['evidence_kind']=='mvp-plan':
        return '\n'.join(['# '+report['milestone']+' plan','',f"Workload: {report['workload_id']}; actual strategy: {report['actual_strategy']}.",
            f"Plan fingerprint: `{report['plan_sha256']}`.",'',*[f"- {d['rank']}. {d['proposal']['panel_id']}: {d['decision']} — {_text(d['proposal']['reason'])}" for d in report['decisions']],
            '', 'Selected IDs are frozen before discovery. Inspect this plan and execute with --approve.',''])
    lines=['# '+report['milestone'],'','**'+report['headline']+'**','',
        f"Workload: **{report['workload_id']}**. Functionality: **{report['implementation_status']}**. Correctness: **{report['correctness_status']}**.",
        f"Requested strategy: {report['requested_strategy']}; actual strategy: **{report['actual_strategy']}**; external AI proposals used: **{report['ai_usage']['used']}**.",
        f"AION model API call: **{report['ai_usage']['model_called_by_aion']}**. {_text(report['ai_usage'].get('fallback_reason') or report['ai_usage'].get('authentication','Deterministic heuristic; not an AI model.'))}",
        f"External proposal provenance: {_text(report['ai_usage'].get('provenance') or 'none')}.",
        '',f"Environments: {', '.join(report['environments']) or 'execution did not reach timing'}. **{report['native_scientific_validation']}**. Phase 6 ready: **False**. Production preset promotion: **disabled**.",
        '', '## Candidate comparison','', f"Paired gain and family-adjusted empirical interval across {report['family_comparisons']} approved comparisons; positive means faster than that row's reference. Discovery and confirmation estimates remain separate. Different reference recipes are not interchangeable baselines.",'',
        '| Candidate | Reference → treatment | Discovery gain [interval] | Confirmation gain [interval] | Result |',
        '|---|---|---:|---:|---|']
    for row in report['candidates']:
        observations={o['role']:o for o in row['observations']}
        lines.append(f"| {row['panel_id']} | {_text(recipe_text(row['reference']))} → {_text(recipe_text(row['candidate']))} | {_estimate(observations.get('discovery',{}))} | {_estimate(observations.get('confirmation',{}))} | {row['status']} |")
    for row in report['candidates']:
        for obs in row['observations']:
            lines.append(f"\n{row['panel_id']} / {obs['role']} failed gates: {', '.join(obs.get('failed_gates',[])) or 'none'}. Raw classification: {obs.get('comparison',{}).get('classification','unavailable')}.")
    lines += ['', '## Proposed experiments and selection','', '| Rank | Panel | Decision | Rationale |','|---:|---|---|---|']
    for d in report['proposals']:lines.append(f"| {d['rank']} | {d['proposal']['panel_id']} | {d['decision']} | {_text(d['proposal']['reason'])} |")
    lines += ['', '## Correctness, budgets and provenance','',f"Separate validation: `{report['validation']}`."]
    for name,budget in report['budgets'].items():
        if budget:lines.append(f"{name}: {budget['commands_used']}/{budget['maximum_commands']} logical commands; {budget['elapsed_seconds']:.2f}/{budget['maximum_seconds']:.0f} elapsed seconds. Nested role commands also count against the global execution budget.")
    for row in report['candidates']:
        for evidence in row['raw_evidence']:
            lines += ['',f"{row['panel_id']} / {evidence['role']}: `{evidence['run_id']}`; compiler `{evidence['compiler']['version']}`; target `{evidence['compiler']['target']}`."]
            for name,e in evidence['configurations'].items():
                build=e.get('build') or {};source=build.get('research') or {};pgo=build.get('pgo') or {}
                lines.append(f"- {name}: status {e['status']}; correctness {(e.get('verification') or {}).get('passed')}; executable SHA-256 `{build.get('binary_sha256')}`; source fingerprint `{source.get('variant_fingerprint')}`; PGO profile `{pgo.get('profile_sha256','not applicable')}`.")
    if report.get('error'):lines += ['',f"Execution error: {_text(report['error'])}"]
    lines += ['',f"Plan SHA-256: `{report['plan_sha256']}`. Declaration: `{report['declaration_sha256']}`.",
              'Complete source/build/input/training identities, commands, failures and uncertainty are retained in report.json and linked raw research evidence.','',
              '## Limitations','',*[f'- {s}' for s in report['limitations']],'']
    return '\n'.join(lines)


def render_html(report):
    escape=lambda value:html.escape(str(value),quote=True)
    rows=[]
    for row in report['candidates']:
        observations={o['role']:o for o in row['observations']}
        failed='; '.join(o['role']+': '+(', '.join(o.get('failed_gates',[])) or 'none') for o in row['observations'])
        rows.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in (row['panel_id'],recipe_text(row['reference'])+' → '+recipe_text(row['candidate']),
            _estimate(observations.get('discovery',{})),_estimate(observations.get('confirmation',{})),row['status'],failed))+'</tr>')
    proposal_rows=''.join('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in (d['rank'],d['proposal']['panel_id'],d['decision'],d['proposal']['reason']))+'</tr>' for d in report['proposals'])
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>AION 0.6 MVP Preview — local report</title><style>
:root{color-scheme:light dark;font:16px/1.5 system-ui,sans-serif;background:#101723;color:#e5edf5}body{max-width:1280px;margin:40px auto;padding:0 24px}h1{font-size:36px;margin-bottom:8px}h2{margin-top:36px}a{color:#8acbff}.notice{border-left:5px solid #e5b95c;background:#29303a;padding:20px}.cards{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}.card{flex:1;min-width:190px;border:1px solid #45546a;border-radius:10px;padding:16px}.card small{display:block;color:#a9bacd}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:12px;border-bottom:1px solid #45546a;text-align:left;vertical-align:top}th{background:#202d40}pre{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid #45546a;padding:18px;border-radius:8px;font-size:13px}.muted{color:#a9bacd}footer{margin-top:36px;padding-top:20px;border-top:1px solid #45546a}
</style><main><p class="muted">LOCAL ENGINEERING PREVIEW</p><h1>'''+escape(report['milestone'])+'''</h1><p>Workload: <strong>'''+escape(report['workload_id'])+'''</strong></p><div class="notice"><strong>'''+escape(report['headline'])+'''</strong><br>Native scientific validation is pending. Research cannot create production presets.</div><div class="cards">'''+''.join('<div class="card"><small>'+escape(k)+'</small><strong>'+escape(v)+'</strong></div>' for k,v in (
        ('Functionality',report['implementation_status']),('Correctness',report['correctness_status']),('Strategy',report['actual_strategy']),('AI proposals used',report['ai_usage']['used'])))+'''</div><p>'''+escape(report['ai_usage'].get('fallback_reason') or report['ai_usage'].get('authentication') or 'Deterministic offline heuristic; no model used.')+''' AION model API call: '''+escape(report['ai_usage']['model_called_by_aion'])+'''.</p><h2>Candidate comparison</h2><p>Paired gain and empirical family-adjusted interval. Positive means faster than the listed reference. These are separate local estimates, not a verified winner.</p><div class="scroll"><table><thead><tr><th>Candidate</th><th>Reference → treatment</th><th>Discovery</th><th>Confirmation</th><th>Status</th><th>Failed gates</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></div><h2>Proposal ranking</h2><p>This order ranks research questions before measurement. It does not select a scientific winner.</p><div class="scroll"><table><tr><th>Rank</th><th>Panel</th><th>Decision</th><th>Rationale</th></tr>'''+proposal_rows+'''</table></div><h2>Detailed validation, provenance and limits</h2><pre>'''+escape(render_markdown(report))+'''</pre><footer>Offline report. No scripts, external resources or provider requests. Full machine-readable evidence: <a href="report.json">report.json</a>.</footer></main></html>'''


def write_reports(prefix,report):
    prefix=Path(prefix);atomic_json(prefix.with_suffix('.json'),report)
    prefix.with_suffix('.md').write_text(render_markdown(report),encoding='utf-8')
    prefix.with_suffix('.html').write_text(render_html(report),encoding='utf-8')
