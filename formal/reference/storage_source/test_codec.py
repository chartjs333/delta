"""Real strict crypto on public synthetic data; no production/provenance claim."""

import json
import os
import unittest
from dataclasses import replace
from pathlib import Path

from formal.reference.isc_crypto.codec import CodecError, content_id, encode_key
from formal.reference.isc_crypto.sodium_reference import MAX_MESSAGE_BYTES, SodiumReference
from formal.reference.storage_source.codec import (
    ARTIFACT_DOMAIN,
    COMMON,
    REGISTRY_DOMAIN,
    Bootstrap,
    Context,
    artifact,
    attestation,
    authenticate,
    authenticate_witness,
    bind_registry,
    canonical,
    context,
    load,
    registry,
    signable,
    split_artifact,
)


def identifier(n):
    return "sha256:" + f"{n:064x}"


class StorageSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pin = Path(__file__).resolve().parents[1] / "isc_crypto/library-provenance.json"
        cls.backend = SodiumReference(
            os.environ["ISC_SODIUM_DLL"], json.loads(pin.read_text())["dll"]["sha256"]
        )
        cls.seeds = {f"storage-{n}": bytes([n + 16]) * 32 for n in range(1, 5)}
        cls.keys = tuple(
            (s, cls.backend.sign(seed, b"public synthetic storage fixture")[0])
            for s, seed in cls.seeds.items()
        )
        cls.bootstrap = Bootstrap(identifier(1), identifier(2), "storage-epoch-1", cls.keys)
        r, _ = registry(cls.bootstrap)
        cls.common = {
            "commitment_id": identifier(3),
            "formal_semantics_id": identifier(1),
            "height": "7",
            "origin_id": identifier(2),
            "parent_checkpoint_id": identifier(4),
            "retention_epoch_id": "retention-1",
            "round_config_id": identifier(5),
            "round_id": "round-7",
            "schema_version": "1.0.0",
            "storage_epoch_id": "storage-epoch-1",
            "storage_registry_id": content_id(REGISTRY_DOMAIN, r),
            "ticket_id": "round-7/worker-1/ticket-1",
        }
        cls.value = Context(canonical(cls.common), 3, ((identifier(6), 256), (identifier(7), 512)))

    def body(self, storage="storage-1", leaf=None, overrides=None):
        leaf = self.value.required_leaves[0][0] if leaf is None else leaf
        _, keys = registry(self.bootstrap)
        obj = {
            **self.common,
            "envelope_bytes": str(dict(self.value.required_leaves)[leaf]),
            "key_id": keys[storage][0],
            "leaf_id": leaf,
            "storage_id": storage,
            "type_name": "STORAGE_AVAILABILITY_ATTESTATION",
        }
        obj.update(overrides or {})
        return canonical(obj)

    def signed(self, storage="storage-1", leaf=None, overrides=None):
        body = self.body(storage, leaf, overrides)
        _, signature = self.backend.sign(self.seeds[storage], signable(body))
        return artifact(body, signature)

    def witness(self, pairs=None):
        if pairs is None:
            pairs = [(self.value.required_leaves[0][0], f"storage-{n}") for n in (1, 2, 3)]
            pairs += [(self.value.required_leaves[1][0], f"storage-{n}") for n in (2, 3, 4)]
        inventory = tuple(self.signed(storage, leaf) for leaf, storage in pairs)
        document = {
            **self.common,
            "attestation_ids": [content_id(ARTIFACT_DOMAIN, g) for g in inventory],
            "threshold": "3",
            "type_name": "STORAGE_AVAILABILITY_CERTIFICATE",
        }
        return canonical(document), inventory

    def test_original_registry_key_role_and_complete_key_inventory(self):
        raw, keys = registry(self.bootstrap)
        key_objects = tuple(encode_key(key) for _, key in self.keys)
        self.assertEqual(
            bind_registry(self.bootstrap, raw, key_objects), content_id(REGISTRY_DOMAIN, raw)
        )
        for altered in (
            replace(self.bootstrap, origin_id=identifier(19)),
            replace(self.bootstrap, storage_keys=self.keys[:3]),
        ):
            with self.assertRaises(CodecError):
                bind_registry(altered, raw, key_objects)
        obj = load(raw)
        obj["members"][0]["roles"] = ["validator"]
        with self.assertRaises(CodecError):
            bind_registry(self.bootstrap, canonical(obj), key_objects)
        with self.assertRaises(CodecError):
            bind_registry(self.bootstrap, raw, key_objects[:-1])
        with self.assertRaises(CodecError):
            registry(
                replace(self.bootstrap, storage_keys=(self.keys[0], ("storage-2", self.keys[0][1])))
            )
        self.assertNotEqual(
            keys["storage-1"][0], content_id("deltareduce.isc-ed25519-key.v1", key_objects[0])
        )

    def test_exact_byte_domains_and_deterministic_signature(self):
        body = self.body()
        g = self.signed()
        self.assertEqual(
            signable(body),
            b"deltareduce.storage-attestation.ed25519.v1\0" + len(body).to_bytes(4, "big") + body,
        )
        self.assertEqual(g[:12], b"SAG1\0\1\0\0" + len(body).to_bytes(4, "big"))
        self.assertEqual(split_artifact(g)[0], body)
        self.assertEqual(self.signed(), g)
        verified = authenticate(self.bootstrap, self.backend, self.value, g)
        self.assertEqual(verified.original_artifact, g)
        self.assertEqual(verified.artifact_id, content_id(ARTIFACT_DOMAIN, g))
        self.assertNotEqual(verified.body_id, verified.artifact_id)

    def test_maximum_legal_attestation_fits_existing_strict_primitive(self):
        body = self.body(
            overrides={
                "height": str(2**64 - 1),
                "envelope_bytes": str(2**64 - 1),
                "ticket_id": "t" * 255,
                **{
                    k: "x" * 128
                    for k in ("round_id", "storage_id", "storage_epoch_id", "retention_epoch_id")
                },
            }
        )
        self.assertLessEqual(len(signable(body)), MAX_MESSAGE_BYTES)
        _, signature = self.backend.sign(self.seeds["storage-1"], signable(body))
        self.assertEqual(len(signature), 64)

    def test_duplicate_keys_numeric_values_and_noncanonical_bytes_fail_before_typing(self):
        body = self.body()
        cases = [
            b'{"ticket_id":"old",' + body[1:],
            body + b"\n",
            b" " + body,
            body.replace(b'"height":"7"', b'"height":7'),
            body.replace(b'"ticket_id":', b'"ticket\\u005fid":'),
            body.replace(b'"height":"7"', b'"height":"07"'),
        ]
        for raw in cases:
            with self.subTest(raw=raw[:30]), self.assertRaises(CodecError):
                attestation(raw)
        duplicate_escaped = b'{"ticket\\u005fid":"old",' + body[1:]
        with self.assertRaisesRegex(CodecError, "duplicate JSON member"):
            attestation(duplicate_escaped)

    def test_trailing_bytes_version_signature_and_wrong_domain_reject(self):
        g = self.signed()
        body, sig = split_artifact(g)
        for bad in (g + b"x", g[:6] + b"\0\1" + g[8:], g[:11] + bytes([g[11] ^ 1]) + g[12:]):
            with self.assertRaises(CodecError):
                split_artifact(bad)
        for message in (b"NSG1" + signable(body), body):
            _, wrong = self.backend.sign(self.seeds["storage-1"], message)
            with self.assertRaisesRegex(CodecError, "Ed25519"):
                authenticate(self.bootstrap, self.backend, self.value, artifact(body, wrong))
        with self.assertRaisesRegex(CodecError, "Ed25519"):
            authenticate(
                self.bootstrap,
                self.backend,
                self.value,
                artifact(body, sig[:-1] + bytes([sig[-1] ^ 1])),
            )

    def test_authentic_wrong_context_leaf_length_retention_key_and_source_reject(self):
        substitutions = {
            k: identifier(99)
            for k in (
                "parent_checkpoint_id",
                "round_config_id",
                "origin_id",
                "formal_semantics_id",
                "commitment_id",
                "leaf_id",
                "key_id",
                "storage_registry_id",
            )
        }
        substitutions.update(
            {
                "envelope_bytes": "255",
                "storage_epoch_id": "later",
                "retention_epoch_id": "later",
                "height": "8",
                "round_id": "later",
                "ticket_id": "other",
                "storage_id": "storage-2",
            }
        )
        for key, value in substitutions.items():
            with self.subTest(key=key), self.assertRaises(CodecError):
                authenticate(
                    self.bootstrap, self.backend, self.value, self.signed(overrides={key: value})
                )

    def test_per_leaf_different_quorums_and_full_occurrence_inventory(self):
        d, inventory = self.witness()
        retained = (*inventory, inventory[0], b"original invalid delivered bytes")
        result = authenticate_witness(self.bootstrap, self.backend, self.value, d, retained)
        self.assertEqual(result.original_inventory, retained)
        self.assertEqual(len(result.witness), 6)
        self.assertEqual(result.attester_ids, tuple(s for s, _ in self.keys))
        self.assertEqual(result.covered_leaf_ids, tuple(k for k, _ in self.value.required_leaves))
        self.assertEqual(result.threshold, 3)

    def test_union_quorum_duplicate_inflation_missing_or_reordered_pairs_reject(self):
        a, b = (k for k, _ in self.value.required_leaves)
        cases = [
            [(a, "storage-1"), (a, "storage-2"), (b, "storage-3")],
            [(a, "storage-1")] * 3 + [(b, "storage-2")] * 3,
        ]
        for pairs in cases:
            d, inventory = self.witness(pairs)
            with self.assertRaises(CodecError):
                authenticate_witness(self.bootstrap, self.backend, self.value, d, inventory)
        d, inventory = self.witness()
        obj = load(d)
        obj["attestation_ids"].reverse()
        with self.assertRaises(CodecError):
            authenticate_witness(
                self.bootstrap, self.backend, self.value, canonical(obj), inventory
            )
        with self.assertRaises(CodecError):
            authenticate_witness(self.bootstrap, self.backend, self.value, d, inventory[:-1])

    def test_distinct_actual_witnesses_keep_distinct_ac_and_never_replace_original(self):
        d, inventory = self.witness()
        pairs = [
            (leaf, f"storage-{n}") for leaf, _ in self.value.required_leaves for n in (1, 2, 3, 4)
        ]
        other, extra = self.witness(pairs)
        original = authenticate_witness(
            self.bootstrap, self.backend, self.value, d, inventory + extra
        )
        alternate = authenticate_witness(
            self.bootstrap, self.backend, self.value, other, inventory + extra
        )
        self.assertNotEqual(original.certificate_id, alternate.certificate_id)
        self.assertEqual(original.original_certificate, d)
        self.assertEqual(original.original_inventory, alternate.original_inventory)

    def test_false_physical_claims_authenticate_without_creating_physical_truth(self):
        # O intentionally has no physical inventory/presence input at this boundary.
        d, inventory = self.witness()
        result = authenticate_witness(self.bootstrap, self.backend, self.value, d, inventory)
        self.assertEqual(result.original_certificate, d)
        self.assertFalse(hasattr(result, "available_artifacts"))
        self.assertFalse(hasattr(result, "usable_bytes"))
        self.assertEqual(set(context(self.bootstrap, self.value)), COMMON)


if __name__ == "__main__":
    unittest.main()
