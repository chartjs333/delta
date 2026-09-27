"""Full synthetic source container and its original004 provenance boundary."""

import copy
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "formal/scripts"))
import generate_native_vector_source as vectors
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes
from generate_native_available_q import fixture, joined_fixture
from generate_native_plan_source import source as original_source
from native_admission_snapshot import decode_flat, state_id
from native_available_q import resolve_plan_available_q
from native_certificate_chain import content_id
from native_source_artifacts import SourceError


class NativeVectorSourceTests(unittest.TestCase):
    def test_raw_policy_state_and_every_parent_match(self):
        p, pr, s, sr, trees, docs, _, _, _, edges, _ = vectors.source()
        self.assertEqual(codec.decode(pr), p)
        self.assertEqual(decode_flat(sr, 5), s)
        snap = p["snapshot"]
        self.assertEqual(snap["state_id"], state_id(sr))
        self.assertEqual(s["config_id"], docs["APC"]["round_config_id"])
        self.assertEqual(snap["input_set_certificates"], [trees["ISC"]])
        self.assertEqual(snap["aggregation_plan_certificates"], [trees["APC"]])
        for name in ["NORM", "SEED", "EC", "APC"]:
            self.assertEqual(docs[name]["input_set_certificate_id"], content_id(docs["ISC"]))
        self.assertEqual(edges, {content_id(docs["EC"]): content_id(docs["SEED"])})

    def test_original_artifacts_unchanged_and_original008_not_repaired(self):
        before = original_source()
        p, _, _, _, _, docs, store, golden, _, edges, observations = vectors.source()
        original_store, original_golden, _ = fixture()
        self.assertEqual(golden, original_golden)
        for identity, raw in original_store.items():
            self.assertEqual(store[identity], raw)
        self.assertEqual(original_source(), before)
        self.assertNotEqual(p["snapshot"]["state_id"], before[0]["snapshot"]["state_id"])
        self.assertNotEqual(
            content_id(docs["APC"]), before[0]["snapshot"]["finalized_aggregation_plan_ids"][0]
        )
        self.assertNotIn(before[0]["snapshot"]["required_accumulator_proof_id"], store)
        self.assertIsNotNone(
            resolve_plan_available_q(store, content_id(docs["APC"]), edges, observations)
        )

    def test_no_candidate_or_current_admission_claim(self):
        p, _, _, _, _, _, _, _, _, _, _ = vectors.source()
        candidate = p["candidates"][0]
        self.assertTrue(candidate["context_id"].startswith("STRUCTURAL-ONLY:"))
        self.assertTrue(all(v == "" for v in candidate["parents"].values()))
        self.assertEqual(p["snapshot"]["parameter_bodies"], [])
        self.assertEqual(p["snapshot"]["apply_candidates"], [])

    def test_corrupt_original_q_and_missing_proof_reject(self):
        store, apc, edges, observations, _, _ = joined_fixture()
        _, golden, _ = fixture()
        ids = [
            golden["proof_instance"]["content_id"],
            golden["manifest"]["value"]["shards"][0]["leaf_id"],
        ]
        for identity in ids:
            for missing in [True, False]:
                altered = copy.deepcopy(store)
                if missing:
                    del altered[identity]
                else:
                    raw = altered[identity]
                    altered[identity] = raw[:-1] + bytes([raw[-1] ^ 1])
                with self.assertRaises(SourceError):
                    resolve_plan_available_q(altered, apc, edges, observations)

    def test_missing_or_duplicate_q_observations_reject(self):
        store, apc, edges, observations, _, _ = joined_fixture()
        for wrong in [[], observations + observations]:
            with self.assertRaises(SourceError):
                resolve_plan_available_q(store, apc, edges, wrong)

    def test_reproduction_and_mandatory_axiom_inventory(self):
        policy, corpus, summary = vectors.generate()
        for mod, text in [
            ("NativeVectorSourceVectors", policy),
            ("NativeVectorCorpusVectors", corpus),
        ]:
            self.assertEqual(
                (vectors.ROOT / f"formal/proofs/DeltaReduce/{mod}.lean").read_bytes(), text.encode()
            )
            self.assertNotRegex(text, r"\b(?:sorry|admit|native_decide)\b")
            audit = (vectors.ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
            imports = (vectors.ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + mod, imports)
            for name in re.findall(r"^(?:def|theorem) (\w+)", text, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{mod}.{name}", audit)
        self.assertEqual(
            (vectors.ROOT / "formal/proposals/native-vector-source-vectors.json").read_bytes(),
            canonical_json_bytes(summary),
        )
        for key in [
            "native_execution",
            "gate_eligible",
            "native_export_authenticated",
            "synthetic_candidate_admitted",
            "full_draft_parameter_join_instantiated",
        ]:
            self.assertFalse(summary[key])
        for name in [
            "NativePlanQCorpus.bindFromSources",
            "NativePlanQCorpus.bindFromAbsentRows",
            "NativePlanQCorpus.extraSingleInput",
            "NativeVectorJoin.runFromContext",
        ]:
            self.assertIn("#print axioms DeltaReduce." + name, audit)


if __name__ == "__main__":
    unittest.main()
