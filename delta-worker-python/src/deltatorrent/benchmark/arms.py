"""Benchmark arm contracts and deterministic non-primary synthetic runner."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Final

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.protocol.canonical import canonical_json_bytes

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")


class ArmError(ValueError):
    """Stable benchmark-arm or synthetic-run rejection."""


@dataclass(frozen=True, slots=True)
class ArmSpec:
    content_id: str
    arm_id: str
    kind: str
    deployment_profile: str
    mandatory: bool
    workload_identity: str
    runtime_profile_id: str
    topology: str

    @classmethod
    def from_wrapper(cls, wrapper: dict[str, Any]) -> ArmSpec:
        value = wrapper.get("value")
        content_id = wrapper.get("content_id")
        if not isinstance(value, dict) or not isinstance(content_id, str):
            raise ArmError("ARM_WRAPPER_INVALID")
        if _CONTENT_ID.fullmatch(content_id) is None or value.get("type_name") != "BENCHMARK_ARM":
            raise ArmError("ARM_IDENTITY_INVALID")
        fields = {
            "arm_id",
            "deployment_profile",
            "kind",
            "mandatory",
            "runtime_profile_id",
            "workload_identity",
        }
        if any(field not in value for field in fields):
            raise ArmError("ARM_FIELDS_INVALID")
        if not isinstance(value["mandatory"], bool):
            raise ArmError("ARM_MANDATORY_INVALID")
        return cls(
            content_id=content_id,
            arm_id=str(value["arm_id"]),
            kind=str(value["kind"]),
            deployment_profile=str(value["deployment_profile"]),
            mandatory=value["mandatory"],
            workload_identity=str(value["workload_identity"]),
            runtime_profile_id=str(value["runtime_profile_id"]),
            topology=str(
                value.get(
                    "topology",
                    "SINGLE_NODE_REFERENCE"
                    if value["deployment_profile"] == "PYTHON"
                    else "FLAT_BFT",
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class MetricSample:
    metric_id: str
    value: int
    unit: str


@dataclass(frozen=True, slots=True)
class RunObservation:
    definition_id: str
    arm: ArmSpec
    environment_manifest_id: str
    network_profile_id: str
    fault_profile_id: str
    seed: int
    repetition: int
    processed_tokens: int
    domain_ticket_counts: tuple[tuple[str, int], ...]
    terminal_outcome: str
    protocol_hash: str
    checkpoint_id: str
    ticket_plan_id: str
    parent_checkpoint_id: str
    certificate_ids: tuple[str, ...]
    model_artifact_id: str
    evaluation_artifact_ids: tuple[str, ...]
    samples: tuple[MetricSample, ...]
    phase_latencies_us: tuple[tuple[str, int], ...]
    bytes_sent: int
    useful_compute_us: int
    total_us: int
    zero_copy_eligible: int
    zero_copy_hits: int
    copy_fallback_bytes: int
    gpu_utilization_ppm: int
    gpu_peak_reserved_bytes: int
    host_offload_bytes: int

    def __post_init__(self) -> None:
        identities = (
            self.definition_id,
            self.environment_manifest_id,
            self.network_profile_id,
            self.fault_profile_id,
            self.protocol_hash,
            self.checkpoint_id,
            self.ticket_plan_id,
            self.parent_checkpoint_id,
            self.model_artifact_id,
            *self.certificate_ids,
            *self.evaluation_artifact_ids,
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in identities):
            raise ArmError("RUN_ARTIFACT_IDENTITY_INVALID")
        if len(set(self.certificate_ids)) != len(self.certificate_ids) or len(
            set(self.evaluation_artifact_ids)
        ) != len(self.evaluation_artifact_ids):
            raise ArmError("RUN_ARTIFACT_IDENTITY_DUPLICATE")
        emitted_ids = (
            self.protocol_hash,
            self.checkpoint_id,
            self.model_artifact_id,
            *self.certificate_ids,
            *self.evaluation_artifact_ids,
        )
        if len(set(emitted_ids)) != len(emitted_ids):
            raise ArmError("RUN_OUTPUT_IDENTITY_DUPLICATE")
        if len({item.metric_id for item in self.samples}) != len(self.samples) or len(
            {phase for phase, _ in self.phase_latencies_us}
        ) != len(self.phase_latencies_us):
            raise ArmError("RUN_METRIC_IDENTITY_DUPLICATE")
        counters = (
            self.processed_tokens,
            self.bytes_sent,
            self.useful_compute_us,
            self.total_us,
            self.zero_copy_eligible,
            self.zero_copy_hits,
            self.copy_fallback_bytes,
            self.gpu_utilization_ppm,
            self.gpu_peak_reserved_bytes,
            self.host_offload_bytes,
        )
        if any(value < 0 for value in counters):
            raise ArmError("RUN_ACCOUNTING_NEGATIVE")
        if (
            self.zero_copy_hits > self.zero_copy_eligible
            or self.gpu_utilization_ppm > 1_000_000
            or self.useful_compute_us > self.total_us
            or sum(value for _, value in self.phase_latencies_us) > self.total_us
        ):
            raise ArmError("RUN_ACCOUNTING_INVALID")

    @property
    def output_id(self) -> str:
        return (
            "sha256:"
            + hashlib.sha256(
                canonical_json_bytes(
                    {
                        "arm_id": self.arm.content_id,
                        "checkpoint_id": self.checkpoint_id,
                        "certificate_ids": list(self.certificate_ids),
                        "copy_fallback_bytes": self.copy_fallback_bytes,
                        "evaluation_artifact_ids": list(self.evaluation_artifact_ids),
                        "gpu_peak_reserved_bytes": self.gpu_peak_reserved_bytes,
                        "gpu_utilization_ppm": self.gpu_utilization_ppm,
                        "host_offload_bytes": self.host_offload_bytes,
                        "model_artifact_id": self.model_artifact_id,
                        "protocol_hash": self.protocol_hash,
                        "samples": [
                            {"metric_id": item.metric_id, "unit": item.unit, "value": item.value}
                            for item in self.samples
                        ],
                        "seed": self.seed,
                        "zero_copy_eligible": self.zero_copy_eligible,
                        "zero_copy_hits": self.zero_copy_hits,
                    }
                )
            ).hexdigest()
        )

    @property
    def manifest(self) -> dict[str, object]:
        return {
            "arm_id": self.arm.content_id,
            "benchmark_definition_id": self.definition_id,
            "domain_ticket_counts": [
                {"count": count, "domain_id": domain_id}
                for domain_id, count in self.domain_ticket_counts
            ],
            "environment_manifest_id": self.environment_manifest_id,
            "fault_profile_id": self.fault_profile_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "namespace": f"benchmark-010-{self.arm.arm_id}-{self.seed}-{self.repetition}",
            "network_profile_id": self.network_profile_id,
            "output_ids": [
                self.output_id,
                self.protocol_hash,
                self.checkpoint_id,
                self.model_artifact_id,
                *self.certificate_ids,
                *self.evaluation_artifact_ids,
            ],
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "processed_tokens": self.processed_tokens,
            "repetition": self.repetition,
            "schema_version": "1.0.0",
            "seed": self.seed,
            "terminal_outcome": self.terminal_outcome,
            "ticket_plan_id": self.ticket_plan_id,
            "type_name": "RUN_MANIFEST",
        }

    @property
    def content_id(self) -> str:
        domain = b"deltareduce.010.run-manifest.v1\0"
        return "sha256:" + hashlib.sha256(domain + canonical_json_bytes(self.manifest)).hexdigest()


class SyntheticArmRunner:
    """Deterministic contract runner; refuses use as primary benchmark evidence."""

    def run(
        self,
        definition: BenchmarkDefinition,
        arm: ArmSpec,
        *,
        definition_id: str,
        environment_manifest_id: str,
        network_profile_id: str,
        fault_profile_id: str,
        seed: int,
        repetition: int,
    ) -> RunObservation:
        if definition.primary:
            raise ArmError("SYNTHETIC_ARM_FOR_PRIMARY_FORBIDDEN")
        if arm.content_id not in definition.arm_ids:
            raise ArmError("ARM_NOT_IN_DEFINITION")
        digest = hashlib.sha256(f"{definition_id}:{seed}".encode()).hexdigest()
        protocol_hash = "sha256:" + digest
        checkpoint_id = "sha256:" + hashlib.sha256(f"checkpoint:{seed}".encode()).hexdigest()
        ticket_plan_id = definition.ticket_plan_id
        parent_checkpoint_id = definition.base_model_id
        model_artifact_id = (
            "sha256:"
            + hashlib.sha256(f"model:{definition_id}:{arm.arm_id}:{seed}".encode()).hexdigest()
        )
        certificate_ids = (
            tuple(
                "sha256:"
                + hashlib.sha256(f"certificate:{kind}:{arm.arm_id}:{seed}".encode()).hexdigest()
                for kind in ("isc", "ec", "apc", "parameter-shard", "aggregate-root", "apply")
            )
            if arm.kind != "SCIENTIFIC_REFERENCE"
            else ()
        )
        evaluation_artifact_ids = tuple(
            "sha256:"
            + hashlib.sha256(f"evaluation:{evaluation_id}:{arm.arm_id}:{seed}".encode()).hexdigest()
            for evaluation_id in definition.evaluation_ids
        )
        deployment_cost = {
            "PYTHON": 0,
            "EMBEDDED_FFM": 200,
            "ISOLATED_SIDECAR": 500,
        }.get(arm.deployment_profile)
        if deployment_cost is None:
            raise ArmError("ARM_DEPLOYMENT_PROFILE_INVALID")
        loss = 1_000_000 + seed % 10_000 + deployment_cost
        samples = (
            MetricSample("validation_loss_micro", loss, "micro-loss"),
            MetricSample("downstream_accuracy_ppm", 760_000 - deployment_cost, "ppm"),
        )
        phase_latencies = (
            ("java_queue", 50 + deployment_cost),
            ("ffi_or_ipc", 25 + deployment_cost),
            ("native_transition", 100),
            ("wal", 75),
            ("network", 300),
            ("artifact", 50),
        )
        return RunObservation(
            definition_id=definition_id,
            arm=arm,
            environment_manifest_id=environment_manifest_id,
            network_profile_id=network_profile_id,
            fault_profile_id=fault_profile_id,
            seed=seed,
            repetition=repetition,
            processed_tokens=definition.B,
            domain_ticket_counts=tuple((item.domain_id, 1) for item in definition.domain_weights),
            terminal_outcome="APPLIED",
            protocol_hash=protocol_hash,
            checkpoint_id=checkpoint_id,
            ticket_plan_id=ticket_plan_id,
            parent_checkpoint_id=parent_checkpoint_id,
            certificate_ids=certificate_ids,
            model_artifact_id=model_artifact_id,
            evaluation_artifact_ids=evaluation_artifact_ids,
            samples=samples,
            phase_latencies_us=phase_latencies,
            bytes_sent=1_000 + deployment_cost,
            useful_compute_us=9_000,
            total_us=10_000 + deployment_cost,
            zero_copy_eligible=1 if arm.deployment_profile != "PYTHON" else 0,
            zero_copy_hits=1 if arm.deployment_profile == "EMBEDDED_FFM" else 0,
            copy_fallback_bytes=1_000 + deployment_cost
            if arm.deployment_profile != "EMBEDDED_FFM"
            else 0,
            gpu_utilization_ppm=500_000,
            gpu_peak_reserved_bytes=1_000_000,
            host_offload_bytes=0,
        )
