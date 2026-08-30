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
    samples: tuple[MetricSample, ...]
    phase_latencies_us: tuple[tuple[str, int], ...]
    bytes_sent: int
    useful_compute_us: int
    total_us: int

    @property
    def output_id(self) -> str:
        return (
            "sha256:"
            + hashlib.sha256(
                canonical_json_bytes(
                    {
                        "arm_id": self.arm.content_id,
                        "checkpoint_id": self.checkpoint_id,
                        "protocol_hash": self.protocol_hash,
                        "samples": [
                            {"metric_id": item.metric_id, "unit": item.unit, "value": item.value}
                            for item in self.samples
                        ],
                        "seed": self.seed,
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
            "output_ids": [self.output_id],
            "parent_checkpoint_id": "sha256:" + "1" * 64,
            "processed_tokens": self.processed_tokens,
            "repetition": self.repetition,
            "schema_version": "1.0.0",
            "seed": self.seed,
            "terminal_outcome": self.terminal_outcome,
            "ticket_plan_id": "sha256:" + "2" * 64,
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
            samples=samples,
            phase_latencies_us=phase_latencies,
            bytes_sent=1_000 + deployment_cost,
            useful_compute_us=9_000,
            total_us=10_000 + deployment_cost,
        )
