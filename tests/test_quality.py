"""Synthetic control study fixtures; rates are not published measurements."""
from copy import deepcopy
from pathlib import Path
import unittest

from aion.controls import ExecutionControls
from aion.engine import ExperimentSettings
from aion.errors import AionError
from aion.quality import build_quality_report,descriptive_rate
from aion.report import render_report
from aion.sessions import new_session
from tests.test_control_experiments import ExperimentalControlTests


def study():
    base=ExperimentalControlTests().run_controls()
    sessions=[new_session(label='synthetic session A'),new_session(label='synthetic session B')]
    runs=[]
    for i in range(4):
        run=deepcopy(base);run['run_id']=f'synthetic-control-{i}';run['experiment_kind']='control'
        run['session']=sessions[i//2];run['settings']['seed']=100+i
        if i%2:
            b=run['benchmarks']['matrix'];b['measurement_case']=next(c for c in b['cases'] if c['name']=='confirmation')
        runs.append(run)
    return runs


class QualityTests(unittest.TestCase):
    def test_descriptive_rates_have_counts_and_nonzero_zero_success_uncertainty(self):
        rate=descriptive_rate(0,8)
        self.assertEqual((rate['count'],rate['total']),(0,8))
        self.assertGreater(rate['interval_95'][1],0)
        self.assertIsNone(descriptive_rate(0,0)['fraction'])
        with self.assertRaises(AionError):descriptive_rate(2,1)

    def test_two_sessions_support_scoped_quality_assessment(self):
        result=build_quality_report(study())
        self.assertEqual(len(result['strata']),1)
        s=result['strata'][0]
        self.assertTrue(s['cross_session_design_complete'])
        self.assertTrue(s['measurement_quality_checks_passed'])
        self.assertEqual(s['rates']['aa_false_positive_all']['total'],4)
        self.assertEqual(s['rates']['slowdown_detected_all']['count'],4)
        self.assertFalse(result['readiness']['native_linux_performance_validated'])
        self.assertIn('correlated',result['uncertainty_caveat'])
        self.assertIn('Benchmark readiness',render_report(result))

    def test_single_session_is_insufficient_and_duplicates_cannot_inflate_counts(self):
        runs=study()
        self.assertFalse(build_quality_report(runs[:2])['strata'][0]['cross_session_design_complete'])
        with self.assertRaises(AionError):build_quality_report([runs[0],runs[0]])

    def test_incompatible_hosts_are_stratified_without_pooling(self):
        runs=study();runs[2]['host_start']['host_fingerprint']='other-host';runs[3]['host_start']['host_fingerprint']='other-host'
        result=build_quality_report(runs)
        self.assertEqual(len(result['strata']),2)
        self.assertTrue(all(not s['cross_session_design_complete'] for s in result['strata']))
        self.assertIn('no timing samples',result['pooling'])

    def test_noisy_slowdowns_remain_inconclusive_in_readiness(self):
        runs=study()
        for i,s in enumerate(runs[0]['benchmarks']['matrix']['configurations']['control-slowdown']['samples']):
            s['measurement']['seconds_per_batch']*=1 if i%2 else 2
        result=build_quality_report(runs)
        self.assertFalse(result['readiness']['measurement_quality_checks_passed'])
        self.assertGreater(result['strata'][0]['rates']['inconclusive_all']['count'],0)
