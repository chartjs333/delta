"""Legacy body labels must not be silently promoted to native certificate bytes."""

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import audit_public_prefix_sources as audit  # noqa: E402


class PublicDurablePrefixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit.audit()

    def test_exact_original_sequences_and_distinct_body_scope(self):
        rows = self.result["records"]
        self.assertEqual([row["sequence"] for row in rows], list(range(1, 9)))
        labels = [row for row in rows if "label_preimage_ascii" in row]
        self.assertEqual([row["sequence"] for row in labels], [2, 3, 4, 7])
        self.assertTrue(all(row["original_vote_parents_empty"] for row in labels))
        self.assertTrue(all(row["body_id"] not in row["graph_projection_ids"] for row in labels))
        self.assertFalse(self.result["full_prefix_bridge_pass"])
        self.assertFalse(self.result["native_export_authenticated"])

    def test_arithmetic_bytes_keep_original_five_six_eight(self):
        rows = self.result["records"]
        self.assertEqual(
            [row["sequence"] for row in rows if row["status"].startswith("CANONICAL_ARITHMETIC")],
            [5, 6, 8],
        )
        self.assertEqual(
            rows[0]["status"], "CANONICAL_ROUND_CONTRACT_PROJECTION_NOT_NATIVE_CONFIG_QC"
        )

    def test_substituting_a_label_hash_is_not_source_authentication(self):
        trace = json.loads(audit.PUBLIC.read_bytes())
        event = next(e for e in trace["events"] if e["action_id"] == "ACT-ISC-VOTE")
        changed = copy.deepcopy(trace)
        changed["events"][trace["events"].index(event)]["body_hash"] = "sha256:" + "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "trace.json"
            path.write_bytes(audit.canonical_json_bytes(changed))
            with self.assertRaisesRegex(ValueError, "PROJECTION_PUBLIC_PIN"):
                audit.audit(path)

    def test_declarations_are_mandatory_and_audited(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        report = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in ["PublicDurablePrefix", "PublicDurablePrefixVectors"]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            self.assertIn(f"import DeltaReduce.{module}\n", project)
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", report)


if __name__ == "__main__":
    unittest.main()
