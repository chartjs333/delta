"""Real strict Ed25519 over synthetic source-shaped bytes, never a production capture."""

import json
import os
import unittest
from dataclasses import replace
from pathlib import Path

from formal.reference.isc_crypto.codec import (
    Artifact,
    CodecError,
    Vote,
    decode_artifact,
    encode_artifact,
    encode_vote,
    preimage,
)
from formal.reference.isc_crypto.sodium_reference import SodiumReference
from formal.reference.isc_source.authentication import (
    Bootstrap,
    authenticate,
    bind_delivery,
    delivered_signers,
    registry,
)
from formal.reference.isc_source.identity import body_id, vote_context_id
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.isc_w1.codec import Delivery


class AuthenticationTests(unittest.TestCase):
    def test_opaque_success_callback_is_not_signature_authority(self):
        class AcceptAll:
            def verify(self, key, message, signature):
                return True

        signer = next(iter(self.seeds))
        raw = self.signed(signer)
        with self.assertRaisesRegex(CodecError, "concrete pinned strict Ed25519"):
            authenticate(self.bootstrap, AcceptAll(), raw, self.body)

    @classmethod
    def setUpClass(cls):
        directory = Path(__file__).resolve().parents[1] / "isc_crypto"
        provenance = json.loads((directory / "library-provenance.json").read_text())
        fixture = json.loads((directory / "public-vector.json").read_text())
        configured = os.environ.get("ISC_SODIUM_DLL")
        if not configured:
            raise RuntimeError("ISC_SODIUM_DLL required; no callback or skip fallback")
        cls.backend = SodiumReference(configured, provenance["dll"]["sha256"])
        cls.body = synthetic_body()
        cls.seeds = {
            entry["validator_id"]: bytes.fromhex(entry["public_test_seed_hex"])
            for entry in fixture["keys"]
        }
        cls.bootstrap = Bootstrap(
            cls.body.formal_semantics_id,
            "synthetic-origin",
            cls.body.validator_epoch_id,
            tuple(
                (entry["validator_id"], bytes.fromhex(entry["public_key_hex"]))
                for entry in fixture["keys"]
            ),
        )

    def signed(self, validator, body=None, slot=2):
        body = self.body if body is None else body
        registry_id, validators = registry(self.bootstrap)
        key_id, public = validators[validator]
        vote = Vote(
            body_id(body),
            vote_context_id(body.round_id),
            slot,
            body.formal_semantics_id,
            body.height,
            body.round_id,
            body.validator_epoch_id,
            validator,
            body.view,
        )
        raw = encode_vote(vote)
        actual, signature = self.backend.sign(
            self.seeds[validator], preimage(registry_id, key_id, raw)
        )
        self.assertEqual(actual, public)
        return encode_artifact(Artifact(registry_id, key_id, raw, signature))

    def test_all_matching_original_signers_with_repeats_and_conflicts(self):
        validators = tuple(self.seeds)
        raw = [self.signed(validator) for validator in validators]
        verified = tuple(authenticate(self.bootstrap, self.backend, g, self.body) for g in raw)
        self.assertEqual(delivered_signers(self.body, verified[:3]), validators[:3])
        self.assertEqual(delivered_signers(self.body, verified[::-1] + verified[:2]), validators)
        # Retain a conflicting authenticated body instead of deleting its evidence.
        other = replace(self.body, parent_checkpoint_id="sha256:" + "8" * 64)
        conflict = authenticate(
            self.bootstrap, self.backend, self.signed(validators[3], other), other
        )
        inventory = (*verified[:3], conflict, verified[0])
        self.assertEqual(delivered_signers(self.body, inventory), validators[:3])
        self.assertEqual(len(inventory), 5)
        self.assertEqual(verified[0].vote.durable_sequence, 2)
        later = authenticate(
            self.bootstrap, self.backend, self.signed(validators[0], slot=4), self.body
        )
        self.assertNotEqual(later.vote_id, verified[0].vote_id)
        # Authentication does not bless two votes as legal local producer history.
        self.assertEqual(delivered_signers(self.body, (verified[0], later)), validators[:1])

    def test_registry_is_not_selected_by_imported_artifact(self):
        validator = next(iter(self.seeds))
        raw = self.signed(validator)
        with self.assertRaisesRegex(CodecError, "registry"):
            authenticate(
                replace(self.bootstrap, origin_id="foreign-origin"), self.backend, raw, self.body
            )
        changed = replace(decode_artifact(raw), registry_id="sha256:" + "f" * 64)
        with self.assertRaisesRegex(CodecError, "registry"):
            authenticate(self.bootstrap, self.backend, encode_artifact(changed), self.body)

    def test_parent_and_signature_cannot_be_substituted(self):
        validator = next(iter(self.seeds))
        raw = self.signed(validator)
        with self.assertRaisesRegex(CodecError, "body/context"):
            authenticate(
                self.bootstrap,
                self.backend,
                raw,
                replace(self.body, parent_checkpoint_id="sha256:" + "8" * 64),
            )
        artifact = decode_artifact(raw)
        altered = replace(
            artifact, signature=artifact.signature[:-1] + bytes([artifact.signature[-1] ^ 1])
        )
        with self.assertRaisesRegex(CodecError, "Ed25519"):
            authenticate(self.bootstrap, self.backend, encode_artifact(altered), self.body)

    def test_w1_duplicate_fields_bind_exact_original_g(self):
        raw = self.signed(next(iter(self.seeds)))
        value = authenticate(self.bootstrap, self.backend, raw, self.body)
        artifact = decode_artifact(raw)
        delivery = Delivery(
            17,
            "relay-peer",
            artifact.vote_bytes,
            preimage(artifact.registry_id, artifact.key_id, artifact.vote_bytes),
            artifact.signature,
            artifact.key_id,
        )
        bind_delivery(value, delivery)
        for changed in (
            replace(delivery, vote_frame=delivery.vote_frame + b"x"),
            replace(delivery, signed_payload=delivery.vote_frame),
            replace(delivery, signature_bytes=bytes(64)),
            replace(delivery, key_id="sha256:" + "f" * 64),
        ):
            with self.assertRaisesRegex(CodecError, "W1 delivery"):
                bind_delivery(value, changed)


if __name__ == "__main__":
    unittest.main()
