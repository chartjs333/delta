"""Protect the actual-byte source and unreduced plan denominator in Lean vectors."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_parameter_kernel_vectors as generator  # noqa: E402

n = generator.native


class ParameterKernelVectorTests(unittest.TestCase):
    def setUp(self):
        self.bundle = n.decode(generator.SOURCE.read_bytes())

    def generate(self, directory):
        source = directory / "source.json"
        source.write_bytes(n.canonical(self.bundle))
        target, evidence = directory / "vectors.lean", directory / "vectors.json"
        with contextlib.redirect_stdout(io.StringIO()):
            generator.generate(source, target, evidence)
        return target, evidence

    def assert_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            with self.assertRaises(n.BindingError):
                self.generate(directory)
            self.assertFalse((directory / "vectors.lean").exists())
            self.assertFalse((directory / "vectors.json").exists())

    def test_pinned_source_reproduces_both_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            target, evidence = self.generate(Path(directory))
            self.assertEqual(target.read_bytes(), generator.TARGET.read_bytes())
            self.assertEqual(evidence.read_bytes(), generator.EVIDENCE.read_bytes())

    def test_missing_native_leaf_cannot_be_synthesized(self):
        key = next(
            key
            for key, raw in self.bundle["artifacts"].items()
            if n.decode(raw.encode("ascii"))["kind"] == "Q_SHARD"
        )
        del self.bundle["artifacts"][key]
        self.assert_rejected()

    def test_corrupt_native_bytes_cannot_be_rehashed_implicitly(self):
        key = next(iter(self.bundle["artifacts"]))
        self.bundle["artifacts"][key] += " "
        self.assert_rejected()

    def test_plan_denominator_is_preserved_without_fraction_reduction(self):
        data = json.loads(generator.EVIDENCE.read_bytes())
        cases = {case["name"]: case for case in data["parameter_cases"]}
        for bits in (64, 128):
            first = cases[f"unequal_denominators_{bits}"]
            second = cases[f"different_bound_denominator_{bits}"]
            self.assertEqual(second["denominator"], 2 * first["denominator"])
            self.assertEqual(second["result"], [2 * value for value in first["result"]])
            self.assertNotEqual(first["result"], second["result"])
