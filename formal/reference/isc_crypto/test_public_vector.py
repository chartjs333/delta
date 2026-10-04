"""REFERENCE_ONLY_NOT_PRODUCTION: frozen public K/E/R/V/M/G byte vector."""

import hashlib
import json
import os
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any

from codec import (
    Artifact,
    CodecError,
    Vote,
    decode_artifact,
    decode_registry,
    decode_vote,
    encode_artifact,
    encode_evidence,
    encode_key,
    encode_registry,
    encode_vote,
    preimage,
)
from sodium_reference import SodiumReference

FROZEN_IDS = {
    "evidence": "sha256:1519d8d2313edeca646c8a3eba0c256bb4d6c1c7a93ab66a0166691a10368db1",
    "registry": "sha256:5aca4cdb7aec280bb3a550a37189227e2ef2b838512916dbefc02f5f9c225eb0",
    "vote": "sha256:95c368749efed2213a8a40d5738ea45fb796d508936eeaba4f28d17a17997537",
    "artifact": "sha256:fa06ec785a7f598aae335004b31ed9cc1ec1786f7a09a6a50b24151335c5b958",
}


def canonical_json(document: dict[str, Any]) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode("ascii")


def identity(domain: str, data: bytes) -> str:
    return "sha256:" + hashlib.sha256(domain.encode("ascii") + b"\x00" + data).hexdigest()


def length_prefix(data: bytes) -> bytes:
    return len(data).to_bytes(4, "big") + data


class PublicVectorTests(unittest.TestCase):
    fixture: dict[str, Any]
    provenance: dict[str, Any]
    backend: SodiumReference

    @classmethod
    def setUpClass(cls) -> None:
        directory = Path(__file__).parent
        cls.fixture = json.loads((directory / "public-vector.json").read_text(encoding="utf-8"))
        cls.provenance = json.loads(
            (directory / "library-provenance.json").read_text(encoding="utf-8")
        )
        configured = os.environ.get("ISC_SODIUM_DLL")
        if not configured:
            raise RuntimeError("ISC_SODIUM_DLL is required; public vector tests cannot skip")
        cls.backend = SodiumReference(configured, cls.provenance["dll"]["sha256"])

    def test_frozen_full_vector_matches_independent_byte_recipes(self) -> None:
        fixture = self.fixture
        self.assertEqual(fixture["scope"], "REFERENCE_ONLY_NOT_PRODUCTION")
        self.assertTrue(fixture["all_seed_material_public_test_only"])
        self.assertFalse(fixture["semantics_assigned"])
        self.assertFalse(fixture["production_authorization"])
        self.assertEqual(fixture["backend_dll_sha256"], self.provenance["dll"]["sha256"])
        keys = {}
        validators = []
        for index, entry in enumerate(fixture["keys"], 1):
            public_key, _ = self.backend.sign(bytes.fromhex(entry["public_test_seed_hex"]), b"")
            self.assertEqual(public_key.hex(), entry["public_key_hex"])
            expected_key = canonical_json(
                {
                    "algorithm": "Ed25519",
                    "public_key_hex": public_key.hex(),
                    "schema_version": "1.0.0",
                }
            )
            self.assertEqual(encode_key(public_key), expected_key)
            self.assertEqual(expected_key.hex(), entry["canonical_hex"])
            key_id = identity("deltareduce.isc-ed25519-key.v1", expected_key)
            self.assertEqual(key_id, entry["key_id"])
            validator_id = f"synthetic-validator-{index}"
            self.assertEqual(entry["validator_id"], validator_id)
            keys[key_id] = expected_key
            validators.append(
                {"key_ref": key_id, "roles": ["validator"], "validator_id": validator_id}
            )
        self.assertEqual(len(keys), 4)
        sigma = "sha256:" + "0" * 64
        epoch = "sha256:" + "1" * 64
        budget = {
            "formal_semantics_id": sigma,
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
        evidence = canonical_json(budget)
        self.assertEqual(encode_evidence(sigma), evidence)
        self.assertEqual(evidence.hex(), fixture["evidence"]["canonical_hex"])
        eid = identity("deltareduce.isc-evidence-budget.v1", evidence)
        self.assertEqual(eid, fixture["evidence"]["evidence_budget_id"])
        registry_document = {
            "evidence_budget_id": eid,
            "formal_semantics_id": sigma,
            "origin_id": "synthetic-origin-1",
            "quorum_threshold": "3",
            "schema_version": "1.0.0",
            "signature_profile": "SIG-ISC-ED25519-v1",
            "validator_epoch_id": epoch,
            "validators": validators,
        }
        registry = canonical_json(registry_document)
        self.assertEqual(fixture["registry"]["document"], registry_document)
        self.assertEqual(encode_registry(registry_document, keys=keys, evidence=evidence), registry)
        self.assertEqual(registry.hex(), fixture["registry"]["canonical_hex"])
        rid = identity("deltareduce.isc-epoch-registry.v1", registry)
        self.assertEqual(rid, fixture["registry"]["registry_id"])
        fields = {
            "body_hash": "sha256:" + "2" * 64,
            "context_id": "synthetic-native-context-placeholder",
            "durable_sequence": "7",
            "formal_semantics_id": sigma,
            "height": "11",
            "kind": "ISC",
            "round_id": "synthetic-round-1",
            "schema_version": "2.0.0",
            "type_name": "VOTE",
            "validator_epoch_id": epoch,
            "validator_id": "synthetic-validator-1",
            "view": "0",
        }
        payload = b"\x31\x00\x00\x00\x0c"
        for key, value in sorted(fields.items()):
            payload += b"\x21" + length_prefix(key.encode("ascii"))
            payload += b"\x21" + length_prefix(value.encode("ascii"))
        vote = b"DRC1\x01\x00\x00\x03" + length_prefix(payload)
        self.assertEqual(encode_vote(Vote(**fixture["vote"]["fields"])), vote)
        self.assertEqual(vote.hex(), fixture["vote"]["canonical_hex"])
        vid = identity("deltareduce:003:vote:v2", vote)
        self.assertEqual(vid, fixture["vote"]["vote_id"])
        key_id = fixture["keys"][0]["key_id"]
        framed = (
            length_prefix(rid.encode("ascii"))
            + length_prefix(key_id.encode("ascii"))
            + length_prefix(vote)
        )
        message = b"deltareduce.isc-vote.ed25519.v1\x00" + framed
        self.assertEqual(preimage(rid, key_id, vote), message)
        self.assertEqual(message.hex(), fixture["preimage"]["canonical_hex"])
        self.assertEqual(len(message), fixture["preimage"]["byte_length"])
        public_key, signature = self.backend.sign(
            bytes.fromhex(fixture["keys"][0]["public_test_seed_hex"]), message
        )
        self.assertEqual(signature.hex(), fixture["signature_hex"])
        self.assertTrue(self.backend.verify(public_key, message, signature))
        artifact = b"ISG1\x00\x01\x00\x00" + framed + signature
        self.assertEqual(encode_artifact(Artifact(rid, key_id, vote, signature)), artifact)
        self.assertEqual(artifact.hex(), fixture["artifact"]["canonical_hex"])
        gid = identity("deltareduce.isc-signature.v1", artifact)
        self.assertEqual(gid, fixture["artifact"]["artifact_id"])
        self.assertEqual(
            {"evidence": eid, "registry": rid, "vote": vid, "artifact": gid}, FROZEN_IDS
        )

    def test_other_valid_signature_does_not_establish_validator_key_association(self) -> None:
        fixture = self.fixture
        artifact = decode_artifact(bytes.fromhex(fixture["artifact"]["canonical_hex"]))
        vote = decode_vote(artifact.vote_bytes)
        rows = fixture["registry"]["document"]["validators"]
        original_key_ref = next(
            row["key_ref"] for row in rows if row["validator_id"] == vote.validator_id
        )
        self.assertEqual(original_key_ref, artifact.key_id)
        other = fixture["keys"][1]
        altered_message = preimage(artifact.registry_id, other["key_id"], artifact.vote_bytes)
        self.assertFalse(
            self.backend.verify(
                bytes.fromhex(fixture["keys"][0]["public_key_hex"]),
                altered_message,
                artifact.signature,
            )
        )
        other_public, other_signature = self.backend.sign(
            bytes.fromhex(other["public_test_seed_hex"]), altered_message
        )
        self.assertTrue(self.backend.verify(other_public, altered_message, other_signature))
        # This deliberately valid raw signature has no authority for V's signer.
        # The test records the necessary association mismatch, not admission.
        self.assertNotEqual(other["key_id"], original_key_ref)
        self.assertNotEqual(other["validator_id"], vote.validator_id)

    def test_registry_role_and_epoch_substitution_do_not_reuse_signature(self) -> None:
        fixture = self.fixture
        keys = {row["key_id"]: bytes.fromhex(row["canonical_hex"]) for row in fixture["keys"]}
        evidence = bytes.fromhex(fixture["evidence"]["canonical_hex"])
        bad_role = deepcopy(fixture["registry"]["document"])
        bad_role["validators"][0]["roles"] = ["worker"]
        with self.assertRaises(CodecError):
            decode_registry(canonical_json(bad_role), keys=keys, evidence=evidence)
        other_epoch = deepcopy(fixture["registry"]["document"])
        other_epoch["validator_epoch_id"] = "sha256:" + "3" * 64
        other_registry = encode_registry(other_epoch, keys=keys, evidence=evidence)
        other_rid = identity("deltareduce.isc-epoch-registry.v1", other_registry)
        artifact = decode_artifact(bytes.fromhex(fixture["artifact"]["canonical_hex"]))
        vote = decode_vote(artifact.vote_bytes)
        self.assertNotEqual(other_epoch["validator_epoch_id"], vote.validator_epoch_id)
        self.assertNotEqual(other_rid, artifact.registry_id)
        self.assertFalse(
            self.backend.verify(
                bytes.fromhex(fixture["keys"][0]["public_key_hex"]),
                preimage(other_rid, artifact.key_id, artifact.vote_bytes),
                artifact.signature,
            )
        )


if __name__ == "__main__":
    unittest.main()
