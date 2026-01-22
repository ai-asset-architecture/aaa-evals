import hashlib
import json
from pathlib import Path
from typing import Any


def _compute_checksum(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _load_runbook(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_runbook_checksums(config: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(config.get("repo_root", Path.cwd()))
    pattern = config.get("pattern", "runbooks/**/*.yaml")
    details: list[dict[str, Any]] = []

    for path in sorted(repo_root.glob(pattern)):
        if not path.is_file():
            continue
        try:
            payload = _load_runbook(path)
        except json.JSONDecodeError as exc:
            details.append(
                {
                    "type": "invalid_runbook_json",
                    "path": str(path),
                    "message": str(exc),
                }
            )
            continue

        metadata = payload.get("metadata", {})
        expected = metadata.get("checksum", "")
        if not expected:
            details.append(
                {
                    "type": "missing_checksum",
                    "path": str(path),
                }
            )
            continue

        computed_payload = dict(payload)
        computed_meta = dict(metadata)
        computed_meta["checksum"] = ""
        computed_payload["metadata"] = computed_meta
        actual = _compute_checksum(computed_payload)
        if actual != expected:
            details.append(
                {
                    "type": "checksum_mismatch",
                    "path": str(path),
                    "expected": expected,
                    "actual": actual,
                }
            )

    return {"pass": not details, "details": details}
