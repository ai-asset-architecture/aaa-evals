import os
import shutil
import unittest
from pathlib import Path

from runner.checks.check_agent_safety import check_agent_safety


class AgentSafetyCheckTests(unittest.TestCase):
    def test_expected_error_counts_as_pass(self):
        repo_root = Path(__file__).resolve().parents[2]
        aaa_cmd = shutil.which("aaa")
        tools_root = None
        for parent in repo_root.parents:
            candidate = parent / "aaa-tools"
            if candidate.is_dir():
                tools_root = candidate
                break
        if aaa_cmd:
            help_result = shutil.which("aaa")
            if help_result:
                output = os.popen("aaa run runbook --help").read()
                if "--runbook-file" not in output:
                    self.skipTest("aaa CLI lacks --runbook-file support")
        elif tools_root is None:
            self.skipTest("aaa-tools not available for agent safety check")
        if not aaa_cmd and tools_root is not None:
            cli_path = tools_root / "aaa" / "cli.py"
            if cli_path.is_file():
                if "--runbook-file" not in cli_path.read_text(encoding="utf-8"):
                    self.skipTest("aaa-tools source lacks --runbook-file support")
            os.environ.setdefault("AAA_TOOLS_ROOT", str(tools_root))
        result = check_agent_safety(
            {
                "runbook": "evals/fixtures/runbooks/security/attack-scope-violation.yaml",
                "expected": {"status": "error", "error_code": "SCOPE_VIOLATION"},
            },
            repo_root,
        )
        self.assertTrue(result["pass"])


if __name__ == "__main__":
    unittest.main()
