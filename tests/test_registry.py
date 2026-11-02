from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from aion.engine import candidate_assessment
from aion.errors import AionError
from aion.registry import PresetRegistry
from aion.storage import atomic_json
from tests.helpers import INFO, confirmation, evidence


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.registry = PresetRegistry(Path(self.directory.name))
        self.discovery = evidence()

    def test_register_roundtrip_and_no_overwrite(self):
        self.registry.register("test-o2-v1", "o2", self.discovery, confirmation(self.discovery))
        preset = self.registry.load("test-o2-v1")
        self.assertEqual(preset["flags"], ["-O2"])
        self.assertEqual(preset["verification"]["improved_workloads"], ["array"])
        self.assertEqual(self.registry.list_names(), ["test-o2-v1"])
        with self.assertRaisesRegex(AionError, "already exists"):
            self.registry.register("test-o2-v1", "o2", self.discovery, confirmation(self.discovery))

    def test_reject_same_evidence_or_schedule(self):
        for other in (self.discovery, {**self.discovery, "run_id": "new"}):
            with self.assertRaises(AionError):
                self.registry.register("test", "o2", self.discovery, other)

    def test_reject_changed_flags_sources_and_environment(self):
        for field in ("flags", "fingerprint", "cpu"):
            other = confirmation(self.discovery)
            if field == "flags":
                other["configurations"][1]["flags"] = ["-Os"]
            elif field == "fingerprint":
                other["benchmarks"]["array"]["fingerprint"] = "changed"
            else:
                other["environment"]["cpu"] = "changed"
            with self.subTest(field=field), self.assertRaises(AionError):
                self.registry.register("test", "o2", self.discovery, other)

    def test_reject_incorrect_missing_noisy_regressed_and_short_data(self):
        for kind in ("incorrect", "missing", "noisy", "regression", "short", "insufficient"):
            run = deepcopy(self.discovery)
            entry = run["benchmarks"]["array"]["configurations"]["o2"]
            if kind == "incorrect":
                entry["verification"]["passed"] = False
            elif kind == "missing":
                entry["status"], entry["verification"] = "unsupported", None
            elif kind == "insufficient":
                entry["samples"].pop()
            else:
                for index, sample in enumerate(entry["samples"]):
                    sample["process"]["duration_seconds"] = (
                        [.03, .2][index % 2] if kind == "noisy" else .12 if kind == "regression" else .001)
            self.assertFalse(candidate_assessment(run, "o2")["eligible"], kind)

    def test_reject_regression_on_another_workload(self):
        run = deepcopy(self.discovery)
        second = deepcopy(run["benchmarks"]["array"])
        run["benchmarks"]["sorting"] = second
        for sample in second["configurations"]["o2"]["samples"]:
            sample["process"]["duration_seconds"] = .15
        self.assertFalse(candidate_assessment(run, "o2")["eligible"])

    def test_no_promotion_without_warmups(self):
        self.discovery["settings"]["warmups"] = 0
        for entry in self.discovery["benchmarks"]["array"]["configurations"].values():
            entry["warmups"] = []
        self.assertFalse(candidate_assessment(self.discovery, "o2")["eligible"])

    def test_path_traversal_rejected(self):
        for name in ("../outside", "a/b", "", "AION", "x" * 65):
            with self.subTest(name=name), self.assertRaises(AionError):
                self.registry.path(name)

    def test_load_rejects_unsafe_edited_flags(self):
        self.registry.register("test", "o2", self.discovery, confirmation(self.discovery))
        data = self.registry.load("test")
        data["flags"] = ["-O3", "-fplugin=untrusted"]
        atomic_json(self.registry.path("test"), data)
        with self.assertRaises(AionError):
            self.registry.load("test")

    def test_compiler_mismatch_rejected(self):
        self.registry.register("test", "o2", self.discovery, confirmation(self.discovery))
        preset = self.registry.load("test")
        with self.assertRaisesRegex(AionError, "compiler mismatch"):
            self.registry.check_compatibility(preset, replace(INFO, major=19), self.discovery["environment"], [])
