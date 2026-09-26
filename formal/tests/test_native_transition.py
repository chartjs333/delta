"""Native summary transitions: byte comparison does not confer public authority."""

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_transition_vectors as tr  # noqa: E402


class NativeTransitionTests(unittest.TestCase):
    def data(self):
        return json.loads((tr.FOLDER / "cpp-cross-check.json").read_bytes())

    def test_reproduction(self):
        with tempfile.TemporaryDirectory() as d:
            lean, target = Path(d) / "v.lean", Path(d) / "v.json"
            with mock.patch.object(tr, "LEAN", lean), mock.patch.object(tr, "TARGET", target):
                tr.generate()
            self.assertEqual(lean.read_bytes(), tr.LEAN.read_bytes())
            self.assertEqual(target.read_bytes(), tr.TARGET.read_bytes())

    def test_all_observed_fields_and_error_codes(self):
        data = self.data()
        rows = tr.validate(data)
        self.assertEqual(len(rows), 59)
        self.assertEqual({r["error"] for r in rows if not r["accepted"]}, set(tr.ERRORS))
        for key in rows[0]:
            changed = copy.deepcopy(data)
            changed["observed"][0][key] = "substituted"
            with self.subTest(key=key), self.assertRaises(ValueError):
                tr.validate(changed)

    def test_original_three_outputs_and_sequence(self):
        data = self.data()
        tr.validate(data)
        original = tr.codec.wal.load()["after-state-command-retry"]
        entry = tr.codec.wal.wal_entries(bytes.fromhex(original["wal_hex"]))[1]
        for field in ["state", "effects", "record"]:
            self.assertEqual(bytes.fromhex(data["observed"][0][field + "_hex"]), entry[field])
        self.assertEqual(entry["sequence"], 2)
        self.assertEqual(tr.codec.decode_state(entry["state"])["durable_sequence"], "1")

    def test_context_and_bound_guards(self):
        rows = {r["name"]: r for r in tr.validate(self.data())}
        for name in [
            "wrong-round",
            "wrong-height",
            "wrong-view",
            "unknown",
            "empty-freeze",
            "sequence-overflow",
            "view-jump",
            "view-max",
            "view-sequence-overflow",
            "tickets-full",
            "availability-full",
        ]:
            self.assertFalse(rows[name]["accepted"], name)
        for name in [
            "config-max-sequence",
            "uint32-last-commit",
            "uint32-last-availability",
            "last-sequence",
        ]:
            self.assertTrue(rows[name]["accepted"], name)
        config = tr.codec.decode_state(bytes.fromhex(rows["config-max-sequence"]["state_hex"]))
        self.assertEqual(config["durable_sequence"], str(2**64 - 1))

    def test_core_is_not_runtime_clock_or_qc_admission(self):
        rows = {r["name"]: r for r in tr.validate(self.data())}
        self.assertTrue(rows["old-clock-core-allows"]["accepted"])
        self.assertTrue(rows["ELIGIBLE-FINALIZE_AGGREGATE"]["accepted"])
        # The standalone core inputs contain no certificate or vote-policy proof.
        _, s, c = next(r for r in tr.cases() if r[0] == "ELIGIBLE-FINALIZE_AGGREGATE")
        self.assertNotIn("qc", s)
        self.assertNotIn("qc", c)
        self.assertEqual(tr.rule(s, c)["state_root"], c["body_hash"])

    def test_missing_or_forged_source_and_scope(self):
        for key in [
            "source_commit",
            "source_sha256",
            "compiler_flags",
            "unmodified_translation_units",
            "native_export_authenticated",
            "native_runtime_execution",
            "gate_eligible",
        ]:
            data = self.data()
            data[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                tr.validate(data)
        data = self.data()
        data["observed"] = data["observed"][:-1]
        with self.assertRaises(ValueError):
            tr.validate(data)

    def test_primitive_encoding_tags_and_all_effect_fields(self):
        self.assertEqual(tr.value(1), b"\x10" + (1).to_bytes(8, "big"))
        self.assertEqual(tr.value("1"), b"\x21\0\0\0\x011")
        _, _, effects, record = tr.outputs(tr.cases()[0][1], tr.cases()[0][2])
        self.assertEqual(len(effects), 8)
        self.assertEqual(len(record), 10)
        self.assertEqual(
            [e["kind"] for e in effects["effects"]], ["PERSIST_STATE", "PUBLISH_CERTIFICATE"]
        )
        self.assertLess(effects["effects"][0]["effect_id"], effects["effects"][1]["effect_id"])
        self.assertEqual(effects["effects"][0]["body_hash"], effects["next_state_root"])
        self.assertEqual(record["sequence"], "1")

    def test_project_import_and_explicit_axiom_audit(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text(encoding="utf-8")
        for module in ["NativeTransition", "NativeTransitionVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(r"^(?:theorem|def) (\w+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
