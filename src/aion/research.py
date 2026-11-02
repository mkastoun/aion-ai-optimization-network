"""Bounded deterministic local research, separate from preset promotion."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid

from .budget import ResearchBudget, bounded
from .compiler import ClangAdapter, source_paths
from .controls import parse_cpus
from .engine import ExperimentSettings, comparison_for, gate_outcomes, run_experiment
from .errors import AionError
from .models import Limits
from .provenance import file_sha256
from .reproducibility import compare_run_compatibility, stable_environment_controls
from .research_catalog import CATALOG, ROOT, benchmark_for, catalog_manifest, digest, training_cases, variant_benchmark
from .sessions import load_session
from .storage import ResultStore, atomic_json, read_json


def now():
    return datetime.now(timezone.utc).isoformat()


def declared_catalog(provider='research-v1'):
    if provider == 'research-v1':return CATALOG,catalog_manifest()
    if provider == 'mvp-preview-v1':
        from .mvp_catalog import MVP_CATALOG,manifest
        return MVP_CATALOG,manifest()
    raise AionError('Unknown trusted catalog provider.')


def declare(output, *, study="all", seed=65000, confirmation_seed=65100, iterations=11,
            warmups=2, commands=2500, seconds=3600, compiler="clang++", cpus="auto",
            selected_panels=None, catalog_provider='research-v1'):
    if output.exists() or seed == confirmation_seed:
        raise AionError("Use a new declaration path and different discovery/confirmation seeds.")
    catalog,manifest = declared_catalog(catalog_provider)
    allowed_studies={'all',*[p.workload for p in catalog]}
    if study not in allowed_studies or not 5 <= iterations <= 15 or not 1 <= warmups <= 3:
        raise AionError("Research requires a fixed study, 5..15 pairs and 1..3 warmups.")
    ResearchBudget(commands,seconds)
    selected=list(selected_panels) if selected_panels is not None else [p.name for p in catalog if study in {'all',p.workload}]
    by_name={p.name:p for p in catalog}
    if not selected or len(selected)!=len(set(selected)) or any(n not in by_name or study not in {'all',by_name[n].workload} for n in selected):
        raise AionError('Select unique compatible trusted research panels.')
    adapter=ClangAdapter(compiler)
    plan={"schema_version":1,"evidence_kind":"research-declaration","created_at":now(),
          "catalog":manifest,"panels":selected,"catalog_provider":catalog_provider,
          "settings":asdict(ExperimentSettings(iterations=iterations,warmups=warmups,seed=seed)),
          "confirmation_seed":confirmation_seed,"compiler":asdict(adapter.info),
          "build_provenance":adapter.build_provenance(),"execution_controls":parse_cpus(cpus).to_dict(),
          "budget_per_role":{"commands":commands,"seconds":seconds},
          "search":"fixed catalog; every selected panel in both roles; no adaptation or retries in this declaration",
          "promotion_eligible":False}
    plan["declaration_sha256"]=digest(plan)
    atomic_json(output,plan)
    snapshot=output.with_suffix(".sources")
    for name in plan["catalog"]["files"]:
        destination=snapshot/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,destination)
    return plan


def check_declaration(plan):
    claimed=plan.get("declaration_sha256")
    if claimed != digest({k:v for k,v in plan.items() if k!="declaration_sha256"}):
        raise AionError("Research declaration seal differs; retain it and create a new declaration.")
    catalog,manifest=declared_catalog(plan.get('catalog_provider','research-v1'))
    if digest(plan.get("catalog")) != digest(manifest):
        raise AionError("Trusted catalog/source/input bytes changed after declaration.")
    names=[p.name for p in catalog]
    selected=plan.get("panels",[])
    if not selected or len(selected)!=len(set(selected)) or any(n not in names for n in selected):
        raise AionError("Declaration contains an invalid or repeated panel.")
    settings=ExperimentSettings(**plan["settings"])
    if not 5<=settings.iterations<=15 or not 1<=settings.warmups<=3 or not settings.calibrate or plan['confirmation_seed']==settings.seed:
        raise AionError("Invalid declared research design.")
    ResearchBudget(**plan["budget_per_role"])


class ResearchAdapter:
    research_only=True

    def __init__(self, adapter, panel, benchmark, archive, declared_files=None):
        self.adapter,self.panel,self.benchmark,self.archive=adapter,panel,benchmark,archive
        self.info=adapter.info
        self.declared_files=declared_files

    def build_provenance(self):
        return self.adapter.build_provenance()

    def recipe(self,candidate):
        recipe=self.panel.reference if candidate.name=="baseline" else self.panel.candidate if candidate.name=="candidate" else None
        if recipe is None or candidate != recipe.candidate(candidate.name):
            raise AionError("Candidate is outside the fixed research panel.")
        return recipe

    def probe(self,candidate):
        self.recipe(candidate)
        return self.adapter.probe(candidate)

    def _build(self,source,output,candidate,limits=None,controls=None):
        recipe=self.recipe(candidate)
        if tuple(source_paths(source)) != self.benchmark.sources:
            raise AionError("Research adapter received foreign source files.")
        benchmark=variant_benchmark(self.benchmark,recipe)
        def verify_sources():
            if self.declared_files is not None and any(
                self.declared_files.get(p.relative_to(ROOT).as_posix())!=file_sha256(p) for p in benchmark.source_files):
                raise AionError('Trusted source bytes differ from the sealed declaration.')
        verify_sources()
        archive=self.archive/candidate.name
        archive.mkdir(parents=True,exist_ok=True)
        build=(self.adapter.compile_profiled(benchmark.compilation_input,output,candidate,
                 training_cases(self.benchmark,recipe),limits or Limits(),controls=controls,
                 profile_archive=archive,training_measurement_batches=1 if recipe.measured_training else None)
               if recipe.mode=="pgo" else self.adapter.compile(benchmark.compilation_input,output,candidate))
        verify_sources()  # Refuse to execute a build whose inputs changed during compilation.
        build["research"]={"recipe":asdict(recipe),"variant_fingerprint":benchmark.fingerprint,
            "source_provenance":[{"path":str(p.resolve()),"sha256":file_sha256(p)} for p in benchmark.source_files]}
        if build["success"]:
            saved=archive/"program.exe"
            shutil.copy2(output,saved)
            build["research"]["saved_binary"]=str(saved.resolve())
        atomic_json(archive/"build.json",build)
        return build

    def compile(self,source,output,candidate):
        return self._build(source,output,candidate)

    def compile_profiled(self,source,output,candidate,training,limits,*,controls=None):
        return self._build(source,output,candidate,limits,controls)


def run_study(declaration_path,store_path,session_path,role,*,progress=print):
    if role not in {"discovery","confirmation"}:
        raise AionError("Choose discovery or confirmation.")
    plan=read_json(declaration_path)
    check_declaration(plan)
    catalog,_=declared_catalog(plan.get('catalog_provider','research-v1'))
    session=load_session(session_path)
    store=ResultStore(store_path)
    previous=[read_json(p) for p in (store_path/"results").glob("*.json")]
    previous=[r for r in previous if r.get("evidence_kind")=="research-study" and r.get("declaration_sha256")==plan['declaration_sha256']]
    if any(r.get('role')==role for r in previous):
        raise AionError("This role already has an attempt; retain it and use a new declaration for a new study.")
    discovery=next((r for r in previous if r.get('role')=='discovery'),None)
    if role=="confirmation" and (not discovery or discovery["session"]["session_id"]==session["session_id"]):
        raise AionError("Confirmation requires a completed discovery invocation and a different explicit observation session.")
    study={"schema_version":1,"evidence_kind":"research-study","run_id":"research-"+uuid.uuid4().hex,
           "created_at":now(),"role":role,"session":session,"status":"running","promotion_eligible":False,
           "declaration_sha256":plan['declaration_sha256'],"declaration_path":str(declaration_path.resolve()),
           "declaration_file_sha256":file_sha256(declaration_path),"declaration":plan,"attempts":[]}
    budget=ResearchBudget(**plan['budget_per_role'])
    store.save(study)  # Journal before any external command or compiler initialization.
    try:
        with bounded(budget):
            adapter=ClangAdapter(plan['compiler']['path'])
            if asdict(adapter.info)!=plan['compiler'] or adapter.build_provenance()!=plan['build_provenance']:
                raise AionError("Declared compiler/build identity changed.")
            controls=parse_cpus(",".join(map(str,plan['execution_controls']['requested_cpus'])) if plan['execution_controls']['requested_cpus'] is not None else 'none')
            settings=ExperimentSettings(**{**plan['settings'],"seed":plan['confirmation_seed'] if role=='confirmation' else plan['settings']['seed']})
            by_name={p.name:p for p in catalog}
            for name in plan['panels']:
                check_declaration(plan)
                panel=by_name[name]
                attempt={"panel":panel.name,"hypothesis":panel.hypothesis,"status":"running","started_at":now(),"recipe":asdict(panel)}
                study['attempts'].append(attempt);store.save(study)
                benchmark=benchmark_for(panel)
                wrapped=ResearchAdapter(adapter,panel,benchmark,store_path/'artifacts'/study['run_id']/panel.name,
                                        declared_files=plan['catalog']['files'])
                try:
                    run=run_experiment(wrapped,[benchmark],[panel.candidate.candidate('candidate')],settings,Limits(),
                        purpose='independent_confirmation' if role=='confirmation' else 'research_discovery',controls=controls,
                        session=session,research_baseline=panel.reference.candidate('baseline'),research_family_size=plan['catalog']['family_comparisons'],
                        progress=progress,on_failure=lambda raw:attempt.update(partial_result=raw))
                    run['research_panel']=asdict(panel)
                    run['declaration_sha256']=plan['declaration_sha256']
                    path=store.save(run)
                    complete=all(e['status']=='measured' for b in run['benchmarks'].values() for e in b['configurations'].values())
                    attempt.update(status=run['status'] if complete else 'failed',result=str(path.resolve()),sha256=file_sha256(path),
                        configuration_outcomes={w:{n:e['status'] for n,e in b['configurations'].items()} for w,b in run['benchmarks'].items()})
                except Exception as exc:
                    attempt.update(status='failed',error={"type":type(exc).__name__,"message":str(exc)})
                    # Continue declared panels on build/correctness failures; budget exhaustion stops launches.
                    if budget.record()['commands_used']>=budget.maximum_commands or budget.record()['elapsed_seconds']>=budget.maximum_seconds:
                        raise
                finally:
                    attempt['ended_at']=now();study['budget']=budget.record();store.save(study)
            study['status']='completed' if all(a['status']=='completed' for a in study['attempts']) else 'failed'
    except BaseException as exc:
        study.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',error={"type":type(exc).__name__,"message":str(exc)})
        if isinstance(exc,KeyboardInterrupt):raise
    finally:
        study['not_attempted']=[n for n in plan['panels'] if n not in {a['panel'] for a in study['attempts']}]
        study['budget']=budget.record();study['ended_at']=now();store.save(study)
    return study


def load_attempts(study):
    runs={}
    for attempt in study['attempts']:
        path=Path(attempt['result']) if attempt.get('result') else None
        if path:
            if file_sha256(path)!=attempt['sha256']:raise AionError("Research result bytes changed.")
            runs[attempt['panel']]=read_json(path)
    return runs


def assess_pair(first,second):
    # Read-only structural views allow reuse of existing primary compatibility rules.
    # Persisted research evidence never changes type and is never passed to a registry.
    compatibility=compare_run_compatibility({**first,'evidence_kind':'primary-timing'}, {**second,'evidence_kind':'primary-timing'})
    reasons=list(compatibility['reasons'])
    if first.get('research_panel')!=second.get('research_panel') or first.get('declaration_sha256')!=second.get('declaration_sha256'):
        reasons.append('research contract differs')
    if not compatibility['different_sessions'] or first['settings']['seed']==second['settings']['seed']:
        reasons.append('independent session/scheduling seed missing')
    if (first.get('host_end',{}).get('observed_at') or 'z') >= second.get('host_start',{}).get('observed_at',''):
        reasons.append('overlapping observation intervals or missing timestamps')
    observations=[]
    for run in (first,second):
        workload=next(iter(run['benchmarks']))
        b=run['benchmarks'][workload]
        if b['configurations']['candidate']['status']!='measured':
            observations.append({'valid':False,'failed_gates':['candidate not measured']});continue
        comparison=comparison_for(run,workload,'candidate')
        view={**run,'benchmarks':{workload:{**b,'configurations':{**b['configurations'],
              'candidate':{**b['configurations']['candidate'],'comparison':comparison}}}}}
        gates=gate_outcomes(view,workload,'candidate')
        quality_keys={'correctness','complete_samples','minimum_samples','warmups','duration','variability','drift','effective_affinity'}
        failed=[k for k,v in gates['gates'].items() if k in quality_keys and v is False]
        stable=stable_environment_controls(run.get('host_start'))==stable_environment_controls(run.get('host_end'))
        if not stable:failed.append('static environment changed')
        if run.get('status')!='completed':failed.append('incomplete experiment')
        observations.append({'run_id':run['run_id'],'valid':not failed,'failed_gates':gates['failed'],
                             'quality_failed_gates':failed,'comparison':comparison,'input':b['measurement_case']})
    if len(observations)==2 and observations[0].get('input',{}).get('args')==observations[1].get('input',{}).get('args'):
        reasons.append('held-out input missing')
    return {'compatible':not reasons,'reasons':reasons,'observations':observations,'pooling':'disabled'}


def verified_native_controls(quality, first, second):
    """Recompute source-linked controls rather than trusting a saved readiness label."""
    from .quality import build_quality_report
    references=quality.get('source_results',[])
    validation=quality.get('validation_evidence') or {}
    if not references or not validation.get('path'):return False
    paths=[Path(r['path']) for r in references if r.get('path')]
    if len(paths)!=len(references) or any(file_sha256(p)!=r['sha256'] for p,r in zip(paths,references)):return False
    validation_path=Path(validation['path'])
    if file_sha256(validation_path)!=validation.get('sha256'):return False
    controls=[read_json(p) for p in paths]
    selected=[]
    for r in controls:
        if all(r.get('compiler')==timing.get('compiler') and r.get('build_provenance')==timing.get('build_provenance')
               and r.get('host_start',{}).get('host_fingerprint')==timing.get('host_start',{}).get('host_fingerprint')
               and r.get('execution_controls')==timing.get('execution_controls') for timing in (first,second)):
            selected.append(r)
    if not selected:return False
    report=build_quality_report(selected,validation=read_json(validation_path))
    return (report['readiness']['native_linux_control_study_passed'] and report['readiness']['measurement_quality_checks_passed']
            and report['readiness']['validation_passed_on_available_environment'])


def build_report(discovery_path,confirmation_path,quality_path=None,validation_path=None,*,diagnostic_paths=()):
    discovery,confirmation=read_json(discovery_path),read_json(confirmation_path)
    if discovery.get('declaration',{}).get('catalog_provider','research-v1')!='research-v1':
        raise AionError('Use aion mvp report for MVP executions, including proposal provenance and preview labels.')
    if discovery.get('role')!='discovery' or confirmation.get('role')!='confirmation' or discovery.get('declaration_sha256')!=confirmation.get('declaration_sha256'):
        raise AionError('Reports require discovery and confirmation from the same declaration.')
    a,b=load_attempts(discovery),load_attempts(confirmation)
    # Native validation is deliberately conservative. A preflight is insufficient.
    quality=read_json(quality_path) if quality_path else {}
    validation=read_json(validation_path) if validation_path else {}
    diagnostics=[(path,read_json(path)) for path in diagnostic_paths]
    if any(d.get('evidence_kind')!='research-diagnostics' for path,d in diagnostics):
        raise AionError('Research diagnostic attachments must be typed research-diagnostics records.')
    result={'schema_version':1,'evidence_kind':'research-report','run_id':'research-report-'+uuid.uuid4().hex,
            'status':'completed','created_at':now(),'promotion_eligible':False,'panels':[],
            'sources':[{'path':str(p.resolve()),'sha256':file_sha256(p)} for p in (discovery_path,confirmation_path)],
            'quality_evidence':{'path':str(quality_path),'sha256':file_sha256(quality_path)} if quality_path else None,
            'validation_evidence':{'path':str(validation_path),'sha256':file_sha256(validation_path)} if validation_path else None}
    for panel in CATALOG:
        if panel.name not in discovery['declaration']['panels']:continue
        row={'panel':panel.name,'hypothesis':panel.hypothesis,'status':'inconclusive','supported':None,
             'predeclared_panel':asdict(panel),'diagnostic_evidence':[]}
        if panel.name not in a or panel.name not in b:
            row['reason']='Missing or failed declared attempt; inspect study journals.'
        else:
            first,second=a[panel.name],b[panel.name]
            row['evidence']=[{'run_id':r['run_id'],'compiler':r['compiler'],'build_provenance':r.get('build_provenance'),
                'host_start':r['host_start'],'host_end':r.get('host_end'),'session':r['session'],
                'input':next(iter(r['benchmarks'].values()))['measurement_case'],
                'configurations':{n:{k:e.get(k) for k in ('build','verification','calibration','summary','status')}
                    for n,e in next(iter(r['benchmarks'].values()))['configurations'].items()}} for r in (first,second)]
            for path,diagnostic in diagnostics:
                if panel.name not in diagnostic.get('panels',{}):continue
                evidence=diagnostic['panels'][panel.name]
                for name,e in evidence.items():
                    source=next((r for r in (first,second) if r['run_id']==e['source_run_id']),None)
                    if source is None or next(iter(source['benchmarks'].values()))['configurations'][name]['build']['binary_sha256']!=e['binary_sha256']:
                        raise AionError('Diagnostic attachment is not linked to the reported timing binary.')
                row['diagnostic_evidence'].append({'path':str(path.resolve()),'sha256':file_sha256(path),'observations':evidence,
                    'scope':'whole-process counters and static codegen, separate from compute timing; not causal proof'})
            assessment=assess_pair(first,second);row.update(assessment)
            native=all(r['host_start'].get('environment_classification')=='native-linux' for r in (first,second))
            native_controls=verified_native_controls(quality,first,second) if native else False
            valid=assessment['compatible'] and all(o['valid'] for o in assessment['observations'])
            classes=[o.get('comparison',{}).get('classification') for o in assessment['observations']]
            row['observed_change']=all(c=='improvement' for c in classes) or all(c=='regression' for c in classes)
            row['environment_status']='supported native environment' if native else 'unsupported environment'
            row['native_measurement_ready']=native and native_controls
            correctness=bool(validation.get('evidence_kind')=='sanitizer-validation' and validation.get('status')=='passed'
                and validation.get('research_catalog_sha256')==digest(discovery['declaration']['catalog'])
                and all(validation.get('compiler')==r.get('compiler') and validation.get('build_provenance')==r.get('build_provenance')
                    and validation.get('host_start',{}).get('host_fingerprint')==r.get('host_start',{}).get('host_fingerprint') for r in (first,second)))
            if not native:
                row['status']='unsupported environment'
                row['reason']='WSL/VM/container measurements cannot validate native hypotheses; estimates remain observable.'
            elif valid and native_controls and correctness and all(c=='improvement' for c in classes):
                row.update(status='validated change',supported=True)
            elif valid and native_controls and correctness and all(c=='regression' for c in classes):
                if 'changes ' in panel.hypothesis:
                    row.update(status='validated change',supported=True)
                else:
                    row.update(status='rejected hypothesis',supported=False)
            elif valid and row['observed_change']:
                row['status']='observed change'
            row['correctness_validation_compatible']=correctness
        result['panels'].append(row)
    result['phase6_ready']=False
    result['phase6_requirements']={
        'validated_native_measurement_conditions':bool(result['panels']) and all(p.get('native_measurement_ready') for p in result['panels']),
        'research_correctness_validation':validation.get('status')=='passed' and validation.get('research_catalog_sha256')==digest(discovery['declaration']['catalog']),
        'compatible_independent_experiments':bool(result['panels']) and all(p.get('compatible') for p in result['panels']),
        'bounded_auditable_catalog':len(discovery['declaration']['panels'])<=len(CATALOG),
        'explicit_compute_budgets':all(s.get('budget',{}).get('commands_used',10001)<=s['declaration']['budget_per_role']['commands']
            and s.get('budget',{}).get('elapsed_seconds',7201)<=s['declaration']['budget_per_role']['seconds'] for s in (discovery,confirmation)),
        'research_separate_from_presets':True,
        'independent_all_ten_native_validation_reviewed':False}
    result['phase6_reason']='Requires native ten-workload and control validation, independent reproducibility and a separately reviewed readiness decision; research never grants automatic AI permission.'
    return result


def render_research(run):
    lines=[f"# AION {run['evidence_kind']}",'',f"Run: `{run['run_id']}`; status: **{run['status']}**.",
           'Research evidence cannot create presets. Estimates remain separate; no raw samples are pooled.','']
    if run['evidence_kind']=='research-timing':
        lines += [f"Panel: `{run.get('research_panel',{}).get('name')}`; environment: `{run['host_start']['environment_classification']}`.",
                  '| Workload | Configuration | Status | Binary SHA-256 |','|---|---|---|---|']
        for w,b in run['benchmarks'].items():
            for n,e in b['configurations'].items():
                lines.append(f"| {w} | {n} | {e['status']} | `{e.get('build',{}).get('binary_sha256')}` |")
                if e.get('comparison'):lines += ['',f"Comparison: `{e['comparison']}`",'']
    elif run['evidence_kind']=='research-study':
        lines += [f"Role: {run['role']}; declaration: `{run['declaration_sha256']}`.",'',
                  *[f"- {a['panel']}: {a['status']}" for a in run['attempts']],
                  '',f"Budget: {run.get('budget',{}).get('commands_used')} logical commands; all attempts retained in JSON."]
    elif run['evidence_kind']=='research-report':
        lines += ['| Panel | Status | Discovery / confirmation improvement % |','|---|---|---|']
        for p in run['panels']:
            effects=' / '.join(f"{o['comparison']['improvement_fraction']*100:.3f}" for o in p.get('observations',[]) if o.get('comparison'))
            lines.append(f"| {p['panel']} | {p['status']} | {effects} |")
        lines += ['', 'Raw JSON retains uncertainty, each failed gate, exact input cases and compatibility reasons.',
                  'Counter/codegen observations are separate diagnostics; changes alone do not establish causality.',
                  '',f"Phase 6 ready: **{run['phase6_ready']}**. {run['phase6_reason']}"]
    elif run['evidence_kind']=='research-diagnostics':
        lines += [run['scope'],'','| Panel | Configuration | Correctness | Counter executions |','|---|---|---|---:|']
        for panel,configs in run['panels'].items():
            for name,e in configs.items():lines.append(f"| {panel} | {name} | {e['verification']['passed']} | {len(e['samples'])} |")
    return '\n'.join(lines)+'\n'
