import argparse
import json
import shutil
import subprocess
import sys


def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def gh_auth_ok():
    if not shutil.which("gh"):
        return False, "gh not installed"
    code, out, err = run(["gh", "auth", "status"])
    if code != 0:
        return False, err or "gh auth status failed"
    return True, ""


def git_identity_ok():
    code, name, _ = run(["git", "config", "--global", "user.name"])
    code2, email, _ = run(["git", "config", "--global", "user.email"])
    if code != 0 or not name:
        return False, "git user.name missing"
    if code2 != 0 or not email:
        return False, "git user.email missing"
    return True, ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", default="gh_cli_setup")
    args = parser.parse_args()

    failures = []

    ok, detail = gh_auth_ok()
    if not ok:
        failures.append(detail)

    ok, detail = git_identity_ok()
    if not ok:
        failures.append(detail)

    output = {
        "check": args.check,
        "pass": len(failures) == 0,
        "details": failures,
    }
    print(json.dumps(output, ensure_ascii=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
