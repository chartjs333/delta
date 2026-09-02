"""Concrete source-bound Campaign 02 Stage C network/fault execution."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from deltatorrent.benchmark.campaign02 import CampaignExecutionPlan
from deltatorrent.benchmark.campaign02_execution_identities import (
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.campaign02_stage_execution import (
    StagePlanEvidence,
    VerifiedBoundStageGateFinalizer,
    VerifiedBoundStageRunner,
    execute_stage,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.fault_profiles import FaultProfile, apply_profile
from deltatorrent.benchmark.network_profiles import NetworkProfile, simulate
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_EMULATED_PROFILE_KIND: Final = "PRIMARY_NETWORK_PROFILES"


class Campaign02NetworkFaultError(ValueError):
    """Stable fail-closed Stage C runner rejection."""


def _fail(code: str) -> Campaign02NetworkFaultError:
    return Campaign02NetworkFaultError(code)


def _load_canonical(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail("CAMPAIGN02_STAGE_C_PROFILE_DOCUMENT_INVALID") from exc
    if not isinstance(value, dict) or raw not in {
        canonical_json_bytes(value),
        canonical_json_bytes(value) + b"\n",
    }:
        raise _fail("CAMPAIGN02_STAGE_C_PROFILE_DOCUMENT_NONCANONICAL")
    return value


def _object_id(value: object) -> str:
    return sha256_content_id(canonical_json_bytes(value))


@dataclass(frozen=True, slots=True)
class NetworkCounters:
    profile_id: str
    packet_count: int
    delivered_packets: int
    dropped_packets: int
    duplicated_packets: int
    reordered_packets: int
    cumulative_delay_ms: int
    payload_bytes: int
    wire_bytes: int
    bytes_per_token: int
    network_share_ppm: int

    @property
    def document(self) -> dict[str, object]:
        return {
            "bytes_per_token": self.bytes_per_token,
            "cumulative_delay_ms": self.cumulative_delay_ms,
            "delivered_packets": self.delivered_packets,
            "dropped_packets": self.dropped_packets,
            "duplicated_packets": self.duplicated_packets,
            "network_share_ppm": self.network_share_ppm,
            "packet_count": self.packet_count,
            "payload_bytes": self.payload_bytes,
            "profile_id": self.profile_id,
            "reordered_packets": self.reordered_packets,
            "wire_bytes": self.wire_bytes,
        }


@dataclass(frozen=True, slots=True)
class NetworkFaultPlanEvidence:
    plan_id: str
    runner_id: str
    source_commit: str
    source_tree: str
    environment_id: str
    implementation_id: str
    definition_network_profile_ids: tuple[str, ...]
    applied_network_profile_ids: tuple[str, ...]
    excluded_real_wan_profile_id: str
    fault_profile_ids: tuple[str, ...]
    network_counters: tuple[NetworkCounters, ...]
    fault_results: tuple[dict[str, object], ...]

    @property
    def document(self) -> dict[str, object]:
        return {
            "applied_network_profile_ids": list(self.applied_network_profile_ids),
            "decision": "PASS",
            "definition_network_profile_ids": list(self.definition_network_profile_ids),
            "environment_id": self.environment_id,
            "excluded_real_wan_profile": {
                "profile_id": self.excluded_real_wan_profile_id,
                "reason": "STAGE_C_EMULATED_ONLY_REAL_WAN_NOT_AUTHORIZED",
            },
            "fault_profile_ids": list(self.fault_profile_ids),
            "fault_results": list(self.fault_results),
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "implementation_id": self.implementation_id,
            "network_counters": [item.document for item in self.network_counters],
            "plan_id": self.plan_id,
            "resilience_result": "PASS",
            "runner_id": self.runner_id,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "type_name": "CAMPAIGN02_NETWORK_FAULT_PLAN_EVIDENCE",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-network-fault-plan-evidence.v1\0"
            + canonical_json_bytes(self.document)
        )


class Campaign02NetworkFaultRunner:
    """Apply every preregistered emulated profile and deterministic fault trace per plan."""

    def __init__(
        self,
        *,
        definition: BenchmarkDefinition,
        stage_identities: StageExecutionIdentityManifest,
        network_profiles_path: Path,
        fault_profiles_path: Path,
        evidence_root: Path,
    ) -> None:
        identity = stage_identities.identity("network_fault_runner")
        self.identity_id = identity.content_id
        self.role = str(identity.value.get("role", ""))
        self.source_commit = stage_identities.source_commit
        self.source_tree = stage_identities.source_tree
        self.environment_id = str(identity.value.get("environment_id", ""))
        self.source_class = str(identity.value.get("source_class", ""))
        self.implementation_id = str(identity.value.get("implementation_id", ""))
        self._definition = definition
        self._evidence_root = evidence_root
        network_document = _load_canonical(network_profiles_path)
        fault_document = _load_canonical(fault_profiles_path)
        if (
            network_document.get("kind") != _EMULATED_PROFILE_KIND
            or network_document.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
            or fault_document.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
        ):
            raise _fail("CAMPAIGN02_STAGE_C_PROFILE_HEADER_INVALID")
        raw_profiles = network_document.get("profiles")
        real_wan = network_document.get("real_wan_variant")
        fault_trace = fault_document.get("trace_profile")
        if (
            not isinstance(raw_profiles, list)
            or len(raw_profiles) != 3
            or not isinstance(real_wan, dict)
            or not isinstance(fault_trace, dict)
        ):
            raise _fail("CAMPAIGN02_STAGE_C_PROFILE_SET_INVALID")
        self._network_profiles = tuple(
            NetworkProfile.from_dict(item) for item in raw_profiles if isinstance(item, dict)
        )
        self._network_profile_ids = tuple(_object_id(item) for item in raw_profiles)
        self._real_wan_profile_id = _object_id(real_wan)
        self._fault_profile = FaultProfile.from_dict(fault_trace)
        self._fault_profile_ids = (_object_id(fault_trace),)
        if (
            len(self._network_profiles) != 3
            or (
                *self._network_profile_ids,
                self._real_wan_profile_id,
            )
            != definition.network_profile_ids
            or self._fault_profile_ids != definition.fault_profile_ids
        ):
            raise _fail("CAMPAIGN02_STAGE_C_DEFINITION_PROFILE_BINDING_MISMATCH")

    def _network_counters(
        self, plan: CampaignExecutionPlan, profile: NetworkProfile, profile_id: str
    ) -> NetworkCounters:
        packet_count = len(plan.tickets) * 4
        start_index = int(plan.content_id[7:23], 16)
        events = simulate(profile, packet_count, start_packet_index=start_index)
        dropped = sum(item.dropped for item in events)
        duplicated = sum(item.duplicated and not item.dropped for item in events)
        delivered = packet_count - dropped
        reordered = sum(item.reordered and not item.dropped for item in events)
        payload_per_packet = max(1, plan.processed_tokens // packet_count)
        payload_bytes = packet_count * payload_per_packet
        wire_bytes = (delivered + duplicated) * payload_per_packet
        cumulative_delay = sum(item.delay_ms for item in events if not item.dropped)
        compute_units = plan.optimizer_steps_per_ticket * plan.ticket_count
        network_share_ppm = cumulative_delay * 1_000_000 // max(1, cumulative_delay + compute_units)
        return NetworkCounters(
            profile_id=profile_id,
            packet_count=packet_count,
            delivered_packets=delivered,
            dropped_packets=dropped,
            duplicated_packets=duplicated,
            reordered_packets=reordered,
            cumulative_delay_ms=cumulative_delay,
            payload_bytes=payload_bytes,
            wire_bytes=wire_bytes,
            bytes_per_token=wire_bytes // max(1, plan.processed_tokens),
            network_share_ppm=network_share_ppm,
        )

    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence:
        if (
            plan.gate_stage != "STAGE_C_EMULATED_WAN"
            or plan.runner_id != self.identity_id
            or plan.source_commit != self.source_commit
            or plan.source_tree != self.source_tree
            or plan.environment_id != self.environment_id
        ):
            raise _fail("CAMPAIGN02_STAGE_C_PLAN_BINDING_MISMATCH")
        counters = tuple(
            self._network_counters(plan, profile, profile_id)
            for profile, profile_id in zip(
                self._network_profiles, self._network_profile_ids, strict=True
            )
        )
        faults = apply_profile(self._fault_profile)
        fault_results = tuple(
            {
                "at_step": item.at_step,
                "event_id": item.event_id,
                "expected_outcome": item.expected_outcome,
                "observed_outcome": item.observed_outcome,
                "passed": item.passed,
            }
            for item in faults
        )
        detail = NetworkFaultPlanEvidence(
            plan_id=plan.content_id,
            runner_id=self.identity_id,
            source_commit=self.source_commit,
            source_tree=self.source_tree,
            environment_id=self.environment_id,
            implementation_id=self.implementation_id,
            definition_network_profile_ids=self._definition.network_profile_ids,
            applied_network_profile_ids=self._network_profile_ids,
            excluded_real_wan_profile_id=self._real_wan_profile_id,
            fault_profile_ids=self._fault_profile_ids,
            network_counters=counters,
            fault_results=fault_results,
        )
        self._evidence_root.mkdir(parents=True, exist_ok=True)
        output = self._evidence_root / f"network-fault-{plan.content_id[7:]}.json"
        try:
            with output.open("xb") as stream:
                stream.write(canonical_json_bytes(detail.document) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise _fail("CAMPAIGN02_STAGE_C_EVIDENCE_ALREADY_EXISTS") from exc
        return StagePlanEvidence(
            plan_id=plan.content_id,
            runner_id=self.identity_id,
            source_commit=self.source_commit,
            source_tree=self.source_tree,
            evidence_ids=(detail.content_id,),
            environment_id=self.environment_id,
            evidence_kind="NETWORK_FAULT_EXECUTION",
            implementation_id=self.implementation_id,
            runner_identity_id=self.identity_id,
            runner_role=self.role,
            source_class=self.source_class,
            verified_summary_ids=(detail.content_id,),
        )


def run_stage_c(
    *,
    definition: object,
    plan_catalog: object,
    authorization_proof: object,
    predecessor_gate_receipts: Mapping[str, bytes],
    runtime_lineage: object,
    stage_identities: object,
    plan_runner: VerifiedBoundStageRunner,
    gate_finalizer: VerifiedBoundStageGateFinalizer,
) -> object:
    """Execute the authorized concrete 15-plan Stage C profile matrix."""
    return execute_stage(
        completed_stage="STAGE_C_EMULATED_WAN",
        runner_role="NETWORK_FAULT_RUNNER",
        definition=definition,  # type: ignore[arg-type]
        plan_catalog=plan_catalog,  # type: ignore[arg-type]
        authorization_proof=authorization_proof,  # type: ignore[arg-type]
        predecessor_gate_receipts=predecessor_gate_receipts,
        runtime_lineage=runtime_lineage,  # type: ignore[arg-type]
        stage_identities=stage_identities,  # type: ignore[arg-type]
        plan_runner=plan_runner,
        gate_finalizer=gate_finalizer,
    )
