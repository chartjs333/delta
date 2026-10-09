"""Selected U/R/P bytes and substitution negatives, not full-history witnesses."""

import copy
import json
import unittest
from hashlib import sha256

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import arithmetic_units as u
from formal.reference.profile_source import configuration as old_config
from formal.reference.profile_source import configuration_units as c
from formal.reference.profile_source import metadata

SCHEMA, PROOF, SEMANTICS = ("sha256:" + ch * 64 for ch in "123")


def numeric(n="1", d=4):
    return {
        "apply_quantum": {"denominator": d, "numerator": n},
        "domain_weights": [{"domain_id": "d0", "pi": {"denominator": 1, "numerator": "1"}}],
        "learning_rate": {"denominator": 4, "numerator": "1"},
        "momentum": {"denominator": 1, "numerator": "0"},
        "nesterov": True,
        "rounding": "HALF_TOWARD_POSITIVE",
        "weight_decay": {"denominator": 1, "numerator": "0"},
    }


def initial():
    return {
        "parameter_schema_id": SCHEMA,
        "quantum": {"denominator": "4", "numerator": "1"},
        "schema_version": "1.0.0",
        "type_name": "INITIAL_ARITHMETIC_UNITS",
    }


def configuration():
    """Fresh synthetic schema3 body; no transformation of an original object."""
    return {
        "apply_arithmetic_profile_source": u.canonical(numeric()).decode("ascii"),
        "availability_policy": {
            "close_policy": "OMIT_UNAVAILABLE",
            "storage_binding": {
                "storage_epoch_id": "s1",
                "storage_registry_id": PROOF,
                "threshold": "3",
                "retention_epoch_id": "r1",
                "retention_policy_source": {
                    "schema_version": "1.0.0",
                    "type_name": "STORAGE_RETENTION_POLICY_SOURCE",
                    "retention_epoch_id": "r1",
                    "obligation_ref": {"byte_length": "1", "sha256": sha256(b"x").hexdigest()},
                },
            },
        },
        "availability_threshold": 3,
        "batch_budget": 8,
        "dataset_manifest_id": PROOF,
        "domain_ticket_counts": [{"domain_id": "d0", "ticket_count": 1}],
        "fault_tolerance": 1,
        "formal_semantics_id": SEMANTICS,
        "hard_deadline_tick": "20",
        "height": "1",
        "integer_profile": {
            "accumulator_bits": 64,
            "byte_order": "big-endian",
            "profile_id": "int64",
            "value_bits": 16,
        },
        "parent_checkpoint_id": PROOF,
        "parameter_schema_id": SCHEMA,
        "protocol_version": "future-reference",
        "quorum_threshold": 3,
        "round_id": "round-1",
        "schema_version": "3.0.0",
        "soft_deadline_tick": "10",
        "step_budget": 8,
        "ticket_count": 1,
        "type_name": "ROUND_CONFIG",
        "validator_epoch_id": PROOF,
        "validator_ids": ["a", "b", "c", "d"],
        "view": "0",
    }


class ArithmeticUnitsTests(unittest.TestCase):
    def test_literal_three_representations(self):
        original = (
            b'{"parameter_schema_id":"'
            + SCHEMA.encode()
            + b'","quantum":{"denominator":"4","numerator":"1"},'
            b'"schema_version":"1.0.0","type_name":"INITIAL_ARITHMETIC_UNITS"}'
        )
        self.assertEqual(u.decode_initial(original), initial())
        self.assertEqual(metadata.canonical(initial()), original)
        r = (
            b'{"apply_quantum":{"denominator":4,"numerator":"1"},'
            b'"domain_weights":[{"domain_id":"d0","pi":{"denominator":1,"numerator":"1"}}],'
            b'"learning_rate":{"denominator":4,"numerator":"1"},'
            b'"momentum":{"denominator":1,"numerator":"0"},"nesterov":true,'
            b'"rounding":"HALF_TOWARD_POSITIVE","weight_decay":{"denominator":1,"numerator":"0"}}'
        )
        self.assertEqual(u.canonical(numeric()), r)
        p = u.derive_profile(r, PROOF, SEMANTICS)
        self.assertEqual(
            p,
            b'{"accumulator_proof_id":"'
            + PROOF.encode()
            + b'",'
            + r[1 : r.index(b'"learning_rate"')]
            + b'"formal_semantics_id":"'
            + SEMANTICS.encode()
            + b'",'
            + r[r.index(b'"learning_rate"') : r.index(b'"weight_decay"')]
            + b'"schema_version":"2.0.0","type_name":"APPLY_ARITHMETIC_PROFILE",'
            + r[r.index(b'"weight_decay"') :],
        )
        self.assertEqual(
            u.bind_profile_bytes(r, PROOF, SEMANTICS, p),
            "sha256:" + sha256(u.DOMAIN.encode() + b"\0" + p).hexdigest(),
        )

    def test_quantum_limits_are_not_coefficient_limits(self):
        for n, d in [(1, 1), (1, u.I64_MAX), (u.I64_MAX, 1), (u.I64_MAX, u.I64_MAX - 1)]:
            value = numeric(str(n), d)
            value["learning_rate"] = {"denominator": u.U64_MAX, "numerator": "1"}
            self.assertEqual(u.decode_numeric(u.canonical(value)), value)
        for n, d in [(0, 1), (1, 0), (2, 8), (1, u.I64_MAX + 1), (u.I64_MAX + 1, 1)]:
            with self.subTest(n=n, d=d), self.assertRaises(CodecError):
                u.decode_numeric(u.canonical(numeric(str(n), d)))

    def test_bad_rational_tokens_and_control_native_swap(self):
        for key, bads in {
            "numerator": [True, 1, "01", "+1", "-1", " 1", "1e0", "1.0"],
            "denominator": [True, "4", -4, 0],
        }.items():
            for bad in bads:
                value = numeric()
                value["apply_quantum"][key] = bad
                with self.subTest(key=key, bad=bad), self.assertRaises(CodecError):
                    u.decode_numeric(u.canonical(value))
        value = initial()
        value["quantum"]["denominator"] = 4
        with self.assertRaises(CodecError):
            u.decode_initial(json.dumps(value, separators=(",", ":")).encode())

    def test_reject_aliases_duplicate_keys_and_nonintegers(self):
        raw = u.canonical(numeric())
        cases = [
            b" " + raw,
            raw + b"\n",
            b"\xef\xbb\xbf" + raw,
            raw.replace(b'"nesterov":true', b'"nesterov":true,"nesterov":true'),
            raw.replace(b'"d0"', b'"d\\u0030"'),
            raw.replace(b'"denominator":4', b'"denominator":4.0'),
            raw.replace(b'"denominator":4', b'"denominator":4e0'),
            raw.replace(b'"denominator":4', b'"denominator":NaN'),
            raw.replace(b'"denominator":4', b'"denominator":null'),
        ]
        for bad in cases:
            with self.subTest(bad=bad[:80]), self.assertRaises(CodecError):
                u.decode_numeric(bad)

    def test_closed_fields_and_native_rules(self):
        base = numeric()
        cases = [
            dict(base, extra="ignored"),
            {k: v for k, v in base.items() if k != "apply_quantum"},
            dict(base, nesterov=False),
            dict(base, nesterov=1),
            dict(base, rounding="FLOOR"),
            dict(base, domain_weights=[]),
            dict(base, domain_weights=base["domain_weights"] * 2),
        ]
        for bad in cases:
            with self.subTest(keys=sorted(bad)), self.assertRaises(CodecError):
                u.decode_numeric(u.canonical(bad))

    def test_proof_numeric_and_semantics_substitution(self):
        r = u.canonical(numeric())
        p = u.derive_profile(r, PROOF, SEMANTICS)
        for args in [
            (u.canonical(numeric("1", 8)), PROOF, SEMANTICS),
            (r, SCHEMA, SEMANTICS),
            (r, PROOF, SCHEMA),
        ]:
            with self.subTest(args=args), self.assertRaises(CodecError):
                u.bind_profile_bytes(*args, p)
        old = u.decode_profile(p, SEMANTICS)
        del old["apply_quantum"]
        with self.assertRaises(CodecError):
            u.decode_profile(u.canonical(old), SEMANTICS)
        with self.assertRaises(CodecError):
            u.derive_profile(r, PROOF, u.LEGACY_SEMANTICS)
        with self.assertRaises(CodecError):
            u.decode_profile(
                p.replace(SEMANTICS.encode(), u.LEGACY_SEMANTICS.encode()), u.LEGACY_SEMANTICS
            )
        old["apply_quantum"] = numeric()["apply_quantum"]
        old["schema_version"] = "1.0.0"
        with self.assertRaises(CodecError):
            u.decode_profile(u.canonical(old), SEMANTICS)

    def test_initial_full_surrounding_bytes_retained(self):
        doc = {
            "arithmetic_units": initial(),
            "storage_authority": {"original": "retained"},
            "unproven_initial_field": "still requires full initial-state check",
        }
        raw = metadata.canonical(doc)
        self.assertEqual(u.initial_member(raw), initial())
        self.assertEqual(metadata.load(raw), doc)
        with self.assertRaises(CodecError):
            u.initial_member(metadata.canonical({"storage_authority": {}}))

    def test_actual_profile_bytes_budget(self):
        value = numeric()
        value["domain_weights"] = [
            {"domain_id": f"domain-{i:06}", "pi": {"denominator": 1, "numerator": "1"}}
            for i in range(70000)
        ]
        # Within the original row-count domain but exceeds actual encoded bytes.
        with self.assertRaises(CodecError):
            u.canonical(value)


class UnitConfigurationTests(unittest.TestCase):
    def test_original_frame_full_fields_and_nocycle(self):
        body = configuration()
        raw = c.encode(body)
        self.assertEqual(raw[:8], b"DRC1\x01\x00\x00\x01")
        self.assertEqual(int.from_bytes(raw[8:12], "big"), len(raw) - 12)
        self.assertEqual(c.decode(raw), body)
        self.assertEqual(set(body), old_config.FIELDS | {c.FIELD})
        self.assertEqual(set(u.decode_numeric(body[c.FIELD].encode())), u.NUMERIC_FIELDS)
        self.assertLess(raw.index(c.FIELD.encode()), raw.index(b"availability_policy"))
        with self.assertRaises(CodecError):
            old_config.decode(raw)

    def test_parent_continuity_needs_no_later_apc(self):
        raw = c.encode(configuration())
        q = u.Rational(1, 4)
        self.assertEqual(c.check_parent_units(raw, SCHEMA, q, q), q)
        for schema, model, optimizer in [
            (PROOF, q, q),
            (SCHEMA, u.Rational(1, 8), q),
            (SCHEMA, q, u.Rational(1, 8)),
            (SCHEMA, u.Rational(1.0, 4), q),
        ]:
            with self.assertRaises(CodecError):
                c.check_parent_units(raw, schema, model, optimizer)

    def test_reject_changed_generation_fields_and_surrounding_config(self):
        base = configuration()
        cases = [
            {k: v for k, v in base.items() if k != c.FIELD},
            dict(base, schema_version="2.0.0"),
            dict(base, formal_semantics_id=u.LEGACY_SEMANTICS),
            dict(base, quorum_threshold=2),
            dict(base, hard_deadline_tick="9"),
            dict(base, extra="ignored"),
            {**base, c.FIELD: " " + base[c.FIELD]},
        ]
        changed = copy.deepcopy(base)
        changed["availability_policy"]["storage_binding"]["threshold"] = "2"
        cases.append(changed)
        for bad in cases:
            with self.subTest(keys=sorted(bad)), self.assertRaises(CodecError):
                c.encode(bad)
        with self.assertRaises(CodecError):
            c.decode(c.encode(base) + b"\0")


if __name__ == "__main__":
    unittest.main()
