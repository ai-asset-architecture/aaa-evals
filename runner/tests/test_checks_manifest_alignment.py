import json
from pathlib import Path
import unittest

from runner.checks.check_checks_manifest_alignment import check_checks_manifest_alignment


class TestChecksManifestAlignment(unittest.TestCase):
    def test_checks_manifest_alignment_pass(self):
        manifest = Path(self._tempdir()) / "checks.manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "checks": [
                        {"id": "lint", "name": "Lint", "applies_to": ["all"]},
                        {"id": "agent", "name": "Agent safety check", "applies_to": ["agent"]},
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = check_checks_manifest_alignment({"manifest_path": str(manifest)})
        self.assertIs(result["pass"], False)
        self.assertTrue(any("missing applies_to types" in item for item in result["details"]))

    def test_checks_manifest_alignment_full(self):
        manifest = Path(self._tempdir()) / "checks.manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "checks": [
                        {"id": "lint", "name": "Lint", "applies_to": ["all"]},
                        {"id": "docs", "name": "Docs", "applies_to": ["docs"]},
                        {"id": "service", "name": "Service", "applies_to": ["service"]},
                        {"id": "frontend", "name": "Frontend", "applies_to": ["frontend"]},
                        {"id": "agent", "name": "Agent", "applies_to": ["agent"]},
                        {"id": "genai", "name": "GenAI", "applies_to": ["genai-service"]},
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = check_checks_manifest_alignment({"manifest_path": str(manifest)})
        self.assertIs(result["pass"], True)

    def _tempdir(self):
        import tempfile
        return tempfile.mkdtemp()


if __name__ == "__main__":
    unittest.main()
