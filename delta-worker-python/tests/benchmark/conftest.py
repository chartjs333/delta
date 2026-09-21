"""Deterministic TEST_FIXTURE factories for the Feature 010 foundation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.contracts import (
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    SCHEMA_VERSION,
    CanonicalContract,
)
from deltatorrent.benchmark.governance import ReviewerSet

SOURCE_COMMIT = "ac0e54ffbab4b9a5c20945b17ede2930b78ff080"
SOURCE_TREE = "4c884424c19bfe05c9c9a570cf6a7e0275369194"
RUN_ID = "foundation-fixture-run"


def cid(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def common(type_name: str, evidence_class: str = "TEST_FIXTURE") -> dict[str, object]:
    return {
        "authority_scope": AUTHORITY_SCOPE,
        "evidence_class": evidence_class,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "gate_eligible": False,
        "primary_eligible": False,
        "schema_version": SCHEMA_VERSION,
        "type_name": type_name,
    }


def reviewer_set(role: str, *, key_offset: int = 0) -> ReviewerSet:
    members: list[dict[str, object]] = []
    role_label = role.lower().replace("_", "-")
    for index in range(1, 5):
        private_key = Ed25519PrivateKey.from_private_bytes(bytes([key_offset + index]) * 32)
        public_bytes = private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        members.append(
            {
                "controller_id": f"{role_label}-controller-{index}",
                "custody_id": f"{role_label}-custody-{index}",
                "key_id": "sha256:" + hashlib.sha256(public_bytes).hexdigest(),
                "public_key_hex": public_bytes.hex(),
                "signer_id": f"{role_label}-signer-{index}",
                "valid_from_epoch_ms": 1000,
                "valid_until_epoch_ms": 10000,
            }
        )
    return ReviewerSet.from_dict(
        {
            "authority_scope": AUTHORITY_SCOPE,
            "evidence_class": "TEST_FIXTURE",
            "f": 1,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "members": members,
            "role": role,
            "schema_version": SCHEMA_VERSION,
            "type_name": "BENCHMARK_REVIEWER_SET",
        }
    )


def runtime_identity(**updates: object) -> CanonicalContract:
    value: dict[str, object] = {
        **common("BENCHMARK_RUNTIME_IDENTITY"),
        "abi_header_id": cid("abi-header"),
        "abi_schema_id": cid("abi-schema"),
        "binary_build_id": cid("fixture-binary-build"),
        "compiler_lock_id": cid("compiler-lock"),
        "cpp_core_id": cid("cpp-core"),
        "cuda_profile_id": cid("cuda-profile-unqualified"),
        "deployment_profile": "EMBEDDED_FFM",
        "fixture_corpus_id": cid("fixture-corpus"),
        "formal_report_id": cid("formal-report"),
        "java_dependency_lock_id": cid("java-dependencies"),
        "java_toolchain_id": cid("jdk-25-toolchain"),
        "native_runtime_id": cid("native-runtime"),
        "netty_profile_id": cid("netty-profile"),
        "protocol_registry_id": cid("protocol-registry"),
        "python_lock_id": cid("python-lock"),
        "python_profile_id": cid("python-3.12-profile"),
        "sbom_id": cid("fixture-sbom"),
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
    }
    value.update(updates)
    return CanonicalContract.from_dict(value)


def scientific_profile(**updates: object) -> CanonicalContract:
    value: dict[str, object] = {
        **common("BENCHMARK_SCIENTIFIC_PROFILE"),
        "dataset_id": cid("dataset"),
        "domain_tokens": {"clinical": 4000, "general": 6000},
        "evaluator_ids": sorted([cid("evaluator-a"), cid("evaluator-b")]),
        "model_id": cid("model"),
        "model_mode": "QLORA_ADAPTER",
        "optimizer_id": cid("optimizer"),
        "repetitions": 2,
        "seeds": [17, 29],
        "ticket_ids": [cid("ticket-1")],
        "ticket_plan_id": cid("ticket-plan"),
        "tokenizer_id": cid("tokenizer"),
        "total_eligible_tokens": 10000,
    }
    value.update(updates)
    return CanonicalContract.from_dict(value)


def arm(
    label: str,
    *,
    kind: str,
    topology: str,
    deployment_profile: str,
    model_mode: str = "QLORA_ADAPTER",
) -> CanonicalContract:
    return CanonicalContract.from_dict(
        {
            **common("BENCHMARK_ARM"),
            "adapter_id": cid(f"adapter-{label}"),
            "arm_kind": kind,
            "deployment_profile": deployment_profile,
            "model_mode": model_mode,
            "topology": topology,
        }
    )


def network_profile(**updates: object) -> CanonicalContract:
    value: dict[str, object] = {
        **common("BENCHMARK_NETWORK_PROFILE"),
        "adapter": "OPTIONAL_TC_NETEM",
        "bandwidth_bytes_per_second": 12500000,
        "disconnect_after_ms": None,
        "duplicate_ppm": 100,
        "duration_ms": 60000,
        "jitter_ms": 5,
        "label": "SIMULATED",
        "loss_ppm": 1000,
        "partition_after_ms": 30000,
        "reorder_ppm": 250,
        "rtt_ms": 80,
        "seed": 101,
    }
    value.update(updates)
    return CanonicalContract.from_dict(value)


def fault_profile(**updates: object) -> CanonicalContract:
    value: dict[str, object] = {
        **common("BENCHMARK_FAULT_PROFILE"),
        "duration_ms": 60000,
        "events": [
            {
                "at_ms": 10000,
                "event_id": "worker-crash",
                "expected_terminal": "CONTINUE",
                "kind": "WORKER_CRASH",
                "target": "worker-01",
            },
            {
                "at_ms": 20000,
                "event_id": "worker-restart",
                "expected_terminal": "RECOVER",
                "kind": "WORKER_RESTART",
                "target": "worker-01",
            },
            {
                "at_ms": 30000,
                "event_id": "region-partition",
                "expected_terminal": "SAFE_ABORT",
                "kind": "REGION_PARTITION",
                "target": "region-b",
            },
        ],
        "label": "SIMULATED",
        "seed": 202,
    }
    value.update(updates)
    return CanonicalContract.from_dict(value)


def environment(runtime: CanonicalContract, **updates: object) -> CanonicalContract:
    value: dict[str, object] = {
        **common("BENCHMARK_ENVIRONMENT_MANIFEST"),
        "binary_ids": sorted(
            [
                cid("fixture-binary-build"),
                cid("java-binary"),
                cid("native-runtime"),
                cid("python-wheel"),
            ]
        ),
        "capture_epoch_ms": 1800000000000,
        "dependency_lock_ids": sorted(
            [cid("compiler-lock"), cid("java-dependencies"), cid("python-lock")]
        ),
        "environment_variable_names": ["CUDA_HOME", "PATH"],
        "hardware_inventory_id": cid("fixture-hardware"),
        "image_id": cid("fixture-image"),
        "runtime_identity_id": runtime.content_id,
        "sbom_id": cid("fixture-sbom"),
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
    }
    value.update(updates)
    return CanonicalContract.from_dict(value)


def definition(
    runtime: CanonicalContract,
    scientific: CanonicalContract,
    arms: tuple[CanonicalContract, ...],
    networks: tuple[CanonicalContract, ...],
    faults: tuple[CanonicalContract, ...],
    **updates: object,
) -> CanonicalContract:
    science = scientific.to_dict()
    dependency_inputs = {
        "dataset": science["dataset_id"],
        "model": science["model_id"],
        "optimizer": science["optimizer_id"],
        "ticket-plan": science["ticket_plan_id"],
        "tokenizer": science["tokenizer_id"],
        **{
            f"evaluator-{index:03d}": identifier
            for index, identifier in enumerate(science["evaluator_ids"])
        },
        **{
            f"ticket-{index:03d}": identifier
            for index, identifier in enumerate(science["ticket_ids"])
        },
    }
    dependencies = []
    for name, dependency_id in sorted(dependency_inputs.items()):
        dependencies.append(
            {
                "access_policy": "PUBLIC_FIXTURE",
                "availability": "VERIFIED_IMMUTABLE",
                "content_id": dependency_id,
                "license_id": cid(f"license-{name}"),
                "locator": "cas://sha256/" + dependency_id.removeprefix("sha256:"),
                "name": name,
            }
        )
    value: dict[str, object] = {
        **common("BENCHMARK_DEFINITION"),
        "B": 64,
        "H": 16,
        "approved_license_ids": sorted(cid(f"license-{name}") for name in dependency_inputs),
        "arm_ids": sorted(item.content_id for item in arms),
        "decision_function": "ALL_MANDATORY",
        "definition_reviewer_set_id": cid("definition-reviewer-set"),
        "dependencies": dependencies,
        "fault_profile_ids": sorted(item.content_id for item in faults),
        "metrics": [
            {
                "aggregation": "MEAN",
                "direction": "LOWER",
                "mandatory": True,
                "metric_id": "validation-loss",
                "missing_rule": "FAIL",
                "threshold": {"denominator": 40, "numerator": 1},
            },
            {
                "aggregation": "ALL",
                "direction": "HIGHER",
                "mandatory": True,
                "metric_id": "wikitext-score",
                "missing_rule": "FAIL",
                "threshold": {"denominator": 20, "numerator": 19},
            },
        ],
        "missing_run_policy": "FAIL_CLOSED",
        "network_profile_ids": sorted(item.content_id for item in networks),
        "policy": {
            "accept_stale": False,
            "adaptive_h": False,
            "consensus_arithmetic": "CHECKED_FIXED_POINT",
            "current_authority": "NATIVE_RUNTIME",
            "threshold_override": False,
        },
        "runtime_identity_id": runtime.content_id,
        "result_evaluator_set_id": cid("result-evaluator-set"),
        "scientific_profile_id": scientific.content_id,
    }
    value.update(updates)
    return CanonicalContract.from_dict(value)


def receipt_document(
    *,
    definition_id: str,
    arm_id: str,
    runtime: CanonicalContract,
    stage: str,
    sequence: int,
    previous_receipt_id: str | None,
    input_ids: list[str],
    output_ids: list[str],
    ticket_id: str,
    run_id: str = RUN_ID,
) -> dict[str, object]:
    runtime_doc = runtime.to_dict()
    component = {
        "WORKER_PYTHON": runtime_doc["python_profile_id"],
        "TRANSPORT_JAVA_NETTY": runtime_doc["netty_profile_id"],
        "NATIVE_CPP_WAL": runtime_doc["native_runtime_id"],
    }[stage]
    native_refs: Mapping[str, object] = {}
    if stage == "NATIVE_CPP_WAL":
        native_refs = {
            "checkpoint_id": cid("checkpoint"),
            "durability_evidence_id": cid("durability-evidence"),
            "effect_id": cid("effect"),
            "state_root_id": cid("state-root"),
            "submit_receipt_id": cid("opaque-native-submit-receipt"),
            "wal_record_id": cid("wal-record"),
        }
    return {
        **common("BENCHMARK_STAGE_RECEIPT"),
        "arm_id": arm_id,
        "benchmark_definition_id": definition_id,
        "component_identity_id": component,
        "input_ids": sorted(input_ids),
        "native_opaque_refs": dict(native_refs),
        "output_ids": sorted(output_ids),
        "previous_receipt_id": previous_receipt_id,
        "run_id": run_id,
        "sequence": sequence,
        "source_commit": SOURCE_COMMIT,
        "stage": stage,
        "ticket_id": ticket_id,
    }


def fixture_receipts(
    definition_id: str,
    arm_id: str,
    runtime: CanonicalContract,
    ticket_id: str,
    run_id: str = RUN_ID,
) -> tuple[CanonicalContract, ...]:
    model_input = cid("model-input")
    normalized = cid("normalized-update")
    envelope = cid("transport-envelope")
    python_receipt = CanonicalContract.from_dict(
        receipt_document(
            definition_id=definition_id,
            arm_id=arm_id,
            runtime=runtime,
            stage="WORKER_PYTHON",
            sequence=1,
            previous_receipt_id=None,
            input_ids=[model_input],
            output_ids=[normalized],
            ticket_id=ticket_id,
            run_id=run_id,
        )
    )
    java_receipt = CanonicalContract.from_dict(
        receipt_document(
            definition_id=definition_id,
            arm_id=arm_id,
            runtime=runtime,
            stage="TRANSPORT_JAVA_NETTY",
            sequence=2,
            previous_receipt_id=python_receipt.content_id,
            input_ids=[normalized],
            output_ids=[envelope],
            ticket_id=ticket_id,
            run_id=run_id,
        )
    )
    native_receipt = CanonicalContract.from_dict(
        receipt_document(
            definition_id=definition_id,
            arm_id=arm_id,
            runtime=runtime,
            stage="NATIVE_CPP_WAL",
            sequence=3,
            previous_receipt_id=java_receipt.content_id,
            input_ids=[envelope],
            output_ids=[cid("checkpoint"), cid("effect")],
            ticket_id=ticket_id,
            run_id=run_id,
        )
    )
    return python_receipt, java_receipt, native_receipt


def completed_run(
    definition_id: str,
    arm_id: str,
    scientific: CanonicalContract,
    network: CanonicalContract,
    fault: CanonicalContract,
    env: CanonicalContract,
    ticket_id: str,
    receipts: tuple[CanonicalContract, ...],
    run_id: str = RUN_ID,
    repetition: int = 1,
    seed: int = 17,
) -> CanonicalContract:
    return CanonicalContract.from_dict(
        {
            **common("BENCHMARK_RUN_MANIFEST"),
            "arm_id": arm_id,
            "benchmark_definition_id": definition_id,
            "environment_manifest_id": env.content_id,
            "execution_authorization_id": None,
            "execution_mode": "CONFORMANCE_FIXTURE",
            "fault_profile_id": fault.content_id,
            "network_profile_id": network.content_id,
            "repetition": repetition,
            "run_id": run_id,
            "scientific_profile_id": scientific.content_id,
            "seed": seed,
            "stage_receipt_ids": [item.content_id for item in receipts],
            "status": "FIXTURE_COMPLETE",
            "ticket_ids": [ticket_id],
        }
    )


def metrics(run_id: str = RUN_ID) -> CanonicalContract:
    return CanonicalContract.from_dict(
        {
            **common("BENCHMARK_METRICS"),
            "byte_counters": {
                "duplicate_bytes": 0,
                "global_bytes": 128,
                "p2p_bytes": 512,
                "regional_bytes": 256,
                "retry_bytes": 0,
                "storage_bytes": 384,
                "validator_bytes": 640,
                "worker_bytes": 1024,
            },
            "gpu_metrics": {
                "device_id": cid("fixture-gpu"),
                "memory_peak_bytes": 1024,
                "sample_count": 2,
                "utilization_basis_points": 5000,
            },
            "phase_timings": [
                {"end_ns": 10, "phase": "compute", "start_ns": 0},
                {"end_ns": 20, "phase": "upload", "start_ns": 10},
                {"end_ns": 30, "phase": "availability", "start_ns": 20},
                {"end_ns": 40, "phase": "certificate", "start_ns": 30},
                {"end_ns": 50, "phase": "reduce", "start_ns": 40},
                {"end_ns": 60, "phase": "apply", "start_ns": 50},
                {"end_ns": 70, "phase": "p2p", "start_ns": 60},
                {"end_ns": 80, "phase": "wait", "start_ns": 70},
            ],
            "resource_metrics": {"cpu_time_ns": 21, "p2p_bytes": 512, "peak_rss_bytes": 2048},
            "run_id": run_id,
        }
    )
