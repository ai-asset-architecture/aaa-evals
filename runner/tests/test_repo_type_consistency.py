import json
from pathlib import Path
import unittest

from runner.checks.check_repo_type_consistency import check_repo_type_consistency


class TestRepoTypeConsistency(unittest.TestCase):
    def test_repo_type_consistency_pass(self):
        repo = Path(self._tempdir()) / "repo"
        repo.mkdir(parents=True)
        (repo / ".aaa").mkdir(parents=True)
        (repo / ".aaa" / "metadata.json").write_text(
            json.dumps({"repo_type": "docs", "plan_ref": "plan.v0.7.json"}),
            encoding="utf-8",
        )

        result = check_repo_type_consistency({"repo_root": str(repo), "expected_repo_type": "docs"})
        self.assertIs(result["pass"], True)

    def test_repo_type_consistency_missing(self):
        repo = Path(self._tempdir()) / "repo"
        repo.mkdir(parents=True)
        result = check_repo_type_consistency({"repo_root": str(repo), "expected_repo_type": "docs"})
        self.assertIs(result["pass"], False)

    def _tempdir(self):
        import tempfile
        return tempfile.mkdtemp()


if __name__ == "__main__":
    unittest.main()
