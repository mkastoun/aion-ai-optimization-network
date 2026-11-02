from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch

from aion.cli import main
from aion.errors import AionError
from aion.storage import atomic_json
from aion.registry import PresetRegistry
from tests.helpers import INFO
from tests import test_engine


class CliTests(unittest.TestCase):
    def invoke(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_doctor_missing_toolchain_json(self):
        with patch("aion.cli.ClangAdapter", side_effect=AionError("missing compiler")):
            code, stdout, _ = self.invoke(["doctor", "--json"])
        self.assertEqual(code, 2)
        self.assertIn('"ready": false', stdout)
        self.assertIn("missing compiler", stdout)

    def test_benchmark_missing_toolchain_is_graceful(self):
        with patch("aion.cli.ClangAdapter", side_effect=AionError("install Clang")):
            code, stdout, stderr = self.invoke(["benchmark"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("install Clang", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_no_presets_and_missing_report_are_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            code, stdout, _ = self.invoke(["--store", directory, "presets"])
            self.assertEqual(code, 0)
            self.assertIn("No verified", stdout)
            code, _, stderr = self.invoke(["--store", directory, "report", "--latest"])
            self.assertEqual(code, 2)
            self.assertIn("Cannot read JSON", stderr)

    def test_invalid_settings_before_compilation(self):
        code, _, stderr = self.invoke(["benchmark", "--iterations", "0"])
        self.assertEqual(code, 2)
        self.assertIn("Iterations", stderr)

    def test_report_rejects_non_experiment_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"foreign.json"
            atomic_json(path, {"schema_version": 1})
            code, _, stderr = self.invoke(["report", "--result", str(path)])
        self.assertEqual(code, 2)
        self.assertIn("Invalid experiment JSON", stderr)

    def test_reports_cannot_overwrite_preserved_raw_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"result.json"
            path.write_text('{"schema_version":1}', encoding="utf-8")
            before = path.read_bytes()
            code, _, stderr = self.invoke(["report", "--result", str(path), "--output", str(path)])
            self.assertEqual(code, 2)
            self.assertIn("must not overwrite", stderr)
            self.assertEqual(path.read_bytes(), before)

    def test_report_can_write_source_linked_gate_audit(self):
        run = test_engine.EngineTests().run_synthetic()
        with tempfile.TemporaryDirectory() as directory:
            source, audit = Path(directory)/"result.json", Path(directory)/"audit.json"
            atomic_json(source, run)
            before = source.read_bytes()
            code, _, stderr = self.invoke(["report", "--result", str(source), "--audit-json", str(audit)])
            self.assertEqual(code, 0, stderr)
            import json
            data = json.loads(audit.read_text())
            self.assertEqual(len(data["runs"][0]["source_sha256"]), 64)
            self.assertIn("o2", data["runs"][0]["assessments"])
            self.assertEqual(source.read_bytes(), before)

    def test_compile_rejects_invalid_source(self):
        code, _, stderr = self.invoke(["compile", "--preset", "local", "--source", "does-not-exist.cpp",
                                      "--output", "a.out"])
        self.assertEqual(code, 2)
        self.assertIn("existing C++ source", stderr)

    def test_optimize_independently_confirms_and_stores_preset(self):
        discovery = test_engine.EngineTests().run_synthetic()
        confirmation = deepcopy(discovery)
        confirmation["run_id"] = "fresh-confirmation"
        confirmation["settings"]["seed"] += 1
        with tempfile.TemporaryDirectory() as directory, patch("aion.cli.ClangAdapter"), patch(
                "aion.cli.run_experiment", side_effect=[discovery, confirmation]) as experiment:
            code, stdout, stderr = self.invoke(["--store", directory, "optimize", "--candidate", "o2"])
            presets = list((Path(directory)/"presets").glob("*.json"))
            self.assertEqual(len(presets), 1)
            self.assertEqual(len(list((Path(directory)/"results").glob("*.json"))), 2)
        self.assertEqual(code, 0, stderr)
        self.assertIn("Verified preset", stdout)
        self.assertEqual(experiment.call_count, 2)
        self.assertEqual(experiment.call_args.kwargs["purpose"], "independent_confirmation")

    def test_failed_confirmation_never_creates_a_preset(self):
        discovery = test_engine.EngineTests().run_synthetic()
        confirmation = deepcopy(discovery)
        confirmation["run_id"] = "failed-confirmation"
        confirmation["settings"]["seed"] += 1
        confirmation["benchmarks"]["array"]["configurations"]["o2"]["verification"]["passed"] = False
        with tempfile.TemporaryDirectory() as directory, patch("aion.cli.ClangAdapter"), patch(
                "aion.cli.run_experiment", side_effect=[discovery, confirmation]):
            code, stdout, _ = self.invoke(["--store", directory, "optimize", "--candidate", "o2"])
            self.assertEqual(list((Path(directory)/"presets").glob("*.json")), [])
        self.assertEqual(code, 0)
        self.assertIn("Preset rejected", stdout)

    def test_confirm_all_records_negative_results_without_promoting(self):
        discovery = test_engine.EngineTests().run_synthetic()
        for sample in discovery["benchmarks"]["array"]["configurations"]["o2"]["samples"]:
            sample["process"]["duration_seconds"] = .1
        confirmation = deepcopy(discovery)
        confirmation["run_id"] = "negative-confirmation"
        confirmation["settings"]["seed"] += 1
        with tempfile.TemporaryDirectory() as directory, patch("aion.cli.ClangAdapter"), patch(
                "aion.cli.run_experiment", side_effect=[discovery, confirmation]) as experiment:
            code, stdout, _ = self.invoke(["--store", directory, "optimize", "--candidate", "o2", "--confirm-all"])
            self.assertEqual(len(list((Path(directory)/"results").glob("*.json"))), 2)
            self.assertEqual(list((Path(directory)/"presets").glob("*.json")), [])
        self.assertEqual(code, 0)
        self.assertEqual(experiment.call_count, 2)
        self.assertIn("Independent confirmation recorded", stdout)

    def test_preset_reverification_and_local_compilation(self):
        discovery = test_engine.EngineTests().run_synthetic()
        confirmation = deepcopy(discovery)
        confirmation["run_id"] = "confirmed"
        confirmation["settings"]["seed"] += 1
        fresh = deepcopy(discovery)
        fresh["run_id"] = "reverification"
        configs = fresh["benchmarks"]["array"]["configurations"]
        configs["preset"] = configs.pop("o2")
        fresh["configurations"][1]["name"] = "preset"
        with tempfile.TemporaryDirectory() as directory:
            registry = PresetRegistry(Path(directory))
            registry.register("local-o2", "o2", discovery, confirmation)
            with patch("aion.cli.ClangAdapter") as adapter, patch(
                    "aion.cli.run_experiment", return_value=fresh):
                adapter.return_value.info = INFO
                code, stdout, stderr = self.invoke(["--store", directory, "verify", "--preset", "local-o2"])
            self.assertEqual(code, 0, stderr)
            self.assertIn("Preset verification: passed", stdout)
            source = Path(directory)/"app.cpp"
            source.write_text("int main() {}", encoding="utf-8")
            with patch("aion.cli.ClangAdapter") as adapter:
                adapter.return_value.info = INFO
                adapter.return_value.compile.return_value = {"success": True}
                code, stdout, stderr = self.invoke(["--store", directory, "compile", "--preset", "local-o2",
                                                   "--source", str(source), "--output", str(Path(directory)/"app")])
                self.assertEqual(adapter.return_value.compile.call_args.args[2].flags, ("-O2",))
            self.assertEqual(code, 0, stderr)
            self.assertIn("Compiled", stdout)
