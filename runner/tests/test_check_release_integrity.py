import unittest
from pathlib import Path
from unittest.mock import patch

from runner.checks.check_release_integrity import check_release_integrity


class ReleaseIntegrityTests(unittest.TestCase):
    def test_missing_tag_fails(self):
        ok, details = check_release_integrity("/tmp", "")
        self.assertFalse(ok)
        self.assertTrue(details)

    def test_missing_script_fails(self):
        ok, details = check_release_integrity("/tmp", "v1.0.0")
        self.assertFalse(ok)
        self.assertTrue(any("release verify script missing" in item for item in details))

    def test_script_failure_reports_output(self):
        repo_root = Path(__file__).resolve().parent
        script_path = repo_root / "release-verify.sh"
        script_path.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        try:
            with patch("runner.checks.check_release_integrity.subprocess.run") as mock_run:
                mock_run.return_value = type(
                    "Result",
                    (),
                    {"returncode": 2, "stdout": "out", "stderr": "err"},
                )()
                ok, details = check_release_integrity(str(repo_root), "v1.0.0", str(script_path))
                self.assertFalse(ok)
                self.assertTrue(any("release verify failed" in item for item in details))
        finally:
            script_path.unlink(missing_ok=True)

    def test_success_passes(self):
        repo_root = Path(__file__).resolve().parent
        script_path = repo_root / "release-verify.sh"
        script_path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        try:
            with patch("runner.checks.check_release_integrity.subprocess.run") as mock_run:
                mock_run.return_value = type(
                    "Result",
                    (),
                    {"returncode": 0, "stdout": "ok", "stderr": ""},
                )()
                ok, details = check_release_integrity(str(repo_root), "v1.0.0", str(script_path))
                self.assertTrue(ok)
                self.assertEqual(details, [])
        finally:
            script_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
