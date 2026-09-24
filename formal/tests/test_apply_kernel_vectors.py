"""APPLY vectors must keep the native fixture's anchored arithmetic inputs."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_apply_kernel_vectors as generator  # noqa: E402

n = generator.native


class ApplyKernelVectorTests(unittest.TestCase):
    def setUp(self):
        self.bundles = [n.decode(source.read_bytes()) for source in generator.SOURCES]

    def generate(self, directory):
        sources = []
        for original, bundle in zip(generator.SOURCES, self.bundles, strict=True):
            source = directory / original.name
            source.write_bytes(n.canonical(bundle))
            sources.append(source)
        target = directory / "vectors.lean"
        evidence = directory / "vectors.json"
        with contextlib.redirect_stdout(io.StringIO()):
            generator.generate(sources, target, evidence)
        return target, evidence

    def assert_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            with self.assertRaises(n.BindingError):
                self.generate(directory)
            self.assertFalse((directory / "vectors.lean").exists())
            self.assertFalse((directory / "vectors.json").exists())

    def test_pinned_graphs_reproduce_both_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            target, evidence = self.generate(Path(directory))
            self.assertEqual(target.read_bytes(), generator.TARGET.read_bytes())
            self.assertEqual(evidence.read_bytes(), generator.EVIDENCE.read_bytes())

    def test_substituted_bytes_under_old_id_are_rejected(self):
        artifacts = self.bundles[0]["artifacts"]
        keys = list(artifacts)
        artifacts[keys[0]] = artifacts[keys[1]]
        self.assert_rejected()

    def test_missing_current_optimizer_is_rejected(self):
        artifacts = self.bundles[1]["artifacts"]
        key = next(
            key
            for key, raw in artifacts.items()
            if n.decode(raw.encode("ascii"))["kind"] == "OPTIMIZER"
        )
        del artifacts[key]
        self.assert_rejected()

    def test_stale_optimizer_anchor_is_rejected(self):
        for snapshot in self.bundles[1]["snapshots"].values():
            snapshot["anchor"]["current_optimizer_hash"] = "sha256:" + "0" * 64
        self.assert_rejected()

    def test_rehashed_aggregate_cannot_replace_independently_derived_body(self):
        bundle = self.bundles[1]
        artifacts = bundle["artifacts"]
        key = next(
            key
            for key, raw in artifacts.items()
            if n.decode(raw.encode("ascii"))["kind"] == "AGGREGATE_PROJECTION"
        )
        aggregate = n.decode(artifacts.pop(key).encode("ascii"))
        aggregate["payload"]["parameters"][0]["numerators"][0] += 1
        raw = n.canonical(aggregate)
        new_key = n.digest(raw)
        artifacts[new_key] = raw.decode("ascii")
        for snapshot in bundle["snapshots"].values():
            if snapshot["anchor"].get("aggregate_id") == key:
                snapshot["anchor"]["aggregate_id"] = new_key
                snapshot["anchor"]["aggregate_length"] = len(raw)
        self.assert_rejected()
