"""The proof generator must reject corrupt source evidence before emitting Lean."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_graph_vectors as generator  # noqa: E402

n = generator.native


class NativeGraphVectorTests(unittest.TestCase):
    def setUp(self):
        self.bundle = n.decode(generator.SOURCE.read_bytes())

    def generate(self, target):
        source = target.with_suffix(".json")
        source.write_bytes(n.canonical(self.bundle))
        with contextlib.redirect_stdout(io.StringIO()):
            generator.generate(source, target)

    def assert_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "vectors.lean"
            with self.assertRaises(n.BindingError):
                self.generate(target)
            self.assertFalse(target.exists())

    def test_pinned_bytes_reproduce_checked_in_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "vectors.lean"
            self.generate(target)
            self.assertEqual(target.read_bytes(), generator.TARGET.read_bytes())

    def test_substituted_bytes_under_old_identity_are_rejected(self):
        keys = list(self.bundle["artifacts"])
        self.bundle["artifacts"][keys[0]] = self.bundle["artifacts"][keys[1]]
        self.assert_rejected()

    def test_missing_referenced_q_shard_is_rejected(self):
        key = next(
            key
            for key, raw in self.bundle["artifacts"].items()
            if n.decode(raw.encode("ascii"))["kind"] == "Q_SHARD"
        )
        del self.bundle["artifacts"][key]
        self.assert_rejected()

    def test_stale_current_model_anchor_is_rejected(self):
        for snapshot in self.bundle["snapshots"].values():
            snapshot["anchor"]["current_model_hash"] = "sha256:" + "0" * 64
        self.assert_rejected()

    def test_stale_current_optimizer_anchor_is_rejected(self):
        for snapshot in self.bundle["snapshots"].values():
            snapshot["anchor"]["current_optimizer_hash"] = "sha256:" + "0" * 64
        self.assert_rejected()

    def test_missing_current_optimizer_cannot_emit_apply_proof(self):
        key = next(
            key
            for key, raw in self.bundle["artifacts"].items()
            if n.decode(raw.encode("ascii"))["kind"] == "OPTIMIZER"
        )
        del self.bundle["artifacts"][key]
        self.assert_rejected()

    def test_noncanonical_artifact_is_rejected(self):
        key = next(iter(self.bundle["artifacts"]))
        self.bundle["artifacts"][key] += " "
        self.assert_rejected()

    def replace_aggregate(self, change):
        key = next(
            key
            for key, raw in self.bundle["artifacts"].items()
            if n.decode(raw.encode("ascii"))["kind"] == "AGGREGATE_PROJECTION"
        )
        aggregate = n.decode(self.bundle["artifacts"].pop(key).encode("ascii"))
        change(aggregate["payload"]["parameters"])
        raw = n.canonical(aggregate)
        new_key = n.digest(raw)
        self.bundle["artifacts"][new_key] = raw.decode("ascii")
        for snapshot in self.bundle["snapshots"].values():
            if snapshot["anchor"].get("aggregate_id") == key:
                snapshot["anchor"]["aggregate_id"] = new_key
                snapshot["anchor"]["aggregate_length"] = len(raw)

    def test_rehashed_certified_numerator_cannot_replace_native_computation(self):
        def change(parameters):
            parameters[0]["numerators"][0] += 1

        self.replace_aggregate(change)
        self.assert_rejected()

    def test_equivalent_certified_fraction_is_not_a_canonical_alias(self):
        def change(parameters):
            parameters[0]["denominator"] *= 2
            parameters[0]["numerators"] = [n * 2 for n in parameters[0]["numerators"]]

        self.replace_aggregate(change)
        self.assert_rejected()

    def test_rehashed_certificate_order_cannot_replace_plan_order(self):
        self.replace_aggregate(lambda parameters: parameters.reverse())
        self.assert_rejected()
