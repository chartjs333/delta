"""Byte/source components only; synthetic IDs are not deployment artifacts."""

import json
import struct
import unittest
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.isc_source.identity import (
    Body,
    Certificate,
    InputTuple,
    body_id,
    body_preimage,
    certificate_bytes,
    certificate_id,
    decode_certificate,
    decode_tuple,
    input_root,
    resolve_body,
    resolve_witness,
    tuple_bytes,
    vote_context_id,
)

ROOT = Path(__file__).resolve().parents[3]


def synthetic_body() -> Body:
    values = (InputTuple("sha256:" + "1" * 64, "sha256:" + "2" * 64, "code", "ticket-001"),)
    return Body(
        "sha256:" + "0" * 64,  # Synthetic sigma parameter, never assigned to deployment.
        "sha256:" + "3" * 64,
        7,
        "sha256:" + "4" * 64,
        "sha256:" + "5" * 64,
        "round-7",
        "sha256:" + "6" * 64,
        2,
        "sha256:" + "7" * 64,
        input_root(values),
        values,
    )


class IdentityTests(unittest.TestCase):
    def test_frozen_fr004_normative_vectors(self):
        source = ROOT / "docs/adr/evidence/0014-isc-commitment-profile-v1-vectors.json"
        vectors = json.loads(source.read_text(encoding="utf-8"))
        leaves = {entry["name"]: InputTuple(**entry["tuple"]) for entry in vectors["leaves"]}
        for entry in vectors["leaves"]:
            self.assertEqual(tuple_bytes(leaves[entry["name"]]), bytes.fromhex(entry["tuple_hex"]))
        for vector in vectors["positive_vectors"]:
            with self.subTest(vector=vector["name"]):
                self.assertEqual(
                    input_root(tuple(leaves[name] for name in vector["tuples"])),
                    vector["input_root"],
                )

    def test_preimage_matches_independent_literal_field_sequence(self):
        value = synthetic_body()

        def text(value):
            raw = value.encode("ascii")
            return struct.pack(">Q", len(raw)) + raw

        expected = text(value.formal_semantics_id) + text("2.0.0")
        expected += text(value.arithmetic_profile_id) + struct.pack(">Q", value.height)
        expected += text(value.parameter_schema_id) + text(value.round_config_id)
        expected += text(value.round_id) + text(value.validator_epoch_id)
        expected += struct.pack(">Q", value.view) + text(value.parent_checkpoint_id)
        expected += text(value.input_root) + struct.pack(">Q", len(value.tuples))
        for row in value.tuples:
            expected += text(row.availability_certificate_id) + text(row.commitment_id)
            expected += text(row.domain_id) + text(row.ticket_id)
        self.assertEqual(body_preimage(value), expected)
        self.assertEqual(
            body_id(value),
            "sha256:" + sha256(b"deltareduce.vote.input-set-body.v2\0" + expected).hexdigest(),
        )
        context = b"deltareduce.vote-context.isc.v1\0" + text(value.round_id)
        self.assertEqual(vote_context_id(value.round_id), "sha256:" + sha256(context).hexdigest())

    def test_parent_changes_signed_body_not_round_anti_equivocation_key(self):
        first = synthetic_body()
        second = replace(first, parent_checkpoint_id="sha256:" + "8" * 64)
        self.assertNotEqual(body_id(first), body_id(second))
        self.assertEqual(vote_context_id(first.round_id), vote_context_id(second.round_id))
        for body in (first, second):
            cert = Certificate(body, ("a", "b", "c"))
            raw = certificate_bytes(cert)
            self.assertIn(body.parent_checkpoint_id.encode("ascii"), raw)
            self.assertEqual(decode_certificate(raw), cert)

    def test_two_original_witnesses_for_one_consensus_body(self):
        body = synthetic_body()
        first = Certificate(body, ("a", "b", "c"))
        second = Certificate(body, ("a", "b", "c", "d"))
        original = (first, second)
        b, c1, c2 = body_id(body), certificate_id(first), certificate_id(second)
        self.assertEqual(len({b, c1, c2}), 3)
        self.assertEqual(resolve_body(b, original), body)
        self.assertEqual(resolve_witness(c1, original), first)
        self.assertEqual(resolve_witness(c2, original), second)
        for wrong in (c1, c2):
            with self.assertRaisesRegex(CodecError, "body identity"):
                resolve_body(wrong, original)
        with self.assertRaisesRegex(CodecError, "witness identity"):
            resolve_witness(b, original)
        # No helper normalizes or collapses the original retained witnesses.
        self.assertEqual(original, (first, second))

    def test_duplicate_members_rejected_before_typed_construction(self):
        raw = tuple_bytes(synthetic_body().tuples[0])
        for inserted in (b'"ticket_id":"ticket-002",', b'"ticket_\\u0069d":"ticket-001",'):
            with self.assertRaisesRegex(CodecError, "REJECT_DUPLICATE_JSON_MEMBER"):
                decode_tuple(b"{" + inserted + raw[1:])
        cert = certificate_bytes(Certificate(synthetic_body(), ("a", "b", "c")))
        malformed = cert.replace(b'"tuples":[{', b'"tuples":[{"ticket_id":"ticket-002",')
        with self.assertRaisesRegex(CodecError, "REJECT_DUPLICATE_JSON_MEMBER"):
            decode_certificate(malformed)

    def test_noncanonical_and_legacy_certificates_rejected(self):
        raw = certificate_bytes(Certificate(synthetic_body(), ("a", "b", "c")))
        mutations = (
            b" " + raw,
            raw + b"\n",
            raw.replace(b'"height":7', b'"height":7.0'),
            raw.replace(b'"height":7', b'"height":true'),
            raw.replace(b'"height":7', b'"height":-1'),
            raw.replace(b'"2.0.0"', b'"1.0.0"'),
            raw.replace(b'"view":2', b'"view":18446744073709551616'),
        )
        for changed in mutations:
            with self.subTest(changed=changed[-70:]), self.assertRaises(CodecError):
                decode_certificate(changed)
        fields = json.loads(raw)
        del fields["parent_checkpoint_id"]
        with self.assertRaises(CodecError):
            decode_certificate(json.dumps(fields).encode())

    def test_root_checks_order_uniqueness_and_all_tuple_fields(self):
        first = synthetic_body().tuples[0]
        second = replace(first, ticket_id="ticket-002")
        for values in ((), (first, first), (second, first)):
            with self.assertRaises(CodecError):
                input_root(values)
        # An alternate commitment for the same ticket is not another eligible position.
        with self.assertRaisesRegex(CodecError, "repeated ticket"):
            input_root((first, replace(first, commitment_id="sha256:" + "9" * 64)))
        for field, value in (
            ("availability_certificate_id", "sha256:" + "8" * 64),
            ("commitment_id", "sha256:" + "8" * 64),
            ("domain_id", "text"),
            ("ticket_id", "ticket-002"),
        ):
            changed = replace(first, **{field: value})
            self.assertNotEqual(input_root((first,)), input_root((changed,)))
        with self.assertRaisesRegex(CodecError, "root mismatch"):
            body_preimage(replace(synthetic_body(), input_root="sha256:" + "f" * 64))


if __name__ == "__main__":
    unittest.main()
