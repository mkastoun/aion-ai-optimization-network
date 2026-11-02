"""Phase 2 tests use explicitly synthetic samples, never published measurements."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aion.benchmarks import load_benchmarks
from aion.calibration import calibrate
from aion.engine import ExperimentSettings, candidate_assessment, run_experiment
from aion.errors import AionError
from aion.models import Candidate, Limits
from aion.registry import PresetRegistry
from aion.report import render_confirmation_report, render_report
from aion.statistics import paired_comparison, summarize
from aion.verification import measure_binary
from tests.helpers import process
from tests.test_engine import TestOnlyAdapter


def timed_record(binary, case, batches, limits):
    unit = .008 if str(binary).endswith("-1.exe") else .01
    checksum = str(int(case["expected"]) * batches & ((1 << 64) - 1))
    data = {"protocol": "aion-compute-v1", "checksum": checksum,
            "batches": batches, "compute_ns": round(unit*batches*1e9), "setup_ns": 1000000}
    return {"passed": True, "reasons": [], "expected": checksum,
            "process": process(json.dumps(data), unit*batches + .01).to_dict(),
            "measurement": {**data, "compute_seconds": unit*batches,
                            "setup_seconds": .001, "seconds_per_batch": unit}}


def synthetic_run(seed=1, purpose="optimize", two_candidates=False):
    candidates = [Candidate("o2", ("-O2",))]
    if two_candidates:
        candidates.append(Candidate("unroll", ("-O3", "-funroll-loops")))
    with patch("aion.engine.verify_binary", return_value={"passed": True}), patch(
            "aion.engine.measure_binary", side_effect=timed_record):
        return run_experiment(TestOnlyAdapter(), load_benchmarks("array"), candidates,
                              ExperimentSettings(iterations=5, warmups=1, seed=seed,
                                                 bootstrap_resamples=200), purpose=purpose)


class CalibrationTests(unittest.TestCase):
    def test_calibration_reaches_band_and_keeps_discarded_pilots(self):
        result = calibrate(lambda batches: timed_record("baseline", {"expected": "1"}, batches, Limits()))
        self.assertTrue(result["passed"])
        self.assertGreater(result["batches"], 1)
        self.assertTrue(.25 <= result["median_compute_seconds"] <= .5)
        self.assertEqual(len(result["pilots"]), 6)

    def test_calibration_checks_correctness_and_honors_bounds(self):
        failed = calibrate(lambda batches: {"passed": False})
        self.assertFalse(failed["passed"])
        bounded = calibrate(lambda batches: timed_record("baseline", {"expected": "1"}, batches, Limits()),
                            max_batches=2)
        self.assertFalse(bounded["passed"])
        self.assertLessEqual(len(bounded["pilots"]), 24)

    def test_invalid_calibration_bounds(self):
        with self.assertRaises(ValueError):
            calibrate(lambda batches: {}, minimum=.5, maximum=.25)


class TimingProtocolTests(unittest.TestCase):
    def valid(self):
        return {"protocol": "aion-compute-v1", "checksum": "6", "batches": 3,
                "compute_ns": 300000000, "setup_ns": 5000000}

    def check(self, data, code=0):
        with patch("aion.verification.run_process", return_value=process(json.dumps(data), .4, code)):
            return measure_binary(Path("local"), {"args": ["7", "42", "1"], "expected": "2"}, 3, Limits())

    def test_normalizes_equal_work_and_keeps_wall_and_setup_separate(self):
        record = self.check(self.valid())
        self.assertTrue(record["passed"])
        self.assertAlmostEqual(record["measurement"]["seconds_per_batch"], .1)
        self.assertEqual(record["process"]["duration_seconds"], .4)
        self.assertEqual(record["measurement"]["setup_seconds"], .005)

    def test_rejects_tampered_malformed_impossible_or_failed_measurements(self):
        for field, value in (("checksum", "7"), ("batches", 4), ("compute_ns", -1),
                             ("compute_ns", 1000000000), ("setup_ns", -1),
                             ("batches", True), ("protocol", "foreign")):
            data = self.valid()
            data[field] = value
            self.assertFalse(self.check(data)["passed"], field)
        self.assertFalse(self.check("not a JSON object")["passed"])
        self.assertFalse(self.check(self.valid(), code=1)["passed"])

    def test_unsigned_checksum_wrap(self):
        data = self.valid()
        data["checksum"] = str((((1<<64)-1)*3) & ((1<<64)-1))
        with patch("aion.verification.run_process", return_value=process(json.dumps(data), .4)):
            result = measure_binary(Path("local"), {"args": [], "expected": str((1<<64)-1)}, 3, Limits())
        self.assertTrue(result["passed"])


class UncertaintyTests(unittest.TestCase):
    def compare(self, baseline, candidate, **kwargs):
        return paired_comparison(baseline, candidate,
                                 baseline_physical=[.375]*len(baseline), candidate_physical=[.375]*len(candidate),
                                 resamples=500, **kwargs)

    def test_paired_interval_and_preserved_thresholds(self):
        result = self.compare([.01]*11, [.008]*11)
        self.assertEqual(result["classification"], "improvement")
        self.assertTrue(result["acceptable"])
        self.assertEqual(result["uncertainty"]["block_length"], 4)
        self.assertAlmostEqual(result["uncertainty"]["improvement_ci_low"], .2)
        self.assertEqual(self.compare([.01]*11, [.0099]*11)["classification"], "no_clear_change")
        self.assertEqual(self.compare([.01]*11, [.011]*11)["classification"], "regression")

    def test_pairing_does_not_relax_noise_rule(self):
        baseline = [.01, .02]*6
        result = self.compare(baseline, [x*.8 for x in baseline])
        self.assertEqual(result["classification"], "inconclusive")
        self.assertFalse(result["acceptable"])

    def test_family_adjustment_and_seeded_reproducibility(self):
        baseline = [.1]*11
        candidate = [.099, .1, .098, .1, .099, .099, .1, .098, .099, .1, .099]
        single = self.compare(baseline, candidate, seed=17)
        family = self.compare(baseline, candidate, seed=17, comparisons=20)
        self.assertEqual(family, self.compare(baseline, candidate, seed=17, comparisons=20))
        self.assertLessEqual(family["uncertainty"]["improvement_ci_low"], single["uncertainty"]["improvement_ci_low"])
        self.assertGreaterEqual(family["uncertainty"]["improvement_ci_high"], single["uncertainty"]["improvement_ci_high"])

    def test_drift_and_outliers_are_recorded_without_deletion(self):
        summary = summarize([.1]*6 + [.2]*5)
        self.assertTrue(summary["drifting"])
        self.assertGreater(summary["outlier_count"], 0)
        self.assertEqual(summary["count"], 11)
        self.assertEqual(summary["outliers_removed"], 0)

    def test_missing_pairs_rejected(self):
        with self.assertRaises(AionError):
            self.compare([.1]*5, [.1]*4)


class ReliableEngineTests(unittest.TestCase):
    def test_process_failure_preserves_all_samples_already_collected(self):
        collected, calls = [], 0
        def fail_later(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 20:
                raise AionError("simulated control change during measurement")
            return timed_record(*args, **kwargs)
        with patch("aion.engine.verify_binary", return_value={"passed": True}), patch(
                "aion.engine.measure_binary", side_effect=fail_later), self.assertRaises(AionError):
            run_experiment(TestOnlyAdapter(), load_benchmarks("array"), [Candidate("o2", ("-O2",))],
                           ExperimentSettings(iterations=7, warmups=1, bootstrap_resamples=200), on_failure=collected.append)
        self.assertEqual(len(collected), 1)
        self.assertEqual(collected[0]["status"], "failed")
        self.assertGreater(sum(len(e["samples"]) for e in collected[0]["benchmarks"]["array"]["configurations"].values()), 0)

    def test_calibration_samples_do_not_enter_measurements(self):
        run = synthetic_run()
        entry = run["benchmarks"]["array"]["configurations"]["o2"]
        self.assertEqual(len(entry["samples"]), 5)
        self.assertGreater(len(entry["calibration"]["pilots"]), 0)
        self.assertEqual(entry["summary"]["median_seconds"], .008)
        self.assertTrue(candidate_assessment(run, "o2")["eligible"])

    def test_each_candidate_gets_adjacent_balanced_baseline_pairs(self):
        run = synthetic_run(two_candidates=True)
        benchmark = run["benchmarks"]["array"]
        measured = [r for r in benchmark["schedule"] if r["phase"] == "measurement"]
        self.assertEqual(len(benchmark["configurations"]["baseline"]["samples"]), 10)
        orders = {"o2": [], "unroll": []}
        for index in range(0, len(measured), 2):
            pair = measured[index:index+2]
            self.assertEqual(pair[0]["pair_id"], pair[1]["pair_id"])
            self.assertEqual({p["configuration"] for p in pair}, {"baseline", pair[0]["pair_candidate"]})
            orders[pair[0]["pair_candidate"]].append(pair[0]["configuration"] == "baseline")
        for order in orders.values():
            self.assertEqual(sum(order), 3)

    def test_confirmation_changes_input_and_schedule_seeds_and_rebuilds(self):
        discovery = synthetic_run()
        confirmation = synthetic_run(seed=2, purpose="independent_confirmation")
        benchmark = discovery["benchmarks"]["array"]
        self.assertNotEqual(benchmark["measurement_case"]["args"][1], confirmation["benchmarks"]["array"]["measurement_case"]["args"][1])
        with tempfile.TemporaryDirectory() as directory:
            registry = PresetRegistry(Path(directory))
            registry.register("phase2", "o2", discovery, confirmation)
            self.assertEqual(registry.load("phase2")["verification"]["methodology_version"], 4)
            confirmation["benchmarks"]["array"]["measurement_case"] = benchmark["measurement_case"]
            with self.assertRaisesRegex(AionError, "different input seeds"):
                registry.register("bad-seed", "o2", discovery, confirmation)

    def test_promotion_recomputes_pairs_and_rejects_missing_uncertainty_evidence(self):
        run = synthetic_run()
        sample = run["benchmarks"]["array"]["configurations"]["o2"]["samples"][0]
        sample["pair_id"] = "mismatched"
        self.assertFalse(candidate_assessment(run, "o2")["eligible"])

    def test_pgo_profile_cannot_be_distributed_as_flag_only_preset(self):
        run = synthetic_run()
        run["configurations"][1]["build_mode"] = "pgo"
        assessment = candidate_assessment(run, "o2")
        self.assertFalse(assessment["eligible"])
        self.assertTrue(any("application-specific" in reason for reason in assessment["reasons"]))

    def test_reports_explain_units_uncertainty_and_confirmation(self):
        discovery, confirmation = synthetic_run(), synthetic_run(seed=2, purpose="independent_confirmation")
        report = render_report(discovery)
        for text in ("Phase 4", "Unit ms", "Adjusted interval", "Setup ms", "No outliers", "250–500"):
            self.assertIn(text, report)
        combined = render_confirmation_report(discovery, confirmation)
        self.assertIn("repeatable improvement", combined)
        self.assertIn(confirmation["run_id"], combined)
        self.assertIn("Duration and correctness audit", combined)
        self.assertIn("Discovery paired gain", combined)
        with self.assertRaises(AionError):
            render_confirmation_report(discovery, discovery)

    def test_relaxed_exploration_settings_cannot_relax_promotion_limits(self):
        run = synthetic_run()
        run["settings"]["noise_threshold"] = .9
        run["settings"]["target_min_seconds"] = .001
        for entry in run["benchmarks"]["array"]["configurations"].values():
            for sample in entry["samples"]:
                sample["measurement"]["compute_seconds"] = .1
        self.assertFalse(candidate_assessment(run, "o2")["eligible"])
