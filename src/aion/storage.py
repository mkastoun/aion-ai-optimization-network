import json
from pathlib import Path
import re
import tempfile

from .errors import AionError


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AionError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise AionError(f"Unsupported or missing schema_version in {path}.")
    return data


def atomic_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
            json.dump(data, file, indent=2, allow_nan=False)
            file.write("\n")
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


class ResultStore:
    def __init__(self, root: Path):
        self.root = root

    def save(self, result: dict) -> Path:
        run_id = result["run_id"]
        if not re.fullmatch(r"[A-Za-z0-9-]+", run_id):
            raise AionError("Invalid experiment identifier.")
        path = self.root / "results" / f"{run_id}.json"
        atomic_json(path, result)
        atomic_json(self.root / "latest.json", {"schema_version": 1, "run_id": run_id})
        return path

    def latest(self) -> Path:
        data = read_json(self.root / "latest.json")
        run_id = data.get("run_id", "")
        if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9-]+", run_id):
            raise AionError("Invalid latest experiment identifier.")
        return self.root / "results" / f"{run_id}.json"
