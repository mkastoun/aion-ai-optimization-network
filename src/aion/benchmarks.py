from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .errors import AionError

ROOT = Path(__file__).with_name("workloads")


@dataclass(frozen=True)
class Benchmark:
    name: str
    source: Path
    cases: tuple[dict, ...]
    additional_sources: tuple[Path, ...] = ()
    headers: tuple[Path, ...] | None = None
    category: str = "micro"

    @property
    def sources(self) -> tuple[Path, ...]:
        return (self.source, *self.additional_sources)

    @property
    def compilation_input(self):
        return self.source if not self.additional_sources else self.sources

    @property
    def source_files(self) -> tuple[Path, ...]:
        return (*self.sources, *(self.headers if self.headers is not None else (ROOT / "common.hpp",)))

    @property
    def performance_case(self) -> dict:
        return next(case for case in self.cases if case["name"] == "performance")

    def case(self, name: str) -> dict:
        for case in self.cases:
            if case["name"] == name:
                return case
        raise AionError(f"Benchmark '{self.name}' is missing required '{name}' input cases.")

    @property
    def fingerprint(self) -> str:
        digest = hashlib.sha256()
        for path in self.source_files:
            digest.update(path.read_bytes())
        digest.update(json.dumps(self.cases, sort_keys=True).encode())
        return digest.hexdigest()


def load_benchmarks(selection: str = "all") -> list[Benchmark]:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    workloads = manifest["workloads"]
    names = (list(workloads) if selection == "all" else
             [name for name, data in workloads.items() if data.get("category", "micro") == selection]
             if selection in {"micro", "applications"} else selection.split(","))
    if not names or len(names) != len(set(names)) or any(name not in workloads for name in names):
        raise AionError(f"Choose 'all' or comma-separated workloads: {', '.join(workloads)}")
    result = []
    resolved_root = ROOT.resolve()
    for name in names:
        data = workloads[name]
        sources = data.get("sources", [data.get("source")])
        headers = data.get("headers", ["common.hpp"])
        paths = [ROOT / value for value in [*sources, *headers] if isinstance(value, str)]
        if len(paths) != len(sources) + len(headers) or not sources or any(
                not path.resolve().is_relative_to(resolved_root) or not path.is_file() for path in paths):
            raise AionError(f"Invalid or missing source/header files for benchmark '{name}'.")
        result.append(Benchmark(name, ROOT / sources[0], tuple(data["cases"]),
                                tuple(ROOT / value for value in sources[1:]),
                                tuple(ROOT / value for value in headers), data.get("category", "micro")))
    return result
