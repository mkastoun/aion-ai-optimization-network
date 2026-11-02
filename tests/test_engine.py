from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aion.benchmarks import load_benchmarks
from aion.engine import ExperimentSettings, candidate_assessment, run_experiment
from aion.errors import AionError
from aion.models import Candidate, Limits
from aion.optimization import BASELINE
from aion.report import render_report
from aion.storage import ResultStore, atomic_json, read_json
from tests.helpers import INFO, process


class TestOnlyAdapter:
    """Synthetic orchestration fixture; not a compiler or performance demo."""
    info = INFO

    def build_provenance(self):
        return {"compiler_binary_sha256": "f"*64, "linker_binary_sha256": "e"*64,
                "linker_version": "synthetic test fixture", "cxx_library_sha256": None}

    def probe(self, candidate):
        return {"supported": True}

    def compile(self, source, output, candidate):
        return {"success": True, "seconds": .2, "executable_bytes": 1000,
                "process": process().to_dict()}


class EngineTests(unittest.TestCase):
    def run_synthetic(self, **kwargs):
        benchmark = load_benchmarks("array")[0]
        def execute(command, limits):
            duration = .1 if command[0].endswith("-0.exe") else .08
            return process(benchmark.performance_case["expected"], duration)
        with patch("aion.engine.verify_binary", return_value={"passed": True}), patch(
                "aion.engine.run_process", side_effect=execute):
            return run_experiment(TestOnlyAdapter(), [benchmark], [Candidate("o2", ("-O2",))],
                                  ExperimentSettings(iterations=7, warmups=1, calibrate=False), **kwargs)

    def test_interleaved_measurements_and_full_record(self):
        run = self.run_synthetic()
        benchmark = run["benchmarks"]["array"]
        self.assertEqual(run["status"], "completed")
        self.assertEqual(len(benchmark["schedule"]), 16)
        for entry in benchmark["configurations"].values():
            self.assertEqual(len(entry["samples"]), 7)
            self.assertEqual(len(entry["warmups"]), 1)
        self.assertTrue(candidate_assessment(run, "o2")["eligible"])
        self.assertEqual(benchmark["configurations"]["o2"]["comparison"]["classification"], "improvement")
        self.assertEqual({x["configuration"] for x in benchmark["schedule"][:2]}, {"baseline", "o2"})

    def test_incorrect_candidate_never_measured(self):
        benchmark = load_benchmarks("array")[0]
        with patch("aion.engine.verify_binary", side_effect=[{"passed": True}, {"passed": False}]), patch(
                "aion.engine.run_process", return_value=process(benchmark.performance_case["expected"])):
            run = run_experiment(TestOnlyAdapter(), [benchmark], [Candidate("o2", ("-O2",))],
                                 ExperimentSettings(calibrate=False))
        entry = run["benchmarks"]["array"]["configurations"]["o2"]
        self.assertEqual(entry["status"], "incorrect")
        self.assertEqual(entry["samples"], [])
        self.assertFalse(candidate_assessment(run, "o2")["eligible"])

    def test_runtime_correctness_failure_invalidates_measurements(self):
        benchmark = load_benchmarks("array")[0]
        with patch("aion.engine.verify_binary", return_value={"passed": True}), patch(
                "aion.engine.run_process", return_value=process("wrong")):
            run = run_experiment(TestOnlyAdapter(), [benchmark], [Candidate("o2", ("-O2",))],
                                 ExperimentSettings(calibrate=False))
        self.assertEqual(run["status"], "baseline_failed")
        self.assertIsNone(run["benchmarks"]["array"]["configurations"]["o2"]["summary"])

    def test_unsupported_baseline_is_a_recorded_failure(self):
        adapter = TestOnlyAdapter()
        adapter.probe = lambda candidate: {"supported": False}
        run = run_experiment(adapter, load_benchmarks("array"), [])
        self.assertEqual(run["status"], "baseline_failed")

    def test_unique_names_and_valid_settings(self):
        for settings in ({"iterations": 0}, {"warmups": -1}, {"noise_threshold": float("nan")},
                         {"min_improvement": 2}):
            with self.assertRaises(AionError):
                ExperimentSettings(**settings)
        with self.assertRaises(AionError):
            run_experiment(TestOnlyAdapter(), load_benchmarks("array"), [BASELINE])
        for settings in ({"timeout_seconds": 0}, {"memory_mb": 1}, {"timeout_seconds": float("inf")}):
            with self.assertRaises(AionError):
                Limits(**settings)

    def test_report_and_json_roundtrip(self):
        run = self.run_synthetic()
        with tempfile.TemporaryDirectory() as directory:
            store = ResultStore(Path(directory))
            path = store.save(run)
            self.assertEqual(store.latest(), path)
            self.assertEqual(read_json(path), run)
        report = render_report(run)
        for expected in ("AION performance comparison", "Peak RSS", "improvement", "20.000%", "-O3"):
            self.assertIn(expected, report)

    def test_storage_rejects_corrupt_schema_and_latest_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root/"bad.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(AionError):
                read_json(path)
            atomic_json(root/"latest.json", {"schema_version": 1, "run_id": "../../outside"})
            with self.assertRaises(AionError):
                ResultStore(root).latest()
