import json
from pathlib import Path
from typing import Any

REQUIRED_TYPES = {"all", "docs", "service", "frontend", "agent", "genai-service"}


def check_checks_manifest_alignment(config: dict[str, Any]) -> dict[str, Any]:
    manifest_path = Path(config.get("manifest_path", ""))
    if not manifest_path.exists():
        return {"pass": False, "details": ["checks.manifest.json missing"]}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"pass": False, "details": ["checks.manifest.json invalid JSON"]}

    missing_fields = []
    seen_types: set[str] = set()
    for item in payload.get("checks", []):
        if not all(key in item for key in ("id", "name", "applies_to")):
            missing_fields.append("missing fields in manifest item")
            continue
        applies = set(item.get("applies_to", []))
        seen_types.update(applies)

    missing_types = sorted(REQUIRED_TYPES - seen_types)
    details = []
    if missing_fields:
        details.extend(missing_fields)
    if missing_types:
        details.append(f"missing applies_to types: {', '.join(missing_types)}")
    return {"pass": not details, "details": details}
