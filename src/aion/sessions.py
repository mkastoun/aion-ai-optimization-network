"""Explicit observation sessions. Session IDs do not establish statistical independence."""
from datetime import datetime, timezone
from pathlib import Path
import uuid

from .errors import AionError
from .host import collect_host_diagnostics
from .storage import atomic_json, read_json


def new_session(host: dict | None = None, label: str = "local invocation") -> dict:
    if not isinstance(label, str) or not 1 <= len(label) <= 120:
        raise AionError("Session label must contain 1..120 characters.")
    host = host or collect_host_diagnostics()
    return {"schema_version": 1, "evidence_kind": "session", "session_id": uuid.uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat(), "label": label,
            "host_fingerprint": host["host_fingerprint"], "boot_id_hash": host.get("boot_id_hash"),
            "environment_classification": host.get("environment_classification", "unavailable"),
            "note": "An explicitly delimited observation session; separate IDs alone do not prove independent host conditions."}


def load_session(path: Path, host: dict | None = None) -> dict:
    data = read_json(path)
    host = host or collect_host_diagnostics()
    if data.get("evidence_kind") != "session" or not isinstance(data.get("session_id"), str) or not data["session_id"]:
        raise AionError("Invalid session record.")
    if data.get("host_fingerprint") != host.get("host_fingerprint"):
        raise AionError("Session host identity differs from the current environment; create a new session.")
    if data.get("boot_id_hash") != host.get("boot_id_hash"):
        raise AionError("Session boot identity differs; create a new observation session after reboot.")
    return data


def save_session(path: Path, session: dict):
    if path.exists():
        raise AionError("Session file already exists; choose a new file to preserve previous sessions.")
    atomic_json(path, session)
