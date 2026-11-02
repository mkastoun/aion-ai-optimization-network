"""Controlled fixtures; synthetic measurements never become published evidence."""
from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import pytest

from aion.benchmarks import load_benchmarks
from aion.budget import ResearchBudget,bounded
from aion.compiler import ClangAdapter
from aion.engine import ExperimentSettings,candidate_assessment,run_experiment
from aion.errors import AionError
from aion.experiments import distribution_benchmarks
from aion.host import classify_environment
from aion.models import Candidate,Limits
from aion.process import run_process
from aion.quality import _validation_matches
from aion.registry import PresetRegistry
from aion.research import ResearchAdapter,assess_pair,check_declaration,declare,load_attempts,run_study
from aion.research_catalog import CATALOG,benchmark_for,catalog_manifest,digest,inputs,variant_benchmark
from aion.research_reference import logs_expected
from aion.storage import atomic_json,read_json
from aion.verification import measure_binary,verify_binary
from tests.helpers import process
from tests.test_control_experiments import FileFixtureAdapter,control_record


def test_catalog_is_finite_and_closed():
    manifest=catalog_manifest()
    assert len(CATALOG)==17 and len({p.name for p in CATALOG})==17
    assert manifest['family_comparisons']==17 and all(manifest['files'].values())
    for panel in CATALOG:
        benchmark=benchmark_for(panel)
        for recipe in (panel.reference,panel.candidate):
            variant=variant_benchmark(benchmark,recipe)
            assert all(p.is_file() for p in variant.source_files)
            assert set(benchmark.source_files)<=set(variant.source_files)


def test_new_log_oracle_preserves_original_and_all_distribution_expectations():
    for case in load_benchmarks('logs')[0].cases:
        assert logs_expected(*map(int,case['args']))==case['expected']
    cases=[*inputs()['validation'],*inputs()['heldout'],*[c for cases in inputs()['training'].values() for c in cases]]
    for case in cases:
        assert logs_expected(*map(int,case['args']))==case['expected']


def test_budget_counts_failures_caps_timeout_and_stops_before_launch():
    budget=ResearchBudget(1,5)
    with bounded(budget),patch('aion.process._run_process',return_value=process(code=7)) as execute:
        assert not run_process(['fixture'],Limits(timeout_seconds=60)).ok
        assert execute.call_args.args[1].timeout_seconds<=5
        with pytest.raises(AionError,match='budget exhausted'):run_process(['second'])
    assert len(budget.attempts)==1 and budget.attempts[0]['result']['returncode']==7


def test_budget_restores_context_after_exception():
    with pytest.raises(RuntimeError),bounded(ResearchBudget(1,5)),patch('aion.process._run_process',side_effect=RuntimeError('fixture')):
        run_process(['fixture'])
    from aion.budget import ACTIVE
    assert ACTIVE.get() is None
    for args in [(0,3),(5,float('nan')),(5,float('inf')),(10001,1)]:
        with pytest.raises(AionError):ResearchBudget(*args)


def test_github_hosted_runner_cannot_be_native():
    with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted'}):
        assert classify_environment('linux',None,linux=True)['classification']=='virtual-machine'


def test_research_engine_preserves_gates_and_cannot_publish(tmp_path):
    adapter=FileFixtureAdapter();adapter.research_only=True
    with patch('aion.engine.verify_binary',return_value={'passed':True}),patch('aion.engine.measure_binary',side_effect=control_record):
        run=run_experiment(adapter,load_benchmarks('matrix'),[Candidate('candidate',('-O3',))],
            ExperimentSettings(iterations=7,warmups=1,bootstrap_resamples=200),research_baseline=Candidate('baseline',('-O3','-flto')),research_family_size=17)
    assert run['evidence_kind']=='research-timing' and not run['promotion_eligible']
    assert run['comparison_family_size']==17
    assert not candidate_assessment(run,'candidate')['eligible']
    with pytest.raises(AionError):PresetRegistry(tmp_path).register('research','candidate',run,run)
    run['evidence_kind']='primary-timing';run['research_panel']={'name':'fixture'}
    with pytest.raises(AionError,match='Research'):PresetRegistry(tmp_path).register('research','candidate',run,run)
    with pytest.raises(AionError):run_experiment(FileFixtureAdapter(),[],[],research_family_size=17)


def test_probe_exception_is_preserved():
    adapter=FileFixtureAdapter();adapter.probe=lambda _:(_ for _ in ()).throw(AionError('fixture probe failure'))
    partial=[]
    with pytest.raises(AionError):run_experiment(adapter,[],[],on_failure=partial.append)
    assert partial[0]['status']=='failed' and partial[0]['error']['message']=='fixture probe failure'


def test_adapter_rejects_foreign_recipes_and_source(tmp_path):
    panel=CATALOG[0];benchmark=benchmark_for(panel)
    adapter=ResearchAdapter(FileFixtureAdapter(),panel,benchmark,tmp_path)
    with pytest.raises(AionError):adapter.probe(Candidate('candidate',('-O2',)))
    with pytest.raises(AionError):adapter.compile(Path('foreign.cpp'),tmp_path/'x',panel.candidate.candidate('candidate'))


def test_distribution_controls_require_exact_source_and_checked_input_coverage():
    for benchmark in distribution_benchmarks(load_benchmarks('image,kv')):
        from aion.validation import validation_cases
        from aion.provenance import file_sha256
        original=load_benchmarks(benchmark.name)[0]
        source=[{'path':str(p),'sha256':file_sha256(p)} for p in original.source_files]
        raw={'fingerprint':benchmark.fingerprint,'cases':list(benchmark.cases),'source_provenance':source}
        validation={'benchmarks':{benchmark.name:{'fingerprint':original.fingerprint,'cases':validation_cases(original),'source_provenance':source}}}
        run={'control_input_design':'existing-validation-distributions-v1'}
        assert _validation_matches(validation,run,benchmark.name,raw)
        changed=deepcopy(raw);changed['cases'][-1]['expected']='bad'
        assert not _validation_matches(validation,run,benchmark.name,changed)
        assert not _validation_matches(validation,{},benchmark.name,raw)


@pytest.fixture
def compiler():
    try:
        adapter=ClangAdapter()
        from aion.optimization import BASELINE
        probe=adapter.probe(BASELINE)
        if not probe['supported']:raise AionError('C++ baseline probe failed: '+str(probe))
        return adapter
    except AionError as exc:
        if os.environ.get('AION_REQUIRE_COMPILER'):raise
        pytest.skip(str(exc))


@pytest.mark.integration
def test_real_variants_match_independent_cases_and_measurement_protocol(compiler,tmp_path):
    seen=set()
    for panel in CATALOG:
        for recipe in (panel.reference,panel.candidate):
            if recipe.variant=='original' or (recipe.variant,panel.distribution) in seen:continue
            seen.add((recipe.variant,panel.distribution))
            benchmark=variant_benchmark(benchmark_for(panel),recipe)
            binary=tmp_path/(recipe.variant+'-'+panel.distribution+'.exe')
            # Differential O3 testing is separate from the fixed treatment flags.
            assert compiler.compile(benchmark.compilation_input,binary,Candidate('check',('-O3',)))['success']
            assert verify_binary(binary,benchmark,Limits(timeout_seconds=30))['passed']
            assert measure_binary(binary,benchmark.case('small'),2,Limits())['passed']


@pytest.mark.integration
def test_real_measurement_path_pgo_training_and_sealed_declaration(compiler,tmp_path):
    panel=next(p for p in CATALOG if p.name=='logs-training-path')
    benchmark=benchmark_for(panel)
    # Smaller trusted input for integration speed, independent expectation retained.
    small=benchmark.case('small')
    candidate=panel.candidate.candidate('candidate')
    probe=compiler.probe(candidate)
    if not probe['supported']:pytest.skip('Optional matching PGO recipe unsupported: '+str(probe))
    build=compiler.compile_profiled(benchmark.compilation_input,tmp_path/'pgo.exe',candidate,[small],Limits(),
                                    profile_archive=tmp_path/'profile',training_measurement_batches=1)
    assert build['success'] and build['pgo']['training'][0]['passed']
    assert build['pgo']['fresh_profile'] and build['pgo']['training_path']=='measure-one-batch'
    assert (tmp_path/'profile/merged.profdata').is_file()
    path=tmp_path/'declaration.json'
    plan=declare(path,study='matrix',compiler=compiler.info.path,cpus='none')
    check_declaration(read_json(path))
    plan['settings']['iterations']=1
    with pytest.raises(AionError,match='seal'):check_declaration(plan)
    plan['declaration_sha256']=digest({k:v for k,v in plan.items() if k!='declaration_sha256'})
    with pytest.raises(AionError,match='design'):check_declaration(plan)


def test_changed_result_cannot_be_reported(tmp_path):
    path=tmp_path/'result.json';atomic_json(path,{'schema_version':1})
    with pytest.raises(AionError,match='bytes changed'):
        load_attempts({'attempts':[{'panel':'x','result':str(path),'sha256':'wrong'}]})


def test_study_retains_all_failed_attempts_and_refuses_silent_retries(tmp_path):
    from aion.sessions import new_session,save_session
    adapter=FileFixtureAdapter()
    planpath=tmp_path/'plan.json'
    sessionpath=tmp_path/'session.json';save_session(sessionpath,new_session())
    with patch('aion.research.ClangAdapter',return_value=adapter):
        declare(planpath,study='records',cpus='none')
        with patch('aion.research.run_experiment',side_effect=AionError('deliberate fixture build failure')):
            study=run_study(planpath,tmp_path/'store',sessionpath,'discovery',progress=lambda _:None)
        assert study['status']=='failed' and len(study['attempts'])==7 and not study['not_attempted']
        assert all(a['error']['message']=='deliberate fixture build failure' for a in study['attempts'])
        with pytest.raises(AionError,match='already has an attempt'):
            run_study(planpath,tmp_path/'store',sessionpath,'discovery')
        with pytest.raises(AionError,match='different explicit'):
            run_study(planpath,tmp_path/'store',sessionpath,'confirmation')


def test_study_budget_failure_before_first_build_is_journalled(tmp_path):
    from aion.sessions import new_session,save_session
    adapter=FileFixtureAdapter()
    planpath=tmp_path/'plan.json';sessionpath=tmp_path/'session.json';save_session(sessionpath,new_session())
    with patch('aion.research.ClangAdapter',return_value=adapter):declare(planpath,study='matrix',cpus='none',commands=1)
    with patch('aion.research.ClangAdapter',side_effect=AionError('budget exhausted during compiler probe')):
        study=run_study(planpath,tmp_path/'store',sessionpath,'discovery')
    assert study['status']=='failed' and len(study['not_attempted'])==5
    assert study['budget']['commands_used']==0 and study['error']['message'].startswith('budget exhausted')


@pytest.mark.parametrize('helper_success',[True,False])
def test_diagnostics_reuses_nested_counter_helper_evidence(tmp_path,helper_success):
    """Synthetic binaries are never executed; exercise the existing helper schema."""
    from dataclasses import asdict
    from aion.host import collect_host_diagnostics
    from aion.provenance import file_sha256
    from aion.research_diagnostics import diagnose
    from aion.sessions import new_session
    adapter=FileFixtureAdapter();panel=CATALOG[0];benchmark=benchmark_for(panel)
    entries={}
    for name in ('baseline','candidate'):
        binary=tmp_path/(name+'.exe');binary.write_bytes(b'fixture never executed')
        entries[name]={'build':{'binary_sha256':file_sha256(binary),'research':{'saved_binary':str(binary)}},'calibration':{'batches':1}}
    raw={'schema_version':1,'run_id':'synthetic-only','host_start':collect_host_diagnostics(),
         'benchmarks':{'records':{'measurement_case':benchmark.case('small'),'configurations':entries}}}
    path=tmp_path/'raw.json';atomic_json(path,raw)
    study={'declaration':{'panels':[panel.name],'compiler':asdict(adapter.info),'build_provenance':adapter.build_provenance(),
                         'execution_controls':{'requested_cpus':None}},
           'attempts':[{'panel':panel.name,'result':str(path),'sha256':file_sha256(path)}]}
    with patch('aion.research_diagnostics.ClangAdapter',return_value=adapter),patch(
        'aion.research_diagnostics.build_counter_helper',return_value=(tmp_path/'helper',{'source_sha256':'fixture','build':{'success':helper_success}})),patch(
        'aion.research_diagnostics.verify_binary',return_value={'passed':True}),patch(
        'aion.research_diagnostics.profile_execution',return_value={'passed':True}) as profile,patch(
        'aion.research_diagnostics.shutil.which',return_value=None),patch(
        'aion.research_diagnostics.run_process',return_value=process()):
        result=diagnose(study,tmp_path/'diagnostics',new_session())
    assert result['status']=='completed'
    assert profile.call_count==(6 if helper_success else 0)
    assert all(len(e['samples'])==(3 if helper_success else 0) for e in result['panels'][panel.name].values())
