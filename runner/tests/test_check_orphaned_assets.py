import json
import tempfile
import unittest
from pathlib import Path

from runner.checks.check_orphaned_assets import check_orphaned_assets


def _write_index(dir_path: Path, paths: list[str]) -> None:
    payload = {"files": [{"path": item} for item in paths]}
    (dir_path / "index.json").write_text(json.dumps(payload), encoding="utf-8")


class TestCheckOrphanedAssets(unittest.TestCase):
    def test_orphaned_assets_detects_missing_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "docs" / "adrs"
            base.mkdir(parents=True)
            (base / "001.md").write_text("# ADR", encoding="utf-8")
            result = check_orphaned_assets(
                {
                    "target_paths": [str(base)],
                    "file_pattern": "*.md",
                    "exclude_patterns": ["**/README.md", "**/index.json", ".*"],
                    "require_index": True,
                }
            )
            self.assertFalse(result["pass"])
            self.assertTrue(any(item["type"] == "missing_index" for item in result["details"]))

    def test_orphaned_assets_detects_orphaned_files_with_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "docs" / "adrs"
            base.mkdir(parents=True)
            (base / "001.md").write_text("# ADR", encoding="utf-8")
            _write_index(base, ["002.md"])
            result = check_orphaned_assets(
                {
                    "target_paths": [str(base)],
                    "file_pattern": "*.md",
                    "exclude_patterns": ["**/README.md", "**/index.json", ".*"],
                    "require_index": True,
                }
            )
            self.assertFalse(result["pass"])
            orphaned = [item for item in result["details"] if item["type"] == "orphaned_asset"]
            self.assertTrue(orphaned)
            self.assertIn("suggested_fix", orphaned[0])


if __name__ == "__main__":
    unittest.main()
