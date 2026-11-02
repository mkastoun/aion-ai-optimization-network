"""Common headers for separate diagnostic evidence, not promotion samples."""
from datetime import datetime, timezone
import uuid
from dataclasses import asdict

from . import __version__
from .host import collect_host_diagnostics
from .sessions import new_session


def evidence_header(kind: str, *, adapter=None, controls=None, session=None) -> dict:
    host = collect_host_diagnostics()
    return {"schema_version": 1, "aion_version": __version__, "evidence_kind": kind,
            "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+"-"+uuid.uuid4().hex[:10],
            "created_at": datetime.now(timezone.utc).isoformat(), "status": "completed",
            "host_start": host, "session": session or new_session(host, kind),
            "execution_controls": controls.to_dict() if controls else None,
            "compiler": asdict(adapter.info) if adapter else None,
            "build_provenance": adapter.build_provenance() if adapter else None,
            "promotion_eligible": False}
