import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from run_repo_checks import check_post_init_audit_required


class TestPostInitAuditRequired(unittest.TestCase):
    def _write_files(self, root: Path, include_runbook: bool):
        (root / "aaa-tpl-docs" / "docs" / "contracts").mkdir(parents=True, exist_ok=True)
        (root / "aaa-tools" / "runbooks" / "init").mkdir(parents=True)

        sop_content = (
            "post-init\n"
            "aaa init repo-checks\n"
            "aaa-tools/runbooks/init/POST_INIT_AUDIT.md\n"
        )
        contract_content = sop_content

        (root / "aaa-tpl-docs" / "docs" / "new-project-sop.md").write_text(
            sop_content, encoding="utf-8"
        )
        (root / "aaa-tpl-docs" / "docs" / "contracts" / "aaa-cli-contract.md").write_text(
            contract_content, encoding="utf-8"
        )

        if include_runbook:
            (root / "aaa-tools" / "runbooks" / "init" / "POST_INIT_AUDIT.md").write_text(
                "aaa init repo-checks\n--suite governance\n",
                encoding="utf-8",
            )

    def test_fails_when_runbook_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_files(root, include_runbook=False)

            ok, details = check_post_init_audit_required(str(root))
            self.assertFalse(ok)
            self.assertTrue(details)

    def test_passes_when_runbook_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_files(root, include_runbook=True)

            ok, details = check_post_init_audit_required(str(root))
            self.assertTrue(ok)
            self.assertEqual(details, [])


if __name__ == "__main__":
    unittest.main()
