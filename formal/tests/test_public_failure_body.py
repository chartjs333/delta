"""Original failure lineage identity, public field inventory and proof audit."""

import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_failure as native  # noqa: E402

MODULES = [
    "NativeFailureSource",
    "PublicFailureBody",
    "PublicFailureHistory",
    "PublicFailureBodyVectors",
]


class PublicFailureBodyTests(unittest.TestCase):
    def test_original_failure_fields_and_public_inventory(self):
        view, abort = native.source()
        self.assertEqual(view[1]["soft_deadline_tick"], view[0]["soft_deadline_tick"])
        self.assertEqual(abort[1]["hard_deadline_tick"], abort[0]["hard_deadline_tick"])
        self.assertEqual(len(native.LIST_FIELDS), 7)
        self.assertTrue(abort[1][native.LIST_FIELDS[0]])
        for field in native.LIST_FIELDS[1:]:
            self.assertEqual(abort[1][field], [])
        for row in [view, abort]:
            self.assertEqual("sha256:" + hashlib.sha256(row[2]).hexdigest(), row[3])
        tla = (ROOT / "formal/tla/DeltaReduceFailures.tla").read_text("utf-8")
        for name, fields in [
            (
                "ViewChangeBody(round, fromView, toView)",
                ["round", "fromView", "toView", "softDeadline"],
            ),
            (
                "AbortBody(round)",
                [
                    "round",
                    "validatorEpoch",
                    "view",
                    "configs",
                    "hardDeadline",
                    "parentCheckpoint",
                    "lineage",
                    "reason",
                ],
            ),
            ("RoundLineage(round)", ["isc", "ec", "apc", "parameter", "aggregate", "apply"]),
        ]:
            definition = tla.split(name + " ==", 1)[1].split("\n\n", 1)[0]
            self.assertEqual(re.findall(r"(\w+)\s*\|->", definition), fields)

    def test_omitted_or_changed_lineage_cannot_retain_original_identity(self):
        _, body, preimage, _ = native.source()[1]
        for field in native.LIST_FIELDS:
            changed = copy.deepcopy(body)
            changed[field] = [body["parent_checkpoint_id"]]
            if changed[field] == body[field]:
                changed[field] = []
            new_preimage = (
                native.DOMAINS[1].encode() + b"\0" + native.body_bytes("abort_body", changed)
            )
            self.assertNotEqual(preimage, new_preimage)
            self.assertNotEqual(
                hashlib.sha256(preimage).digest(), hashlib.sha256(new_preimage).digest()
            )
            missing = copy.deepcopy(body)
            del missing[field]
            with self.assertRaises(KeyError):
                native.body_bytes("abort_body", missing)
        # Identity checks do not authenticate absence or authorize native admission.

    def test_declarations_and_exact_public_reasons(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(
                r"^(?:def|abbrev|theorem|structure|inductive) ([\w.]+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
        tla = (ROOT / "formal/tla/DeltaReduceTypes.tla").read_text("utf-8")
        reasons = set(
            re.findall(r'"([A-Z_]+)"', tla.split("AbortReasons ==", 1)[1].split("\n\n", 1)[0])
        )
        body = (ROOT / "formal/proofs/DeltaReduce/PublicFailureBody.lean").read_text("utf-8")
        supported = set(
            re.findall(
                r'some "([A-Z_]+)"', body.split("def reason", 1)[1].split("structure Trust", 1)[0]
            )
        )
        self.assertEqual(supported, reasons - {"NO_ABORT"})
