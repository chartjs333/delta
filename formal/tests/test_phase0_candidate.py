"""R1: a rehashed or published-looking document cannot replace the frozen scope."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))

from formal_artifacts import (  # noqa: E402
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    semantic_text_sha256,
)
from verify_phase0 import REQUIRED_INPUTS, verify  # noqa: E402


class CandidatePhase0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name)
        cls.baseline_path = cls.root / "formal/reports/baseline-inputs.json"
        cls.registry_path = cls.root / "formal/reports/formal-id-registry.json"
        cls.semantics_path = cls.root / "formal/reports/formal-semantics.json"
        paths = (
            REQUIRED_INPUTS
            | {
                "formal/reports/baseline-inputs.json",
                "formal/reports/formal-semantics.json",
                "formal/schemas/formal-verification-report.schema.json",
            }
            | {entry["path"] for entry in discover_semantic_artifacts(ROOT)}
        )
        for relative in paths:
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        cls.originals = {
            cls.root / relative: (cls.root / relative).read_bytes()
            for relative in REQUIRED_INPUTS
            | {
                "formal/reports/baseline-inputs.json",
                "formal/reports/formal-semantics.json",
                "formal/proofs/DeltaReduce.lean",
            }
        }

    @classmethod
    def tearDownClass(cls) -> None:
        cls.directory.cleanup()

    def tearDown(self) -> None:
        for path, original in self.originals.items():
            path.write_bytes(original)

    def read(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def write(self, path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8", newline="\n")

    def rehash_inputs(self, baseline: dict | None = None) -> None:
        document = baseline if baseline is not None else self.read(self.baseline_path)
        for entry in document["inputs"]:
            entry["sha256"] = semantic_text_sha256(self.root / entry["path"])
        bundle = "".join(
            f"{entry['path']}\t{entry['sha256']}\n"
            for entry in sorted(document["inputs"], key=lambda entry: entry["path"])
        )
        document["input_bundle_sha256"] = hashlib.sha256(bundle.encode("utf-8")).hexdigest()
        self.write(self.baseline_path, document)

    def assert_rejected(self, reason: str) -> None:
        result = verify(self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(reason, result["errors"])

    def test_frozen_candidate_passes_without_becoming_authority(self) -> None:
        self.assertEqual(verify(self.root)["errors"], [])
        baseline = self.read(self.baseline_path)
        self.assertEqual(baseline["authority_status"], "CANDIDATE_NOT_FORMAL_GO")
        self.assertNotEqual(
            baseline["formal_semantics_id"],
            baseline["scope_freeze"]["historical_merged_formal_semantics_id"],
        )

    def test_historical_baseline_cannot_qualify_candidate(self) -> None:
        baseline = self.read(self.baseline_path)
        baseline["formal_semantics_version"] = "1.0.0"
        baseline["formal_semantics_id"] = baseline["scope_freeze"][
            "historical_merged_formal_semantics_id"
        ]
        self.write(self.baseline_path, baseline)
        self.assert_rejected("formal semantics version mismatch")

    def test_checkout_newlines_do_not_change_accepted_scope(self) -> None:
        path = self.root / "specs/000-formal-tla-spec/accepted-residual-20260928.md"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(verify(self.root)["errors"], [])

    def test_consistently_rehashed_unapproved_version_rejects(self) -> None:
        version = "9.0.0"
        identifier = derive_formal_semantics_id(version, discover_semantic_artifacts(self.root))
        registry = self.read(self.registry_path)
        registry["formal_semantics_version"] = version
        registry["compatibility"]["formal_semantics_id"] = identifier
        self.write(self.registry_path, registry)
        semantics = self.read(self.semantics_path)
        semantics.update(
            formal_semantics_version=version,
            formal_semantics_id=identifier,
            compatibility=registry["compatibility"],
        )
        self.write(self.semantics_path, semantics)
        baseline = self.read(self.baseline_path)
        baseline.update(formal_semantics_version=version, formal_semantics_id=identifier)
        self.rehash_inputs(baseline)
        self.assert_rejected("formal semantics version mismatch")

    def test_omitted_amendment_rejects_even_after_rehash(self) -> None:
        baseline = self.read(self.baseline_path)
        baseline["inputs"] = [
            entry
            for entry in baseline["inputs"]
            if entry["path"]
            != "specs/000-formal-tla-spec/amendments/0001-arithmetic-input-binding.md"
        ]
        self.rehash_inputs(baseline)
        self.assert_rejected("baseline normative input inventory mismatch")

    def test_existing_harness_invariant_cannot_be_removed(self) -> None:
        registry = self.read(self.registry_path)
        registry["invariants"] = [
            entry for entry in registry["invariants"] if entry["name"] != "PersistenceRecoverySound"
        ]
        self.write(self.registry_path, registry)
        self.rehash_inputs()
        self.assert_rejected("registered invariant set differs from the normative invariant set")

    def test_rehashed_residual_edit_does_not_change_accepted_dod(self) -> None:
        path = self.root / "specs/000-formal-tla-spec/accepted-residual-20260928.md"
        path.write_text("R3 removed", encoding="utf-8")
        self.rehash_inputs()
        self.assert_rejected("accepted residual document changed")

    def test_old_compatibility_id_cannot_hide_in_nested_registry(self) -> None:
        registry = self.read(self.registry_path)
        registry["compatibility"]["formal_semantics_id"] = "sha256:" + "0" * 64
        self.write(self.registry_path, registry)
        self.rehash_inputs()
        self.assert_rejected("candidate compatibility identity mismatch")

    def test_proof_source_change_invalidates_frozen_compatibility_binding(self) -> None:
        path = self.root / "formal/proofs/DeltaReduce.lean"
        path.write_bytes(path.read_bytes() + b"\n-- changed source binding\n")
        self.assert_rejected("candidate compatibility identity mismatch")

    def test_phase0_cannot_mislabel_candidate_as_merged_go(self) -> None:
        baseline = self.read(self.baseline_path)
        baseline["authority_status"] = "MERGED_FORMAL_GO"
        self.write(self.baseline_path, baseline)
        self.assert_rejected("candidate freeze must not claim merged Formal GO")


if __name__ == "__main__":
    unittest.main()
