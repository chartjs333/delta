"""Freeze the exact primary Feature-010 benchmark definition and preregistration inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.definition import (  # noqa: E402
    FORMAL_SEMANTICS_ID,
    BenchmarkDefinition,
)
from deltatorrent.benchmark.review import (  # noqa: E402
    GovernanceAttestation,
    GovernanceVote,
)
from deltatorrent.protocol.canonical import canonical_json_bytes  # noqa: E402

OUTPUT_ROOT: Final = ROOT / "configs/benchmark"
FORMAL_REPORT_ID: Final = "sha256:b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"
FEATURE_REPORT_IDS: Final = (
    "sha256:2cd392aafaba1ab70cc0a6919cae9580955c742f9f92296f54a570af29dca769",
    "sha256:9dbd9c7bda30d6ebe9b70f33a1a16d49a2b837b140d24f87becd433f05e3dccb",
    "sha256:7f7f86ad5021107688277ab626b266a61c7e633eb5c401e44c7778b98733dad6",
    "sha256:d16f9cfc62efe95e902b301823c136c0530db68b1cfb48788c6a239ade123800",
    "sha256:2b45bf2dba25b15db624a02ee11e530a967961220e414ab04054428d44f59ef3",
    "sha256:fb7b9f572923e3d8a8e24195f630474ed836ff0a7ef6454b7d31d3f930a4cc9c",
    "sha256:95b312b45f3c2df4293ceaa0cbb16dd1e89c5d12a86c890211353a45798516ef",
)
CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


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


def object_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def tracked_id(commit: str, path: str) -> str:
    return "sha256:" + hashlib.sha256(tracked_bytes(commit, path)).hexdigest()


def profile(kind: str, **fields: object) -> dict[str, object]:
    return {
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "kind": kind,
        "schema_version": "1.0.0",
        **fields,
    }


def external_dependencies() -> dict[str, object]:
    return profile(
        "IMMUTABLE_MODEL_DATA_EVALUATION_DEPENDENCIES",
        artifacts=[
            {
                "license": "MIT",
                "repository": "microsoft/Phi-3.5-mini-instruct",
                "revision": "2fe192450127e6a83f7441aef6e3ca586c338b77",
                "role": "BASE_MODEL_AND_TOKENIZER",
                "tokenizer_sha256": (
                    "9e556afd44213b6bd1be2b850ebbbd98f5481437a8021afaf58ee7fb1818d347"
                ),
            },
            {
                "file": "wikitext-2-raw-v1/train-00000-of-00001.parquet",
                "license": "CC-BY-SA-3.0-or-later",
                "license_evidence": [
                    "repository-metadata:CC-BY-SA-3.0",
                    "dataset-card:CC-BY-SA-4.0",
                ],
                "repository": "Salesforce/wikitext",
                "revision": "b08601e04326c79dfdd32d625aee71d232d685c3",
                "role": "TRAIN",
                "sha256": "e83889baabc497075506f91975be5fac0d45c5290b6b20582c8cd1e853d0c9f7",
                "size_bytes": 6_357_543,
            },
            {
                "file": "wikitext-2-raw-v1/validation-00000-of-00001.parquet",
                "license": "CC-BY-SA-3.0-or-later",
                "license_evidence": [
                    "repository-metadata:CC-BY-SA-3.0",
                    "dataset-card:CC-BY-SA-4.0",
                ],
                "repository": "Salesforce/wikitext",
                "revision": "b08601e04326c79dfdd32d625aee71d232d685c3",
                "role": "VALIDATION_AND_PER_DOMAIN",
                "sha256": "204929b7ff9d6184953f867dedb860e40aa69c078fc1e54b3baaa8fb28511c4c",
                "size_bytes": 657_209,
            },
            {
                "file": "data/lambada_test.jsonl",
                "license": "MIT-Modified",
                "repository": "EleutherAI/lambada_openai",
                "revision": "900124bf3b8235c6daf21033af9948b3f07346c4",
                "role": "DOWNSTREAM_LAMBADA",
                "sha256": "4aa8d02cd17c719165fc8a7887fddd641f43fcafa4b1c806ca8abc31fabdb226",
                "size_bytes": 1_819_752,
            },
            {
                "file": "data/validation-00000-of-00001.parquet",
                "license": "MIT",
                "repository": "Rowan/hellaswag",
                "revision": "218ec52e09a7e7462a5400043bb9a69a41d06b76",
                "role": "POST_TRAINING_HELLASWAG",
                "sha256": "899813071e1e95efafec90f856e1987d2150fa4d020fc005df6962c259f660cd",
                "size_bytes": 6_315_951,
            },
        ],
        download_policy="FETCH_BY_REVISION_THEN_VERIFY_SHA256_BEFORE_USE",
        raw_weights_committed=False,
    )


def workload() -> dict[str, object]:
    return profile(
        "PRIMARY_WORKLOAD",
        B=32_768,
        H=32,
        domain_mixture=[{"denominator": 1, "domain_id": "wikitext-en", "numerator": 1}],
        gradient_accumulation_steps=4,
        microbatch_size=1,
        optimizer={"learning_rate": "0.0001", "type": "ADAMW", "weight_decay": "0.0"},
        parent_model_policy="EXACT_BASE_HASH_FOR_ALL_ARMS",
        repetitions=3,
        seeds=[2_026_090_101, 2_026_090_102, 2_026_090_103],
        sequence_length=256,
        ticket_count=32,
        tokens_per_optimizer_step=1024,
    )


def arms(workload_id: str) -> dict[str, object]:
    common: dict[str, object] = {
        "mandatory": True,
        "workload_identity": workload_id,
    }
    values = [
        {
            **common,
            "allowed_differences": ["arithmetic", "deployment_profile", "topology"],
            "arm_id": "scientific-reference",
            "deployment_profile": "PYTHON",
            "kind": "SCIENTIFIC_REFERENCE",
            "topology": "SINGLE_NODE_REFERENCE",
        },
        {
            **common,
            "allowed_differences": ["arithmetic", "deployment_profile", "topology"],
            "arm_id": "flat-embedded",
            "deployment_profile": "EMBEDDED_FFM",
            "kind": "CERTIFIED_QLORA",
            "topology": "FLAT_BFT",
        },
        {
            **common,
            "allowed_differences": ["arithmetic", "deployment_profile", "topology"],
            "arm_id": "hierarchy-embedded",
            "deployment_profile": "EMBEDDED_FFM",
            "kind": "CERTIFIED_QLORA",
            "topology": "HIERARCHICAL_BFT",
        },
        {
            **common,
            "allowed_differences": ["arithmetic", "deployment_profile", "topology"],
            "arm_id": "flat-sidecar",
            "deployment_profile": "ISOLATED_SIDECAR",
            "kind": "CERTIFIED_QLORA",
            "topology": "FLAT_BFT",
        },
        {
            **common,
            "allowed_differences": ["arithmetic", "deployment_profile", "topology"],
            "arm_id": "hierarchy-sidecar",
            "deployment_profile": "ISOLATED_SIDECAR",
            "kind": "CERTIFIED_QLORA",
            "topology": "HIERARCHICAL_BFT",
        },
    ]
    return profile("PRIMARY_ARMS", arms=values)


def networks() -> dict[str, object]:
    profiles = [
        {
            "bandwidth_kbps": 1_000_000,
            "disconnect_ms": 0,
            "duplication_ppm": 0,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "jitter_ms": 0,
            "loss_ppm": 0,
            "profile_id": "lan-control",
            "reordering_ppm": 0,
            "rtt_ms": 1,
            "schema_version": "1.0.0",
            "seed": 10_001,
            "type_name": "NETWORK_PROFILE",
        },
        {
            "bandwidth_kbps": 100_000,
            "disconnect_ms": 2_000,
            "duplication_ppm": 100,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "jitter_ms": 5,
            "loss_ppm": 1_000,
            "profile_id": "wan-regional",
            "reordering_ppm": 500,
            "rtt_ms": 40,
            "schema_version": "1.0.0",
            "seed": 10_002,
            "type_name": "NETWORK_PROFILE",
        },
        {
            "bandwidth_kbps": 25_000,
            "disconnect_ms": 4_000,
            "duplication_ppm": 500,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "jitter_ms": 20,
            "loss_ppm": 5_000,
            "profile_id": "wan-intercontinental",
            "reordering_ppm": 2_000,
            "rtt_ms": 160,
            "schema_version": "1.0.0",
            "seed": 10_003,
            "type_name": "NETWORK_PROFILE",
        },
    ]
    real_wan = {
        "approval_evidence_required": True,
        "kind": "REAL_WAN_PREPILOT",
        "measured_path_conditions_required": True,
        "must_follow_emulated_pass": True,
        "profile_id": "real-wan-certified-environment-variant",
        "public_internet_not_used_by_deterministic_tests": True,
    }
    return profile("PRIMARY_NETWORK_PROFILES", profiles=profiles, real_wan_variant=real_wan)


def faults() -> dict[str, object]:
    scenarios = [
        ("initial-seed-loss-complete-union", "RECOVERED"),
        ("initial-seed-loss-incomplete-union", "PIECE_UNAVAILABLE"),
        ("worker-loss-10pct-sufficient", "APPLIED"),
        ("worker-loss-concentrated", "ABORTED"),
        ("validator-crash-restart", "RECOVERED"),
        ("storage-crash-restart", "RECOVERED"),
        ("regional-delay-eventual-synchrony", "APPLIED"),
        ("regional-partition-hard-deadline", "ABORTED"),
    ]
    events = [
        ("worker-loss-10pct", "WORKER", "CRASH", 100, "APPLIED"),
        ("validator-crash", "VALIDATOR", "CRASH", 120, "VIEW_CHANGE"),
        ("validator-restart", "VALIDATOR", "RESTART", 140, "RECOVERED"),
        ("storage-crash", "STORAGE", "CRASH", 160, "RETRIEVAL"),
        ("storage-restart", "STORAGE", "RESTART", 180, "RECOVERED"),
        ("regional-delay", "REGION", "DELAY", 200, "APPLIED"),
        ("regional-partition", "REGION", "PARTITION", 240, "ABORTED"),
    ]
    trace_profile = {
        "events": [
            {
                "action": action,
                "actor_class": actor,
                "assumptions_hold": True,
                "at_step": step,
                "event_id": event_id,
                "expected_outcome": outcome,
            }
            for event_id, actor, action, step, outcome in events
        ],
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "profile_id": "primary-crash-restart-partition-v1",
        "schema_version": "1.0.0",
        "type_name": "FAULT_PROFILE",
    }
    return profile(
        "PRIMARY_FAULT_AND_ATTACK_PROFILES",
        attacks=[
            "ac-mutation",
            "certificate-downgrade",
            "conflicting-apply",
            "conflicting-config",
            "conflicting-vote",
            "duplicate-root",
            "frankenstein-shard",
            "incomplete-root",
            "seed-before-isc",
            "unsafe-accumulator",
            "wrong-epoch",
        ],
        retry_policy={"hard_deadline_action": "CERTIFIED_ABORT", "unbounded_retries": False},
        scenarios=[
            {"expected_terminal": outcome, "scenario_id": name} for name, outcome in scenarios
        ],
        trace_profile=trace_profile,
    )


def runtime_policy(commit: str) -> dict[str, object]:
    return profile(
        "PRIMARY_RUNTIME_AND_COMPATIBILITY",
        compiler_contract="GCC_14_2_AND_CLANG_20_1_8_CXX20_CXX23_STRICT",
        deployment_profiles=["EMBEDDED_FFM", "ISOLATED_SIDECAR"],
        exact_physical_runner_profile="configs/qlora/8gb-reference.json",
        execution_image="NONE_LOCAL_PHYSICAL_PINNED_SOFTWARE",
        isolation_policy="COMPARE_BOTH",
        jdk_contract="JDK_25_AND_26_FFM_WITH_JDK17_TRANSPORT_CONFORMANCE",
        jdk_compatibility=["25.0.4.1", "26.0.2"],
        mismatch_action="REJECT_BEFORE_RUN",
        native_runtime_evidence_id=tracked_id(
            commit,
            "specs/010-wan-benchmark-and-quality/evidence/runtime-adapters.json",
        ),
        protocol_authority="CXX_ONLY",
        pilot_selection={
            "cross_jdk_agreement_required": True,
            "eligible_profiles": ["EMBEDDED_FFM", "ISOLATED_SIDECAR"],
            "minimum_repetitions_per_jdk_and_profile": 5,
            "require_crash_containment": True,
            "selection_rule": "REQUIRE_CRASH_CONTAINMENT_THEN_LOWEST_P95_LATENCY",
        },
        process_profile_repetitions=5,
        python_contract="CPYTHON_3_12_UV_LOCKED",
        sanitizer_campaigns={
            "address_undefined": {
                "executions": 1,
                "targets": [
                    "delta_runtime_benchmark_test",
                    "delta_ffi_benchmark_test",
                    "delta_runtime_test",
                    "delta_certificates_test",
                ],
            },
            "parser_fuzz": {
                "certificate_contract_mutations": 2_000,
                "executions": 1,
                "ffi_parser_abi_cases": 2_052,
                "targets": [
                    "delta_certificate_contract_fuzz",
                    "delta_fixedpoint_parser_fuzz",
                    "delta_distribution_parser_fuzz",
                    "delta_hierarchy_parser_fuzz",
                    "delta_scheduling_contract_fuzz",
                    "delta_ffi_fuzz_smoke_test",
                ],
            },
            "thread": {
                "executions": 1,
                "targets": [
                    "delta_runtime_benchmark_test",
                    "delta_runtime_test",
                    "delta_certificates_test",
                ],
            },
        },
        supported_architectures=["x86_64"],
    )


def evidence_policy() -> dict[str, object]:
    return profile(
        "PRIMARY_EVIDENCE_POLICY",
        artifact_addressing="SHA256_CONTENT_ADDRESSED",
        decision_function="ALL_MANDATORY",
        mandatory_gates=[
            "EVIDENCE",
            "FORMAL_REGRESSION",
            "PROCESS_ISOLATION",
            "PROTOCOL_EXACTNESS",
            "QUALITY",
            "RESILIENCE",
            "WAN_P2P",
        ],
        missing_run_policy="FAIL_CLOSED",
        raw_private_data_committed=False,
        retention="MANIFESTS_AND_LICENSED_OR_AUTHORIZED_CONTENT_REFS",
        threshold_override_allowed=False,
    )


def licenses() -> dict[str, object]:
    return profile(
        "PRIMARY_LICENSE_POLICY",
        allowed=["MIT", "MIT-Modified", "CC-BY-SA-3.0-or-later"],
        access_policy="PUBLIC_IMMUTABLE_REVISION_AND_VERIFIED_FILE_SHA256",
        attribution_manifest_required=True,
        restricted_material_in_repository=False,
    )


def metrics(commit: str) -> dict[str, object]:
    implementations = {
        "efficiency": tracked_id(
            commit, "delta-worker-python/src/deltatorrent/benchmark/efficiency.py"
        ),
        "quality": tracked_id(commit, "delta-worker-python/src/deltatorrent/benchmark/quality.py"),
        "resilience": tracked_id(
            commit, "delta-worker-python/src/deltatorrent/benchmark/resilience.py"
        ),
        "safety": tracked_id(commit, "delta-worker-python/src/deltatorrent/benchmark/safety.py"),
    }

    def item(
        metric_id: str,
        implementation: str,
        direction: str,
        unit: str,
        aggregation: str,
        statistics: str,
        threshold: int,
    ) -> dict[str, object]:
        return {
            "aggregation": aggregation,
            "direction": direction,
            "implementation_id": implementations[implementation],
            "mandatory": True,
            "metric_id": metric_id,
            "missing_run_rule": "REQUIRE_ALL",
            "outlier_rule": "NONE",
            "pass_threshold": threshold,
            "repetitions": 3,
            "statistical_method": statistics,
            "unit": unit,
        }

    values = [
        item("protocol_exactness", "safety", "EXACT", "boolean", "ALL", "EXACT", 1),
        item(
            "validation_loss_micro",
            "quality",
            "LOWER",
            "micro-loss",
            "MEAN",
            "NON_INFERIORITY",
            100_000,
        ),
        item(
            "downstream_lambada_accuracy_ppm",
            "quality",
            "HIGHER",
            "ppm",
            "MEAN",
            "NON_INFERIORITY",
            20_000,
        ),
        item(
            "post_training_hellaswag_accuracy_ppm",
            "quality",
            "HIGHER",
            "ppm",
            "MEAN",
            "NON_INFERIORITY",
            20_000,
        ),
        item(
            "per_domain_wikitext_loss_micro",
            "quality",
            "LOWER",
            "micro-loss",
            "MEAN",
            "NON_INFERIORITY",
            100_000,
        ),
        item(
            "network_share_ppm",
            "efficiency",
            "LOWER",
            "ppm",
            "P95",
            "FIXED_SEED_MEAN",
            300_000,
        ),
        item(
            "bytes_per_token",
            "efficiency",
            "LOWER",
            "bytes",
            "P95",
            "FIXED_SEED_MEAN",
            2_000_000,
        ),
        item(
            "gpu_utilization_ppm",
            "efficiency",
            "HIGHER",
            "ppm",
            "MEDIAN",
            "FIXED_SEED_MEAN",
            400_000,
        ),
        item("resilience_exact", "resilience", "EXACT", "boolean", "ALL", "EXACT", 1),
    ]
    return profile("PRIMARY_METRICS", metrics=values)


def sbom(commit: str, dependencies: dict[str, object]) -> dict[str, object]:
    paths = (
        "CMakePresets.json",
        "delta-core-cpp/toolchain/build-tools.lock.json",
        "delta-core-cpp/toolchain/compilers.lock.json",
        "delta-ffi/toolchain/jextract.lock.json",
        "delta-node-java/distribution-dependencies.lock.json",
        "delta-node-java/toolchains.toml",
        "delta-worker-python/pyproject.toml",
        "uv.lock",
    )
    return profile(
        "PRIMARY_SBOM",
        external_dependency_manifest_id=object_id(dependencies),
        files=[{"path": path, "sha256": tracked_id(commit, path)[7:]} for path in paths],
        source_commit=commit,
    )


def definition_document(commit: str, documents: dict[str, dict[str, object]]) -> dict[str, object]:
    workload_document = documents["workload-v1.json"]
    arms_document = documents["arms-v1.json"]
    networks_document = documents["networks-v1.json"]
    faults_document = documents["faults-v1.json"]
    metric_document = documents["metrics-v1.json"]
    dependencies = documents["dependencies-v1.json"]
    runtime = documents["runtime-v1.json"]
    return {
        "B": workload_document["B"],
        "H": workload_document["H"],
        "abi_descriptor_id": tracked_id(commit, "delta-protocol/schemas/003/delta-abi-v1.json"),
        "apply_profile_id": tracked_id(commit, "delta-protocol/schemas/008/apply-qc-v1.json"),
        "arm_ids": [object_id(item) for item in arms_document["arms"]],
        "base_model_id": (
            "sha256:aefa0b68c6182ee526df1a3178bbcd6ccbaff2455b72f829846d30e035895a4c"
        ),
        "compatibility_policy_id": object_id(runtime),
        "compiler_profile_id": tracked_id(commit, "delta-core-cpp/toolchain/compilers.lock.json"),
        "dataset_manifest_id": object_id(dependencies),
        "decision_function": "ALL_MANDATORY",
        "dependency_lock_ids": [
            tracked_id(commit, path)
            for path in (
                "delta-core-cpp/toolchain/build-tools.lock.json",
                "delta-core-cpp/toolchain/compilers.lock.json",
                "delta-node-java/distribution-dependencies.lock.json",
                "uv.lock",
            )
        ],
        "deployment_policy_id": object_id(runtime),
        "domain_manifest_id": object_id(workload_document),
        "evaluation_ids": [
            object_id(item)
            for item in dependencies["artifacts"]
            if str(item["role"]).startswith(("VALIDATION", "DOWNSTREAM", "POST_TRAINING"))
        ],
        "exclusions": ["NO_POST_HOC_RUN_OR_METRIC_EXCLUSIONS"],
        "fault_profile_ids": [object_id(faults_document["trace_profile"])],
        "fixedpoint_profile_id": tracked_id(
            commit, "delta-core-cpp/toolchain/fixedpoint-targets.lock.json"
        ),
        "formal_report_id": FORMAL_REPORT_ID,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "formal_trace_schema_id": tracked_id(commit, "formal/schemas/formal-trace.schema.json"),
        "image_id": tracked_id(commit, "configs/qlora/8gb-reference.json"),
        "isolation_policy": "COMPARE_BOTH",
        "jdk_profile_id": tracked_id(commit, "delta-node-java/toolchains.toml"),
        "license_policy_id": object_id(documents["licenses-v1.json"]),
        "metric_definitions": metric_document["metrics"],
        "missing_run_policy": "FAIL_CLOSED",
        "model_mode": "QLORA_ADAPTER",
        "native_build_id": tracked_id(
            commit, "specs/010-wan-benchmark-and-quality/evidence/runtime-adapters.json"
        ),
        "netty_profile_id": tracked_id(
            commit, "delta-node-java/distribution-dependencies.lock.json"
        ),
        "network_profile_ids": [
            *[object_id(item) for item in networks_document["profiles"]],
            object_id(networks_document["real_wan_variant"]),
        ],
        "optimizer_profile_id": object_id(workload_document["optimizer"]),
        "physical_profile_id": tracked_id(commit, "configs/qlora/8gb-reference.json"),
        "pi_d": workload_document["domain_mixture"],
        "primary": True,
        "protocol_registry_id": tracked_id(commit, "delta-protocol/registry.json"),
        "python_profile_id": tracked_id(commit, "uv.lock"),
        "qlora_profile_id": tracked_id(commit, "configs/qlora/8gb-reference.json"),
        "refinement_evidence_ids": list(FEATURE_REPORT_IDS),
        "repetitions": workload_document["repetitions"],
        "robust_profile_id": tracked_id(commit, "delta-protocol/schemas/008/norm-evidence-v1.json"),
        "sbom_id": object_id(documents["sbom-v1.json"]),
        "schema_version": "1.0.0",
        "seeds": workload_document["seeds"],
        "source_commit": commit,
        "source_tree": git("show", "-s", "--format=%T", commit),
        "theorem_build_id": tracked_id(commit, "formal/reports/lean-proof-report.json"),
        "ticket_plan_id": object_id(workload_document),
        "tokenizer_id": ("sha256:9e556afd44213b6bd1be2b850ebbbd98f5481437a8021afaf58ee7fb1818d347"),
        "type_name": "BENCHMARK_DEFINITION",
    }


def attestation(definition: BenchmarkDefinition) -> dict[str, object]:
    validators = tuple(f"benchmark-validator-{index}" for index in range(4))
    validator_set_id = object_id({"members": list(validators), "purpose": "DEFINITION"})
    votes = tuple(
        GovernanceVote(signer, validator_set_id, definition.content_id, "DEFINITION")
        for signer in validators[:3]
    )
    value = GovernanceAttestation.finalize(
        body_id=definition.content_id,
        validator_set_id=validator_set_id,
        purpose="DEFINITION",
        validator_ids=validators,
        f_b=1,
        votes=votes,
    )
    return value.to_dict()


def expected_outputs(commit: str) -> dict[Path, bytes]:
    dependencies = external_dependencies()
    workload_document = workload()
    documents = {
        "dependencies-v1.json": dependencies,
        "workload-v1.json": workload_document,
        "arms-v1.json": arms(object_id(workload_document)),
        "networks-v1.json": networks(),
        "faults-v1.json": faults(),
        "runtime-v1.json": runtime_policy(commit),
        "evidence-policy-v1.json": evidence_policy(),
        "licenses-v1.json": licenses(),
        "metrics-v1.json": metrics(commit),
    }
    documents["sbom-v1.json"] = sbom(commit, dependencies)
    definition_value = definition_document(commit, documents)
    definition = BenchmarkDefinition.from_dict(definition_value)
    documents["primary.yaml"] = definition_value
    documents["primary-definition-attestation.json"] = attestation(definition)
    return {OUTPUT_ROOT / name: canonical_json_bytes(value) for name, value in documents.items()}


def source_commit_from_output() -> str:
    value = json.loads((OUTPUT_ROOT / "primary.yaml").read_text(encoding="utf-8"))
    commit = value.get("source_commit") if isinstance(value, dict) else None
    require(isinstance(commit, str) and len(commit) == 40, "PRIMARY_SOURCE_COMMIT_INVALID")
    return commit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if arguments.write:
        require(not git("status", "--porcelain"), "SOURCE_TREE_NOT_CLEAN")
        commit = git("rev-parse", "HEAD")
    else:
        commit = source_commit_from_output()
    outputs = expected_outputs(commit)
    if arguments.write:
        for path, value in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
    else:
        for path, expected in outputs.items():
            require(
                path.is_file() and path.read_bytes() == expected,
                f"PRIMARY_OUTPUT_DRIFT:{path.name}",
            )
    definition = BenchmarkDefinition.from_dict(json.loads(outputs[OUTPUT_ROOT / "primary.yaml"]))
    print(
        json.dumps(
            {
                "definition_id": definition.content_id,
                "output_count": len(outputs),
                "primary": definition.primary,
                "source_commit": commit,
                "status": "PASS",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
