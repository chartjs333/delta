"""Adversarial checks of the public arithmetic witness trust boundary."""

import copy
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
from formal_artifacts import load_json_strict, write_canonical_json  # noqa: E402
from native_trace_witness import NativeEvidence, n  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "native_checker", ROOT / "formal/scripts/check-refinement.py"
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
FIXTURES = ROOT / "formal/fixtures/traces"


class NativeTraceWitnessTests(unittest.TestCase):
    def setUp(self):
        self.trace_path = FIXTURES / "legal/normal-apply.json"
        self.native_path = FIXTURES / "native/normal-apply.json"
        self.digest = hashlib.sha256(self.native_path.read_bytes()).hexdigest()

    def test_external_digest_is_required_and_checked(self):
        for invalid in (None, "", "0" * 64):
            with self.subTest(digest=invalid), self.assertRaises(n.BindingError):
                NativeEvidence(self.native_path, invalid)

    def test_trace_cannot_supply_its_own_trusted_native_state(self):
        with self.assertRaises(checker.RefinementError) as caught:
            checker.check_trace(self.trace_path)
        self.assertEqual(caught.exception.reason, "NATIVE_EVIDENCE_REQUIRED")

    def test_exact_native_pack_checks_all_votes(self):
        evidence = NativeEvidence(self.native_path, self.digest)
        result = checker.check_trace(self.trace_path, evidence)
        self.assertEqual(result["native_arithmetic_votes_checked"], 9)
        self.assertEqual(result["native_evidence_sha256"], self.digest)

    def test_mutations_fail_for_their_intended_reason(self):
        manifest = load_json_strict(FIXTURES / "native/manifest.json")
        for case in load_json_strict(FIXTURES / "native/negative-expectations.json"):
            name = case["fixture"]
            with self.subTest(fixture=name):
                evidence = NativeEvidence(
                    FIXTURES / "native" / name, manifest["illegal/" + name]["sha256"]
                )
                with self.assertRaises(checker.RefinementError) as caught:
                    checker.check_trace(FIXTURES / "illegal" / name, evidence)
                self.assertEqual(caught.exception.reason, case["reason"])

    def test_artifact_cannot_be_replaced_under_old_id_even_with_new_bundle_digest(self):
        bundle = load_json_strict(self.native_path)
        key = next(iter(bundle["artifacts"]))
        bundle["artifacts"][key] = bundle["artifacts"][key] + " "
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native.json"
            write_canonical_json(path, bundle)
            with self.assertRaisesRegex(n.BindingError, "NATIVE_ARTIFACT_ID"):
                NativeEvidence(path, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_native_state_cannot_be_replaced_under_old_snapshot_id(self):
        bundle = load_json_strict(self.native_path)
        snapshot = next(iter(bundle["snapshots"].values()))
        snapshot["current_checkpoint"] = "replacement"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native.json"
            write_canonical_json(path, bundle)
            with self.assertRaisesRegex(n.BindingError, "NATIVE_SNAPSHOT_ID"):
                NativeEvidence(path, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_checker_does_not_mutate_frozen_evidence(self):
        before = self.native_path.read_bytes()
        evidence = NativeEvidence(self.native_path, self.digest)
        snapshot = copy.deepcopy(evidence.snapshots)
        store = copy.deepcopy(evidence.store)
        checker.check_trace(self.trace_path, evidence)
        self.assertEqual(snapshot, evidence.snapshots)
        self.assertEqual(store, evidence.store)
        self.assertEqual(before, self.native_path.read_bytes())

    def test_cli_needs_both_external_arguments(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "formal/scripts/check-refinement.py"),
                str(self.trace_path),
                "--native-evidence",
                str(self.native_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required together", result.stderr)


if __name__ == "__main__":
    unittest.main()
