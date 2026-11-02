"""Conservative descriptive comparisons, not claims of statistical significance."""

import math
import statistics
import random

from .errors import AionError


def summarize(samples: list[float], noise_threshold: float = 0.05, *,
              physical_seconds: list[float] | None = None,
              minimum_seconds: float = .02) -> dict:
    if not samples or any(not math.isfinite(x) or x <= 0 for x in samples):
        raise AionError("Timing samples must be finite and positive.")
    if physical_seconds is not None and (len(physical_seconds) != len(samples)
            or any(not math.isfinite(x) or x <= 0 for x in physical_seconds)):
        raise AionError("Physical timing samples must be complete, finite, and positive.")
    median = statistics.median(samples)
    mean = statistics.mean(samples)
    mad = statistics.median(abs(x - median) for x in samples)
    cv = statistics.stdev(samples) / mean if len(samples) > 1 else 0.0
    half = len(samples) // 2
    drift = (statistics.median(samples[half:]) / statistics.median(samples[:half]) - 1
             if half else 0.0)
    outliers = sum(abs(x - median) > 3 * 1.4826 * mad for x in samples) if mad else sum(x != median for x in samples)
    return {"count": len(samples), "median_seconds": median, "min_seconds": min(samples),
            "max_seconds": max(samples), "mad_seconds": mad, "relative_mad": mad / median,
            "coefficient_of_variation": cv, "noisy": cv > noise_threshold,
            "too_short": statistics.median(physical_seconds or samples) < minimum_seconds,
            "physical_median_seconds": statistics.median(physical_seconds or samples),
            "drift_fraction": drift, "drifting": abs(drift) > noise_threshold,
            "outlier_count": outliers, "outliers_removed": 0}


def compare(baseline: dict, candidate: dict, *, min_improvement: float = 0.02,
            max_regression: float = 0.05) -> dict:
    change = 1 - candidate["median_seconds"] / baseline["median_seconds"]
    uncertain = (baseline["noisy"] or candidate["noisy"]
                 or baseline["too_short"] or candidate["too_short"]
                 or min(baseline["count"], candidate["count"]) < 5)
    # Require the observed improvement to exceed both a floor and twice the
    # combined relative MAD. This is a screening rule, not a confidence interval.
    floor = max(min_improvement, 2 * (baseline["relative_mad"] + candidate["relative_mad"]))
    if uncertain:
        classification = "inconclusive"
    elif change < -max_regression:
        classification = "regression"
    elif change > floor:
        classification = "improvement"
    else:
        classification = "no_clear_change"
    return {"improvement_fraction": change,
            "speedup": baseline["median_seconds"] / candidate["median_seconds"],
            "classification": classification, "required_improvement_fraction": floor,
            "regression_observed": change < -max_regression,
            "acceptable": not uncertain and change >= -max_regression}


def _quantile(sorted_values: list[float], probability: float) -> float:
    position = probability * (len(sorted_values) - 1)
    lower = math.floor(position)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[math.ceil(position)] * weight


def paired_comparison(baseline: list[float], candidate: list[float], *,
                      baseline_physical: list[float], candidate_physical: list[float],
                      noise_threshold: float = .05, min_improvement: float = .02,
                      max_regression: float = .05, minimum_seconds: float = .25,
                      confidence: float = .95, comparisons: int = 1,
                      resamples: int = 10000, seed: int | str = 1729) -> dict:
    if (len(baseline) != len(candidate) or not baseline or comparisons < 1
            or resamples < 100 or not 0 < confidence < 1
            or len(baseline_physical) != len(baseline) or len(candidate_physical) != len(candidate)):
        raise AionError("Paired uncertainty analysis requires complete matched samples and valid settings.")
    first = summarize(baseline, noise_threshold, physical_seconds=baseline_physical,
                      minimum_seconds=minimum_seconds)
    second = summarize(candidate, noise_threshold, physical_seconds=candidate_physical,
                       minimum_seconds=minimum_seconds)
    result = compare(first, second, min_improvement=min_improvement, max_regression=max_regression)
    effects = [1 - c / b for b, c in zip(baseline, candidate)]
    rng = random.Random(seed)
    block_length = min(len(effects), max(1, math.ceil(math.sqrt(len(effects)))))
    estimates = []
    for _ in range(resamples):
        draw = []
        while len(draw) < len(effects):
            start = rng.randrange(len(effects))
            draw.extend(effects[(start + offset) % len(effects)] for offset in range(block_length))
        estimates.append(statistics.median(draw[:len(effects)]))
    estimates.sort()
    # Bonferroni-adjusted percentile intervals across the declared experiment
    # family. These remain empirical bootstrap intervals, not a guarantee of
    # exact coverage under serial dependence or small samples.
    tail = (1 - confidence) / comparisons / 2
    lower, upper = _quantile(estimates, tail), _quantile(estimates, 1 - tail)
    result["uncertainty"] = {
        "method": "paired circular moving-block percentile bootstrap; Bonferroni family adjustment",
        "confidence_level": 1 - 2*tail, "family_confidence_level": confidence,
        "family_comparisons": comparisons, "resamples": resamples, "seed": seed,
        "paired_improvement_fraction": statistics.median(effects),
        "improvement_ci_low": lower, "improvement_ci_high": upper,
        "pair_count": len(effects), "block_length": block_length,
        "assumptions": "approximately stationary, weakly dependent pairs; small samples limit coverage",
    }
    result["paired_baseline_summary"], result["paired_candidate_summary"] = first, second
    if first["drifting"] or second["drifting"]:
        result["classification"], result["acceptable"] = "inconclusive", False
    elif result["classification"] == "improvement" and lower <= result["required_improvement_fraction"]:
        result["classification"] = "no_clear_change"
    elif result["classification"] == "regression" and upper >= -max_regression:
        result["classification"] = "inconclusive"
    # Do not accept a potentially unacceptable slowdown merely because its
    # point estimate is small. Existing CV/MAD/floor rules are never relaxed.
    result["acceptable"] = result["acceptable"] and lower >= -max_regression
    return result
