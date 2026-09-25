"""Snapshot substitutions, exact regeneration, and the explicit opaque-root limit."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_public_snapshot_vectors as g  # noqa: E402
from native_durability_witness import observation_id  # noqa: E402
from native_trace_witness import snapshot_id  # noqa: E402


class PublicSnapshotVectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.trace = self.directory / "trace.json"
        self.source = self.directory / "source.json"
        self.target = self.directory / "vectors.lean"
        self.evidence = self.directory / "vectors.json"
        self.trace.write_bytes(g.TRACE.read_bytes())
        self.source.write_bytes(g.SOURCE.read_bytes())

    def generate(self):
        with contextlib.redirect_stdout(io.StringIO()):
            g.generate(self.trace, self.source, self.target, self.evidence)

    def mutate_snapshot(self, change):
        trace = g.n.decode(self.trace.read_bytes())
        bundle = g.n.decode(self.source.read_bytes())
        event = next(e for e in trace["events"] if e["action_id"] == "ACT-PARAM-VOTE")
        witness = event["arithmetic_witness"]
        snapshot = bundle["snapshots"].pop(witness["snapshot_id"])
        change(snapshot)
        identity = snapshot_id(snapshot)
        bundle["snapshots"][identity] = snapshot
        witness["snapshot_id"] = identity
        operation = bundle["operations"].pop(event["durability_witness"])
        operation["snapshot_id"] = identity
        operation_id = observation_id(operation)
        bundle["operations"][operation_id] = operation
        event["durability_witness"] = operation_id
        self.trace.write_bytes(g.n.canonical(trace))
        self.source.write_bytes(g.n.canonical(bundle))

    def rejected(self, reason):
        with self.assertRaisesRegex(ValueError, reason):
            self.generate()
        self.assertFalse(self.target.exists())
        self.assertFalse(self.evidence.exists())

    def test_exact_snapshot_vectors(self):
        self.generate()
        self.assertEqual(self.target.read_bytes(), g.TARGET.read_bytes())
        self.assertEqual(self.evidence.read_bytes(), g.EVIDENCE.read_bytes())

    def test_rehashed_prior_root_substitution(self):
        self.mutate_snapshot(lambda s: s.update(prior_state_root="sha256:" + "0" * 64))
        self.rejected("NATIVE_EVENT_BINDING")

    def test_rehashed_sequence_substitution(self):
        self.mutate_snapshot(lambda s: s.update(durable_sequence=s["durable_sequence"] + 1))
        self.rejected("NATIVE_EVENT_BINDING")

    def test_rehashed_contract_substitution(self):
        self.mutate_snapshot(lambda s: s.update(round_contract_id="sha256:" + "0" * 64))
        self.rejected("NATIVE_ROUND_CONTRACT")

    def test_rehashed_event_time_substitution(self):
        self.mutate_snapshot(
            lambda s: s["anchor"].update(logical_time=s["anchor"]["logical_time"] + 1)
        )
        self.rejected("NATIVE_EVENT_CONTEXT")

    def test_rehashed_current_value_hash_substitution(self):
        self.mutate_snapshot(lambda s: s["anchor"].update(current_model_hash="sha256:" + "0" * 64))
        self.rejected("PARENT_MODEL")

    def test_opaque_root_adjacency_is_not_state_hash_verification(self):
        # Explicit limitation counterexample, not a new qualifying fixture.
        # No state preimage is supplied: arbitrary initial root relabeling that
        # preserves adjacency remains accepted by the existing public checker.
        trace = g.n.decode(self.trace.read_bytes())
        replacement = g.n.digest(b"no public state preimage supplied")
        trace["initial_state_root"] = replacement
        trace["events"][0]["prior_state_root"] = replacement
        self.trace.write_bytes(g.n.canonical(trace))
        self.generate()
        self.assertEqual(self.target.read_bytes(), g.TARGET.read_bytes())


if __name__ == "__main__":
    unittest.main()
