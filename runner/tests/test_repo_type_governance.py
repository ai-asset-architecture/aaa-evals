import unittest

from runner.run_repo_checks import should_require_agent_assets


class TestRepoTypeGovernance(unittest.TestCase):
    def test_docs_repo_skips_agent_assets(self):
        self.assertIs(should_require_agent_assets("docs"), False)

    def test_agent_repo_requires_agent_assets(self):
        self.assertIs(should_require_agent_assets("agent"), True)


if __name__ == "__main__":
    unittest.main()
