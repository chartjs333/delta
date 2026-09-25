"""Actual native policy/admission results remain distinct from snapshot authentication."""

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_admission_vectors as vectors  # noqa: E402
from formal_artifacts import canonical_json_bytes  # noqa: E402
from native_admission_snapshot import bind_state, decode_flat, state_id  # noqa: E402


class NativeAdmissionSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())
        cls.rows = cls.evidence["observed"]
        cls.by_name = {r["name"]: r for r in cls.rows}
        cls.original = cls.by_name["original-input_set"]

    def output(self, rows):
        return "\n".join(canonical_json_bytes(row).decode("ascii") for row in rows)

    def test_all_native_policy_and_vote_results(self):
        self.assertEqual(vectors.parse_output(self.output(self.rows)), self.rows)
        self.assertEqual(len(self.rows), 66)
        self.assertTrue(self.evidence["native_component_execution"])
        for key in [
            "native_runtime_execution",
            "native_export_authenticated",
            "full_public_state_relation",
            "gate_eligible",
        ]:
            self.assertFalse(self.evidence[key])

    def test_arithmetic_guard_rejects_both_actions_and_modes(self):
        for action in ["parameter", "apply"]:
            for mode in ["live", "recovery"]:
                row = self.by_name[f"{action}-guard-{mode}"]
                self.assertEqual(row["policy"]["status"], "ACCEPT")
                self.assertEqual(row["vote"]["status"], "REJECT")
                self.assertEqual(
                    row["vote"]["message"],
                    "arithmetic vote lacks authoritative native recomputation inputs",
                )
                self.assertEqual(row["returned_context"], "")
        self.assertNotIn("/D", self.evidence["compiler_flags"])
        self.assertNotIn("#define", vectors.harness())

    def test_stale_native_state_and_context_rejections(self):
        stale = [r for r in self.rows if r["name"].startswith("stale-state-")]
        self.assertEqual(len(stale), 11)
        for row in stale:
            self.assertEqual(row["policy"]["status"], "REJECT")
            self.assertNotEqual(state_id(bytes.fromhex(row["state_hex"])), row["snapshot_state_id"])
        for name in [
            "closed-membership",
            "closed-typed-body",
            "closed-duplicate",
            "closed-foreign",
            "body-context",
            "candidate-context",
            "config-policy",
            "epoch-policy",
            "committee-order",
            "committee-duplicate",
            "schema-policy",
            "arithmetic-profile-policy",
        ]:
            self.assertEqual(self.by_name[name]["policy"]["status"], "REJECT", name)

    def test_runtime_prerequisite_checks_are_separate_from_policy(self):
        for name in [
            "vote-body",
            "vote-context",
            "vote-actor",
            "vote-epoch",
            "vote-sequence",
            "expected-sequence",
            "vote-height",
            "vote-view",
            "vote-round",
            "current-parent",
            "not-ready-live",
            "authority-invalidated-live",
            "at-hard-deadline",
            "abort-request",
        ]:
            row = self.by_name[name]
            self.assertEqual(row["policy"]["status"], "ACCEPT", name)
            self.assertEqual(row["vote"]["status"], "REJECT", name)
        self.assertEqual(self.by_name["not-ready-recovery"]["vote"]["status"], "ACCEPT")
        self.assertEqual(self.by_name["invalidated-recovery"]["vote"]["status"], "REJECT")
        self.assertEqual(self.by_name["before-hard-deadline"]["vote"]["status"], "ACCEPT")

    def test_exact_drc1_state_hash_is_not_inner_root_provenance(self):
        original = self.original
        raw = bytes.fromhex(original["state_hex"])
        result = bind_state(raw, original["snapshot_state_id"])
        self.assertEqual(result["fields"], decode_flat(raw, 5))
        for key in [
            "inner_state_root_preimage_verified",
            "closed_input_origin_authenticated",
            "native_export_authenticated",
            "full_public_state_relation",
        ]:
            self.assertFalse(result[key])
        changed = self.by_name["rebound-summary-root"]
        self.assertEqual(changed["vote"]["status"], "ACCEPT")
        self.assertNotEqual(changed["snapshot_state_id"], original["snapshot_state_id"])
        with self.assertRaisesRegex(ValueError, "preimage"):
            bind_state(bytes.fromhex(changed["state_hex"]), original["snapshot_state_id"])
        self.assertFalse(
            bind_state(bytes.fromhex(changed["state_hex"]), changed["snapshot_state_id"])[
                "full_public_state_relation"
            ]
        )

    def test_same_native_state_id_does_not_authenticate_closed_snapshot(self):
        for name, field in [
            ("rebound-input-root", "input_root"),
            ("rebound-input-commitment", "commitment_id"),
            ("rebound-input-ac", "availability_certificate_id"),
        ]:
            row = self.by_name[name]
            self.assertEqual(row["vote"]["status"], "ACCEPT")
            self.assertEqual(row["state_hex"], self.original["state_hex"])
            self.assertEqual(row["snapshot_state_id"], self.original["snapshot_state_id"])
            self.assertNotEqual(
                row["input_bodies"][0]["body_id"], self.original["input_bodies"][0]["body_id"]
            )
            self.assertEqual(row["closed_ids"], [row["input_bodies"][0]["body_id"]])
            before, after = self.original["input_bodies"][0], row["input_bodies"][0]
            if field != "input_root":
                before, after = before["tuples"][0], after["tuples"][0]
            self.assertNotEqual(before[field], after[field])
        row = self.by_name["no-finalized-config-assertion"]
        self.assertEqual(row["finalized_config_ids"], [])
        self.assertEqual(row["state_hex"], self.original["state_hex"])
        self.assertEqual(row["vote"]["status"], "ACCEPT")
        # This is a trust-boundary countercheck, not a claim about the full reactor pipeline.

    def test_flat_decoder_rejects_headers_truncations_types_and_trailing_data(self):
        raw = bytes.fromhex(self.original["state_hex"])
        for size in range(len(raw)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                decode_flat(raw[:size], 5)
        for bad in [
            b"X" + raw[1:],
            raw[:4] + b"\x02" + raw[5:],
            raw[:6] + b"\x00\x03" + raw[8:],
            raw + b"\0",
            raw[:12] + b"\x30" + raw[13:],
            b"x" * 16385,
        ]:
            with self.assertRaises(ValueError):
                decode_flat(bad, 5)
        # Exact state fields contain unsigned count tags, not bools or decimal text.
        tag = raw.index(b"available_ticket_count") + len(b"available_ticket_count")
        for value in [1, 2, 0x11, 0x21]:
            with self.assertRaises(ValueError):
                decode_flat(raw[:tag] + bytes([value]) + raw[tag + 1 :], 5)
        with self.assertRaisesRegex(ValueError, "header"):
            decode_flat(b'{"variables":{}}', 5)

    def test_flat_decoder_rejects_field_order_and_bad_numeric_spelling(self):
        raw = bytes.fromhex(self.original["state_hex"])
        for old, new in [
            (b"available_ticket_count", b"committed_ticket_count"),
            (b"durable_sequence", b"durable_sequencf"),
            (b"sha256:", b"sha257:"),
            (b"1.0.0", b"9.0.0"),
        ]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                decode_flat(raw.replace(old, new, 1), 5)
        marker = b"\x21\x00\x00\x00\x06height\x21\x00\x00\x00\x01"
        index = raw.index(marker) + len(marker)
        with self.assertRaisesRegex(ValueError, "decimal"):
            decode_flat(raw[:index] + b"-" + raw[index + 1 :], 5)

    def test_diagnostics_reject_omissions_order_results_and_preimage_substitution(self):
        for rows in [self.rows[:-1], self.rows[::-1], self.rows + self.rows[-1:]]:
            with self.assertRaises(ValueError):
                vectors.parse_output(self.output(rows))
        for key, value in [
            ("snapshot_state_id", vectors.ledger.cid("f")),
            ("returned_context", "forged"),
            ("extra", False),
        ]:
            rows = copy.deepcopy(self.rows)
            rows[1][key] = value
            with self.assertRaises(ValueError):
                vectors.parse_output(self.output(rows))
        rows = copy.deepcopy(self.rows)
        rows[1]["input_bodies"][0]["tuples"][0]["commitment_id"] = vectors.ledger.cid("f")
        with self.assertRaisesRegex(ValueError, "identity"):
            vectors.parse_output(self.output(rows))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            vectors.parse_output('{"name":"a","name":"b"}')

    def test_source_harness_fixture_and_full_unit_reproduction(self):
        self.assertEqual(vectors.TARGET.read_bytes(), canonical_json_bytes(vectors.document()))
        self.assertEqual(
            self.evidence["source_sha256"],
            {p: hashlib.sha256(b).hexdigest() for p, b in vectors.sources().items()},
        )
        self.assertEqual(self.evidence["unmodified_translation_units"], vectors.UNITS)
        self.assertEqual(len(vectors.UNITS), 8)
        self.assertEqual((vectors.FOLDER / "harness.cpp").read_bytes(), vectors.harness().encode())
        self.assertEqual(
            self.evidence["harness_sha256"], hashlib.sha256(vectors.harness().encode()).hexdigest()
        )


if __name__ == "__main__":
    unittest.main()
