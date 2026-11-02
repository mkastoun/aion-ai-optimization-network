import unittest

from aion.benchmarks import load_benchmarks
from aion.models import Limits
from aion.reference import expected
from aion.verification import check_output, verify_binary
from tests.helpers import process
from unittest.mock import patch
from pathlib import Path


class VerificationTests(unittest.TestCase):
    def test_memory_limit_failure_survives_zero_exit_race(self):
        result = process('123\n')
        result.memory_limited = True
        check = check_output(result, '123')
        self.assertFalse(check['passed'])
        self.assertIn('memory limit exceeded', check['reasons'])
        self.assertFalse(result.ok)

    def test_reference_matches_all_small_checked_in_cases(self):
        for benchmark in load_benchmarks():
            for case in benchmark.cases:
                if case["name"] in {"empty", "small", "alternate"}:
                    with self.subTest(workload=benchmark.name, case=case["name"]):
                        self.assertEqual(expected(benchmark.name, *map(int, case["args"])), case["expected"])

    def test_expected_output_does_not_hide_failed_process(self):
        self.assertTrue(check_output(process("123\n"), "123")["passed"])
        self.assertFalse(check_output(process("123\n", code=1), "123")["passed"])
        self.assertFalse(check_output(process("wrong\n"), "123")["passed"])
        result = process()
        result.timed_out = True
        self.assertFalse(check_output(result, "123")["passed"])

    def test_all_cases_are_checked_even_after_failure(self):
        benchmark = load_benchmarks("array")[0]
        with patch("aion.verification.run_process", return_value=process("wrong")) as runner:
            result = verify_binary(Path("local"), benchmark, Limits())
        self.assertFalse(result["passed"])
        self.assertEqual(runner.call_count, len(benchmark.cases))

    def test_selection_and_fingerprints(self):
        self.assertEqual(len(load_benchmarks("micro")), 5)
        self.assertEqual(len(load_benchmarks()), 10)
        self.assertEqual(len(load_benchmarks("applications")), 5)
        self.assertEqual(len(load_benchmarks("array,sorting")), 2)
        self.assertEqual(len(load_benchmarks("array")[0].fingerprint), 64)
        from aion.errors import AionError
        for name in ("missing", "array,array", "../array"):
            with self.assertRaises(AionError):
                load_benchmarks(name)
