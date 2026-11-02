"""AION 0.6 engineering preview: plan, validate, execute and report trusted IDs."""
from dataclasses import replace
from pathlib import Path
import shutil
import sys
import uuid

from . import __version__
from .budget import ResearchBudget,bounded
from .compiler import ClangAdapter
from .controls import parse_cpus
from .errors import AionError
from .mvp_catalog import PROVIDER,MVP_CATALOG,available,manifest
from .mvp_context import export_context
from .mvp_proposals import deterministic,read_proposals,validate_ai,rank,MAX_IMPORT_BYTES
from .provenance import file_sha256
from .research import declare,check_declaration,run_study,now
from .research_catalog import ROOT,benchmark_for,variant_benchmark,digest
from .sessions import new_session,save_session
from .storage import atomic_json,read_json
from .validation import run_validation,validation_cases

MILESTONE='AION 0.6 MVP Preview'


def seal(plan):
    plan['plan_sha256']=digest({k:v for k,v in plan.items() if k!='plan_sha256'})
    return plan


def create_plan(directory,workload,*,strategy='deterministic',proposals_path=None,context_path=None,
                maximum=2,seed=76000,confirmation_seed=76100,iterations=7,warmups=1,
                commands=2000,seconds=1800,compiler='clang++',cpus='auto',prior_paths=(),diagnostic_paths=()):
    directory=Path(directory).resolve()
    if directory.exists():raise AionError('Use a new output directory; earlier plans and attempts are preserved.')
    directory.mkdir(parents=True)
    receipt={'schema_version':1,'evidence_kind':'mvp-planning-attempt','milestone':MILESTONE,'created_at':now(),
             'status':'planning','workload_id':workload,'requested_strategy':strategy}
    atomic_json(directory/'planning.json',receipt)
    planning_budget=ResearchBudget(100,120)
    try:
        if strategy not in {'deterministic','ai-import','auto'}:raise AionError('Unknown MVP strategy.')
        if strategy=='deterministic' and proposals_path is not None:raise AionError('Deterministic selection does not consume an AI proposal file.')
        if seed==confirmation_seed:raise AionError('Discovery and confirmation scheduling seeds must differ.')
        context,sources=export_context(workload,maximum=maximum,iterations=iterations,warmups=warmups,
                                      commands=commands,seconds=seconds,prior_paths=prior_paths,diagnostic_paths=diagnostic_paths)
        if context_path is not None:
            supplied=read_json(Path(context_path))
            if digest(supplied)!=digest(context):raise AionError('Exported selection context differs from these inputs, sources, budgets or installed catalog.')
        atomic_json(directory/'context.json',context)
        atomic_json(directory/'context-sources.json',{'schema_version':1,'sources':sources})
        fallback=None
        if proposals_path is not None:
            path=Path(proposals_path)
            if path.stat().st_size>MAX_IMPORT_BYTES:raise AionError('AI proposal file exceeds 64 KiB.')
            # Preserve the supplied data before validation, including rejected outputs.
            shutil.copyfile(path,directory/'imported-proposals.json')
            payload=read_proposals(directory/'imported-proposals.json')
            proposals=validate_ai(payload,workload,context['context_sha256'])
            actual='ai-import';ai={'used':True,'mode':'imported external proposals','provenance':payload['provenance'],
                'model_called_by_aion':False,'authentication':'external authorship is caller-declared, not authenticated by AION',
                'input_sha256':file_sha256(directory/'imported-proposals.json')}
        else:
            if strategy!='deterministic':fallback='AI unavailable: no external proposal file or provider configured. Deterministic ranking was used; no AI model was used.'
            proposals=deterministic(workload,seed,iterations,warmups);actual='deterministic'
            ai={'used':False,'model_called_by_aion':False,'mode':'none','fallback_reason':fallback}
        decisions=rank(proposals,seed,maximum)
        atomic_json(directory/'selection.json',{'schema_version':1,'decisions':decisions,'actual_strategy':actual,'ai_usage':ai})
        selected=[d['proposal']['panel_id'] for d in decisions if d['selected']]
        with bounded(planning_budget):
            declaration=declare(directory/'declaration.json',study=workload,selected_panels=selected,
                catalog_provider=PROVIDER,seed=seed,confirmation_seed=confirmation_seed,iterations=iterations,
                warmups=warmups,commands=commands,seconds=seconds,compiler=compiler,cpus=cpus)
        plan={'schema_version':1,'evidence_kind':'mvp-plan','milestone':MILESTONE,'aion_version':__version__,
              'created_at':now(),'workload_id':workload,'requested_strategy':strategy,'actual_strategy':actual,
              'ai_usage':ai,'context':context,'context_sources':sources,'decisions':decisions,'selected_panels':selected,
              'maximum_candidates':maximum,'total_execution_budget':{'commands':commands,'seconds':seconds},
              'declaration_file':'declaration.json','declaration_sha256':declaration['declaration_sha256'],
              'declaration_file_sha256':file_sha256(directory/'declaration.json'),'planning_budget':planning_budget.record(),
              'approval_required':True,'promotion_eligible':False,'phase6_scientific_ready':False,
              'status':'planned','frozen_selection':'Selected IDs and order are frozen before any discovery or confirmation execution.'}
        seal(plan);atomic_json(directory/'plan.json',plan)
        receipt.update(status='planned',plan_sha256=plan['plan_sha256'])
        return directory/'plan.json'
    except BaseException as exc:
        receipt.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'rejected',
                       error={'type':type(exc).__name__,'message':str(exc)})
        raise
    finally:
        receipt['planning_budget']=planning_budget.record();atomic_json(directory/'planning.json',receipt)


def check_plan(path):
    path=Path(path).resolve();plan=read_json(path)
    if plan.get('evidence_kind')!='mvp-plan' or plan.get('plan_sha256')!=digest({k:v for k,v in plan.items() if k!='plan_sha256'}):
        raise AionError('MVP plan seal differs or its evidence kind is invalid.')
    if plan.get('declaration_file')!='declaration.json':raise AionError('A plan can reference only its fixed sibling declaration.')
    declaration_path=path.parent/'declaration.json'
    if file_sha256(declaration_path)!=plan.get('declaration_file_sha256'):raise AionError('Declared evidence bytes changed.')
    declaration=read_json(declaration_path);check_declaration(declaration)
    if declaration.get('catalog_provider')!=PROVIDER or declaration['declaration_sha256']!=plan['declaration_sha256']:
        raise AionError('Plan has the wrong trusted catalog or declaration.')
    selected=plan['selected_panels'];compatible={p.name for p in available(plan['workload_id'])}
    if not 1<=len(selected)<=plan['maximum_candidates']<=4 or len(set(selected))!=len(selected) or any(n not in compatible for n in selected):
        raise AionError('MVP candidate-count or catalog compatibility gate failed.')
    if selected!=declaration['panels'] or selected!=[d['proposal']['panel_id'] for d in plan['decisions'] if d['selected']]:
        raise AionError('Frozen selected proposals differ from the execution declaration.')
    context=plan['context']
    if context.get('context_sha256')!=digest({k:v for k,v in context.items() if k!='context_sha256'}) or context.get('catalog_sha256')!=digest(manifest()):
        raise AionError('Discovery-only context or trusted catalog changed.')
    expected_budget={'commands':context['available_budget']['commands_total'],'seconds':context['available_budget']['seconds_total']}
    if plan['total_execution_budget']!=expected_budget or declaration['budget_per_role']!=expected_budget:
        raise AionError('Execution budgets differ from the approved context.')
    ResearchBudget(**expected_budget)
    if plan['actual_strategy']=='ai-import':
        if plan['ai_usage'].get('used') is not True or plan['ai_usage'].get('model_called_by_aion') is not False:
            raise AionError('Imported AI usage labels differ from the executed strategy.')
        if file_sha256(path.parent/'imported-proposals.json')!=plan['ai_usage']['input_sha256']:raise AionError('Imported AI proposal bytes changed.')
        proposals=validate_ai(read_proposals(path.parent/'imported-proposals.json'),plan['workload_id'],context['context_sha256'])
    elif plan['actual_strategy']=='deterministic':
        if plan['ai_usage'].get('used') is not False or plan['ai_usage'].get('model_called_by_aion') is not False:
            raise AionError('Deterministic selection cannot be labeled as an AI result.')
        proposals=deterministic(plan['workload_id'],declaration['settings']['seed'],declaration['settings']['iterations'],declaration['settings']['warmups'])
    else:raise AionError('Unknown actual strategy.')
    if rank(proposals,declaration['settings']['seed'],plan['maximum_candidates'])!=plan['decisions']:
        raise AionError('Proposal ranking/selection changed after approval.')
    for source in plan.get('context_sources',[]):
        if file_sha256(Path(source['path']))!=source['sha256']:raise AionError('Prior discovery evidence changed after selection.')
    return plan,declaration


def validation_benchmarks(plan):
    by_name={p.name:p for p in MVP_CATALOG};result={}
    for name in plan['selected_panels']:
        panel=by_name[name];benchmark=benchmark_for(panel)
        for recipe in (panel.reference,panel.candidate):
            variant=variant_benchmark(benchmark,recipe)
            if variant.fingerprint in result:continue
            result[variant.fingerprint]=replace(variant,name='mvp-variant-'+str(len(result)),cases=tuple(validation_cases(variant)))
    return list(result.values())


def run_plan(path,*,approve=False,authorization='explicit CLI --approve',progress=print):
    if not approve:raise AionError('Inspect the plan, then execute with --approve. The demo command authorizes its bounded generated plan.')
    path=Path(path).resolve();plan,declaration=check_plan(path)
    directory=path.parent
    if (directory/'job.json').exists():raise AionError('This plan already has an execution attempt; retain it and create a new plan.')
    budget=ResearchBudget(**plan['total_execution_budget'])
    job={'schema_version':1,'evidence_kind':'mvp-run','milestone':MILESTONE,'aion_version':__version__,
         'run_id':'mvp-'+uuid.uuid4().hex,'created_at':now(),'status':'running','plan_path':str(path),
         'plan_file_sha256':file_sha256(path),'plan':plan,'stages':[],
         'authorization':{'kind':authorization,'plan_sha256':plan['plan_sha256'],'approved_at':now()},
         'promotion_eligible':False,'phase6_scientific_ready':False,'native_scientific_validation':'pending'}
    def save():
        job['budget']=budget.record();atomic_json(directory/'job.json',job)
    def stage(name):
        current={'name':name,'status':'running','started_at':now(),'commands_before':budget.record()['commands_used']}
        job['stages'].append(current);save();progress(name)
        return current
    def complete(current,evidence,filename):
        atomic_json(directory/filename,evidence)
        current.update(status=evidence['status'],ended_at=now(),evidence_path=str((directory/filename).resolve()),
                       evidence_sha256=file_sha256(directory/filename),commands_after=budget.record()['commands_used'])
        save()
    save()
    try:
        if not (sys.platform.startswith('linux') or sys.platform == 'darwin'):raise AionError('Execute the MVP inside Linux, Ubuntu on WSL2, or macOS. Listing, context and proposal inspection remain cross-platform.')
        with bounded(budget):
            check_plan(path)
            adapter=ClangAdapter(declaration['compiler']['path'])
            if adapter.build_provenance()!=declaration['build_provenance']:raise AionError('Approved compiler/build identity changed.')
            cpus=declaration['execution_controls']['requested_cpus'];controls=parse_cpus(','.join(map(str,cpus)) if cpus is not None else 'none')
            session_a=new_session(label='MVP discovery observation window');save_session(directory/'session-a.json',session_a)
            current=stage('separate correctness validation')
            validation=run_validation(adapter,validation_benchmarks(plan),directory/'validation-artifacts',controls=controls,session=session_a,progress=progress)
            validation['mvp_plan_sha256']=plan['plan_sha256'];complete(current,validation,'validation.json')
            if validation['status']!='passed':raise AionError('Separate correctness validation did not pass; primary execution was not started.')
            current=stage('discovery')
            discovery=run_study(directory/'declaration.json',directory/'research',directory/'session-a.json','discovery',progress=progress)
            complete(current,discovery,'discovery.json')
            if discovery['status']!='completed':raise AionError('Discovery has failed attempts; no silent retry or replacement selection is allowed.')
            session_b=new_session(label='MVP held-out confirmation observation window');save_session(directory/'session-b.json',session_b)
            current=stage('confirmation')
            confirmation=run_study(directory/'declaration.json',directory/'research',directory/'session-b.json','confirmation',progress=progress)
            complete(current,confirmation,'confirmation.json')
            if confirmation['status']!='completed':raise AionError('Confirmation has failed attempts; see retained evidence.')
            if budget.record()['elapsed_seconds']>budget.maximum_seconds:raise AionError('MVP wall budget exhausted; results retained without qualification.')
        job['status']='completed'
    except BaseException as exc:
        job.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',error={'type':type(exc).__name__,'message':str(exc)})
        if job['stages'] and job['stages'][-1]['status']=='running':
            job['stages'][-1].update(status='failed',ended_at=now(),error=job['error'])
        job['partial_validation_files']=[{'path':str(p.resolve()),'sha256':file_sha256(p)} for p in (directory/'validation-artifacts').glob('*/partial.json')]
    finally:
        job['ended_at']=now();save()
        from .mvp_report import build_report,write_reports
        try:
            report=build_report(job)
        except (AionError,KeyError,TypeError,ValueError) as exc:
            job.update(status='failed',error={'type':type(exc).__name__,'message':'Report integrity failure: '+str(exc)})
            save()
            report=build_report({**job,'stages':[]})
        write_reports(directory/'report',report)
        job['reports']={suffix:str((directory/'report').with_suffix(suffix)) for suffix in ('.json','.md','.html')};save()
    return job
