"""Run the exact 15-plan Campaign 02 Stage C catalog twice as non-primary evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from deltatorrent.benchmark.campaign02_network_fault import Campaign02NetworkFaultRunner
from deltatorrent.benchmark.campaign02_stage_c_candidate import (
    CandidateCatalog,
    build_candidate_catalog,
)
from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredStageCRuntimeBoundary,
    RuntimeArtifact,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]


def artifact(path: Path) -> RuntimeArtifact:
    return RuntimeArtifact(path.resolve(), sha256_content_id(path.read_bytes()))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--java-executable", type=Path, required=True)
    result.add_argument("--native-executable", type=Path, required=True)
    result.add_argument("--transport-harness", type=Path, required=True)
    result.add_argument("--netty-artifact", type=Path, action="append", required=True)
    result.add_argument("--os-counter-root", type=Path, required=True)
    result.add_argument("--output-root", type=Path, required=True)
    result.add_argument("--image-id", required=True)
    result.add_argument("--source-commit", required=True)
    result.add_argument("--source-tree", required=True)
    return result


def _semantic_projection(document: dict[str, object]) -> dict[str, object]:
    counters = document.get("network_counters")
    faults = document.get("fault_results")
    if not isinstance(counters, list) or not isinstance(faults, list):
        raise SystemExit("candidate evidence lacks typed counter or fault rows")
    stable_counters = []
    for counter in counters:
        if not isinstance(counter, dict):
            raise SystemExit("candidate counter row is malformed")
        stable_counters.append(
            {
                key: counter[key]
                for key in (
                    "attempted_packets",
                    "attempted_payload_bytes",
                    "disconnect_count",
                    "dropped_packets",
                    "dropped_payload_bytes",
                    "duplicate_packets",
                    "duplicate_payload_bytes",
                    "java_rx_payload_bytes",
                    "java_tx_payload_bytes",
                    "network_profile_id",
                    "reordered_packets",
                    "unique_delivered_packets",
                    "unique_delivered_payload_bytes",
                )
            }
            | {
                "disconnect_duration_observed": int(counter["disconnect_duration_ms"]) > 0,
            }
        )
    stable_faults = []
    for fault in faults:
        if not isinstance(fault, dict):
            raise SystemExit("candidate fault row is malformed")
        stable_faults.append(
            {
                key: fault[key]
                for key in (
                    "action",
                    "actor_class",
                    "at_step",
                    "availability_success",
                    "current_checkpoint_advanced",
                    "event_id",
                    "expected_outcome",
                    "native_effect_root",
                    "native_state_root",
                    "native_trace_id",
                    "native_wal_sha256",
                    "observation_source",
                    "observed_outcome",
                    "passed",
                    "runtime_operation_count",
                    "view_change_observed",
                    "wal_replayed",
                )
            }
        )
    return {
        "applied_network_profile_ids": document["applied_network_profile_ids"],
        "fault_profile_ids": document["fault_profile_ids"],
        "fault_results": stable_faults,
        "native_fault_trace_id": document["native_fault_trace_id"],
        "network_counters": stable_counters,
        "plan_id": document["plan_id"],
    }


def _causal_projection(document: dict[str, object]) -> dict[str, object]:
    faults = document.get("fault_results")
    if not isinstance(faults, list):
        raise SystemExit("candidate evidence lacks typed causal fault rows")
    fields = (
        "abort_qc_id",
        "aggregate_root_qc_id",
        "aggregate_root_qc_tick",
        "apply_qc_id",
        "apply_qc_tick",
        "apply_quorum_threshold",
        "apply_validator_set_id",
        "apply_work_item_id",
        "causal_transport_receipt_id",
        "certified_abort_tick",
        "current_checkpoint_advanced",
        "current_pointer_after",
        "current_pointer_before",
        "dropped_message_ids",
        "event_id",
        "failed_quorum_reason",
        "gst_tick",
        "hard_deadline_tick",
        "isc_ticket_set",
        "loss_fraction",
        "lost_ticket_ids",
        "lost_worker_ids",
        "message_delivery_ticks",
        "missing_work_policy_result",
        "network_profile_id",
        "next_checkpoint_id",
        "next_optimizer_state_id",
        "parent_checkpoint_id",
        "parent_optimizer_state_id",
        "partition_start_tick",
        "per_domain_remaining_tickets",
        "per_domain_required_tickets",
        "pi_d_renormalized",
        "quorum_capacity_after",
        "quorum_capacity_before",
        "quorum_formation_tick",
        "unavailable_ids",
        "worker_count_before",
        "worker_count_lost",
    )
    projection = []
    for fault in faults:
        if not isinstance(fault, dict) or any(field not in fault for field in fields):
            raise SystemExit("candidate causal fault row is malformed")
        projection.append({field: fault[field] for field in fields})
    return {
        "fault_profile_ids": document["fault_profile_ids"],
        "fault_results": projection,
        "plan_id": document["plan_id"],
    }


def _root(domain: bytes, values: object) -> str:
    return sha256_content_id(domain + canonical_json_bytes(values))


def _execute_once(
    candidate: CandidateCatalog,
    boundary: MeasuredStageCRuntimeBoundary,
    run_root: Path,
    ordinal: int,
) -> tuple[dict[str, object], str]:
    run_root.mkdir(parents=True, exist_ok=False)
    evidence_root = run_root / "raw-evidence"
    runner = Campaign02NetworkFaultRunner(
        definition=candidate.definition,
        stage_identities=candidate.stage_identities,
        network_profiles_path=ROOT / "configs/benchmark/networks-v1.json",
        fault_profiles_path=ROOT / "configs/benchmark/faults-v1.json",
        evidence_root=evidence_root,
        runtime_boundary=replace(boundary, working_root=run_root / "runtime"),
    )
    stage_c_plans = tuple(
        plan for plan in candidate.catalog.plans if plan.gate_stage == "STAGE_C_EMULATED_WAN"
    )
    plan_records: list[dict[str, object]] = []
    semantic_records: list[dict[str, object]] = []
    causal_records: list[dict[str, object]] = []
    raw_file_ids: list[str] = []
    for plan in stage_c_plans:
        evidence = runner.execute(plan)
        evidence_path = evidence_root / f"network-fault-{plan.content_id[7:]}.json"
        raw = evidence_path.read_bytes()
        document = json.loads(raw)
        if not isinstance(document, dict) or document.get("plan_id") != plan.content_id:
            raise SystemExit("candidate evidence is not bound to the exact catalog plan")
        raw_file_id = sha256_content_id(raw)
        semantic = _semantic_projection(document)
        causal = _causal_projection(document)
        raw_file_ids.append(raw_file_id)
        semantic_records.append(semantic)
        causal_records.append(causal)
        plan_records.append(
            {
                "applied_network_profile_ids": document["applied_network_profile_ids"],
                "causal_projection_id": _root(
                    b"deltareduce.010.campaign02-stage-c-causal-projection.v1\0",
                    causal,
                ),
                "fault_profile_ids": document["fault_profile_ids"],
                "plan_id": plan.content_id,
                "raw_evidence_file_id": raw_file_id,
                "raw_evidence_path": evidence_path.relative_to(run_root).as_posix(),
                "raw_java_receipt_id": document["raw_java_receipt_id"],
                "semantic_projection_id": _root(
                    b"deltareduce.010.campaign02-stage-c-semantic-projection.v1\0",
                    semantic,
                ),
                "typed_evidence_id": evidence.evidence_ids[0],
            }
        )
    if len(plan_records) != 15 or len({item["plan_id"] for item in plan_records}) != 15:
        raise SystemExit("candidate did not execute the exact 15-plan Stage C set")
    package: dict[str, object] = {
        "authoritative_definition_vote_count": 0,
        "authoritative_definition_attestation_present": False,
        "benchmark_result_qc_emitted": False,
        "candidate_compiler_attestation_class": "TEST_ONLY_DETERMINISTIC_EPHEMERAL",
        "candidate_compiler_signature_ids": list(candidate.compiler_signature_ids),
        "candidate_definition_id": candidate.definition.content_id,
        "candidate_run_ordinal": ordinal,
        "causal_root": _root(b"deltareduce.010.campaign02-stage-c-causal-set.v1\0", causal_records),
        "decision": "PASS",
        "execution_authorized": False,
        "formal_semantics_id": candidate.definition.raw["formal_semantics_id"],
        "observation_count": 0,
        "plan_catalog_id": candidate.catalog.content_id,
        "plan_count": len(plan_records),
        "plan_records": plan_records,
        "qualified_runtime_lineage_id": candidate.runtime_lineage.content_id,
        "raw_evidence_root": _root(
            b"deltareduce.010.campaign02-stage-c-raw-evidence-set.v1\0", raw_file_ids
        ),
        "schema_version": "2.0.0",
        "semantic_root": _root(
            b"deltareduce.010.campaign02-stage-c-semantic-set.v1\0", semantic_records
        ),
        "source_commit": candidate.runtime_lineage.source_commit,
        "source_tree": candidate.runtime_lineage.source_tree,
        "stage_execution_identities_id": candidate.stage_identities.content_id,
        "stage_gate_receipt_emitted": False,
        "type_name": "CAMPAIGN02_STAGE_C_NON_PRIMARY_CANDIDATE_RUN",
    }
    package_path = run_root / "candidate-run.json"
    package_bytes = canonical_json_bytes(package) + b"\n"
    package_path.write_bytes(package_bytes)
    return package, sha256_content_id(package_bytes)


def main() -> None:
    arguments = parser().parse_args()
    boundary = MeasuredStageCRuntimeBoundary(
        image_id=arguments.image_id,
        java_executable=artifact(arguments.java_executable),
        native_executable=artifact(arguments.native_executable),
        transport_harness=artifact(arguments.transport_harness),
        netty_artifacts=tuple(artifact(path) for path in arguments.netty_artifact),
        os_interface_counter_root=arguments.os_counter_root.resolve(),
        working_root=arguments.output_root / "unused",
    )
    candidate = build_candidate_catalog(
        source_root=ROOT,
        source_commit=arguments.source_commit,
        source_tree=arguments.source_tree,
        boundary=boundary,
    )
    arguments.output_root.mkdir(parents=True, exist_ok=False)
    first, first_id = _execute_once(candidate, boundary, arguments.output_root / "run-1", 1)
    second, second_id = _execute_once(candidate, boundary, arguments.output_root / "run-2", 2)
    first_records = first["plan_records"]
    second_records = second["plan_records"]
    if (
        first["semantic_root"] != second["semantic_root"]
        or first["causal_root"] != second["causal_root"]
        or not isinstance(first_records, list)
        or not isinstance(second_records, list)
        or [item["plan_id"] for item in first_records]
        != [item["plan_id"] for item in second_records]
        or [item["semantic_projection_id"] for item in first_records]
        != [item["semantic_projection_id"] for item in second_records]
        or [item["causal_projection_id"] for item in first_records]
        != [item["causal_projection_id"] for item in second_records]
    ):
        raise SystemExit("second candidate run changed Stage C semantic evidence")
    summary = {
        "authoritative_catalog_constructed": False,
        "authoritative_definition_attestation_present": False,
        "authoritative_definition_vote_count": 0,
        "benchmark_result_qc_emitted": False,
        "candidate_definition_id": candidate.definition.content_id,
        "candidate_plan_catalog_id": candidate.catalog.content_id,
        "candidate_run_package_ids": [first_id, second_id],
        "causal_root": first["causal_root"],
        "decision": "PASS",
        "execution_authorized": False,
        "formal_semantics_id": candidate.definition.raw["formal_semantics_id"],
        "observation_count": 0,
        "plan_count": 15,
        "plan_ids": [item["plan_id"] for item in first_records],
        "raw_evidence_roots": [first["raw_evidence_root"], second["raw_evidence_root"]],
        "repeat_semantic_match": True,
        "repeat_causal_match": True,
        "schema_version": "2.0.0",
        "semantic_root": first["semantic_root"],
        "source_commit": arguments.source_commit,
        "source_tree": arguments.source_tree,
        "stage_gate_receipt_emitted": False,
        "type_name": "CAMPAIGN02_STAGE_C_NON_PRIMARY_CANDIDATE_SUMMARY",
    }
    summary_bytes = canonical_json_bytes(summary) + b"\n"
    (arguments.output_root / "campaign02-stage-c-candidate-summary.json").write_bytes(summary_bytes)
    print(summary_bytes.decode("utf-8"), end="")


if __name__ == "__main__":
    main()
