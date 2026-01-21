import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from run_repo_checks import check_onboarding_doc_drift


class TestOnboardingDocDrift(unittest.TestCase):
    def test_detects_version_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github" / "profile").mkdir(parents=True)
            (root / "aaa-tpl-docs" / "docs").mkdir(parents=True)

            (root / ".github" / "profile" / "README.md").write_text(
                "python3 -m pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@v0.2.0\"\n"
                "plan.v0.1.json?ref=v0.2.0\n",
                encoding="utf-8",
            )
            (root / "aaa-tpl-docs" / "docs" / "new-project-sop.md").write_text(
                "python3 -m pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@v0.1.0\"\n"
                "plan.v0.1.json?ref=v0.1.0\n"
                "plan.schema.json?ref=v0.1.0\n",
                encoding="utf-8",
            )
            (root / "aaa-tpl-docs" / "PROJECT_PLAYBOOK.md").write_text(
                "python3 -m pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@v0.2.0\"\n",
                encoding="utf-8",
            )

            ok, details = check_onboarding_doc_drift(str(root))
            self.assertFalse(ok)
            self.assertTrue(details)

    def test_passes_when_versions_align(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github" / "profile").mkdir(parents=True)
            (root / "aaa-tpl-docs" / "docs").mkdir(parents=True)

            content = (
                "python3 -m pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@v0.2.0\"\n"
                "plan.v0.1.json?ref=v0.2.0\n"
                "plan.schema.json?ref=v0.2.0\n"
            )
            (root / ".github" / "profile" / "README.md").write_text(content, encoding="utf-8")
            (root / "aaa-tpl-docs" / "docs" / "new-project-sop.md").write_text(content, encoding="utf-8")
            (root / "aaa-tpl-docs" / "PROJECT_PLAYBOOK.md").write_text(content, encoding="utf-8")

            ok, details = check_onboarding_doc_drift(str(root))
            self.assertTrue(ok)
            self.assertEqual(details, [])


if __name__ == "__main__":
    unittest.main()
