import os
import platform
from pathlib import Path
import sys

from .process import capabilities


def machine_environment() -> dict:
    cpu = platform.processor() or "unknown"
    cpu_flags = []
    if sys.platform.startswith("linux"):
        try:
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                elif line.startswith(("flags", "Features")):
                    cpu_flags = line.split(":", 1)[1].split()
        except OSError:
            pass
    return {
        "system": platform.system(), "release": platform.release(),
        "machine": platform.machine(), "cpu": cpu,
        "cpu_count": os.cpu_count(), "cpu_flags": sorted(cpu_flags),
        "python": platform.python_version(), "measurement": capabilities(),
    }
