"""Separate sanitizer/differential evidence, never an optimization experiment."""
from dataclasses import asdict
import json
from pathlib import Path
import re
import tempfile
import sys

from .benchmarks import ROOT
from .errors import AionError
from .evidence import evidence_header
from .host import collect_host_diagnostics
from .models import Limits
from .process import run_process
from .provenance import file_sha256
from .storage import atomic_json
from .verification import check_output

SANITIZERS = ("address", "undefined")
OPTIONS = {"ASAN_OPTIONS": "halt_on_error=1:detect_leaks=1", "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"}


def sanitizer_options():
    return {**OPTIONS, 'ASAN_OPTIONS': 'halt_on_error=1:detect_leaks=0'} if sys.platform in {'darwin','win32'} else dict(OPTIONS)


def leak_detection_status():
    requested = sys.platform.startswith('linux')
    return {'requested':requested, 'available':None if requested else False,
            'reason':'Requested through ASan; leak detection has not been independently validated' if requested else
                     'LeakSanitizer is unsupported by this platform validation path; ASan and UBSan remain required'}


def validation_cases(benchmark):
    path = ROOT / "validation.json"
    extra = json.loads(path.read_text(encoding="utf-8"))["workloads"].get(benchmark.name, []) if path.is_file() else []
    return [*benchmark.cases, *extra]


def check_sanitizer(result, expected):
    check = check_output(result, expected)
    if re.search(r"(?:ERROR: (?:AddressSanitizer|LeakSanitizer)|runtime error:|SUMMARY: .*Sanitizer|UndefinedBehaviorSanitizer:)",result.stderr):
        check["reasons"].append("sanitizer diagnostic detected")
        check["passed"] = False
    return check


def probe_sanitizer(adapter, sanitizer, directory, controls=None):
    source, binary = directory / f"probe-{sanitizer}.cpp", directory / f"probe-{sanitizer}.exe"
    source.write_text('#include <iostream>\nint main(){std::cout << "healthy\\n";}\n',encoding="utf-8")
    build = adapter.compile_validation(source,binary,sanitizer)
    if not build["success"]: return {"supported":False,"reason":"sanitizer compile/link unavailable","build":build}
    # ASan reserves a very large shadow address range. Keep time/output/CPU
    # limits; explicitly disable only the virtual address-space ceiling here.
    process = run_process([str(binary)],Limits(timeout_seconds=30,memory_mb=None),controls=controls,env_overrides=sanitizer_options())
    check = check_sanitizer(process,"healthy")
    return {"supported":check["passed"],"build":build,"execution":check,
            "reason":None if check["passed"] else "healthy sanitizer runtime probe failed"}


def run_validation(adapter, benchmarks, directory: Path, *, modes=("address","undefined"), differential=True,
                   controls=None, session=None, progress=None):
    if not modes or len(set(modes)) != len(modes) or any(m not in SANITIZERS for m in modes):
        raise AionError("Choose unique address/undefined sanitizer modes.")
    emit = progress or (lambda _:None)
    result = evidence_header("sanitizer-validation",adapter=adapter,controls=controls,session=session)
    result.update(probes={},benchmarks={},scope="separate correctness validation; instrumented runtime is not optimization evidence",
                  sanitizer_limits=asdict(Limits(timeout_seconds=30,memory_mb=None)),
                  limits_note="Separate sanitizer runs explicitly uncap memory for shadow mappings; time/CPU/output limits remain. Primary timing retains its OS-specific memory protection.",
                  sanitizer_environment=sanitizer_options(),
                  leak_detection=leak_detection_status(),
                  validation_manifest_sha256=file_sha256(ROOT/"validation.json"))
    root=directory/result["run_id"]
    root.mkdir(parents=True,exist_ok=True)
    for mode in modes:
        emit(f"Probing sanitizer {mode}")
        result["probes"][mode]=probe_sanitizer(adapter,mode,root,controls)
    for benchmark in benchmarks:
        b={"fingerprint":benchmark.fingerprint,"cases":validation_cases(benchmark),"modes":{},
           "source_provenance":[{"path":str(p.resolve()),"sha256":file_sha256(p)} for p in benchmark.source_files]}
        result["benchmarks"][benchmark.name]=b
        for mode in ([None] if differential else [])+list(modes):
            name=mode or "differential-o3"
            emit(f"Validating {benchmark.name}/{name}")
            entry={"checks":[],"status":"unsupported"}
            b["modes"][name]=entry
            if mode and not result["probes"][mode]["supported"]:
                continue
            binary=root/f"{benchmark.name}-{name}.exe"
            build=adapter.compile_validation(benchmark.compilation_input,binary,mode)
            entry["build"]=build
            if not build["success"]:
                entry["status"]="compile_failed";continue
            limits=Limits(timeout_seconds=30,memory_mb=None if mode else 1024)
            for case in b["cases"]:
                process=run_process([str(binary),*case["args"]],limits,controls=controls,env_overrides=sanitizer_options() if mode else None)
                entry["checks"].append({"case":case,"sample_id":f"{result['run_id']}:{benchmark.name}:{name}:{case['name']}",
                                        **check_sanitizer(process,case["expected"])})
                atomic_json(root/"partial.json",result)
            entry["status"]="passed" if all(c["passed"] for c in entry["checks"]) else "failed"
    statuses=[m["status"] for b in result["benchmarks"].values() for m in b["modes"].values()]
    result["status"]="passed" if statuses and all(s=="passed" for s in statuses) else "inconclusive" if all(s in {"passed","unsupported"} for s in statuses) else "failed"
    result["host_end"]=collect_host_diagnostics()
    atomic_json(root/"validation.json",result)
    return result
