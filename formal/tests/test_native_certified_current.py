"""Retained original CURRENT/QC identity and complete Lean declaration audit."""

import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES = ["NativeCertifiedCurrent", "NativeCertifiedCurrentVectors"]


class NativeCertifiedCurrentTests(unittest.TestCase):
    def test_original_command_and_qc_preimages(self):
        path = ROOT / (
            "formal/proposals/evidence/native-current-pointer/"
            "delta-protocol__fixtures__008__cross-language__golden-v1.json"
        )
        golden = json.loads(path.read_bytes())
        for key, domain in [
            ("current_pointer_command", "deltareduce.008.current-pointer-command.v1"),
            ("apply_qc", "deltareduce.008.apply-qc.v1"),
        ]:
            entry = golden[key]
            payload = json.dumps(entry["value"], sort_keys=True, separators=(",", ":")).encode()
            digest = hashlib.sha256(domain.encode() + b"\x00" + payload).hexdigest()
            self.assertEqual(entry["content_id"], "sha256:" + digest)
        command = golden["current_pointer_command"]["value"]
        qc = golden["apply_qc"]["value"]
        self.assertEqual(command["apply_qc_id"], golden["apply_qc"]["content_id"])
        self.assertEqual(command["next_checkpoint_id"], qc["next_model_hash"])
        self.assertEqual(command["next_optimizer_hash"], qc["next_optimizer_hash"])
        self.assertEqual(command["expected_parent_checkpoint_id"], qc["parent_checkpoint_id"])

    def test_named_declarations_imported_and_audited(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in MODULES:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(
                r"^(?:def|abbrev|theorem|structure|inductive) (\w+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)
