"""Separate diagnostics on hash-verified archived research executables."""
from dataclasses import asdict
from pathlib import Path
import shutil
import sys

from .compiler import ClangAdapter
from .controls import parse_cpus
from .errors import AionError
from .evidence import evidence_header
from .models import Limits
from .process import run_process
from .profiling import build_counter_helper,profile_execution
from .provenance import file_sha256
from .research import load_attempts,declared_catalog
from .research_catalog import CATALOG,benchmark_for,variant_benchmark
from .storage import atomic_json
from .verification import verify_binary
from .toolchain import find_llvm_tool


def diagnose(study,directory,session,panels=None):
    selected=panels or study['declaration']['panels']
    catalog,_=declared_catalog(study['declaration'].get('catalog_provider','research-v1'))
    runs=load_attempts(study)
    if not selected or any(n not in runs for n in selected) or len(selected)!=len(set(selected)):
        raise AionError('Choose unique completed declared panels.')
    adapter=ClangAdapter(study['declaration']['compiler']['path'])
    if asdict(adapter.info)!=study['declaration']['compiler'] or adapter.build_provenance()!=study['declaration']['build_provenance']:
        raise AionError('Research diagnostic compiler identity changed.')
    cpus=study['declaration']['execution_controls']['requested_cpus']
    controls=parse_cpus(','.join(map(str,cpus)) if cpus is not None else 'none')
    result=evidence_header('research-diagnostics',adapter=adapter,controls=controls,session=session)
    root=directory/result['run_id'];root.mkdir(parents=True,exist_ok=True)
    helper,build=build_counter_helper(adapter,root)
    result.update(panels={},counter_helper=build,status='completed',promotion_eligible=False,
        scope='separate whole-process counters and static codegen; never compute-only timing or causal proof')
    for panel in catalog:
        if panel.name not in selected:continue
        run=runs[panel.name];benchmark=benchmark_for(panel)
        if result['host_start']['host_fingerprint']!=run['host_start']['host_fingerprint']:
            raise AionError('Research counters must run on the original host; cross-host attribution refused.')
        b=run['benchmarks'][benchmark.name]
        batches=b['configurations']['baseline'].get('calibration',{}).get('batches')
        if not isinstance(batches,int) or batches<1:raise AionError('No baseline calibrated work unit.')
        output={};result['panels'][panel.name]=output
        for name,recipe in (('baseline',panel.reference),('candidate',panel.candidate)):
            entry=b['configurations'][name]
            binary=Path(entry['build']['research']['saved_binary'])
            if file_sha256(binary)!=entry['build']['binary_sha256']:
                raise AionError('Archived research executable changed.')
            dest=root/panel.name/name;dest.mkdir(parents=True,exist_ok=True)
            actual=variant_benchmark(benchmark,recipe)
            record={'source_run_id':run['run_id'],'binary_sha256':file_sha256(binary),'binary_matches_timing':True,
                    'verification':verify_binary(binary,actual,Limits(),controls=controls),
                    'batches':batches,'input':b['measurement_case'],'samples':[],'ir':[]}
            output[name]=record
            if not record['verification']['passed']:
                record['status']='incorrect';result['status']='failed';continue
            if build['build']['success']:
                for i in range(3):
                    record['samples'].append(profile_execution(helper,binary,b['measurement_case'],batches,Limits(),dest/f'counter-{i}.json',controls))
            else:record['counter_unavailable']=build['build'].get('reason','helper compile failed')
            try:tool=find_llvm_tool('llvm-objdump',adapter.info,fallback=() if sys.platform == 'darwin' else ('objdump',))
            except AionError as exc:
                tool=None;record['disassembly']={'available':False,'reason':str(exc)}
            if tool:
                dump=run_process([tool,'-d','-C',str(binary)],Limits(timeout_seconds=60,output_bytes=64*1024*1024))
                assembly=dest/'disassembly.txt';assembly.write_text(dump.stdout,encoding='utf-8')
                record['disassembly']={'path':str(assembly.resolve()),'sha256':file_sha256(assembly),'process':dump.to_dict()}
            elif 'disassembly' not in record:record['disassembly']={'available':False,'reason':'No compatible local LLVM disassembler found'}
            profile=entry['build'].get('pgo',{}).get('saved_profile')
            if profile and file_sha256(Path(profile))!=entry['build']['pgo']['profile_sha256']:
                raise AionError('Archived profile changed.')
            for i,source in enumerate(actual.sources):
                irpath=dest/f'tu-{i}.ll';remarks=dest/f'tu-{i}-remarks.txt'
                command=[adapter.info.path,'-std=c++17',*recipe.flags,*([f'-fprofile-instr-use={profile}'] if profile else []),
                         '-S','-emit-llvm','-Rpass=inline|loop-vectorize','-Rpass-missed=inline|loop-vectorize',
                         '-Rpass-analysis=loop-vectorize',str(source.resolve()),'-o',str(irpath.resolve())]
                execution=run_process(command,Limits(timeout_seconds=60,memory_mb=2048,output_bytes=64*1024*1024))
                remarks.write_text(execution.stderr,encoding='utf-8')
                record['ir'].append({'source':str(source.resolve()),'path':str(irpath.resolve()),'sha256':file_sha256(irpath),
                                     'remarks':str(remarks.resolve()),'process':execution.to_dict(),
                                     'scope':'pre-link per-TU IR, not final LTO decisions'})
            record['status']='diagnosed'
            atomic_json(root/'partial.json',result)
    atomic_json(root/'diagnostics.json',result)
    return result
