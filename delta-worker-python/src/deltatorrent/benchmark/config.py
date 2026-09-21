"""Strict loader for the frozen Feature 010 TEST_FIXTURE plan."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from deltatorrent.benchmark.adapters import STAGE_RECEIPT_PATH
from deltatorrent.benchmark.canonical import canonical_bytes, content_id, load_json_bytes
from deltatorrent.benchmark.contracts import (
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    REQUIRED_BYTE_COUNTERS,
    REQUIRED_METRIC_PHASES,
    SCHEMA_VERSION,
    CanonicalContract,
    ContractError,
    validate_scientific_dependencies,
)
from deltatorrent.benchmark.profiles import (
    ATTACK_VECTORS,
    validate_fault_corpus,
)

_FIELDS = {
    "arms",
    "attack_vectors",
    "authority_scope",
    "benchmark_definition",
    "definition_qc_id",
    "evidence_class",
    "execution_authorized",
    "fault_profiles",
    "feature010_go",
    "formal_semantics_id",
    "gate_eligible",
    "network_profiles",
    "ordered_receipt_stages",
    "primary_eligible",
    "primary_observation_count",
    "qualifying_gate_c",
    "real_wan_gate_d",
    "required_byte_counters",
    "required_metric_phases",
    "result_qc_id",
    "runtime_constraints",
    "runtime_identity",
    "schema_version",
    "scientific_profile",
    "type_name",
}
_RUNTIME_CONSTRAINTS = {
    "cpp_compilers": ["CLANG", "GCC"],
    "cuda_profile_status": "UNQUALIFIED",
    "fast_math": False,
    "jdk_compatibility": 26,
    "jdk_reference": 25,
    "native_checked_arithmetic": True,
    "netty_lock_required": True,
    "python_minor": "3.12",
}


@dataclass(frozen=True, slots=True)
class FrozenFoundationConfig:
    _document_bytes: bytes
    definition: CanonicalContract
    runtime_identity: CanonicalContract
    scientific_profile: CanonicalContract
    arms: tuple[CanonicalContract, ...]
    network_profiles: tuple[CanonicalContract, ...]
    fault_profiles: tuple[CanonicalContract, ...]
    content_id: str

    @property
    def document(self) -> dict[str, Any]:
        """Return a defensive copy while retaining immutable identity bytes."""

        return load_json_bytes(self._document_bytes)


def _contracts(value: object, expected_type: str, code: str) -> tuple[CanonicalContract, ...]:
    if not isinstance(value, list) or not value:
        raise ContractError(code)
    contracts = tuple(CanonicalContract.from_dict(item) for item in value)
    if any(item.type_name != expected_type for item in contracts):
        raise ContractError(code)
    if len({item.content_id for item in contracts}) != len(contracts):
        raise ContractError(code)
    return contracts


def validate_foundation_config(document: object, *, raw_bytes: bytes) -> FrozenFoundationConfig:
    if not isinstance(document, dict) or set(document) != _FIELDS:
        raise ContractError("FOUNDATION_CONFIG_FIELDS_INVALID")
    value = cast(dict[str, Any], document)
    if type(raw_bytes) is not bytes or raw_bytes != canonical_bytes(value):
        raise ContractError("FOUNDATION_CONFIG_BYTES_MISMATCH")
    expected_base = {
        "authority_scope": AUTHORITY_SCOPE,
        "evidence_class": "TEST_FIXTURE",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "schema_version": SCHEMA_VERSION,
        "type_name": "FEATURE010_FOUNDATION_CONFIG",
    }
    if any(value[key] != expected for key, expected in expected_base.items()):
        raise ContractError("FOUNDATION_CONFIG_IDENTITY_INVALID")
    zero_authority = {
        "definition_qc_id": None,
        "execution_authorized": False,
        "feature010_go": False,
        "gate_eligible": False,
        "primary_eligible": False,
        "primary_observation_count": 0,
        "qualifying_gate_c": False,
        "real_wan_gate_d": False,
        "result_qc_id": None,
    }
    if any(
        type(value[key]) is not type(expected) or value[key] != expected
        for key, expected in zero_authority.items()
    ):
        raise ContractError("FOUNDATION_CONFIG_AUTHORITY_FORBIDDEN")
    if value["runtime_constraints"] != _RUNTIME_CONSTRAINTS:
        raise ContractError("FOUNDATION_CONFIG_RUNTIME_CONSTRAINTS_INVALID")
    if tuple(value["ordered_receipt_stages"]) != STAGE_RECEIPT_PATH:
        raise ContractError("FOUNDATION_CONFIG_RECEIPT_STAGES_INVALID")
    if tuple(value["required_metric_phases"]) != REQUIRED_METRIC_PHASES:
        raise ContractError("FOUNDATION_CONFIG_METRIC_PHASES_INVALID")
    if tuple(value["required_byte_counters"]) != REQUIRED_BYTE_COUNTERS:
        raise ContractError("FOUNDATION_CONFIG_BYTE_COUNTERS_INVALID")
    if value["attack_vectors"] != [vector.to_dict() for vector in ATTACK_VECTORS]:
        raise ContractError("FOUNDATION_CONFIG_ATTACK_VECTORS_INVALID")

    definition = CanonicalContract.from_dict(value["benchmark_definition"])
    runtime = CanonicalContract.from_dict(value["runtime_identity"])
    science = CanonicalContract.from_dict(value["scientific_profile"])
    arms = _contracts(value["arms"], "BENCHMARK_ARM", "FOUNDATION_CONFIG_ARMS_INVALID")
    networks = _contracts(
        value["network_profiles"],
        "BENCHMARK_NETWORK_PROFILE",
        "FOUNDATION_CONFIG_NETWORKS_INVALID",
    )
    faults = _contracts(
        value["fault_profiles"],
        "BENCHMARK_FAULT_PROFILE",
        "FOUNDATION_CONFIG_FAULTS_INVALID",
    )
    definition_value = definition.to_dict()
    if definition_value["runtime_identity_id"] != runtime.content_id:
        raise ContractError("FOUNDATION_CONFIG_RUNTIME_JOIN_INVALID")
    if definition_value["scientific_profile_id"] != science.content_id:
        raise ContractError("FOUNDATION_CONFIG_SCIENCE_JOIN_INVALID")
    if tuple(definition_value["arm_ids"]) != tuple(sorted(item.content_id for item in arms)):
        raise ContractError("FOUNDATION_CONFIG_ARM_JOIN_INVALID")
    if {str(item.to_dict()["arm_kind"]) for item in arms} != {"REFERENCE", "DELTAREDUCE"}:
        raise ContractError("FOUNDATION_CONFIG_ARM_KIND_SET_INVALID")
    if tuple(definition_value["network_profile_ids"]) != tuple(
        sorted(item.content_id for item in networks)
    ):
        raise ContractError("FOUNDATION_CONFIG_NETWORK_JOIN_INVALID")
    if tuple(definition_value["fault_profile_ids"]) != tuple(
        sorted(item.content_id for item in faults)
    ):
        raise ContractError("FOUNDATION_CONFIG_FAULT_JOIN_INVALID")
    validate_scientific_dependencies(definition, science)
    validate_fault_corpus(faults)
    return FrozenFoundationConfig(
        _document_bytes=raw_bytes,
        definition=definition,
        runtime_identity=runtime,
        scientific_profile=science,
        arms=arms,
        network_profiles=networks,
        fault_profiles=faults,
        content_id=content_id(raw_bytes),
    )


def load_foundation_config(path: Path) -> FrozenFoundationConfig:
    raw = path.read_bytes()
    return validate_foundation_config(load_json_bytes(raw), raw_bytes=raw)
