"""Optional Linux counters. Whole-process profiling is separate from compute timing."""
from dataclasses import asdict
import errno
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from collections import Counter
import hashlib

from .benchmarks import load_benchmarks
from .errors import AionError
from .evidence import evidence_header
from .host import collect_host_diagnostics
from .models import Candidate, Limits
from .optimization import BASELINE
from .process import run_process
from .provenance import file_sha256
from .storage import atomic_json
from .verification import check_output, verify_binary
from .toolchain import find_llvm_tool

HELPER = Path(__file__).with_name("helpers") / "perf_runner.cpp"


def analyze_counters(raw: dict) -> dict:
    events = []
    for row in raw.get("events", []):
        e = {**row, "source": "Linux perf_event_open, generic event", "filter": "exclude_kernel=1, exclude_hv=1",
             "scope": "main workload thread, exec through exit; no inherited threads", "scaled_estimate": None,
             "running_fraction": None, "multiplexed": None}
        code = e.get("errno", 0)
        if code:
            e["status"] = "permission_denied" if code in {errno.EPERM, errno.EACCES} else "unsupported" if code in {errno.EINVAL, errno.ENOENT, errno.ENODEV, errno.EOPNOTSUPP, errno.ENOSYS} else "error"
            e["reason"] = os.strerror(code)
        elif e.get("raw_count") is None:
            e.update(status="unavailable", reason="no counter observation")
        elif (not isinstance(e.get("time_enabled_ns"), int) or not isinstance(e.get("time_running_ns"), int)
              or not 0 < e["time_running_ns"] <= e["time_enabled_ns"] or e["raw_count"] < 0):
            e.update(status="not_counted", reason="zero or invalid enabled/running time")
        else:
            e.update(status="counted", reason=None,
                     running_fraction=e["time_running_ns"] / e["time_enabled_ns"],
                     multiplexed=e["time_running_ns"] != e["time_enabled_ns"])
            if e["multiplexed"]:
                e["scaled_estimate"] = e["raw_count"] * e["time_enabled_ns"] / e["time_running_ns"]
        events.append(e)
    lookup = {e["name"]: e for e in events}
    derived = {}
    for name, numerator, denominator in (("instructions_per_cycle", "instructions", "cycles"),
            ("cache_miss_rate", "cache-misses", "cache-references"), ("branch_miss_rate", "branch-misses", "branches")):
        a, b = lookup.get(numerator, {}), lookup.get(denominator, {})
        valid = all(e.get("status") == "counted" and not e.get("multiplexed") for e in (a,b)) and b.get("raw_count", 0) > 0
        derived[name] = {"value": a["raw_count"] / b["raw_count"] if valid else None,
                         "source_events": [numerator, denominator],
                         "reason": None if valid else "requires two counted, unmultiplexed events and a nonzero denominator",
                         "scope": "whole-process user-mode observation, not compute-region IPC or a causal attribution"}
    return {"events": events, "derived": derived,
            "resource_usage": {"source": "wait4 rusage (software accounting, includes pre-exec child setup)",
                               "values": raw.get("rusage")},
            "multiplexing_policy": "retain raw counts and enabled/running times; scaled estimates are labeled; ratios suppressed when multiplexed"}


def build_counter_helper(adapter, directory: Path) -> tuple[Path, dict]:
    helper = directory / "perf-runner.exe"
    if not sys.platform.startswith('linux'):
        return helper, {'build':{'success':False,'reason':'Linux perf_event_open helper is unsupported on this OS'}}
    build = adapter.compile(HELPER, helper, Candidate("counter-helper", ("-O2",)))
    return helper, {"source_sha256": file_sha256(HELPER), "build": build}


def probe_counters(adapter, controls=None) -> dict:
    if not sys.platform.startswith("linux"):
        return {"available": False, "reason": "perf_event_open requires Linux", "events": []}
    with tempfile.TemporaryDirectory(prefix="aion-counter-probe-") as temp:
        root = Path(temp)
        helper, evidence = build_counter_helper(adapter, root)
        if not evidence["build"]["success"]:
            return {"available": False, "reason": "trusted counter helper could not compile", "helper": evidence, "events": []}
        output = root / "counters.json"
        true = shutil.which("true")
        if not true: return {"available": False, "reason": "local true probe unavailable", "events": []}
        result = run_process([str(helper), str(output), true], Limits(), controls=controls)
        if not output.is_file():
            return {"available": False, "reason": "counter probe failed", "process": result.to_dict(), "helper": evidence, "events": []}
        analyzed = analyze_counters(json.loads(output.read_text()))
        return {**analyzed, "available": any(e["status"] == "counted" for e in analyzed["events"]),
                "process": result.to_dict(), "helper": evidence,
                "perf_event_paranoid": _read(Path("/proc/sys/kernel/perf_event_paranoid")),
                "generic_cpu_event_source_type": _read(Path("/sys/bus/event_source/devices/cpu/type"))}


def _read(path):
    try: return path.read_text().strip()
    except OSError: return None


def profile_execution(helper, binary, case, batches, limits, output, controls=None, *, sampling=False) -> dict:
    if not sys.platform.startswith('linux'):
        raise AionError('Linux perf_event_open execution is unsupported on this OS.')
    process = run_process([str(helper), *(["--sample"] if sampling else []), str(output), str(binary), *case["args"], "--measure", str(batches)],
                          limits, controls=controls)
    expected = str(int(case["expected"]) * batches & ((1 << 64)-1))
    # Profiling stdout uses the normal workload measurement protocol, but these
    # times are diagnostics and are never passed to timing comparison functions.
    metadata_error=None
    try:
        raw = json.loads(output.read_text()) if output.is_file() else {}
        if not isinstance(raw,dict) or raw.get('protocol')!='aion-perf-v1':
            raw={};metadata_error="missing/invalid counter helper metadata"
    except (OSError,ValueError):
        raw={};metadata_error="counter helper metadata could not be read"
    record = {"passed": process.ok and metadata_error is None, "process": process.to_dict(), "counter_raw": raw,
              "counters": analyze_counters(raw), "workload_observation": None, "reasons": []}
    if metadata_error: record['reasons'].append(metadata_error)
    try:
        data = json.loads(process.stdout)
        if data.get("protocol") != "aion-compute-v1" or data.get("checksum") != expected or data.get("batches") != batches:
            raise ValueError("profiled workload output/checksum differs")
        requested = controls.to_dict()["requested_cpus"] if controls else None
        if data.get("pid") != raw.get("child_pid"):
            raise ValueError("profiled executable PID is unverified")
        if requested is not None and (data.get("affinity_start") != requested or data.get("affinity_end") != requested):
            raise ValueError("profiled executable affinity differs")
        record["workload_observation"] = data
    except (ValueError, TypeError, AttributeError) as exc:
        record["passed"] = False
        record["reasons"].append(str(exc))
    if not process.ok: record["reasons"].append("profiled execution failed")
    return record


def resolve_sample_ips(ips, maps, *, resolver=None, expected_objects=None):
    if sys.platform == 'darwin':
        return {'addresses':[], 'objects':{}, 'symbols':[], 'available':False,
                'reason':'Linux ELF mapping/sized-symbol attribution is unsupported for macOS Mach-O; no attribution fabricated'}
    """Resolve sampled user IPs, preserving unresolved addresses and mappings."""
    mappings=[]
    for line in maps.splitlines():
        parts=line.split(maxsplit=5)
        if len(parts)<6 or 'x' not in parts[1]: continue
        try:
            start,end=(int(v,16) for v in parts[0].split('-'))
            mappings.append((start,end,int(parts[2],16),parts[5]))
        except ValueError: continue
    objects={};addresses=[]
    for ip,count in Counter(ips).items():
        match=next((m for m in mappings if m[0]<=ip<m[1]),None)
        row={"ip":ip,"sample_count":count,"object":match[3] if match else None,"object_address":None,"symbol":None}
        if match and Path(match[3]).is_file():
            path=Path(match[3])
            if str(path) not in objects:
                try:
                    with path.open('rb') as stream: header=stream.read(20)
                    elf_type=int.from_bytes(header[16:18],'little' if header[5]==1 else 'big') if header[:4]==b'\x7fELF' else None
                except (OSError,IndexError): elf_type=None
                sha=file_sha256(path)
                identity_matches=expected_objects is None or sha==(expected_objects.get(str(path)) or {}).get('sha256')
                objects[str(path)]={"sha256":sha,"elf_type":elf_type,'identity_matches':identity_matches}
            if objects[str(path)]['identity_matches']:
                row['object_address']=ip if objects[str(path)]['elf_type']==2 else ip-match[0]+match[2]
            else:row['resolution_limit']='mapped object no longer matches the recorded SHA-256'
        addresses.append(row)
    resolver=resolver or find_llvm_tool('llvm-addr2line', fallback=('addr2line',))
    diagnostics=[]
    if resolver:
        for path in objects:
            pending=[r for r in addresses if r['object']==path and r['object_address'] is not None]
            for offset in range(0,len(pending),256):
                batch=pending[offset:offset+256]
                resolved=run_process([resolver,'-f','-C','-e',path,*[hex(r['object_address']) for r in batch]],
                                     Limits(timeout_seconds=30,output_bytes=4*1024*1024))
                diagnostics.append(resolved.to_dict())
                lines=resolved.stdout.splitlines()
                if resolved.ok and len(lines)==2*len(batch):
                    for index,row in enumerate(batch):
                        row['nearest_symbol_hint']=None if lines[2*index]=='??' else lines[2*index]
                        row['source_location']=lines[2*index+1]
    # addr2line may label an address in a stripped libc implementation with an
    # unrelated nearby exported symbol. Require an actual sized function range.
    nm=find_llvm_tool('llvm-nm', fallback=('nm',));tables=[]
    for path,identity in objects.items():
        if not identity['identity_matches'] or not nm:continue
        ranges=[]
        for dynamic in (False,True):
            command=[nm,'-S','-n','--defined-only',*(['-D'] if dynamic else []),path]
            result=run_process(command,Limits(timeout_seconds=30,output_bytes=8*1024*1024))
            tables.append({'command':command,'returncode':result.returncode,'stderr':result.stderr,
                           'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),'dynamic_symbols':dynamic})
            if result.ok:
                for line in result.stdout.splitlines():
                    parts=line.split(maxsplit=3)
                    if len(parts)!=4 or parts[2] not in 'tTwW':continue
                    try:start,size=int(parts[0],16),int(parts[1],16)
                    except ValueError:continue
                    if size:ranges.append((start,start+size,parts[3]))
            if ranges:break
        for row in addresses:
            if row['object']!=path or row['object_address'] is None:continue
            match=next((r for r in ranges if r[0]<=row['object_address']<r[1]),None)
            if match:
                row.update(symbol=match[2],symbol_start=match[0],symbol_end=match[1],resolution='verified-sized-function-range')
            else:row['resolution']='unresolved; nearest-symbol hints are not attribution'
    filt=shutil.which('c++filt')
    names=sorted({r['symbol'] for r in addresses if r['symbol']})
    demangled={}
    if filt:
        for offset in range(0,len(names),128):
            batch=names[offset:offset+128]
            result=run_process([filt,'--',*batch],Limits(timeout_seconds=10,output_bytes=1024*1024))
            lines=result.stdout.splitlines()
            if result.ok and len(lines)==len(batch):demangled.update(zip(batch,lines))
    for row in addresses:
        if row['symbol']:row['symbol']=demangled.get(row['symbol'],row['symbol'])
    symbols=Counter()
    for row in addresses: symbols[(row['object'],row['symbol'])]+=row['sample_count']
    return {"addresses":addresses,"objects":objects,"symbolizer":resolver,"symbolizer_processes":diagnostics,
            'function_range_source':nm,'symbol_table_observations':tables,
            'resolution_methodology_version':2,
            'resolution_policy':'Only sized nm text-function ranges establish symbols. addr2line-only names are retained as unverified hints; stripped private code may remain unresolved.',
            "symbols":[{"object":obj,"symbol":symbol,"sample_count":count,
                         "sample_fraction":count/len(ips) if ips else None} for (obj,symbol),count in symbols.most_common()],
            "scope":"fractions of recorded user-cycle IP samples; not exact CPU-time fractions, call counts, or causal effects"}


def resolve_profile_symbols(source_path: Path, source: dict):
    if source.get('evidence_kind')!='profiling':raise AionError('Symbol audits require saved profiling evidence.')
    result=evidence_header('symbol-resolution')
    result.update(source_profile={'run_id':source['run_id'],'path':str(source_path.resolve()),'sha256':file_sha256(source_path)},
                  benchmarks={},note='Derived resolution of retained IPs; raw counters/profiles are unchanged. Earlier addr2line-only names are hints, not verified function attribution.')
    for workload,b in source['benchmarks'].items():
        entries={};result['benchmarks'][workload]={'fingerprint':b['fingerprint'],'configurations':entries}
        for name,entry in b['configurations'].items():
            h=entry.get('hotspots',{});raw=h.get('execution',{}).get('counter_raw',{}).get('sampling',{})
            old_objects=h.get('resolved',{}).get('objects',{})
            resolved=resolve_sample_ips(raw.get('ips',[]),raw.get('maps',''),expected_objects=old_objects)
            entries[name]={'source_binary_sha256':entry.get('source_binary_sha256'),'profiled_binary_sha256':entry.get('build',{}).get('binary_sha256'),
                           'matches_timed_binary':entry.get('matches_timed_binary'),'sampling_available':h.get('available',False),
                           'sample_count':len(raw.get('ips',[])),'lost_samples':raw.get('lost_samples'),'buffer_overrun':raw.get('buffer_overrun'),
                           'resolved':resolved}
    return result


def sample_native_hotspots(helper,binary,case,batches,directory,limits,controls):
    directory.mkdir(parents=True,exist_ok=True)
    record=profile_execution(helper,binary,case,batches,limits,directory/'sampling.json',controls,sampling=True)
    raw=record.get('counter_raw',{}).get('sampling',{})
    symbols=resolve_sample_ips(raw.get('ips',[]),raw.get('maps',''))
    complete=bool(raw.get('ips')) and record['passed'] and not raw.get('lost_samples') and not raw.get('buffer_overrun')
    return {"available":record['passed'] and bool(raw.get('ips')),"complete":complete,
            "source":"Linux perf_event_open user-cycle IP sampling, 997 Hz requested",
            "reason":None if raw.get('ips') else "No samples: inspect per-event permission/support, mmap status and runtime duration",
            "execution":record,"resolved":symbols,
            "attribution_limit":"Mapping snapshots may miss transient mappings; unresolved addresses and lost/overrun indicators are retained. Sampling is a separate instrumented execution."}


def sample_hotspots(binary, case, batches, directory, limits, controls=None, helper=None) -> dict:
    if not sys.platform.startswith('linux'):
        return {'available':False,'reason':'Linux perf_event_open/perf sampling is unsupported on this OS'}
    if helper is not None:
        return sample_native_hotspots(helper,binary,case,batches,directory,limits,controls)
    perf = shutil.which("perf")
    if not perf: return {"available": False, "reason": "Linux perf sampling tool unavailable"}
    directory.mkdir(parents=True, exist_ok=True)
    data = directory / "perf.data"
    version = run_process([perf,"--version"], Limits(timeout_seconds=10))
    recorded = run_process([perf,"record","-e","cycles:u","-g","--call-graph","dwarf","-o",str(data),"--",
                           str(binary),*case["args"],"--measure",str(batches)], limits, controls=controls)
    result = {"tool": perf, "tool_sha256": file_sha256(Path(perf)), "version": version.to_dict(),
              "record": recorded.to_dict(), "scope": "separate whole-process user-cycle sampling; not primary timing"}
    if not recorded.ok or not data.is_file():
        return {**result, "available": False, "reason": "perf sampling unsupported or denied; raw diagnostics retained"}
    reported = run_process([perf,"report","--stdio","--no-children","-i",str(data),"--sort","symbol"],
                           Limits(timeout_seconds=30,output_bytes=8*1024*1024))
    text = directory / "hotspots.txt"
    text.write_text(reported.stdout, encoding="utf-8")
    return {**result,"available": reported.ok, "data_sha256": file_sha256(data), "report": reported.to_dict(),
            "data": str(data.resolve()), "report_path": str(text.resolve())}


def run_profiles(adapter, source_path: Path, source: dict, selection: str, candidates: list[str] | None,
                 directory: Path, *, samples=3, controls=None, session=None, codegen=False, hotspots=False, progress=None):
    if source.get("evidence_kind", "primary-timing") != "primary-timing" or source.get("methodology_version", 1) < 3:
        raise AionError("Profiling requires preserved ordinary Phase 3+ timing evidence with executable PID/affinity fields.")
    if not 1 <= samples <= 30: raise AionError("Profile repetitions must be 1..30.")
    emit = progress or (lambda _: None)
    benchmarks = load_benchmarks(','.join(source['benchmarks']) if selection=='all' else selection)
    for benchmark in benchmarks:
        old=source['benchmarks'].get(benchmark.name)
        if not old or old['fingerprint']!=benchmark.fingerprint:
            raise AionError(f"Source/input fingerprint mismatch for profiling {benchmark.name}; frozen sources must be restored explicitly.")
    result = evidence_header("profiling", adapter=adapter, controls=controls, session=session)
    result.update(source_result={"path": str(source_path.resolve()), "sha256": file_sha256(source_path), "run_id": source["run_id"],
                                  "host_fingerprint": source.get("host_start",{}).get("host_fingerprint"),
                                  "session": source.get("session"),"compiler":source.get("compiler"),
                                  "build_provenance":source.get("build_provenance"),"execution_controls":source.get("execution_controls")},
                  benchmarks={}, notes=["Counters cover exec through exit including input setup and checksum output.",
                  "CPU-time and rusage are software accounting, not hardware counters. No timing/preset claims from profiling."])
    result["source_environment_matches"] = (source.get("host_start",{}).get("host_fingerprint")==result["host_start"]["host_fingerprint"]
        and source.get("compiler")==result["compiler"] and all((source.get("build_provenance") or {}).get(k)==(result.get("build_provenance") or {}).get(k)
             for k in ("compiler_binary_sha256","linker_binary_sha256","cxx_library_sha256")))
    result["source_placement_matches"] = (source.get("execution_controls",{}).get("requested_cpus") == (result.get("execution_controls") or {}).get("requested_cpus"))
    result["counter_scope"]="Hardware-type events exposed by this environment/guest; no claim of physical-host counter isolation. Each sample records its own event availability."
    result["work_unit_policy"]="All configurations of a workload use its source baseline batch count, equal inputs and equal work. Each source configuration's original batch count is also retained. Whole-process setup remains included."
    root = directory / result["run_id"]
    root.mkdir(parents=True, exist_ok=True)
    if not sys.platform.startswith("linux"):
        result.update(status="unsupported", reason="Linux perf_event_open unavailable")
        return result
    helper, helper_build = build_counter_helper(adapter, root)
    result["counter_helper"] = helper_build
    if not helper_build["build"]["success"]:
        result.update(status="unsupported", reason="counter helper compilation failed")
        return result
    result["counter_environment"] = {"perf_event_paranoid": _read(Path("/proc/sys/kernel/perf_event_paranoid")),
        "cpu_event_source_type": _read(Path("/sys/bus/event_source/devices/cpu/type"))}
    for benchmark in benchmarks:
        old = source["benchmarks"].get(benchmark.name)
        if not old or old["fingerprint"] != benchmark.fingerprint:
            raise AionError(f"Source/input fingerprint mismatch for profiling {benchmark.name}; frozen sources must be restored explicitly.")
        configs = candidates or list(old["configurations"])
        if len(set(configs)) != len(configs) or any(n not in old["configurations"] for n in configs):
            raise AionError("Choose unique configurations present in the source timing result.")
        b = {"fingerprint": benchmark.fingerprint, "measurement_case": old["measurement_case"], "configurations": {},
             "source_provenance": [{"path":str(p.resolve()),"sha256":file_sha256(p)} for p in benchmark.source_files]}
        result["benchmarks"][benchmark.name] = b
        profile_batches=old['configurations']['baseline'].get('calibration',{}).get('batches')
        if not isinstance(profile_batches,int) or profile_batches<1:
            raise AionError("Source baseline has no calibrated work unit for equal-work profiling.")
        for configuration_index,name in enumerate(configs):
            emit(f"Profiling {benchmark.name}/{name}")
            previous = old["configurations"][name]
            config = next(c for c in source["configurations"] if c["name"] == name)
            candidate = Candidate(name,tuple(config["flags"]),build_mode=config.get("build_mode","standard"))
            if candidate.build_mode not in {"standard","pgo"}: raise AionError("Experimental controls are not profiler optimization candidates.")
            # Saved labels are data, never filesystem path components.
            destination = root / benchmark.name / f"config-{configuration_index}"
            destination.mkdir(parents=True, exist_ok=True)
            binary = destination / "workload.exe"
            if codegen:
                from .investigation import capture_build_diagnostics
                diagnostics = capture_build_diagnostics(adapter,benchmark,candidate,destination,controls)
                build = diagnostics["build"]
            else:
                build = adapter.compile_profiled(benchmark.compilation_input,binary,candidate,[benchmark.case("training")],Limits(),
                         controls=controls,profile_archive=destination/"profiles") if candidate.build_mode == "pgo" else adapter.compile(benchmark.compilation_input,binary,candidate)
                diagnostics = None
            entry = {"build":build,"codegen":({"path":str((destination/'evidence.json').resolve()),
                     "sha256":file_sha256(destination/'evidence.json'),"scope":"preserved disassembly, pre-link IR, optimization remarks and full codegen provenance"} if diagnostics else None),
                     "source_binary_sha256":previous.get("build",{}).get("binary_sha256"),
                     "matches_timed_binary":bool(previous.get("build",{}).get("binary_sha256") and build.get("binary_sha256") == previous.get("build",{}).get("binary_sha256")),
                     "source_batches":previous.get('calibration',{}).get('batches'),
                     "source_sample_ids":[s.get('sample_id') or f"{source['run_id']}:{benchmark.name}:{name}:{s.get('pair_id')}" for s in previous.get('samples',[])],
                     "samples":[],"status":"compile_failed"}
            b["configurations"][name] = entry
            if not build["success"]:
                result["status"]="failed"
                continue
            entry["verification"] = diagnostics['verification'] if diagnostics and diagnostics.get('verification') else verify_binary(binary,benchmark,Limits(),controls=controls)
            if not entry["verification"]["passed"]:
                entry["status"]="incorrect";result["status"]="failed";continue
            batches = profile_batches
            if not isinstance(batches,int) or batches < 1: raise AionError("Source result has no valid calibrated work unit.")
            entry["batches"] = batches
            for index in range(samples):
                record = profile_execution(helper,binary,b["measurement_case"],batches,Limits(),destination/f"counter-{index}.json",controls)
                record.update(sample_id=f"{result['run_id']}:{benchmark.name}:{name}:{index}", iteration=index,
                              source_binary_sha256=entry["source_binary_sha256"], binary_sha256=build["binary_sha256"],
                              input_case=b["measurement_case"], batches=batches)
                entry["samples"].append(record)
                atomic_json(root/"partial.json",result)
            entry["status"]="profiled" if all(s["passed"] for s in entry["samples"]) else "execution_failed"
            entry["attributable_binary_and_environment"] = entry["matches_timed_binary"] and result["source_environment_matches"] and result["source_placement_matches"] and entry["status"]=="profiled"
            if entry["status"] != "profiled": result["status"]="failed"
            if not entry["matches_timed_binary"]: entry["attribution_limit"]="rebuilt binary differs; cannot attribute these counters to the preserved timed executable"
            if hotspots: entry["hotspots"] = sample_hotspots(binary,b["measurement_case"],batches,destination/"sampling",Limits(),controls,helper)
            entry['binary_unchanged_after_profiling']=file_sha256(binary)==build['binary_sha256']
            if not entry['binary_unchanged_after_profiling']:
                entry['status']='binary_changed';result['status']='failed';entry['attributable_binary_and_environment']=False
            atomic_json(root/'partial.json',result)
    result["host_end"] = collect_host_diagnostics()
    atomic_json(root/"profiling.json",result)
    return result
