import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runner.checks.check_gate_a_smoke import check_gate_a_smoke


def _write_plan(path: Path, version_tag: str | None) -> None:
    payload = {"aaa": {}}
    if version_tag is not None:
        payload["aaa"]["version_tag"] = version_tag
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestCheckGateASmoke(unittest.TestCase):
    def test_missing_version_tag_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            _write_plan(plan_path, None)
            result = check_gate_a_smoke(
                {
                    "plan_path": str(plan_path),
                    "template_repos": ["org/repo"],
                },
                Path(tmp),
            )
            self.assertFalse(result["pass"])
            self.assertTrue(any(item["type"] == "missing_version_tag" for item in result["details"]))

    def test_missing_tag_in_template_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            _write_plan(plan_path, "v0.1.0")

            def _fake_run(cmd, capture_output, text, check):
                repo = cmd[-1]
                stdout = ""
                if repo.endswith("org/ok.git"):
                    stdout = "abc\trefs/tags/v0.1.0\n"
                return type("Result", (), {"returncode": 0, "stdout": stdout, "stderr": ""})

            with patch("runner.checks.check_gate_a_smoke.subprocess.run", side_effect=_fake_run):
                result = check_gate_a_smoke(
                    {
                        "plan_path": str(plan_path),
                        "template_repos": ["org/ok", "org/missing"],
                    },
                    Path(tmp),
                )
            self.assertFalse(result["pass"])
            self.assertTrue(any(item["type"] == "missing_template_tag" for item in result["details"]))

    def test_all_tags_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            _write_plan(plan_path, "v0.1.0")

            def _fake_run(cmd, capture_output, text, check):
                return type(
                    "Result",
                    (),
                    {"returncode": 0, "stdout": "abc\trefs/tags/v0.1.0\n", "stderr": ""},
                )

            with patch("runner.checks.check_gate_a_smoke.subprocess.run", side_effect=_fake_run):
                result = check_gate_a_smoke(
                    {
                        "plan_path": str(plan_path),
                        "template_repos": ["org/ok", "org/ok2"],
                    },
                    Path(tmp),
                )
            self.assertTrue(result["pass"])
            self.assertEqual(result["details"], [])


if __name__ == "__main__":
    unittest.main()
