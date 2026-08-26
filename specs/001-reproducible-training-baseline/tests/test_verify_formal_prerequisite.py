from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT
    / "specs"
    / "001-reproducible-training-baseline"
    / "scripts"
    / "verify_formal_prerequisite.py"
)
REPORT = ROOT / "formal" / "reports" / "formal-verification-report.json"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class FormalPrerequisiteVerifierTests(unittest.TestCase):
    def run_verifier(self, report: Path) -> tuple[int, dict[str, Any]]:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check-only", "--report", str(report)],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        self.assertEqual(completed.stderr, "")
        return completed.returncode, json.loads(completed.stdout)

    def mutated_report(self, mutate: Any) -> Path:
        payload = json.loads(REPORT.read_text(encoding="utf-8"))
        mutate(payload)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "formal-verification-report.json"
        path.write_bytes(canonical_bytes(payload))
        return path

    def test_exact_merged_go_passes(self) -> None:
        code, result = self.run_verifier(REPORT)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["report"]["decision"], "GO")

    def test_no_go_fails_closed(self) -> None:
        path = self.mutated_report(lambda payload: payload.update(decision="NO_GO"))
        code, result = self.run_verifier(path)
        self.assertEqual(code, 2)
        self.assertEqual(result["error_code"], "REPORT_NOT_GO")

    def test_incompatible_semantics_fails_closed(self) -> None:
        path = self.mutated_report(
            lambda payload: payload.update(formal_semantics_id="sha256:" + "0" * 64)
        )
        code, result = self.run_verifier(path)
        self.assertEqual(code, 2)
        self.assertEqual(result["error_code"], "SEMANTICS_ID_MISMATCH")

    def test_altered_evidence_hash_fails_closed(self) -> None:
        def mutate(payload: dict[str, Any]) -> None:
            payload["evidence_graph"]["nodes"][0]["sha256"] = "0" * 64

        path = self.mutated_report(mutate)
        code, result = self.run_verifier(path)
        self.assertEqual(code, 2)
        self.assertEqual(result["error_code"], "EVIDENCE_HASH_MISMATCH")

    def test_duplicate_reviewer_fails_closed(self) -> None:
        def mutate(payload: dict[str, Any]) -> None:
            reviews = payload["review_attestations"]
            reviews[1] = copy.deepcopy(reviews[0])

        path = self.mutated_report(mutate)
        code, result = self.run_verifier(path)
        self.assertEqual(code, 2)
        self.assertEqual(result["error_code"], "REVIEWER_ID_DUPLICATE")

    def test_missing_report_fails_closed(self) -> None:
        missing = Path(tempfile.gettempdir()) / "delta-missing-formal-report.json"
        code, result = self.run_verifier(missing)
        self.assertEqual(code, 2)
        self.assertIn(result["error_code"], {"JSON_FILE_MISSING", "REPORT_MISSING"})


if __name__ == "__main__":
    unittest.main()
