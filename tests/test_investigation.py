import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from aion.investigation import restore_phase2_sources
from aion.errors import AionError


class InvestigationTests(unittest.TestCase):
    def test_frozen_source_extraction_is_fixed_member_only_and_hashed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root/"phase2.whl"
            manifest = {"workloads": {name: {"cases": [{"name": "performance", "args": ["0","1","1"], "expected": "0"}]}
                                      for name in ("sorting", "matrix")}}
            with ZipFile(wheel, "w") as archive:
                archive.writestr("aion_network-0.2.0.dist-info/METADATA", "Metadata-Version: 2.4\nVersion: 0.2.0\n")
                for name in ("sorting.cpp", "matrix.cpp", "common.hpp"):
                    archive.writestr("aion/workloads/"+name, "// fixture only\n")
                archive.writestr("aion/workloads/manifest.json", json.dumps(manifest))
                archive.writestr("../outside.txt", "must never extract")
            benchmarks, provenance = restore_phase2_sources(wheel, root/"restored")
            self.assertEqual([b.name for b in benchmarks], ["sorting", "matrix"])
            self.assertTrue(all(len(b.fingerprint)==64 for b in benchmarks))
            self.assertEqual(len(provenance["wheel_sha256"]), 64)
            self.assertFalse((root/"outside.txt").exists())

    def test_missing_or_wrong_source_bundle_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AionError):
                restore_phase2_sources(Path(directory)/"missing.whl", Path(directory)/"restored")
