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

    def test_noncanonical_artifact_is_rejected(self):
        key = next(iter(self.bundle["artifacts"]))
        self.bundle["artifacts"][key] += " "
        self.assert_rejected()
