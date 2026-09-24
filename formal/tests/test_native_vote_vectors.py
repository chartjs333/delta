"""The native pre-WAL bridge's examples require consistent independent evidence."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_vote_vectors as generator  # noqa: E402
from native_durability_witness import EVENT_FIELDS, observation_id  # noqa: E402

n = generator.n


class NativeVoteVectorTests(unittest.TestCase):
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
        observation = self.bundle["operations"].pop(event["durability_witness"])
        update(event, observation)
        observation["event"] = {field: event[field] for field in EVENT_FIELDS}
        key = observation_id(observation)
        self.bundle["operations"][key] = observation
        event["durability_witness"] = key

    def test_native_records_reproduce_lean_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            target, evidence = self.generate(Path(directory))
            self.assertEqual(target.read_bytes(), generator.TARGET.read_bytes())
            self.assertEqual(evidence.read_bytes(), generator.EVIDENCE.read_bytes())

    def test_rehashed_receipt_substitution_rejected(self):
        self.mutate_observation(lambda e, o: o.update(receipt_ascii=o["receipt_ascii"] + " "))
        self.assert_rejected()

    def test_rehashed_wrong_parameter_body_rejected(self):
        def change(event, observation):
            command = n.decode(observation["command_ascii"].encode("ascii"))
            command["payload"]["numerators"][0] += 1
            raw = n.canonical(command).decode("ascii")
            event["arithmetic_witness"]["command_ascii"] = raw
            event["body_hash"] = n.digest(n.canonical(command["payload"]))
            observation["command_ascii"] = raw

        self.mutate_observation(change)
        self.assert_rejected()

    def test_wrong_role_cannot_generate_preparation(self):
        self.mutate_observation(lambda e, o: e.update(actor_role="WORKER"))
        self.assert_rejected()

    def test_missing_optimizer_cannot_generate_native_records(self):
        artifacts = self.bundle["artifacts"]
        key = next(
            key
            for key, raw in artifacts.items()
            if n.decode(raw.encode("ascii"))["kind"] == "OPTIMIZER"
        )
        del artifacts[key]
        self.assert_rejected()
