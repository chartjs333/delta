"""Deterministic scientific/network/fault profile helpers (plan-only)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from deltatorrent.benchmark.canonical import canonical_bytes, content_id
from deltatorrent.benchmark.contracts import (
    FAULT_EXPECTED_TERMINALS,
    CanonicalContract,
    ContractError,
)

FAULT_EVENT_KINDS = (
    "CONCENTRATED_CHURN",
    "DISPERSED_CHURN",
    "REGION_PARTITION",
    "REGION_RESTORE",
    "STORAGE_CRASH",
    "STORAGE_RESTART",
    "VALIDATOR_CRASH",
    "VALIDATOR_RESTART",
    "WORKER_CRASH",
    "WORKER_RESTART",
)


@dataclass(frozen=True, slots=True)
class AttackVector:
    attack_id: str
    target_stage: str
    mutation: str
    expected_terminal: str

    def to_dict(self) -> dict[str, str]:
        return {
            "attack_id": self.attack_id,
            "expected_terminal": self.expected_terminal,
            "mutation": self.mutation,
            "target_stage": self.target_stage,
        }


ATTACK_VECTORS = (
    AttackVector("APPLY_CONFLICT", "APPLY", "CONFLICTING_APPLY_QC", "REJECT"),
    AttackVector("CERTIFICATE_DOWNGRADE", "P2P", "DOWNGRADE_CERTIFICATE", "REJECT"),
    AttackVector("CONFLICTING_CONFIG", "CONFIG", "CONFLICTING_CONFIG_QC", "REJECT"),
    AttackVector("CONFLICTING_VOTE", "VOTE", "DUPLICATE_SIGNER_CONFLICT", "REJECT"),
    AttackVector("EARLY_SEED", "P2P", "SEED_BEFORE_ISC", "REJECT"),
    AttackVector("INCOMPLETE_AGGREGATE", "REDUCE", "OMIT_DOMAIN", "REJECT"),
    AttackVector("MIXED_VIEW", "REDUCE", "MIX_PARENT_VIEWS", "REJECT"),
    AttackVector(
        "MUTATED_ACCUMULATOR_CERTIFICATE",
        "REDUCE",
        "MUTATE_ACCUMULATOR_CERTIFICATE",
        "REJECT",
    ),
    AttackVector("OVERFLOW_INPUT", "ARITHMETIC", "I64_OVERFLOW", "REJECT"),
    AttackVector("WRONG_EPOCH", "VOTE", "REPLAY_WRONG_EPOCH", "REJECT"),
)
ATTACK_CORPUS = tuple(vector.attack_id for vector in ATTACK_VECTORS)


@dataclass(frozen=True, slots=True)
class FaultEventTemplate:
    at_ms: int
    event_id: str
    expected_terminal: str
    kind: str
    target: str

    def to_dict(self) -> dict[str, object]:
        return {
            "at_ms": self.at_ms,
            "event_id": self.event_id,
            "expected_terminal": self.expected_terminal,
            "kind": self.kind,
            "target": self.target,
        }


FOUNDATION_FAULT_EVENTS = tuple(
    FaultEventTemplate(
        at_ms=(index + 1) * 1_000,
        event_id=f"foundation-{kind.lower().replace('_', '-')}",
        expected_terminal=FAULT_EXPECTED_TERMINALS[kind],
        kind=kind,
        target=f"fixture-{kind.lower().replace('_', '-')}",
    )
    for index, kind in enumerate(FAULT_EVENT_KINDS)
)


@dataclass(frozen=True, slots=True)
class NetemPlan:
    apply_argv: tuple[str, ...]
    cleanup_argv: tuple[str, ...]
    profile_id: str
    duration_ms: int
    seed: int
    disconnect_after_ms: int | None
    partition_after_ms: int | None
    label: str = "SIMULATED"


@dataclass(frozen=True, slots=True)
class FaultTrace:
    profile_id: str
    canonical_events: bytes
    trace_id: str
    expected_terminals: tuple[str, ...]
    label: str = "SIMULATED"


@dataclass(frozen=True, slots=True)
class AttackTrace:
    canonical_vectors: bytes
    trace_id: str
    expected_terminals: tuple[str, ...]
    label: str = "TEST_FIXTURE"


def _ppm_percent(value: int) -> str:
    return f"{value // 10_000}.{value % 10_000:04d}%"


def plan_tc_netem(profile: CanonicalContract, *, interface: str) -> NetemPlan:
    """Build inert argv for an optional tc/netem adapter; never execute it."""

    if profile.type_name != "BENCHMARK_NETWORK_PROFILE":
        raise ContractError("NETEM_PROFILE_TYPE_INVALID")
    if re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", interface) is None:
        raise ContractError("NETEM_INTERFACE_INVALID")
    value = profile.to_dict()
    if value["adapter"] != "OPTIONAL_TC_NETEM" or value["label"] != "SIMULATED":
        raise ContractError("NETEM_PROFILE_NOT_ELIGIBLE")
    one_way_delay = (int(value["rtt_ms"]) + 1) // 2
    apply_argv = (
        "tc",
        "qdisc",
        "replace",
        "dev",
        interface,
        "root",
        "netem",
        "delay",
        f"{one_way_delay}ms",
        f"{value['jitter_ms']}ms",
        "loss",
        _ppm_percent(int(value["loss_ppm"])),
        "duplicate",
        _ppm_percent(int(value["duplicate_ppm"])),
        "reorder",
        _ppm_percent(int(value["reorder_ppm"])),
        "rate",
        f"{int(value['bandwidth_bytes_per_second']) * 8}bit",
    )
    return NetemPlan(
        apply_argv=apply_argv,
        cleanup_argv=("tc", "qdisc", "del", "dev", interface, "root"),
        profile_id=profile.content_id,
        duration_ms=int(value["duration_ms"]),
        seed=int(value["seed"]),
        disconnect_after_ms=value["disconnect_after_ms"],
        partition_after_ms=value["partition_after_ms"],
    )


def replay_fault_profile(profile: CanonicalContract) -> FaultTrace:
    """Materialize the exact declared fixture trace without inferring observations."""

    if profile.type_name != "BENCHMARK_FAULT_PROFILE":
        raise ContractError("FAULT_TRACE_PROFILE_TYPE_INVALID")
    value = profile.to_dict()
    if value["label"] != "SIMULATED":
        raise ContractError("FAULT_TRACE_LABEL_INVALID")
    events = value["events"]
    if any(
        event["expected_terminal"] != FAULT_EXPECTED_TERMINALS[event["kind"]] for event in events
    ):
        raise ContractError("FAULT_TRACE_TERMINAL_MISMATCH")
    encoded = canonical_bytes(events)
    return FaultTrace(
        profile_id=profile.content_id,
        canonical_events=encoded,
        trace_id=content_id(encoded),
        expected_terminals=tuple(str(event["expected_terminal"]) for event in events),
    )


def validate_attack_corpus(values: tuple[str, ...]) -> None:
    if values != ATTACK_CORPUS:
        raise ContractError("ATTACK_CORPUS_MISMATCH")


def replay_attack_corpus(vectors: tuple[AttackVector, ...] = ATTACK_VECTORS) -> AttackTrace:
    """Return a deterministic non-executing attack-vector transcript."""

    if vectors != ATTACK_VECTORS:
        raise ContractError("ATTACK_VECTOR_CORPUS_MISMATCH")
    encoded = canonical_bytes([vector.to_dict() for vector in vectors])
    return AttackTrace(
        canonical_vectors=encoded,
        trace_id=content_id(encoded),
        expected_terminals=tuple(vector.expected_terminal for vector in vectors),
    )


def validate_fault_corpus(profiles: tuple[CanonicalContract, ...]) -> None:
    """Require the frozen fixture corpus to cover every declared fault kind."""

    observed: list[dict[str, object]] = []
    for profile in profiles:
        if profile.type_name != "BENCHMARK_FAULT_PROFILE":
            raise ContractError("FAULT_CORPUS_PROFILE_TYPE_INVALID")
        observed.extend(profile.to_dict()["events"])
    expected = [event.to_dict() for event in FOUNDATION_FAULT_EVENTS]
    if observed != expected:
        raise ContractError("FAULT_CORPUS_INCOMPLETE")
