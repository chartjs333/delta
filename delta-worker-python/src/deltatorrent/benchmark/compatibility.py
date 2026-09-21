"""Exact, non-coercing runtime compatibility admission for benchmark plans."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.contracts import CanonicalContract, ContractError


@dataclass(frozen=True, slots=True)
class CompatibilityAdmission:
    expected_identity_id: str
    actual_identity_id: str
    mismatch_codes: tuple[str, ...]
    admitted: bool
    deployment_profile: str
    admission_class: str = "CONFORMANCE_ONLY"


def compare_runtime_identities(
    expected: CanonicalContract,
    actual: CanonicalContract,
) -> CompatibilityAdmission:
    if expected.type_name != "BENCHMARK_RUNTIME_IDENTITY":
        raise ContractError("EXPECTED_RUNTIME_IDENTITY_TYPE_INVALID")
    if actual.type_name != "BENCHMARK_RUNTIME_IDENTITY":
        raise ContractError("ACTUAL_RUNTIME_IDENTITY_TYPE_INVALID")
    expected_doc = expected.to_dict()
    actual_doc = actual.to_dict()
    fields = tuple(sorted(expected_doc))
    mismatches = tuple(
        sorted(
            f"{field.upper()}_MISMATCH"
            for field in fields
            if expected_doc[field] != actual_doc[field]
        )
    )
    return CompatibilityAdmission(
        expected_identity_id=expected.content_id,
        actual_identity_id=actual.content_id,
        mismatch_codes=mismatches,
        admitted=not mismatches,
        deployment_profile=str(actual_doc["deployment_profile"]),
    )


def admit_plan(
    *,
    definition: CanonicalContract,
    expected_runtime: CanonicalContract,
    actual_runtime: CanonicalContract,
    environment: CanonicalContract,
    admission_class: str = "CONFORMANCE_ONLY",
) -> CompatibilityAdmission:
    """Admit only an exact conformance plan; primary admission is out of scope."""

    if admission_class != "CONFORMANCE_ONLY":
        raise ContractError("FOUNDATION_PRIMARY_ADMISSION_FORBIDDEN")
    if definition.type_name != "BENCHMARK_DEFINITION":
        raise ContractError("ADMISSION_DEFINITION_TYPE_INVALID")
    if environment.type_name != "BENCHMARK_ENVIRONMENT_MANIFEST":
        raise ContractError("ADMISSION_ENVIRONMENT_TYPE_INVALID")
    definition_doc = definition.to_dict()
    environment_doc = environment.to_dict()
    if definition_doc["runtime_identity_id"] != expected_runtime.content_id:
        raise ContractError("DEFINITION_RUNTIME_IDENTITY_MISMATCH")
    if environment_doc["runtime_identity_id"] != actual_runtime.content_id:
        raise ContractError("ENVIRONMENT_RUNTIME_IDENTITY_MISMATCH")
    actual_doc = actual_runtime.to_dict()
    for field in ("source_commit", "source_tree", "sbom_id"):
        if environment_doc[field] != actual_doc[field]:
            raise ContractError(f"ENVIRONMENT_{field.upper()}_MISMATCH")
    required_locks = {
        actual_doc["compiler_lock_id"],
        actual_doc["java_dependency_lock_id"],
        actual_doc["python_lock_id"],
    }
    if not required_locks <= set(environment_doc["dependency_lock_ids"]):
        raise ContractError("ENVIRONMENT_DEPENDENCY_LOCK_SET_INCOMPLETE")
    required_binaries = {
        actual_doc["binary_build_id"],
        actual_doc["native_runtime_id"],
    }
    if not required_binaries <= set(environment_doc["binary_ids"]):
        raise ContractError("ENVIRONMENT_BINARY_SET_INCOMPLETE")
    admission = compare_runtime_identities(expected_runtime, actual_runtime)
    return CompatibilityAdmission(
        expected_identity_id=admission.expected_identity_id,
        actual_identity_id=admission.actual_identity_id,
        mismatch_codes=admission.mismatch_codes,
        admitted=admission.admitted,
        deployment_profile=admission.deployment_profile,
        admission_class=admission_class,
    )
