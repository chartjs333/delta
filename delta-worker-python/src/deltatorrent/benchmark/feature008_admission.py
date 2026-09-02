"""Run-level admission against the authoritative native Feature 008 chain verifier.

Python performs fail-closed typed preflight, then submits one canonical complete
bundle to the C ABI.  Only the content-addressed receipt from the native C++
``delta::certificates::ChainVerifier`` can admit a certified observation.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any, Final, Protocol

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_SHA256_HEX: Final = re.compile(r"^[0-9a-f]{64}$")
_CONTEXT_FIELDS: Final = (
    "arithmetic_profile_id",
    "height",
    "parameter_schema_id",
    "round_config_id",
    "round_id",
    "validator_epoch_id",
    "view",
)
_CERTIFICATE_DOMAINS: Final = {
    "INPUT_SET_CERTIFICATE": "deltareduce.008.input-set-certificate.v1",
    "SEED_TRANSCRIPT": "deltareduce.008.seed-transcript.v1",
    "NORM_EVIDENCE": "deltareduce.008.norm-evidence.v1",
    "ELIGIBILITY_CERTIFICATE": "deltareduce.008.eligibility-certificate.v1",
    "AGGREGATION_PLAN_CERTIFICATE": "deltareduce.008.aggregation-plan-certificate.v1",
    "PARAMETER_SHARD_QC": "deltareduce.008.parameter-shard-qc.v1",
    "AGGREGATE_ROOT_QC": "deltareduce.008.aggregate-root-qc.v1",
    "APPLY_ARITHMETIC_PROFILE": "deltareduce.008.apply-arithmetic-profile.v1",
    "APPLY_CANDIDATE": "deltareduce.008.apply-candidate.v1",
    "APPLY_QC": "deltareduce.008.apply-qc.v1",
    "CURRENT_POINTER_COMMAND": "deltareduce.008.current-pointer-command.v1",
}
_CERTIFICATE_FIELDS: Final = {
    "INPUT_SET_CERTIFICATE": frozenset(
        {
            *_CONTEXT_FIELDS,
            "formal_semantics_id",
            "input_root",
            "quorum_threshold",
            "schema_version",
            "signer_ids",
            "tuples",
            "type_name",
        }
    ),
    "SEED_TRANSCRIPT": frozenset(
        {
            *_CONTEXT_FIELDS,
            "formal_semantics_id",
            "input_set_certificate_id",
            "schema_version",
            "seed_id",
            "seed_profile_id",
            "share_ids",
            "type_name",
        }
    ),
    "NORM_EVIDENCE": frozenset(
        {
            *_CONTEXT_FIELDS,
            "entries",
            "formal_semantics_id",
            "input_set_certificate_id",
            "norm_root",
            "schema_version",
            "type_name",
        }
    ),
    "ELIGIBILITY_CERTIFICATE": frozenset(
        {
            *_CONTEXT_FIELDS,
            "entries",
            "formal_semantics_id",
            "input_set_certificate_id",
            "norm_evidence_id",
            "quorum_threshold",
            "robust_profile_id",
            "schema_version",
            "signer_ids",
            "type_name",
        }
    ),
    "AGGREGATION_PLAN_CERTIFICATE": frozenset(
        {
            *_CONTEXT_FIELDS,
            "accumulator_proof_id",
            "bucket_assignments",
            "eligibility_certificate_id",
            "formal_semantics_id",
            "input_set_certificate_id",
            "iteration_count",
            "quorum_threshold",
            "schema_version",
            "seed_transcript_id",
            "signer_ids",
            "transcript_root",
            "type_name",
            "weights",
        }
    ),
    "PARAMETER_SHARD_QC": frozenset(
        {
            *_CONTEXT_FIELDS,
            "aggregation_plan_certificate_id",
            "denominator",
            "domain_id",
            "eligibility_certificate_id",
            "formal_semantics_id",
            "input_leaf_ids",
            "input_set_certificate_id",
            "quorum_threshold",
            "result_numerators",
            "schema_version",
            "shard_id",
            "signer_ids",
            "type_name",
        }
    ),
    "AGGREGATE_ROOT_QC": frozenset(
        {
            *_CONTEXT_FIELDS,
            "aggregation_plan_certificate_id",
            "eligibility_certificate_id",
            "formal_semantics_id",
            "input_set_certificate_id",
            "leaves",
            "merkle_root",
            "quorum_threshold",
            "required_keys",
            "schema_version",
            "signer_ids",
            "type_name",
        }
    ),
    "APPLY_ARITHMETIC_PROFILE": frozenset(
        {
            "accumulator_proof_id",
            "domain_weights",
            "formal_semantics_id",
            "learning_rate",
            "momentum",
            "nesterov",
            "rounding",
            "schema_version",
            "type_name",
            "weight_decay",
        }
    ),
    "APPLY_CANDIDATE": frozenset(
        {
            *_CONTEXT_FIELDS,
            "aggregate_root_qc_id",
            "apply_arithmetic_profile_id",
            "formal_semantics_id",
            "next_model_hash",
            "next_model_values",
            "next_optimizer_hash",
            "next_optimizer_values",
            "parent_checkpoint_id",
            "parent_optimizer_hash",
            "schema_version",
            "type_name",
        }
    ),
    "APPLY_QC": frozenset(
        {
            *_CONTEXT_FIELDS,
            "aggregate_root_qc_id",
            "apply_arithmetic_profile_id",
            "apply_candidate_id",
            "formal_semantics_id",
            "next_model_hash",
            "next_optimizer_hash",
            "parent_checkpoint_id",
            "quorum_threshold",
            "schema_version",
            "signer_ids",
            "type_name",
        }
    ),
    "CURRENT_POINTER_COMMAND": frozenset(
        {
            *_CONTEXT_FIELDS,
            "apply_qc_id",
            "expected_parent_checkpoint_id",
            "formal_semantics_id",
            "next_checkpoint_id",
            "next_optimizer_hash",
            "schema_version",
            "type_name",
        }
    ),
}


class Feature008AdmissionError(ValueError):
    """Stable rejection from run-level Feature 008 admission."""


def _fail(code: str) -> Feature008AdmissionError:
    return Feature008AdmissionError(code)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise _fail(code)


def _content_id(value: object, code: str) -> str:
    if not isinstance(value, str) or _CONTENT_ID.fullmatch(value) is None:
        raise _fail(code)
    return value


def _mapping(value: object, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _fail(code)
    return value


def _sequence(value: object, code: str) -> list[Any]:
    if not isinstance(value, list):
        raise _fail(code)
    return value


def _certificate_id(type_name: str, payload: bytes) -> str:
    domain = _CERTIFICATE_DOMAINS[type_name]
    return sha256_content_id(domain.encode("ascii") + b"\0" + payload)


def _label(value: object, code: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value) is None:
        raise _fail(code)
    return value


def _canonical_i64(value: object, code: str, *, non_negative: bool = False) -> int:
    if not isinstance(value, str) or re.fullmatch(r"0|-?[1-9][0-9]*", value) is None:
        raise _fail(code)
    parsed = int(value)
    if not -(2**63) <= parsed < 2**63 or (non_negative and parsed < 0):
        raise _fail(code)
    return parsed


def _rational(value: object, code: str, *, non_negative: bool = False) -> None:
    item = _mapping(value, code)
    _require(set(item) == {"denominator", "numerator"}, code)
    denominator = item.get("denominator")
    _require(
        isinstance(denominator, int)
        and not isinstance(denominator, bool)
        and 0 < denominator < 2**64,
        code,
    )
    assert isinstance(denominator, int)
    numerator = _canonical_i64(item.get("numerator"), code, non_negative=non_negative)
    _require(math.gcd(abs(numerator), denominator) == 1, code)


def _strict_order(values: list[Any], key: Any, code: str) -> None:
    projected = [key(item) for item in values]
    _require(all(left < right for left, right in pairwise(projected)), code)


def _canonical_content_array(value: object, code: str) -> list[Any]:
    items = _sequence(value, code)
    _strict_order(items, lambda item: str(item), code)
    for item in items:
        _content_id(item, code)
    return items


def _typed_certificate_preflight(type_name: str, value: dict[str, Any]) -> None:
    if "signer_ids" in value:
        signers = _sequence(value["signer_ids"], "FEATURE008_SIGNER_SET_INVALID")
        _strict_order(
            signers,
            lambda item: _label(item, "FEATURE008_SIGNER_SET_INVALID"),
            "FEATURE008_SIGNER_SET_INVALID",
        )
    if type_name == "INPUT_SET_CERTIFICATE":
        tuples = _sequence(value.get("tuples"), "FEATURE008_ISC_TUPLE_SET_INVALID")
        _strict_order(
            tuples,
            lambda raw: (
                _label(
                    _mapping(raw, "FEATURE008_ISC_TUPLE_INVALID").get("ticket_id"),
                    "FEATURE008_ISC_TUPLE_INVALID",
                ),
                _content_id(
                    _mapping(raw, "FEATURE008_ISC_TUPLE_INVALID").get("commitment_id"),
                    "FEATURE008_ISC_TUPLE_INVALID",
                ),
            ),
            "FEATURE008_ISC_TUPLE_SET_INVALID",
        )
        for raw in tuples:
            item = _mapping(raw, "FEATURE008_ISC_TUPLE_INVALID")
            _content_id(item.get("availability_certificate_id"), "FEATURE008_ISC_TUPLE_INVALID")
            _label(item.get("domain_id"), "FEATURE008_ISC_TUPLE_INVALID")
    elif type_name == "SEED_TRANSCRIPT":
        _canonical_content_array(value.get("share_ids"), "FEATURE008_SEED_SHARE_SET_INVALID")
    elif type_name == "NORM_EVIDENCE":
        entries = _sequence(value.get("entries"), "FEATURE008_NORM_ENTRY_SET_INVALID")
        _strict_order(
            entries,
            lambda raw: _label(
                _mapping(raw, "FEATURE008_NORM_ENTRY_INVALID").get("ticket_id"),
                "FEATURE008_NORM_ENTRY_INVALID",
            ),
            "FEATURE008_NORM_ENTRY_SET_INVALID",
        )
        for raw in entries:
            item = _mapping(raw, "FEATURE008_NORM_ENTRY_INVALID")
            _require(
                isinstance(item.get("scale_denominator"), int)
                and not isinstance(item.get("scale_denominator"), bool)
                and 0 < item["scale_denominator"] < 2**64,
                "FEATURE008_NORM_ENTRY_INVALID",
            )
            _canonical_i64(
                item.get("squared_norm"), "FEATURE008_NORM_ENTRY_INVALID", non_negative=True
            )
    elif type_name == "ELIGIBILITY_CERTIFICATE":
        entries = _sequence(value.get("entries"), "FEATURE008_EC_ENTRY_SET_INVALID")
        _strict_order(
            entries,
            lambda raw: _label(
                _mapping(raw, "FEATURE008_EC_ENTRY_INVALID").get("ticket_id"),
                "FEATURE008_EC_ENTRY_INVALID",
            ),
            "FEATURE008_EC_ENTRY_SET_INVALID",
        )
        for raw in entries:
            item = _mapping(raw, "FEATURE008_EC_ENTRY_INVALID")
            _rational(item.get("gamma"), "FEATURE008_EC_RATIONAL_INVALID", non_negative=True)
    elif type_name == "AGGREGATION_PLAN_CERTIFICATE":
        assignments = _sequence(
            value.get("bucket_assignments"), "FEATURE008_APC_ASSIGNMENT_SET_INVALID"
        )
        weights = _sequence(value.get("weights"), "FEATURE008_APC_WEIGHT_SET_INVALID")
        _strict_order(
            assignments,
            lambda raw: _label(
                _mapping(raw, "FEATURE008_APC_ASSIGNMENT_INVALID").get("ticket_id"),
                "FEATURE008_APC_ASSIGNMENT_INVALID",
            ),
            "FEATURE008_APC_ASSIGNMENT_SET_INVALID",
        )
        _strict_order(
            weights,
            lambda raw: _label(
                _mapping(raw, "FEATURE008_APC_WEIGHT_INVALID").get("ticket_id"),
                "FEATURE008_APC_WEIGHT_INVALID",
            ),
            "FEATURE008_APC_WEIGHT_SET_INVALID",
        )
        for raw in weights:
            _rational(
                _mapping(raw, "FEATURE008_APC_WEIGHT_INVALID").get("alpha"),
                "FEATURE008_APC_RATIONAL_INVALID",
                non_negative=True,
            )
    elif type_name == "PARAMETER_SHARD_QC":
        _canonical_content_array(value.get("input_leaf_ids"), "FEATURE008_SHARD_LEAF_SET_INVALID")
        denominator = value.get("denominator")
        _require(
            isinstance(denominator, int)
            and not isinstance(denominator, bool)
            and 0 < denominator < 2**64,
            "FEATURE008_SHARD_DENOMINATOR_INVALID",
        )
        for item in _sequence(
            value.get("result_numerators"), "FEATURE008_SHARD_NUMERATOR_SET_INVALID"
        ):
            _canonical_i64(item, "FEATURE008_SHARD_NUMERATOR_INVALID")
    elif type_name == "AGGREGATE_ROOT_QC":
        required = _sequence(value.get("required_keys"), "FEATURE008_ROOT_REQUIRED_SET_INVALID")
        leaves = _sequence(value.get("leaves"), "FEATURE008_ROOT_LEAF_SET_INVALID")

        def key(raw: object) -> tuple[str, str]:
            mapped = _mapping(raw, "FEATURE008_ROOT_KEY_INVALID")
            return (
                _label(mapped.get("domain_id"), "FEATURE008_ROOT_KEY_INVALID"),
                _label(mapped.get("shard_id"), "FEATURE008_ROOT_KEY_INVALID"),
            )

        _strict_order(required, key, "FEATURE008_ROOT_REQUIRED_SET_INVALID")
        _strict_order(leaves, key, "FEATURE008_ROOT_LEAF_SET_INVALID")
        for raw in leaves:
            _content_id(
                _mapping(raw, "FEATURE008_ROOT_LEAF_INVALID").get("parameter_shard_qc_id"),
                "FEATURE008_ROOT_LEAF_INVALID",
            )
    elif type_name == "APPLY_ARITHMETIC_PROFILE":
        weights = _sequence(value.get("domain_weights"), "FEATURE008_DOMAIN_WEIGHT_SET_INVALID")
        _strict_order(
            weights,
            lambda raw: _label(
                _mapping(raw, "FEATURE008_DOMAIN_WEIGHT_INVALID").get("domain_id"),
                "FEATURE008_DOMAIN_WEIGHT_INVALID",
            ),
            "FEATURE008_DOMAIN_WEIGHT_SET_INVALID",
        )
        for raw in weights:
            _rational(
                _mapping(raw, "FEATURE008_DOMAIN_WEIGHT_INVALID").get("pi"),
                "FEATURE008_DOMAIN_WEIGHT_INVALID",
                non_negative=True,
            )
        for name in ("learning_rate", "momentum", "weight_decay"):
            _rational(value.get(name), "FEATURE008_APPLY_RATIONAL_INVALID", non_negative=True)
    elif type_name == "APPLY_CANDIDATE":
        for name in ("next_model_values", "next_optimizer_values"):
            for item in _sequence(value.get(name), "FEATURE008_APPLY_VECTOR_INVALID"):
                _canonical_i64(item, "FEATURE008_APPLY_VECTOR_INVALID")


@dataclass(frozen=True, slots=True)
class CertificateArtifact:
    """One exact canonical Feature 008 artifact and its domain-separated ID."""

    type_name: str
    content_id: str
    canonical_bytes: bytes
    value: dict[str, Any] = field(init=False, repr=False)

    @classmethod
    def from_value(cls, value: dict[str, Any]) -> CertificateArtifact:
        payload = canonical_json_bytes(value)
        type_name = str(value.get("type_name"))
        _require(type_name in _CERTIFICATE_DOMAINS, "FEATURE008_CERTIFICATE_TYPE_INVALID")
        return cls(type_name, _certificate_id(type_name, payload), payload)

    def __post_init__(self) -> None:
        _require(self.type_name in _CERTIFICATE_DOMAINS, "FEATURE008_CERTIFICATE_TYPE_INVALID")
        _content_id(self.content_id, "FEATURE008_CERTIFICATE_ID_INVALID")
        try:
            value = json.loads(self.canonical_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _fail("FEATURE008_CERTIFICATE_JSON_INVALID") from exc
        _require(
            isinstance(value, dict)
            and canonical_json_bytes(value) == self.canonical_bytes
            and value.get("type_name") == self.type_name
            and value.get("schema_version") == "1.0.0"
            and value.get("formal_semantics_id") == FORMAL_SEMANTICS_ID,
            "FEATURE008_CERTIFICATE_CANONICAL_INVALID",
        )
        _require(
            set(value) == _CERTIFICATE_FIELDS[self.type_name],
            "FEATURE008_CERTIFICATE_FIELDS_INVALID",
        )
        _require(
            _certificate_id(self.type_name, self.canonical_bytes) == self.content_id,
            "FEATURE008_CERTIFICATE_CONTENT_ID_MISMATCH",
        )
        _typed_certificate_preflight(self.type_name, value)
        object.__setattr__(self, "value", value)

    @property
    def name(self) -> str:
        stem = self.type_name.lower().replace("_", "-")
        return f"{stem}-{self.content_id[7:23]}.json"

    @property
    def media_type(self) -> str:
        return (
            f"application/vnd.deltareduce.{self.type_name.lower().replace('_', '-')}+json;version=1"
        )


@dataclass(frozen=True, slots=True)
class Feature008CertificateBundle:
    """Exactly one complete ISC→EC/APC→shards→root→ApplyQC chain."""

    input_set: CertificateArtifact
    seed_transcript: CertificateArtifact
    norm_evidence: CertificateArtifact
    eligibility: CertificateArtifact
    aggregation_plan: CertificateArtifact
    parameter_shards: tuple[CertificateArtifact, ...]
    aggregate_root: CertificateArtifact
    apply_profile: CertificateArtifact
    apply_candidate: CertificateArtifact
    apply_qc: CertificateArtifact
    current_pointer_command: CertificateArtifact

    def __post_init__(self) -> None:
        expected = (
            (self.input_set, "INPUT_SET_CERTIFICATE"),
            (self.seed_transcript, "SEED_TRANSCRIPT"),
            (self.norm_evidence, "NORM_EVIDENCE"),
            (self.eligibility, "ELIGIBILITY_CERTIFICATE"),
            (self.aggregation_plan, "AGGREGATION_PLAN_CERTIFICATE"),
            (self.aggregate_root, "AGGREGATE_ROOT_QC"),
            (self.apply_profile, "APPLY_ARITHMETIC_PROFILE"),
            (self.apply_candidate, "APPLY_CANDIDATE"),
            (self.apply_qc, "APPLY_QC"),
            (self.current_pointer_command, "CURRENT_POINTER_COMMAND"),
        )
        _require(
            all(artifact.type_name == type_name for artifact, type_name in expected),
            "FEATURE008_CERTIFICATE_BUNDLE_TYPE_MISMATCH",
        )
        _require(
            bool(self.parameter_shards)
            and all(item.type_name == "PARAMETER_SHARD_QC" for item in self.parameter_shards),
            "FEATURE008_PARAMETER_SHARD_SET_INVALID",
        )
        ids = [item.content_id for item in self.artifacts]
        _require(len(ids) == len(set(ids)), "FEATURE008_CERTIFICATE_BUNDLE_DUPLICATE")

    @property
    def artifacts(self) -> tuple[CertificateArtifact, ...]:
        return (
            self.input_set,
            self.seed_transcript,
            self.norm_evidence,
            self.eligibility,
            self.aggregation_plan,
            *self.parameter_shards,
            self.aggregate_root,
            self.apply_profile,
            self.apply_candidate,
            self.apply_qc,
            self.current_pointer_command,
        )


class _BytesView(ctypes.Structure):
    _fields_ = [("data", ctypes.POINTER(ctypes.c_uint8)), ("size", ctypes.c_size_t)]


class _OutputBuffer(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("capacity", ctypes.c_size_t),
        ("required", ctypes.c_size_t),
        ("written", ctypes.c_size_t),
    ]


class _RuntimeDescriptor(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_major", ctypes.c_uint16),
        ("abi_minor", ctypes.c_uint16),
        ("feature_bits", ctypes.c_uint64),
        ("schema_version", ctypes.c_char_p),
        ("protocol_version", ctypes.c_char_p),
        ("formal_semantics_id", ctypes.c_char_p),
        ("build_id", ctypes.c_char_p),
        ("schema_set_id", ctypes.c_char_p),
        ("runtime_profile", ctypes.c_char_p),
    ]


class _ChainContext(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
        ("expected_formal_semantics_id", _BytesView),
        ("expected_native_build_id", _BytesView),
        ("expected_execution_plan_id", _BytesView),
        ("expected_certified_round_policy_id", _BytesView),
        ("expected_parent_checkpoint_id", _BytesView),
        ("expected_final_checkpoint_id", _BytesView),
        ("expected_runtime_state_id", _BytesView),
        ("expected_effect_set_id", _BytesView),
        ("expected_runtime_wal_sha256", _BytesView),
        ("expected_checkpoint_wal_sha256", _BytesView),
    ]


_NATIVE_RECEIPT_FIELDS: Final = frozenset(
    {
        "aggregate_root_qc_id",
        "apply_qc_id",
        "certificate_bundle_id",
        "certified_round_policy_id",
        "checkpoint_wal_sha256",
        "effect_set_id",
        "execution_plan_id",
        "final_checkpoint_id",
        "formal_semantics_id",
        "input_set_certificate_id",
        "native_build_id",
        "native_chain_verifier_id",
        "runtime_state_id",
        "runtime_wal_sha256",
        "schema_version",
        "status",
        "type_name",
    }
)
_NATIVE_BUNDLE_DOMAIN: Final = b"deltareduce.010.native-chain-admission-bundle.v1\0"


@dataclass(frozen=True, slots=True)
class NativeChainAdmissionReceipt:
    canonical_bytes: bytes
    value: dict[str, Any]

    def __post_init__(self) -> None:
        _require(
            canonical_json_bytes(self.value) == self.canonical_bytes
            and set(self.value) == _NATIVE_RECEIPT_FIELDS
            and self.value.get("formal_semantics_id") == FORMAL_SEMANTICS_ID
            and self.value.get("schema_version") == "1.0.0"
            and self.value.get("status") == "ACCEPT"
            and self.value.get("type_name") == "CAMPAIGN02_NATIVE_CHAIN_ADMISSION_RECEIPT",
            "FEATURE008_NATIVE_RECEIPT_INVALID",
        )

    @property
    def content_id(self) -> str:
        return sha256_content_id(self.canonical_bytes)


class NativeChainAdmissionVerifier(Protocol):
    @property
    def native_build_id(self) -> str: ...

    def verify(
        self,
        plan: Any,
        result: Any,
        canonical_bundle: bytes,
    ) -> NativeChainAdmissionReceipt: ...


class CtypesFeature008NativeChainVerifier:
    """Invoke the authoritative C++ ChainVerifier through the full-bundle C ABI."""

    def __init__(self, native_library: Path) -> None:
        try:
            library = ctypes.CDLL(str(native_library.resolve()))
        except OSError as exc:
            raise _fail("FEATURE008_NATIVE_LIBRARY_LOAD_FAILED") from exc
        descriptor_function = library.delta_runtime_descriptor
        descriptor_function.argtypes = [ctypes.c_uint32, ctypes.POINTER(_RuntimeDescriptor)]
        descriptor_function.restype = ctypes.c_int
        descriptor = _RuntimeDescriptor()
        status = descriptor_function(ctypes.sizeof(_RuntimeDescriptor), ctypes.byref(descriptor))
        _require(status == 0, "FEATURE008_NATIVE_DESCRIPTOR_FAILED")
        _require(
            ctypes.sizeof(_ChainContext) == 168,
            "FEATURE008_NATIVE_CHAIN_ABI_LAYOUT_INVALID",
        )
        formal_id = (descriptor.formal_semantics_id or b"").decode("ascii")
        native_build_id = (descriptor.build_id or b"").decode("ascii")
        _require(
            formal_id == FORMAL_SEMANTICS_ID and _CONTENT_ID.fullmatch(native_build_id) is not None,
            "FEATURE008_NATIVE_DESCRIPTOR_INCOMPATIBLE",
        )
        function = library.delta_certificate_chain_verify_copy
        function.argtypes = [
            ctypes.POINTER(_ChainContext),
            _BytesView,
            ctypes.POINTER(_OutputBuffer),
        ]
        function.restype = ctypes.c_int
        self._library = library
        self._verify = function
        self._native_build_id = native_build_id

    @property
    def native_build_id(self) -> str:
        return self._native_build_id

    @staticmethod
    def _view(value: bytes) -> tuple[_BytesView, Any]:
        buffer = (ctypes.c_uint8 * len(value)).from_buffer_copy(value)
        return _BytesView(ctypes.cast(buffer, ctypes.POINTER(ctypes.c_uint8)), len(value)), buffer

    def verify(
        self,
        plan: Any,
        result: Any,
        canonical_bundle: bytes,
    ) -> NativeChainAdmissionReceipt:
        policy = plan.certified_round_policy
        _require(policy is not None, "FEATURE008_PLAN_POLICY_MISSING")
        return self.verify_canonical_bundle(
            canonical_bundle,
            execution_plan_id=plan.content_id,
            certified_round_policy_id=policy.content_id,
            parent_checkpoint_id=plan.parent_checkpoint_id,
            final_checkpoint_id=result.final_checkpoint_id,
            runtime_state_id=result.runtime_state_id,
            effect_set_id=result.effect_set_id,
            runtime_wal_sha256=result.runtime_wal_sha256,
            checkpoint_wal_sha256=result.checkpoint_wal_sha256,
        )

    def verify_canonical_bundle(
        self,
        canonical_bundle: bytes,
        *,
        execution_plan_id: str,
        certified_round_policy_id: str,
        parent_checkpoint_id: str,
        final_checkpoint_id: str,
        runtime_state_id: str,
        effect_set_id: str,
        runtime_wal_sha256: str,
        checkpoint_wal_sha256: str,
    ) -> NativeChainAdmissionReceipt:
        """Verify a corpus bundle with explicit run-context bindings."""

        values = (
            FORMAL_SEMANTICS_ID,
            self.native_build_id,
            execution_plan_id,
            certified_round_policy_id,
            parent_checkpoint_id,
            final_checkpoint_id,
            runtime_state_id,
            effect_set_id,
            runtime_wal_sha256,
            checkpoint_wal_sha256,
        )
        views_and_buffers = [self._view(item.encode("ascii")) for item in values]
        context = _ChainContext(
            ctypes.sizeof(_ChainContext),
            0,
            *(item[0] for item in views_and_buffers),
        )
        payload_view, payload_buffer = self._view(canonical_bundle)
        output = _OutputBuffer()
        first = self._verify(ctypes.byref(context), payload_view, ctypes.byref(output))
        if first == 13:
            _require(
                output.required == 0 and output.written == 0,
                "FEATURE008_NATIVE_REJECTION_EXPOSED_OUTPUT",
            )
            raise _fail("FEATURE008_NATIVE_CHAIN_REJECTED")
        _require(first == 7 and 0 < output.required <= 4096, "FEATURE008_NATIVE_SIZING_FAILED")
        destination = (ctypes.c_uint8 * output.required)()
        output.data = ctypes.cast(destination, ctypes.POINTER(ctypes.c_uint8))
        output.capacity = output.required
        output.written = 0
        second = self._verify(ctypes.byref(context), payload_view, ctypes.byref(output))
        _require(
            second == 0 and output.written == output.required,
            "FEATURE008_NATIVE_CHAIN_REJECTED",
        )
        try:
            receipt = json.loads(bytes(destination))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _fail("FEATURE008_NATIVE_RECEIPT_INVALID") from exc
        _require(
            isinstance(receipt, dict),
            "FEATURE008_NATIVE_RECEIPT_INVALID",
        )
        # Keep all caller-owned views live through both downcalls.
        _ = views_and_buffers, payload_buffer, self._library
        return NativeChainAdmissionReceipt(bytes(destination), receipt)


@dataclass(frozen=True, slots=True)
class Feature008AdmissionReceipt:
    round_id: str
    input_set_certificate_id: str
    aggregate_root_qc_id: str
    apply_qc_id: str
    final_checkpoint_id: str
    canonical_ticket_ids: tuple[str, ...]
    canonical_contribution_ids: tuple[str, ...]
    native_receipt: NativeChainAdmissionReceipt


def _context(value: dict[str, Any]) -> tuple[object, ...]:
    return tuple(value.get(name) for name in _CONTEXT_FIELDS)


def _signers(value: dict[str, Any], policy: Any) -> None:
    signers = _sequence(value.get("signer_ids"), "FEATURE008_SIGNER_SET_INVALID")
    _require(
        value.get("quorum_threshold") == policy.quorum_threshold
        and len(signers) >= policy.quorum_threshold
        and signers == sorted(set(signers))
        and set(signers).issubset(set(policy.validator_ids)),
        "FEATURE008_QUORUM_INVALID",
    )


def _merkle_root(leaves: list[Any]) -> str:
    level: list[str] = []
    for raw_leaf in leaves:
        leaf = _mapping(raw_leaf, "FEATURE008_ROOT_LEAF_INVALID")
        payload = canonical_json_bytes(
            {
                "domain_id": leaf.get("domain_id"),
                "parameter_shard_qc_id": leaf.get("parameter_shard_qc_id"),
                "shard_id": leaf.get("shard_id"),
            }
        )
        level.append(sha256_content_id(b"deltareduce.008.aggregate-leaf.v1\0" + payload))
    _require(bool(level), "FEATURE008_ROOT_COVERAGE_INCOMPLETE")
    while len(level) > 1:
        parent: list[str] = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                parent.append(level[index])
                continue
            pair = bytes.fromhex(level[index][7:]) + bytes.fromhex(level[index + 1][7:])
            parent.append(sha256_content_id(b"deltareduce.008.aggregate-node.v1\0" + pair))
        level = parent
    return level[0]


def _runtime_document(
    artifacts: tuple[Any, ...], content_id: str, type_name: str
) -> dict[str, Any]:
    matches = [item for item in artifacts if item.content_id == content_id]
    _require(len(matches) == 1, "FEATURE008_RUNTIME_ARTIFACT_MISSING")
    try:
        value = json.loads(matches[0].data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail("FEATURE008_RUNTIME_ARTIFACT_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise _fail("FEATURE008_RUNTIME_ARTIFACT_INVALID")
    _require(
        canonical_json_bytes(value) == matches[0].data
        and value.get("type_name") == type_name
        and value.get("schema_version") == "1.0.0",
        "FEATURE008_RUNTIME_ARTIFACT_INVALID",
    )
    return value


def canonical_native_chain_bundle(
    plan: Any,
    contributions: tuple[Any, ...],
    result: Any,
) -> bytes:
    """Build the only canonical input accepted by the native full-chain ABI."""

    policy = plan.certified_round_policy
    _require(policy is not None, "FEATURE008_PLAN_POLICY_MISSING")
    by_ticket = {item.ticket_id: item for item in contributions}
    ordered = tuple(item.ticket_id for item in plan.tickets)
    _require(
        len(by_ticket) == len(contributions) and set(by_ticket) == set(ordered),
        "FEATURE008_CONTRIBUTION_SET_MISMATCH",
    )
    bundle: Feature008CertificateBundle = result.certificate_bundle
    document = {
        "aggregate_root_qc": bundle.aggregate_root.value,
        "aggregation_plan_certificate": bundle.aggregation_plan.value,
        "apply_arithmetic_profile": bundle.apply_profile.value,
        "apply_candidate": bundle.apply_candidate.value,
        "apply_qc": bundle.apply_qc.value,
        "checkpoint_wal_sha256": result.checkpoint_wal_sha256,
        "current_pointer_command": bundle.current_pointer_command.value,
        "effect_set_id": result.effect_set_id,
        "eligibility_certificate": bundle.eligibility.value,
        "execution_plan_id": plan.content_id,
        "expected_input_tuples": [
            {
                "availability_certificate_id": by_ticket[ticket_id].availability_certificate_id,
                "commitment_id": by_ticket[ticket_id].commitment_id,
                "domain_id": by_ticket[ticket_id].domain_id,
                "ticket_id": ticket_id,
            }
            for ticket_id in ordered
        ],
        "final_checkpoint_id": result.final_checkpoint_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "input_set_certificate": bundle.input_set.value,
        "norm_evidence": bundle.norm_evidence.value,
        "ordered_contributions": [
            {
                "contribution_id": by_ticket[ticket_id].contribution_id,
                "ticket_id": ticket_id,
            }
            for ticket_id in ordered
        ],
        "parameter_shard_qcs": [item.value for item in bundle.parameter_shards],
        "parent_checkpoint_id": plan.parent_checkpoint_id,
        "policy": policy.document,
        "runtime_state_id": result.runtime_state_id,
        "runtime_wal_sha256": result.runtime_wal_sha256,
        "schema_version": "1.0.0",
        "seed_transcript": bundle.seed_transcript.value,
        "terminal_outcome": result.terminal_outcome,
        "type_name": "CAMPAIGN02_NATIVE_CHAIN_ADMISSION_BUNDLE",
    }
    return canonical_json_bytes(document)


class Feature008ChainVerifier:
    """Feature 010 admission adapter for the accepted Feature 008 verifier contract."""

    def __init__(self, native_verifier: NativeChainAdmissionVerifier | None = None) -> None:
        self._native_verifier = native_verifier

    def verify(
        self,
        plan: Any,
        contributions: tuple[Any, ...],
        result: Any,
        *,
        require_native: bool,
    ) -> Feature008AdmissionReceipt:
        policy = plan.certified_round_policy
        _require(policy is not None, "FEATURE008_PLAN_POLICY_MISSING")
        _require(
            result.round_id == plan.round_id
            and result.parent_checkpoint_id == plan.parent_checkpoint_id,
            "FEATURE008_ROUND_PARENT_MISMATCH",
        )
        bundle: Feature008CertificateBundle = result.certificate_bundle
        native_verifier = self._native_verifier
        _require(
            native_verifier is not None,
            (
                "FEATURE008_NATIVE_VERIFIER_REQUIRED"
                if require_native
                else "FEATURE008_NATIVE_RECEIPT_REQUIRED"
            ),
        )
        assert native_verifier is not None

        expected_context = (
            policy.arithmetic_profile_id,
            policy.height,
            policy.parameter_schema_id,
            policy.round_config_id,
            policy.round_id,
            policy.validator_epoch_id,
            policy.view,
        )
        contextual = (
            bundle.input_set,
            bundle.seed_transcript,
            bundle.norm_evidence,
            bundle.eligibility,
            bundle.aggregation_plan,
            *bundle.parameter_shards,
            bundle.aggregate_root,
            bundle.apply_candidate,
            bundle.apply_qc,
            bundle.current_pointer_command,
        )
        _require(
            all(_context(item.value) == expected_context for item in contextual),
            "FEATURE008_CONTEXT_MISMATCH",
        )
        for artifact in (
            bundle.input_set,
            bundle.eligibility,
            bundle.aggregation_plan,
            *bundle.parameter_shards,
            bundle.aggregate_root,
            bundle.apply_qc,
        ):
            _signers(artifact.value, policy)

        plan_ticket_ids = tuple(item.ticket_id for item in plan.tickets)
        by_ticket = {item.ticket_id: item for item in contributions}
        _require(
            len(by_ticket) == len(contributions) and set(by_ticket) == set(plan_ticket_ids),
            "FEATURE008_CONTRIBUTION_SET_MISMATCH",
        )
        contribution_ids = tuple(
            by_ticket[ticket_id].contribution_id for ticket_id in plan_ticket_ids
        )
        _require(
            len(set(contribution_ids)) == len(contribution_ids),
            "FEATURE008_CONTRIBUTION_DUPLICATE",
        )
        declared_pairs = tuple(
            zip(
                result.ordered_ticket_ids,
                result.ordered_contribution_ids,
                strict=True,
            )
        )
        expected_pairs = tuple(zip(plan_ticket_ids, contribution_ids, strict=True))
        _require(
            len(declared_pairs) == len(expected_pairs)
            and len(set(declared_pairs)) == len(declared_pairs)
            and set(declared_pairs) == set(expected_pairs),
            "FEATURE008_ORDERED_CONTRIBUTION_SET_MISMATCH",
        )

        isc = bundle.input_set.value
        tuples = [
            _mapping(item, "FEATURE008_ISC_TUPLE_INVALID")
            for item in _sequence(isc.get("tuples"), "FEATURE008_ISC_TUPLE_SET_INVALID")
        ]
        actual_tuples = {
            (
                item.get("ticket_id"),
                item.get("domain_id"),
                item.get("commitment_id"),
                item.get("availability_certificate_id"),
            )
            for item in tuples
        }
        expected_tuples = {
            (
                item.ticket_id,
                item.domain_id,
                item.commitment_id,
                item.availability_certificate_id,
            )
            for item in contributions
        }
        _require(
            len(actual_tuples) == len(tuples) and actual_tuples == expected_tuples,
            "FEATURE008_ISC_MEMBERSHIP_MISMATCH",
        )
        _require(
            result.input_set_certificate_id == bundle.input_set.content_id,
            "FEATURE008_ISC_ID_MISMATCH",
        )

        seed = bundle.seed_transcript.value
        norms = bundle.norm_evidence.value
        eligibility = bundle.eligibility.value
        _require(
            result.seed_transcript_id == bundle.seed_transcript.content_id
            and seed.get("input_set_certificate_id") == bundle.input_set.content_id
            and norms.get("input_set_certificate_id") == bundle.input_set.content_id,
            "FEATURE008_SEED_OR_NORM_PARENT_MISMATCH",
        )
        entries = [
            _mapping(item, "FEATURE008_EC_ENTRY_INVALID")
            for item in _sequence(eligibility.get("entries"), "FEATURE008_EC_ENTRY_SET_INVALID")
        ]
        isc_order = [(item.get("ticket_id"), item.get("domain_id")) for item in tuples]
        ec_order = [(item.get("ticket_id"), item.get("domain_id")) for item in entries]
        _require(
            result.eligibility_certificate_id == bundle.eligibility.content_id
            and eligibility.get("input_set_certificate_id") == bundle.input_set.content_id
            and eligibility.get("norm_evidence_id") == bundle.norm_evidence.content_id
            and ec_order == isc_order,
            "FEATURE008_ELIGIBILITY_MEMBERSHIP_MISMATCH",
        )
        accepted = [str(item["ticket_id"]) for item in entries if item.get("accepted") is True]

        aggregation_plan = bundle.aggregation_plan.value
        assignments = [
            str(_mapping(item, "FEATURE008_APC_ASSIGNMENT_INVALID").get("ticket_id"))
            for item in _sequence(
                aggregation_plan.get("bucket_assignments"),
                "FEATURE008_APC_ASSIGNMENT_SET_INVALID",
            )
        ]
        weights = [
            str(_mapping(item, "FEATURE008_APC_WEIGHT_INVALID").get("ticket_id"))
            for item in _sequence(
                aggregation_plan.get("weights"), "FEATURE008_APC_WEIGHT_SET_INVALID"
            )
        ]
        _require(
            result.aggregation_plan_certificate_id == bundle.aggregation_plan.content_id
            and aggregation_plan.get("input_set_certificate_id") == bundle.input_set.content_id
            and aggregation_plan.get("eligibility_certificate_id") == bundle.eligibility.content_id
            and aggregation_plan.get("seed_transcript_id") == bundle.seed_transcript.content_id
            and aggregation_plan.get("accumulator_proof_id") == policy.accumulator_proof_id
            and assignments == accepted
            and weights == accepted
            and len(assignments) == len(set(assignments))
            and len(weights) == len(set(weights)),
            "FEATURE008_APC_PARENT_OR_MEMBERSHIP_MISMATCH",
        )

        shard_ids = tuple(item.content_id for item in bundle.parameter_shards)
        _require(
            result.parameter_shard_qc_ids == shard_ids,
            "FEATURE008_PARAMETER_SHARD_ID_SET_MISMATCH",
        )
        required_keys = tuple((item.domain_id, item.shard_id) for item in policy.required_shards)
        shard_keys: list[tuple[object, object]] = []
        for shard in bundle.parameter_shards:
            value = shard.value
            _require(
                value.get("input_set_certificate_id") == bundle.input_set.content_id
                and value.get("eligibility_certificate_id") == bundle.eligibility.content_id
                and value.get("aggregation_plan_certificate_id")
                == bundle.aggregation_plan.content_id,
                "FEATURE008_PARAMETER_SHARD_PARENT_MISMATCH",
            )
            shard_keys.append((value.get("domain_id"), value.get("shard_id")))
        _require(
            tuple(shard_keys) == required_keys and len(set(shard_keys)) == len(shard_keys),
            "FEATURE008_PARAMETER_SHARD_COVERAGE_INCOMPLETE",
        )

        root = bundle.aggregate_root.value
        leaves = [
            _mapping(item, "FEATURE008_ROOT_LEAF_INVALID")
            for item in _sequence(root.get("leaves"), "FEATURE008_ROOT_LEAF_SET_INVALID")
        ]
        declared_keys = tuple(
            (item.get("domain_id"), item.get("shard_id"))
            for item in (
                _mapping(raw, "FEATURE008_ROOT_REQUIRED_KEY_INVALID")
                for raw in _sequence(
                    root.get("required_keys"), "FEATURE008_ROOT_REQUIRED_SET_INVALID"
                )
            )
        )
        leaf_rows = tuple(
            (item.get("domain_id"), item.get("shard_id"), item.get("parameter_shard_qc_id"))
            for item in leaves
        )
        expected_leaves = tuple(
            (domain_id, shard_id, shard_id_value)
            for (domain_id, shard_id), shard_id_value in zip(required_keys, shard_ids, strict=True)
        )
        _require(
            result.aggregate_root_qc_id == bundle.aggregate_root.content_id
            and root.get("input_set_certificate_id") == bundle.input_set.content_id
            and root.get("eligibility_certificate_id") == bundle.eligibility.content_id
            and root.get("aggregation_plan_certificate_id") == bundle.aggregation_plan.content_id
            and declared_keys == required_keys
            and leaf_rows == expected_leaves
            and root.get("merkle_root") == _merkle_root(leaves),
            "FEATURE008_AGGREGATE_ROOT_COVERAGE_INVALID",
        )

        profile = bundle.apply_profile.value
        candidate = bundle.apply_candidate.value
        apply_qc = bundle.apply_qc.value
        pointer = bundle.current_pointer_command.value
        _require(
            bundle.apply_profile.content_id == policy.apply_arithmetic_profile_id
            and profile.get("accumulator_proof_id") == policy.accumulator_proof_id,
            "FEATURE008_APPLY_PROFILE_MISMATCH",
        )
        _require(
            candidate.get("aggregate_root_qc_id") == bundle.aggregate_root.content_id
            and candidate.get("apply_arithmetic_profile_id") == bundle.apply_profile.content_id
            and candidate.get("parent_checkpoint_id") == plan.parent_checkpoint_id,
            "FEATURE008_APPLY_CANDIDATE_PARENT_MISMATCH",
        )
        _require(
            result.apply_qc_id == bundle.apply_qc.content_id
            and apply_qc.get("aggregate_root_qc_id") == bundle.aggregate_root.content_id
            and apply_qc.get("apply_arithmetic_profile_id") == bundle.apply_profile.content_id
            and apply_qc.get("apply_candidate_id") == bundle.apply_candidate.content_id
            and apply_qc.get("parent_checkpoint_id") == plan.parent_checkpoint_id
            and apply_qc.get("next_model_hash") == candidate.get("next_model_hash")
            and apply_qc.get("next_optimizer_hash") == candidate.get("next_optimizer_hash")
            and result.final_checkpoint_id == apply_qc.get("next_model_hash"),
            "FEATURE008_APPLY_QC_BINDING_INVALID",
        )
        _require(
            pointer.get("apply_qc_id") == bundle.apply_qc.content_id
            and pointer.get("expected_parent_checkpoint_id") == plan.parent_checkpoint_id
            and pointer.get("next_checkpoint_id") == result.final_checkpoint_id
            and pointer.get("next_optimizer_hash") == apply_qc.get("next_optimizer_hash"),
            "FEATURE008_CURRENT_POINTER_BINDING_INVALID",
        )

        runtime_state = _runtime_document(
            result.artifacts, result.runtime_state_id, "CERTIFIED_RUNTIME_STATE"
        )
        effect_set = _runtime_document(
            result.artifacts, result.effect_set_id, "CERTIFIED_EFFECT_SET"
        )
        receipt = _runtime_document(
            result.artifacts, result.runtime_receipt_id, "CERTIFIED_FINALIZATION_RECEIPT"
        )
        common = {
            "apply_qc_id": result.apply_qc_id,
            "execution_plan_id": plan.content_id,
            "final_checkpoint_id": result.final_checkpoint_id,
            "parent_checkpoint_id": plan.parent_checkpoint_id,
            "round_id": result.round_id,
        }
        _require(
            all(
                document.get(key) == value
                for document in (runtime_state, effect_set)
                for key, value in common.items()
            ),
            "FEATURE008_RUNTIME_CONTEXT_MISMATCH",
        )
        _require(
            all(receipt.get(key) == value for key, value in common.items())
            and receipt.get("runtime_state_id") == result.runtime_state_id
            and receipt.get("effect_set_id") == result.effect_set_id
            and receipt.get("runtime_wal_sha256") == result.runtime_wal_sha256
            and receipt.get("checkpoint_wal_sha256") == result.checkpoint_wal_sha256,
            "FEATURE008_RUNTIME_RECEIPT_MISMATCH",
        )
        for expected_hash in (result.runtime_wal_sha256, result.checkpoint_wal_sha256):
            _require(
                _SHA256_HEX.fullmatch(expected_hash) is not None
                and sum(
                    hashlib.sha256(item.data).hexdigest() == expected_hash
                    for item in result.artifacts
                )
                == 1,
                "FEATURE008_WAL_ARTIFACT_MISMATCH",
            )
        _require(result.terminal_outcome == "APPLIED", "FEATURE008_TERMINAL_OUTCOME_INVALID")
        native_bundle = canonical_native_chain_bundle(plan, contributions, result)
        native_receipt = native_verifier.verify(plan, result, native_bundle)
        expected_bundle_id = sha256_content_id(_NATIVE_BUNDLE_DOMAIN + native_bundle)
        receipt = native_receipt.value
        _require(
            receipt.get("native_build_id") == native_verifier.native_build_id
            and receipt.get("certificate_bundle_id") == expected_bundle_id
            and receipt.get("certified_round_policy_id") == policy.content_id
            and receipt.get("execution_plan_id") == plan.content_id
            and receipt.get("input_set_certificate_id") == bundle.input_set.content_id
            and receipt.get("aggregate_root_qc_id") == bundle.aggregate_root.content_id
            and receipt.get("apply_qc_id") == bundle.apply_qc.content_id
            and receipt.get("final_checkpoint_id") == result.final_checkpoint_id
            and receipt.get("runtime_state_id") == result.runtime_state_id
            and receipt.get("effect_set_id") == result.effect_set_id
            and receipt.get("runtime_wal_sha256") == result.runtime_wal_sha256
            and receipt.get("checkpoint_wal_sha256") == result.checkpoint_wal_sha256
            and _CONTENT_ID.fullmatch(str(receipt.get("native_chain_verifier_id"))) is not None,
            "FEATURE008_NATIVE_RECEIPT_BINDING_MISMATCH",
        )
        return Feature008AdmissionReceipt(
            round_id=result.round_id,
            input_set_certificate_id=bundle.input_set.content_id,
            aggregate_root_qc_id=bundle.aggregate_root.content_id,
            apply_qc_id=bundle.apply_qc.content_id,
            final_checkpoint_id=result.final_checkpoint_id,
            canonical_ticket_ids=plan_ticket_ids,
            canonical_contribution_ids=contribution_ids,
            native_receipt=native_receipt,
        )
