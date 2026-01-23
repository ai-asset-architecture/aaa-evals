import json
from pathlib import Path
from typing import Any


def check_repo_type_consistency(config: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(config.get("repo_root", "."))
    expected = (config.get("expected_repo_type") or "").strip()
    metadata = repo_root / ".aaa" / "metadata.json"
    if not metadata.exists():
        return {"pass": False, "details": [".aaa/metadata.json missing"]}
    try:
        payload = json.loads(metadata.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"pass": False, "details": [".aaa/metadata.json invalid JSON"]}
    repo_type = str(payload.get("repo_type", "")).strip()
    if not repo_type:
        return {"pass": False, "details": ["repo_type missing"]}
    if expected and repo_type != expected:
        return {"pass": False, "details": [f"repo_type mismatch: {repo_type} != {expected}"]}
    return {"pass": True, "details": []}
