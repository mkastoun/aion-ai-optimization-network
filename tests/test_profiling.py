"""Counter/parser fixtures are synthetic, not hardware measurement results."""
import errno
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aion.profiling import analyze_counters,probe_counters,resolve_sample_ips,run_profiles
from aion.engine import candidate_assessment
from aion.errors import AionError
from aion.registry import PresetRegistry
from tests.test_reliable_benchmarking import synthetic_run
from tests.helpers import process


def event(name,count,enabled=100,running=100,code=0):
    return {'name':name,'kind':'hardware','type':0,'config':0,'raw_count':count,
            'time_enabled_ns':enabled,'time_running_ns':running,'errno':code}


class CounterTests(unittest.TestCase):
    def test_raw_counts_and_unmultiplexed_derived_metrics(self):
        result=analyze_counters({'events':[event('cycles',10),event('instructions',20),
                                         event('cache-references',100),event('cache-misses',5)]})
        self.assertEqual(result['derived']['instructions_per_cycle']['value'],2)
        self.assertEqual(result['derived']['cache_miss_rate']['value'],.05)
        self.assertIsNone(result['derived']['branch_miss_rate']['value'])
        self.assertIsNone(result['events'][0]['scaled_estimate'])

    def test_multiplexing_is_labeled_and_ratios_suppressed(self):
        result=analyze_counters({'events':[event('cycles',10,running=50),event('instructions',20)]})
        self.assertTrue(result['events'][0]['multiplexed'])
        self.assertEqual(result['events'][0]['scaled_estimate'],20)
        self.assertIsNone(result['derived']['instructions_per_cycle']['value'])

    def test_permissions_missing_and_zero_running_are_not_zero_measurements(self):
        result=analyze_counters({'events':[event('cycles',None,None,None,errno.EPERM),
             event('instructions',None,None,None,errno.EOPNOTSUPP),event('cache-misses',0,running=0)]})
        self.assertEqual([e['status'] for e in result['events']],['permission_denied','unsupported','not_counted'])
        self.assertIsNone(result['events'][0]['raw_count'])
        self.assertEqual(result['derived']['instructions_per_cycle']['value'],None)
        self.assertEqual(analyze_counters({})['events'],[])

    def test_non_linux_counter_probe_is_graceful(self):
        with patch('aion.profiling.sys.platform','win32'):
            self.assertFalse(probe_counters(None)['available'])

    def test_unknown_sample_addresses_remain_unresolved(self):
        result=resolve_sample_ips([123,123,456],'',resolver=None)
        self.assertEqual(sum(e['sample_count'] for e in result['addresses']),3)
        self.assertTrue(all(e['symbol'] is None for e in result['addresses']))
        self.assertEqual(result['symbols'][0]['sample_count'],3)

    def test_nearest_library_symbol_is_not_accepted_without_a_matching_range(self):
        with tempfile.TemporaryDirectory() as directory:
            binary=Path(directory)/'object.so'
            header=bytearray(20);header[:4]=b'\x7fELF';header[5]=1;header[16]=3;binary.write_bytes(header)
            maps=f'1000-2000 r-xp 00000000 00:00 1 {binary}'
            def tool(command,limits):
                return process('misleading_nearest\n??:0\n' if command[0]=='addr2line' else '00000010 00000004 T actual\n')
            with patch('aion.profiling.shutil.which',side_effect=lambda name:'nm' if name=='nm' else None),patch('aion.profiling.run_process',side_effect=tool):
                unresolved=resolve_sample_ips([0x1100],maps,resolver='addr2line')['addresses'][0]
                verified=resolve_sample_ips([0x1011],maps,resolver='addr2line')['addresses'][0]
            self.assertIsNone(unresolved['symbol'])
            self.assertEqual(unresolved['nearest_symbol_hint'],'misleading_nearest')
            self.assertEqual(verified['symbol'],'actual')
            self.assertEqual(verified['resolution'],'verified-sized-function-range')

    def test_resymbolization_rejects_a_changed_object_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            binary=Path(directory)/'object.so';binary.write_bytes(b'not the recorded object')
            maps=f'1000-2000 r-xp 00000000 00:00 1 {binary}'
            result=resolve_sample_ips([0x1100],maps,expected_objects={str(binary):{'sha256':'different'}})
            self.assertIsNone(result['addresses'][0]['symbol'])
            self.assertIsNone(result['addresses'][0]['object_address'])

    def test_profiler_or_sanitizer_evidence_never_creates_presets(self):
        for kind in ('profiling','sanitizer-validation','measurement-quality'):
            run=synthetic_run();run['evidence_kind']=kind
            self.assertFalse(candidate_assessment(run,'o2')['eligible'])
            with tempfile.TemporaryDirectory() as directory,self.assertRaisesRegex(AionError,'Diagnostic'):
                PresetRegistry(Path(directory)).register('forbidden','o2',run,run)
