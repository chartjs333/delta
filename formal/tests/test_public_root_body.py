"""Pinned pre-finalization ROOT source and checked proof/audit inventory."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_aggregate as aggregate  # noqa: E402
import native_policy_codec as codec  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402


class RootBodyTests(unittest.TestCase):
    def test_original_root_vote_precedes_root_qc_and_apply(self):
        capture = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        row = next(r for r in capture["observed"] if r["name"] == "codec-AGGREGATE_ROOT")
        raw = bytes.fromhex(row["policy_hex"])
        policy = codec.decode(raw)
        self.assertEqual(codec.HEADER + codec.encode_value("policy", policy), raw)
        snapshot = policy["snapshot"]
        doc, _, proposed, docs, _, observed = aggregate.source()
        self.assertEqual(snapshot["aggregate_root_bodies"], [proposed])
        for key in (
            "aggregate_root_qcs",
            "finalized_aggregate_root_ids",
            "apply_qcs",
            "finalized_apply_ids",
        ):
            self.assertEqual(snapshot[key], [], key)
        self.assertEqual(snapshot["finalized_parameter_ids"], [content_id(docs["PARAMETER"])])
        self.assertEqual(
            proposed["leaves"][0]["parameter_shard_qc_id"], content_id(docs["PARAMETER"])
        )
        self.assertEqual(aggregate.body_id(doc), observed["bodies"]["ROOT"])
        self.assertNotEqual(aggregate.body_id(doc), content_id(doc))

    def test_source_bound_modules_and_axiom_inventory(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in (
            "NativeRootSource",
            "NativeRootCorpus",
            "PublicRootBody",
            "PublicRootBodyVectors",
        ):
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) ([\w.]+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
        corpus = (ROOT / "formal/proofs/DeltaReduce/NativeRootCorpus.lean").read_text("utf-8")
        self.assertIn("NativeVectorAuthority.rawSource src.vector", corpus)
        self.assertIn("{adapter : HashAdapter codec}", corpus)
        self.assertNotIn("NativeCertifiedCorpus.check binding", corpus)
        self.assertNotIn("deriveNativeApply", corpus)


if __name__ == "__main__":
    unittest.main()
