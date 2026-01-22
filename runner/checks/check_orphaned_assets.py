from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any, Iterable

DEFAULT_EXCLUDES = [
    "**/README.md",
    "**/index.json",
    ".*",
    "**/.DS_Store",
    "**/.venv-aaa/**",
    "**/.aaa-tmp/**",
    "**/.worktrees/**",
    "**/aaa-evals/runner/tests/fixtures/**",
]
DEFAULT_TARGETS = ["**/docs/adrs", "**/docs/milestones", "**/reports"]


def _has_glob(value: str) -> bool:
    return any(char in value for char in ("*", "?", "["))


def _match_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _iter_target_dirs(root: Path, patterns: Iterable[str]) -> list[Path]:
    dirs: set[Path] = set()
    for pattern in patterns:
        if not pattern:
            continue
        candidate = Path(pattern)
        if candidate.is_absolute() and not _has_glob(pattern):
            if candidate.is_dir():
                dirs.add(candidate)
            continue
        for hit in root.glob(pattern):
            if hit.is_dir():
                dirs.add(hit)
    return sorted(dirs)


def _expected_paths(index_path: Path) -> set[str]:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    expected: set[str] = set()
    for entry in payload.get("files", []):
        rel = str(entry.get("path", "")).strip()
        if rel:
            expected.add(rel)
    return expected


def _actual_paths(directory: Path, file_pattern: str, excludes: list[str]) -> set[str]:
    actual: set[str] = set()
    for path in directory.rglob(file_pattern):
        rel = path.relative_to(directory).as_posix()
        if _match_any(rel, excludes) or _match_any(path.as_posix(), excludes):
            continue
        actual.add(rel)
    return actual


def check_orphaned_assets(config: dict[str, Any]) -> dict[str, Any]:
    root = Path(config.get("repo_root", Path.cwd()))
    targets = config.get("target_paths", DEFAULT_TARGETS)
    excludes = config.get("exclude_patterns", DEFAULT_EXCLUDES)
    file_pattern = config.get("file_pattern", "*.md")
    require_index = config.get("require_index", True)
    allow_empty = config.get("allow_empty", False)

    details: list[dict[str, Any]] = []
    target_dirs = _iter_target_dirs(root, targets)

    for directory in target_dirs:
        if _match_any(directory.as_posix(), excludes):
            continue
        index_path = directory / "index.json"
        if require_index and not index_path.exists():
            details.append(
                {
                    "type": "missing_index",
                    "path": str(index_path),
                    "suggested_fix": "Run `aaa run ops/reindex-all-assets` to update index.json",
                }
            )
            continue

        expected = _expected_paths(index_path) if index_path.exists() else set()
        actual = _actual_paths(directory, file_pattern, excludes)

        if not actual and not expected and allow_empty:
            continue

        for orphan in sorted(actual - expected):
            details.append(
                {
                    "type": "orphaned_asset",
                    "path": str(directory / orphan),
                    "suggested_fix": "Run `aaa run ops/reindex-all-assets` to update index.json",
                }
            )

    return {"pass": not details, "details": details}
