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
from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredNetworkCounters,
    MeasuredStageCRuntimeBoundary,
    NativeFaultTransition,
)
from deltatorrent.benchmark.campaign02_stage_execution import (
    StagePlanEvidence,
    VerifiedBoundStageGateFinalizer,
    VerifiedBoundStageRunner,
    execute_stage,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.fault_profiles import FaultProfile
from deltatorrent.benchmark.network_profiles import NetworkProfile
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
    network_counters: tuple[MeasuredNetworkCounters, ...]
    fault_results: tuple[NativeFaultTransition, ...]
    native_fault_trace_id: str
    image_id: str
    java_executable_id: str
    native_executable_id: str
    transport_harness_id: str
    netty_artifact_ids: tuple[str, ...]

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
            "fault_results": [item.document for item in self.fault_results],
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "image_id": self.image_id,
            "implementation_id": self.implementation_id,
            "java_executable_id": self.java_executable_id,
            "measurement_source": "PYTHON_JAVA_NETTY_CPP_OS",
            "native_effect_root": self.fault_results[-1].native_effect_root,
            "native_executable_id": self.native_executable_id,
            "native_fault_trace_id": self.native_fault_trace_id,
            "native_state_root": self.fault_results[-1].native_state_root,
            "native_wal_sha256": self.fault_results[-1].native_wal_sha256,
            "netty_artifact_ids": list(self.netty_artifact_ids),
            "network_counters": [item.document for item in self.network_counters],
            "plan_id": self.plan_id,
            "resilience_result": "PASS",
            "runner_id": self.runner_id,
            "schema_version": "2.0.0",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "transport_harness_id": self.transport_harness_id,
            "type_name": "CAMPAIGN02_NETWORK_FAULT_PLAN_EVIDENCE",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-network-fault-plan-evidence.v2\0"
            + canonical_json_bytes(self.document)
        )


class Campaign02NetworkFaultRunner:
    """Measure each preregistered profile through the bound Java/native/OS runtime path."""

    def __init__(
        self,
        *,
        definition: BenchmarkDefinition,
        stage_identities: StageExecutionIdentityManifest,
        network_profiles_path: Path,
        fault_profiles_path: Path,
        evidence_root: Path,
        runtime_boundary: MeasuredStageCRuntimeBoundary,
    ) -> None:
        identity = stage_identities.identity("network_fault_runner")
        self.identity_id = identity.content_id
        self.role = str(identity.value.get("role", ""))
        self.source_commit = stage_identities.source_commit
        self.source_tree = stage_identities.source_tree
        self.environment_id = str(identity.value.get("environment_id", ""))
        self.source_class = str(identity.value.get("source_class", ""))
        self.implementation_id = str(identity.value.get("implementation_id", ""))
        self.image_id = str(identity.value.get("image_id", ""))
        self.java_executable_id = str(identity.value.get("java_executable_id", ""))
        self.native_executable_id = str(identity.value.get("native_executable_id", ""))
        self.transport_harness_id = str(identity.value.get("transport_harness_id", ""))
        raw_netty_ids = identity.value.get("netty_artifact_ids")
        self.netty_artifact_ids = (
            tuple(str(item) for item in raw_netty_ids) if isinstance(raw_netty_ids, list) else ()
        )
        self._definition = definition
        self._evidence_root = evidence_root
        self._runtime_boundary = runtime_boundary
        if (
            stage_identities.schema_version != "4.0.0"
            or self.role != "NETWORK_FAULT_RUNNER"
            or self.source_class != "MEASURED_RUNTIME"
            or self.image_id != runtime_boundary.image_id
            or self.java_executable_id != runtime_boundary.java_executable_id
            or self.native_executable_id != runtime_boundary.native_executable_id
            or self.transport_harness_id != runtime_boundary.transport_harness_id
            or self.netty_artifact_ids != runtime_boundary.netty_artifact_ids
        ):
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_IDENTITY_MISMATCH")
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

    def execute(self, plan: CampaignExecutionPlan) -> StagePlanEvidence:
        if (
            plan.gate_stage != "STAGE_C_EMULATED_WAN"
            or plan.runner_id != self.identity_id
            or plan.source_commit != self.source_commit
            or plan.source_tree != self.source_tree
            or plan.environment_id != self.environment_id
            or plan.image_id != self.image_id
            or plan.java_executable_id != self.java_executable_id
            or plan.native_executable_id != self.native_executable_id
            or plan.transport_harness_id != self.transport_harness_id
            or plan.netty_artifact_ids != self.netty_artifact_ids
        ):
            raise _fail("CAMPAIGN02_STAGE_C_PLAN_BINDING_MISMATCH")
        packet_count = len(plan.tickets) * 4
        measurement = self._runtime_boundary.execute(
            plan_id=plan.content_id,
            packet_count=packet_count,
            payload_bytes=min(4096, max(64, plan.processed_tokens // packet_count)),
            network_profiles=tuple(
                zip(self._network_profile_ids, self._network_profiles, strict=True)
            ),
            fault_profile=self._fault_profile,
        )
        if measurement.plan_id != plan.content_id:
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_PLAN_MISMATCH")
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
            network_counters=measurement.network_counters,
            fault_results=measurement.fault_transitions,
            native_fault_trace_id=measurement.native_fault_trace_id,
            image_id=self.image_id,
            java_executable_id=self.java_executable_id,
            native_executable_id=self.native_executable_id,
            transport_harness_id=self.transport_harness_id,
            netty_artifact_ids=self.netty_artifact_ids,
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
