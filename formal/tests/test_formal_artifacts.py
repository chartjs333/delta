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
    MUTANT_IDS,
    REPRODUCTION_CHECK_IDS,
    REQUIREMENT_IDS,
    REVIEW_SCOPE,
    TOOLCHAIN_IDS,
    CanonicalJsonError,
    SchemaValidationError,
    canonical_json_bytes,
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    finalize_report,
    load_json_strict,
    reproduction_matches_source,
    review_attestation_matches,
    semantic_text_sha256,
    sha256_file,
    validate_contract_registry,
    validate_json_schema,
    validate_trace_document,
    verify_report_document,
    write_canonical_json,
)
from generate_formal_report import (  # noqa: E402
    is_report_output,
    verified_source_manifest_status,
)
from run_clean_offline_reproduction import (  # noqa: E402
    COMMANDS,
    git_safe_directory_environment,
    verify_source_manifest,
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
        "round_contract": {
            "contract_id": HASH_A,
            "round_id": "round-1",
            "round_config": {
                "body_hash": HASH_A,
                "domain_ids": ["domain-1"],
                "parameter_schema_hash": HASH_A,
                "shard_plan_hash": HASH_B,
            },
            "parameter_schema": {
                "schema_hash": HASH_A,
                "parameter_ids": ["parameter-1"],
            },
            "shard_plan": {
                "plan_hash": HASH_B,
                "assignments": [
                    {
                        "parameter_id": "parameter-1",
                        "domain_id": "domain-1",
                        "shard_id": "shard-1",
                        "vote_context_id": "PARAM:domain-1:shard-1",
                    }
                ],
            },
        },
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


def reproduction_document(
    *,
    commit: str = "1" * 40,
    source_tree: str = "2" * 40,
    formal_semantics_id: str = HASH_A,
) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "status": "PASS",
        "environment": "linux/amd64 clean container with --network none",
        "source_commit": commit,
        "source_tree": source_tree,
        "source_clean_at_start": True,
        "source_manifest_sha256": "3" * 64,
        "formal_semantics_id": formal_semantics_id,
        "platform": "Linux-6.8.0-x86_64-with-glibc2.36",
        "machine": "x86_64",
        "network_interfaces": ["lo"],
        "network_proxies_forced_to_loopback": True,
        "checks": [
            {
                "id": identifier,
                "command": ["python", identifier],
                "exit_code": 0,
                "output_sha256": "5" * 64,
                "status": "PASS",
            }
            for identifier in REPRODUCTION_CHECK_IDS
        ],
        "errors": [],
    }


class ReportSourceBoundaryTests(unittest.TestCase):
    def test_offline_git_safe_directories_are_exact_and_non_wildcard(self) -> None:
        environment = git_safe_directory_environment({"PRESERVED": "yes"})
        count = int(environment["GIT_CONFIG_COUNT"])
        values = {
            environment[f"GIT_CONFIG_VALUE_{index}"] for index in range(count)
        }
        self.assertEqual(environment["PRESERVED"], "yes")
        self.assertEqual(count, 10)
        self.assertNotIn("*", values)
        self.assertEqual(
            values,
            {
                str((REPOSITORY / "formal" / "proofs").resolve()),
                *(
                    str(
                        (
                            REPOSITORY
                            / "formal"
                            / "proofs"
                            / ".lake"
                            / "packages"
                            / package["name"]
                        ).resolve()
                    )
                    for package in load_json_strict(
                        REPOSITORY / "formal" / "proofs" / "dependencies.lock.json"
                    )["packages"]
                ),
            },
        )

    def test_ci_tee_pipelines_cannot_mask_gate_failures(self) -> None:
        lines = (REPOSITORY / ".github" / "workflows" / "formal.yml").read_text(
            encoding="utf-8"
        ).splitlines()
        pipeline_count = 0
        for index, line in enumerate(lines):
            if "| tee " not in line:
                continue
            pipeline_count += 1
            run_index = max(
                position
                for position in range(index)
                if lines[position].strip() == "run: |"
            )
            self.assertIn("set -o pipefail", [item.strip() for item in lines[run_index:index]])
        self.assertGreaterEqual(pipeline_count, 5)

    def test_generated_evidence_overlay_does_not_change_source_commit(self) -> None:
        self.assertTrue(is_report_output("formal/reports/tlc-evidence.json"))
        self.assertTrue(is_report_output("formal\\reports\\reviews\\review-a.json"))
        self.assertFalse(is_report_output("formal/reports/reviews/README.md"))
        self.assertFalse(is_report_output("formal/reports/baseline-inputs.json"))

    def test_offline_runner_regenerates_report_before_verifying_it(self) -> None:
        check_ids = [identifier for identifier, _command, _timeout in COMMANDS]
        self.assertEqual(check_ids, list(REPRODUCTION_CHECK_IDS))
        generation = check_ids.index("report-generation")
        self.assertEqual(check_ids[generation + 1], "report-verifier")

    def test_verified_source_manifest_supplies_gitless_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source-manifest.json"
            manifest = {
                "schema_version": "1.0.0",
                "source_commit": "1" * 40,
                "source_tree": "2" * 40,
                "source_clean": True,
                "files": [{"path": "tracked.txt", "sha256": "3" * 64}],
            }
            write_canonical_json(path, manifest)
            self.assertEqual(
                verified_source_manifest_status(path),
                ("1" * 40, "2" * 40, True),
            )
            manifest["source_clean"] = False
            write_canonical_json(path, manifest)
            with self.assertRaises(ValueError):
                verified_source_manifest_status(path)

    def test_reproduction_must_bind_exact_source_and_semantics(self) -> None:
        reproduction = reproduction_document()
        self.assertTrue(
            reproduction_matches_source(
                reproduction,
                "1" * 40,
                HASH_A,
                source_tree="2" * 40,
            )
        )
        self.assertFalse(
            reproduction_matches_source(
                reproduction,
                "1" * 40,
                HASH_A,
                source_tree="9" * 40,
            )
        )
        reproduction["source_commit"] = "4" * 40
        self.assertFalse(reproduction_matches_source(reproduction, "1" * 40, HASH_A))

    def test_offline_source_manifest_rejects_untracked_source_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            temporary = Path(temporary_name)
            root = temporary / "source"
            root.mkdir()
            source = root / "tracked.txt"
            source.write_text("tracked\n", encoding="utf-8")
            cache = root / "formal" / "toolchain" / "cache"
            cache.mkdir(parents=True)
            (cache / "ignored.bin").write_bytes(b"cache")
            manifest_path = temporary / "source-manifest.json"
            write_canonical_json(
                manifest_path,
                {
                    "schema_version": "1.0.0",
                    "source_commit": "1" * 40,
                    "source_tree": "2" * 40,
                    "source_clean": True,
                    "files": [
                        {"path": "tracked.txt", "sha256": sha256_file(source)}
                    ],
                },
            )
            verify_source_manifest(manifest_path, root)
            (root / "untracked.txt").write_text("unexpected\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_source_manifest(manifest_path, root)


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

    def test_phase0_text_hash_is_newline_independent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lf = Path(directory) / "lf.txt"
            crlf = Path(directory) / "crlf.txt"
            lf.write_bytes(b"alpha\nbeta\n")
            crlf.write_bytes(b"alpha\r\nbeta\r\n")
            self.assertEqual(semantic_text_sha256(lf), semantic_text_sha256(crlf))

    def test_semantic_artifact_discovery_is_checkout_eol_independent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = {
                "formal/tla/Core.tla": "---- MODULE Core ----\n====\n",
                "formal/proofs/DeltaReduce.lean": (
                    "namespace DeltaReduce\nend DeltaReduce\n"
                ),
                "formal/schemas/formal-trace.schema.json": '{"type":"object"}\n',
            }
            for relative, content in sources.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")

            lf_artifacts = discover_semantic_artifacts(root)
            lf_id = derive_formal_semantics_id("1.0.0", lf_artifacts)
            raw_lf_hashes = {
                relative: sha256_file(root / relative) for relative in sources
            }

            for relative in sources:
                path = root / relative
                path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))

            self.assertTrue(
                any(
                    sha256_file(root / relative) != raw_lf_hashes[relative]
                    for relative in sources
                )
            )
            crlf_artifacts = discover_semantic_artifacts(root)
            self.assertEqual(crlf_artifacts, lf_artifacts)
            self.assertEqual(
                derive_formal_semantics_id("1.0.0", crlf_artifacts), lf_id
            )

            core = root / "formal/tla/Core.tla"
            core.write_bytes(core.read_bytes().replace(b"Core", b"Changed", 1))
            self.assertNotEqual(
                derive_formal_semantics_id(
                    "1.0.0", discover_semantic_artifacts(root)
                ),
                lf_id,
            )

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

    def test_review_payload_binding_is_fail_closed(self) -> None:
        payload = {
            "formal_semantics_id": HASH_A,
            "independent": True,
            "reviewed_commit": "1" * 40,
            "reviewer_id": "reviewer-a",
            "scope": sorted(REVIEW_SCOPE),
            "status": "PASS",
        }
        projection = {
            "reviewer_id": "reviewer-a",
            "independent": True,
            "status": "PASS",
            "scope": sorted(REVIEW_SCOPE),
            "evidence_id": "EVIDENCE-REVIEW-1",
        }
        self.assertTrue(
            review_attestation_matches(
                payload,
                reviewed_commit="1" * 40,
                formal_semantics_id=HASH_A,
                projection=projection,
            )
        )
        for field, value in (
            ("reviewed_commit", "2" * 40),
            ("formal_semantics_id", HASH_B),
            ("reviewer_id", "reviewer-b"),
            ("scope", ["MODEL"]),
        ):
            mutated = copy.deepcopy(payload)
            mutated[field] = value
            self.assertFalse(
                review_attestation_matches(
                    mutated,
                    reviewed_commit="1" * 40,
                    formal_semantics_id=HASH_A,
                    projection=projection,
                ),
                field,
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

    def test_full_liveness_evidence_reaches_applied(self) -> None:
        evidence = load_json_strict(REPOSITORY / "formal/reports/tlc-evidence.json")
        model = next(
            item
            for item in evidence["models"]
            if item["id"] == "CFG-LIVENESS-EVENTUAL-SYNCHRONY"
        )
        self.assertIn("LIVE-APPLIED-REACHED", model["properties"])
        self.assertIn("APPLIED", model["terminal_outcomes_observed"])
        self.assertGreater(model["terminal_outcome_class_count"], 0)


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
        semantics_id = derive_formal_semantics_id("1.0.0", artifacts)
        reproduction_path = (
            self.root / "formal" / "reports" / "reproducibility-evidence.json"
        )
        write_canonical_json(
            reproduction_path,
            reproduction_document(formal_semantics_id=semantics_id),
        )
        reproduction_node = {
            "id": "EVIDENCE-REPRODUCIBILITY",
            "path": reproduction_path.relative_to(self.root).as_posix(),
            "sha256": sha256_file(reproduction_path),
            "media_type": "application/json",
        }
        review_nodes = []
        review_attestations = []
        for index, reviewer in enumerate(("reviewer-a", "reviewer-b"), start=1):
            review_path = (
                self.root / "formal" / "reports" / "reviews" / f"{reviewer}.json"
            )
            review_payload = {
                "formal_semantics_id": semantics_id,
                "independent": True,
                "reviewed_commit": "1" * 40,
                "reviewer_id": reviewer,
                "scope": sorted(REVIEW_SCOPE),
                "status": "PASS",
            }
            write_canonical_json(review_path, review_payload)
            evidence_id = f"EVIDENCE-REVIEW-{index}"
            review_nodes.append(
                {
                    "id": evidence_id,
                    "path": review_path.relative_to(self.root).as_posix(),
                    "sha256": sha256_file(review_path),
                    "media_type": "application/json",
                }
            )
            review_attestations.append(
                {
                    "reviewer_id": reviewer,
                    "independent": True,
                    "status": "PASS",
                    "scope": sorted(REVIEW_SCOPE),
                    "evidence_id": evidence_id,
                }
            )
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
        manifest_files.extend(
            {"path": node["path"], "sha256": node["sha256"]}
            for node in [reproduction_node, *review_nodes]
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
            "review_attestations": review_attestations,
            "evidence_graph": {
                "nodes": [
                    {
                        "id": "EVIDENCE-SUITE",
                        "path": "formal/reports/evidence.txt",
                        "sha256": sha256_file(self.evidence),
                        "media_type": "text/plain",
                    },
                    reproduction_node,
                    *review_nodes,
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

    def test_report_manifest_uses_same_eol_profile_as_semantic_identity(self) -> None:
        for item in self.report["source_tree"]["semantic_artifacts"]:
            path = self.root / item["path"]
            canonical = (
                path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            )
            path.write_bytes(canonical.replace(b"\n", b"\r\n"))

        result = verify_report_document(self.report_path, self.root, require_go=True)
        self.assertEqual((result["status"], result["decision"]), ("PASS", "GO"))

        core = self.root / "formal/tla/Core.tla"
        core.write_bytes(core.read_bytes().replace(b"Core", b"Changed", 1))
        result = verify_report_document(self.report_path, self.root)
        self.assertEqual((result["status"], result["decision"]), ("FAIL", "NO_GO"))

    def test_review_projection_cannot_forge_a_valid_evidence_payload(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["review_attestations"][0]["reviewer_id"] = "forged-reviewer"
        no_go = finalize_report(mutated, self.root, self.registry)
        self.assertEqual(no_go["decision"], "NO_GO")
        self.assertIn(
            "INVALID_REVIEW_ATTESTATION:EVIDENCE-REVIEW-1",
            no_go["decision_reasons"],
        )
        self.assertIn("INSUFFICIENT_INDEPENDENT_REVIEWS", no_go["decision_reasons"])

    def test_stale_reproduction_cannot_relabel_the_report_source(self) -> None:
        mutated = copy.deepcopy(self.report)
        manifest_path = self.root / mutated["source_tree"]["manifest_path"]
        manifest = load_json_strict(manifest_path)
        manifest["commit"] = "9" * 40
        write_canonical_json(manifest_path, manifest)
        mutated["source_tree"]["commit"] = "9" * 40
        mutated["source_tree"]["tree_sha256"] = sha256_file(manifest_path)

        no_go = finalize_report(mutated, self.root, self.registry)
        self.assertEqual(no_go["decision"], "NO_GO")
        self.assertIn(
            "INVALID_REPRODUCTION_ATTESTATION", no_go["decision_reasons"]
        )

    def test_current_regeneration_failure_set_is_stable(self) -> None:
        draft = copy.deepcopy(self.report)
        draft["review_attestations"] = []
        for record in draft["coverage"]["requirements"]:
            if record["id"] in {"FR-042", "FR-043", "FR-044"}:
                record["status"] = "FAIL"

        no_go = finalize_report(draft, self.root, self.registry)
        self.assertEqual(
            no_go["decision_reasons"],
            [
                "FAILED_COVERAGE:FR-042",
                "FAILED_COVERAGE:FR-043",
                "FAILED_COVERAGE:FR-044",
                "INSUFFICIENT_INDEPENDENT_REVIEWS",
            ],
        )

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
