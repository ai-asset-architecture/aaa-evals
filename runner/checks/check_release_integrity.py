import subprocess
from pathlib import Path
from typing import Any


def _resolve_script(repo_path: str, script_path: str) -> Path | None:
    if script_path:
        candidate = Path(script_path)
        return candidate if candidate.is_file() else None
    root = Path(repo_path)
    candidates = [
        root / "aaa-tools" / "scripts" / "release-verify.sh",
        root / "scripts" / "release-verify.sh",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def check_release_integrity(repo_path: str, tag: str, script_path: str = "") -> tuple[bool, list[str]]:
    if not tag:
        return False, ["release tag missing"]

    script = _resolve_script(repo_path, script_path)
    if script is None:
        return False, ["release verify script missing"]

    result = subprocess.run(
        ["bash", str(script), tag],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = _format_failure_detail(result)
        return False, [detail]

    return True, []


def _format_failure_detail(result: Any) -> str:
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    combined = "\n".join(item for item in [stdout, stderr] if item)
    if not combined:
        combined = "release verify failed"
    return f"release verify failed: {combined}"
