import json
import subprocess
from pathlib import Path
from typing import Any


def _load_plan(plan_path: Path) -> dict[str, Any]:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def _list_tags(repo: str) -> set[str]:
    url = f"https://github.com/{repo}.git"
    result = subprocess.run(
        ["git", "ls-remote", "--tags", url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-remote failed")
    tags = set()
    for line in result.stdout.splitlines():
        if "\trefs/tags/" not in line:
            continue
        _, ref = line.split("\t", 1)
        name = ref.replace("refs/tags/", "")
        if name.endswith("^{}"):  # annotated tag
            name = name[:-3]
        tags.add(name)
    return tags


def check_gate_a_smoke(case: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    plan_path = case.get("plan_path")
    template_repos = case.get("template_repos", [])
    if not plan_path:
        return {
            "pass": False,
            "details": [{"type": "invalid_case", "message": "missing plan_path"}],
        }
    if not template_repos:
        return {
            "pass": False,
            "details": [{"type": "invalid_case", "message": "missing template_repos"}],
        }

    resolved_plan = Path(plan_path)
    if not resolved_plan.is_absolute():
        resolved_plan = (repo_root / resolved_plan).resolve()
    if not resolved_plan.is_file():
        return {
            "pass": False,
            "details": [{"type": "missing_plan", "path": str(resolved_plan)}],
        }

    plan = _load_plan(resolved_plan)
    version_tag = plan.get("aaa", {}).get("version_tag")
    if not version_tag:
        return {
            "pass": False,
            "details": [{"type": "missing_version_tag", "path": str(resolved_plan)}],
        }

    details: list[dict[str, Any]] = []
    for repo in template_repos:
        try:
            tags = _list_tags(repo)
        except RuntimeError as exc:
            details.append(
                {
                    "type": "tag_query_failed",
                    "repo": repo,
                    "message": str(exc),
                }
            )
            continue
        if version_tag not in tags:
            details.append(
                {
                    "type": "missing_template_tag",
                    "repo": repo,
                    "tag": version_tag,
                }
            )

    return {"pass": not details, "details": details}
