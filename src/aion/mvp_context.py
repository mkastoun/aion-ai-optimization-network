"""Bounded, path/source-free exports for optional external AI selection."""
from dataclasses import asdict
from pathlib import Path
import math

from .benchmarks import load_benchmarks
from .errors import AionError
from .mvp_catalog import available,manifest
from .provenance import file_sha256
from .research_catalog import benchmark_for,digest
from .storage import read_json


def export_context(workload,*,maximum=2,iterations=7,warmups=1,commands=2000,seconds=1800,prior_paths=(),diagnostic_paths=()):
    from .budget import ResearchBudget
    from .mvp_proposals import rank
    ResearchBudget(commands,seconds)
    if type(maximum) is not int or not 1<=maximum<=4 or type(iterations) is not int or not 5<=iterations<=15 or type(warmups) is not int or not 1<=warmups<=3:
        raise AionError('MVP requires 1..4 candidates, 5..15 pairs and 1..3 warmups.')
    if len(prior_paths)>8 or len(diagnostic_paths)>4:raise AionError('Context allows at most eight discovery records and four diagnostics.')
    panels=available(workload);by_name={p.name:p for p in panels};benchmark=load_benchmarks(workload)[0]
    prior=[];sources=[];allowed_runs={}
    for value in prior_paths:
        path=Path(value)
        if path.stat().st_size>8*1024*1024:raise AionError('Prior discovery record exceeds the context input bound.')
        raw=read_json(path)
        if raw.get('evidence_kind')!='research-timing' or raw.get('purpose')!='research_discovery' or raw.get('role')=='confirmation':
            raise AionError('Selection context accepts discovery research records only; confirmation evidence is forbidden.')
        name=raw.get('research_panel',{}).get('name')
        if name not in by_name or digest(raw['research_panel'])!=digest(asdict(by_name[name])):
            raise AionError('Prior evidence references an unavailable or incompatible panel.')
        data=raw.get('benchmarks',{}).get(workload,{})
        if data.get('fingerprint')!=benchmark_for(by_name[name]).fingerprint or data.get('measurement_case')!=benchmark_for(by_name[name]).case('performance'):
            raise AionError('Prior discovery source/input contract differs or held-out data was supplied.')
        entry=data['configurations'].get('candidate',{});c=entry.get('comparison') or {}
        if (entry.get('status') not in {'unsupported','compile_failed','incorrect','calibration_failed','execution_failed','measured'}
                or c.get('classification') not in {None,'improvement','regression','no_clear_change','inconclusive'}
                or (c.get('improvement_fraction') is not None and (type(c['improvement_fraction']) not in {int,float} or not math.isfinite(c['improvement_fraction'])))):
            raise AionError('Prior evidence contains invalid summary metadata; no free-form text is exported.')
        prior.append({'panel_id':name,'source_sha256':file_sha256(path),'evidence_scope':'discovery-only',
                      'status':entry.get('status'),'classification':c.get('classification'),
                      'improvement_fraction':c.get('improvement_fraction'),
                      'failed_gates':[g for g in entry.get('gate_outcomes',{}).get('failed',[]) if g in {
                          'correctness','complete_samples','minimum_samples','warmups','duration','variability','drift',
                          'acceptable_regression_bound','improvement_floor_and_uncertainty','effective_affinity'}]})
        allowed_runs[raw['run_id']]=name
        sources.append({'kind':'discovery','path':str(path.resolve()),'sha256':file_sha256(path)})
    diagnostics=[]
    for value in diagnostic_paths:
        path=Path(value)
        if path.stat().st_size>64*1024*1024:raise AionError('Diagnostic input exceeds the context input bound.')
        raw=read_json(path)
        if raw.get('evidence_kind')!='research-diagnostics':raise AionError('Use typed research diagnostics tied to supplied discovery records.')
        included=0
        for name,configs in raw.get('panels',{}).items():
            if name not in {p['panel_id'] for p in prior}:continue
            for config,e in configs.items():
                if allowed_runs.get(e.get('source_run_id'))!=name:
                    raise AionError('Diagnostic context is unlinked or contains held-out confirmation data.')
                events=[{'name':event['name'],'status':event['status']} for s in e.get('samples',[])[:3] for event in s.get('counters',{}).get('events',[])[:9]
                        if event.get('name') in {'cycles','instructions','branches','branch-misses','cache-references','cache-misses','task-clock','context-switches','page-faults'}
                        and event.get('status') in {'counted','unavailable','unsupported','permission_denied','not_counted','error'}]
                inline=[{'successful':str(ir.get('process',{}).get('stderr',''))[:1048576].count('[-Rpass=inline]'),
                         'missed':str(ir.get('process',{}).get('stderr',''))[:1048576].count('[-Rpass-missed=inline]')} for ir in e.get('ir',[])[:8]]
                diagnostics.append({'panel_id':name,'configuration':config,'binary_sha256':e.get('binary_sha256'),
                    'verified_archive':e.get('binary_matches_timing') is True,'counter_event_statuses':events,
                    'prelink_ir_units':len(e.get('ir',[])),'prelink_inline_remark_counts':inline,
                    'scope':'separate diagnostic availability and static inline counts; no source text, paths or confirmation data'})
                included+=1
        if not included:raise AionError('Diagnostic has no proven discovery-only source in this context.')
        sources.append({'kind':'diagnostic','path':str(path.resolve()),'sha256':file_sha256(path)})
    context={'schema_version':1,'evidence_kind':'mvp-selection-context','workload_id':workload,
             'workload':{'category':benchmark.category,'description':'Trusted deterministic C++ workload with independent output checks.'},
             'catalog_sha256':digest(manifest()),'available_panels':[{'panel_id':p.name,'hypothesis':p.hypothesis,
                 'reference':asdict(p.reference),'candidate':asdict(p.candidate),'distribution':p.distribution} for p in panels],
             'available_budget':{'maximum_candidates':maximum,'iterations_per_role':iterations,'warmups':warmups,'commands_total':commands,'seconds_total':seconds},
             'prior_discovery_evidence':prior,'compiler_diagnostics':diagnostics,
             'instructions':['Return only the documented mvp-proposals JSON schema.','Rank only these approved IDs; reasons are hypotheses.',
                             'Use discovery-only evidence; never use held-out confirmation to select candidates.',
                             'No source files, commands, custom flags, LLVM passes, preset approvals or verified performance claims.'],
             'privacy':'No source text, credentials, filesystem paths or raw process output. Nothing is sent to a provider by AION.'}
    context['context_sha256']=digest(context)
    return context,sources
