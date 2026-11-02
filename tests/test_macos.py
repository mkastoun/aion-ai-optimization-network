"""Portability fixtures are unit checks; only native tests establish Mac execution."""
import ctypes
import hashlib
import os
from pathlib import Path
import sys
from unittest.mock import Mock, patch

import pytest

from aion.compiler import ClangAdapter, binary_format
from aion.controls import ExecutionControls, parse_cpus
from aion.darwin_memory import DarwinMemoryReader, TaskInfo
from aion.errors import AionError
from aion.models import CompilerInfo, Limits
from aion.platform_support import platform_capabilities
from aion.process import run_process
from aion.toolchain import find_llvm_tool, llvm_tool_candidates
from aion.validation import sanitizer_options
from tests.helpers import process


def test_macos_fixture_never_reads_linux_paths():
    from aion.host import collect_host_diagnostics
    environment=dict(system='Darwin',release='fixture',machine='arm64',cpu='fixture',cpu_count=8,cpu_flags=[])
    with patch('aion.host.sys.platform','darwin'),patch('aion.host.machine_environment',return_value=environment),patch(
        'aion.host.allowed_cpus',return_value=None),patch('aion.host._read',side_effect=AssertionError('Linux path accessed')):
        host=collect_host_diagnostics()
    assert host['environment_classification']=='macos' and host['topology'] is None
    assert host['observation_sources']['sysfs'] is None and host['boot_id_hash'] is None
    assert not host['virtualization']['physical_cpu_placement_verified']


def test_macos_auto_affinity_is_explicitly_unavailable():
    with patch('aion.controls.sys.platform','darwin'),patch('aion.controls.os.sched_setaffinity',create=True) as setter:
        control=parse_cpus('auto')
        assert control.cpu_affinity is None
        assert not control.to_dict()['supported'] and 'unpinned' in control.to_dict()['unsupported_reason']
        with pytest.raises(AionError,match='unavailable'):ExecutionControls((0,)).validate()
        setter.assert_not_called()


def test_macos_capabilities_fixture_does_not_claim_linux_features():
    with patch('aion.platform_support.sys.platform','darwin'),patch('aion.darwin_memory.DarwinMemoryReader'):
        caps=platform_capabilities()
    assert caps['os']=='macos' and not caps['address_space_limit'] and not caps['linux_host_metadata']
    assert not caps['cpu_affinity']['available'] and not caps['hardware_counters']['available']
    assert not caps['measurement_environment_validated']


def test_missing_macos_memory_protection_refuses_before_launch():
    with patch('aion.process.sys.platform','darwin'),patch('aion.darwin_memory.DarwinMemoryReader',side_effect=AionError('libproc unavailable')),patch('aion.process.subprocess.Popen') as launch:
        with pytest.raises(AionError,match='libproc'):run_process(['trusted-program'])
        launch.assert_not_called()


def test_macos_memory_abi_and_group_accounting_fixture():
    assert ctypes.sizeof(TaskInfo)==96
    reader=DarwinMemoryReader.__new__(DarwinMemoryReader)
    def listing(kind,group,pids,size):
        assert kind==2 and group==123
        if pids is not None:pids[0],pids[1]=11,12
        return 8
    reader.library=Mock(proc_listpids=listing)
    reader.resident_bytes=lambda pid:pid*10
    assert reader.group_resident_bytes(123)==230


def test_macos_failed_live_process_observation_is_not_zero():
    reader=DarwinMemoryReader.__new__(DarwinMemoryReader)
    reader.library=Mock(proc_pidinfo=Mock(return_value=0))
    with patch('aion.darwin_memory.os.kill'):
        with pytest.raises(AionError,match='live process'):reader.resident_bytes(123)
    with patch('aion.darwin_memory.os.kill',side_effect=ProcessLookupError):assert reader.resident_bytes(123)==0


def test_macos_enumeration_failure_is_not_ignored():
    reader=DarwinMemoryReader.__new__(DarwinMemoryReader)
    reader.library=Mock(proc_listpids=Mock(return_value=-1))
    with pytest.raises(AionError,match='enumerate'):reader.group_resident_bytes(123)


def test_macos_optional_counters_never_launch_helper(tmp_path):
    from aion.profiling import build_counter_helper,probe_counters,sample_hotspots,resolve_sample_ips
    adapter=Mock()
    with patch('aion.profiling.sys.platform','darwin'):
        assert not probe_counters(adapter)['available']
        assert not build_counter_helper(adapter,tmp_path)[1]['build']['success']
        assert not sample_hotspots(None,None,1,tmp_path,Limits())['available']
        assert not resolve_sample_ips([], '')['available']
    adapter.compile.assert_not_called()


def test_macos_leak_limitation_is_explicit_but_asan_remains_enabled():
    with patch('aion.validation.sys.platform','darwin'):options=sanitizer_options()
    assert 'detect_leaks=0' in options['ASAN_OPTIONS'] and 'halt_on_error=1' in options['ASAN_OPTIONS']
    assert 'halt_on_error=1' in options['UBSAN_OPTIONS']


@pytest.mark.parametrize('system',['linux','darwin','win32'])
def test_leak_detection_is_never_assumed_available(system):
    from aion.validation import leak_detection_status
    with patch('aion.validation.sys.platform',system):
        status=leak_detection_status()
        options=sanitizer_options()
    assert status['available'] is not True and status['reason']
    assert status['requested']==(system=='linux')
    assert ('detect_leaks=1' in options['ASAN_OPTIONS'])==(system=='linux')


@pytest.mark.parametrize('header,expected',[(b'\xcf\xfa\xed\xfe','Mach-O'),(b'\x7fELF','ELF'),(b'MZxx','PE'),(b'other','unknown')])
def test_binary_format_fixture(tmp_path,header,expected):
    path=tmp_path/'binary';path.write_bytes(header)
    assert binary_format(path)==expected


def test_apple_clang_is_distinct_from_upstream():
    with patch('aion.compiler.shutil.which',return_value='/fixture/clang++'),patch('aion.compiler.run_process',side_effect=[
        process('Apple clang version 17.0.0 (clang-1700.0.13.3)\n'),process('arm64-apple-darwin\n')]):
        adapter=ClangAdapter()
    assert adapter.info.family=='apple-clang' and adapter.info.path.endswith('clang++')


@pytest.mark.parametrize('family,compiler_version,tool_version,accepted',[
    ('clang','clang version 18.1.8','llvm-profdata version 18.1.8',True),
    ('clang','clang version 18.1.8','llvm-profdata version 19.1.0',False),
    ('clang','clang version 18.1.8','Apple LLVM version 18.0.0',False),
    ('apple-clang','Apple clang version 17 (clang-1700.0.13.3)','Apple LLVM version 17.0.0 (clang-1700.0.13.3)',True),
    ('apple-clang','Apple clang version 17 (clang-1700.0.13.3)','LLVM version 17.0.0',False),
    ('apple-clang','Apple clang version 17 (clang-1700.0.13.3)','Apple LLVM version 17.0.0 (clang-1700.1.1)',False),
])
def test_pgo_matching_vendor_major_and_apple_build(family,compiler_version,tool_version,accepted):
    adapter=ClangAdapter.__new__(ClangAdapter)
    adapter.info=CompilerInfo('/fixture/clang++',compiler_version,18 if family=='clang' else 17,'fixture',family)
    with patch('aion.compiler.llvm_tool_candidates',return_value=['/fixture/llvm-profdata']),patch('aion.compiler.run_process',return_value=process(tool_version)):
        if accepted:assert adapter._profdata_tool()[0]=='/fixture/llvm-profdata'
        else:
            with pytest.raises(AionError,match='matching'):adapter._profdata_tool()


def test_configured_tool_path_is_not_shell_content_or_silently_replaced():
    with patch.dict(os.environ,{'AION_LLVM_PROFDATA':'missing --extra'},clear=False),patch('aion.toolchain.shutil.which',return_value=None):
        with pytest.raises(AionError,match='unavailable'):llvm_tool_candidates('llvm-profdata',None)


def test_homebrew_prefix_discovery_preserves_driver_directory(tmp_path):
    directory=tmp_path/'custom-prefix/bin'
    tool=directory/'llvm-nm';directory.mkdir(parents=True);tool.touch()
    with patch.dict(os.environ,{'AION_LLVM_BIN':str(directory)}),patch('aion.toolchain.shutil.which',side_effect=lambda name:str(tool) if str(name)==str(tool) else None):
        assert find_llvm_tool('llvm-nm')==str(tool.absolute())


def test_statistics_and_catalog_contracts_remain_frozen():
    from aion import statistics
    from aion.benchmarks import load_benchmarks
    from aion.mvp_catalog import MVP_CATALOG
    from aion.research_catalog import CATALOG
    assert hashlib.sha256(Path(statistics.__file__).read_bytes()).hexdigest()=='9e2af3e31e7924fd88ff737c8cc2de48048987ca5223b4bc4f1950b8eb2a92b8'
    assert len(load_benchmarks())==10 and len(MVP_CATALOG)==31 and len(CATALOG)==17


@pytest.mark.skipif(sys.platform!='darwin',reason='Actual macOS libproc execution required; fixtures are not native verification')
def test_native_macos_resident_memory_limit_terminates_workload():
    result=run_process([sys.executable,'-c','import time; x=bytearray(256*1024*1024); time.sleep(10)'],Limits(timeout_seconds=8,memory_mb=96))
    assert result.memory_limited and not result.ok and not result.timed_out
    assert result.resource_protection['allocation_ceiling'] is False


@pytest.mark.skipif(sys.platform!='darwin',reason='Actual macOS compiler execution required')
@pytest.mark.integration
def test_native_macos_cpp_format_and_protection(tmp_path):
    from aion.benchmarks import load_benchmarks
    from aion.optimization import BASELINE
    from aion.verification import measure_binary
    adapter=ClangAdapter();benchmark=load_benchmarks('array')[0]
    binary=tmp_path/'array.exe';build=adapter.compile(benchmark.compilation_input,binary,BASELINE)
    assert build['success'] and build['binary_format']=='Mach-O'
    measured=measure_binary(binary,benchmark.case('small'),1,Limits())
    assert measured['passed'] and measured['process']['resource_protection']['allocation_ceiling'] is False
