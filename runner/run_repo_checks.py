import argparse
import json
import os
import re
import sys


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


def check_workflows(repo_path):
    workflows_dir = os.path.join(repo_path, ".github", "workflows")
    if not os.path.isdir(workflows_dir):
        return False, [".github/workflows missing"]

    yaml_files = [
        os.path.join(workflows_dir, name)
        for name in os.listdir(workflows_dir)
        if name.endswith((".yml", ".yaml"))
    ]
    if not yaml_files:
        return False, ["No workflow files found"]

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


def load_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_prompt(schema, prompt_obj):
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
            ok, issues = validate_prompt(schema, payload)
            if not ok:
                failures.append(f"{os.path.relpath(path, repo_path)}: {', '.join(issues)}")

    return len(failures) == 0, failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", required=True, choices=["readme", "workflow", "skills", "prompt"])
    parser.add_argument("--repo", required=True, help="Target repo path")
    parser.add_argument("--skills-root", default="skills")
    parser.add_argument("--schema-path", default="prompt.schema.json")
    parser.add_argument("--prompts-dir", default="prompts")
    args = parser.parse_args()

    if args.check == "readme":
        passed, details = check_readme(args.repo)
    elif args.check == "workflow":
        passed, details = check_workflows(args.repo)
    elif args.check == "skills":
        passed, details = check_skills(args.repo, args.skills_root)
    else:
        passed, details = check_prompt_schema(args.repo, args.schema_path, args.prompts_dir)

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
