from dataclasses import asdict, replace
from pathlib import Path
import re
import shutil
import tempfile
import hashlib
import os
import sys
from typing import Protocol
from collections.abc import Sequence

from .errors import AionError
from .models import Candidate, CompilerInfo, Limits
from .optimization import validate_candidate, validate_flags
from .process import run_process
from .controls import ExecutionControls
from .provenance import file_sha256
from .toolchain import llvm_tool_candidates, find_llvm_tool

SourceInput = Path | Sequence[Path]


def binary_format(path):
    with path.open('rb') as stream:
        magic = stream.read(4)
    if magic == b'\x7fELF':return 'ELF'
    if magic in (b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xce', b'\xca\xfe\xba\xbe'):return 'Mach-O'
    if magic[:2] == b'MZ':return 'PE'
    return 'unknown'


def source_paths(source: SourceInput) -> tuple[Path, ...]:
    return (source,) if isinstance(source, Path) else tuple(source)


class CompilerAdapter(Protocol):
    info: CompilerInfo

    def compile(self, source: SourceInput, output: Path, candidate: Candidate) -> dict: ...

    def probe(self, candidate: Candidate, *, controls: ExecutionControls | None = None) -> dict: ...

    def compile_profiled(self, source: SourceInput, output: Path, candidate: Candidate,
                         training_cases: list[dict], limits: Limits, *,
                         controls: ExecutionControls | None = None,
                         profile_archive: Path | None = None) -> dict: ...


class ClangAdapter:
    def __init__(self, executable: str = "clang++", timeout: float = 60):
        if executable == 'clang++':
            executable = os.environ.get('AION_CXX', executable)
        resolved = shutil.which(executable)
        if resolved is None:
            raise AionError(f"Clang C++ compiler '{executable}' was not found. "
                            "Install Clang and a C++ standard library, or pass --compiler /path/to/clang++.")
        self.timeout = timeout
        version = run_process([resolved, "--version"], Limits(timeout_seconds=10))
        match = re.search(r"(?:Apple )?clang version (\d+)", version.stdout)
        if not version.ok or not match:
            raise AionError(f"'{executable}' is not a working Clang compiler: {version.stderr.strip()}")
        target = run_process([resolved, "-dumpmachine"], Limits(timeout_seconds=10))
        if not target.ok or not target.stdout.strip():
            raise AionError(f"Cannot detect Clang target: {target.stderr.strip()}")
        # Preserve the driver name: clang++ is commonly a symlink to clang,
        # and resolving it changes argv[0] and disables automatic C++ linking.
        self.info = CompilerInfo(str(Path(resolved).absolute()), version.stdout.splitlines()[0],
                                 int(match.group(1)), target.stdout.strip(),
                                 'apple-clang' if 'Apple' in version.stdout.splitlines()[0] else 'clang')

    def compile(self, source: SourceInput, output: Path, candidate: Candidate) -> dict:
        validate_candidate(candidate)
        if candidate.build_mode != "standard":
            raise AionError("PGO requires an instrument/train/merge/rebuild workflow.")
        return self._compile(source, output, candidate.flags)

    def _compile(self, source: SourceInput, output: Path, flags: tuple[str, ...],
                 internal_flags: tuple[str, ...] = ()) -> dict:
        flags = validate_flags(flags)
        sources = source_paths(source)
        if not sources:
            raise AionError("Compilation requires at least one translation unit.")
        output.parent.mkdir(parents=True, exist_ok=True)
        result = run_process(
            [self.info.path, "-std=c++17", "-Werror=unused-command-line-argument",
             *flags, *internal_flags, *[str(path.resolve()) for path in sources], "-o", str(output.resolve())],
            Limits(timeout_seconds=self.timeout, memory_mb=2048, output_bytes=64*1024*1024),
        )
        return {"success": result.ok and output.is_file(), "process": result.to_dict(),
                "seconds": result.duration_seconds,
                "executable_bytes": output.stat().st_size if result.ok and output.exists() else None,
                "compiler": asdict(self.info),
                "binary_sha256": file_sha256(output) if result.ok and output.is_file() else None,
                "binary_format": binary_format(output) if result.ok and output.is_file() else None,
                "sources": [{"path": str(path.resolve()), "sha256": file_sha256(path)} for path in sources]}

    def build_provenance(self) -> dict:
        cached = getattr(self, "_build_provenance", None)
        if cached is not None:
            return cached
        if sys.platform == 'darwin':
            return self._darwin_build_provenance()
        selected = run_process([self.info.path, "-print-prog-name=ld"], Limits(timeout_seconds=10))
        linker = shutil.which(selected.stdout.strip()) if selected.ok else None
        version = run_process([linker, "--version"], Limits(timeout_seconds=10)) if linker else None
        library = run_process([self.info.path, "-print-file-name=libstdc++.so"], Limits(timeout_seconds=10))
        library_path = Path(library.stdout.strip()) if library.ok else None
        self._build_provenance = {
            "compiler": asdict(self.info), "compiler_binary_sha256": file_sha256(Path(self.info.path)),
            "linker_path": str(Path(linker).absolute()) if linker else None,
            "linker_version": version.stdout.strip() if version and version.ok else None,
            "linker_binary_sha256": file_sha256(Path(linker)) if linker else None,
            "cxx_library": str(library_path) if library_path and library_path.is_file() else None,
            "cxx_library_sha256": file_sha256(library_path) if library_path else None,
            "build_language_standard": "c++17", "available": True,
        }
        return self._build_provenance

    def _darwin_build_provenance(self):
        selected = run_process([self.info.path, '-print-prog-name=ld'], Limits(timeout_seconds=10))
        linker = shutil.which(selected.stdout.strip()) if selected.ok else None
        version = run_process([linker, '-v'], Limits(timeout_seconds=10)) if linker else None
        library = run_process([self.info.path, '-print-file-name=libc++.dylib'], Limits(timeout_seconds=10))
        library_path = Path(library.stdout.strip()) if library.ok and library.stdout.strip() else None
        sdk = os.environ.get('SDKROOT')
        sdk_probe = None
        if not sdk and (xcrun := shutil.which('xcrun')):
            sdk_probe = run_process([xcrun, '--show-sdk-path'], Limits(timeout_seconds=10))
            sdk = sdk_probe.stdout.strip() if sdk_probe.ok else None
        stub = Path(sdk) / 'usr/lib/libc++.tbd' if sdk else None
        tools = {}
        for name in ('llvm-profdata','llvm-objdump','llvm-nm','llvm-symbolizer'):
            try:
                path = find_llvm_tool(name, self.info)
                tools[name] = {'path':path,'available':path is not None,'reason':None if path else 'optional local tool not found'}
            except AionError as exc:tools[name] = {'available':False,'reason':str(exc),'path':None}
        self._build_provenance = {
            'compiler': asdict(self.info), 'compiler_binary_sha256': file_sha256(Path(self.info.path)),
            'linker_path': str(Path(linker).absolute()) if linker else None,
            'linker_version': (version.stdout + version.stderr).strip() if version else None,
            'linker_version_process': version.to_dict() if version else None,
            'linker_binary_sha256': file_sha256(Path(linker)) if linker else None,
            'cxx_library': str(library_path) if library_path and library_path.is_file() else None,
            'cxx_library_sha256': file_sha256(library_path) if library_path and library_path.is_file() else None,
            'cxx_library_family': 'libc++', 'sdk_root': sdk, 'sdk_probe': sdk_probe.to_dict() if sdk_probe else None,
            'llvm_tools': tools,
            'sdk_library_stub': str(stub) if stub and stub.is_file() else None,
            'sdk_library_stub_sha256': file_sha256(stub) if stub and stub.is_file() else None,
            'library_identity_caveat': 'SDK stubs are not runtime library bytes; a dyld shared-cache image may have no standalone hash.',
            'build_language_standard': 'c++17', 'available': True,
        }
        return self._build_provenance

    def compile_validation(self, source: SourceInput, output: Path, sanitizer: str | None) -> dict:
        if sanitizer not in {None, "address", "undefined"}:
            raise AionError("Supported separate validation modes are address and undefined.")
        internal = (("-g", "-fno-omit-frame-pointer", f"-fsanitize={sanitizer}", "-fno-sanitize-recover=all")
                    if sanitizer else ())
        build = self._compile(source, output, ("-O2",) if sanitizer else ("-O3",), internal)
        return {**build, "instrumentation": sanitizer, "evidence_only": True,
                "promotion_eligible": False, "instrumentation_flags": list(internal)}

    def _profdata_tool(self) -> tuple[str, str]:
        for path in llvm_tool_candidates('llvm-profdata', self.info):
            version = run_process([path, '--version'], Limits(timeout_seconds=10))
            match = re.search(r'version\s+(\d+)', version.stdout)
            apple = self.info.family == 'apple-clang'
            builds = [re.search(r'clang-([\d.]+)', text) for text in (self.info.version, version.stdout)]
            vendor_matches = ('Apple' in version.stdout) == apple
            build_matches = not apple or (all(builds) and builds[0].group(1) == builds[1].group(1))
            if version.ok and match and int(match.group(1)) == self.info.major and vendor_matches and build_matches:
                return path, version.stdout.strip()
        raise AionError(f'PGO needs llvm-profdata matching {self.info.family} {self.info.major}; Apple builds also require the same clang build identity. Configure AION_LLVM_PROFDATA or use upstream LLVM and its sibling tools.')

    def compile_profiled(self, source: SourceInput, output: Path, candidate: Candidate,
                         training_cases: list[dict], limits: Limits, *, controls: ExecutionControls | None = None,
                         profile_archive: Path | None = None, training_measurement_batches: int | None = None) -> dict:
        validate_candidate(candidate)
        if candidate.build_mode != "pgo" or not training_cases:
            raise AionError("PGO requires an explicit recipe and independent training inputs.")
        tool, version = self._profdata_tool()
        from .verification import check_output, measure_binary
        if training_measurement_batches is not None and training_measurement_batches != 1:
            raise AionError("Research measurement-path training uses exactly one batch.")
        with tempfile.TemporaryDirectory(prefix="aion-pgo-") as directory:
            root = Path(directory)
            instrumented, profile = root / "training.exe", root / "merged.profdata"
            instrument = self._compile(source, instrumented, candidate.flags, ("-fprofile-instr-generate",))
            evidence = {"tool": tool, "tool_version": version, "instrumentation": instrument,
                        "training": [], "fresh_profile": True,
                        "profile_pattern": str(root / "%m-%p.profraw"),
                        "training_path": "measure-one-batch" if training_measurement_batches else "ordinary-checksum"}
            if not instrument["success"]:
                return {**instrument, "pgo": evidence}
            for case in training_cases:
                if training_measurement_batches:
                    check = {"case": case, **measure_binary(instrumented, case, 1, limits, controls=controls,
                              env_overrides={"LLVM_PROFILE_FILE": str(root / "%m-%p.profraw")})}
                    executed_dict = check["process"]
                else:
                    executed = run_process([str(instrumented), *case["args"]], limits,
                                       env_overrides={"LLVM_PROFILE_FILE": str(root / "%m-%p.profraw")},
                                       **({"controls": controls} if controls else {}))
                    check = {"case": case, **check_output(executed, case["expected"])}
                    executed_dict = executed.to_dict()
                evidence["training"].append(check)
                if not check["passed"]:
                    return {"success": False, "seconds": instrument["seconds"], "pgo": evidence,
                            "executable_bytes": None, "process": executed_dict, "compiler": asdict(self.info)}
            profiles = sorted(root.glob("*.profraw"))
            if not profiles:
                return {**instrument, "success": False, "pgo": evidence, "executable_bytes": None}
            evidence["raw_profile_sha256"] = [hashlib.sha256(p.read_bytes()).hexdigest() for p in profiles]
            merged = run_process([tool, "merge", "-o", str(profile), *map(str, profiles)],
                                 Limits(timeout_seconds=self.timeout, memory_mb=2048, output_bytes=64*1024*1024))
            evidence["merge"] = merged.to_dict()
            if not merged.ok or not profile.exists():
                return {"success": False, "seconds": instrument["seconds"], "pgo": evidence,
                        "executable_bytes": None, "process": merged.to_dict(), "compiler": asdict(self.info)}
            evidence["profile_sha256"] = hashlib.sha256(profile.read_bytes()).hexdigest()
            if profile_archive is not None:
                profile_archive.mkdir(parents=True, exist_ok=True)
                saved = profile_archive / "merged.profdata"
                shutil.copy2(profile, saved)
                for index, raw in enumerate(profiles):
                    shutil.copy2(raw, profile_archive / f"raw-{index}.profraw")
                evidence["saved_profile"] = str(saved.resolve())
            build = self._compile(source, output, candidate.flags,
                                  (f"-fprofile-instr-use={profile}", "-Werror=profile-instr-out-of-date"))
            evidence["total_build_seconds"] = (instrument["seconds"] + merged.duration_seconds + build["seconds"])
            return {**build, "pgo": evidence}

    def probe(self, candidate: Candidate, *, controls: ExecutionControls | None = None) -> dict:
        validate_candidate(candidate)
        if candidate.build_mode.startswith("control-"):
            candidate = replace(candidate, build_mode="standard")
        with tempfile.TemporaryDirectory(prefix="aion-probe-") as directory:
            root = Path(directory)
            source = root / "probe.cpp"
            source.write_text('#include <iostream>\nint main(){std::cout << "aion\\n";}\n',
                              encoding="utf-8")
            output = root / "probe.exe"
            try:
                build = (self.compile_profiled(source, output, candidate,
                                               [{"name": "probe", "args": [], "expected": "aion"}], Limits())
                         if candidate.build_mode == "pgo" else self.compile(source, output, candidate))
            except AionError as exc:
                return {"supported": False, "reason": str(exc)}
            if not build["success"]:
                return {"supported": False, "build": build, "reason": "compile/link failed"}
            result = run_process([str(output)], Limits(timeout_seconds=10),
                                 **({"controls": controls} if controls else {}))
            return {"supported": result.ok and result.stdout.strip() == "aion",
                    "build": build, "execution": result.to_dict(),
                    "reason": "" if result.ok else "compiled probe could not execute"}
