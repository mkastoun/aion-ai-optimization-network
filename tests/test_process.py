import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
import json
from unittest.mock import patch

from aion.models import Limits
from aion.process import run_process


class ProcessTests(unittest.TestCase):
    def test_capture_exit_status_and_literal_arguments(self):
        result = run_process([sys.executable, "-c",
                              "import sys; print(sys.argv[1]); print('error',file=sys.stderr); sys.exit(4)",
                              "a space; $NOT_A_COMMAND"])
        self.assertEqual(result.stdout.strip(), "a space; $NOT_A_COMMAND")
        self.assertEqual(result.stderr.strip(), "error")
        self.assertEqual(result.returncode, 4)
        self.assertFalse(result.ok)

    def test_deterministic_environment(self):
        result = run_process([sys.executable, "-c", "import os; print(os.environ['LC_ALL'])"])
        self.assertTrue(result.ok)
        self.assertEqual(result.stdout.strip(), "C")

    def test_timeout(self):
        result = run_process([sys.executable, "-c", "import time; time.sleep(10)"],
                             Limits(timeout_seconds=.2))
        self.assertTrue(result.timed_out)
        self.assertLess(result.duration_seconds, 5)

    def test_output_limit(self):
        result = run_process([sys.executable, "-c", "import sys; sys.stdout.write('x'*1000000)"],
                             Limits(output_bytes=4096))
        self.assertTrue(result.output_limited)
        self.assertLessEqual(len(result.stdout), 4096)
        self.assertFalse(result.ok)

    @unittest.skipUnless(os.name == "posix", "POSIX supervisor metadata required")
    def test_missing_or_partial_supervisor_metadata_is_a_process_failure(self):
        with patch("aion.process.json.loads", side_effect=json.JSONDecodeError("truncated", "", 0)):
            result = run_process([sys.executable, "-c", "print(1)"])
        self.assertFalse(result.ok)
        self.assertEqual(result.returncode, 125)

    @unittest.skipUnless(os.name == "posix", "POSIX wait4 and rlimits required")
    def test_peak_rss_is_per_child(self):
        large = run_process([sys.executable, "-c", "x=bytearray(64*1024*1024); print(len(x))"])
        small = run_process([sys.executable, "-c", "print(1)"])
        self.assertTrue(large.ok and small.ok)
        self.assertGreater(large.peak_rss_bytes, small.peak_rss_bytes + 32*1024*1024)

    @unittest.skipUnless(sys.platform.startswith('linux'), "Linux RLIMIT_AS required; macOS uses an explicitly different resident-memory watchdog")
    def test_address_space_limit(self):
        result = run_process([sys.executable, "-c", "x=bytearray(512*1024*1024)"],
                             Limits(memory_mb=64))
        self.assertFalse(result.ok)
        self.assertIn("MemoryError", result.stderr)

    @unittest.skipUnless(os.name == "posix", "POSIX process groups required")
    def test_timeout_terminates_descendants(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "survived"
            child = "import time; from pathlib import Path; time.sleep(.7); Path(" + repr(str(marker)) + ").touch()"
            parent = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); time.sleep(10)"
            result = run_process([sys.executable, "-c", parent], Limits(timeout_seconds=.3))
            self.assertTrue(result.timed_out)
            time.sleep(.8)
            self.assertFalse(marker.exists())
