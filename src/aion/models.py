from dataclasses import asdict, dataclass
import math

from .errors import AionError


@dataclass(frozen=True)
class Limits:
    timeout_seconds: float = 15.0
    memory_mb: int | None = 1024
    output_bytes: int = 1_048_576

    def __post_init__(self):
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise AionError("Timeout must be finite and positive.")
        if (self.memory_mb is not None and self.memory_mb < 32) or self.output_bytes < 1024:
            raise AionError("Memory must be >=32 MiB and output limit >=1024 bytes.")


@dataclass(frozen=True)
class Candidate:
    name: str
    flags: tuple[str, ...]
    description: str = ""
    build_mode: str = "standard"


@dataclass(frozen=True)
class CompilerInfo:
    path: str
    version: str
    major: int
    target: str
    family: str = "clang"


@dataclass
class ProcessResult:
    command: list[str]
    returncode: int
    duration_seconds: float
    peak_rss_bytes: int | None
    stdout: str
    stderr: str
    timed_out: bool = False
    output_limited: bool = False
    affinity: dict | None = None
    workload_pid: int | None = None
    memory_limited: bool = False
    resource_protection: dict | None = None

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out and not self.output_limited and not self.memory_limited

    def to_dict(self) -> dict:
        return asdict(self)
