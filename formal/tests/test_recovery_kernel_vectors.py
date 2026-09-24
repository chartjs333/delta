"""Do not emit trusted-looking Lean receipt examples from invalid witnesses."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_recovery_kernel_vectors as generator  # noqa: E402
from native_durability_witness import observation_id  # noqa: E402

n = generator.n


class RecoveryKernelVectorTests(unittest.TestCase):
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
            with self.assertRaises(n.BindingError):
                self.generate(directory)
            self.assertFalse((directory / "vectors.lean").exists())
            self.assertFalse((directory / "vectors.json").exists())

    def mutate_observation(self, update):
        event = next(e for e in self.trace["events"] if e["action_id"] == "ACT-PARAM-VOTE")
        old = event["durability_witness"]
        observation = self.bundle["operations"].pop(old)
        update(observation)
        new = observation_id(observation)
        self.bundle["operations"][new] = observation
        event["durability_witness"] = new

    def test_pinned_bytes_reproduce_lean_and_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            target, evidence = self.generate(Path(directory))
            self.assertEqual(target.read_bytes(), generator.TARGET.read_bytes())
            self.assertEqual(evidence.read_bytes(), generator.EVIDENCE.read_bytes())

    def test_rehashed_receipt_substitution_rejected(self):
        self.mutate_observation(lambda o: o.update(receipt_ascii=o["receipt_ascii"] + " "))
        self.assert_rejected()

    def test_rehashed_sequence_substitution_rejected(self):
        self.mutate_observation(lambda o: o.update(sequence_after=o["sequence_after"] + 1))
        self.assert_rejected()

    def test_missing_receipt_is_not_an_exposed_record(self):
        self.mutate_observation(lambda o: o.update(receipt_ascii=None, effect_ascii=None))
        self.assert_rejected()

    def test_missing_optimizer_cannot_generate_admission_table(self):
        artifacts = self.bundle["artifacts"]
        key = next(
            key
            for key, raw in artifacts.items()
            if n.decode(raw.encode("ascii"))["kind"] == "OPTIMIZER"
        )
        del artifacts[key]
        self.assert_rejected()
