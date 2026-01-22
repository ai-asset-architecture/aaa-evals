import json
import tempfile
import unittest
from pathlib import Path

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
            self.assertTrue(passed)
            self.assertEqual(details, [])


if __name__ == "__main__":
    unittest.main()
