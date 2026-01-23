import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from runner.checks.check_agent_safety import check_agent_safety as check_agent_safety_impl
    from runner.checks.check_gate_a_smoke import check_gate_a_smoke as check_gate_a_smoke_impl
    from runner.checks.check_orphaned_assets import check_orphaned_assets as check_orphaned_assets_impl
    from runner.checks.check_runbook_checksums import check_runbook_checksums as check_runbook_checksums_impl
except ModuleNotFoundError:  # pragma: no cover - allow script execution
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from runner.checks.check_agent_safety import check_agent_safety as check_agent_safety_impl
    from runner.checks.check_gate_a_smoke import check_gate_a_smoke as check_gate_a_smoke_impl
    from runner.checks.check_orphaned_assets import check_orphaned_assets as check_orphaned_assets_impl
    from runner.checks.check_runbook_checksums import check_runbook_checksums as check_runbook_checksums_impl

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - optional runtime dependency
    Draft202012Validator = None


REQUIRED_SECTIONS = [
    "## Purpose / Scope",
    "## Ownership / CODEOWNERS",
    "## Versioning / Release",
    "## How to Consume / Use",
    "## Contribution / Promotion Rules",
]


def read_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def check_readme(repo_path):
    readme_path = os.path.join(repo_path, "README.md")
    if not os.path.isfile(readme_path):
        return False, ["README.md missing"]

    content = read_file(readme_path)
    missing = [section for section in REQUIRED_SECTIONS if section not in content]

    codeowners_root = os.path.join(repo_path, "CODEOWNERS")
    codeowners_dot = os.path.join(repo_path, ".github", "CODEOWNERS")
    if not (os.path.isfile(codeowners_root) or os.path.isfile(codeowners_dot)):
        missing.append("CODEOWNERS missing")

    return len(missing) == 0, missing


def _find_missing(content, required):
    return [item for item in required if item not in content]


def check_member_bootstrap_prereq(repo_path, sop_path):
    sop_file = os.path.join(repo_path, sop_path)
    if not os.path.isfile(sop_file):
        return False, [f"{sop_path} missing"]

    content = read_file(sop_file)
    required = [
        "gh auth setup-git",
        "pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@",
        "aaa init validate-plan",
        "模式 A",
        "模式 B",
    ]
    missing = _find_missing(content, required)
    return len(missing) == 0, missing


def check_private_download_sanity(repo_path, sop_path):
    sop_file = os.path.join(repo_path, sop_path)
    if not os.path.isfile(sop_file):
        return False, [f"{sop_path} missing"]

    content = read_file(sop_file)
    required = [
        "gh api -H \"Accept: application/vnd.github.v3.raw\"",
        "/tmp/aaa_plan_resolved.json",
        "/tmp/aaa_plan_schema.json",
        "json.load",
        "grep -n \"{{\"",
    ]
    missing = _find_missing(content, required)
    return len(missing) == 0, missing


DOC_DRIFT_FILES = [
    ".github/profile/README.md",
    "aaa-tpl-docs/docs/new-project-sop.md",
    "aaa-tpl-docs/PROJECT_PLAYBOOK.md",
]

VERSION_RE = re.compile(r"@v\d+\.\d+\.\d+")
PLAN_REF_RE = re.compile(r"plan\.v0\.1\.json\?ref=(v\d+\.\d+\.\d+)")
SCHEMA_REF_RE = re.compile(r"plan\.schema\.json\?ref=(v\d+\.\d+\.\d+)")


def _extract_versions(text):
    versions = set(VERSION_RE.findall(text))
    plan_refs = set(PLAN_REF_RE.findall(text))
    schema_refs = set(SCHEMA_REF_RE.findall(text))
    return versions, plan_refs, schema_refs


def check_onboarding_doc_drift(repo_path):
    missing = []
    versions = set()
    plan_refs = set()
    schema_refs = set()

    for rel_path in DOC_DRIFT_FILES:
        abs_path = Path(repo_path) / rel_path
        if not abs_path.is_file():
            missing.append(f"missing: {rel_path}")
            continue
        content = abs_path.read_text(encoding="utf-8")

        if "{{AAA_VERSION}}" in content or "@<tag>" in content:
            content = content.replace("{{AAA_VERSION}}", "").replace("@<tag>", "")

        v, p, s = _extract_versions(content)
        versions.update(v)
        plan_refs.update(p)
        schema_refs.update(s)

    if missing:
        return False, missing

    if len({v.replace("@", "") for v in versions}) > 1:
        return False, [f"version mismatch: {sorted(versions)}"]

    if len(plan_refs) > 1:
        return False, [f"plan ref mismatch: {sorted(plan_refs)}"]

    if len(schema_refs) > 1:
        return False, [f"schema ref mismatch: {sorted(schema_refs)}"]

    return True, []


COMMAND_REQUIRED = [
    "gh auth setup-git",
    "python3 -m pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@",
    "plan.v0.1.json?ref=",
]


def check_onboarding_command_integrity(repo_path):
    profile_path = Path(repo_path) / ".github/profile/README.md"
    sop_path = Path(repo_path) / "aaa-tpl-docs/docs/new-project-sop.md"

    if not profile_path.is_file():
        return False, [".github/profile/README.md missing"]
    if not sop_path.is_file():
        return False, ["aaa-tpl-docs/docs/new-project-sop.md missing"]

    profile = profile_path.read_text(encoding="utf-8")
    sop = sop_path.read_text(encoding="utf-8")

    missing = []
    for required in COMMAND_REQUIRED:
        if required not in profile:
            missing.append(f"profile missing: {required}")
        if required not in sop:
            missing.append(f"sop missing: {required}")

    profile_versions = VERSION_RE.findall(profile)
    sop_versions = VERSION_RE.findall(sop)
    profile_plan_refs = PLAN_REF_RE.findall(profile)
    sop_plan_refs = PLAN_REF_RE.findall(sop)

    if profile_versions != sop_versions:
        missing.append(f"version mismatch: profile={profile_versions} sop={sop_versions}")
    if profile_plan_refs != sop_plan_refs:
        missing.append(f"plan ref mismatch: profile={profile_plan_refs} sop={sop_plan_refs}")

    return len(missing) == 0, missing


def check_plan_schema_ref_sync(repo_path):
    sop_path = Path(repo_path) / "aaa-tpl-docs/docs/new-project-sop.md"
    if not sop_path.is_file():
        return False, ["aaa-tpl-docs/docs/new-project-sop.md missing"]

    content = sop_path.read_text(encoding="utf-8")
    plan_refs = PLAN_REF_RE.findall(content)
    schema_refs = SCHEMA_REF_RE.findall(content)

    if not plan_refs or not schema_refs:
        return False, ["plan/schema ref missing"]

    if set(plan_refs) != set(schema_refs):
        return False, [f"plan/schema ref mismatch: plan={plan_refs} schema={schema_refs}"]

    return True, []


def check_cli_contract_sync(repo_path):
    missing = []
    profile_path = Path(repo_path) / ".github/profile/README.md"
    sop_path = Path(repo_path) / "aaa-tpl-docs/docs/new-project-sop.md"
    user_contract_path = Path(repo_path) / "aaa-tpl-docs/docs/contracts/aaa-cli-contract.md"
    cli_contract_path = Path(repo_path) / "aaa-tools/specs/CLI_CONTRACT.md"
    runbook_path = Path(repo_path) / "aaa-tools/runbooks/init/AGENT_BOOTSTRAP.md"

    required_files = [
        (profile_path, ".github/profile/README.md"),
        (sop_path, "aaa-tpl-docs/docs/new-project-sop.md"),
        (user_contract_path, "aaa-tpl-docs/docs/contracts/aaa-cli-contract.md"),
        (cli_contract_path, "aaa-tools/specs/CLI_CONTRACT.md"),
        (runbook_path, "aaa-tools/runbooks/init/AGENT_BOOTSTRAP.md"),
    ]
    for path, label in required_files:
        if not path.is_file():
            missing.append(f"{label} missing")
    if missing:
        return False, missing

    profile = profile_path.read_text(encoding="utf-8")
    sop = sop_path.read_text(encoding="utf-8")
    user_contract = user_contract_path.read_text(encoding="utf-8")
    cli_contract = cli_contract_path.read_text(encoding="utf-8")

    required_common = [
        "gh auth setup-git",
        "python3 -m pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@",
        "plan.v0.1.json?ref=",
    ]
    for required in required_common:
        if required not in profile:
            missing.append(f"profile missing: {required}")
        if required not in sop:
            missing.append(f"sop missing: {required}")

    required_contract_steps = [
        "aaa init validate-plan",
        "aaa init repo-checks",
        "plan.schema.json?ref=",
        "aaa-tools/runbooks/init/AGENT_BOOTSTRAP.md",
    ]
    for required in required_contract_steps:
        if required not in sop:
            missing.append(f"sop missing: {required}")
        if required not in user_contract:
            missing.append(f"user contract missing: {required}")

    if "post-init audit" not in cli_contract:
        missing.append("cli contract missing: post-init audit requirement")

    versions = set()
    for label, content in [("profile", profile), ("sop", sop), ("user contract", user_contract)]:
        matches = VERSION_RE.findall(content)
        if not matches:
            missing.append(f"{label} missing version tag")
            continue
        versions.update(matches)
    if len({v.replace("@", "") for v in versions}) > 1:
        missing.append(f"version mismatch: {sorted(versions)}")

    sop_plan_refs = PLAN_REF_RE.findall(sop)
    sop_schema_refs = SCHEMA_REF_RE.findall(sop)
    contract_plan_refs = PLAN_REF_RE.findall(user_contract)
    contract_schema_refs = SCHEMA_REF_RE.findall(user_contract)

    if not sop_plan_refs or not sop_schema_refs:
        missing.append("sop missing plan/schema refs")
    if not contract_plan_refs or not contract_schema_refs:
        missing.append("user contract missing plan/schema refs")
    if set(sop_plan_refs) != set(sop_schema_refs):
        missing.append(f"sop plan/schema ref mismatch: plan={sop_plan_refs} schema={sop_schema_refs}")
    if set(contract_plan_refs) != set(contract_schema_refs):
        missing.append(
            f"user contract plan/schema ref mismatch: plan={contract_plan_refs} schema={contract_schema_refs}"
        )
    if set(sop_plan_refs) != set(contract_plan_refs):
        missing.append(
            f"plan ref mismatch: sop={sop_plan_refs} user_contract={contract_plan_refs}"
        )
    if set(sop_schema_refs) != set(contract_schema_refs):
        missing.append(
            f"schema ref mismatch: sop={sop_schema_refs} user_contract={contract_schema_refs}"
        )

    return len(missing) == 0, missing


def check_post_init_audit_required(repo_path):
    missing = []
    sop_path = Path(repo_path) / "aaa-tpl-docs/docs/new-project-sop.md"
    user_contract_path = Path(repo_path) / "aaa-tpl-docs/docs/contracts/aaa-cli-contract.md"
    runbook_path = Path(repo_path) / "aaa-tools/runbooks/init/POST_INIT_AUDIT.md"


def check_runbook_schema_validate(repo_path):
    schema_path = Path(repo_path) / "aaa-tools/specs/runbook.schema.json"
    runbooks_root = Path(repo_path) / "aaa-tools/runbooks"

    if not schema_path.is_file():
        return False, ["aaa-tools/specs/runbook.schema.json missing"]
    if not runbooks_root.is_dir():
        return False, ["aaa-tools/runbooks missing"]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"schema invalid JSON: {exc}"]

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return False, ["jsonschema not available"]

    validator = Draft202012Validator(schema)
    failures = []
    for path in runbooks_root.rglob("*.yaml"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{path.relative_to(Path(repo_path))}: invalid JSON: {exc}")
            continue
        errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
        if errors:
            detail = "; ".join(err.message for err in errors)
            failures.append(f"{path.relative_to(Path(repo_path))}: {detail}")

    return len(failures) == 0, failures


def check_orphaned_assets(repo_path):
    config = {
        "repo_root": repo_path,
        "target_paths": ["**/docs/adrs", "**/docs/milestones", "**/reports"],
        "exclude_patterns": [
            "**/README.md",
            "**/index.json",
            ".*",
            "**/.DS_Store",
            "**/.venv-aaa/**",
            "**/.aaa-tmp/**",
            "**/.worktrees/**",
            "**/aaa-evals/runner/tests/fixtures/**",
        ],
        "file_pattern": "*.md",
        "require_index": True,
    }
    result = check_orphaned_assets_impl(config)
    return result["pass"], result["details"]


def check_runbook_checksums(repo_path):
    config = {"repo_root": repo_path, "pattern": "runbooks/**/*.yaml"}
    result = check_runbook_checksums_impl(config)
    return result["pass"], result["details"]


def check_gate_a_smoke(repo_path):
    repo_root = Path(repo_path)
    cases_path = repo_root / "evals" / "cases" / "gate_a_smoke.jsonl"
    if not cases_path.is_file():
        nested = repo_root / "aaa-evals" / "evals" / "cases" / "gate_a_smoke.jsonl"
        if nested.is_file():
            cases_path = nested
            repo_root = repo_root / "aaa-evals"
        else:
            return False, ["gate_a_smoke cases missing"]

    failures = []
    with cases_path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"case {idx}: invalid JSON: {exc}")
                continue
            result = check_gate_a_smoke_impl(case, repo_root)
            if not result.get("pass"):
                failures.append({"case": case.get("id", f"line-{idx}"), "details": result.get("details")})

    return len(failures) == 0, failures


def check_agent_safety(repo_path):
    repo_root = Path(repo_path)
    cases_path = repo_root / "evals" / "cases" / "agent_safety.jsonl"
    if not cases_path.is_file():
        nested = repo_root / "aaa-evals" / "evals" / "cases" / "agent_safety.jsonl"
        if nested.is_file():
            cases_path = nested
            repo_root = repo_root / "aaa-evals"
        else:
            worktrees_root = repo_root / "aaa-evals" / ".worktrees"
            if worktrees_root.is_dir():
                for candidate in worktrees_root.glob("*/evals/cases/agent_safety.jsonl"):
                    cases_path = candidate
                    repo_root = candidate.parents[2]
                    break
            if not cases_path.is_file():
                return False, ["agent safety cases missing"]

    failures = []
    with cases_path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"case {idx}: invalid JSON: {exc}")
                continue
            result = check_agent_safety_impl(case, repo_root)
            if not result.get("pass"):
                failures.append({"case": case.get("id", f"line-{idx}"), "details": result.get("details")})

    return len(failures) == 0, failures


    required_files = [
        (sop_path, "aaa-tpl-docs/docs/new-project-sop.md"),
        (user_contract_path, "aaa-tpl-docs/docs/contracts/aaa-cli-contract.md"),
        (runbook_path, "aaa-tools/runbooks/init/POST_INIT_AUDIT.md"),
    ]
    for path, label in required_files:
        if not path.is_file():
            missing.append(f"{label} missing")
    if missing:
        return False, missing

    sop = sop_path.read_text(encoding="utf-8")
    user_contract = user_contract_path.read_text(encoding="utf-8")
    runbook = runbook_path.read_text(encoding="utf-8")

    required_doc_refs = [
        "aaa init repo-checks",
        "aaa-tools/runbooks/init/POST_INIT_AUDIT.md",
    ]
    for required in required_doc_refs:
        if required not in sop:
            missing.append(f"sop missing: {required}")
        if required not in user_contract:
            missing.append(f"user contract missing: {required}")

    required_runbook = [
        "aaa init repo-checks",
        "--suite governance",
    ]
    for required in required_runbook:
        if required not in runbook:
            missing.append(f"runbook missing: {required}")

    return len(missing) == 0, missing


def check_start_here_sync(repo_path, profile_path):
    profile_file = os.path.join(repo_path, profile_path)
    if not os.path.isfile(profile_file):
        return False, [f"{profile_path} missing"]

    content = read_file(profile_file)
    required = [
        "gh auth setup-git",
        "gh api -H \"Accept: application/vnd.github.v3.raw\"",
        "pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@",
        "aaa-tpl-docs/blob/main/docs/new-project-sop.md",
    ]
    missing = _find_missing(content, required)
    return len(missing) == 0, missing


def check_workflows(repo_path):
    workflows_dir = os.path.join(repo_path, ".github", "workflows")
    if not os.path.isdir(workflows_dir):
        return True, ["no workflows to check"]

    if os.path.basename(repo_path) == "aaa-actions":
        return True, ["skip aaa-actions self-check"]

    yaml_files = [
        os.path.join(workflows_dir, name)
        for name in os.listdir(workflows_dir)
        if name.endswith((".yml", ".yaml"))
    ]
    if not yaml_files:
        return True, ["no workflow files found"]

    missing = []
    uses_pattern = re.compile(r"uses:\s*ai-asset-architecture/aaa-actions/.github/workflows/[^@\s]+@v")
    for workflow in yaml_files:
        content = read_file(workflow)
        if not uses_pattern.search(content):
            missing.append(os.path.relpath(workflow, repo_path))

    return len(missing) == 0, missing


def _load_repo_type(repo_path: str) -> str:
    index_path = Path(repo_path) / "index.json"
    if not index_path.is_file():
        return ""
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    repo_type = str(payload.get("repo_type", "")).strip()
    return repo_type


def should_require_agent_assets(repo_type: str) -> bool:
    return repo_type in {"agent", "genai-service"}


def is_agent_repo(repo_path):
    repo_type = _load_repo_type(repo_path)
    if repo_type:
        return should_require_agent_assets(repo_type)
    markers = ["agent.yaml", "agent.py"]
    return any(os.path.isfile(os.path.join(repo_path, marker)) for marker in markers)


def check_skills(repo_path, skills_root):
    if not is_agent_repo(repo_path):
        return True, ["skipped: non-agent repo"]

    root = os.path.join(repo_path, skills_root)
    if not os.path.isdir(root):
        return False, [f"{skills_root} missing"]

    buckets = ["common", "codex", "agent"]
    missing = []
    for bucket in buckets:
        bucket_path = os.path.join(root, bucket)
        if not os.path.isdir(bucket_path):
            missing.append(f"{skills_root}/{bucket} missing")
            continue
        for skill in os.listdir(bucket_path):
            skill_path = os.path.join(bucket_path, skill)
            if not os.path.isdir(skill_path):
                continue
            if skill.startswith("."):
                continue
            if not os.path.isfile(os.path.join(skill_path, "SKILL.md")):
                missing.append(f"{skills_root}/{bucket}/{skill}/SKILL.md missing")

    return len(missing) == 0, missing


def check_skill_structure_v2(repo_path, skills_root):
    root = os.path.join(repo_path, skills_root)
    if not os.path.isdir(root):
        return False, [f"{skills_root} missing"]

    required_sections = [
        "## Routing Logic",
        "## Execution Steps",
        "## Fallback",
        "## Inputs / Outputs",
        "## Execution Test",
        "## Limitations",
    ]
    missing = []
    bucket = "common"
    bucket_path = os.path.join(root, bucket)
    if os.path.isdir(bucket_path):
        for skill in os.listdir(bucket_path):
            if skill.startswith(".") or not skill.startswith("aaa-"):
                continue
            skill_path = os.path.join(bucket_path, skill, "SKILL.md")
            if not os.path.isfile(skill_path):
                continue
            content = read_file(skill_path)
            absent = [section for section in required_sections if section not in content]
            if absent:
                missing.append(f"{skills_root}/{bucket}/{skill}: missing {', '.join(absent)}")

    return len(missing) == 0, missing


def load_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fallback_validate_prompt(schema, prompt_obj):
    required = schema.get("required", [])
    props = schema.get("properties", {})
    missing = [key for key in required if key not in prompt_obj]
    if missing:
        return False, [f"missing required fields: {', '.join(missing)}"]

    for key, spec in props.items():
        if key not in prompt_obj:
            continue
        expected_type = spec.get("type")
        if expected_type == "string" and not isinstance(prompt_obj[key], str):
            return False, [f"{key} must be string"]
        if expected_type == "object" and not isinstance(prompt_obj[key], dict):
            return False, [f"{key} must be object"]

    return True, []


def check_prompt_schema(repo_path, schema_path, prompts_dir):
    if not is_agent_repo(repo_path):
        return True, ["skipped: non-agent repo"]

    schema_file = os.path.join(repo_path, schema_path)
    if not os.path.isfile(schema_file):
        return False, [f"{schema_path} missing"]

    prompts_root = os.path.join(repo_path, prompts_dir)
    if not os.path.isdir(prompts_root):
        return False, [f"{prompts_dir} missing"]

    schema = load_schema(schema_file)
    validator = Draft202012Validator(schema) if Draft202012Validator else None
    failures = []
    for root, _dirs, files in os.walk(prompts_root):
        for name in files:
            if not name.endswith(".json"):
                continue
            path = os.path.join(root, name)
            try:
                payload = json.loads(read_file(path))
            except json.JSONDecodeError as exc:
                failures.append(f"{os.path.relpath(path, repo_path)} invalid JSON: {exc}")
                continue
            if validator is None:
                ok, issues = fallback_validate_prompt(schema, payload)
                if not ok:
                    failures.append(f"{os.path.relpath(path, repo_path)}: {', '.join(issues)}")
                continue
            errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
            if errors:
                detail = "; ".join(err.message for err in errors)
                failures.append(f"{os.path.relpath(path, repo_path)}: {detail}")

    return len(failures) == 0, failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        required=True,
        choices=[
            "readme",
            "workflow",
            "skills",
            "prompt",
            "member_bootstrap_prereq",
            "private_download_sanity",
            "start_here_sync",
            "skill_structure_v2",
            "onboarding_doc_drift",
            "onboarding_command_integrity",
            "plan_schema_ref_sync",
            "cli_contract_sync",
            "post_init_audit_required",
            "runbook_schema_validate",
            "runbook_checksums",
            "orphaned_assets",
            "gate_a_smoke",
            "agent_safety",
        ],
    )
    parser.add_argument("--repo", required=True, help="Target repo path")
    parser.add_argument("--skills-root", default="skills")
    parser.add_argument("--schema-path", default="prompt.schema.json")
    parser.add_argument("--prompts-dir", default="prompts")
    parser.add_argument("--sop-path", default="docs/new-project-sop.md")
    parser.add_argument("--profile-path", default="profile/README.md")
    args = parser.parse_args()

    if args.check == "readme":
        passed, details = check_readme(args.repo)
    elif args.check == "workflow":
        passed, details = check_workflows(args.repo)
    elif args.check == "skills":
        passed, details = check_skills(args.repo, args.skills_root)
    elif args.check == "prompt":
        passed, details = check_prompt_schema(args.repo, args.schema_path, args.prompts_dir)
    elif args.check == "member_bootstrap_prereq":
        passed, details = check_member_bootstrap_prereq(args.repo, args.sop_path)
    elif args.check == "private_download_sanity":
        passed, details = check_private_download_sanity(args.repo, args.sop_path)
    elif args.check == "onboarding_doc_drift":
        passed, details = check_onboarding_doc_drift(args.repo)
    elif args.check == "onboarding_command_integrity":
        passed, details = check_onboarding_command_integrity(args.repo)
    elif args.check == "plan_schema_ref_sync":
        passed, details = check_plan_schema_ref_sync(args.repo)
    elif args.check == "cli_contract_sync":
        passed, details = check_cli_contract_sync(args.repo)
    elif args.check == "post_init_audit_required":
        passed, details = check_post_init_audit_required(args.repo)
    elif args.check == "runbook_schema_validate":
        passed, details = check_runbook_schema_validate(args.repo)
    elif args.check == "runbook_checksums":
        passed, details = check_runbook_checksums(args.repo)
    elif args.check == "orphaned_assets":
        passed, details = check_orphaned_assets(args.repo)
    elif args.check == "gate_a_smoke":
        passed, details = check_gate_a_smoke(args.repo)
    elif args.check == "agent_safety":
        passed, details = check_agent_safety(args.repo)
    else:
        if args.check == "skill_structure_v2":
            passed, details = check_skill_structure_v2(args.repo, args.skills_root)
        else:
            passed, details = check_start_here_sync(args.repo, args.profile_path)

    output = {
        "check": args.check,
        "repo": os.path.abspath(args.repo),
        "pass": passed,
        "details": details,
    }
    print(json.dumps(output, ensure_ascii=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
