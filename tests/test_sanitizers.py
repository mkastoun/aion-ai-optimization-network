"""Separate validation fixtures; timings are never performance evidence."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aion.benchmarks import Benchmark,load_benchmarks
from aion.models import Limits
from aion.validation import check_sanitizer,run_validation,validation_cases
from tests.helpers import process,INFO


class FakeValidationCompiler:
    info=INFO
    def build_provenance(self):return {}
    def compile_validation(self,source,output,sanitizer):return {'success':True,'binary_sha256':'synthetic'}


class SanitizerTests(unittest.TestCase):
    def test_sanitizer_diagnostics_fail_even_with_zero_exit_status(self):
        result=process('ok');result.stderr='test.cpp:4: runtime error: signed integer overflow'
        self.assertFalse(check_sanitizer(result,'ok')['passed'])
        result.stderr='ERROR: AddressSanitizer: heap-buffer-overflow'
        self.assertFalse(check_sanitizer(result,'ok')['passed'])
        result.stderr=''
        self.assertTrue(check_sanitizer(result,'ok')['passed'])

    def test_shadow_address_space_exception_is_explicit(self):
        self.assertIsNone(Limits(memory_mb=None).memory_mb)
        self.assertEqual(Limits().memory_mb,1024)

    def test_extra_edge_large_and_pattern_cases_preserve_timing_inputs(self):
        for benchmark in load_benchmarks():
            before=benchmark.fingerprint
            cases=validation_cases(benchmark)
            self.assertGreater(len(cases),len(benchmark.cases))
            self.assertIn('large',{c['name'] for c in cases})
            self.assertIn('two-elements-wrap',{c['name'] for c in cases})
            self.assertEqual(benchmark.fingerprint,before)

    def test_failed_case_does_not_discard_other_validation_checks(self):
        benchmark=Benchmark('fixture',load_benchmarks('array')[0].source,({'name':'good','args':[],'expected':'ok'},
                                                            {'name':'error','args':[],'expected':'ok'}),headers=())
        bad=process('ok');bad.stderr='ERROR: AddressSanitizer: injected test fixture'
        with tempfile.TemporaryDirectory() as directory,patch('aion.validation.probe_sanitizer',return_value={'supported':True}),patch(
                'aion.validation.run_process',side_effect=[process('ok'),bad]),patch('aion.validation.validation_cases',return_value=list(benchmark.cases)):
            run=run_validation(FakeValidationCompiler(),[benchmark],Path(directory),modes=('address',),differential=False)
        entry=run['benchmarks']['fixture']['modes']['address']
        self.assertEqual(len(entry['checks']),2)
        self.assertEqual(run['status'],'failed')
        self.assertFalse(run['promotion_eligible'])
