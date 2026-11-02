"""Approved preview experiments, including existing recipes for all ten workloads."""
from dataclasses import asdict

from .benchmarks import load_benchmarks
from .errors import AionError
from .provenance import file_sha256
from .research_catalog import CATALOG, ROOT, O3, LTO, Panel, Recipe, catalog_manifest, variant_benchmark, benchmark_for

PROVIDER = "mvp-preview-v1"
EXTRA_WORKLOADS = ("array", "sorting", "hashmap", "strings", "graph", "image", "kv")
MVP_CATALOG = (*CATALOG, *tuple(panel for name in EXTRA_WORKLOADS for panel in (
    Panel(name+"-o2", name, "O2 changes runtime relative to O3", O3, Recipe(flags=("-O2",))),
    Panel(name+"-lto", name, "LTO changes runtime relative to O3", O3, LTO))))
MAX_PROPOSALS = 16
MAX_SELECTED = 4


def available(workload):
    load_benchmarks(workload)  # Preserve the existing workload ID validation.
    if ',' in workload or workload in {'all','micro','applications'}:
        raise AionError("Select one existing workload ID.")
    return tuple(p for p in MVP_CATALOG if p.workload == workload)


def manifest():
    result = catalog_manifest()
    files = dict(result['files'])
    # The original research manifest already covers every source variant. The
    # additional approved recipes use only the original ten source contracts.
    for benchmark in load_benchmarks():
        for path in benchmark.source_files:
            files[path.relative_to(ROOT).as_posix()] = file_sha256(path)
    for name in ('mvp_catalog.py','mvp_proposals.py','mvp_context.py','mvp.py','mvp_report.py','mvp_cli.py',
                 'validation.py','sessions.py','registry.py','evidence.py'):
        files[name] = file_sha256(ROOT/name)
    return {**result,'provider':PROVIDER,'panels':[asdict(p) for p in MVP_CATALOG],
            'files':dict(sorted(files.items())), 'family_comparisons':max(len(CATALOG),len(MVP_CATALOG))}
