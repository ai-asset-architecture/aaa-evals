import base64
import json
import subprocess
from datetime import datetime
from pathlib import Path


ORG = "ai-asset-architecture"
REQUIRED_README_SECTIONS = [
    "## Purpose / Scope",
    "## Ownership / CODEOWNERS",
    "## Versioning / Release",
    "## How to Consume / Use",
    "## Contribution / Promotion Rules",
]
REQUIRED_CHECKS = {"lint", "test", "eval"}
WORKFLOW_REQUIRED_REPOS = {"aaa-tpl-docs", "aaa-tpl-service", "aaa-tpl-frontend"}


def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def gh_api(path):
    code, out, err = run(["gh", "api", path])
    if code != 0:
        return None, err
    return json.loads(out), None


def gh_api_jq(path, jq):
    code, out, err = run(["gh", "api", path, "--jq", jq])
    if code != 0:
        return None, err
    return out, None


def get_readme(repo):
    content_b64, err = gh_api_jq(f"repos/{ORG}/{repo}/readme", ".content")
    if err or content_b64 is None:
        return None
    return base64.b64decode(content_b64).decode("utf-8", errors="replace")


def get_file(repo, path):
    content_b64, err = gh_api_jq(f"repos/{ORG}/{repo}/contents/{path}", ".content")
    if err or content_b64 is None:
        return None
    return base64.b64decode(content_b64).decode("utf-8", errors="replace")


def list_dir(repo, path):
    data, err = gh_api(f"repos/{ORG}/{repo}/contents/{path}")
    if err or data is None:
        return None
    if isinstance(data, list):
        return data
    return None


def check_readme_sections(readme_text):
    if readme_text is None:
        return ["README.md missing"]
    return [s for s in REQUIRED_README_SECTIONS if s not in readme_text]


def check_codeowners(repo):
    if get_file(repo, "CODEOWNERS"):
        return True
    if get_file(repo, ".github/CODEOWNERS"):
        return True
    return False


def check_workflow_pins(repo):
    if repo == ".github":
        return "skip", []
    if repo not in WORKFLOW_REQUIRED_REPOS:
        return "n/a", []
    workflows = list_dir(repo, ".github/workflows")
    if workflows is None:
        return "missing", [".github/workflows missing"]
    missing = []
    for item in workflows:
        if item.get("type") != "file":
            continue
        name = item.get("name", "")
        if not name.endswith((".yml", ".yaml")):
            continue
        content = get_file(repo, f".github/workflows/{name}")
        if content is None:
            missing.append(name)
            continue
        if "ai-asset-architecture/aaa-actions/.github/workflows/" not in content:
            missing.append(name)
            continue
        if "@v" not in content:
            missing.append(name)
    return "ok" if not missing else "missing", missing


def check_branch_protection(repo, default_branch):
    data, err = gh_api(f"repos/{ORG}/{repo}/branches/{default_branch}/protection")
    if err or data is None:
        blocked = "Upgrade to GitHub Pro" in (err or "")
        return {"ok": False, "error": err or "not available", "blocked_plan": blocked}
    checks = set((data.get("required_status_checks") or {}).get("contexts") or [])
    pr_reviews = data.get("required_pull_request_reviews") or {}
    dismiss = pr_reviews.get("dismiss_stale_reviews")
    approvals = pr_reviews.get("required_approving_review_count")
    force_push = (data.get("allow_force_pushes") or {}).get("enabled")
    linear = (data.get("required_linear_history") or {}).get("enabled")
    ok = REQUIRED_CHECKS.issubset(checks) and approvals == 1 and dismiss is True and force_push is False
    return {
        "ok": ok,
        "checks": sorted(checks),
        "approvals": approvals,
        "dismiss_stale": dismiss,
        "force_push": force_push,
        "linear_history": linear,
        "blocked_plan": False,
    }


def check_tags():
    tags, err = gh_api(f"repos/{ORG}/aaa-actions/tags")
    if err or tags is None:
        return False
    return any(tag.get("name") == "v0.1.0" for tag in tags)


def main():
    repos_data, err = gh_api(f"orgs/{ORG}/repos?per_page=200")
    if err or repos_data is None:
        raise SystemExit(f"failed to list repos: {err}")

    repos = sorted([r["name"] for r in repos_data])
    results = {}
    for repo in repos:
        default_branch = next((r["default_branch"] for r in repos_data if r["name"] == repo), "main")
        readme_text = get_readme(repo)
        readme_missing = check_readme_sections(readme_text)
        codeowners_ok = check_codeowners(repo)
        workflow_status, workflow_missing = check_workflow_pins(repo)
        protection = check_branch_protection(repo, default_branch)
        results[repo] = {
            "readme_missing": readme_missing,
            "codeowners": codeowners_ok,
            "workflow_status": workflow_status,
            "workflow_unpinned": workflow_missing,
            "branch_protection": protection,
        }

    report = []
    report.append("# GitHub AAA v0.1 Audit Report")
    report.append("")
    report.append(f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"- Org: {ORG}")
    report.append("")
    report.append("## Summary")
    report.append(f"- aaa-actions tag v0.1.0: {'OK' if check_tags() else 'MISSING'}")
    report.append(f"- Workflow required repos: {', '.join(sorted(WORKFLOW_REQUIRED_REPOS))}")
    report.append("")

    issues = []
    for repo, data in results.items():
        if data["readme_missing"]:
            issues.append(f"- {repo}: README missing sections -> {', '.join(data['readme_missing'])}")
        if not data["codeowners"]:
            issues.append(f"- {repo}: CODEOWNERS missing")
        if data["workflow_status"] == "missing":
            issues.append(f"- {repo}: workflows missing/ unpinned -> {', '.join(data['workflow_unpinned'])}")
        bp = data["branch_protection"]
        if not bp.get("ok"):
            if bp.get("blocked_plan"):
                issues.append(f"- {repo}: branch protection blocked by plan (private repo + no Pro)")
            else:
                issues.append(f"- {repo}: branch protection not compliant ({bp})")

    report.append("## Issues")
    report.extend(issues if issues else ["- None"])
    report.append("")

    report.append("## Per-Repo Checks")
    for repo, data in results.items():
        report.append(f"### {repo}")
        report.append(f"- README: {'OK' if not data['readme_missing'] else 'Missing sections'}")
        if data["readme_missing"]:
            report.append(f"  - Missing: {', '.join(data['readme_missing'])}")
        report.append(f"- CODEOWNERS: {'OK' if data['codeowners'] else 'Missing'}")
        wf_status = data["workflow_status"]
        if wf_status == "skip":
            report.append("- Workflows: Skip (.github repo)")
        elif wf_status == "n/a":
            report.append("- Workflows: N/A (not required in v0.1)")
        elif data["workflow_unpinned"]:
            report.append(f"- Workflows: Missing/Unpinned -> {', '.join(data['workflow_unpinned'])}")
        else:
            report.append("- Workflows: OK")
        bp = data["branch_protection"]
        if bp.get("blocked_plan"):
            report.append("- Branch protection: Blocked by plan (private repo + no Pro)")
        else:
            report.append(f"- Branch protection: {'OK' if bp.get('ok') else 'Not OK'}")
            if bp.get("ok") is False:
                report.append(f"  - Details: {bp}")
        report.append("")

    report_text = "\n".join(report)
    out_dir = Path("/Users/imac/Documents/Code/AI-Lotto/AAA_WORKSPACE/aaa-tpl-docs/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("github_audit_report_%Y%m%d_%H%M.md")
    (out_dir / name).write_text(report_text, encoding="utf-8")
    print(str(out_dir / name))


if __name__ == "__main__":
    main()
