"""Synthetic environment/session fixtures; never native performance evidence."""
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

from aion.host import classify_environment, collect_host_diagnostics
from aion.errors import AionError
from aion.sessions import new_session,save_session,load_session
from aion.reproducibility import compare_run_compatibility
from tests.test_reliable_benchmarking import synthetic_run


class ReplicationTests(unittest.TestCase):
    def test_native_wsl_vm_container_detection_is_observational(self):
        self.assertEqual(classify_environment('6.8.0','flags : sse',linux=True)['classification'],'native-linux')
        self.assertEqual(classify_environment('6.6-microsoft-standard-WSL2','',linux=True)['classification'],'wsl2')
        self.assertEqual(classify_environment('6.8','flags : sse hypervisor',linux=True)['classification'],'virtual-machine')
        self.assertEqual(classify_environment('6.8','',linux=True,dmi={'product_name':'KVM'})['classification'],'virtual-machine')
        self.assertEqual(classify_environment('6.8','',linux=True,container='docker')['classification'],'container')
        self.assertEqual(classify_environment('windows','',linux=False)['classification'],'non-linux')
        self.assertFalse(classify_environment('6.8','',linux=True)['physical_cpu_placement_verified'])

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux sysfs topology capability required; non-Linux hosts explicitly leave these metrics unavailable')
    def test_topology_smt_and_missing_frequency_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory,patch('aion.host.allowed_cpus',return_value=[2]):
            root=Path(directory);topology=root/'devices/system/cpu/cpu2/topology';topology.mkdir(parents=True)
            for name,value in [('physical_package_id','0'),('core_id','1'),('thread_siblings_list','2,6')]:
                (topology/name).write_text(value)
            host=collect_host_diagnostics(root,root)
        self.assertEqual(host['topology'][0]['thread_siblings'],'2,6')
        self.assertEqual(host['topology'][0]['core_id'],'1')
        self.assertIsNone(host['frequency_sysfs'])
        self.assertFalse(host['system_settings_modified'])

    def test_session_round_trip_reboot_and_cross_host_rejection(self):
        host={'host_fingerprint':'test-host','boot_id_hash':'boot1','environment_classification':'native-linux'}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'session.json';session=new_session(host,'test only')
            save_session(path,session)
            self.assertEqual(load_session(path,host),session)
            with self.assertRaises(AionError):save_session(path,session)
            with self.assertRaises(AionError):load_session(path,{**host,'boot_id_hash':'boot2'})
            with self.assertRaises(AionError):load_session(path,{**host,'host_fingerprint':'other'})

    def test_cross_session_comparisons_keep_estimates_separate(self):
        first,second=synthetic_run(),synthetic_run(seed=2,purpose='independent_confirmation')
        comparison=compare_run_compatibility(first,second)
        self.assertTrue(comparison['compatible'])
        self.assertTrue(comparison['different_sessions'])
        self.assertIn('disabled',comparison['pooling'])
        second['session']={}
        self.assertFalse(compare_run_compatibility(first,second)['compatible'])
