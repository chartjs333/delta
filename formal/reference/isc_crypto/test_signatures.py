"""REFERENCE_ONLY_NOT_PRODUCTION: strict Ed25519 conformance with public vectors.

RFC 8032 section 7.1 test seeds below are public test material, never deployment
keys. No test downloads a library or skips conformance when the backend is absent.
"""

import hashlib
import json
import os
import unittest
from dataclasses import replace
from pathlib import Path

from codec import Vote, encode_vote, preimage
from sodium_reference import SodiumReference

# Source: https://www.rfc-editor.org/rfc/rfc8032.txt, section 7.1, TEST 1 / 2.
RFC8032_VECTORS = (
    (
        "empty",
        bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"),
        bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"),
        b"",
        bytes.fromhex(
            "e5564300c360ac729086e2cc806e828a"
            "84877f1eb8e5d974d873e06522490155"
            "5fb8821590a33bacc61e39701cf9b46b"
            "d25bf5f0595bbe24655141438e7a100b"
        ),
    ),
    (
        "one_byte",
        bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb"),
        bytes.fromhex("3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"),
        bytes.fromhex("72"),
        bytes.fromhex(
            "92a009a9f0d4cab8720e820b5f642540"
            "a2b27b5416503f8fb3762223ebdb69da"
            "085ac1e43e15996e458f3613d0f11d8c"
            "387b2eaeb4302aeeb00d291612bb0c00"
        ),
    ),
)
L = 2**252 + 27742317777372353535851937790883648493
INVALID_POINTS = {
    "identity": b"\x01" + bytes(31),
    "identity_with_noncanonical_sign": b"\x01" + bytes(30) + b"\x80",
    "order_two": bytes.fromhex("ec" + "ff" * 30 + "7f"),
    "order_four": bytes(32),
    "noncanonical_y_equal_p": bytes.fromhex("ed" + "ff" * 30 + "7f"),
    "noncanonical_identity_y_p_plus_one": bytes.fromhex("ee" + "ff" * 30 + "7f"),
    # B + (0,-1): canonical encoding, order 2L, not the prime-order subgroup.
    "mixed_order_2L": bytes.fromhex("95" + "99" * 31),
}


class SignatureConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configured = os.environ.get("ISC_SODIUM_DLL")
        if not configured:
            raise RuntimeError("ISC_SODIUM_DLL is required; crypto tests cannot skip")
        cls.dll_path = Path(configured)
        provenance_path = Path(__file__).with_name("library-provenance.json")
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance["sodium_version"] != "1.0.22":
            raise RuntimeError("conformance requires the pinned libsodium 1.0.22")
        cls.dll_sha256 = provenance["dll"]["sha256"]
        cls.backend = SodiumReference(cls.dll_path, cls.dll_sha256)

    def test_rfc8032_known_answers_and_deterministic_repeat(self) -> None:
        for name, seed, public_key, message, signature in RFC8032_VECTORS:
            with self.subTest(vector=name):
                self.assertEqual(self.backend.sign(seed, message), (public_key, signature))
                self.assertEqual(self.backend.sign(seed, message), (public_key, signature))
                self.assertTrue(self.backend.verify(public_key, message, signature))

    def test_wrong_binary_hash_fails_closed(self) -> None:
        with self.assertRaises(RuntimeError):
            SodiumReference(self.dll_path, "0" * 64)

    def test_seed_size_and_message_budget_fail_closed(self) -> None:
        seed = RFC8032_VECTORS[0][1]
        for size in (0, 1, 31, 33, 64):
            with self.subTest(seed_size=size), self.assertRaises(ValueError):
                self.backend.sign((seed + bytes(64))[:size], b"public vector")
        maximum_message = b"\x00" * 4282
        public_key, signature = self.backend.sign(seed, maximum_message)
        self.assertTrue(self.backend.verify(public_key, maximum_message, signature))
        with self.assertRaises(ValueError):
            self.backend.sign(seed, maximum_message + b"\x00")
        self.assertFalse(self.backend.verify(public_key, maximum_message + b"\x00", signature))

    def test_ed25519ph_and_ed25519ctx_vectors_are_not_pure_ed25519(self) -> None:
        # RFC 8032 sections 7.3 (TEST abc) and 7.2 (foo). No multipart/ctx
        # fallback may cause their signatures to pass the selected pure API.
        variants = (
            (
                "Ed25519ph",
                "ec172b93ad5e563bf4932c70e1245034c35467ef2efd4d64ebf819683467e2bf",
                "616263",
                "98a70222f0b8121aa9d30f813d683f80"
                "9e462b469c7ff87639499bb94e6dae41"
                "31f85042463c2a355a2003d062adf5aa"
                "a10b8c61e636062aaad11c2a26083406",
            ),
            (
                "Ed25519ctx_context_foo",
                "dfc9425e4f968f7f0c29f0259cf5f9aed6851c2bb4ad8bfb860cfee0ab248292",
                "f726936d19c800494e3fdaff20b276a8",
                "55a4cc2f70a54e04288c5f4cd1e45a7b"
                "b520b36292911876cada7323198dd87a"
                "8b36950b95130022907a7fb7c4e9b2d5"
                "f6cca685a587b4b21f4b888e4e7edb0d",
            ),
        )
        for name, public_key, message, signature in variants:
            with self.subTest(variant=name):
                self.assertFalse(
                    self.backend.verify(
                        bytes.fromhex(public_key), bytes.fromhex(message), bytes.fromhex(signature)
                    )
                )

    def test_invalid_public_key_points_are_rejected(self) -> None:
        _, _, _, message, signature = RFC8032_VECTORS[1]
        for name, point in INVALID_POINTS.items():
            with self.subTest(point=name):
                self.assertFalse(self.backend.verify(point, message, signature))

    def test_invalid_r_points_are_rejected(self) -> None:
        _, _, public_key, message, signature = RFC8032_VECTORS[1]
        for name, point in INVALID_POINTS.items():
            with self.subTest(point=name):
                self.assertFalse(self.backend.verify(public_key, message, point + signature[32:]))

    def test_public_identity_key_equation_witness_is_rejected(self) -> None:
        signature = bytes.fromhex("58" + "66" * 31) + (1).to_bytes(32, "little")
        self.assertFalse(
            self.backend.verify(
                INVALID_POINTS["identity"], b"ISC-S16 public negative probe", signature
            )
        )

    def test_scalar_range_and_s_plus_l_malleability_are_rejected(self) -> None:
        _, _, public_key, message, signature = RFC8032_VECTORS[1]
        original_s = int.from_bytes(signature[32:], "little")
        for value in (L, L + 1, original_s + L, 2**256 - 1):
            with self.subTest(scalar=value):
                changed = signature[:32] + value.to_bytes(32, "little")
                self.assertFalse(self.backend.verify(public_key, message, changed))

    def test_short_and_long_public_keys_and_signatures_are_rejected(self) -> None:
        _, _, public_key, message, signature = RFC8032_VECTORS[1]
        for size in (0, 1, 31, 33, 64):
            with self.subTest(public_key_size=size):
                candidate = (public_key + bytes(64))[:size]
                self.assertFalse(self.backend.verify(candidate, message, signature))
        for size in (0, 1, 31, 32, 63, 65, 128):
            with self.subTest(signature_size=size):
                candidate = (signature + bytes(128))[:size]
                self.assertFalse(self.backend.verify(public_key, message, candidate))

    def test_modified_message_key_and_every_signature_byte_are_rejected(self) -> None:
        _, _, public_key, message, signature = RFC8032_VECTORS[1]
        for candidate in (b"", b"s", message + b"\x00"):
            with self.subTest(message=candidate.hex()):
                self.assertFalse(self.backend.verify(public_key, candidate, signature))
        self.assertFalse(self.backend.verify(RFC8032_VECTORS[0][2], message, signature))
        for index in range(len(signature)):
            changed = bytearray(signature)
            changed[index] ^= 1
            with self.subTest(signature_byte=index):
                self.assertFalse(self.backend.verify(public_key, message, bytes(changed)))

    def test_full_exact_isc_preimage_is_signed_without_prehash(self) -> None:
        # These are deliberately synthetic IDs, not a semantics assignment or
        # an independently admitted registry, body or native round context.
        registry_id = "sha256:" + "1" * 64
        key_id = "sha256:" + "2" * 64
        vote = Vote(
            body_hash="sha256:" + "3" * 64,
            context_id="synthetic-context-1",
            durable_sequence=2,
            formal_semantics_id="sha256:" + "0" * 64,
            height=1,
            round_id="synthetic-round-1",
            validator_epoch_id="sha256:" + "4" * 64,
            validator_id="synthetic-validator-1",
            view=0,
        )
        vote_bytes = encode_vote(vote)
        exact = (
            b"deltareduce.isc-vote.ed25519.v1\x00"
            + b"\x00\x00\x00\x47"
            + registry_id.encode("ascii")
            + b"\x00\x00\x00\x47"
            + key_id.encode("ascii")
            + len(vote_bytes).to_bytes(4, "big")
            + vote_bytes
        )
        self.assertEqual(preimage(registry_id, key_id, vote_bytes), exact)
        self.assertEqual(len(exact), 186 + len(vote_bytes))
        seed = RFC8032_VECTORS[0][1]
        public_key, signature = self.backend.sign(seed, exact)
        self.assertTrue(self.backend.verify(public_key, exact, signature))
        self.assertEqual(self.backend.sign(seed, exact), (public_key, signature))
        for alternative in (
            vote_bytes,
            vote.body_hash.encode("ascii"),
            hashlib.sha256(exact).digest(),
            hashlib.sha512(exact).digest(),
            exact[:-1],
            exact + b"\x00",
        ):
            with self.subTest(alternative_length=len(alternative)):
                self.assertFalse(self.backend.verify(public_key, alternative, signature))
        # Every octet includes the domain, embedded NULs/lengths, both IDs, every
        # V field and the last byte; an opaque C-string/truncated path must fail.
        for index in range(len(exact)):
            changed = bytearray(exact)
            changed[index] ^= 1
            with self.subTest(preimage_byte=index):
                self.assertFalse(self.backend.verify(public_key, bytes(changed), signature))
        for changes in (
            {"body_hash": "sha256:" + "5" * 64},
            {"context_id": "synthetic-context-2"},
            {"durable_sequence": 4},
            {"height": 2},
            {"round_id": "synthetic-round-2"},
            {"validator_epoch_id": "sha256:" + "5" * 64},
            {"validator_id": "synthetic-validator-2"},
            {"view": 1},
            {"formal_semantics_id": "sha256:" + "6" * 64},
        ):
            changed_vote = encode_vote(replace(vote, **changes))
            with self.subTest(vote_fields=changes):
                self.assertFalse(
                    self.backend.verify(
                        public_key, preimage(registry_id, key_id, changed_vote), signature
                    )
                )


if __name__ == "__main__":
    unittest.main()
