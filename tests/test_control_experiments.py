"""Synthetic control fixtures, not published performance evidence."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aion.benchmarks import load_benchmarks
from aion.controls import ExecutionControls
from aion.engine import ExperimentSettings, candidate_assessment, run_experiment
from aion.errors import AionError
from aion.experiments import CONTROL_CANDIDATES, control_diagnostics, run_control_series
from aion.models import Limits
from aion.provenance import file_sha256
from aion.registry import PresetRegistry
from aion.report import render_control_report, render_report, render_confirmation_report, render_run_comparison
from aion.reproducibility import compare_run_compatibility
from tests.test_engine import TestOnlyAdapter
from tests.test_reliable_benchmarking import synthetic_run, timed_record


class FileFixtureAdapter(TestOnlyAdapter):
    def compile(self, source, output, candidate):
        output.write_bytes(b"synthetic executable fixture, never executed")
        return {**super().compile(source, output, candidate), "binary_sha256": file_sha256(output)}


def control_record(binary, case, batches, limits, *, controls=None, control_delay_ns=0):
    record = timed_record("baseline", case, batches, limits)
    seconds = .01 + control_delay_ns / 1e9
    record["measurement"].update({"seconds_per_batch": seconds, "compute_seconds": batches*seconds,
                                  "compute_ns": round(batches*seconds*1e9), "control_delay_ns": control_delay_ns,
                                  "injected_control_ns": batches*control_delay_ns})
    record["process"]["duration_seconds"] = batches*seconds + .01
    if controls is not None:
        requested = controls.to_dict()["requested_cpus"]
        record["execution_controls"] = {"requested_cpus": requested, "effective_cpus": requested,
                                        "verified": True if requested else None}
    return record


class ExperimentalControlTests(unittest.TestCase):
    def run_controls(self):
        with patch("aion.engine.verify_binary", return_value={"passed": True}), patch(
                "aion.engine.measure_binary", side_effect=control_record):
            return run_experiment(FileFixtureAdapter(), load_benchmarks("matrix"), list(CONTROL_CANDIDATES),
                                  ExperimentSettings(iterations=7, warmups=1, bootstrap_resamples=500))

    def test_identical_aa_has_no_improvement_and_negative_is_detected(self):
        run = self.run_controls()
        diagnostic = control_diagnostics(run)
        verdicts = {row["control"]: row["verdict"] for row in diagnostic["rows"]}
        self.assertEqual(verdicts["control-aa"], "consistent_with_AA")
        self.assertEqual(verdicts["control-slowdown"], "verified_regression_control")
        self.assertEqual(diagnostic["false_positive_workloads"], [])
        self.assertTrue(all(row["identical_baseline_binary"] for row in diagnostic["rows"]))
        for candidate in CONTROL_CANDIDATES:
            self.assertFalse(candidate_assessment(run, candidate.name)["eligible"])

    def test_false_optimization_signal_is_audited_even_though_controls_cannot_publish(self):
        run = self.run_controls()
        for sample in run["benchmarks"]["matrix"]["configurations"]["control-aa"]["samples"]:
            sample["measurement"]["seconds_per_batch"] = .008
            sample["measurement"]["compute_seconds"] = sample["measurement"]["batches"]*.008
            sample["measurement"]["compute_ns"] = round(sample["measurement"]["compute_seconds"]*1e9)
            sample["process"]["duration_seconds"] = sample["measurement"]["compute_seconds"]+.01
        from aion.engine import comparison_for
        entry = run["benchmarks"]["matrix"]["configurations"]["control-aa"]
        entry["comparison"] = comparison_for(run, "matrix", "control-aa")
        diagnostics = control_diagnostics(run)
        self.assertEqual(diagnostics["false_positive_workloads"], ["matrix"])
        self.assertTrue(diagnostics["aa_performance_gate"]["eligible"])
        self.assertFalse(candidate_assessment(run, "control-aa")["eligible"])

    def test_noisy_slowdown_remains_inconclusive(self):
        run = self.run_controls()
        samples = run["benchmarks"]["matrix"]["configurations"]["control-slowdown"]["samples"]
        for index, sample in enumerate(samples):
            sample["measurement"]["seconds_per_batch"] = [.06, .1][index % 2]
        from aion.engine import comparison_for
        run["benchmarks"]["matrix"]["configurations"]["control-slowdown"]["comparison"] = comparison_for(run, "matrix", "control-slowdown")
        self.assertEqual(control_diagnostics(run)["rows"][1]["verdict"], "inconclusive")
        self.assertEqual(len(samples), 7)

    def test_series_balances_placement_order_and_changes_seeds(self):
        with patch("aion.controls.allowed_cpus", return_value=[0]), patch(
                "aion.engine.verify_binary", return_value={"passed": True}), patch(
                "aion.engine.measure_binary", side_effect=control_record):
            runs = run_control_series(FileFixtureAdapter(), load_benchmarks("matrix"),
                                      ExperimentSettings(iterations=5, warmups=1, bootstrap_resamples=200),
                                      Limits(), ExecutionControls((0,)), compare_unpinned=True)
        self.assertEqual([r["execution_controls"]["requested_cpus"] for r in runs], [None, [0], [0], None])
        self.assertEqual([r["settings"]["seed"] for r in runs], [1729, 1729, 1730, 1730])
        self.assertIn("false-positive", render_control_report(runs))


class ReproducibilityTests(unittest.TestCase):
    def test_cross_host_or_placement_cannot_confirm_or_pool(self):
        first, second = synthetic_run(), synthetic_run(seed=2, purpose="independent_confirmation")
        self.assertTrue(compare_run_compatibility(first, second)["compatible"])
        for mutation in ("host", "placement", "compiler"):
            other = deepcopy(second)
            if mutation == "host": other["host_start"]["host_fingerprint"] = "different-host"
            elif mutation == "placement": other["execution_controls"]["requested_cpus"] = [0]
            else: other["compiler"]["version"] = "different compiler"
            self.assertFalse(compare_run_compatibility(first, other)["compatible"])
            self.assertIn("side-by-side", render_run_comparison(first, other))
            with self.assertRaises(AionError): render_confirmation_report(first, other)
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(AionError):
                PresetRegistry(Path(directory)).register("invalid", "o2", first, other)

    def test_phase2_results_still_render_without_inventing_host_identity(self):
        first, second = synthetic_run(), synthetic_run(seed=2, purpose="independent_confirmation")
        for run in (first, second):
            run["methodology_version"] = 2
            run["aion_version"] = "0.2.0"
            for key in ("host_start", "host_end", "execution_controls", "build_provenance"):
                run.pop(key, None)
        self.assertIn("Phase 2", render_report(first))
        self.assertIn("paired gain", render_confirmation_report(first, second))
        self.assertTrue(compare_run_compatibility(first, second)["legacy_identity_unverified"])

    def test_changing_observational_load_does_not_change_compatibility(self):
        first, second = synthetic_run(), synthetic_run(seed=2, purpose="independent_confirmation")
        second["host_start"]["load_average"] = [100, 100, 100]
        second["host_start"]["frequency_proc_mhz"] = ["999"]
        self.assertTrue(compare_run_compatibility(first, second)["compatible"])

    def test_available_power_policy_changes_are_incompatible(self):
        first, second = synthetic_run(), synthetic_run(seed=2, purpose="independent_confirmation")
        second["host_start"]["turbo_controls_observed"] = {"cpufreq_boost": "changed"}
        self.assertFalse(compare_run_compatibility(first, second)["compatible"])
