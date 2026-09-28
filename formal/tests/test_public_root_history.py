"""Original ROOT context convention and history/envelope proof inventory."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_aggregate as aggregate  # noqa: E402
import native_policy_codec as codec  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402

MODULES = (
    "NativeHistoryRow",
    "PublicRootEnvelope",
    "PublicRootHistory",
    "PublicRootHistoryVectors",
)


class RootHistoryTests(unittest.TestCase):
    def test_original_root_parent_and_public_context_are_distinct_representations(self):
        capture = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        row = next(r for r in capture["observed"] if r["name"] == "codec-AGGREGATE_ROOT")
        raw = bytes.fromhex(row["policy_hex"])
        policy = codec.decode(raw)
        self.assertEqual(codec.HEADER + codec.encode_value("policy", policy), raw)
        doc, _, proposal, _, _, observed = aggregate.source()
        self.assertEqual(
            proposal["aggregation_plan_certificate_id"], doc["aggregation_plan_certificate_id"]
        )
        self.assertEqual(aggregate.body_id(doc), observed["bodies"]["ROOT"])
        tla = (ROOT / "formal/tla/DeltaReduceReduceApply.tla").read_text("utf-8")
        self.assertIn('VoteEnvelope(validator, "AGGREGATE_ROOT", body.apc, body)', tla)
        self.assertIn(r"validator \in Validators", tla)
        self.assertIn(r"body \in aggregateCandidates", tla)
        self.assertEqual(policy["snapshot"]["aggregate_root_qcs"], [])
        self.assertEqual(policy["snapshot"]["apply_qcs"], [])

    def test_checked_general_history_and_envelope_declarations_are_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) ([\w.]+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
        history = (ROOT / "formal/proofs/DeltaReduce/PublicRootHistory.lean").read_text("utf-8")
        for required in (
            "NativeEarlySource.load",
            "NativeRootSource.loadRoot",
            "NativeRootCorpus.check",
            "PublicRootEnvelope.check",
            "historicalPosition adapter history",
            "ordinaryOriginalAuthority",
        ):
            self.assertIn(required, history)
        self.assertNotIn("NativePrepared", history)
        self.assertNotIn("ready := true", history)
        lookup = (ROOT / "formal/proofs/DeltaReduce/NativeHistoryRow.lean").read_text("utf-8")
        self.assertIn("match complete : NativeCacheHistory.recover", lookup)
        self.assertIn("theorem originalSequences", lookup)
        self.assertIn("theorem incompleteRejects", lookup)


if __name__ == "__main__":
    unittest.main()
