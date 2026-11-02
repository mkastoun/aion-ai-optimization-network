"""Compatibility checks for independent runs, never pooled raw samples."""


def stable_environment_controls(host):
    restrictions=(host or {}).get('restrictions') or {}
    cgroup=restrictions.get('cgroup') or {}
    return {'scheduler_policy':restrictions.get('scheduler_policy'),'nice':restrictions.get('nice'),
            'allowed_cpus':restrictions.get('allowed_cpus'),'resource_limits':restrictions.get('resource_limits'),
            'cgroup_limits':{k:v for k,v in cgroup.items() if k!='cpu.stat'},
            'cgroup_process_paths':restrictions.get('cgroup_process_paths'),
            'governors':[(r['cpu'],r.get('governor')) for r in (host or {}).get('frequency_sysfs') or []],
            'turbo':(host or {}).get('turbo_controls_observed')}


def compare_run_compatibility(first: dict, second: dict) -> dict:
    reasons, unavailable = [], []
    method_a, method_b = first.get("methodology_version", 1), second.get("methodology_version", 1)
    if method_a != method_b:
        reasons.append("measurement methodology differs")
    if first.get("compiler") != second.get("compiler"):
        reasons.append("compiler identity differs")
    if first.get("environment") != second.get("environment"):
        reasons.append("hardware/OS/Python environment differs")
    if first.get("limits") != second.get("limits"):
        reasons.append("resource limits differ")
    if any(r.get("evidence_kind", "primary-timing") != "primary-timing" for r in (first,second)):
        reasons.append("diagnostic evidence cannot confirm primary timing")
    if method_a >= 3 or method_b >= 3:
        host_a = first.get("host_start", {}).get("host_fingerprint")
        host_b = second.get("host_start", {}).get("host_fingerprint")
        if not host_a or not host_b:
            reasons.append("stable host identity is unavailable")
        elif host_a != host_b:
            reasons.append("host identity differs; incompatible hosts must not be pooled or confirmed")
        placement_a = first.get("execution_controls", {}).get("requested_cpus")
        placement_b = second.get("execution_controls", {}).get("requested_cpus")
        if placement_a != placement_b:
            reasons.append("requested CPU placement differs")
        def power_settings(run):
            host = run.get("host_start") or {}
            governors = [(row["cpu"], row.get("governor")) for row in host.get("frequency_sysfs") or []]
            return {"governors": governors, "turbo": host.get("turbo_controls_observed")}
        if power_settings(first) != power_settings(second):
            reasons.append("observed governor/turbo configuration differs")
        for run in (first, second):
            requested = run.get("execution_controls", {}).get("requested_cpus")
            if requested is not None:
                for benchmark in run.get("benchmarks", {}).values():
                    for entry in benchmark.get("configurations", {}).values():
                        for sample in entry.get("samples", []):
                            proof = sample.get("execution_controls") or {}
                            if proof.get("verified") is not True or proof.get("effective_cpus") != requested:
                                reasons.append("effective measured workload affinity is unverified or differs")
        for key in ("compiler_binary_sha256", "linker_binary_sha256", "linker_version", "cxx_library_sha256"):
            a, b = (first.get("build_provenance") or {}).get(key), (second.get("build_provenance") or {}).get(key)
            if a != b:
                reasons.append(f"build provenance differs: {key}")
            if a is None or b is None:
                unavailable.append(key)
                if key in {"compiler_binary_sha256", "linker_binary_sha256"}:
                    reasons.append(f"build identity cannot be verified: {key}")
    else:
        unavailable.append("legacy result has no stable host or effective-control proof")
    if method_a>=4 or method_b>=4:
        for run in (first,second):
            if not run.get("session",{}).get("session_id"):
                reasons.append("observation session identity is unavailable")
        class_a=(first.get("host_start") or {}).get("environment_classification")
        class_b=(second.get("host_start") or {}).get("environment_classification")
        if class_a!=class_b: reasons.append("native/virtualized environment classification differs")
        if not class_a or not class_b: reasons.append('environment classification is unavailable')
        if stable_environment_controls(first.get('host_start'))!=stable_environment_controls(second.get('host_start')):
            reasons.append('observed scheduler/cgroup/CPU constraints differ')
    workloads_a, workloads_b = first.get("benchmarks", {}), second.get("benchmarks", {})
    if set(workloads_a) != set(workloads_b):
        reasons.append("selected workload suites differ")
    for name in set(workloads_a) & set(workloads_b):
        if workloads_a[name].get("fingerprint") != workloads_b[name].get("fingerprint"):
            reasons.append(f"source/input fingerprint differs: {name}")
    configs_a = {c["name"]: (c.get("flags"), c.get("build_mode", "standard")) for c in first.get("configurations", [])}
    configs_b = {c["name"]: (c.get("flags"), c.get("build_mode", "standard")) for c in second.get("configurations", [])}
    for name in set(configs_a) & set(configs_b):
        if configs_a[name] != configs_b[name]:
            reasons.append(f"candidate recipe differs: {name}")
    return {"compatible": not reasons, "reasons": sorted(set(reasons)), "unavailable": sorted(set(unavailable)),
            "pooling": "disabled: comparisons retain separate run estimates",
            "session_ids": [r.get("session",{}).get("session_id") for r in (first,second)],
            "different_sessions": first.get("session",{}).get("session_id") != second.get("session",{}).get("session_id"),
            "legacy_identity_unverified": method_a < 3 or method_b < 3}


def require_confirmation_compatible(first: dict, second: dict):
    from .errors import AionError
    result = compare_run_compatibility(first, second)
    if not result["compatible"]:
        raise AionError("Incompatible independent runs: " + "; ".join(result["reasons"]))
