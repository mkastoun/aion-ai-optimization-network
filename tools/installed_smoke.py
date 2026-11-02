"""Run a clean-venv wheel smoke from outside the source repository."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',type=Path,required=True)
    parser.add_argument('--mvp',action='store_true')
    args=parser.parse_args()
    repository=Path(__file__).resolve().parents[1]
    assert not Path.cwd().resolve().is_relative_to(repository),'Run from outside the repository'
    args.store=args.store.resolve()
    assert not args.store.exists(),'Use a fresh evidence directory'
    args.store.mkdir(parents=True)
    import aion
    from aion.benchmarks import load_benchmarks
    from aion.compiler import ClangAdapter
    from aion.models import Limits
    from aion.optimization import BASELINE
    from aion.verification import verify_binary,measure_binary
    package=Path(aion.__file__).resolve().parent
    assert package.is_relative_to(Path(sys.prefix).resolve()),aion.__file__
    assert not package.is_relative_to(repository/'src'),aion.__file__
    assert aion.__version__=='0.6.0.dev0'
    distribution=importlib.metadata.distribution('aion-network')
    assert distribution.version==aion.__version__
    assert any(e.name=='aion' and e.value=='aion.cli:main' for e in distribution.entry_points)
    console=Path(sys.executable).parent/('aion.exe' if sys.platform=='win32' else 'aion')
    assert console.is_file(),console
    metadata={'version':aion.__version__,'import_path':str(package),'python_prefix':sys.prefix,
              'cwd':str(Path.cwd()),'source_checkout_imported':False,'commands':[],'workloads':{}}
    def command(name,parts,timeout=900):
        executed=subprocess.run([str(console),*parts],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
        (args.store/(name+'.txt')).write_text(executed.stdout,encoding='utf-8')
        metadata['commands'].append({'args':[str(console),*parts],'returncode':executed.returncode})
        assert executed.returncode==0,executed.stdout
        return executed.stdout
    command('cli-help',['--help'],30)
    command('doctor',['doctor','--json'],120)
    command('mvp-list',['mvp','list','--json'],30)
    adapter=ClangAdapter()
    for benchmark in load_benchmarks('array,records'):
        assert all(p.resolve().is_relative_to(package) for p in benchmark.source_files)
        binary=args.store/(benchmark.name+'.exe')
        build=adapter.compile(benchmark.compilation_input,binary,BASELINE)
        assert build['success'],build
        checked=verify_binary(binary,benchmark,Limits(timeout_seconds=30))
        measured=measure_binary(binary,benchmark.case('small'),1,Limits())
        assert checked['passed'] and measured['passed'],(checked,measured)
        metadata['workloads'][benchmark.name]={'build':build,'verification':checked,'measurement':measured}
    if args.mvp:
        assert sys.platform.startswith('linux') or sys.platform=='darwin'
        output=args.store/'mvp'
        command('mvp',['mvp','demo','--workload','array','--max-candidates','1','--iterations','5',
            '--warmups','1','--commands','700','--seconds','300','--cpus','auto' if sys.platform.startswith('linux') else 'none',
            '--output',str(output)])
        report=json.loads((output/'report.json').read_text())
        assert report['status']=='completed' and report['correctness_status']=='Correctness passed'
        assert not report['promotion_eligible'] and not report['phase6_scientific_ready']
        for row in report['candidates']:
            for evidence in row['raw_evidence']:
                for entry in evidence['configurations'].values():
                    assert all(Path(p['path']).is_relative_to(package) for p in entry['build']['research']['source_provenance'])
        metadata['mvp']={'run_id':report['run_id'],'status':report['status'],'report':str(output/'report.html')}
    metadata.update(status='passed',scope='installed package functionality; no scientific performance claim')
    (args.store/'smoke.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in metadata.items() if k!='workloads'},indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
