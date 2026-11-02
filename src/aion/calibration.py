"""Bounded calibration using discarded pilot executions, never measured samples."""

import math
import statistics
from collections.abc import Callable


def calibrate(execute: Callable[[int], dict], minimum: float = .250,
              maximum: float = .500, max_batches: int = 65536,
              max_attempts: int = 8) -> dict:
    if not 0 < minimum < maximum or max_batches < 1 or max_attempts < 1:
        raise ValueError("Invalid calibration bounds")
    target = (minimum + maximum) / 2
    pilots, batches = [], 1
    for attempt in range(max_attempts):
        durations = []
        for _ in range(3):
            record = execute(batches)
            pilots.append({"attempt": attempt, "batches": batches, **record})
            if not record["passed"]:
                return {"passed": False, "batches": batches, "pilots": pilots,
                        "reason": "calibration correctness or execution failure"}
            durations.append(record["measurement"]["compute_seconds"])
        median = statistics.median(durations)
        if minimum <= median <= maximum:
            return {"passed": True, "batches": batches, "pilots": pilots,
                    "median_compute_seconds": median, "target_min_seconds": minimum,
                    "target_max_seconds": maximum, "reason": ""}
        proposed = max(1, min(max_batches, round(batches * target / median)))
        if proposed == batches:
            proposed += 1 if median < minimum else -1
        proposed = max(1, min(max_batches, proposed))
        if proposed == batches:
            break
        batches = proposed
    return {"passed": False, "batches": batches, "pilots": pilots,
            "reason": "unable to reach target duration within bounded calibration"}
