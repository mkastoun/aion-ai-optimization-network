"""Finite trusted interventions. No user-supplied flags, paths or source rewriting."""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path

from .benchmarks import load_benchmarks
from .errors import AionError
from .models import Candidate
from .provenance import file_sha256

ROOT = Path(__file__).parent
SOURCES = ROOT / "research_sources"


@dataclass(frozen=True)
class Recipe:
    variant: str = "original"
    flags: tuple[str, ...] = ("-O3",)
    mode: str = "standard"
    training: str = "default"
    measured_training: bool = False

    def candidate(self, name):
        return Candidate(name, self.flags, "fixed research recipe", self.mode)


@dataclass(frozen=True)
class Panel:
    name: str
    workload: str
    hypothesis: str
    reference: Recipe
    candidate: Recipe
    distribution: str = "ordinary"


O3 = Recipe()
LTO = Recipe(flags=("-O3","-flto"))
LOG_O3 = Recipe(variant="logs_distributions")
LOG_PGO = replace(LOG_O3, mode="pgo")
CATALOG = (
    Panel("records-lto", "records", "LTO changes records runtime relative to O3", O3, LTO),
    Panel("records-parser-noinline", "records", "Preventing parser inlining improves LTO", LTO, replace(LTO,variant="records_parser_noinline")),
    Panel("records-aggregate-noinline", "records", "Preventing aggregate inlining improves LTO", LTO, replace(LTO,variant="records_aggregate_noinline")),
    Panel("records-scalar", "records", "Disabling vectorization improves LTO", LTO, replace(LTO,flags=(*LTO.flags,"-fno-vectorize","-fno-slp-vectorize"))),
    Panel("records-no-unroll", "records", "Disabling loop unrolling improves LTO", LTO, replace(LTO,flags=(*LTO.flags,"-fno-unroll-loops"))),
    Panel("records-pgo-lto", "records", "Program-specific PGO improves LTO", LTO, replace(LTO,mode="pgo")),
    Panel("records-branchless", "records", "Branchless aggregation improves O3", O3, replace(O3,variant="records_branchless")),
    Panel("logs-pgo", "logs", "Default program-specific PGO improves O3", LOG_O3, LOG_PGO),
    Panel("logs-training-rounds", "logs", "More training rounds improve PGO", LOG_PGO, replace(LOG_PGO,training="long")),
    Panel("logs-training-path", "logs", "Measurement-path training improves PGO", LOG_PGO, replace(LOG_PGO,measured_training=True)),
    Panel("logs-training-mix", "logs", "Mixed training improves PGO on ordinary held-out inputs", replace(LOG_PGO,training="uniform"), replace(LOG_PGO,training="mixed")),
    Panel("logs-unseen", "logs", "Mixed training generalizes to unseen malformed-heavy inputs", replace(LOG_PGO,training="uniform"), replace(LOG_PGO,training="mixed"), "malformed-heavy"),
    Panel("matrix-lto", "matrix", "LTO changes matrix runtime relative to O3", O3, LTO),
    Panel("matrix-scalar", "matrix", "Disabling vectorization improves LTO", LTO, replace(LTO,flags=(*LTO.flags,"-fno-vectorize","-fno-slp-vectorize"))),
    Panel("matrix-no-unroll", "matrix", "Disabling loop unrolling improves LTO", LTO, replace(LTO,flags=(*LTO.flags,"-fno-unroll-loops"))),
    Panel("matrix-pgo-lto", "matrix", "Program-specific PGO improves LTO", LTO, replace(LTO,mode="pgo")),
    Panel("matrix-transposed", "matrix", "Transposed dot-product implementation improves O3", O3, replace(O3,variant="matrix_transposed")),
)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def inputs():
    return json.loads((SOURCES / "inputs.json").read_text(encoding="utf-8"))


def benchmark_for(panel):
    benchmark = load_benchmarks(panel.workload)[0]
    if panel.workload != "logs":
        return benchmark
    cases = list(benchmark.cases)
    extra = inputs()["validation"]
    if panel.distribution == "malformed-heavy":
        cases = [{**c, "name": "original-"+c["name"]} if c["name"] in {"performance","confirmation"} else c for c in cases]
        cases += inputs()["heldout"]
    return replace(benchmark,cases=tuple([*cases,*extra]))


def variant_benchmark(benchmark, recipe):
    if recipe.variant == "original":
        return benchmark
    substitutions = {"records_parser_noinline": ("parser.cpp", "records_parser_noinline.cpp"),
                     "records_aggregate_noinline": ("aggregate.cpp", "records_aggregate_noinline.cpp"),
                     "records_branchless": ("aggregate.cpp", "records_branchless.cpp"),
                     "logs_distributions": ("main.cpp", "logs_distributions.cpp"),
                     "matrix_transposed": ("matrix.cpp", "matrix_transposed.cpp")}
    if recipe.variant not in substitutions:
        raise AionError("Unknown trusted research variant.")
    old, new = substitutions[recipe.variant]
    sources = tuple(SOURCES/new if p.name == old else p for p in benchmark.sources)
    # Includes the original source closure as well as wrapper/replacement bytes.
    return replace(benchmark,source=sources[0],additional_sources=sources[1:],
                   headers=tuple(dict.fromkeys([*(benchmark.headers or ()),*benchmark.source_files])))


def training_cases(benchmark, recipe):
    if benchmark.name != "logs" or recipe.training == "default":
        return [benchmark.case("training")]
    return inputs()["training"][recipe.training]


def catalog_manifest():
    files = {"research_reference.py", "research_catalog.py", "research.py", "research_cli.py", "budget.py",
             "engine.py", "compiler.py", "verification.py", "process.py", "statistics.py", "host.py", "controls.py",
             "models.py", "platform_support.py", "darwin_memory.py", "toolchain.py", "_worker.py", "reproducibility.py", "calibration.py", "benchmarks.py", "workloads/manifest.json",
             "workloads/validation.json", "reference.py", "application_reference.py", "expanded_reference.py"}
    # Source closures do not depend on the chosen input distribution. Validate
    # each bundled workload once instead of resolving it twice per panel.
    benchmarks={b.name:b for b in load_benchmarks('records,logs,matrix')}
    for panel in CATALOG:
        for recipe in (panel.reference,panel.candidate):
            files.update(str(p.relative_to(ROOT)).replace("\\","/") for p in variant_benchmark(benchmarks[panel.workload],recipe).source_files)
    files.update(str(p.relative_to(ROOT)).replace("\\","/") for p in SOURCES.iterdir() if p.is_file())
    return {"panels":[asdict(p) for p in CATALOG], "files":{name:file_sha256(ROOT/name) for name in sorted(files)},
            "family_comparisons":len(CATALOG),"inputs":inputs()}
