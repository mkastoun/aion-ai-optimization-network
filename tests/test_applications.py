import json
from pathlib import Path
import tempfile
import unittest

from aion.application_reference import graph_distances, logs_output, records_output
from aion.benchmarks import Benchmark, load_benchmarks


class ApplicationTests(unittest.TestCase):
    def test_three_real_linked_applications_are_manifest_driven(self):
        applications = load_benchmarks("applications")
        self.assertEqual({b.name for b in applications}, {"records", "graph", "logs", "image", "kv"})
        for benchmark in applications:
            self.assertGreaterEqual(len(benchmark.sources), 3)
            self.assertTrue(all(path.is_file() for path in benchmark.source_files))
            self.assertNotEqual(benchmark.case("training")["args"][1], benchmark.performance_case["args"][1])
            self.assertNotEqual(benchmark.case("confirmation")["args"][1], benchmark.performance_case["args"][1])

    def test_all_translation_units_and_headers_affect_the_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second, header = [root/name for name in ("main.cpp", "library.cpp", "types.hpp")]
            for path in (first, second, header): path.write_text("// fixture", encoding="utf-8")
            benchmark = Benchmark("future-app", first, (), (second,), (header,), "applications")
            digest = benchmark.fingerprint
            second.write_text("// implementation changed", encoding="utf-8")
            self.assertNotEqual(benchmark.fingerprint, digest)
            digest = benchmark.fingerprint
            header.write_text("// contract changed", encoding="utf-8")
            self.assertNotEqual(benchmark.fingerprint, digest)

    def test_small_graph_oracle_uses_independent_algorithm(self):
        edges = [(0,1,2), (1,2,3), (0,2,10), (2,0,1)]
        self.assertEqual(graph_distances(3,edges,0,bellman_ford=True), [0,2,5])
        self.assertEqual(graph_distances(3,edges,0,bellman_ford=False), [0,2,5])

    def test_log_invalid_lines_and_record_serialization_are_observable(self):
        logs = json.loads(logs_output(98,42))
        self.assertEqual(logs["lines"], 98)
        self.assertEqual(logs["invalid"], 2)
        self.assertEqual(sum(row[1] for row in logs["services"]), logs["selected"])
        records = json.loads(records_output(17,42))
        self.assertEqual(records["records"], 17)
        self.assertEqual(sum(row[1] for row in records["groups"]), records["accepted"])
