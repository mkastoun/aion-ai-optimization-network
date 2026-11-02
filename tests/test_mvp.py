"""Preview safety fixtures; synthetic samples never become demo evidence."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys

import pytest

from aion.budget import ResearchBudget,bounded
from aion.errors import AionError
from aion.mvp import create_plan,check_plan,run_plan,seal
from aion.mvp_catalog import MVP_CATALOG,available,manifest
from aion.mvp_context import export_context
from aion.mvp_proposals import deterministic,rank,validate_ai,read_proposals
from aion.mvp_report import build_report,render_html,render_markdown,NO_WINNER
from aion.process import run_process
from aion.provenance import file_sha256
from aion.registry import PresetRegistry
from aion.research_catalog import CATALOG,digest
from aion.storage import atomic_json,read_json
from tests.helpers import process,INFO
from tests.test_control_experiments import FileFixtureAdapter
from tests.test_reliable_benchmarking import synthetic_run


def ai_payload(context,workload='array'):
    return {'schema_version':1,'evidence_kind':'mvp-proposals','context_sha256':context['context_sha256'],
            'provenance':{'kind':'external-llm','origin':'coding-assistant','provider':'Synthetic fixture',
                          'model':'fixture-not-a-real-model','generated_at':'2026-10-31T00:00:00+00:00','evidence_scope':'discovery-only'},
            'proposals':[{'workload_id':workload,'panel_id':available(workload)[0].name,
                          'reason':'Test the approved compiler policy as a hypothesis.','priority':1,'estimated_cost':None}]}


@pytest.fixture
def fake_compiler():
    adapter=FileFixtureAdapter()
    with patch('aion.research.ClangAdapter',return_value=adapter),patch('aion.mvp.ClangAdapter',return_value=adapter):
        yield adapter


def validation_result(status='passed'):
    return {'schema_version':1,'evidence_kind':'sanitizer-validation','status':status,'compiler':asdict(INFO),
        'benchmarks':{'synthetic':{'modes':{mode:{'checks':[{'passed':status=='passed'}],'status':status}
                     for mode in ('address','undefined','differential-o3')}}}}


def test_catalog_all_ten_and_original_family_preserved():
    assert len(CATALOG)==17 and len(MVP_CATALOG)==31
    assert len({p.name for p in MVP_CATALOG})==31
    from aion.benchmarks import load_benchmarks
    assert all(available(b.name) for b in load_benchmarks())
    assert manifest()['family_comparisons']==31
    assert all(manifest()['files'].values())


def test_deterministic_ranking_is_offline_reproducible_bounded_and_honest():
    first=rank(deterministic('records',77),77,2)
    assert first==rank(deterministic('records',77),77,2)
    assert [d['proposal']['panel_id'] for d in first if d['selected']]==['records-lto','records-branchless']
    assert len(first)==7 and sum(d['selected'] for d in first)==2
    assert all(d['proposal']['provenance']['kind']=='deterministic' for d in first)
    for maximum in (0,5,True):
        with pytest.raises(AionError):rank(deterministic('records',77),77,maximum)


def test_equal_priorities_have_seeded_stable_tie_breaks():
    proposals=deterministic('matrix',5)
    for p in proposals:p['priority']=1;p['estimated_cost']=None
    assert rank(proposals,5,2)==rank(list(reversed(proposals)),5,2)
    assert {d['proposal']['panel_id'] for d in rank(proposals,5,4)}=={d['proposal']['panel_id'] for d in rank(proposals,6,4)}


def test_ai_valid_data_stays_data_and_gets_per_proposal_provenance():
    context,_=export_context('array');payload=ai_payload(context)
    result=validate_ai(payload,'array',context['context_sha256'])
    assert len(result)==1 and result[0]['provenance']['kind']=='external-llm'
    assert 'not authenticated' in result[0]['provenance']['authenticity']


@pytest.mark.parametrize('mutation',[
    lambda p:p.update(command='whoami'),
    lambda p:p['proposals'][0].update(flags=['-ffast-math']),
    lambda p:p['proposals'][0].update(source='/tmp/evil.cpp'),
    lambda p:p['proposals'][0].update(llvm_passes='default<O3>'),
    lambda p:p['proposals'][0].update(panel_id='records-lto'),
    lambda p:p['proposals'][0].update(panel_id='array-o2;whoami'),
    lambda p:p['proposals'][0].update(reason='__import__("os").system("whoami")'),
    lambda p:p['proposals'][0].update(reason='<script>alert(1)</script>'),
    lambda p:p['proposals'][0].update(reason='Use -ffast-math'),
    lambda p:p['proposals'][0].update(reason='A guaranteed verified improvement'),
    lambda p:p['proposals'][0].update(priority=True),
    lambda p:p['proposals'][0].update(estimated_cost={'commands':10,'seconds':float('nan')}),
    lambda p:p['proposals'].append(deepcopy(p['proposals'][0])),
    lambda p:p.update(context_sha256='wrong'),
    lambda p:p['provenance'].update(evidence_scope='confirmation'),
    lambda p:p['provenance'].update(origin=[]),
    lambda p:p['proposals'][0].update(reason='invalid unicode \ud800'),
])
def test_malicious_or_invalid_ai_outputs_are_rejected(mutation):
    context,_=export_context('array');payload=ai_payload(context);mutation(payload)
    with pytest.raises(AionError):validate_ai(payload,'array',context['context_sha256'])


def test_json_rejects_duplicate_keys_nonfinite_and_oversized(tmp_path):
    path=tmp_path/'data.json'
    for content in ('{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}', ' '*65537):
        path.write_text(content)
        with pytest.raises(AionError):read_proposals(path)


def test_missing_provider_fallback_is_explicit_and_never_ai(tmp_path,fake_compiler):
    path=create_plan(tmp_path/'plan','array',strategy='auto',cpus='none')
    plan,declaration=check_plan(path)
    assert plan['actual_strategy']=='deterministic' and not plan['ai_usage']['used']
    assert 'AI unavailable' in plan['ai_usage']['fallback_reason']
    assert declaration['catalog_provider']=='mvp-preview-v1' and declaration['catalog']['family_comparisons']==31
    plan['ai_usage']['used']=True;atomic_json(path,seal(plan))
    with pytest.raises(AionError,match='labeled'):check_plan(path)


def test_imported_ai_and_context_fingerprint_round_trip(tmp_path,fake_compiler):
    context,_=export_context('array');contextpath=tmp_path/'context.json';atomic_json(contextpath,context)
    external=tmp_path/'ai.json';atomic_json(external,ai_payload(context))
    path=create_plan(tmp_path/'plan','array',strategy='ai-import',proposals_path=external,context_path=contextpath,cpus='none')
    plan,_=check_plan(path)
    assert plan['actual_strategy']=='ai-import' and plan['ai_usage']['used'] and not plan['ai_usage']['model_called_by_aion']
    external_copy=path.parent/'imported-proposals.json';external_copy.write_text('{}')
    with pytest.raises(AionError,match='bytes changed'):check_plan(path)


def test_rejected_ai_receipt_and_payload_are_retained(tmp_path):
    context,_=export_context('array');payload=ai_payload(context);payload['command']='whoami'
    external=tmp_path/'bad.json';atomic_json(external,payload)
    directory=tmp_path/'rejected'
    with pytest.raises(AionError):create_plan(directory,'array',strategy='ai-import',proposals_path=external,cpus='none')
    assert read_json(directory/'planning.json')['status']=='rejected'
    assert (directory/'imported-proposals.json').read_bytes()==external.read_bytes()
    assert not (directory/'declaration.json').exists()


def test_budget_is_global_across_nested_stage_budgets():
    overall=ResearchBudget(2,10);child=ResearchBudget(10,100)
    with bounded(overall):
        with bounded(child),patch('aion.process._run_process',return_value=process()):
            run_process(['fixture']);run_process(['fixture'])
            with pytest.raises(AionError,match='exhausted'):run_process(['never launched'])
    assert len(overall.attempts)==len(child.attempts)==2
    assert overall.attempts[0] is child.attempts[0]
    assert overall.attempts[0]['status']=='completed'


def test_selection_and_budget_tampering_are_refused(tmp_path,fake_compiler):
    path=create_plan(tmp_path/'plan','array',cpus='none');plan,_=check_plan(path)
    altered=deepcopy(plan);altered['selected_panels']=['logs-pgo'];atomic_json(path,seal(altered))
    with pytest.raises(AionError):check_plan(path)
    altered=deepcopy(plan);altered['total_execution_budget']['commands']=10000;atomic_json(path,seal(altered))
    with pytest.raises(AionError,match='budgets'):check_plan(path)


def test_confirmation_leakage_and_sensitive_export_are_blocked(tmp_path):
    raw=synthetic_run(seed=1,purpose='independent_confirmation');raw['evidence_kind']='research-timing'
    path=tmp_path/'confirmation.json';atomic_json(path,raw)
    with pytest.raises(AionError,match='confirmation'):export_context('array',prior_paths=[path])
    panel=next(p for p in MVP_CATALOG if p.name=='array-o2')
    raw=synthetic_run(seed=2,purpose='research_discovery');raw.update(evidence_kind='research-timing',research_panel=asdict(panel))
    raw['benchmarks']['array']['configurations']['candidate']=raw['benchmarks']['array']['configurations'].pop('o2')
    raw['private_credentials']='DO NOT EXPORT THIS';raw['benchmarks']['array']['configurations']['candidate']['process_secret']='C:/private/path'
    atomic_json(path,raw)
    context,_=export_context('array',prior_paths=[path]);encoded=json.dumps(context)
    assert 'DO NOT EXPORT' not in encoded and 'C:/private' not in encoded and str(tmp_path) not in encoded
    assert 'confirmation' not in json.dumps(context['prior_discovery_evidence'])
    raw['benchmarks']['array']['measurement_case']=raw['benchmarks']['array']['cases'][-1]
    atomic_json(path,raw)
    with pytest.raises(AionError,match='held-out'):export_context('array',prior_paths=[path])


def test_correctness_failure_stops_execution_and_reports_it(tmp_path,fake_compiler):
    path=create_plan(tmp_path/'plan','array',cpus='none')
    with patch('aion.mvp.sys',SimpleNamespace(platform='linux')),patch('aion.mvp.run_validation',return_value=validation_result('failed')),patch('aion.mvp.run_study') as study:
        job=run_plan(path,approve=True,progress=lambda _:None)
    assert job['status']=='failed' and not study.called
    report=read_json(path.parent/'report.json')
    assert report['correctness_status']=='Correctness incomplete or failed' and report['verified_winner'] is None
    assert NO_WINNER in (path.parent/'report.html').read_text()
    with pytest.raises(AionError,match='already has'):run_plan(path,approve=True)


def test_approval_required_before_any_run(tmp_path):
    with pytest.raises(AionError,match='--approve'):run_plan(tmp_path/'missing.json')


def test_wsl_labels_and_report_escaping_do_not_fabricate_winner(tmp_path,fake_compiler):
    path=create_plan(tmp_path/'plan','array',maximum=1,iterations=5,cpus='none')
    plan,_=check_plan(path);raws={}
    for role,seed in [('discovery',76000),('confirmation',76100)]:
        raw=synthetic_run(seed=seed,purpose='research_discovery' if role=='discovery' else 'independent_confirmation')
        raw.update(evidence_kind='research-timing',research_panel=asdict(next(p for p in MVP_CATALOG if p.name==plan['selected_panels'][0])),declaration_sha256=plan['declaration_sha256'],comparison_family_size=31)
        b=raw['benchmarks']['array'];b['configurations']['candidate']=b['configurations'].pop('o2')
        for records in (b['configurations']['baseline'],b['configurations']['candidate']):
            for phase in ('samples','warmups'):
                for record in records[phase]:record['pair_candidate']='candidate'
        for c in raw['configurations']:
            if c['name']=='o2':c['name']='candidate'
        raw['host_start']['environment_classification']='wsl2'
        rawpath=tmp_path/(role+'-raw.json');atomic_json(rawpath,raw)
        study={'schema_version':1,'evidence_kind':'research-study','run_id':'fixture-'+role,'status':'completed','role':role,
               'attempts':[{'panel':plan['selected_panels'][0],'result':str(rawpath),'sha256':file_sha256(rawpath)}]}
        raws[role]=study
    with patch('aion.mvp.sys',SimpleNamespace(platform='linux')),patch('aion.mvp.run_validation',return_value=validation_result()),patch(
        'aion.mvp.run_study',side_effect=lambda a,b,c,role,**kw:raws[role]):
        job=run_plan(path,approve=True,progress=lambda _:None)
    report=read_json(path.parent/'report.json')
    assert job['status']=='completed' and report['environments']==['wsl2']
    assert report['native_scientific_validation']=='Native scientific validation pending'
    assert not report['phase6_scientific_ready'] and not report['promotion_eligible'] and report['verified_winner'] is None
    assert NO_WINNER in render_markdown(report) and 'Confirmation gain' in render_markdown(report)
    report['proposals'][0]['proposal']['reason']='<script>alert(1)</script>'
    html=render_html(report)
    assert '<script>' not in html and '&lt;script&gt;' in html and 'default-src' in html
    with pytest.raises(AionError):PresetRegistry(tmp_path/'presets').register('bad','candidate',report,report)


@pytest.mark.integration
def test_real_one_command_mvp_pipeline(tmp_path):
    if sys.platform=='win32':pytest.skip('Native Windows MVP execution is unsupported; use Linux/WSL2 or macOS.')
    from aion.compiler import ClangAdapter
    try:adapter=ClangAdapter()
    except AionError as exc:
        import os
        if os.environ.get('AION_REQUIRE_COMPILER'):raise
        pytest.skip(str(exc))
    from aion.cli import main
    directory=tmp_path/'real-mvp'
    code=main(['mvp','demo','--workload','array','--max-candidates','1','--iterations','5','--warmups','1',
               '--commands','700','--seconds','300','--compiler',adapter.info.path,'--cpus','auto','--output',str(directory)])
    path=directory/'plan.json';job=read_json(directory/'job.json')
    assert code==0,job.get('error')
    assert job['status']=='completed',job.get('error')
    report=read_json(path.parent/'report.json')
    assert report['correctness_status']=='Correctness passed' and report['validation']['checks']>=30
    assert report['candidates'][0]['raw_evidence'][0]['configurations']['candidate']['build']['binary_sha256']
    assert len(report['candidates'][0]['observations'])==2
    assert report['budgets']['execution']['commands_used']<=700
    assert report['family_comparisons']==31 and NO_WINNER in (path.parent/'report.html').read_text()
