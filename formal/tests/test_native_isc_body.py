"""Byte/profile checks must not silently become native admission/provenance."""

import copy
import hashlib
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_isc_body_vectors as vectors  # noqa: E402
import native_isc_body as codec  # noqa: E402
from formal_artifacts import canonical_json_bytes  # noqa: E402


class NativeIscBodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = vectors.cases()["pinned-vote-fixture"]
        cls.raw = cls.base.encode()

    def test_actual_fixture_id_and_exact_native_component_bytes(self):
        self.assertEqual(len(self.raw), 635)
        self.assertEqual(
            self.base.content_id(),
            "sha256:33e327fe50bd52a92e0675c846fe2ee53671dde65350152380c82a99af21c27d",
        )
        evidence = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())
        self.assertEqual(evidence["source_commit"], vectors.SOURCE)
        self.assertEqual(evidence["status"], "PASS_EXACT_SOURCE_ENCODER_SHA_COMPONENTS_ONLY")
        self.assertFalse(evidence["native_runtime_execution"])
        for name, body in vectors.cases().items():
            self.assertEqual(evidence["observed"][name]["body_bytes_hex"], body.encode().hex())
            self.assertEqual(evidence["observed"][name]["body_id"], body.content_id())

    def test_all_cases_decode_exactly_and_remain_nonqualifying(self):
        for body in vectors.cases().values():
            self.assertEqual(codec.decode(body.encode()), body)
            claim = codec.witness(body)
            self.assertEqual(codec.verify_witness(claim, body), body)
            self.assertFalse(claim["native_export_authenticated"])
            self.assertFalse(claim["gate_eligible"])

    def test_every_truncated_prefix_and_trailing_bytes_reject(self):
        for cut in range(len(self.raw)):
            with self.subTest(cut=cut), self.assertRaises(ValueError):
                codec.decode(self.raw[:cut])
        with self.assertRaisesRegex(ValueError, "trailing"):
            codec.decode(self.raw + b"\0")

    def test_uint64_endianness_and_invalid_typed_values(self):
        self.assertEqual(codec.u64(256), b"\0" * 6 + b"\1\0")
        self.assertEqual(codec.u64(2**64 - 1), b"\xff" * 8)
        for value in [-1, 2**64, True, False, 1.0, "1", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                codec.u64(value)

    def test_lengths_counts_nonascii_and_resource_limits_reject(self):
        with self.assertRaisesRegex(ValueError, "text length"):
            codec.decode(b"\xff" * 8 + self.raw[8:])
        prefix = self.base.context.encode() + codec.text(self.base.input_root)
        with self.assertRaisesRegex(ValueError, "tuple count"):
            codec.decode(prefix + codec.u64(codec.MAX_ITEMS + 1))
        with self.assertRaisesRegex(ValueError, "body size"):
            codec.decode(b"\0" * (codec.MAX_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "text length"):
            replace(self.base, input_root="a" * (codec.MAX_TEXT + 1)).encode()
        with self.assertRaises(UnicodeError):
            replace(self.base, input_root="é").encode()
        with self.assertRaises(UnicodeError):
            codec.decode(self.raw[:8] + b"\xff" + self.raw[9:])
        with self.assertRaisesRegex(ValueError, "tuple count"):
            replace(self.base, tuples=self.base.tuples * (codec.MAX_ITEMS + 1)).encode()

    def test_full_supported_tuple_bound_roundtrips(self):
        # Duplicates are deliberately representable; this is NOT valid ISC admission.
        body = replace(self.base, tuples=self.base.tuples * codec.MAX_ITEMS)
        self.assertEqual(codec.decode(body.encode()), body)

    def test_order_duplicates_and_empty_are_not_silently_rewritten(self):
        cases = vectors.cases()
        names = ["two-tuples", "reversed-tuples-preserved", "duplicate-tuples-preserved"]
        self.assertEqual(len({cases[name].content_id() for name in names}), 3)
        self.assertEqual(
            codec.decode(cases["empty-tuples-encoding-not-admission"].encode()).tuples, ()
        )
        duplicate = cases["duplicate-tuples-preserved"]
        self.assertEqual(len(codec.decode(duplicate.encode()).tuples), 2)

    def test_rehashed_field_substitutions_do_not_override_original_source(self):
        for name, body in vectors.cases().items():
            if name != "pinned-vote-fixture":
                with (
                    self.subTest(name=name),
                    self.assertRaisesRegex(ValueError, "witness mismatch"),
                ):
                    codec.verify_witness(codec.witness(body), self.base)

    def test_forged_provenance_qc_fields_and_version_reject(self):
        original = codec.witness(self.base)
        for field, value in [
            ("native_export_authenticated", True),
            ("gate_eligible", True),
            ("version", "deltareduce.native-snapshot.v1"),
            ("signer_ids", ["validator-1", "validator-2", "validator-3"]),
            ("scope", "AUTHENTICATED_NATIVE_RUNTIME"),
            ("native_export_authenticated", 0),
        ]:
            bad = copy.deepcopy(original)
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                codec.verify_witness(bad, self.base)

    def test_unknown_fields_bool_integer_alias_and_byte_substitution_reject(self):
        claim = codec.witness(self.base)
        fields = copy.deepcopy(claim["fields"])
        fields["signers"] = []
        with self.assertRaisesRegex(ValueError, "body fields"):
            codec.from_fields(fields)
        fields = copy.deepcopy(claim["fields"])
        fields["context"]["height"] = True
        with self.assertRaisesRegex(ValueError, "uint64"):
            codec.from_fields(fields)
        changed = copy.deepcopy(claim)
        changed["fields"]["context"]["height"] = True
        with self.assertRaises(ValueError):
            codec.verify_witness(changed, self.base)
        for field in ["body_bytes_hex", "hash_preimage_hex", "body_id"]:
            changed = copy.deepcopy(claim)
            changed[field] += "00"
            with self.subTest(field=field), self.assertRaises(ValueError):
                codec.verify_witness(changed, self.base)

    def test_exact_source_spans_sha_and_fixture_reproduction(self):
        blobs = vectors.source_blobs()
        code, spans = vectors.harness(blobs)
        evidence = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())
        self.assertEqual(spans, evidence["extracted_definitions"])
        self.assertEqual(hashlib.sha256(code.encode()).hexdigest(), evidence["harness_sha256"])
        self.assertEqual((vectors.FOLDER / "harness.cpp").read_bytes(), code.encode())
        self.assertEqual(
            evidence["source_sha256"],
            {path: hashlib.sha256(raw).hexdigest() for path, raw in blobs.items()},
        )
        self.assertEqual(vectors.TARGET.read_bytes(), canonical_json_bytes(vectors.document()))


if __name__ == "__main__":
    unittest.main()
