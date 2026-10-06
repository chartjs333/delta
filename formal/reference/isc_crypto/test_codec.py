"""Public synthetic codec conformance; no fixture assigns deployment semantics."""

import copy
import json
import struct
import unittest
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto.codec import (
    ARTIFACT_DOMAIN,
    EVIDENCE_DOMAIN,
    KEY_DOMAIN,
    M_DOMAIN,
    MAX_ARTIFACT_BYTES,
    MAX_CONTROL_BYTES,
    MAX_PREIMAGE_BYTES,
    MAX_VOTE_BYTES,
    REGISTRY_DOMAIN,
    VOTE_DOMAIN,
    Artifact,
    CodecError,
    Vote,
    content_id,
    decode_artifact,
    decode_evidence,
    decode_key,
    decode_preimage,
    decode_registry,
    decode_vote,
    encode_artifact,
    encode_evidence,
    encode_key,
    encode_registry,
    encode_vote,
    preimage,
)

# This zero digest is a test parameter, never a selected or derived sigma.
SYNTHETIC_SIGMA = "sha256:" + "0" * 64
SYNTHETIC_EPOCH = "sha256:" + "e" * 64


def synthetic_vote() -> Vote:
    return Vote(
        "sha256:" + "b" * 64,
        "isc:round-7",
        4,
        SYNTHETIC_SIGMA,
        7,
        "round-7",
        SYNTHETIC_EPOCH,
        "validator-1",
        2,
    )


def literal_vote_fields() -> dict[str, str]:
    return {
        "body_hash": "sha256:" + "b" * 64,
        "context_id": "isc:round-7",
        "durable_sequence": "4",
        "formal_semantics_id": SYNTHETIC_SIGMA,
        "height": "7",
        "kind": "ISC",
        "round_id": "round-7",
        "schema_version": "2.0.0",
        "type_name": "VOTE",
        "validator_epoch_id": SYNTHETIC_EPOCH,
        "validator_id": "validator-1",
        "view": "2",
    }


def independent_vote(fields: list[tuple[str, str]]) -> bytes:
    def txt(text: str) -> bytes:
        raw = text.encode("ascii")
        return b"\x21" + struct.pack(">I", len(raw)) + raw

    payload = b"\x31" + struct.pack(">I", len(fields))
    payload += b"".join(txt(key) + txt(value) for key, value in fields)
    return struct.pack(">4sBBHI", b"DRC1", 1, 0, 3, len(payload)) + payload


def independent_json(document: object) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode("ascii")


def synthetic_registry() -> tuple[dict, dict[str, bytes], bytes]:
    evidence = encode_evidence(SYNTHETIC_SIGMA)
    keys = {}
    validators = []
    for index in range(1, 5):
        # Byte-codec-only values: these are not claimed to be valid curve points.
        key = encode_key(bytes([index]) * 32)
        key_id = content_id(KEY_DOMAIN, key)
        keys[key_id] = key
        validators.append(
            {"key_ref": key_id, "roles": ["validator"], "validator_id": f"validator-{index}"}
        )
    registry = {
        "evidence_budget_id": content_id(EVIDENCE_DOMAIN, evidence),
        "formal_semantics_id": SYNTHETIC_SIGMA,
        "origin_id": "synthetic-origin",
        "quorum_threshold": "3",
        "schema_version": "1.0.0",
        "signature_profile": "SIG-ISC-ED25519-v1",
        "validator_epoch_id": SYNTHETIC_EPOCH,
        "validators": validators,
    }
    return registry, keys, evidence


class CodecTests(unittest.TestCase):
    def test_key_exact_json_and_domain(self) -> None:
        key = bytes(range(32))
        expected = (
            b'{"algorithm":"Ed25519","public_key_hex":"'
            b"000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
            b'","schema_version":"1.0.0"}'
        )
        self.assertEqual(encode_key(key), expected)
        self.assertEqual(decode_key(expected), key)
        expected_id = "sha256:" + sha256(b"deltareduce.isc-ed25519-key.v1\0" + expected).hexdigest()
        self.assertEqual(content_id(KEY_DOMAIN, expected), expected_id)

    def test_key_length_hex_algorithm_schema_and_closed_fields(self) -> None:
        for length in (0, 31, 33):
            with self.subTest(length=length), self.assertRaises(CodecError):
                encode_key(b"k" * length)
        original = json.loads(encode_key(b"k" * 32))
        for field, value in (
            ("algorithm", "Ed25519ph"),
            ("schema_version", "2.0.0"),
            ("public_key_hex", "AB" * 32),
            ("public_key_hex", "g" * 64),
            ("public_key_hex", "0" * 63),
        ):
            document = {**original, field: value}
            with self.subTest(field=field, value=value), self.assertRaises(CodecError):
                decode_key(independent_json(document))
        for document in ({**original, "key_id": "self"}, {"algorithm": "Ed25519"}):
            with self.assertRaises(CodecError):
                decode_key(independent_json(document))

    def test_control_json_canonical_and_duplicate_rejection(self) -> None:
        original = encode_key(b"k" * 32)
        alternatives = (
            original + b"\n",
            b" " + original,
            b"\xef\xbb\xbf" + original,
            original.replace(b"Ed25519", b"Ed2551\\u0039"),
            original.replace(b'{"algorithm":', b'{"algorithm":"Ed25519","algorithm":'),
            original.replace(b'"algorithm":"Ed25519"', b'"algorithm":null'),
            original.replace(b'"algorithm":"Ed25519"', b'"algorithm":true'),
            original.replace(b'"algorithm":"Ed25519"', b'"algorithm":1'),
            original.replace(b'"algorithm":"Ed25519"', b'"algorithm":1.0'),
            original.replace(b'"algorithm":"Ed25519"', b'"algorithm":NaN'),
            original.replace(b'"algorithm":"Ed25519"', b'"algorithm":"\xc3\xa9"'),
        )
        for changed in alternatives:
            with self.subTest(changed=changed), self.assertRaises(CodecError):
                decode_key(changed)
        with self.assertRaises(CodecError):
            decode_key(b"x" * (MAX_CONTROL_BYTES + 1))

    def test_fixed_evidence_exact_values_and_all_changed_budget_rejection(self) -> None:
        expected = {
            "formal_semantics_id": SYNTHETIC_SIGMA,
            "profile_id": "ISC-EVIDENCE-BUDGET-v1",
            "schema_version": "1.0.0",
            "max_delivery_events": "4096",
            "max_delivery_bytes": "33554432",
            "max_vote_bytes": "4096",
            "max_vote_frame_bytes": "4096",
            "max_signature_artifact_bytes": "4322",
            "max_signed_payload_bytes": "4282",
            "max_peer_id_bytes": "128",
            "signature_bytes": "64",
            "key_id_bytes": "71",
            "max_command_bytes": "65536",
            "max_round_state_bytes": "65536",
            "max_policy_bytes": "4194304",
            "max_isc_bytes": "4194304",
            "max_effect_bytes": "1048576",
            "max_wal_frame_bytes": "67108864",
            "max_output_bytes": "16777216",
            "max_result_metadata_bytes": "8192",
        }
        self.assertEqual(encode_evidence(SYNTHETIC_SIGMA), independent_json(expected))
        self.assertEqual(decode_evidence(independent_json(expected)), expected)
        for field in expected:
            changed = {**expected, field: "wrong"}
            with self.subTest(field=field), self.assertRaises(CodecError):
                decode_evidence(independent_json(changed))
        for value in (4096, "04096", "+4096", "4096 "):
            with self.subTest(value=value), self.assertRaises(CodecError):
                decode_evidence(independent_json({**expected, "max_vote_bytes": value}))
        for changed in (
            {**expected, "evidence_id": "self"},
            {key: value for key, value in expected.items() if key != "signature_bytes"},
        ):
            with self.assertRaises(CodecError):
                decode_evidence(independent_json(changed))

    def test_registry_exact_json_round_trip_and_linkage(self) -> None:
        registry, keys, evidence = synthetic_registry()
        encoded = encode_registry(registry, keys=keys, evidence=evidence)
        self.assertEqual(encoded, independent_json(registry))
        self.assertEqual(decode_registry(encoded, keys=keys, evidence=evidence), registry)
        for domain in (EVIDENCE_DOMAIN, REGISTRY_DOMAIN, VOTE_DOMAIN, ARTIFACT_DOMAIN):
            self.assertEqual(
                content_id(domain, encoded),
                "sha256:" + sha256(domain.encode() + b"\0" + encoded).hexdigest(),
            )
        self.assertEqual(
            len(
                {
                    content_id(domain, encoded)
                    for domain in (
                        KEY_DOMAIN,
                        EVIDENCE_DOMAIN,
                        REGISTRY_DOMAIN,
                        VOTE_DOMAIN,
                        ARTIFACT_DOMAIN,
                    )
                }
            ),
            5,
        )

    def test_registry_rejects_wrong_profiles_bindings_roles_and_members(self) -> None:
        registry, keys, evidence = synthetic_registry()
        for field, value in (
            ("formal_semantics_id", "sha256:" + "1" * 64),
            ("evidence_budget_id", "sha256:" + "2" * 64),
            ("signature_profile", "other"),
            ("quorum_threshold", "2"),
            ("schema_version", "2.0.0"),
            ("validator_epoch_id", "epoch-1"),
            ("origin_id", "bad origin"),
        ):
            with self.subTest(field=field), self.assertRaises(CodecError):
                encode_registry({**registry, field: value}, keys=keys, evidence=evidence)
        for role in ([], ["storage"], ["validator", "storage"], "validator"):
            edited = copy.deepcopy(registry)
            edited["validators"][0]["roles"] = role
            with self.subTest(role=role), self.assertRaises(CodecError):
                encode_registry(edited, keys=keys, evidence=evidence)
        for edited in (
            {**registry, "extra": "x"},
            {key: value for key, value in registry.items() if key != "origin_id"},
        ):
            with self.assertRaises(CodecError):
                encode_registry(edited, keys=keys, evidence=evidence)

    def test_registry_rejects_duplicate_unsorted_count_and_key_reuse(self) -> None:
        registry, keys, evidence = synthetic_registry()
        for entries in (
            registry["validators"][:3],
            registry["validators"] * 2,
            registry["validators"][::-1],
            [registry["validators"][0]] * 4,
        ):
            with self.subTest(entries=entries), self.assertRaises(CodecError):
                encode_registry({**registry, "validators": entries}, keys=keys, evidence=evidence)
        edited = copy.deepcopy(registry)
        edited["validators"][1]["key_ref"] = edited["validators"][0]["key_ref"]
        with self.assertRaisesRegex(CodecError, "duplicate.*key"):
            encode_registry(edited, keys=keys, evidence=evidence)
        with self.assertRaisesRegex(CodecError, "unavailable"):
            encode_registry(registry, keys={}, evidence=evidence)
        changed_keys = dict(keys)
        changed_keys[next(iter(keys))] = encode_key(b"z" * 32)
        with self.assertRaisesRegex(CodecError, "reference mismatch"):
            encode_registry(registry, keys=changed_keys, evidence=evidence)
        encoded = encode_registry(registry, keys=keys, evidence=evidence)
        doubled = encoded.replace(
            b'"roles":["validator"]', b'"roles":["validator"],"roles":["validator"]', 1
        )
        with self.assertRaises(CodecError):
            decode_registry(doubled, keys=keys, evidence=evidence)

    def test_vote_exact_struct_encoding_and_domain(self) -> None:
        expected = independent_vote(list(literal_vote_fields().items()))
        actual = encode_vote(synthetic_vote())
        self.assertEqual(actual, expected)
        self.assertEqual(decode_vote(actual), synthetic_vote())
        self.assertEqual(
            content_id(VOTE_DOMAIN, actual),
            "sha256:" + sha256(b"deltareduce:003:vote:v2\0" + actual).hexdigest(),
        )

    def test_vote_unknown_duplicate_missing_reordered_old_signature_field(self) -> None:
        fields = list(literal_vote_fields().items())
        alternatives = (
            fields[:-1],
            [*fields, ("signature_id", "sha256:" + "f" * 64)],
            fields[:1] + fields,
            fields[::-1],
            [("unknown", fields[0][1]), *fields[1:]],
        )
        for changed in alternatives:
            with self.subTest(changed=changed), self.assertRaises(CodecError):
                decode_vote(independent_vote(changed))

    def test_vote_dispatch_canonical_decimals_and_content_ids(self) -> None:
        original = literal_vote_fields()
        changes = [
            (field, text)
            for field in ("durable_sequence", "height", "view")
            for text in ("-1", "+1", "00", "01", "1 ", str(1 << 64))
        ]
        changes += [
            ("durable_sequence", "0"),
            ("kind", "APPLY"),
            ("schema_version", "1.0.0"),
            ("type_name", "VOTES"),
        ]
        changes += [
            (field, text)
            for field in ("body_hash", "formal_semantics_id", "validator_epoch_id")
            for text in ("sha256:" + "A" * 64, "sha256:" + "a" * 63, "epoch")
        ]
        for field, text in changes:
            changed = {**original, field: text}
            with self.subTest(field=field, text=text), self.assertRaises(CodecError):
                decode_vote(independent_vote(list(changed.items())))

    def test_integer_and_label_boundaries(self) -> None:
        original = synthetic_vote()
        maximum = replace(
            original,
            height=(1 << 64) - 1,
            view=(1 << 64) - 1,
            durable_sequence=(1 << 64) - 1,
            context_id="c" * 128,
            round_id="r" * 128,
            validator_id="v" * 128,
        )
        self.assertEqual(decode_vote(encode_vote(maximum)), maximum)
        self.assertEqual(decode_vote(encode_vote(replace(original, height=0, view=0))).height, 0)
        for field in ("durable_sequence", "height", "view"):
            for value in (-1, 1 << 64, True):
                with self.subTest(field=field, value=value), self.assertRaises(CodecError):
                    encode_vote(replace(original, **{field: value}))
        for field in ("context_id", "round_id", "validator_id"):
            for text in ("", "x" * 129, "é", "bad/name", "space here", 'quote"'):
                with self.subTest(field=field, text=text), self.assertRaises(CodecError):
                    encode_vote(replace(original, **{field: text}))

    def test_vote_header_lengths_tags_and_truncation(self) -> None:
        wire = encode_vote(synthetic_vote())
        for offset in (0, 4, 5, 6, 7, 11, 12, 16, 17):
            changed = bytearray(wire)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(CodecError):
                decode_vote(bytes(changed))
        for length in range(len(wire)):
            with self.subTest(length=length), self.assertRaises(CodecError):
                decode_vote(wire[:length])
        with self.assertRaises(CodecError):
            decode_vote(wire + b"x")
        for size in (MAX_VOTE_BYTES - 1, MAX_VOTE_BYTES, MAX_VOTE_BYTES + 1):
            with self.subTest(size=size), self.assertRaises(CodecError):
                decode_vote(wire + b"x" * (size - len(wire)))
        # A valid vote cannot be padded to the cap: strict fields/re-encoding still apply.
        bad = bytearray(wire)
        bad[18:22] = b"\xff\xff\xff\xff"
        with self.assertRaises(CodecError):
            decode_vote(bytes(bad))

    def test_preimage_and_artifact_exact_literal_layout(self) -> None:
        vote = encode_vote(synthetic_vote())
        registry_id, key_id = "sha256:" + "a" * 64, "sha256:" + "d" * 64
        tail = struct.pack(">I", 71) + registry_id.encode("ascii")
        tail += struct.pack(">I", 71) + key_id.encode("ascii")
        tail += struct.pack(">I", len(vote)) + vote
        message = preimage(registry_id, key_id, vote)
        self.assertEqual(message, b"deltareduce.isc-vote.ed25519.v1\0" + tail)
        self.assertEqual(len(message), 186 + len(vote))
        self.assertEqual(decode_preimage(message), (registry_id, key_id, vote))
        artifact = Artifact(registry_id, key_id, vote, bytes(range(64)))
        encoded = encode_artifact(artifact)
        self.assertEqual(encoded, b"ISG1\x00\x01\x00\x00" + tail + bytes(range(64)))
        self.assertEqual(len(encoded), 226 + len(vote))
        self.assertEqual(decode_artifact(encoded), artifact)
        self.assertEqual(
            content_id(ARTIFACT_DOMAIN, encoded),
            "sha256:" + sha256(b"deltareduce.isc-signature.v1\0" + encoded).hexdigest(),
        )
        self.assertEqual(M_DOMAIN, "deltareduce.isc-vote.ed25519.v1")

    def test_artifact_and_preimage_malformed_rejected(self) -> None:
        vote = encode_vote(synthetic_vote())
        artifact = Artifact("sha256:" + "a" * 64, "sha256:" + "d" * 64, vote, b"s" * 64)
        message, wire = (
            preimage(artifact.registry_id, artifact.key_id, vote),
            encode_artifact(artifact),
        )
        for original, decoder, cap in (
            (message, decode_preimage, MAX_PREIMAGE_BYTES),
            (wire, decode_artifact, MAX_ARTIFACT_BYTES),
        ):
            for length in range(len(original)):
                with self.subTest(decoder=decoder.__name__, length=length):
                    with self.assertRaises(CodecError):
                        decoder(original[:length])
            for changed in (original + b"x", b"?" + original[1:], b"x" * (cap + 1)):
                with self.assertRaises(CodecError):
                    decoder(changed)
        for offset in (4, 5, 6, 7):
            changed = bytearray(wire)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(CodecError):
                decode_artifact(bytes(changed))
        for length in (0, 63, 65):
            with self.subTest(length=length), self.assertRaises(CodecError):
                encode_artifact(replace(artifact, signature=b"s" * length))
        changed = bytearray(wire)
        changed[8:12] = b"\xff\xff\xff\xff"
        with self.assertRaises(CodecError):
            decode_artifact(bytes(changed))

    def test_byte_identity_and_parsing_are_not_authority(self) -> None:
        vote = encode_vote(synthetic_vote())
        # Structurally valid substitutions change M/G but require the separately
        # pinned registry/signature/body/source verifier to establish meaning.
        first = Artifact("sha256:" + "a" * 64, "sha256:" + "d" * 64, vote, b"\0" * 64)
        second = replace(first, registry_id="sha256:" + "c" * 64)
        self.assertNotEqual(
            preimage(first.registry_id, first.key_id, vote),
            preimage(second.registry_id, second.key_id, vote),
        )
        self.assertEqual(decode_artifact(encode_artifact(first)), first)
        self.assertNotEqual(
            content_id(ARTIFACT_DOMAIN, encode_artifact(first)),
            content_id(ARTIFACT_DOMAIN, encode_artifact(second)),
        )


if __name__ == "__main__":
    unittest.main()
