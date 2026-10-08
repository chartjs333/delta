"""Full-body source/signature binding with public synthetic keys, not finality."""

import copy
import unittest
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source.authentication import registry
from formal.reference.non_isc import codec as votes
from formal.reference.non_isc.test_authentication import NonIscTests
from formal.reference.profile_source import configuration as c
from formal.reference.storage_source import codec as storage
from formal.reference.storage_source.test_codec import StorageSourceTests, identifier


class ConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        NonIscTests.setUpClass()
        StorageSourceTests.setUpClass()
        cls.signer = NonIscTests()
        cls.storage_boot = StorageSourceTests.bootstrap
        cls.boot = replace(
            cls.signer.bootstrap,
            formal_semantics_id=cls.storage_boot.formal_semantics_id,
            origin_id=cls.storage_boot.origin_id,
        )
        cls.backend = cls.signer.backend
        cls.registry_id, cls.keys = registry(cls.boot)
        cls.declaration = b"original retained declaration\r\n"

    def body(self):
        sr, _ = storage.registry(self.storage_boot)
        binding = {
            "retention_epoch_id": "retention-1",
            "storage_epoch_id": self.storage_boot.storage_epoch_id,
            "storage_registry_id": storage.content_id(storage.REGISTRY_DOMAIN, sr),
            "threshold": "3",
            "retention_policy_source": {
                "schema_version": "1.0.0",
                "type_name": "STORAGE_RETENTION_POLICY_SOURCE",
                "retention_epoch_id": "retention-1",
                "obligation_ref": {
                    "byte_length": str(len(self.declaration)),
                    "sha256": sha256(self.declaration).hexdigest(),
                },
            },
        }
        return {
            "availability_policy": {"storage_binding": binding},
            "availability_threshold": 3,
            "batch_budget": 8,
            "dataset_manifest_id": identifier(31),
            "domain_ticket_counts": [{"domain_id": "d0", "ticket_count": 1}],
            "fault_tolerance": 1,
            "formal_semantics_id": self.boot.formal_semantics_id,
            "hard_deadline_tick": "20",
            "height": "1",
            "integer_profile": {
                "accumulator_bits": 64,
                "byte_order": "big-endian",
                "profile_id": "int64",
                "value_bits": 16,
            },
            "parent_checkpoint_id": identifier(32),
            "parameter_schema_id": identifier(33),
            "protocol_version": "future-reference",
            "quorum_threshold": 3,
            "round_id": "round-1",
            "schema_version": "2.0.0",
            "soft_deadline_tick": "10",
            "step_budget": 8,
            "ticket_count": 1,
            "type_name": "ROUND_CONFIG",
            "validator_epoch_id": self.boot.validator_epoch_id,
            "validator_ids": [name for name, _ in self.boot.validators],
            "view": "0",
        }

    def sign(self, raw, overrides=None):
        body = c.decode(raw)
        name = self.boot.validators[0][0]
        original = crypto.Vote(
            crypto.content_id(c.DOMAIN, raw),
            c.vote_context(int(body["height"]), self.boot.validator_epoch_id),
            1,
            self.boot.formal_semantics_id,
            int(body["height"]),
            body["round_id"],
            self.boot.validator_epoch_id,
            name,
            int(body["view"]),
        )
        original = replace(original, **(overrides or {}))
        frame = votes.encode_vote(votes.NonIscVote(original, "ROUND_CONFIG"))
        key_id, _ = self.keys[name]
        _, signature = self.backend.sign(
            self.signer.seeds[name], votes.preimage(self.registry_id, key_id, frame)
        )
        return votes.encode_artifact(crypto.Artifact(self.registry_id, key_id, frame, signature))

    def check(self, raw, artifact):
        return c.authenticate_config_vote(
            self.boot, self.storage_boot, self.backend, raw, self.declaration, artifact
        )

    def test_whole_config_bytes_and_original_vote_retained(self):
        body = self.body()
        raw = c.encode(body)
        self.assertEqual(c.decode(raw), body)
        artifact = self.sign(raw)
        result, signed = self.check(raw, artifact)
        self.assertIs(result.original, raw)
        self.assertEqual(result.body_id, crypto.content_id(c.DOMAIN, raw))
        self.assertNotEqual(result.body_id, "sha256:" + sha256(raw).hexdigest())
        self.assertEqual(signed.original_artifact, artifact)
        self.assertEqual(result.storage_binding.source.original_declaration, self.declaration)
        self.assertEqual(set(body) - {"availability_policy"}, c.FIELDS - {"availability_policy"})

    def test_all_original_config_fields_are_signed_not_only_storage_binding(self):
        body = self.body()
        raw = c.encode(body)
        artifact = self.sign(raw)
        changes = {
            "parent_checkpoint_id": identifier(90),
            "parameter_schema_id": identifier(91),
            "dataset_manifest_id": identifier(92),
            "round_id": "round-other",
            "view": "1",
            "height": "2",
            "batch_budget": 9,
            "step_budget": 9,
            "soft_deadline_tick": "11",
            "hard_deadline_tick": "21",
            "protocol_version": "other",
        }
        for key, value in changes.items():
            altered = c.encode({**body, key: value})
            with self.subTest(key=key), self.assertRaises(crypto.CodecError):
                self.check(altered, artifact)
        altered = copy.deepcopy(body)
        altered["integer_profile"]["accumulator_bits"] = 128
        with self.assertRaises(crypto.CodecError):
            self.check(c.encode(altered), artifact)

    def test_wrong_signed_context_or_own_crypto_fails(self):
        raw = c.encode(self.body())
        for field, value in {
            "body_hash": identifier(96),
            "context_id": identifier(97),
            "height": 2,
            "view": 1,
            "round_id": "other",
        }.items():
            with self.subTest(field=field), self.assertRaises(crypto.CodecError):
                self.check(raw, self.sign(raw, {field: value}))
        good = self.sign(raw)
        with self.assertRaises(crypto.CodecError):
            self.check(raw, good[:-1] + bytes([good[-1] ^ 1]))

    def test_strict_wire_no_legacy_or_lossy_config(self):
        body = self.body()
        for changed in (
            {**body, "schema_version": "1.0.0"},
            {k: v for k, v in body.items() if k != "availability_policy"},
            {**body, "extra": "ignored"},
            {**body, "height": "01"},
            {**body, "batch_budget": "8"},
            {**body, "fault_tolerance": 0},
        ):
            with self.assertRaises(crypto.CodecError):
                c.encode(changed)
        raw = c.encode(body)
        for corrupt in (
            raw[:-1],
            raw + b"\0",
            raw[:6] + b"\0\2" + raw[8:],
            raw[:8] + (len(raw) - 11).to_bytes(4, "big") + raw[12:],
        ):
            with self.assertRaises(crypto.CodecError):
                c.decode(corrupt)

    def test_configuration_cannot_select_storage_trust_or_normalize_declaration(self):
        raw = c.encode(self.body())
        for wrong in (
            replace(self.storage_boot, origin_id=identifier(99)),
            replace(self.storage_boot, storage_epoch_id="other"),
        ):
            with self.assertRaises(crypto.CodecError):
                c.bind(self.boot, wrong, raw, self.declaration)
        with self.assertRaises(crypto.CodecError):
            c.bind(self.boot, self.storage_boot, raw, self.declaration.replace(b"\r\n", b"\n"))
        # A valid source/signature above still carries no FinalizeRoundConfig claim.


if __name__ == "__main__":
    unittest.main()
