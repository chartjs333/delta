"""Retained whole policy/state provenance and non-interchangeable proof inputs."""

import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "formal/scripts"))
import generate_native_plan as plan
import generate_native_plan_source as vectors
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_plan_weights import original_store
from generate_native_source_artifacts import fixture_store
from native_plan_weights import resolve_plan_weights
from native_source_artifacts import SourceError


class NativePlanSourceTests(unittest.TestCase):
    def test_original_state_is_exact_policy_preimage(self):
        policy, raw_policy, state, raw_state = vectors.source()
        self.assertEqual((len(raw_policy), len(raw_state)), (5849, 674))
        self.assertEqual(
            policy["snapshot"]["state_id"],
            "sha256:" + hashlib.sha256(b"deltareduce:003:round-state:v1\0" + raw_state).hexdigest(),
        )
        self.assertEqual(state["durable_sequence"], "0")
        self.assertEqual(state["phase"], "ELIGIBLE")
        self.assertEqual(policy["round_id"], state["round_id"])

    def test_whole_snapshot_retains_original_plan_and_parent(self):
        p, _, _, _ = vectors.source()
        _, tree, _, docs, _, _ = plan.source()
        snap = p["snapshot"]
        self.assertEqual(snap["aggregation_plan_certificates"], [tree])
        self.assertEqual(snap["required_accumulator_proof_id"], docs["APC"]["accumulator_proof_id"])
        self.assertEqual(snap["aggregation_plan_bodies"], [])
        self.assertEqual(snap["eligibility_bodies"], [])
        self.assertEqual(len(snap["input_set_certificates"]), 1)
        self.assertEqual(len(snap["norm_evidence"]), 1)
        self.assertEqual(len(snap["seed_transcripts"]), 1)
        self.assertEqual(len(snap["parameter_bodies"]), 1)  # preserved, not checked by plan prepare

    def test_actual004_store_does_not_repair_original008_proof(self):
        p, _, _, _ = vectors.source()
        store, pid, edges, _ = original_store()
        store.update(fixture_store()[0])
        required = p["snapshot"]["required_accumulator_proof_id"]
        self.assertNotIn(required, store)
        with self.assertRaisesRegex(SourceError, "MISSING_PREIMAGE:" + required):
            resolve_plan_weights(store, pid, edges)

    def test_retained_source_substitution_is_rejected(self):
        for path, field in [(vectors.POLICY, "policy_hex"), (vectors.STATE, "state_hex")]:
            document = copy.deepcopy(load_json_strict(vectors.ROOT / path))
            row = next(r for r in document["observed"] if field in r)
            row[field] = "00" + row[field][2:]
            real = vectors.load_json_strict
            with patch.object(
                vectors,
                "load_json_strict",
                side_effect=lambda p, doc=document, target=path, reader=real: (
                    doc if p == vectors.ROOT / target else reader(p)
                ),
            ):
                with self.assertRaisesRegex(ValueError, "original .* observation changed"):
                    vectors.source()

    def test_reproduction_and_kernel_inventory(self):
        lean, summary = vectors.generate()
        target = vectors.ROOT / "formal/proofs/DeltaReduce/NativePlanSourceVectors.lean"
        self.assertEqual(target.read_bytes(), lean.encode())
        self.assertEqual(
            (vectors.ROOT / "formal/proposals/native-plan-source-vectors.json").read_bytes(),
            canonical_json_bytes(summary),
        )
        self.assertFalse(summary["complete_vector_join"])
        self.assertFalse(summary["native_export_authenticated"])
        audit = (target.parent / "AxiomAudit.lean").read_text("utf-8")
        imports = (target.parent.parent / "DeltaReduce.lean").read_text("utf-8")
        for module in ["NativeSourceRefusal", "NativePlanSourceVectors"]:
            self.assertIn("import DeltaReduce." + module, imports)
            source = (target.parent / (module + ".lean")).read_text("utf-8")
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
