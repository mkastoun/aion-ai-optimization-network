from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from aion.controls import ExecutionControls, allowed_cpus, parse_cpus
from aion.errors import AionError
from aion.host import collect_host_diagnostics
from aion.models import Limits
from aion.process import run_process


class HostControlTests(unittest.TestCase):
    def test_validate_cpu_selection_and_disable(self):
        with patch("aion.controls.allowed_cpus", return_value=[2, 4, 5]):
            self.assertEqual(parse_cpus("auto").cpu_affinity, (2,))
            self.assertEqual(parse_cpus("2,4-5").cpu_affinity, (2, 4, 5))
            self.assertIsNone(parse_cpus("none").cpu_affinity)
            for value in ("3", "2,2", "5-2", "abc", "-1"):
                with self.subTest(value=value), self.assertRaises(AionError):
                    parse_cpus(value)

    def test_unsupported_affinity_is_explicit(self):
        with patch("aion.controls.allowed_cpus", return_value=None):
            with self.assertRaisesRegex(AionError, "unavailable"):
                ExecutionControls((0,)).validate()
            ExecutionControls().validate()

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux affinity required")
    def test_affinity_applies_to_actual_child_and_parent_is_unchanged(self):
        original = allowed_cpus()
        controls = ExecutionControls((original[0],))
        result = run_process([sys.executable, "-c",
                              "import os,json; print(json.dumps({'pid':os.getpid(),'cpus':sorted(os.sched_getaffinity(0))}))"],
                             Limits(), controls=controls)
        self.assertTrue(result.ok, result)
        data = json.loads(result.stdout)
        self.assertEqual(data["cpus"], [original[0]])
        self.assertEqual(data["pid"], result.workload_pid)
        self.assertTrue(result.affinity["verified_before_exec"])
        self.assertEqual(allowed_cpus(), original)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux worker required")
    def test_affinity_set_failure_is_a_recorded_process_failure(self):
        # Parent validation is not enough; the child must handle a changed mask.
        with patch("aion.controls.allowed_cpus", return_value=[999999]):
            result = run_process([sys.executable, "-c", "print('must not run')"],
                                 controls=ExecutionControls((999999,)))
        self.assertFalse(result.ok)
        self.assertNotIn("must not run", result.stdout)

    def test_unavailable_host_metrics_are_not_fabricated(self):
        with tempfile.TemporaryDirectory() as directory, patch("aion.host.allowed_cpus", return_value=[0]):
            empty = Path(directory)
            host = collect_host_diagnostics(empty, empty)
        self.assertIsNone(host["frequency_sysfs"])
        self.assertIsNone(host["thermal"])
        self.assertIsNone(host["power"])
        self.assertIn("sysfs frequency/governor", host["unavailable"])
        self.assertFalse(host["system_settings_modified"])
        self.assertEqual(len(host["host_fingerprint"]), 64)

    def test_host_fingerprint_does_not_include_load_and_frequency(self):
        first, second = collect_host_diagnostics(), collect_host_diagnostics()
        self.assertEqual(first["host_fingerprint"], second["host_fingerprint"])
