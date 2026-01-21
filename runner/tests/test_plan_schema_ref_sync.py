import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from run_repo_checks import check_plan_schema_ref_sync


class TestPlanSchemaRefSync(unittest.TestCase):
    def test_detects_mismatched_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "aaa-tpl-docs" / "docs").mkdir(parents=True)

            (root / "aaa-tpl-docs" / "docs" / "new-project-sop.md").write_text(
                "plan.v0.1.json?ref=v0.2.0\n"
                "plan.schema.json?ref=v0.1.0\n",
                encoding="utf-8",
            )

            ok, details = check_plan_schema_ref_sync(str(root))
            self.assertFalse(ok)
            self.assertTrue(details)

    def test_passes_when_refs_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "aaa-tpl-docs" / "docs").mkdir(parents=True)

            (root / "aaa-tpl-docs" / "docs" / "new-project-sop.md").write_text(
                "plan.v0.1.json?ref=v0.2.0\n"
                "plan.schema.json?ref=v0.2.0\n",
                encoding="utf-8",
            )

            ok, details = check_plan_schema_ref_sync(str(root))
            self.assertTrue(ok)
            self.assertEqual(details, [])


if __name__ == "__main__":
    unittest.main()
