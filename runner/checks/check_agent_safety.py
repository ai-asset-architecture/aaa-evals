import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _resolve_aaa_tools_command(repo_root: Path) -> tuple[list[str] | None, dict[str, str]]:
    env = os.environ.copy()
    override = env.get("AAA_TOOLS_CMD")
    if override:
        return shlex.split(override), env

    aaa_cmd = shutil.which("aaa")
    if aaa_cmd:
        return [aaa_cmd], env

    tools_root = env.get("AAA_TOOLS_ROOT")
    if not tools_root:
        for parent in [repo_root.parent, *repo_root.parents]:
            candidate = parent / "aaa-tools"
            if candidate.is_dir():
                tools_root = str(candidate)
                break

    if tools_root:
        pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = f"{tools_root}{os.pathsep}{pythonpath}" if pythonpath else tools_root
        return [sys.executable, "-m", "aaa.cli"], env

    return None, env


def _run_runbook(repo_root: Path, runbook_path: str) -> dict[str, Any]:
    base_cmd, env = _resolve_aaa_tools_command(repo_root)
    if base_cmd is None:
        return {
            "status": "error",
            "error_code": "TOOL_NOT_AVAILABLE",
            "message": "aaa-tools CLI not available",
            "details": {},
        }

    command = [
        *base_cmd,
        "run",
        "runbook",
        "--runbook-file",
        runbook_path,
        "--json",
    ]
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    stdout = result.stdout.strip()
    if not stdout:
        stderr = result.stderr.strip()
        if "--runbook-file" in stderr and "unrecognized arguments" in stderr:
            return {
                "status": "error",
                "error_code": "TOOL_INCOMPATIBLE",
                "message": "aaa-tools CLI missing --runbook-file support",
                "details": {"stderr": stderr},
            }
        return {
            "status": "error",
            "error_code": "EMPTY_OUTPUT",
            "message": "no stdout from runbook execution",
            "details": {"stderr": result.stderr},
        }
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "error_code": "INVALID_JSON",
            "message": "invalid JSON output from runbook execution",
            "details": {"stdout": stdout, "stderr": result.stderr},
        }


def check_agent_safety(case: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    expected = case.get("expected", {})
    runbook = case.get("runbook")
    if not runbook:
        return {
            "pass": False,
            "details": [{"type": "invalid_case", "message": "missing runbook path"}],
        }
    actual = _run_runbook(repo_root, runbook)
    if actual.get("status") == expected.get("status") and actual.get("error_code") == expected.get("error_code"):
        return {"pass": True, "details": []}
    return {
        "pass": False,
        "details": [
            {
                "type": "unexpected_result",
                "expected": expected,
                "actual": actual,
            }
        ],
    }
