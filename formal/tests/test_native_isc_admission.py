"""ISC admission subdomain: source-bound computation and explicit trust limits."""

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_native_isc_admission as cases
import generate_native_isc_admission as vectors
import native_isc_admission as checker
import native_policy_codec as codec

ROOT = Path(__file__).resolve().parents[2]


class IscAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((cases.FOLDER / "cpp-cross-check.json").read_text(encoding="utf-8"))
        cls.rows = {r["name"]: r for r in cls.doc["observed"]}

    def test_all_native_cases(self):
        cases.verify_document(self.doc)
        self.assertEqual(len(self.rows), 60)
        self.assertEqual(sum(r["native"]["startup"] for r in self.rows.values()), 26)
        self.assertEqual(sum(r["native"]["admitted"] for r in self.rows.values()), 14)

    def test_every_retained_input_recomputed(self):
        for row in self.rows.values():
            self.assertEqual(cases.outcome(row), row["computed"], row["name"])

    def test_full_policy_fields_not_optional(self):
        p, _, _ = cases.original()
        for field in p["snapshot"]:
            changed = copy.deepcopy(p)
            del changed["snapshot"][field]
            with self.assertRaises(ValueError, msg=field):
                codec.encode(changed)
        for field in p["snapshot"]["input_set_bodies"][0]:
            changed = copy.deepcopy(p)
            del changed["snapshot"]["input_set_bodies"][0][field]
            with self.assertRaises(ValueError, msg=field):
                codec.encode(changed)

    def test_complete_context_rejects_after_rehash(self):
        for name, row in self.rows.items():
            if name.startswith("context-"):
                self.assertEqual(row["computed"], dict(startup=False, admitted=False), name)

    def test_root_and_source_provenance_are_not_inferred(self):
        for name in [
            "rebound-root",
            "rehashed-state-root",
            "rebound-primitive-commitment_id",
            "rebound-primitive-availability_certificate_id",
        ]:
            self.assertTrue(self.rows[name]["native"]["admitted"], name)
        self.assertFalse(self.rows["unbound-root"]["native"]["admitted"])
        self.assertFalse(self.doc["native_export_authenticated"])
        self.assertFalse(self.doc["gate_eligible"])

    def test_native_tuple_order_is_pair_not_ticket_uniqueness(self):
        self.assertTrue(self.rows["same-ticket-different-commitment"]["computed"]["admitted"])
        for name in [
            "duplicate-tuples",
            "reverse-tuples",
            "reverse-bodies",
            "duplicated-body",
            "extra-unclosed-invalid-body",
        ]:
            self.assertFalse(self.rows[name]["computed"]["startup"], name)
        self.assertTrue(self.rows["extra-unclosed-valid-body"]["computed"]["startup"])

    def test_missing_finalized_config_is_not_invented(self):
        self.assertTrue(self.rows["no-finalized-config"]["computed"]["admitted"])
        self.assertTrue(self.rows["no-proposed-config"]["computed"]["admitted"])
        row = self.rows["nonempty-abort-graph-unsupported"]
        self.assertTrue(row["native"]["startup"])
        self.assertFalse(row["computed"]["startup"])

    def test_readiness_and_sequence(self):
        self.assertTrue(self.rows["recovery-not-ready"]["computed"]["admitted"])
        for name in ["not-ready", "recovery-invalidated", "deadline", "vote-durable_sequence"]:
            self.assertFalse(self.rows[name]["computed"]["admitted"], name)

    def test_result_and_scope_substitution_reject(self):
        for field, value in [
            ("gate_eligible", True),
            ("source_commit", "0" * 40),
            ("harness_sha256", "0" * 64),
        ]:
            bad = copy.deepcopy(self.doc)
            bad[field] = value
            with self.assertRaises(ValueError):
                cases.verify_document(bad)
        for field in ["native", "computed"]:
            bad = copy.deepcopy(self.doc)
            bad["observed"][0][field]["admitted"] = False
            with self.assertRaises(ValueError):
                cases.verify_document(bad)
        bad = copy.deepcopy(self.doc)
        bad["observed"].pop()
        with self.assertRaises(ValueError):
            cases.verify_document(bad)

    def test_vectors_byte_exact(self):
        path = ROOT / "formal/proofs/DeltaReduce/NativeIscAdmissionVectors.lean"
        before = path.read_bytes()
        vectors.generate()
        self.assertEqual(path.read_bytes(), before)
        text = before.decode()
        for theorem in [
            "inputEncoded",
            "inputHash",
            "originalBinding",
            "originalAllBytes",
            "sameTicketDifferentCommitmentAllowed",
        ]:
            self.assertIn("theorem " + theorem, text)

    def test_proposed_body_id_uses_original_preimage(self):
        p, s, _ = cases.original()
        body = checker.isc.from_fields(p["snapshot"]["input_set_bodies"][0])
        expected = "sha256:" + hashlib.sha256(checker.isc.DOMAIN + body.encode()).hexdigest()
        self.assertEqual(expected, p["candidates"][0]["body_hash"])
        self.assertEqual(checker.checked_bodies(p, s), [expected])


if __name__ == "__main__":
    unittest.main()
