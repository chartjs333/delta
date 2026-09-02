"""Join portable CI and hardware evidence for an exact Campaign 02 source seal."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.campaign02 import (  # noqa: E402
    WorkloadContract,
    load_domain_manifest,
    load_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.evaluators.common import load_evaluator_profile  # noqa: E402
from deltatorrent.benchmark.gpu_environment import (  # noqa: E402
    verify_gpu_environment_outputs,
)
from deltatorrent.benchmark.measured_runner import ComponentIdentity  # noqa: E402
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id  # noqa: E402

PREDECESSOR: Final = "8e945ac9713de5898d3abdb10ad2474079a87260"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
OLD_DEFINITION: Final = "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244"
IMMUTABLE_CAMPAIGN01: Final = (
    "configs/benchmark/primary.yaml",
    "configs/benchmark/primary-definition-attestation.json",
    "configs/benchmark/primary-definition-supersession.json",
    "specs/010-wan-benchmark-and-quality/evidence/primary-exactness.json",
    "specs/010-wan-benchmark-and-quality/evidence/primary-exactness-ci-receipt.json",
    "specs/010-wan-benchmark-and-quality/evidence/primary-scientific-prerun.json",
)
EVALUATOR_SOURCES: Final = {
    "wikitext": (
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/common.py",
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/hf_backend.py",
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/wikitext.py",
    ),
    "lambada": (
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/common.py",
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/hf_backend.py",
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/lambada.py",
    ),
    "hellaswag": (
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/common.py",
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/hf_backend.py",
        "delta-worker-python/src/deltatorrent/benchmark/evaluators/hellaswag.py",
    ),
}
EXECUTION_BINDING_SOURCES: Final = (
    "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_binding.py",
    "delta-worker-python/src/deltatorrent/benchmark/definition.py",
    "delta-worker-python/src/deltatorrent/benchmark/governance.py",
    "delta-worker-python/src/deltatorrent/benchmark/primary.py",
    "delta-worker-python/src/deltatorrent/benchmark/primary_executor.py",
    "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
    "delta-worker-python/src/deltatorrent/cli/benchmark.py",
)


class Campaign02ExactSourceError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Campaign02ExactSourceError(code)


def git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def tracked_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def artifact(commit: str, path: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256_content_id(tracked_bytes(commit, path))}


def canonical_file(path: Path, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Campaign02ExactSourceError(code) from exc
    require(isinstance(value, dict) and canonical_json_bytes(value) + b"\n" == raw, code)
    return value


def verify_source_boundary(source_commit: str) -> list[str]:
    require(
        git("merge-base", PREDECESSOR, source_commit) == PREDECESSOR,
        "CAMPAIGN02_WRONG_PREDECESSOR",
    )
    for path in IMMUTABLE_CAMPAIGN01:
        require(
            tracked_bytes(source_commit, path) == tracked_bytes(PREDECESSOR, path),
            f"CAMPAIGN01_ARTIFACT_MUTATED:{path}",
        )
    changed = git("diff", "--name-only", PREDECESSOR, source_commit).splitlines()
    forbidden_patterns = (
        re.compile(r"^configs/benchmark/campaign-02/.*definition", re.IGNORECASE),
        re.compile(r"^reports/benchmark/campaigns/campaign-02/.*attestation", re.IGNORECASE),
        re.compile(r"^reports/benchmark/campaigns/campaign-02/methodology-diff\.json$"),
        re.compile(r"^reports/benchmark/campaigns/campaign-02/.*observation", re.IGNORECASE),
        re.compile(r"^reports/benchmark/campaigns/campaign-02/.*result", re.IGNORECASE),
    )
    for path in changed:
        require(
            not any(pattern.search(path) for pattern in forbidden_patterns),
            f"CAMPAIGN02_PREMATURE_ARTIFACT:{path}",
        )
    return sorted(changed)


def verify_governance() -> dict[str, object]:
    closure = canonical_file(
        ROOT
        / "reports/benchmark/campaigns"
        / OLD_DEFINITION.removeprefix("sha256:")
        / "closure.json",
        "CAMPAIGN01_CLOSURE_INVALID",
    )
    authorization = canonical_file(
        ROOT / "reports/benchmark/campaigns/campaign-02/remediation-authorization.json",
        "CAMPAIGN02_REMEDIATION_AUTHORIZATION_INVALID",
    )
    supersession = canonical_file(
        ROOT / "reports/benchmark/campaigns/campaign-02/qualification-supersession.json",
        "CAMPAIGN02_OLD_QUALIFICATION_SUPERSESSION_INVALID",
    )
    native_chain_supersession = canonical_file(
        ROOT
        / "reports/benchmark/campaigns/campaign-02/qualification-supersession-native-chain.json",
        "CAMPAIGN02_NATIVE_CHAIN_QUALIFICATION_SUPERSESSION_INVALID",
    )
    definition_supersession = canonical_file(
        ROOT
        / "reports/benchmark/campaigns/campaign-02"
        / "definition-supersession-execution-binding.json",
        "CAMPAIGN02_DEFINITION_SUPERSESSION_INVALID",
    )
    execution_binding_supersession = canonical_file(
        ROOT
        / "reports/benchmark/campaigns/campaign-02"
        / "qualification-supersession-execution-binding.json",
        "CAMPAIGN02_EXECUTION_BINDING_QUALIFICATION_SUPERSESSION_INVALID",
    )
    stage_authorization_supersession = canonical_file(
        ROOT
        / "reports/benchmark/campaigns/campaign-02"
        / "qualification-supersession-stage-authorization.json",
        "CAMPAIGN02_STAGE_AUTHORIZATION_QUALIFICATION_SUPERSESSION_INVALID",
    )
    signed_stage_governance_supersession = canonical_file(
        ROOT
        / "reports/benchmark/campaigns/campaign-02"
        / "qualification-supersession-signed-stage-governance.json",
        "CAMPAIGN02_SIGNED_STAGE_GOVERNANCE_SUPERSESSION_INVALID",
    )
    tsan_exception_lifetime_supersession = canonical_file(
        ROOT
        / "reports/benchmark/campaigns/campaign-02"
        / "qualification-supersession-tsan-exception-lifetime.json",
        "CAMPAIGN02_TSAN_EXCEPTION_LIFETIME_SUPERSESSION_INVALID",
    )
    readiness = canonical_file(
        ROOT
        / "reports/benchmark/campaigns/campaign-02"
        / "execution-binding-remediation-readiness.json",
        "CAMPAIGN02_EXECUTION_BINDING_READINESS_INVALID",
    )
    require(
        closure.get("benchmark_definition_id") == OLD_DEFINITION
        and closure.get("status") == "TERMINATED_NO_GO_AFTER_STAGE_A_BEFORE_SCIENTIFIC_EXECUTION"
        and closure.get("primary_scientific_execution_count") == 0
        and closure.get("scientific_results_exist") is False
        and closure.get("stage_a_transferable_to_new_campaign") is False,
        "CAMPAIGN01_CLOSURE_INVALID",
    )
    required_false = (
        "old_stage_a_reusable",
        "primary_execution_authorized",
        "stage_c_authorized",
        "real_wan_authorized",
        "benchmark_result_qc_authorized",
        "feature_011_authorized",
    )
    require(
        authorization.get("status") == "APPROVED_DESIGN_AND_QUALIFICATION_ONLY"
        and all(authorization.get(field) is False for field in required_false),
        "CAMPAIGN02_REMEDIATION_AUTHORIZATION_INVALID",
    )
    require(
        supersession.get("status") == "SUPERSEDED_BEFORE_CAMPAIGN02_DEFINITION"
        and supersession.get("reason") == "RUN_LEVEL_CERTIFIED_FINALIZATION_CONTRACT_INCOMPLETE"
        and supersession.get("source_commit") == "6c68dc6c7360ef8a85efdf59f6b232be6c52a849"
        and supersession.get("source_tree") == "8bba1e1a12a94bcfd176ccfc307b9425851092ea"
        and supersession.get("evidence_head") == "2157d81abd3543a3b3c4ba8655797c1a363c036f"
        and supersession.get("primary_scientific_execution_count") == 0
        and supersession.get("scientific_observations_created") is False,
        "CAMPAIGN02_OLD_QUALIFICATION_SUPERSESSION_INVALID",
    )
    require(
        native_chain_supersession.get("status") == "SUPERSEDED_BEFORE_CAMPAIGN02_DEFINITION"
        and native_chain_supersession.get("reason")
        == "NATIVE_FEATURE008_CHAIN_VERIFIER_NOT_IN_ADMISSION_PATH"
        and native_chain_supersession.get("source_commit")
        == "aa04ca82399c98e43fbe61744bd20ed17b96f87e"
        and native_chain_supersession.get("source_tree")
        == "51b989388c7386a8cb8d6711f9415022a72459ea"
        and native_chain_supersession.get("evidence_head")
        == "55187704e7310edb71e53f4114726b25cd659dc8"
        and native_chain_supersession.get("primary_scientific_execution_count") == 0
        and native_chain_supersession.get("scientific_observations_created") is False,
        "CAMPAIGN02_NATIVE_CHAIN_QUALIFICATION_SUPERSESSION_INVALID",
    )
    authorization_flags = definition_supersession.get("authorization")
    observation_counts = definition_supersession.get("observation_counts")
    require(
        definition_supersession.get("status") == "SUPERSEDED_BEFORE_EXECUTION"
        and definition_supersession.get("superseded_definition_id")
        == "sha256:a4160af58ba310135bd86d03b2427c5034ae231f481e6229314e0e61d12b97af"
        and definition_supersession.get("superseded_attestation_id")
        == "sha256:6c59421bb773e4fe12a0df3414507682b93ae008ab04e75191292ab7a64b83f7"
        and definition_supersession.get("replacement_definition_required") is True
        and definition_supersession.get("execution_authorization") == "ABSENT"
        and definition_supersession.get("benchmark_result_qc") == "ABSENT"
        and isinstance(authorization_flags, dict)
        and authorization_flags
        and all(value is False for value in authorization_flags.values())
        and observation_counts
        == {
            "primary_observations": 0,
            "scientific_observations": 0,
            "stage_a_receipts": 0,
        },
        "CAMPAIGN02_DEFINITION_SUPERSESSION_INVALID",
    )
    require(
        execution_binding_supersession.get("status") == "SUPERSEDED_BEFORE_EXECUTION"
        and execution_binding_supersession.get("reason")
        == "QUALIFIED_PRIMARY_EXECUTION_PATH_NOT_BOUND_TO_CAMPAIGN02_WORKLOAD"
        and execution_binding_supersession.get("replacement_qualification_required") is True
        and execution_binding_supersession.get("primary_observations_created") == 0,
        "CAMPAIGN02_EXECUTION_BINDING_QUALIFICATION_SUPERSESSION_INVALID",
    )
    require(
        stage_authorization_supersession.get("status")
        == "SUPERSEDED_AFTER_GOVERNANCE_REVIEW_BEFORE_EXECUTION"
        and stage_authorization_supersession.get("replacement_qualification_required") is True
        and stage_authorization_supersession.get("primary_observations_created") == 0
        and stage_authorization_supersession.get("superseded_evidence")
        == {
            "ci_receipt_head": "0d5dcc8af0e2f8563a64a85346671e64dfeb94eb",
            "evidence_overlay": "2aaf2931d8c808354d69488f1da7171a0b9576a6",
            "source_commit": "d9b8230d373e484c8fbcdd0a0444ea0ee465e8c3",
            "source_tree": "c5591557d2ef6617a08f99c91a79e570c391d306",
        },
        "CAMPAIGN02_STAGE_AUTHORIZATION_QUALIFICATION_SUPERSESSION_INVALID",
    )
    require(
        signed_stage_governance_supersession.get("status")
        == "SUPERSEDED_AFTER_GOVERNANCE_REVIEW_BEFORE_EXECUTION"
        and signed_stage_governance_supersession.get("replacement_qualification_required") is True
        and signed_stage_governance_supersession.get("primary_observations_created") == 0
        and signed_stage_governance_supersession.get("superseded_evidence")
        == {
            "ci_receipt_head": "04aad0c530aa8c83a76315f737e5caa36fe9b14e",
            "evidence_overlay": "68d2ddfed472e76197e0fcdfd29ee2a9ad601584",
            "source_commit": "b870c8a83ab89c694d1f3467804bafe5e08aac59",
            "source_tree": "1651bc3fd810ba7f47b32e1058f9c0e5d4e4cf92",
        },
        "CAMPAIGN02_SIGNED_STAGE_GOVERNANCE_SUPERSESSION_INVALID",
    )
    require(
        tsan_exception_lifetime_supersession.get("status")
        == "SUPERSEDED_AFTER_TSAN_FAILURE_BEFORE_EXECUTION"
        and tsan_exception_lifetime_supersession.get("replacement_qualification_required") is True
        and tsan_exception_lifetime_supersession.get("primary_observations_created") == 0
        and tsan_exception_lifetime_supersession.get("failed_gate")
        == {
            "check_name": "GCC TSan WAL and sidecar replay",
            "job_id": 100208818052,
            "summary": "RUNTIME_ERROR_FUTURE_SHARED_STATE_RELEASE_DATA_RACE",
            "workflow_run_id": 33618187137,
        }
        and tsan_exception_lifetime_supersession.get("superseded_evidence")
        == {
            "ci_receipt_head": "1620d6b8e66abab338cd4c056b17d3a5662bd544",
            "ci_receipt_tree": "e9fe4f3a209b8898d96528255d6b90e7be3d415d",
            "evidence_overlay": "67d038375c172e0a14d7271d2bc0f82ea22e0458",
            "evidence_overlay_tree": "fbfdebe500d00bed39f9881614ea0d990e53fa8e",
            "source_commit": "90f4b46a81f6a9ba05e0e5f3c757d008b4bdfcd9",
            "source_tree": "e188e339ec6073dc9b431658fca95627e526a7bd",
        },
        "CAMPAIGN02_TSAN_EXCEPTION_LIFETIME_SUPERSESSION_INVALID",
    )
    readiness_flags = readiness.get("authorization")
    cryptographic_governance = readiness.get("cryptographic_governance")
    require(
        readiness.get("status") == "SOURCE_REMEDIATION_IN_PROGRESS_NO_EXECUTION"
        and readiness.get("definition_created") is False
        and readiness.get("execution_authorization") == "ABSENT"
        and readiness.get("legacy_primary_path")
        == "FORBIDDEN_BY_CAMPAIGN_AND_DEFINITION_ID_REGISTRY"
        and readiness.get("next_required_gate") == "C2_021_TSAN_EXCEPTION_LIFETIME_REQUALIFICATION"
        and isinstance(readiness_flags, dict)
        and readiness_flags
        and all(value is False for value in readiness_flags.values())
        and cryptographic_governance
        == {
            "definition_verifier_implemented": True,
            "independent_votes_present": 0,
            "private_keys_committed": False,
            "stage_authorization_verifier_implemented": True,
            "status": "IMPLEMENTED_AWAITING_EXTERNAL_VALIDATOR_ACTIONS",
        },
        "CAMPAIGN02_EXECUTION_BINDING_READINESS_INVALID",
    )
    return {
        "campaign01_closure_id": sha256_content_id(canonical_json_bytes(closure)),
        "definition_supersession_id": sha256_content_id(
            canonical_json_bytes(definition_supersession)
        ),
        "execution_binding_qualification_supersession_id": sha256_content_id(
            canonical_json_bytes(execution_binding_supersession)
        ),
        "execution_binding_readiness_id": sha256_content_id(canonical_json_bytes(readiness)),
        "old_qualification_supersession_id": sha256_content_id(canonical_json_bytes(supersession)),
        "native_chain_qualification_supersession_id": sha256_content_id(
            canonical_json_bytes(native_chain_supersession)
        ),
        "stage_authorization_qualification_supersession_id": sha256_content_id(
            canonical_json_bytes(stage_authorization_supersession)
        ),
        "signed_stage_governance_supersession_id": sha256_content_id(
            canonical_json_bytes(signed_stage_governance_supersession)
        ),
        "tsan_exception_lifetime_supersession_id": sha256_content_id(
            canonical_json_bytes(tsan_exception_lifetime_supersession)
        ),
        "remediation_authorization_id": sha256_content_id(canonical_json_bytes(authorization)),
        "status": "PASS",
    }


def verify_junit(path: Path) -> dict[str, object]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise Campaign02ExactSourceError("CAMPAIGN02_PORTABLE_JUNIT_INVALID") from exc
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    require(bool(suites), "CAMPAIGN02_PORTABLE_JUNIT_EMPTY")
    tests = sum(int(item.attrib.get("tests", "0")) for item in suites)
    failures = sum(int(item.attrib.get("failures", "0")) for item in suites)
    errors = sum(int(item.attrib.get("errors", "0")) for item in suites)
    require(tests > 0 and failures == 0 and errors == 0, "CAMPAIGN02_PORTABLE_TESTS_FAILED")
    cases = sorted(
        {
            f"{case.attrib.get('classname', '')}::{case.attrib.get('name', '')}"
            for suite in suites
            for case in suite.iter("testcase")
        }
    )
    require(len(cases) == tests, "CAMPAIGN02_PORTABLE_JUNIT_DUPLICATE_CASE")
    case_names = {item.rsplit("::", 1)[-1] for item in cases}
    required_cases = {
        "test_campaign02_changed_submitted_at_invalidates_signature",
        "test_campaign02_catalog_compiler_reverifies_every_detached_signature",
        "test_campaign02_compiler_creates_exact_15_plan_matrix_per_stage",
        "test_campaign02_distinct_workload_domain_and_ticket_plan_ids",
        "test_campaign02_forged_signature_is_rejected",
        "test_campaign02_legacy_primary_adapter_is_forbidden",
        "test_campaign02_plan_total_cannot_fall_back_to_per_ticket_b",
        "test_campaign02_signature_over_noncanonical_bytes_is_rejected",
        "test_caller_constructed_verified_attestation_cannot_enter_binder",
        "test_exact_superseded_a4160_is_parseable_but_all_adapter_execution_is_forbidden",
        "test_stage_a_authorizes_only_exact_stage_a_catalog_plans",
        "test_stage_authorization_rejects_generic_extra_and_inexact_plan_sets",
        "test_stage_b_and_c_require_exact_predecessor_gate_receipts",
        "test_unsigned_and_self_created_stage_authorization_are_rejected",
        "test_stage_authorization_vote_artifacts_are_strictly_typed_and_round_trip",
        "test_changed_signed_stage_authorization_issued_at_is_rejected",
        "test_forged_stage_authorization_signature_is_rejected",
        "test_wrong_stage_authorization_validator_set_is_rejected",
        "test_stage_b_rejects_random_fail_and_other_definition_predecessors",
        "test_stage_c_requires_exact_stage_a_and_stage_b_receipt_set",
        "test_missing_runner_role_and_cross_stage_roles_are_rejected",
        "test_independent_stages_have_unique_bft_round_contexts",
        "test_duplicate_bft_round_context_across_independent_stages_is_rejected",
    }
    require(
        required_cases <= case_names
        and sum(
            name.startswith("test_all_legacy_primary_cli_routes_reject_campaign02[")
            for name in case_names
        )
        == 4,
        "CAMPAIGN02_EXECUTION_BINDING_PORTABLE_COVERAGE_MISSING",
    )
    require(
        sum(
            name.startswith(
                "test_exact_a4160_and_unsigned_6c594_are_rejected_by_every_legacy_cli_route["
            )
            for name in case_names
        )
        == 4,
        "CAMPAIGN02_SUPERSEDED_DEFINITION_PORTABLE_COVERAGE_MISSING",
    )
    manifest = {
        "errors": errors,
        "failures": failures,
        "test_cases": cases,
        "tests": tests,
    }
    return {
        "errors": errors,
        "failures": failures,
        # Durations, timestamps and absolute paths are runner-local metadata.  The
        # exact-source identity is the canonical set of passing test cases.
        "junit_id": sha256_content_id(canonical_json_bytes(manifest)),
        "status": "PASS",
        "test_cases": cases,
        "tests": tests,
    }


def verify_cross_verifier_corpus() -> dict[str, object]:
    path = ROOT / "delta-protocol/fixtures/010/campaign-02/native-chain-conformance-v1.json"
    corpus = canonical_file(path, "CAMPAIGN02_NATIVE_CHAIN_CORPUS_INVALID")
    cases = corpus.get("cases")
    require(
        corpus.get("type_name") == "CAMPAIGN02_NATIVE_CHAIN_CONFORMANCE_CORPUS"
        and isinstance(cases, list)
        and len(cases) == 12,
        "CAMPAIGN02_NATIVE_CHAIN_CORPUS_INVALID",
    )
    names = {str(item.get("name")) for item in cases if isinstance(item, dict)}
    required = {
        "incomplete-shard-coverage",
        "invalid-nested-content-id",
        "noncanonical-squared-norm",
        "reversed-apc-weights",
        "unordered-norm-entries",
        "unordered-seed-shares",
        "unordered-signers",
        "unreduced-rational",
        "valid-complete-chain",
        "wrong-required-key-order",
        "wrong-seed-parent",
        "zero-denominator",
    }
    require(names == required, "CAMPAIGN02_NATIVE_CHAIN_CORPUS_CASES_INVALID")
    accepted = 0
    for item in cases:
        require(isinstance(item, dict), "CAMPAIGN02_NATIVE_CHAIN_CORPUS_INVALID")
        expected = item.get("expected")
        require(
            expected in {"ACCEPT", "REJECT"}
            and item.get("python_admission") == expected
            and item.get("native_chain_verifier") == expected
            and item.get("c_abi") == expected,
            "CAMPAIGN02_NATIVE_CHAIN_CORPUS_DECISION_DIVERGENCE",
        )
        accepted += expected == "ACCEPT"
    require(accepted == 1, "CAMPAIGN02_NATIVE_CHAIN_CORPUS_ACCEPT_COUNT_INVALID")
    return {
        "case_count": len(cases),
        "content_id": sha256_content_id(path.read_bytes()),
        "status": "PASS",
    }


def verify_execution_binding(
    source_commit: str,
    source_tree: str,
    workload: WorkloadContract,
) -> dict[str, object]:
    domain_manifest = load_domain_manifest(
        ROOT / "configs/benchmark/campaign-02/domain-manifest-v1.json"
    )
    ticket_plan = load_ticket_plan(
        ROOT / "configs/benchmark/campaign-02/ticket-plan-v1.json",
        workload,
        domain_manifest,
    )
    identities = {
        workload.content_id,
        domain_manifest.content_id,
        ticket_plan.content_id,
    }
    require(len(identities) == 3, "CAMPAIGN02_EXECUTION_BINDING_ID_ALIAS")
    require(
        ticket_plan.workload_contract_id == workload.content_id
        and ticket_plan.domain_manifest_id == domain_manifest.content_id
        and len(ticket_plan.tickets) == 32
        and tuple(item.ordinal for item in ticket_plan.tickets) == tuple(range(32))
        and all(item.tokens_per_optimizer_step == 1024 for item in ticket_plan.tickets)
        and all(item.optimizer_steps == 32 for item in ticket_plan.tickets)
        and all(item.tokens_per_ticket == 32_768 for item in ticket_plan.tickets)
        and sum(item.tokens_per_ticket for item in ticket_plan.tickets) == 1_048_576,
        "CAMPAIGN02_EXECUTION_BINDING_TICKET_PLAN_INVALID",
    )
    source_files = [artifact(source_commit, path) for path in EXECUTION_BINDING_SOURCES]
    manifest = {
        "campaign_id": "campaign-02",
        "domain_manifest_id": domain_manifest.content_id,
        "formal_semantics_id": FORMAL_ID,
        "source_commit": source_commit,
        "source_files": source_files,
        "source_tree": source_tree,
        "ticket_plan_id": ticket_plan.content_id,
        "type_name": "CAMPAIGN02_EXECUTION_BINDING_IMPLEMENTATION_IDENTITY",
        "workload_contract_id": workload.content_id,
    }
    return {
        "base_plan_count": 15,
        "catalog_plan_count": 45,
        "certified_result_arms": [
            "flat-embedded",
            "flat-sidecar",
            "hierarchy-embedded",
            "hierarchy-sidecar",
        ],
        "domain_manifest_id": domain_manifest.content_id,
        "implementation_id": sha256_content_id(
            b"deltareduce.010.campaign02-execution-binding-implementation.v1\0"
            + canonical_json_bytes(manifest)
        ),
        "implementation_manifest": manifest,
        "legacy_campaign02_primary_path": "FAIL_CLOSED",
        "plan_catalog_execution_authorized": False,
        "plans_per_stage": 15,
        "certified_round_context_count": 36,
        "stage_authorization_authority": "DETACHED_ED25519_QUORUM_PROOF",
        "stage_execution_model": "INDEPENDENT_BFT_RUNS",
        "ticket_identity_scope": "ROUND_ID_PLUS_TICKET_TEMPLATE_ID",
        "typed_predecessor_receipts_required": True,
        "optimizer_steps_per_ticket": 32,
        "reference_result_arms": ["scientific-reference"],
        "status": "PASS",
        "ticket_count": 32,
        "ticket_plan_id": ticket_plan.content_id,
        "tokens_per_ticket": 32_768,
        "total_tokens_per_arm_run": 1_048_576,
        "workload_contract_id": workload.content_id,
    }


def implementation_id(
    source_commit: str,
    source_tree: str,
    evaluator_id: str,
    profile_id: str,
    gpu_lock_id: str,
) -> tuple[str, dict[str, object]]:
    sources = [artifact(source_commit, path) for path in EVALUATOR_SOURCES[evaluator_id]]
    manifest: dict[str, object] = {
        "evaluator_id": evaluator_id,
        "formal_semantics_id": FORMAL_ID,
        "gpu_environment_lock_id": gpu_lock_id,
        "profile_id": profile_id,
        "source_commit": source_commit,
        "source_files": sources,
        "source_tree": source_tree,
        "type_name": "EVALUATOR_IMPLEMENTATION_IDENTITY",
    }
    return sha256_content_id(canonical_json_bytes(manifest)), manifest


def policy_id(policy: dict[str, Any], field: str) -> str:
    value = policy.get(field)
    require(isinstance(value, dict), f"CAMPAIGN02_RUNNER_POLICY_INVALID:{field}")
    return sha256_content_id(canonical_json_bytes(value))


def component_identity(
    component: str,
    paths: tuple[str, ...],
    *,
    source_commit: str,
    source_tree: str,
    environment_id: str,
    image_id: str,
    hardware_class_id: str,
    policy: dict[str, Any],
    output_schema_ids: tuple[str, ...],
) -> ComponentIdentity:
    return ComponentIdentity(
        component=component,
        source_commit=source_commit,
        source_tree=source_tree,
        executable_hashes=tuple(
            sorted((path, artifact(source_commit, path)["sha256"]) for path in paths)
        ),
        environment_id=environment_id,
        image_id=image_id,
        hardware_compatibility_class_id=hardware_class_id,
        model_data_staging_policy_id=policy_id(policy, "model_data_staging_policy"),
        timeout_policy_id=policy_id(policy, "timeout_policy"),
        output_schema_ids=output_schema_ids,
        create_only_store_policy_id=policy_id(policy, "create_only_store_policy"),
    )


def build(source_commit: str, portable_junit: Path, hardware_evidence: Path) -> dict[str, object]:
    source_tree = git("show", "-s", "--format=%T", source_commit)
    require(re.fullmatch(r"[0-9a-f]{40}", source_tree) is not None, "SOURCE_TREE_INVALID")
    changed = verify_source_boundary(source_commit)
    governance = verify_governance()
    workload = load_workload_contract(ROOT / "configs/benchmark/campaign-02/workload-v2.json")
    require(
        workload.tokens_per_optimizer_step == 1024
        and workload.optimizer_steps_per_ticket == 32
        and workload.tokens_per_ticket == 32_768
        and workload.ticket_count == 32
        and workload.total_tokens_per_arm_run == 1_048_576,
        "CAMPAIGN02_WORKLOAD_CONTRACT_INVALID",
    )
    execution_binding = verify_execution_binding(source_commit, source_tree, workload)
    gpu_lock = verify_gpu_environment_outputs(ROOT)
    require(
        gpu_lock.document["required_packages"].get("cryptography") == "46.0.7",
        "CAMPAIGN02_GOVERNANCE_CRYPTOGRAPHY_NOT_SOURCE_LOCKED",
    )
    portable = verify_junit(portable_junit)
    cross_verifier_corpus = verify_cross_verifier_corpus()
    hardware = canonical_file(hardware_evidence, "CAMPAIGN02_HARDWARE_EVIDENCE_INVALID")
    require(
        hardware.get("status") == "PASS"
        and hardware.get("fixture_class") == "NON_PRIMARY_HARDWARE_QUALIFICATION"
        and hardware.get("primary_scientific_execution_count") == 0
        and hardware.get("scientific_observations_created") is False
        and hardware.get("source") == {"commit": source_commit, "tree": source_tree},
        "CAMPAIGN02_HARDWARE_EVIDENCE_INVALID",
    )
    hardware_environment = hardware.get("environment")
    require(isinstance(hardware_environment, dict), "CAMPAIGN02_HARDWARE_ENVIRONMENT_INVALID")
    require(
        hardware_environment.get("gpu_environment_lock_id") == gpu_lock.content_id
        and hardware_environment.get("sbom_id") == gpu_lock.sbom_id
        and hardware_environment.get("oci_image_digest") == gpu_lock.document["oci_image_digest"],
        "CAMPAIGN02_HARDWARE_ENVIRONMENT_INVALID",
    )
    environment_id = str(hardware_environment.get("environment_id"))
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", environment_id) is not None, "ENV_ID_INVALID")
    profiles = tuple(
        load_evaluator_profile(ROOT / f"configs/benchmark/campaign-02/evaluators/{name}-v1.json")
        for name in ("wikitext", "lambada", "hellaswag")
    )
    evaluator_identities: dict[str, dict[str, object]] = {}
    for profile in profiles:
        identity, manifest = implementation_id(
            source_commit,
            source_tree,
            profile.evaluator_id,
            profile.content_id,
            gpu_lock.content_id,
        )
        evaluator_identities[profile.evaluator_id] = {
            "implementation_id": identity,
            "manifest": manifest,
        }
    policy = canonical_file(
        ROOT / "configs/benchmark/campaign-02/runner-policy-v1.json",
        "CAMPAIGN02_RUNNER_POLICY_INVALID",
    )
    environment_policy = canonical_file(
        ROOT / "configs/benchmark/campaign-02/gpu-environment-policy-v1.json",
        "GPU_ENVIRONMENT_POLICY_INVALID",
    )
    hardware_class_id = sha256_content_id(
        canonical_json_bytes(environment_policy["hardware_compatibility_class"])
    )
    schema_ids = tuple(
        sha256_content_id(tracked_bytes(source_commit, path)) for path in policy["output_schemas"]
    )
    common = {
        "source_commit": source_commit,
        "source_tree": source_tree,
        "environment_id": environment_id,
        "image_id": str(gpu_lock.document["oci_image_digest"]),
        "hardware_class_id": hardware_class_id,
        "policy": policy,
        "output_schema_ids": schema_ids,
    }
    scientific = component_identity(
        "PRIMARY_SCIENTIFIC_RUNNER",
        (
            "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
            "delta-worker-python/src/deltatorrent/benchmark/feature008_admission.py",
            "delta-worker-python/src/deltatorrent/benchmark/measured_runner.py",
            "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
            "delta-worker-python/src/deltatorrent/qlora/backend.py",
            "delta-worker-python/src/deltatorrent/qlora/trainer.py",
            "delta-core-cpp/include/delta/certificates/contracts.hpp",
            "delta-core-cpp/include/delta/certificates/verifier.hpp",
            "delta-core-cpp/src/certificates/contracts.cpp",
            "delta-core-cpp/src/certificates/verifier.cpp",
            "delta-ffi/include/delta_abi.h",
            "delta-ffi/src/certificate_chain_abi.cpp",
            "delta-ffi/src/certificates_abi.cpp",
            "delta-runtime-cpp/include/delta/runtime/bounded_mpsc.hpp",
            "delta-runtime-cpp/include/delta/runtime/runtime.hpp",
            "delta-runtime-cpp/src/runtime.cpp",
            "delta-runtime-cpp/src/wal.cpp",
            "delta-runtime-cpp/src/wal.hpp",
        ),
        **common,
    )
    evaluation = component_identity(
        "PRIMARY_EVALUATION_RUNNER",
        tuple(
            sorted(
                {
                    "delta-worker-python/src/deltatorrent/benchmark/measured_runner.py",
                    "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
                    "delta-worker-python/src/deltatorrent/benchmark/feature008_admission.py",
                    *(path for paths in EVALUATOR_SOURCES.values() for path in paths),
                }
            )
        ),
        **common,
    )
    writer = component_identity(
        "PRIMARY_OBSERVATION_WRITER",
        (
            "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
            "delta-worker-python/src/deltatorrent/benchmark/evaluators/common.py",
            "delta-worker-python/src/deltatorrent/benchmark/feature008_admission.py",
            "delta-worker-python/src/deltatorrent/benchmark/measured_runner.py",
            "delta-worker-python/src/deltatorrent/benchmark/observation_writer.py",
            "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
        ),
        **common,
    )
    source_paths = sorted(
        {
            *EVALUATOR_SOURCES["wikitext"],
            *EVALUATOR_SOURCES["lambada"],
            *EVALUATOR_SOURCES["hellaswag"],
            *(
                path
                for identity in (scientific, evaluation, writer)
                for path, _ in identity.executable_hashes
            ),
            "configs/benchmark/campaign-02/gpu-environment-lock-v1.json",
            "configs/benchmark/campaign-02/gpu-environment-policy-v1.json",
            "configs/benchmark/campaign-02/gpu-linux-x86_64.lock",
            "configs/benchmark/campaign-02/domain-manifest-v1.json",
            "configs/benchmark/campaign-02/gpu-windows-x86_64.lock",
            "configs/benchmark/campaign-02/runner-policy-v1.json",
            "configs/benchmark/campaign-02/ticket-plan-v1.json",
            "configs/benchmark/campaign-02/workload-v2.json",
            "delta-protocol/fixtures/010/campaign-02/native-chain-conformance-v1.json",
            *EXECUTION_BINDING_SOURCES,
        }
    )
    return {
        "checks": [
            "CAMPAIGN01_TERMINAL_CLOSURE_AND_IMMUTABILITY_PASS",
            "CAMPAIGN02_REMEDIATION_ONLY_AUTHORIZATION_PASS",
            "EXPLICIT_TICKET_AND_ARM_TOKEN_RECONCILIATION_PASS",
            "SEPARATE_HASH_LOCKED_CPU_AND_GPU_ENVIRONMENTS_PASS",
            "PINNED_OCI_CUDA_IMAGE_AND_SBOM_PASS",
            "THREE_PREREGISTERED_MEASURED_EVALUATORS_AND_GOLDENS_PASS",
            "SOURCE_BOUND_SCIENTIFIC_EVALUATION_RUNNERS_PASS",
            "AUTHORITATIVE_NATIVE_FEATURE008_CHAIN_ADMISSION_PASS",
            "CROSS_VERIFIER_CONFORMANCE_CORPUS_PASS",
            "FINAL_CHECKPOINT_APPLY_QC_RUNTIME_WAL_BINDING_PASS",
            "NATIVE_CHAIN_ADMISSION_RECEIPT_WRITER_BINDING_PASS",
            "CREATE_ONLY_TYPED_OBSERVATION_WRITER_PASS",
            "DISTINCT_WORKLOAD_DOMAIN_AND_TICKET_IDENTITIES_PASS",
            "EXACT_15_PLAN_PER_STAGE_CAMPAIGN02_CATALOG_PASS",
            "PLAN_CATALOG_COMPILES_WITHOUT_EXECUTION_AUTHORIZATION_PASS",
            "EXACT_STAGE_AUTHORIZATION_AND_PREDECESSOR_ENFORCEMENT_PASS",
            "SIGNED_STAGE_AUTHORIZATION_QUORUM_PROOF_PASS",
            "TYPED_STAGE_GATE_RECEIPT_LINEAGE_PASS",
            "MANDATORY_STAGE_RUNNER_ROLE_PASS",
            "UNIQUE_STAGE_BFT_ROUND_CONTEXT_PASS",
            "ROUND_SCOPED_TICKET_TEMPLATE_IDENTITY_PASS",
            "LEGACY_PRIMARY_PATH_FAIL_CLOSED_BY_DEFINITION_ID_REGISTRY_PASS",
            "ED25519_DETACHED_GOVERNANCE_VERIFIER_BOUND_TO_BINDER_PASS",
            "VOTE_SIGNER_KEY_AND_SUBMITTED_AT_SIGNATURE_BINDING_PASS",
            "SUPERSEDED_DEFINITION_AND_QUALIFICATION_NO_EXECUTION_PASS",
            "PORTABLE_EXACT_SOURCE_TESTS_PASS",
            "DESIGNATED_GPU_HARDWARE_QUALIFICATION_PASS",
            "NO_PRIMARY_OBSERVATION_OR_DEFINITION_CREATED",
        ],
        "components": {
            "evaluation_runner": {
                "content_id": evaluation.content_id,
                "value": evaluation.document,
            },
            "observation_writer": {"content_id": writer.content_id, "value": writer.document},
            "scientific_runner": {
                "content_id": scientific.content_id,
                "value": scientific.document,
            },
        },
        "cross_verifier_corpus": cross_verifier_corpus,
        "definition_construction_eligible_after_remediation_merge": True,
        "execution_binding": execution_binding,
        "evaluator_implementations": evaluator_identities,
        "formal_semantics_id": FORMAL_ID,
        "governance": governance,
        "gpu_environment": {
            "environment_id": environment_id,
            "hardware_evidence_id": sha256_content_id(hardware_evidence.read_bytes()),
            "hardware_id": hardware_environment["runner_hardware_id"],
            "image_id": gpu_lock.document["oci_image_digest"],
            "lock_id": gpu_lock.content_id,
            "sbom_id": gpu_lock.sbom_id,
            "status": "PASS",
        },
        "old_stage_a_reusable": False,
        "portable_tests": portable,
        "primary_execution_authorized": False,
        "primary_scientific_execution_count": 0,
        "schema_version": "1.0.0",
        "scientific_observations_created": False,
        "source": {
            "artifacts": [artifact(source_commit, path) for path in source_paths],
            "changed_path_count": len(changed),
            "commit": source_commit,
            "tree": source_tree,
        },
        "status": "PASS",
        "task_ids": [
            "C2-001",
            "C2-002",
            "C2-003",
            "C2-004",
            "C2-005",
            "C2-006",
            "C2-007",
            "C2-008",
            "C2-009",
            "C2-010",
            "C2-011",
            "C2-012",
            "C2-017",
            "C2-018",
            "C2-019",
            "C2-020",
            "C2-025",
            "C2-026",
            "C2-027",
        ],
        "type_name": "CAMPAIGN02_EXACT_SOURCE_QUALIFICATION",
        "workload": {
            "optimizer_steps_per_ticket": workload.optimizer_steps_per_ticket,
            "ticket_count": workload.ticket_count,
            "tokens_per_optimizer_step": workload.tokens_per_optimizer_step,
            "tokens_per_ticket": workload.tokens_per_ticket,
            "total_tokens_per_arm_run": workload.total_tokens_per_arm_run,
            "workload_id": workload.content_id,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--portable-junit", type=Path, required=True)
    parser.add_argument("--hardware-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = build(arguments.source_commit, arguments.portable_junit, arguments.hardware_evidence)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                "primary_execution_authorized": False,
                "source_commit": arguments.source_commit,
                "source_tree": report["source"]["tree"],
                "status": "PASS",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
