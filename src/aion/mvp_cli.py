"""User-facing local preview commands. No remote model or execution provider."""
from pathlib import Path
import json
import uuid

from .errors import AionError


def selection_options(parser):
    parser.add_argument('--workload',required=True)
    parser.add_argument('--max-candidates',type=int,default=2)
    parser.add_argument('--iterations',type=int,default=7)
    parser.add_argument('--warmups',type=int,default=1)
    parser.add_argument('--commands',type=int,default=2000,help='total external command budget across all execution stages')
    parser.add_argument('--seconds',type=float,default=1800,help='total elapsed execution budget')
    parser.add_argument('--prior',type=Path,action='append',default=[],help='explicit discovery research record; confirmation is forbidden')
    parser.add_argument('--diagnostic',type=Path,action='append',default=[],help='diagnostics linked to the supplied discovery records')


def configure(commands):
    root=commands.add_parser('mvp',help='AION 0.6 MVP Preview: trusted-ID proposals and local experiments')
    sub=root.add_subparsers(dest='mvp_command',required=True)
    listing=sub.add_parser('list',help='list all ten workloads and approved experiment IDs')
    listing.add_argument('--json',action='store_true')
    context=sub.add_parser('context',help='export bounded discovery-only context for external AI')
    selection_options(context);context.add_argument('--output',type=Path,required=True)
    for name in ('plan','demo'):
        command=sub.add_parser(name,help='create an inspectable plan' if name=='plan' else 'authorize and run one bounded real local demonstration')
        selection_options(command)
        command.add_argument('--strategy',choices=('deterministic','ai-import','auto'),default='deterministic')
        command.add_argument('--proposals',type=Path)
        command.add_argument('--context',type=Path)
        command.add_argument('--seed',type=int,default=76000)
        command.add_argument('--confirmation-seed',type=int,default=76100)
        command.add_argument('--compiler',default='clang++')
        command.add_argument('--cpus',default='auto')
        command.add_argument('--output',type=Path,help='new artifact directory; never overwrite an earlier attempt')
    inspect=sub.add_parser('inspect');inspect.add_argument('--plan',type=Path,required=True)
    run=sub.add_parser('run');run.add_argument('--plan',type=Path,required=True);run.add_argument('--approve',action='store_true')
    report=sub.add_parser('report');report.add_argument('--run',type=Path,required=True);report.add_argument('--output',type=Path,required=True)


def execute(args):
    try:return _execute(args)
    except (KeyError,TypeError,ValueError,AttributeError) as exc:raise AionError(f'Invalid MVP evidence or design: {exc}') from exc


def _execute(args):
    from .mvp_catalog import available
    from .benchmarks import load_benchmarks
    from .mvp import create_plan,check_plan,run_plan
    from .mvp_context import export_context
    from .mvp_report import build_report,render_markdown,write_reports
    from .storage import atomic_json,read_json
    if args.mvp_command=='list':
        rows=[{'workload_id':b.name,'category':b.category,'approved_panels':[p.name for p in available(b.name)]} for b in load_benchmarks()]
        if args.json:print(json.dumps({'schema_version':1,'workloads':rows},indent=2))
        else:
            for row in rows:print(row['workload_id']+': '+', '.join(row['approved_panels']))
        return 0
    if args.mvp_command=='context':
        if args.output.exists():raise AionError('Context output already exists; choose a new path.')
        context,_=export_context(args.workload,maximum=args.max_candidates,iterations=args.iterations,warmups=args.warmups,
                commands=args.commands,seconds=args.seconds,prior_paths=args.prior,diagnostic_paths=args.diagnostic)
        atomic_json(args.output,context)
        print(f"Discovery-only context: {args.output}; SHA-256 {context['context_sha256']}. Nothing was sent to a provider.")
        return 0
    if args.mvp_command=='inspect':
        plan,_=check_plan(args.plan);print(render_markdown(plan));return 0
    if args.mvp_command=='report':
        if args.output.exists():raise AionError('Report output directory already exists; preserve the previous report.')
        report=build_report(read_json(args.run));args.output.mkdir(parents=True)
        write_reports(args.output/'report',report);print(args.output/'report.html');return 0
    if args.mvp_command in {'plan','demo'}:
        output=args.output or args.store/'mvp'/('preview-'+uuid.uuid4().hex[:12])
        path=create_plan(output,args.workload,strategy=args.strategy,proposals_path=args.proposals,context_path=args.context,
                maximum=args.max_candidates,seed=args.seed,confirmation_seed=args.confirmation_seed,
                iterations=args.iterations,warmups=args.warmups,commands=args.commands,seconds=args.seconds,
                compiler=args.compiler,cpus=args.cpus,prior_paths=args.prior,diagnostic_paths=args.diagnostic)
        plan,_=check_plan(path);print(render_markdown(plan),flush=True)
        if plan['ai_usage'].get('fallback_reason'):print(plan['ai_usage']['fallback_reason'],flush=True)
        print(f'Plan: {path}',flush=True)
        if args.mvp_command=='plan':return 0
        job=run_plan(path,approve=True,authorization='one-command demo invocation authorizes this bounded generated plan',progress=lambda s:print(s,flush=True))
    else:
        job=run_plan(args.plan,approve=args.approve,progress=lambda s:print(s,flush=True))
    print(f"Engineering execution: {job['status']}. Native scientific validation pending. Phase 6 is not qualified.")
    for label,path in job['reports'].items():print(f'{label} report: {path}')
    return 0 if job['status']=='completed' else 1
