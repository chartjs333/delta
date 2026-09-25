"""Reproduce complete-state Lean vectors and reject substituted source observations."""

import copy
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_public_state_lean as g  # noqa: E402
from formal_artifacts import load_json_strict, write_canonical_json  # noqa: E402
from public_state_projection import inventory, model_identity, state_root  # noqa: E402
from public_state_storage import pack, unpack  # noqa: E402


class PublicStateLeanTests(unittest.TestCase):
    def test_exact_regeneration(self):
        with tempfile.TemporaryDirectory() as directory:
            target, evidence = Path(directory) / "vectors.lean", Path(directory) / "vectors.json"
            g.generate(target, evidence)
            self.assertEqual(target.read_bytes(), g.TARGET.read_bytes())
            self.assertEqual(
                target.with_name("PublicStateValues.lean").read_bytes(),
                g.VALUES_TARGET.read_bytes(),
            )
            self.assertEqual(evidence.read_bytes(), g.EVIDENCE.read_bytes())
            for original in [g.DOCUMENTS_TARGET, g.LOADS_TARGET]:
                self.assertEqual(
                    target.with_name(original.name).read_bytes(), original.read_bytes()
                )

    def test_inventory_is_actual_complete_model_inventory(self):
        source = (ROOT / "formal/proofs/DeltaReduce/PublicState.lean").read_text(encoding="utf-8")
        block = source.split("def fieldNames : List String := [", 1)[1].split("]", 1)[0]
        self.assertEqual(re.findall(r'"(\w+)"', block), list(inventory()))

    def test_no_semantic_self_hash_cycle(self):
        source = g.VALUES_TARGET.read_text(encoding="utf-8")
        self.assertNotIn(model_identity("native-arithmetic")["formal_semantics_id"], source)
        self.assertIn("semantics := List.replicate 32 0", source)
        evidence = load_json_strict(g.EVIDENCE)
        self.assertFalse(evidence["native_export_authenticated"])
        self.assertEqual(evidence["first_votes"], 9)
        self.assertEqual([p["sequence"] for p in evidence["full_load_pairs"]], [5, 6, 8])
        self.assertEqual(evidence["complete_states"], 18)

    def reject_changed(self, change):
        document = copy.deepcopy(load_json_strict(g.VECTORS))
        trace = unpack(document["positive"])
        first = next(
            e for e in document["legacy_correspondence"] if e["action_id"] == "ACT-PARAM-VOTE"
        )
        for index in [first["prior_state_index"], first["next_state_index"]]:
            observation = trace["states"][index]
            change(observation["state"])
            observation["root"] = state_root(
                observation["state"], model_identity("native-arithmetic")
            )
        document["positive"] = pack(trace)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            source, target, evidence = (
                path / "source.json",
                path / "vectors.lean",
                path / "vectors.json",
            )
            write_canonical_json(source, document)
            with self.assertRaises(ValueError):
                g.generate(target, evidence, source)
            self.assertFalse(target.exists())
            self.assertFalse(evidence.exists())

    def test_rehashed_wrong_clock_rejects_before_output(self):
        self.reject_changed(lambda s: s["variables"].update(logicalTime=["int", "0"]))

    def test_rehashed_wrong_current_rejects_before_output(self):
        self.reject_changed(lambda s: s["variables"].update(currentCheckpoint=["model", "next1"]))

    def test_rehashed_wrong_phase_rejects_before_output(self):
        self.reject_changed(lambda s: s["variables"].update(phase=["str", "ABORTED"]))

    def test_every_declaration_is_kernel_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in [
            "PublicState",
            "PublicStateValues",
            "PublicStateDocuments",
            "PublicStateLoads",
            "PublicStateVectors",
        ]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(
                r"^(?:noncomputable )?(?:def|abbrev|theorem) ([\w.]+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
