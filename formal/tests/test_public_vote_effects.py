"""Source correspondence and exact reproduction, not a TLA action proof."""

import copy
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_public_vote_effects as g  # noqa: E402
from formal_artifacts import load_json_strict, write_canonical_json  # noqa: E402
from public_state_projection import inventory  # noqa: E402


def operator(source, name):
    match = re.search(r"(?m)^" + name + r"(?:\([^\n]*\))? ==\n", source)
    if match is None:
        raise ValueError("MISSING_OPERATOR")
    return source[match.end() :].split("\n\n", 1)[0]


def tuple_fields(source, types):
    match = re.search(r"<<([^<>]+)>>", source)
    if match is None:
        raise ValueError("MISSING_TUPLE")
    result = []
    for name in match[1].replace("\n", " ").split(","):
        name = name.strip()
        if name.endswith("Variables"):
            result.extend(tuple_fields(operator(types, name), types))
        else:
            result.append(name)
    return result


def footprint(types, reduce, quorum, action, phase):
    body = operator(reduce, action)
    if "PersistVoteEnvelopeChanges(envelope)" not in body:
        raise ValueError("MISSING_COMMON_EFFECTS")
    if "PersistedReduceVoteUpstreamUnchanged" not in body:
        raise ValueError("MISSING_UNCHANGED_UPSTREAM")
    common = operator(quorum, "PersistVoteEnvelopeChanges")
    changed = re.findall(r"\b(\w+)'\s*=", body + common)
    preserved = tuple_fields(body, types) + tuple_fields(
        operator(reduce, "PersistedReduceVoteUpstreamUnchanged"), types
    )
    expected = {phase, "durableVotes", "volatileVotes", "durableSequence"}
    if set(changed) != expected or len(changed) != 4 or len(preserved) != 60:
        raise ValueError("WRONG_FOOTPRINT")
    if sorted(changed + preserved) != list(inventory()):
        raise ValueError("INCOMPLETE_FOOTPRINT")
    return changed, preserved


class PublicVoteEffectsTests(unittest.TestCase):
    def test_exact_regeneration(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "Calculations.lean"
            g.generate(target)
            self.assertEqual(target.read_bytes(), g.TARGET.read_bytes())

    def test_substituted_complete_state_source_rejected_before_output(self):
        document = copy.deepcopy(load_json_strict(g.VECTORS))
        document["legacy_correspondence"][0]["legacy_event_index"] = 999
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / "source.json", Path(directory) / "out.lean"
            write_canonical_json(source, document)
            with self.assertRaises(ValueError):
                g.generate(target, source)
            self.assertFalse(target.exists())

    def test_complete_production_assignment_inventory(self):
        def read(name):
            return (ROOT / f"formal/tla/{name}.tla").read_text(encoding="utf-8")

        types, reduce, quorum = map(
            read, ["DeltaReduceTypes", "DeltaReduceReduceApply", "DeltaReduceQuorums"]
        )
        for action, phase in [("VoteParameter", "parameterVotes"), ("VoteApply", "applyVotes")]:
            changed, preserved = footprint(types, reduce, quorum, action, phase)
            self.assertEqual(len(changed), 4)
            self.assertEqual(len(preserved), 60)
            self.assertIn("messages", preserved)
            self.assertIn("currentCheckpoint", preserved)
        broken = reduce.replace(
            "UNCHANGED <<proposals, byzantine, messages, messageMultiplicity,",
            "UNCHANGED <<proposals, byzantine, messageMultiplicity,",
        )
        self.assertNotEqual(broken, reduce)
        with self.assertRaises(ValueError):
            footprint(types, broken, quorum, "VoteParameter", "parameterVotes")
        with self.assertRaises(ValueError):
            footprint(
                types,
                reduce,
                quorum.replace("durableSequence' =", "messages' ="),
                "VoteApply",
                "applyVotes",
            )

    def test_every_new_declaration_is_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text(encoding="utf-8")
        for module in [
            "PublicVoteEffects",
            "PublicVoteEffectsCalculations",
            "PublicVoteEffectsExamples",
        ]:
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text(encoding="utf-8")
            for name in re.findall(
                r"^(?:noncomputable )?(?:def|abbrev|theorem) ([\w.]+)", source, re.M
            ):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
