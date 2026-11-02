"""Sample resident memory of our macOS process group using public libproc APIs.

This is a watchdog, not an allocation ceiling or a hostile-code sandbox. The ABI
is documented in Apple's xnu bsd/sys/proc_info.h (PROC_PIDTASKINFO). No Apple
implementation code is vendored here.
"""
import ctypes
import ctypes.util
import os
import sys

from .errors import AionError


class TaskInfo(ctypes.Structure):
    _fields_ = [('virtual_bytes', ctypes.c_uint64), ('resident_bytes', ctypes.c_uint64),
                ('times', ctypes.c_uint64 * 4), ('counters', ctypes.c_int32 * 12)]


class DarwinMemoryReader:
    def __init__(self):
        if sys.platform != 'darwin':
            raise AionError('libproc resident-memory monitoring requires macOS.')
        try:
            self.library = ctypes.CDLL(ctypes.util.find_library('proc') or '/usr/lib/libproc.dylib', use_errno=True)
            self.library.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
            self.library.proc_pidinfo.restype = ctypes.c_int
            self.library.proc_listpids.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int]
            self.library.proc_listpids.restype = ctypes.c_int
            if self.resident_bytes(os.getpid()) <= 0:
                raise OSError('no resident memory observation for the current process')
        except (OSError, AttributeError) as exc:
            raise AionError(f'macOS memory protection unavailable: libproc probe failed: {exc}') from exc

    def resident_bytes(self, pid):
        info = TaskInfo()
        size = ctypes.sizeof(info)
        returned = self.library.proc_pidinfo(pid, 4, 0, ctypes.byref(info), size)
        if returned != size:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return 0  # A process exiting between the two observations is normal.
            raise AionError('macOS memory protection lost a live process observation; execution refused.')
        return info.resident_bytes

    def group_resident_bytes(self, group):
        # Bound enumeration and fail closed if it cannot be observed completely.
        needed = self.library.proc_listpids(2, group, None, 0)
        if needed <= 0:
            raise AionError('macOS memory protection could not enumerate its process group.')
        capacity = max(64, needed // ctypes.sizeof(ctypes.c_int) + 32)
        for _ in range(3):
            if capacity > 65536:
                break
            pids = (ctypes.c_int * capacity)()
            returned = self.library.proc_listpids(2, group, pids, ctypes.sizeof(pids))
            if returned < 0 or returned % ctypes.sizeof(ctypes.c_int):
                break
            if returned < ctypes.sizeof(pids):
                # Include the Python supervisor: the explicit macOS policy caps
                # aggregate observed RSS in this invocation's isolated group.
                return sum(self.resident_bytes(pid) for pid in pids[:returned // ctypes.sizeof(ctypes.c_int)] if pid > 0)
            capacity *= 2
        raise AionError('macOS memory protection could not obtain a complete bounded process list.')
