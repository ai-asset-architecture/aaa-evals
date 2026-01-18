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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", required=True, choices=["readme", "workflow", "skills"])
    parser.add_argument("--repo", required=True, help="Target repo path")
    parser.add_argument("--skills-root", default="skills")
    args = parser.parse_args()

    if args.check == "readme":
        passed, details = check_readme(args.repo)
    elif args.check == "workflow":
        passed, details = check_workflows(args.repo)
    else:
        passed, details = check_skills(args.repo, args.skills_root)

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
