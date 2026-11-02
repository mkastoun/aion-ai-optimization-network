"""Preserved code-generation evidence and honest regression retests."""

from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import uuid
import sys
from zipfile import ZipFile, BadZipFile

from .benchmarks import Benchmark, load_benchmarks
from .engine import run_experiment
from .errors import AionError
from .models import Limits
from .optimization import BASELINE
from .process import run_process
from .provenance import file_sha256
from .storage import atomic_json
from .verification import verify_binary
from .toolchain import find_llvm_tool


def restore_phase2_sources(wheel: Path, directory: Path) -> tuple[list[Benchmark], dict]:
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(wheel) as archive:
            metadata = archive.read("aion_network-0.2.0.dist-info/METADATA").decode("utf-8")
            if "\nVersion: 0.2.0\n" not in metadata:
                raise AionError("The archived source bundle must be the local AION 0.2.0 wheel.")
            for name in ("common.hpp", "sorting.cpp", "matrix.cpp", "manifest.json"):
                # Explicit fixed member names; no archive path extraction.
                (directory / name).write_bytes(archive.read(f"aion/workloads/{name}"))
    except (OSError, KeyError, BadZipFile) as exc:
        raise AionError(f"Cannot restore the local Phase 2 source bundle: {exc}") from exc
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    benchmarks = [Benchmark(name, directory/f"{name}.cpp", tuple(manifest["workloads"][name]["cases"]),
                            headers=(directory/"common.hpp",)) for name in ("sorting", "matrix")]
    return benchmarks, {"wheel": str(wheel.resolve()), "wheel_sha256": file_sha256(wheel),
                        "source_scope": "frozen local Phase 2 source; original executable was not retained",
                        "benchmarks": {b.name: b.fingerprint for b in benchmarks}}


def capture_build_diagnostics(adapter, benchmark: Benchmark, candidate, directory: Path, controls=None) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / "workload.exe"
    kwargs = {"controls": controls} if controls else {}
    build = (adapter.compile_profiled(benchmark.compilation_input, binary, candidate,
                                      [benchmark.case("training")], Limits(), profile_archive=directory/"profile", **kwargs)
             if candidate.build_mode == "pgo" else adapter.compile(benchmark.compilation_input, binary, candidate))
    result = {"candidate": asdict(candidate), "build": build, "benchmark_fingerprint": benchmark.fingerprint,
              "files": [{"path": str(path.resolve()), "sha256": file_sha256(path)} for path in benchmark.source_files],
              "scope": "diagnostic binaries are separate from fresh timed builds; compare their hashes before attributing codegen"}
    if not build["success"]:
        atomic_json(directory/"evidence.json", {"schema_version": 1, **result})
        return result
    result["verification"] = verify_binary(binary, benchmark, Limits(), **kwargs)
    try:tool = find_llvm_tool('llvm-objdump', adapter.info, fallback=() if sys.platform == 'darwin' else ('objdump',))
    except AionError as exc:
        tool = None
        result['disassembly'] = {'available':False,'reason':str(exc)}
    if tool:
        version = run_process([tool, "--version"], Limits(timeout_seconds=15))
        extra = ['--no-show-raw-insn'] if sys.platform == 'darwin' else []
        dump = run_process([tool, "-d", "-C", *extra, str(binary)], Limits(timeout_seconds=60, output_bytes=64*1024*1024))
        assembly = directory / "final-disassembly.txt"
        assembly.write_text(dump.stdout, encoding="utf-8")
        mnemonics = re.findall(r"^\s*[0-9a-f]+:\s+(?:(?:[0-9a-f]{2})\s+)+\s*([a-z][a-z0-9.]*)", dump.stdout, re.MULTILINE)
        if sys.platform == 'darwin':mnemonics = re.findall(r'^\s*[0-9a-f]+:\s+([a-z][a-z0-9.]*)', dump.stdout, re.MULTILINE)
        counts = {name: mnemonics.count(name) for name in sorted(set(mnemonics))}
        result["disassembly"] = {"tool": tool, "version": version.stdout.strip(), "process": dump.to_dict(),
                                 "path": str(assembly.resolve()), "sha256": file_sha256(assembly),
                                 "static_mnemonic_counts": counts,
                                 "count_scope": "text-derived static whole-binary counts, not dynamic retired instructions"}
    elif 'disassembly' not in result:
        result["disassembly"] = {"available": False, "reason": "no local disassembler found"}
    result["llvm_ir"] = []
    for index, source in enumerate(benchmark.sources):
        output = directory / f"tu-{index}.ll"
        remarks = directory / f"tu-{index}-remarks.txt"
        profile = (build.get("pgo") or {}).get("saved_profile")
        profile_flags = [f"-fprofile-instr-use={profile}"] if profile else []
        command = [adapter.info.path, "-std=c++17", *candidate.flags, *profile_flags, "-S", "-emit-llvm",
                   "-Rpass=inline|loop-vectorize", "-Rpass-missed=inline|loop-vectorize",
                   "-Rpass-analysis=loop-vectorize", str(source.resolve()), "-o", str(output.resolve())]
        ir = run_process(command, Limits(timeout_seconds=adapter.timeout, memory_mb=2048, output_bytes=64*1024*1024))
        remarks.write_text(ir.stderr, encoding="utf-8")
        text = output.read_text(encoding="utf-8") if output.exists() else ""
        result["llvm_ir"].append({"stage": "optimized per-TU IR before link; not post-LTO IR",
            "source": str(source.resolve()), "path": str(output.resolve()), "sha256": file_sha256(output),
            "process": ir.to_dict(), "remarks": str(remarks.resolve()),
            "branch_weight_metadata_count": text.count('!"branch_weights"'),
            "profile_entry_metadata_count": text.count('!"function_entry_count"'),
            "vector_type_occurrences": {width: len(re.findall(r"<" + width + r" x ", text)) for width in ("2", "4", "8", "16")},
            "limitations": "whole-module static counts are not a causal performance diagnosis"})
    result["training_representativeness"] = {
        "training_input": benchmark.case("training"), "measurement_input": benchmark.performance_case,
        "confirmation_input": benchmark.case("confirmation"),
        "verified_fact": "same workload/input size; different seeds and fewer training rounds",
        "hypothesis": "branch-frequency and inlining choices may differ; these inputs do not establish production representativeness"}
    atomic_json(directory/"evidence.json", {"schema_version": 1, **result})
    return result


def run_investigation(adapter, benchmarks, candidates, settings, limits, directory: Path,
                      controls=None, phase2_wheel: Path | None = None, on_result=None, progress=None) -> dict:
    emit = progress or (lambda message: None)
    root = directory / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    root.mkdir(parents=True, exist_ok=True)
    frozen = None
    if phase2_wheel:
        recovered, frozen = restore_phase2_sources(phase2_wheel, root/"phase2-source")
        selected = {b.name for b in benchmarks}
        benchmarks = [b for b in recovered if b.name in selected]
        if not benchmarks:
            raise AionError("The Phase 2 regression investigation supports sorting and matrix.")
    evidence = {"schema_version": 1, "directory": str(root.resolve()), "phase2_bundle": frozen,
                "static_builds": {}, "runs": [], "hypotheses_are_not_verified_findings": True}
    if frozen:
        evidence["phase2_source_matches"] = {}
        for path in Path(".aion/results").glob("*.json"):
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if previous.get("aion_version") == "0.2.0":
                evidence["phase2_source_matches"][previous["run_id"]] = {
                    b.name: b.fingerprint == previous.get("benchmarks", {}).get(b.name, {}).get("fingerprint") for b in benchmarks}
    for benchmark in benchmarks:
        evidence["static_builds"][benchmark.name] = {}
        for candidate in [BASELINE, *candidates]:
            emit(f"Preserving codegen: {benchmark.name}/{candidate.name}")
            evidence["static_builds"][benchmark.name][candidate.name] = capture_build_diagnostics(
                adapter, benchmark, candidate, root/"codegen"/benchmark.name/candidate.name, controls)
    runs = []
    for index, purpose in enumerate(("regression-investigation", "independent_confirmation")):
        run = run_experiment(adapter, benchmarks, candidates, replace(settings, seed=settings.seed+index), limits,
                             purpose=purpose, controls=controls, progress=emit, on_failure=on_result)
        run["experiment_kind"] = "regression-investigation"
        run["investigation_source"] = frozen
        for name, benchmark in run["benchmarks"].items():
            for candidate, entry in benchmark["configurations"].items():
                static = evidence["static_builds"][name][candidate]["build"].get("binary_sha256")
                entry["diagnostic_binary_matches"] = bool(static and static == entry.get("build", {}).get("binary_sha256"))
        evidence["runs"].append(run["run_id"])
        runs.append(run)
        if on_result: on_result(run)
    atomic_json(root/"investigation.json", evidence)
    from .report import render_confirmation_report
    (root/"performance.md").write_text(render_confirmation_report(*runs), encoding="utf-8")
    return evidence
