"""Read-only host observations. Unknown metrics stay null with provenance."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

from .controls import allowed_cpus
from .environment import machine_environment


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def classify_environment(release: str, cpuinfo: str | None, *, linux: bool,
                         dmi: dict | None = None, hypervisor: str | None = None,
                         container: str | None = None) -> dict:
    """Observational classification, never proof that virtualization is absent."""
    release = release.lower()
    evidence = []
    if not linux:
        classification, kind = "non-linux", "unavailable"
    elif "microsoft" in release or "wsl" in release:
        classification, kind = ("wsl2", "wsl2") if "wsl2" in release else ("wsl", "wsl")
        evidence.append("kernel release identifies Microsoft/WSL")
    else:
        text = " ".join(str(v or "") for v in (dmi or {}).values()).lower()
        vendor = any(v in text for v in ("vmware", "virtualbox", "virtual machine", "kvm", "qemu",
                                          "xen", "amazon ec2", "google compute", "parallels", "bhyve"))
        hosted_ci = os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('RUNNER_ENVIRONMENT') != 'self-hosted'
        if hypervisor or vendor or "hypervisor" in (cpuinfo or "").split() or hosted_ci:
            classification, kind = "virtual-machine", "hypervisor-detected"
            if hypervisor: evidence.append("sysfs hypervisor type exposed")
            if hosted_ci: evidence.append("GitHub-hosted virtual runner; never native bare-metal evidence")
            if vendor: evidence.append("DMI identifies a virtualization platform")
            if "hypervisor" in (cpuinfo or "").split(): evidence.append("CPU hypervisor feature exposed")
        elif container:
            classification, kind = "container", "container-detected"
            evidence.append("container marker exposed")
        else:
            classification, kind = "native-linux", "none-detected"
            evidence.append("no virtualization indicator detected; this is not proof of bare metal")
    return {"classification": classification, "kind": kind, "evidence": evidence,
            "container": container, "physical_cpu_placement_verified": False,
            "detection_scope": "guest-visible kernel, CPU, DMI, hypervisor and container indicators"}


def collect_host_diagnostics(sys_root: Path = Path("/sys"), proc_root: Path = Path("/proc")) -> dict:
    environment = machine_environment()
    allowed = allowed_cpus()
    linux = sys.platform.startswith("linux")
    release = environment["release"].lower()
    cpuinfo = _read(proc_root / "cpuinfo") if linux else None
    dmi = {name: _read(sys_root / "class/dmi/id" / name) if linux else None for name in ("sys_vendor", "product_name")}
    container = _read(Path("/run/systemd/container")) if linux else None
    if linux and not container and Path("/.dockerenv").exists(): container = "docker-marker"
    virtualization = classify_environment(release, cpuinfo, linux=linux, dmi=dmi,
        hypervisor=_read(sys_root / "hypervisor/type") if linux else None, container=container)
    if sys.platform == 'darwin':
        virtualization.update(classification='macos', kind='unverified',
            evidence=['macOS execution; physical Apple hardware and virtualization are not authenticated'])
    kind = virtualization["kind"]
    topology, frequency = [], []
    for cpu in ((allowed or [])[:4096] if linux else []):
        root = sys_root / f"devices/system/cpu/cpu{cpu}"
        topology.append({"cpu": cpu, "package_id": _read(root / "topology/physical_package_id"),
                         "core_id": _read(root / "topology/core_id"),
                         "thread_siblings": _read(root / "topology/thread_siblings_list")})
        frequency.append({"cpu": cpu, "scaling_cur_freq_khz": _read(root / "cpufreq/scaling_cur_freq"),
                          "governor": _read(root / "cpufreq/scaling_governor")})
    if not any(row["scaling_cur_freq_khz"] is not None or row["governor"] is not None for row in frequency):
        frequency = None
    proc_mhz = [line.split(":", 1)[1].strip() for line in (cpuinfo or "").splitlines() if line.startswith("cpu MHz")]
    thermals = [{"zone": p.name, "type": _read(p / "type"), "temperature_millidegrees": _read(p / "temp")}
                for p in sorted((sys_root / "class/thermal").glob("thermal_zone*"))] if linux else []
    power = [{"device": p.name, "type": _read(p / "type"), "status": _read(p / "status"),
              "online": _read(p / "online"), "capacity_percent": _read(p / "capacity")}
             for p in sorted((sys_root / "class/power_supply").glob("*"))] if linux else []
    machine_id = _read(Path("/etc/machine-id")) if linux else None
    identity = {key: environment[key] for key in ("system", "release", "machine", "cpu", "cpu_count", "cpu_flags")}
    identity.update({"topology": topology, "virtualization": kind})
    hardware_fingerprint = _hash(identity)
    installation = _hash({"node": platform.node(), "machine_id": machine_id})
    restrictions = {"allowed_cpus": allowed, "scheduler_policy": None, "nice": None,
                    "resource_limits": None, "cgroup": None}
    if linux:
        try:
            restrictions["scheduler_policy"] = os.sched_getscheduler(0)
            restrictions["nice"] = os.getpriority(os.PRIO_PROCESS, 0)
            import resource
            restrictions["resource_limits"] = {name: list(resource.getrlimit(getattr(resource, name)))
                for name in ("RLIMIT_AS", "RLIMIT_CPU", "RLIMIT_NOFILE", "RLIMIT_NPROC") if hasattr(resource, name)}
        except OSError:
            pass
        restrictions["cgroup"] = {name: _read(sys_root / "fs/cgroup" / name)
                                   for name in ("cpu.max", "cpu.stat", "cpuset.cpus.effective", "memory.max")}
        restrictions["cgroup_membership"] = _read(proc_root / "self/cgroup")
        # Keep root-mount observations above for compatibility, and separately
        # inspect visible process paths. A cgroup namespace can hide ancestors.
        cgroup_root=sys_root/'fs/cgroup'
        groups=[]
        for line in (restrictions['cgroup_membership'] or '').splitlines():
            fields=line.split(':',2)
            if len(fields)!=3: continue
            controllers,relative=fields[1],fields[2].lstrip('/')
            bases=[cgroup_root] if not controllers else [cgroup_root/name for name in controllers.split(',')]
            for base in bases:
                location=base/relative
                if not location.resolve().is_relative_to(cgroup_root.resolve()):continue
                if not location.is_dir():continue
                names=('cpu.max','cpuset.cpus.effective','memory.max','cpu.weight','cpu.cfs_quota_us',
                       'cpu.cfs_period_us','cpu.shares','cpuset.cpus','memory.limit_in_bytes')
                groups.append({'controllers':controllers or 'unified','path':str(location),
                               'values':{name:_read(location/name) for name in names}})
        restrictions['cgroup_process_paths']=groups or None
        restrictions['cgroup_ancestry_caveat']='Visible mount and membership paths only; hidden ancestor constraints may be unavailable.'
        restrictions["process_status"] = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
            for line in (_read(proc_root / "self/status") or "").splitlines()
            if line.startswith(("Cpus_allowed_list:", "Mems_allowed_list:", "Seccomp:", "NoNewPrivs:"))}
    try:
        load = list(os.getloadavg())
    except (AttributeError, OSError):
        load = None
    return {"observed_at": datetime.now(timezone.utc).isoformat(),
            "host_fingerprint": _hash({"hardware": hardware_fingerprint, "installation": installation}),
            "hardware_fingerprint": hardware_fingerprint, "installation_id_hash": installation,
            "identity_scope": "current OS/guest installation and exposed hardware; not physical-host authentication",
            "virtualization": virtualization, "environment_classification": virtualization["classification"],
            "dmi_observations": dmi, "boot_id_hash": _hash(_read(proc_root / "sys/kernel/random/boot_id")) if linux and _read(proc_root / "sys/kernel/random/boot_id") else None,
            "topology": topology or None, "frequency_sysfs": frequency,
            "frequency_proc_mhz": proc_mhz or None,
            "frequency_caveat": "guest/container-visible observations; not verified physical frequency" if kind in {"wsl", "wsl2", "hypervisor-detected", "container-detected"} else None,
            "thermal": thermals or None, "power": power or None, "load_average": load,
            "turbo_controls_observed": {"intel_pstate_no_turbo": _read(sys_root / "devices/system/cpu/intel_pstate/no_turbo") if linux else None,
                                         "cpufreq_boost": _read(sys_root / "devices/system/cpu/cpufreq/boost") if linux else None},
            "restrictions": restrictions,
            "observation_sources": {"sysfs": str(sys_root) if linux else None, "procfs": str(proc_root) if linux else None,
                                     "cgroup_scope": "visible cgroup mount; membership recorded separately"},
            "unavailable": [name for name, value in (("sysfs frequency/governor", frequency), ("thermal", thermals), ("power", power)) if not value],
            "system_settings_modified": False}
