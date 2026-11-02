"""Requested per-process controls; never mutate machine-wide configuration."""

from dataclasses import dataclass
import os
import sys

from .errors import AionError


def affinity_supported() -> bool:
    return sys.platform.startswith("linux") and hasattr(os, "sched_setaffinity") and hasattr(os, "sched_getaffinity")


def allowed_cpus() -> list[int] | None:
    if not affinity_supported():
        return None
    try:
        return sorted(os.sched_getaffinity(0))
    except OSError:
        return None


@dataclass(frozen=True)
class ExecutionControls:
    cpu_affinity: tuple[int, ...] | None = None
    selection: str = "explicit"

    def __post_init__(self):
        if self.cpu_affinity is not None and (not self.cpu_affinity
                or any(type(cpu) is not int or cpu < 0 for cpu in self.cpu_affinity)
                or len(set(self.cpu_affinity)) != len(self.cpu_affinity)):
            raise AionError("CPU affinity must contain unique nonnegative CPU IDs.")

    def validate(self):
        if self.cpu_affinity is None:
            return
        allowed = allowed_cpus()
        if allowed is None:
            raise AionError("Requested CPU affinity is unavailable on this platform. Use --cpus none.")
        if not set(self.cpu_affinity).issubset(allowed):
            raise AionError(f"Requested CPUs {list(self.cpu_affinity)} are outside the allowed affinity set {allowed}.")

    def to_dict(self) -> dict:
        result = {"requested_cpus": sorted(self.cpu_affinity) if self.cpu_affinity is not None else None,
                "selection": self.selection if self.cpu_affinity is not None else "disabled",
                "supported": affinity_supported(), "governor_changed": False,
                "turbo_changed": False, "system_power_changed": False}
        if self.selection == 'auto-unavailable-macos':
            result.update(selection=self.selection, unsupported_reason='macOS does not support Linux core affinity; execution is unpinned')
        return result


def parse_cpus(value: str = "none") -> ExecutionControls:
    if value == "none":
        return ExecutionControls()
    if value == "auto":
        if sys.platform == 'darwin':
            return ExecutionControls(selection='auto-unavailable-macos')
        allowed = allowed_cpus()
        if not allowed:
            raise AionError("Cannot select a CPU automatically; affinity is unavailable. Use --cpus none.")
        return ExecutionControls((allowed[0],), selection="auto-first-allowed")
    try:
        ids = []
        for part in value.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                if start < 0 or end < start or end - start > 65536:
                    raise ValueError
                ids.extend(range(start, end + 1))
            else:
                ids.append(int(part))
        controls = ExecutionControls(tuple(sorted(ids)))
    except ValueError as exc:
        raise AionError("Use --cpus none, auto, or CPU IDs/ranges such as 2 or 2,4-5.") from exc
    controls.validate()
    return controls
