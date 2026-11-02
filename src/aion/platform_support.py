"""Explicit OS capabilities, separate from measurement-quality readiness."""
import os
import sys


def platform_capabilities():
    linux = sys.platform.startswith('linux')
    darwin = sys.platform == 'darwin'
    posix = os.name == 'posix' and all(hasattr(os, name) for name in ('fork', 'wait4', 'killpg'))
    memory = {'available': False, 'reason': 'macOS libproc watchdog is not applicable'}
    if darwin:
        from .darwin_memory import DarwinMemoryReader
        from .errors import AionError
        try:
            DarwinMemoryReader()
            memory = {'available': True, 'reason': 'sampled aggregate process-group RSS; not an allocation ceiling'}
        except AionError as exc:
            memory = {'available': False, 'reason': str(exc)}
    return {
        'os': 'macos' if darwin else 'linux' if linux else 'windows' if sys.platform == 'win32' else 'unsupported',
        'posix_supervisor': posix,
        'cpu_affinity': {'available': linux and all(hasattr(os, n) for n in ('sched_setaffinity', 'sched_getaffinity')),
                         'reason': None if linux else 'Linux CPU affinity APIs are unavailable; no core pinning is claimed'},
        'hardware_counters': {'available': False, 'requires_probe': linux,
                              'reason': 'Linux perf_event_open permission/support needs a real probe' if linux else 'Linux perf_event_open is unsupported on this OS'},
        'linux_host_metadata': linux,
        'address_space_limit': linux and posix,
        'resident_memory_watchdog': memory,
        'cpu_time_limit': posix,
        'peak_rss': posix,
        'measurement_environment_validated': False,
    }
