"""Original early-vote payloads versus public shapes and explicit alias limits."""

import copy
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
from check_native_isc_admission import original  # noqa: E402
from native_isc_admission import checked_bodies, context, isc  # noqa: E402

MODULES = [
    "NativeEarlySource",
    "PublicEarlyBody",
    "PublicEarlyHistory",
    "PublicEarlyBodyVectors",
]


class PublicEarlyBodyTests(unittest.TestCase):
    def test_original_isc_identity_and_public_shape_have_different_roots(self):
        policy, state, vote = original()
        body = policy["snapshot"]["input_set_bodies"][0]
        self.assertEqual(checked_bodies(policy, state), [vote["body_hash"]])
        self.assertEqual(isc.from_fields(body).content_id(), vote["body_hash"])
        self.assertEqual(context(policy["round_id"]), vote["context_id"])
        self.assertEqual(body["context"]["height"], int(vote["height"]))
        self.assertEqual(body["context"]["view"], int(vote["view"]))
        self.assertEqual(len(body["tuples"]), 1)
        self.assertEqual(
            set(body["tuples"][0]),
            {"availability_certificate_id", "commitment_id", "domain_id", "ticket_id"},
        )
        tla = (ROOT / "formal/tla/DeltaReduceCertificates.tla").read_text("utf-8")
        definition = tla.split("InputBody(round, config, entries) ==", 1)[1].split(
            "ClosedBodiesFor(round) ==", 1
        )[0]
        self.assertEqual(
            re.findall(r"(\w+)\s*\|->", definition),
            ["round", "config", "policy", "entries", "canonicalRoot"],
        )
        self.assertIn("canonicalRoot |-> entries", definition)
        self.assertNotIn("policy", body)
        self.assertIsInstance(body["input_root"], str)
        self.assertNotEqual(body["input_root"], body["tuples"])

    def test_primitive_content_alias_requires_the_entire_native_source(self):
        policy, _, _ = original()
        original_body = policy["snapshot"]["input_set_bodies"][0]
        before = isc.from_fields(original_body).content_id()

        # A ticket/commitment-only mapping loses availability, domain and root changes.
        def weak(body):
            return [(t["ticket_id"], t["commitment_id"]) for t in body["tuples"]]

        for field, replacement in [
            ("availability_certificate_id", "sha256:" + "9" * 64),
            ("domain_id", "domain-b"),
            ("input_root", "sha256:" + "a" * 64),
        ]:
            changed = copy.deepcopy(original_body)
            if field == "input_root":
                changed[field] = replacement
            else:
                changed["tuples"][0][field] = replacement
            self.assertEqual(weak(changed), weak(original_body))
            self.assertNotEqual(isc.from_fields(changed).content_id(), before)
        # Codec/body identity checks are not signer or public alias authentication.

    def test_all_declarations_imported_and_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(
                r"^(?:def|abbrev|theorem|structure|inductive) ([\w.]+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
