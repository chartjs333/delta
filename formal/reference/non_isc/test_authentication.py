"""Public synthetic vectors; real pinned C Ed25519, no production provenance claim."""

import json
import os
import unittest
from dataclasses import replace
from pathlib import Path

from formal.reference.isc_crypto import codec as isc
from formal.reference.isc_crypto.sodium_reference import SCALAR_ORDER, SodiumReference
from formal.reference.isc_source.authentication import Bootstrap, registry
from formal.reference.non_isc import codec
from formal.reference.non_isc.authentication import CONTRACT, AuthorityInputs, authenticate


class NonIscTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / "isc_crypto"
        provenance = json.loads((root / "library-provenance.json").read_text(encoding="utf8"))
        fixture = json.loads((root / "public-vector.json").read_text(encoding="utf8"))
        cls.backend = SodiumReference(os.environ["ISC_SODIUM_DLL"], provenance["dll"]["sha256"])
        cls.bootstrap = Bootstrap(
            "sha256:" + "0" * 64,
            "public-synthetic-origin",
            "sha256:" + "4" * 64,
            tuple((x["validator_id"], bytes.fromhex(x["public_key_hex"])) for x in fixture["keys"]),
        )
        cls.seeds = {
            x["validator_id"]: bytes.fromhex(x["public_test_seed_hex"]) for x in fixture["keys"]
        }
        cls.authority = AuthorityInputs(cls.bootstrap, CONTRACT)
        cls.r, cls.keys = registry(cls.bootstrap)

    def vote(self, kind="APPLY", validator=None, slot=2):
        return codec.NonIscVote(
            isc.Vote(
                "sha256:" + "1" * 64,
                "sha256:" + "2" * 64,
                slot,
                self.bootstrap.formal_semantics_id,
                1,
                "public-synthetic-round",
                self.bootstrap.validator_epoch_id,
                validator or next(iter(self.seeds)),
                0,
            ),
            kind,
        )

    def signed(self, value):
        key_id, _ = self.keys[value.original.validator_id]
        raw = codec.encode_vote(value)
        _, sig = self.backend.sign(
            self.seeds[value.original.validator_id], codec.preimage(self.r, key_id, raw)
        )
        return codec.encode_artifact(isc.Artifact(self.r, key_id, raw, sig))

    def test_all_eight_original_kinds_are_explicit_and_isc_stays_closed(self):
        for kind in sorted(codec.KINDS):
            with self.subTest(kind=kind):
                value = self.vote(kind)
                raw = codec.encode_vote(value)
                self.assertEqual(codec.decode_vote(raw), value)
                with self.assertRaises(isc.CodecError):
                    isc.decode_vote(raw)
                signed = self.signed(value)
                verified = authenticate(self.authority, self.backend, signed)
                self.assertEqual(verified.original_vote, raw)
                self.assertEqual(verified.original_artifact, signed)
                a = codec.decode_artifact(signed)
                m = codec.preimage(a.registry_id, a.key_id, raw)
                self.assertEqual(codec.decode_preimage(m), (a.registry_id, a.key_id, raw))
                self.assertEqual(len(m), 190 + len(raw))
                self.assertEqual(len(signed), 226 + len(raw))
                with self.assertRaises(isc.CodecError):
                    isc.decode_artifact(signed)
        with self.assertRaises(isc.CodecError):
            codec.decode_vote(isc.encode_vote(self.vote().original))
        for kind in ["ISC", "APPLY_QC", "STORAGE", "apply", "", "APPLY\0"]:
            with self.assertRaises(isc.CodecError):
                codec.encode_vote(self.vote(kind))

    def test_exact_framing_vector_and_maximum_derived_bound(self):
        # Independent field-list construction of the normative DRC1 preimage.
        v = self.vote("AGGREGATE_ROOT")
        fields = {
            "body_hash": v.original.body_hash,
            "context_id": v.original.context_id,
            "durable_sequence": "2",
            "formal_semantics_id": self.bootstrap.formal_semantics_id,
            "height": "1",
            "kind": "AGGREGATE_ROOT",
            "round_id": "public-synthetic-round",
            "schema_version": "2.0.0",
            "type_name": "VOTE",
            "validator_epoch_id": self.bootstrap.validator_epoch_id,
            "validator_id": v.original.validator_id,
            "view": "0",
        }
        payload = bytes.fromhex("310000000c")
        for k, value in sorted(fields.items()):
            for text in [k, value]:
                payload += b"\x21" + len(text).to_bytes(4, "big") + text.encode("ascii")
        expected = bytes.fromhex("4452433101000003") + len(payload).to_bytes(4, "big") + payload
        self.assertEqual(codec.encode_vote(v), expected)
        maximum = replace(
            v,
            original=replace(
                v.original,
                context_id="c" * 128,
                round_id="r" * 128,
                validator_id="v" * 128,
                durable_sequence=2**64 - 1,
                height=2**64 - 1,
                view=2**64 - 1,
            ),
        )
        raw = codec.encode_vote(maximum)
        self.assertEqual(len(raw), codec.MAX_VOTE_BYTES)
        self.assertEqual(codec.decode_vote(raw), maximum)

    def test_all_original_bytes_matter_and_no_false_crypto_backend(self):
        value = self.vote()
        a = codec.decode_artifact(self.signed(value))
        changes = [
            replace(value, kind="EC"),
            *[
                replace(value, original=replace(value.original, **{key: changed}))
                for key, changed in [
                    ("body_hash", "sha256:" + "7" * 64),
                    ("context_id", "different-context"),
                    ("durable_sequence", 4),
                    ("round_id", "other-round"),
                    ("height", 2),
                    ("view", 1),
                    ("validator_id", list(self.seeds)[1]),
                    ("validator_epoch_id", "sha256:" + "5" * 64),
                    ("formal_semantics_id", "sha256:" + "6" * 64),
                ]
            ],
        ]
        for changed in changes:
            with self.assertRaises(isc.CodecError):
                authenticate(
                    self.authority,
                    self.backend,
                    codec.encode_artifact(replace(a, vote_bytes=codec.encode_vote(changed))),
                )
        with self.assertRaisesRegex(isc.CodecError, "backend"):
            authenticate(self.authority, lambda *_: True, codec.encode_artifact(a))

    def test_independent_codec_registry_and_key_selection(self):
        raw = self.signed(self.vote())
        for contract in ["SIG-ISC-ED25519-v1", "", "snapshot-selects-the-codec"]:
            with self.assertRaisesRegex(isc.CodecError, "codec selection"):
                authenticate(replace(self.authority, codec_contract=contract), self.backend, raw)
        with self.assertRaises(isc.CodecError):
            authenticate(
                replace(self.authority, bootstrap=replace(self.bootstrap, origin_id="attacker")),
                self.backend,
                raw,
            )
        a = codec.decode_artifact(raw)
        for changed in [
            replace(a, registry_id="sha256:" + "9" * 64),
            replace(a, key_id=list(self.keys.values())[1][0]),
            replace(a, signature=bytes(64)),
            replace(a, signature=a.signature[:32] + SCALAR_ORDER.to_bytes(32, "little")),
        ]:
            with self.assertRaises(isc.CodecError):
                authenticate(self.authority, self.backend, codec.encode_artifact(changed))

    def test_domain_separation_cannot_be_replaced_by_magic_only(self):
        value = self.vote()
        raw = codec.encode_vote(value)
        key_id, _ = self.keys[value.original.validator_id]
        wrong_m = codec.preimage(self.r, key_id, raw).replace(
            codec.M_DOMAIN, b"deltareduce.isc-vote.ed25519.v1\0", 1
        )
        _, sig = self.backend.sign(self.seeds[value.original.validator_id], wrong_m)
        with self.assertRaises(isc.CodecError):
            authenticate(
                self.authority,
                self.backend,
                codec.encode_artifact(isc.Artifact(self.r, key_id, raw, sig)),
            )
        for altered in [raw + b"x", raw[:-1], raw.replace(b"round_id", b"ROUND_ID", 1)]:
            with self.assertRaises(isc.CodecError):
                codec.decode_vote(altered)
        a = self.signed(value)
        for altered in [a + b"x", a[:-1], b"ISG1" + a[4:]]:
            with self.assertRaises(isc.CodecError):
                codec.decode_artifact(altered)

    def test_original_slots_replay_and_repeated_evidence_are_not_collapsed(self):
        first = self.signed(self.vote(slot=2))
        repeat = self.signed(self.vote(slot=2))
        later = self.signed(self.vote(slot=4))
        self.assertEqual(first, repeat)
        inventory = tuple(
            authenticate(self.authority, self.backend, g) for g in [first, repeat, later]
        )
        self.assertEqual([v.vote.original.durable_sequence for v in inventory], [2, 2, 4])
        self.assertEqual(inventory[0].vote_id, inventory[1].vote_id)
        self.assertNotEqual(inventory[0].vote_id, inventory[2].vote_id)
        # This is an authentication component, not permission for two local votes
        # in one journal key and not a quorum or production history constructor.


if __name__ == "__main__":
    unittest.main()
