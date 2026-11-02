"""Read-only replication preflight; no privileged tuning or timing claims."""
from .compiler import ClangAdapter
from .controls import parse_cpus
from .errors import AionError
from .evidence import evidence_header
from .optimization import BASELINE
from .profiling import probe_counters


def run_preflight(compiler="clang++", cpus="none", *, session=None, counters=False, require_native=False):
    controls=parse_cpus(cpus)
    result=evidence_header("preflight",controls=controls,session=session)
    classification=result["host_start"]["environment_classification"]
    result.update(ready_for_local_validation=False,native_linux_evidence_available=False,
                  native_environment_detected=classification=="native-linux",warnings=[],checks={})
    if classification!="native-linux": result["warnings"].append("This environment cannot supply native Linux performance evidence.")
    result["warnings"].append("Logical CPU affinity does not establish physical CPU isolation or exclusive ownership.")
    try:
        adapter=ClangAdapter(compiler)
        result["build_provenance"]=adapter.build_provenance()
        result["compiler"]=result["build_provenance"]["compiler"]
        result["checks"]["compiler"]=adapter.probe(BASELINE,controls=controls)
        result["ready_for_local_validation"]=result["checks"]["compiler"]["supported"]
        result["checks"]["counters"]=probe_counters(adapter,controls) if counters else {"available":None,"reason":"optional counter probe not requested"}
    except AionError as exc:
        result["checks"]["compiler"]={"supported":False,"reason":str(exc)}
    result["status"]="passed" if result["ready_for_local_validation"] and (not require_native or classification=="native-linux") else "failed"
    result["measurement_environment_validated"]=False
    result["note"]="A successful compile/affinity preflight is not a measurement-quality study or native performance validation."
    return result
