"""Pinned native failure bytes, source-field coverage and kernel audit inventory."""

import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_failure as g  # noqa: E402
import native_policy_codec as codec  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class NativeFailureTests(unittest.TestCase):
    def test_reproduction(self):
        self.assertEqual(g.generate().encode(), g.TARGET.read_bytes())

    def test_original_observation_pin(self):
        original = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        for name in ["codec-VIEW_CHANGE", "codec-ABORT"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == name)
            row["policy_hex"] = row["policy_hex"][:-2] + "ff"
            with self.subTest(name=name), patch.object(g, "load_json_strict", return_value=changed):
                with self.assertRaises(ValueError):
                    g.source()

    def test_wire_components_reproduce_and_differ_from_hash_preimages(self):
        for (policy, obj, pre, ident), kind, domain in zip(
            g.source(), ["view_change", "abort_body"], g.DOMAINS, strict=True
        ):
            raw = codec.encode_value(kind, obj)
            reader = codec.Reader(raw)
            self.assertEqual(reader.value(kind), obj)
            self.assertEqual(reader.at, len(raw))
            self.assertNotEqual(raw, g.body_bytes(kind, obj))
            self.assertEqual(pre, domain.encode() + b"\0" + g.body_bytes(kind, obj))
            self.assertEqual("sha256:" + hashlib.sha256(pre).hexdigest(), ident)
            self.assertEqual(policy["candidates"][0]["body_hash"], ident)

    def test_every_abort_field_changes_binary_preimage(self):
        original = g.source()[1][1]
        expected = g.body_bytes("abort_body", original)
        self.assertEqual(len(original), 14)
        for key, val in original.items():
            changed = copy.deepcopy(original)
            changed[key] = (
                [*val, "different"]
                if isinstance(val, list)
                else val + 1
                if isinstance(val, int)
                else val + "x"
            )
            with self.subTest(key=key):
                self.assertNotEqual(g.body_bytes("abort_body", changed), expected)

    def test_all_seven_lists_preserve_order_multiplicity_and_u64_count(self):
        original = g.source()[1][1]
        for key in g.LIST_FIELDS:
            a = copy.deepcopy(original)
            b = copy.deepcopy(original)
            c = copy.deepcopy(original)
            a[key] = ["a", "b"]
            b[key] = ["b", "a"]
            c[key] = ["a", "a", "b"]
            self.assertEqual(len({g.body_bytes("abort_body", x) for x in [a, b, c]}), 3)
        self.assertEqual(g.text64("a"), b"\0" * 7 + b"\1a")

    def test_snapshot_field_inventory(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeFailureSection.lean").read_text("utf-8")
        read = src.split("def readLineage")[1].split("def LineageSource")[0]
        expected = [
            "finalized_round_config_ids",
            "finalized_input_set_ids",
            "finalized_eligibility_ids",
            "finalized_aggregation_plan_ids",
            "finalized_parameter_ids",
            "finalized_aggregate_root_ids",
            "finalized_apply_ids",
        ]
        self.assertEqual(re.findall(r'getTexts fmtSnapshot p.snapshot "([a-z_]+)"', read), expected)
        for field in [
            "timeout_observations",
            "view_change_bodies",
            "abort_requests",
            "abort_bodies",
        ]:
            self.assertIn('trees p "' + field + '"', src)
        self.assertIn("NativeApplySection.bindSection sha p s", src)
        self.assertIn("completeAbortLists", src)

    def test_original_binary_hash_scope_not_certificate_json(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeFailurePayload.lean").read_text("utf-8")
        self.assertIn("NativeStateBytes.contentId sha viewDomain (viewBytes v)", src)
        self.assertIn("NativeStateBytes.contentId sha abortDomain (abortBytes a)", src)
        self.assertNotIn("NativeContractSize.contentId", src)
        self.assertIn("let wire ← encode fmt source", src)
        self.assertIn("INCOMPLETE_INPUT", src)
        self.assertIn("UNSAFE_COEFFICIENTS", src)
        self.assertNotIn(
            "HARD_DEADLINE", src.split("def RequestValid")[1].split("def timeoutLT")[0]
        )

    def test_all_declarations_audited_and_scope_counterchecks(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in ["NativeFailurePayload", "NativeFailureSection", "NativeFailureVectors"]:
            self.assertIn("import DeltaReduce." + module, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", src, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)
        vectors = g.TARGET.read_text("utf-8")
        for name in [
            "uncheckedViewEnable",
            "matchingFinalApplyIsSnapshotOnly",
            "viewWireOverflow",
            "timeoutOtherRound",
        ]:
            self.assertIn("theorem " + name, vectors)


if __name__ == "__main__":
    unittest.main()
