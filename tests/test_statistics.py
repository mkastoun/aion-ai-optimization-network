import math
import unittest

from aion.errors import AionError
from aion.statistics import compare, summarize


class StatisticsTests(unittest.TestCase):
    def test_median_and_variability(self):
        summary = summarize([.1, .11, .09, .1, .1])
        self.assertEqual(summary["median_seconds"], .1)
        self.assertEqual(summary["mad_seconds"], 0)
        self.assertTrue(summary["noisy"])

    def test_reject_invalid_samples(self):
        for samples in ([], [0], [-1], [math.nan], [math.inf]):
            with self.subTest(samples=samples), self.assertRaises(AionError):
                summarize(samples)

    def test_classification(self):
        baseline = summarize([.1] * 7)
        for duration, outcome, accepted in ((.08, "improvement", True),
                                             (.101, "no_clear_change", True),
                                             (.12, "regression", False)):
            comparison = compare(baseline, summarize([duration] * 7))
            self.assertEqual(comparison["classification"], outcome)
            self.assertEqual(comparison["acceptable"], accepted)

    def test_noisy_short_or_insufficient_is_inconclusive(self):
        for samples in ([.1, .2, .3, .4, .5], [.001]*7, [.1]*2):
            self.assertEqual(compare(summarize([.2]*7), summarize(samples))["classification"],
                             "inconclusive")
