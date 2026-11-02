"""Validate an independently installed AION wheel; no performance claim."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--store',type=Path,required=True)
    parser.add_argument('--mvp',action='store_true',help='also run the installed MVP one-command pipeline')
    args=parser.parse_args()
    target=args.target.resolve()
    sys.path.insert(0,str(target))
    import aion
    from aion.benchmarks import load_benchmarks
    from aion.compiler import ClangAdapter
    from aion.controls import parse_cpus
    from aion.engine import ExperimentSettings,run_experiment
    from aion.models import Limits
    from aion.profiling import HELPER,probe_counters
    from aion.report import render_report
    from aion.storage import ResultStore,atomic_json
    assert aion.__version__=='0.6.0.dev0',aion.__version__
    from aion.research_catalog import catalog_manifest
    catalog=catalog_manifest()
    assert len(catalog['panels'])==17 and all(catalog['files'].values())
    assert Path(aion.__file__).resolve().is_relative_to(target),aion.__file__
    benchmarks=load_benchmarks()
    assert len(benchmarks)==10
    assert all(p.is_file() and p.resolve().is_relative_to(target) for b in benchmarks for p in b.source_files)
    assert HELPER.is_file() and HELPER.resolve().is_relative_to(target)
    adapter=ClangAdapter();controls=parse_cpus('auto' if sys.platform.startswith('linux') else 'none')
    run=run_experiment(adapter,benchmarks,[],ExperimentSettings(iterations=1,warmups=0,seed=64500,bootstrap_resamples=200),
                       Limits(),purpose='package-smoke-no-performance-claim',controls=controls,
                       progress=lambda message:print(message,flush=True))
    assert run['status']=='completed'
    assert all(e['status']=='measured' and e['verification']['passed'] for b in run['benchmarks'].values() for e in b['configurations'].values())
    from aion.research_catalog import CATALOG,benchmark_for,variant_benchmark
    from aion.models import Candidate
    from aion.verification import verify_binary,measure_binary
    import tempfile
    variants={}
    with tempfile.TemporaryDirectory(prefix='aion-wheel-research-') as directory:
        for panel in CATALOG:
            for recipe in (panel.reference,panel.candidate):
                key=recipe.variant+'-'+panel.distribution
                if recipe.variant=='original' or key in variants:continue
                benchmark=variant_benchmark(benchmark_for(panel),recipe)
                assert all(p.resolve().is_relative_to(target) for p in benchmark.source_files)
                binary=Path(directory)/(key+'.exe')
                build=adapter.compile(benchmark.compilation_input,binary,Candidate('wheel-check',('-O3',)))
                assert build['success'],build
                verification=verify_binary(binary,benchmark,Limits(),controls=controls)
                measurement=measure_binary(binary,benchmark.case('small'),1,Limits(),controls=controls)
                assert verification['passed'] and measurement['passed']
                variants[key]={'fingerprint':benchmark.fingerprint,'build':build,'verification':verification,'measurement':measurement}
    run['research_variant_smoke']=variants
    run['evidence_kind']='package-smoke';run['promotion_eligible']=False
    run['installed_package']={'version':aion.__version__,'import_path':aion.__file__,'target':str(target),'workloads':[b.name for b in benchmarks]}
    run['counter_capability']=probe_counters(adapter,controls)
    store=ResultStore(args.store);path=store.save(run)
    path.with_suffix('.md').write_text(render_report(run),encoding='utf-8')
    metadata={'schema_version':1,'version':aion.__version__,'import_path':aion.__file__,'run_id':run['run_id'],
              'source_files_present':True,'workloads':[b.name for b in benchmarks],'result':str(path.resolve()),
              'research_variants':list(variants),'research_catalog_panels':len(catalog['panels']),
              'scope':'independent installed-wheel correctness/calibration smoke; ten single samples, no performance claim'}
    atomic_json(args.store/'smoke.json',metadata)
    if args.mvp:
        from aion.cli import main as aion_main
        import aion.mvp as installed_mvp
        assert Path(installed_mvp.__file__).resolve().is_relative_to(target)
        output=args.store/'mvp'
        code=aion_main(['mvp','demo','--workload','array','--strategy','deterministic','--max-candidates','1',
                       '--iterations','5','--warmups','1','--commands','700','--seconds','300',
                       '--output',str(output)])
        assert code==0,code
        report=json.loads((output/'report.json').read_text())
        assert report['status']=='completed' and report['correctness_status']=='Correctness passed'
        assert not report['phase6_scientific_ready'] and not report['promotion_eligible']
        for candidate in report['candidates']:
            for evidence in candidate['raw_evidence']:
                for entry in evidence['configurations'].values():
                    assert all(Path(p['path']).resolve().is_relative_to(target) for p in entry['build']['research']['source_provenance'])
        metadata['installed_mvp']={'status':report['status'],'run_id':report['run_id'],'report':str((output/'report.html').resolve()),
                                   'correctness':report['correctness_status'],'import_path':installed_mvp.__file__}
        atomic_json(args.store/'smoke.json',metadata)
    print(json.dumps(metadata,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
