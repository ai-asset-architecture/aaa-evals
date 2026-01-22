import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runner import run_repo_checks


class TestRunRepoChecks(unittest.TestCase):
    def test_orphaned_assets_check_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "docs" / "adrs"
            base.mkdir(parents=True)
            (base / "001.md").write_text("# ADR", encoding="utf-8")
            payload = {"files": [{"path": "001.md"}]}
            (base / "index.json").write_text(json.dumps(payload), encoding="utf-8")

            passed, details = run_repo_checks.check_orphaned_assets(str(tmp))
            self.assertTrue(passed, details)
            self.assertEqual(details, [])

    def test_orphaned_assets_ignores_default_temp_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / ".venv-aaa" / "lib" / "python3.13" / "site-packages" / "reports"
            base.mkdir(parents=True)
            payload = {"files": []}
            (base / "index.json").write_text(json.dumps(payload), encoding="utf-8")
            (base / "orphan.md").write_text("# Orphan", encoding="utf-8")

            passed, details = run_repo_checks.check_orphaned_assets(str(root))
            self.assertTrue(passed, details)
            self.assertEqual(details, [])

    def test_gate_a_smoke_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases_dir = root / "evals" / "cases"
            cases_dir.mkdir(parents=True)
            plan_path = root / "plan.json"
            plan_path.write_text("{\"aaa\": {\"version_tag\": \"v0.1.0\"}}", encoding="utf-8")
            (cases_dir / "gate_a_smoke.jsonl").write_text(
                "{\"id\":\"case-1\",\"plan_path\":\"plan.json\",\"template_repos\":[\"org/repo\"]}\n",
                encoding="utf-8",
            )

            with patch("runner.checks.check_gate_a_smoke._list_tags", return_value={"v0.1.0"}):
                passed, details = run_repo_checks.check_gate_a_smoke(str(root))
            self.assertTrue(passed, details)
            self.assertEqual(details, [])

    def test_runbook_checksum_guard_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("runner.run_repo_checks.check_runbook_checksums_impl") as checker:
                checker.return_value = {"pass": True, "details": []}
                passed, details = run_repo_checks.check_runbook_checksums(str(tmp))
            self.assertTrue(passed)
            self.assertEqual(details, [])


if __name__ == "__main__":
    unittest.main()
