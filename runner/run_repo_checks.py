import argparse
import json
import os
import re
import sys

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


def check_skills(repo_path, skills_root):
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
