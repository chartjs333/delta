"""Full public-prefix examples must not hide invalid non-arithmetic votes."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_public_journal_vectors as generator  # noqa: E402
from native_durability_witness import observation_id  # noqa: E402

n = generator.n


class PublicJournalVectorTests(unittest.TestCase):
    def setUp(self):
        self.trace = n.decode(generator.TRACE.read_bytes())
        self.bundle = n.decode(generator.SOURCE.read_bytes())

    def generate(self, directory):
        trace, source = directory / "trace.json", directory / "native.json"
        trace.write_bytes(n.canonical(self.trace))
        source.write_bytes(n.canonical(self.bundle))
        target, evidence = directory / "vectors.lean", directory / "vectors.json"
        with contextlib.redirect_stdout(io.StringIO()):
            generator.generate(trace, source, target, evidence)
        return target, evidence

    def assert_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            with self.assertRaises(ValueError) as caught:
                self.generate(directory)
            self.assertNotIn("FORMAL_SEMANTICS_MISMATCH", str(caught.exception))
            self.assertFalse((directory / "vectors.lean").exists())
            self.assertFalse((directory / "vectors.json").exists())

    def first_vote(self, action):
        return next(e for e in self.trace["events"] if e["action_id"] == action)

    def test_full_prefix_reproduces_bytes_without_renumbering(self):
        with tempfile.TemporaryDirectory() as directory:
            target, evidence = self.generate(Path(directory))
            self.assertEqual(target.read_bytes(), generator.TARGET.read_bytes())
            self.assertEqual(evidence.read_bytes(), generator.EVIDENCE.read_bytes())
            document = n.decode(evidence.read_bytes().strip())
            self.assertEqual(document["original_sequences"], list(range(1, 9)))
            self.assertEqual(document["arithmetic_sequences"], [5, 6, 8])

    def test_other_vote_wrong_epoch_rejected(self):
        self.first_vote("ACT-CONFIG-VOTE")["validator_epoch"] = "different-epoch"
        self.assert_rejected()

    def test_other_vote_wrong_sequence_rejected(self):
        self.first_vote("ACT-ISC-VOTE")["durable_sequence"] = 1
        self.assert_rejected()

    def test_missing_other_vote_breaks_public_history(self):
        event = self.first_vote("ACT-ROOT-VOTE")
        self.trace["events"].remove(event)
        self.assert_rejected()

    def test_rehashed_before_root_substitution_rejected(self):
        event = self.first_vote("ACT-PARAM-VOTE")
        observation = self.bundle["operations"].pop(event["durability_witness"])
        observation["journal_before"] = "sha256:" + "00" * 32
        key = observation_id(observation)
        self.bundle["operations"][key] = observation
        event["durability_witness"] = key
        self.assert_rejected()

    def test_rehashed_receipt_substitution_rejected(self):
        event = self.first_vote("ACT-PARAM-VOTE")
        observation = self.bundle["operations"].pop(event["durability_witness"])
        observation["receipt_ascii"] += " "
        key = observation_id(observation)
        self.bundle["operations"][key] = observation
        event["durability_witness"] = key
        self.assert_rejected()
