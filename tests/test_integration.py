"""Real compilation only. Skip cleanly when Clang or its C++ runtime is absent."""

import os
from pathlib import Path
import shutil
import tempfile
import unittest

from aion.benchmarks import load_benchmarks
from aion.compiler import ClangAdapter
from aion.engine import ExperimentSettings, run_experiment
from aion.errors import AionError
from aion.models import Candidate, Limits
from aion.optimization import BASELINE
from aion.verification import verify_binary, measure_binary
from aion.controls import ExecutionControls, allowed_cpus


class RealClangTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = os.environ.get("AION_TEST_COMPILER", "clang++")
        try:
            cls.adapter = ClangAdapter(compiler)
            if not cls.adapter.probe(BASELINE)["supported"]:
                raise AionError("C++ compile/link/run probe failed")
        except AionError as exc:
            if os.environ.get("AION_REQUIRE_COMPILER") == "1":
                raise AssertionError(f"CI requires a working Clang: {exc}") from exc
            raise unittest.SkipTest(str(exc))

    def test_all_workloads_match_independent_references_at_o3_and_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            for benchmark in load_benchmarks():
                for candidate in (BASELINE, Candidate("o2", ("-O2",)),
                                  Candidate("unroll", ("-O3", "-funroll-loops"))):
                    with self.subTest(workload=benchmark.name, candidate=candidate.name):
                        binary = Path(directory)/f"{benchmark.name}-{candidate.name}.exe"
                        build = self.adapter.compile(benchmark.compilation_input, binary, candidate)
                        self.assertTrue(build["success"], build)
                        checked = verify_binary(binary, benchmark, Limits(timeout_seconds=30))
                        self.assertTrue(checked["passed"], checked)
                        measured = measure_binary(binary, benchmark.case("small"), 3, Limits())
                        self.assertTrue(measured["passed"], measured)
                        self.assertGreater(measured["measurement"]["compute_seconds"], 0)

    def test_real_end_to_end_measurements(self):
        run = run_experiment(self.adapter, load_benchmarks("sorting"),
                             [Candidate("o2", ("-O2",))],
                             ExperimentSettings(iterations=5, warmups=1), Limits(timeout_seconds=30))
        self.assertEqual(run["status"], "completed")
        for entry in run["benchmarks"]["sorting"]["configurations"].values():
            self.assertEqual(entry["status"], "measured")
            self.assertGreater(entry["summary"]["median_seconds"], 0)
            self.assertEqual(len(entry["samples"]), 5)
            self.assertTrue(entry["calibration"]["passed"])
            self.assertTrue(.25 <= entry["calibration"]["median_compute_seconds"] <= .5)

    def test_real_profiled_workload_when_supported(self):
        candidate = Candidate("pgo", ("-O3",), build_mode="pgo")
        probe = self.adapter.probe(candidate)
        if not probe["supported"]:
            self.skipTest(f"Optional PGO toolchain unavailable: {probe}")
        for benchmark in load_benchmarks("sorting,records,graph,logs,image,kv"):
            with self.subTest(workload=benchmark.name), tempfile.TemporaryDirectory() as directory:
                binary = Path(directory)/"profiled.exe"
                build = self.adapter.compile_profiled(benchmark.compilation_input, binary, candidate,
                                                      [benchmark.case("training")], Limits())
                self.assertTrue(build["success"], build)
                self.assertEqual(len(build["pgo"]["profile_sha256"]), 64)
                self.assertNotEqual(build["pgo"]["training"][0]["case"]["args"][1], benchmark.performance_case["args"][1])
                self.assertTrue(verify_binary(binary, benchmark, Limits())["passed"])

    @unittest.skipUnless(os.name=="posix" and hasattr(os,"sched_getaffinity"),"Linux counters required")
    def test_real_counters_and_separate_sampling(self):
        from aion.profiling import build_counter_helper,profile_execution,sample_hotspots
        benchmark=load_benchmarks('sorting')[0]
        controls=ExecutionControls((allowed_cpus()[0],))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);helper,build=build_counter_helper(self.adapter,root)
            self.assertTrue(build['build']['success'],build)
            binary=root/'workload.exe'
            self.assertTrue(self.adapter.compile(benchmark.source,binary,BASELINE)['success'])
            sample=profile_execution(helper,binary,benchmark.performance_case,2,Limits(),root/'count.json',controls)
            self.assertTrue(sample['passed'],sample)
            self.assertEqual(len(sample['counters']['events']),9)
            self.assertGreaterEqual(sample['counters']['resource_usage']['values']['minor_page_faults'],0)
            for e in sample['counters']['events']:
                if e['status']=='counted':self.assertGreater(e['time_running_ns'],0)
                else:self.assertIn(e['status'],{'permission_denied','unsupported','not_counted'})
            sampled=sample_hotspots(binary,benchmark.performance_case,2,root/'sample',Limits(),controls,helper)
            self.assertTrue(sampled['execution']['passed'],sampled)
            if sampled['available']:
                self.assertGreater(len(sampled['resolved']['addresses']),0)
                self.assertTrue(all('sample_count' in r for r in sampled['resolved']['addresses']))

    def test_real_sanitizers_detect_trusted_error_fixtures(self):
        from aion.validation import probe_sanitizer,check_sanitizer
        from aion.process import run_process
        fixtures={'address':'#include <iostream>\nint main(int argc,char**){volatile int index=argc+3;volatile int* p=new int[1];p[index]=7;std::cout<<p[0];delete[] p;}\n',
                  'undefined':'#include <climits>\n#include <iostream>\nint main(int argc,char**){volatile int value=INT_MAX;std::cout<<value+argc;}\n'}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for mode,code in fixtures.items():
                with self.subTest(sanitizer=mode):
                    probe=probe_sanitizer(self.adapter,mode,root)
                    if not probe['supported']:self.skipTest(f'Optional {mode} runtime unavailable: {probe}')
                    source=root/f'error-{mode}.cpp';source.write_text(code)
                    binary=root/f'error-{mode}.exe'
                    self.assertTrue(self.adapter.compile_validation(source,binary,mode)['success'])
                    executed=run_process([str(binary)],Limits(timeout_seconds=30,memory_mb=None))
                    self.assertNotEqual(executed.returncode,0)
                    self.assertFalse(check_sanitizer(executed,'normal')['passed'])
                    self.assertTrue('Sanitizer' in executed.stderr or 'runtime error:' in executed.stderr,executed)

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "sched_getaffinity"), "Linux affinity required")
    def test_affinity_verified_inside_cpp_workload(self):
        benchmark = load_benchmarks("matrix")[0]
        controls = ExecutionControls((allowed_cpus()[0],))
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory)/"pinned.exe"
            build = self.adapter.compile(benchmark.source, binary, BASELINE)
            self.assertTrue(build["success"], build)
            record = measure_binary(binary, benchmark.case("small"), 2, Limits(), controls=controls)
        self.assertTrue(record["passed"], record)
        self.assertTrue(record["execution_controls"]["verified"])
        self.assertEqual(record["execution_controls"]["effective_cpus"], list(controls.cpu_affinity))
        self.assertIn("actual executable", record["execution_controls"]["method"])

    def test_known_slowdown_is_actual_time_with_unchanged_checksum(self):
        benchmark = load_benchmarks("matrix")[0]
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory)/"control.exe"
            self.assertTrue(self.adapter.compile(benchmark.source, binary, BASELINE)["success"])
            plain = measure_binary(binary, benchmark.case("small"), 2, Limits())
            slow = measure_binary(binary, benchmark.case("small"), 2, Limits(), control_delay_ns=50000000)
        self.assertTrue(plain["passed"] and slow["passed"])
        self.assertEqual(plain["measurement"]["checksum"], slow["measurement"]["checksum"])
        self.assertGreaterEqual(slow["measurement"]["injected_control_ns"], 100000000)
        self.assertGreaterEqual(slow["measurement"]["compute_seconds"], .1)

    def test_multi_translation_unit_lto_when_supported(self):
        candidate = Candidate("lto", ("-O3", "-flto"))
        if not self.adapter.probe(candidate)["supported"]:
            self.skipTest("Optional linker LTO support unavailable")
        for benchmark in load_benchmarks("applications"):
            with self.subTest(workload=benchmark.name), tempfile.TemporaryDirectory() as directory:
                binary = Path(directory)/"linked.exe"
                build = self.adapter.compile(benchmark.compilation_input, binary, candidate)
                self.assertTrue(build["success"], build)
                self.assertEqual(len(build["sources"]), len(benchmark.sources))
                self.assertTrue(verify_binary(binary, benchmark, Limits())["passed"])
