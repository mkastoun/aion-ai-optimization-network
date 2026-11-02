from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aion.compiler import ClangAdapter
from aion.errors import AionError
from aion.models import Candidate
from aion.optimization import BASELINE, DeterministicGenerator, validate_flags
from tests.helpers import process


class CompilerTests(unittest.TestCase):
    def test_missing_compiler_is_actionable(self):
        with patch("aion.compiler.shutil.which", return_value=None), self.assertRaisesRegex(AionError, "not found"):
            ClangAdapter()

    def test_detect_version_and_target(self):
        with patch("aion.compiler.shutil.which", return_value="/local/clang++"), patch(
                "aion.compiler.run_process", side_effect=[process("clang version 18.1.0\n"),
                                                          process("x86_64-linux-gnu\n")]):
            adapter = ClangAdapter()
        self.assertEqual(adapter.info.major, 18)
        self.assertEqual(adapter.info.target, "x86_64-linux-gnu")

    def test_preserves_cpp_driver_symlink_name(self):
        # Clang uses its invocation name to select C++ library linking.
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "clang"
            target.touch()
            driver = Path(directory) / "clang++"
            try:
                driver.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"Cannot create a compiler-driver symlink: {exc}")
            with patch("aion.compiler.shutil.which", return_value=str(driver)), patch(
                    "aion.compiler.run_process", side_effect=[process("clang version 18.1.0\n"),
                                                              process("x86_64-linux-gnu\n")]):
                adapter = ClangAdapter()
            self.assertEqual(Path(adapter.info.path), driver.absolute())

    def test_reject_other_compiler(self):
        with patch("aion.compiler.shutil.which", return_value="g++"), patch(
                "aion.compiler.run_process", return_value=process("g++ version 13\n")), self.assertRaises(AionError):
            ClangAdapter()

    def test_flag_allowlist(self):
        for flags in (("-O3", "-Xclang", "-load", "bad.so"), ("-Ofast",),
                      ("-O3", "-fprofile-instr-use=untrusted.profdata"),
                      ("-O3", "-O2"), ("-O3", "-O3"), ("-O3", "-funroll-loops", "-fno-unroll-loops")):
            with self.subTest(flags=flags), self.assertRaises(AionError):
                validate_flags(flags)
        for candidate in [BASELINE, *DeterministicGenerator().generate()]:
            self.assertEqual(validate_flags(candidate.flags), candidate.flags)

    def test_compile_failure_preserves_diagnostics(self):
        adapter = ClangAdapter.__new__(ClangAdapter)
        from tests.helpers import INFO
        adapter.info, adapter.timeout = INFO, 60
        with tempfile.TemporaryDirectory() as directory, patch(
                "aion.compiler.run_process", return_value=process("", code=1)):
            output = adapter.compile(Path(directory)/"missing.cpp", Path(directory)/"a.out", BASELINE)
        self.assertFalse(output["success"])
        self.assertIsNone(output["executable_bytes"])

    def test_compile_rejects_untrusted_flags_before_execution(self):
        adapter = ClangAdapter.__new__(ClangAdapter)
        with self.assertRaises(AionError):
            adapter.compile(Path("a.cpp"), Path("a.out"), Candidate("evil", ("-fplugin=evil",)))
