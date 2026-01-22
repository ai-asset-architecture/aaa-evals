import json
import tempfile
import unittest
from pathlib import Path

from runner.checks.check_runbook_checksums import check_runbook_checksums


def _checksum(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    import hashlib

    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _write_runbook(path: Path, checksum: str | None) -> None:
    payload = {
        "metadata": {
            "id": "ops/sample",
            "version": "1.0.0",
            "checksum": checksum or "",
        },
        "contract": {},
        "steps": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestCheckRunbookChecksums(unittest.TestCase):
    def test_checksum_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook_path = root / "runbooks" / "ops" / "sample.yaml"
            runbook_path.parent.mkdir(parents=True)
            _write_runbook(runbook_path, "sha256:bad")

            result = check_runbook_checksums({"repo_root": str(root)})
            self.assertFalse(result["pass"])
            self.assertTrue(any(item["type"] == "checksum_mismatch" for item in result["details"]))

    def test_checksum_match_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook_path = root / "runbooks" / "ops" / "sample.yaml"
            runbook_path.parent.mkdir(parents=True)

            payload = {
                "metadata": {
                    "id": "ops/sample",
                    "version": "1.0.0",
                    "checksum": "",
                },
                "contract": {},
                "steps": [],
            }
            payload["metadata"]["checksum"] = _checksum(payload)
            runbook_path.write_text(json.dumps(payload), encoding="utf-8")

            result = check_runbook_checksums({"repo_root": str(root)})
            self.assertTrue(result["pass"])
            self.assertEqual(result["details"], [])


if __name__ == "__main__":
    unittest.main()
