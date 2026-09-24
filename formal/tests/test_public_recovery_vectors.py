"""Real diagnostic fixture mutations must be rejected before Lean generation."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_public_recovery_vectors as g  # noqa: E402
from native_durability_witness import observation_id  # noqa: E402


class PublicRecoveryVectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for folder in ["legal", "native"]:
            (self.directory / folder).mkdir()
            for name in g.NAMES:
                path = Path(folder) / f"{name}.json"
                (self.directory / path).write_bytes(
                    (ROOT / "formal/fixtures/traces" / path).read_bytes()
                )
        self.target, self.evidence = (
            self.directory / "vectors.lean",
            self.directory / "vectors.json",
        )

    def generate(self):
        with contextlib.redirect_stdout(io.StringIO()):
            g.generate(self.directory, self.target, self.evidence)

    def mutate(self, name, select, change):
        trace_path = self.directory / "legal" / f"{name}.json"
        bundle_path = self.directory / "native" / f"{name}.json"
        trace, bundle = g.n.decode(trace_path.read_bytes()), g.n.decode(bundle_path.read_bytes())
        event = next(
            e
            for e in trace["events"]
            if select(e, bundle["operations"].get(e.get("durability_witness")))
        )
        value = bundle["operations"].pop(event["durability_witness"])
        change(value)
        key = observation_id(value)
        bundle["operations"][key] = value
        event["durability_witness"] = key
        trace_path.write_bytes(g.n.canonical(trace))
        bundle_path.write_bytes(g.n.canonical(bundle))

    def assert_rejected(self, code):
        with self.assertRaisesRegex(ValueError, code):
            self.generate()
        self.assertFalse(self.target.exists())
        self.assertFalse(self.evidence.exists())

    def test_exact_stage_and_scan_vectors(self):
        self.generate()
        self.assertEqual(self.target.read_bytes(), g.TARGET.read_bytes())
        self.assertEqual(self.evidence.read_bytes(), g.EVIDENCE.read_bytes())

    def test_unexposed_receipt_cannot_be_invented(self):
        self.mutate(
            "cut-parameter-durable",
            lambda e, o: o and o["stages"] == ["VALIDATED", "APPENDED", "DURABLE"],
            lambda o: o.update(receipt_ascii=""),
        )
        self.assert_rejected("DURABILITY_PERSISTED_BYTES")

    def test_no_barrier_exposure_rejected(self):
        self.mutate(
            "normal-apply",
            lambda e, o: e["action_id"] == "ACT-PARAM-VOTE" and o,
            lambda o: o.update(stages=["VALIDATED", "APPENDED", "COMMITTED", "EXPOSED"]),
        )
        self.assert_rejected("DURABILITY_EXPOSE_ORDER")

    def test_ordinary_scan_does_not_prove_absence(self):
        self.mutate(
            "uncertain-parameter-append-absent",
            lambda e, o: o and "VERIFIED_ABSENT" in o["stages"],
            lambda o: o.update(stages=["READ", "VERIFIED", "RECOVERED"]),
        )
        self.assert_rejected("DURABILITY_ABSENCE_NOT_VERIFIED")

    def test_absence_cannot_truncate_known_prefix(self):
        self.mutate(
            "uncertain-apply-barrier-absent",
            lambda e, o: o and "VERIFIED_ABSENT" in o["stages"],
            lambda o: o.update(sequence_after=o["sequence_after"] - 1),
        )
        self.assert_rejected("DURABILITY_JOURNAL_CHANGED")

    def test_unknown_write_cannot_claim_known_root(self):
        self.mutate(
            "uncertain-parameter-incomplete",
            lambda e, o: o and "UNKNOWN" in o["stages"],
            lambda o: o.update(journal_after=o["journal_before"]),
        )
        self.assert_rejected("DURABILITY_UNKNOWN_ASSERTS_JOURNAL")


if __name__ == "__main__":
    unittest.main()
