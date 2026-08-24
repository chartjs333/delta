from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY / "formal" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from formal_artifacts import (  # noqa: E402
    CanonicalJsonError,
    MUTANT_IDS,
    REQUIREMENT_IDS,
    REVIEW_SCOPE,
    TOOLCHAIN_IDS,
    SchemaValidationError,
    canonical_json_bytes,
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    finalize_report,
    load_json_strict,
    sha256_file,
    validate_contract_registry,
    validate_json_schema,
    validate_trace_document,
    verify_report_document,
    write_canonical_json,
)
from run_formal_gate import verify_action_coverage, verify_sany_output  # noqa: E402


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def trace_document() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "formal_semantics_id": HASH_A,
        "trace_id": "TRACE-UNIT",
        "abstraction_version": "1.0.0",
        "initial_state_root": HASH_A,
        "terminal_state_root": HASH_B,
        "terminal_outcome": "IN_PROGRESS",
        "events": [
            {
                "schema_version": "1.0.0",
                "action_id": "ACT-CONFIG-PROPOSE",
                "round_id": "round-1",
                "height": 1,
                "view": 0,
                "validator_epoch": "epoch-1",
                "actor_id": "validator-1",
                "actor_role": "VALIDATOR",
                "request_id": None,
                "vote_context_id": None,
                "parent_hashes": [],
                "body_hash": HASH_A,
                "result_hash": None,
                "prior_state_root": HASH_A,
                "next_state_root": HASH_B,
                "durable_sequence": None,
                "logical_time": 0,
                "outcome": "ACCEPTED",
                "error_code": None,
                "artifact_refs": [],
            }
        ],
    }


class ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.trace_schema = load_json_strict(
            REPOSITORY / "formal" / "schemas" / "formal-trace.schema.json"
        )
        cls.report_schema = load_json_strict(
            REPOSITORY / "formal" / "schemas" / "formal-verification-report.schema.json"
        )

    def test_trace_schema_accepts_explicit_absence(self) -> None:
        validate_json_schema(trace_document(), self.trace_schema)

    def test_trace_schema_rejects_omitted_field(self) -> None:
        mutated = trace_document()
        del mutated["events"][0]["actor_id"]  # type: ignore[index]
        with self.assertRaises(SchemaValidationError):
            validate_json_schema(mutated, self.trace_schema)

    def test_trace_schema_rejects_unknown_action(self) -> None:
        mutated = trace_document()
        mutated["events"][0]["action_id"] = "ACT-NOT-FROZEN"  # type: ignore[index]
        with self.assertRaises(SchemaValidationError):
            validate_json_schema(mutated, self.trace_schema)

    def test_trace_schema_rejects_extra_property(self) -> None:
        mutated = trace_document()
        mutated["events"][0]["hidden_transition"] = True  # type: ignore[index]
        with self.assertRaises(SchemaValidationError):
            validate_json_schema(mutated, self.trace_schema)

    def test_trace_state_roots_must_form_one_chain(self) -> None:
        mutated = trace_document()
        mutated["events"][0]["prior_state_root"] = HASH_B  # type: ignore[index]
        with self.assertRaises(ValueError):
            validate_trace_document(mutated, REPOSITORY)

    def test_registry_matches_both_schema_contracts(self) -> None:
        validate_contract_registry(REPOSITORY)

    def test_canonicalization_ignores_insertion_order(self) -> None:
        left = {"z": [3, 2, 1], "a": {"y": True, "x": None}}
        right = {"a": {"x": None, "y": True}, "z": [3, 2, 1]}
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))

    def test_canonicalization_rejects_float(self) -> None:
        with self.assertRaises(CanonicalJsonError):
            canonical_json_bytes({"unsafe": 0.5})

    def test_strict_loader_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"a":1,"a":2}', encoding="utf-8")
            with self.assertRaises(CanonicalJsonError):
                load_json_strict(path)

    def test_semantics_id_is_input_order_independent(self) -> None:
        entries = [
            {"kind": "tla_module", "path": "formal/tla/A.tla", "sha256": "a" * 64},
            {"kind": "lean_theorem", "path": "formal/proofs/A.lean", "sha256": "b" * 64},
            {"kind": "trace_schema", "path": "formal/schemas/t.json", "sha256": "c" * 64},
        ]
        self.assertEqual(
            derive_formal_semantics_id("1.0.0", entries),
            derive_formal_semantics_id("1.0.0", list(reversed(entries))),
        )

    def test_tlc_action_coverage_is_fail_closed(self) -> None:
        verify_action_coverage(
            "<CrashAfterSend line 1, col 1 to line 2, col 2 of module M>: 7:9",
            ["CrashAfterSend"],
        )
        with self.assertRaises(RuntimeError):
            verify_action_coverage("", ["CrashAfterSend"])
        with self.assertRaises(RuntimeError):
            verify_action_coverage(
                "<CrashAfterSend line 1, col 1 to line 2, col 2 of module M>: 0:0",
                ["CrashAfterSend"],
            )

    def test_sany_semantic_errors_are_fail_closed(self) -> None:
        verify_sany_output("Semantic processing of module Safe")
        with self.assertRaises(RuntimeError):
            verify_sany_output(
                "Semantic processing of module Broken\nSemantic errors:\n*** Errors: 1"
            )
        with self.assertRaises(RuntimeError):
            verify_sany_output("SANY produced no semantic evidence")

    def test_legal_trace_fixtures_are_canonical_and_compatible(self) -> None:
        semantics_id = derive_formal_semantics_id(
            "1.0.0", discover_semantic_artifacts(REPOSITORY)
        )
        fixtures = sorted((REPOSITORY / "formal/fixtures/traces/legal").glob("*.json"))
        self.assertGreaterEqual(len(fixtures), 2)
        for fixture in fixtures:
            trace = load_json_strict(fixture)
            self.assertEqual(
                fixture.read_bytes().removesuffix(b"\n"), canonical_json_bytes(trace), fixture
            )
            self.assertEqual(trace["formal_semantics_id"], semantics_id, fixture)
            validate_trace_document(trace, REPOSITORY)


class ReportVerifierTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for relative in (
            "formal/schemas/formal-trace.schema.json",
            "formal/schemas/formal-verification-report.schema.json",
            "formal/reports/formal-id-registry.json",
        ):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPOSITORY / relative, target)

        tla = self.root / "formal" / "tla" / "Core.tla"
        tla.parent.mkdir(parents=True, exist_ok=True)
        tla.write_text("---- MODULE Core ----\n====\n", encoding="utf-8")
        lean = self.root / "formal" / "proofs" / "DeltaReduce.lean"
        lean.parent.mkdir(parents=True, exist_ok=True)
        lean.write_text("namespace DeltaReduce\nend DeltaReduce\n", encoding="utf-8")

        self.baseline = self.root / "formal" / "reports" / "baseline-inputs.json"
        write_canonical_json(
            self.baseline,
            {"schema_version": "1.0.0", "input_bundle_sha256": "d" * 64},
        )
        self.evidence = self.root / "formal" / "reports" / "evidence.txt"
        self.evidence.write_text("checked evidence\n", encoding="utf-8")
        self.registry = load_json_strict(
            self.root / "formal" / "reports" / "formal-id-registry.json"
        )
        self.report = self._make_go_report()
        self.report_path = self.root / "formal" / "reports" / "report.json"
        write_canonical_json(self.report_path, self.report)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _check(identifier: str) -> dict[str, object]:
        return {
            "id": identifier,
            "mandatory": True,
            "status": "PASS",
            "verified": True,
            "evidence_id": "EVIDENCE-SUITE",
        }

    def _make_go_report(self) -> dict[str, object]:
        artifacts = discover_semantic_artifacts(self.root)
        manifest_path = self.root / "formal" / "reports" / "source-tree-manifest.json"
        manifest_files = [
            {"path": item["path"], "sha256": item["sha256"]} for item in artifacts
        ]
        manifest_files.extend(
            [
                {
                    "path": "formal/reports/baseline-inputs.json",
                    "sha256": sha256_file(self.baseline),
                },
                {"path": "formal/reports/evidence.txt", "sha256": sha256_file(self.evidence)},
            ]
        )
        manifest_files.sort(key=lambda item: item["path"])
        write_canonical_json(
            manifest_path,
            {"schema_version": "1.0.0", "commit": "1" * 40, "files": manifest_files},
        )

        model_checks = []
        for item in self.registry["configs"]:
            record = self._check(item["id"])
            record.update(
                {
                    "kind": "liveness" if "LIVENESS" in item["id"] else "safety",
                    "states": 10,
                    "distinct_states": 8,
                    "diameter": 4,
                    "terminal_states": 1,
                    "properties": [{"id": "INV-TYPE-OK", "status": "PASS"}],
                }
            )
            model_checks.append(record)

        theorem_checks = []
        for item in self.registry["proof_obligations"]:
            record = self._check(item["id"])
            record.update({"source": "formal/proofs/DeltaReduce.lean", "axioms": []})
            theorem_checks.append(record)

        mutant_checks = []
        for identifier in sorted(MUTANT_IDS):
            record = self._check(identifier)
            record["expected_property_id"] = "INV-TYPE-OK"
            mutant_checks.append(record)

        refinement = self._check("REFINEMENT-SUITE")
        refinement.update({"legal_fixture_count": 5, "illegal_fixture_count": 14})
        coverage = [
            {"id": identifier, "status": "PASS", "evidence_id": "EVIDENCE-SUITE"}
            for identifier in sorted(REQUIREMENT_IDS)
        ]
        report: dict[str, object] = {
            "report_schema_version": "1.0.0",
            "formal_semantics_version": "1.0.0",
            "formal_semantics_id": HASH_A,
            "source_tree": {
                "commit": "1" * 40,
                "manifest_path": "formal/reports/source-tree-manifest.json",
                "tree_sha256": sha256_file(manifest_path),
                "clean": True,
                "semantic_artifacts": [],
            },
            "baseline_inputs": {
                "path": "formal/reports/baseline-inputs.json",
                "sha256": sha256_file(self.baseline),
                "input_bundle_sha256": "d" * 64,
                "verified": True,
            },
            "toolchains": [self._check(identifier) for identifier in sorted(TOOLCHAIN_IDS)],
            "model_checks": model_checks,
            "theorem_checks": theorem_checks,
            "mutant_checks": mutant_checks,
            "refinement_checks": [refinement],
            "coverage": {"requirements": coverage, "unresolved": []},
            "assumptions": ["At most f validators are Byzantine."],
            "abstractions": ["Hashes are collision-resistant identifiers."],
            "limitations": ["Cryptographic implementations are not proved."],
            "review_attestations": [
                {
                    "reviewer_id": reviewer,
                    "independent": True,
                    "status": "PASS",
                    "scope": sorted(REVIEW_SCOPE),
                    "evidence_id": "EVIDENCE-SUITE",
                }
                for reviewer in ("reviewer-a", "reviewer-b")
            ],
            "evidence_graph": {
                "nodes": [
                    {
                        "id": "EVIDENCE-SUITE",
                        "path": "formal/reports/evidence.txt",
                        "sha256": sha256_file(self.evidence),
                        "media_type": "text/plain",
                    }
                ],
                "edges": [],
            },
            "decision": "NO_GO",
            "decision_reasons": ["DRAFT"],
        }
        return finalize_report(report, self.root, self.registry)

    def test_complete_report_computes_go_and_verifies_offline(self) -> None:
        self.assertEqual(self.report["decision"], "GO")
        result = verify_report_document(self.report_path, self.root, require_go=True)
        self.assertEqual(result["status"], "PASS")

    def test_report_schema_mutation_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.report)
        del mutated["limitations"]
        with self.assertRaises(SchemaValidationError):
            validate_json_schema(
                mutated,
                load_json_strict(
                    self.root / "formal" / "schemas" / "formal-verification-report.schema.json"
                ),
            )

    def test_reported_decision_cannot_override_computed_decision(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["decision"] = "NO_GO"
        mutated["decision_reasons"] = ["DRAFT"]
        write_canonical_json(self.report_path, mutated)
        result = verify_report_document(self.report_path, self.root)
        self.assertEqual(result["status"], "FAIL")

    def test_evidence_mutation_invalidates_go(self) -> None:
        self.evidence.write_text("mutated evidence\n", encoding="utf-8")
        result = verify_report_document(self.report_path, self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["decision"], "NO_GO")

    def test_consistent_no_go_is_valid_but_not_a_go_gate(self) -> None:
        draft = copy.deepcopy(self.report)
        draft["toolchains"][0]["status"] = "FAIL"
        no_go = finalize_report(draft, self.root, self.registry)
        write_canonical_json(self.report_path, no_go)
        result = verify_report_document(self.report_path, self.root)
        self.assertEqual((result["status"], result["decision"]), ("PASS", "NO_GO"))
        gated = verify_report_document(self.report_path, self.root, require_go=True)
        self.assertEqual(gated["status"], "FAIL")

    def test_noncanonical_report_bytes_are_rejected(self) -> None:
        self.report_path.write_text(json.dumps(self.report, indent=2), encoding="utf-8")
        result = verify_report_document(self.report_path, self.root)
        self.assertEqual(result["status"], "FAIL")

    def test_cli_verifier_has_no_network_or_package_dependency(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(REPOSITORY / "formal" / "scripts" / "verify_formal_report.py"),
                str(self.report_path),
                "--root",
                str(self.root),
                "--require-go",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
