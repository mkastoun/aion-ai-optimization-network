"""Candidate generation is separate from execution and verification."""

from collections.abc import Iterable
from typing import Protocol

from .errors import AionError
from .models import Candidate


ALLOWED_FLAGS = frozenset({
    "-O2", "-O3", "-Os", "-funroll-loops", "-fno-unroll-loops",
    "-fno-vectorize", "-fno-slp-vectorize", "-flto",
})
BASELINE = Candidate("baseline", ("-O3",), "Standard Clang -O3")


def validate_flags(flags: Iterable[str]) -> tuple[str, ...]:
    flags = tuple(flags)
    if not flags or any(not isinstance(flag, str) or flag not in ALLOWED_FLAGS for flag in flags):
        raise AionError("Compiler flags must belong to AION's explicit optimization allowlist.")
    if len(set(flags)) != len(flags) or sum(f in {"-O2", "-O3", "-Os"} for f in flags) != 1:
        raise AionError("Use exactly one optimization level and no duplicate flags.")
    if "-funroll-loops" in flags and "-fno-unroll-loops" in flags:
        raise AionError("Conflicting loop unrolling flags.")
    return flags


def validate_candidate(candidate: Candidate):
    validate_flags(candidate.flags)
    if candidate.build_mode not in {"standard", "pgo", "control-aa", "control-slowdown"}:
        raise AionError("Unknown build or experimental-control recipe.")
    if candidate.build_mode.startswith("control-") and candidate.flags != BASELINE.flags:
        raise AionError("Experimental controls must use the exact -O3 baseline flags.")


class CandidateGenerator(Protocol):
    """Future research agents receive data and return proposals, never commands.

    Every proposal must pass validate_flags, compilation, correctness, measurement,
    and independent confirmation before reaching the registry.
    """

    def generate(self, previous_results: dict | None = None) -> Iterable[Candidate]: ...


class DeterministicGenerator:
    def generate(self, previous_results: dict | None = None) -> Iterable[Candidate]:
        return (
            Candidate("o2", ("-O2",), "Compare a smaller optimization budget"),
            Candidate("size", ("-Os",), "Compare code size and execution time"),
            Candidate("unroll", ("-O3", "-funroll-loops"), "Request loop unrolling"),
            Candidate("no-vectorize", ("-O3", "-fno-vectorize", "-fno-slp-vectorize"),
                      "Measure scalar code as a counter-experiment"),
            Candidate("lto", ("-O3", "-flto"), "Clang -O3 with link-time optimization"),
            Candidate("pgo", ("-O3",), "Clang -O3 with separately trained instrumentation profiles", "pgo"),
            Candidate("pgo-lto", ("-O3", "-flto"), "Clang -O3 with PGO and LTO", "pgo"),
        )
