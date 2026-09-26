"""Cross-source original ROOT identities, exact coverage and Merkle carry scope."""

import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_aggregate as generator  # noqa: E402
from formal_artifacts import canonical_json_bytes, load_json_strict  # noqa: E402
from native_certificate_chain import content_id, merkle_root  # noqa: E402


class AggregateTests(unittest.TestCase):
    def test_generated_bytes(self):
        self.assertEqual(generator.generate().encode("utf-8"), generator.TARGET.read_bytes())

    def test_complete_original_fields(self):
        doc, _, _, _, _, observed = generator.source()
        text = (ROOT / "formal/proofs/DeltaReduce/NativeAggregateRoot.lean").read_text("utf-8")
        fields = text.split("def fields ", 1)[1].split("def json ", 1)[0]
        self.assertEqual(re.findall(r'\("([a-z_]+)",', fields), sorted(doc))
        self.assertEqual(len(doc), 18)
        self.assertEqual(content_id(doc), observed["certificates"]["ROOT"]["id"])
        self.assertEqual(generator.body_id(doc), observed["bodies"]["ROOT"])
        self.assertNotEqual(generator.body_id(doc), content_id(doc))

    def test_rehashed_original_body_substitutions_reject(self):
        original = generator.prior.source()
        for field, value in [
            ("leaves", []),
            ("required_keys", []),
            ("merkle_root", "sha256:" + "1" * 64),
            ("aggregation_plan_certificate_id", "sha256:" + "a" * 64),
            ("eligibility_certificate_id", "sha256:" + "b" * 64),
            ("input_set_certificate_id", "sha256:" + "c" * 64),
            ("quorum_threshold", 2),
            ("signer_ids", ["validator-1"]),
            ("view", 1),
            ("round_id", "different"),
        ]:
            changed = copy.deepcopy(original)
            changed[3]["ROOT"][field] = value
            with (
                self.subTest(field=field),
                patch.object(generator.prior, "source", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_original_policy_pin_rejects(self):
        original = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        for name in ["codec-AGGREGATE_ROOT", "codec-APPLY"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == name)
            row["policy_hex"] = row["policy_hex"][:-2] + "ff"
            with (
                self.subTest(name=name),
                patch.object(generator, "load_json_strict", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    generator.source()

    def test_full_leaf_matrix_and_native_parents(self):
        doc, _, _, docs, _, _ = generator.source()
        self.assertEqual(
            doc["leaves"],
            [
                {
                    "domain_id": docs["PARAMETER"]["domain_id"],
                    "shard_id": docs["PARAMETER"]["shard_id"],
                    "parameter_shard_qc_id": content_id(docs["PARAMETER"]),
                }
            ],
        )
        self.assertEqual(
            doc["required_keys"],
            [{k: item[k] for k in ["domain_id", "shard_id"]} for item in doc["leaves"]],
        )
        src = (ROOT / "formal/proofs/DeltaReduce/NativeAggregateLineage.lean").read_text("utf-8")
        for text in [
            "e.id ∈ finalized",
            "shardLeaf e = l",
            "NativeParameter.Valid expected committee",
            "NativeContractSize.contentId sha NativeParameter.domain",
            "c.keys = keys",
            "c.leaves.map NativeAggregateMerkle.key = keys",
        ]:
            self.assertIn(text, src)

    def test_retained_native_merkle_cases(self):
        observed = generator.source()[-1]["merkle_cases"]
        for n in range(1, 5):
            self.assertEqual(merkle_root(generator.sample_leaves(n)), observed[str(n)])
        changed = copy.deepcopy(generator.prior.source())
        changed[-1]["merkle_cases"]["3"] = "sha256:" + "0" * 64
        with patch.object(generator.prior, "source", return_value=changed):
            with self.assertRaises(ValueError):
                generator.source()

    def test_odd_carry_differs_from_duplicate_last(self):
        leaves = generator.sample_leaves(3)

        def hash_id(domain, raw):
            return hashlib.sha256(domain + b"\0" + raw).digest()

        level = [
            hash_id(b"deltareduce.008.aggregate-leaf.v1", canonical_json_bytes(item))
            for item in leaves
        ]
        left = hash_id(b"deltareduce.008.aggregate-node.v1", level[0] + level[1])
        correct = "sha256:" + hash_id(b"deltareduce.008.aggregate-node.v1", left + level[2]).hex()
        duplicate = hash_id(b"deltareduce.008.aggregate-node.v1", level[2] + level[2])
        incorrect = (
            "sha256:" + hash_id(b"deltareduce.008.aggregate-node.v1", left + duplicate).hex()
        )
        self.assertEqual(correct, generator.source()[-1]["merkle_cases"]["3"])
        self.assertNotEqual(correct, incorrect)

    def test_each_leaf_order_and_parent_affects_body(self):
        doc = generator.source()[0]
        for field in ["domain_id", "parameter_shard_qc_id", "shard_id"]:
            changed = copy.deepcopy(doc)
            changed["leaves"][0][field] += "x"
            self.assertNotEqual(generator.body_bytes(changed), generator.body_bytes(doc))
        changed = copy.deepcopy(doc)
        changed["leaves"] = generator.sample_leaves(3)
        reverse = copy.deepcopy(changed)
        reverse["leaves"].reverse()
        self.assertNotEqual(generator.body_bytes(changed), generator.body_bytes(reverse))
        self.assertNotEqual(merkle_root(changed["leaves"]), merkle_root(reverse["leaves"]))

    def test_sized_prior_section_and_root_both_modes(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeAggregateSection.lean").read_text("utf-8")
        for text in [
            "NativeSizedParameterSection.bindSection sha p s",
            "parameters.prior .proposed",
            "parameters.prior .finalized",
            '"aggregate_root_bodies"',
            '"aggregate_root_qcs"',
            '"finalized_aggregate_root_ids"',
        ]:
            self.assertIn(text, src)
        src = (ROOT / "formal/proofs/DeltaReduce/NativeAggregateRoot.lean").read_text("utf-8")
        self.assertIn("NativeContractSize.contentId sha domain (json c)", src)
        merkle = (ROOT / "formal/proofs/DeltaReduce/NativeAggregateMerkle.lean").read_text("utf-8")
        self.assertIn("leaves.length ≤ 100000", merkle)
        self.assertIn("decoderMatchesNativeByte", merkle)

    def test_all_declarations_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in [
            "NativeAggregateMerkle",
            "NativeAggregateRoot",
            "NativeAggregateLineage",
            "NativeAggregateSection",
            "NativeAggregateVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", src, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
