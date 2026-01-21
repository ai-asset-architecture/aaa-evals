import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from run_repo_checks import check_cli_contract_sync


class TestCliContractSync(unittest.TestCase):
    def _write_common_files(self, root: Path):
        (root / ".github" / "profile").mkdir(parents=True)
        (root / "aaa-tpl-docs" / "docs" / "contracts").mkdir(parents=True)
        (root / "aaa-tools" / "specs").mkdir(parents=True)
        (root / "aaa-tools" / "runbooks" / "init").mkdir(parents=True)

        profile_content = (
            "gh auth setup-git\n"
            "python3 -m pip install \"git+https://github.com/ai-asset-architecture/aaa-tools.git@v0.2.0\"\n"
            "plan.v0.1.json?ref=v0.2.0\n"
        )
        (root / ".github" / "profile" / "README.md").write_text(
            profile_content, encoding="utf-8"
        )

        (root / "aaa-tools" / "runbooks" / "init" / "AGENT_BOOTSTRAP.md").write_text(
            "bootstrap", encoding="utf-8"
        )

        (root / "aaa-tools" / "specs" / "CLI_CONTRACT.md").write_text(
            "post-init audit required\nrepo-checks\n",
            encoding="utf-8",
        )

        return profile_content

    def test_fails_when_post_init_missing_in_sop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_content = self._write_common_files(root)

            sop_content = (
                profile_content
                + "plan.schema.json?ref=v0.2.0\n"
                + "aaa init validate-plan\n"
                + "aaa-tools/runbooks/init/AGENT_BOOTSTRAP.md\n"
            )
            (root / "aaa-tpl-docs" / "docs" / "new-project-sop.md").write_text(
                sop_content, encoding="utf-8"
            )

            user_contract_content = (
                profile_content
                + "plan.schema.json?ref=v0.2.0\n"
                + "aaa init validate-plan\n"
                + "aaa init repo-checks\n"
                + "aaa-tools/runbooks/init/AGENT_BOOTSTRAP.md\n"
            )
            (root / "aaa-tpl-docs" / "docs" / "contracts" / "aaa-cli-contract.md").write_text(
                user_contract_content, encoding="utf-8"
            )

            ok, details = check_cli_contract_sync(str(root))
            self.assertFalse(ok)
            self.assertTrue(details)

    def test_passes_when_contracts_align(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_content = self._write_common_files(root)

            sop_content = (
                profile_content
                + "plan.schema.json?ref=v0.2.0\n"
                + "aaa init validate-plan\n"
                + "aaa init repo-checks\n"
                + "aaa-tools/runbooks/init/AGENT_BOOTSTRAP.md\n"
            )
            (root / "aaa-tpl-docs" / "docs" / "new-project-sop.md").write_text(
                sop_content, encoding="utf-8"
            )

            user_contract_content = sop_content
            (root / "aaa-tpl-docs" / "docs" / "contracts" / "aaa-cli-contract.md").write_text(
                user_contract_content, encoding="utf-8"
            )

            ok, details = check_cli_contract_sync(str(root))
            self.assertTrue(ok)
            self.assertEqual(details, [])


if __name__ == "__main__":
    unittest.main()
