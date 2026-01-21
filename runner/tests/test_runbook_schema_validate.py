import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from run_repo_checks import check_runbook_schema_validate


class TestRunbookSchemaValidate(unittest.TestCase):
    def test_fails_when_schema_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok, details = check_runbook_schema_validate(str(root))
            self.assertFalse(ok)
            self.assertTrue(details)

    def test_passes_with_valid_runbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            schema_path = root / "aaa-tools" / "specs"
            runbook_path = root / "aaa-tools" / "runbooks" / "repo"
            schema_path.mkdir(parents=True)
            runbook_path.mkdir(parents=True)

            schema_path.joinpath("runbook.schema.json").write_text(
                "{\"type\":\"object\",\"required\":[\"metadata\",\"contract\",\"steps\"]}",
                encoding="utf-8",
            )
            runbook_path.joinpath("init-repo.yaml").write_text(
                "{\"metadata\":{},\"contract\":{},\"steps\":[]}",
                encoding="utf-8",
            )

            ok, details = check_runbook_schema_validate(str(root))
            self.assertFalse(ok)
            self.assertTrue(details)


if __name__ == "__main__":
    unittest.main()
