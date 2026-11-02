"""Explicit declaration, separate invocations, retained evidence and reports."""
from pathlib import Path

from .errors import AionError


def configure(commands):
    root=commands.add_parser('research',help='fixed trusted experiments; never create presets')
    sub=root.add_subparsers(dest='research_command',required=True)
    declare=sub.add_parser('declare')
    declare.add_argument('--output',type=Path,required=True)
    declare.add_argument('--study',choices=('all','records','logs','matrix'),default='all')
    declare.add_argument('--compiler',default='clang++')
    declare.add_argument('--cpus',default='auto')
    declare.add_argument('--seed',type=int,default=65000)
    declare.add_argument('--confirmation-seed',type=int,default=65100)
    declare.add_argument('--iterations',type=int,default=11)
    declare.add_argument('--warmups',type=int,default=2)
    declare.add_argument('--commands',type=int,default=2500)
    declare.add_argument('--seconds',type=float,default=3600)
    run=sub.add_parser('run')
    run.add_argument('--declaration',type=Path,required=True)
    run.add_argument('--session-file',type=Path,required=True)
    run.add_argument('--role',choices=('discovery','confirmation'),required=True)
    report=sub.add_parser('report')
    report.add_argument('--discovery',type=Path,required=True)
    report.add_argument('--confirmation',type=Path,required=True)
    report.add_argument('--quality',type=Path)
    report.add_argument('--validation',type=Path)
    report.add_argument('--diagnostic',type=Path,action='append',default=[])
    validate=sub.add_parser('validate')
    validate.add_argument('--compiler',default='clang++')
    validate.add_argument('--cpus',default='auto')
    validate.add_argument('--session-file',type=Path,required=True)
    diagnostics=sub.add_parser('diagnose')
    diagnostics.add_argument('--study',type=Path,required=True)
    diagnostics.add_argument('--session-file',type=Path,required=True)
    diagnostics.add_argument('--panel',action='append')


def execute(args,store):
    try:
        return _execute(args,store)
    except (KeyError,TypeError,ValueError,AttributeError) as exc:
        raise AionError(f'Invalid research evidence or design: {exc}') from exc


def _execute(args,store):
    from .research import declare,run_study,build_report,render_research
    if args.research_command=='declare':
        plan=declare(args.output,study=args.study,seed=args.seed,confirmation_seed=args.confirmation_seed,
                     iterations=args.iterations,warmups=args.warmups,commands=args.commands,seconds=args.seconds,
                     compiler=args.compiler,cpus=args.cpus)
        print(f"Sealed declaration: {args.output} / {plan['declaration_sha256']}")
        return 0
    if args.research_command=='run':
        data=run_study(args.declaration,args.store,args.session_file,args.role,progress=lambda m:print(m,flush=True))
    elif args.research_command=='report':
        data=build_report(args.discovery,args.confirmation,args.quality,args.validation,diagnostic_paths=args.diagnostic)
    elif args.research_command=='diagnose':
        from .research_diagnostics import diagnose
        from .storage import read_json
        from .sessions import load_session
        data=diagnose(read_json(args.study),args.store/'diagnostic-artifacts',load_session(args.session_file),args.panel)
    else:
        from dataclasses import replace
        from .compiler import ClangAdapter
        from .controls import parse_cpus
        from .research_catalog import CATALOG,benchmark_for,catalog_manifest,digest,variant_benchmark
        from .sessions import load_session
        from .validation import run_validation,validation_cases
        variants={}
        for panel in CATALOG:
            benchmark=benchmark_for(panel)
            for recipe in (panel.reference,panel.candidate):
                if recipe.variant=='original':continue
                variant=variant_benchmark(benchmark,recipe)
                # Preserve extended ordinary validation too; unique names avoid unrelated lookup.
                variants[(recipe.variant,panel.distribution)]=replace(variant,
                    name=recipe.variant+'-'+panel.distribution,cases=tuple(validation_cases(variant)))
        data=run_validation(ClangAdapter(args.compiler),list(variants.values()),args.store/'validation-artifacts',
                            controls=parse_cpus(args.cpus),session=load_session(args.session_file),progress=print)
        data['research_catalog_sha256']=digest(catalog_manifest())
        data['research_scope']='all trusted replacement/wrapper variants, ordinary and held-out distributions'
    path=store.save(data)
    from .report import render_report
    path.with_suffix('.md').write_text(render_report(data),encoding='utf-8')
    print(f"Results: {path}")
    return 0 if data['status'] in {'completed','passed'} else 1
