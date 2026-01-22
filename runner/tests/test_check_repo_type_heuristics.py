import tempfile
import unittest
from pathlib import Path

from runner.run_repo_checks import check_prompt_schema, check_skills


def _write(path: Path, content: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestRepoTypeHeuristics(unittest.TestCase):
    def test_non_agent_repo_skips_skills_and_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "README.md", "# Repo\n")
            skills_ok, skills_details = check_skills(str(repo), "skills")
            prompt_ok, prompt_details = check_prompt_schema(str(repo), "prompt.schema.json", "prompts")

            self.assertIs(skills_ok, True)
            self.assertIs(prompt_ok, True)
            self.assertTrue(any("skipped" in item for item in skills_details))
            self.assertTrue(any("skipped" in item for item in prompt_details))

    def test_agent_repo_requires_skills_and_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo / "agent.yaml", "name: agent\n")

            skills_ok, skills_details = check_skills(str(repo), "skills")
            prompt_ok, prompt_details = check_prompt_schema(str(repo), "prompt.schema.json", "prompts")

            self.assertIs(skills_ok, False)
            self.assertIs(prompt_ok, False)
            self.assertTrue(any("missing" in item for item in skills_details))
            self.assertTrue(any("missing" in item for item in prompt_details))


if __name__ == "__main__":
    unittest.main()
