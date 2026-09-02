"""Campaign 02 token accounting and exact execution-plan contracts.

This module deliberately does not construct a primary BenchmarkDefinition.  It
defines the source-sealed contracts that a later, separately attested definition
may reference.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Protocol

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.stage_authorization import (
    CAMPAIGN02_STAGE_GATE_ANALYZER_ID,
    StageAuthorizationProof,
    StageGateReceipt,
    VerifiedStageAuthorization,
    verify_stage_authorization_proof,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")
_WORKLOAD_FIELDS: Final = {
    "campaign_id",
    "domain_ticket_counts",
    "execution_class",
    "formal_semantics_id",
    "optimizer_steps_per_ticket",
    "schema_version",
    "ticket_count",
    "tokens_per_optimizer_step",
    "tokens_per_ticket",
    "total_tokens_per_arm_run",
    "type_name",
}
_DOMAIN_MANIFEST_FIELDS: Final = {
    "campaign_id",
    "domains",
    "formal_semantics_id",
    "schema_version",
    "type_name",
}
_DOMAIN_ENTRY_FIELDS: Final = {
    "dataset_id",
    "denominator",
    "domain_id",
    "numerator",
    "ticket_count",
}
_TICKET_PLAN_FIELDS: Final = {
    "campaign_id",
    "domain_manifest_id",
    "formal_semantics_id",
    "schema_version",
    "tickets",
    "type_name",
    "workload_contract_id",
}
CAMPAIGN02_GATE_STAGES: Final = (
    "STAGE_A_EXACTNESS",
    "STAGE_B_SCIENTIFIC",
    "STAGE_C_EMULATED_WAN",
)
CAMPAIGN02_STAGE_TASK_IDS: Final = {
    "STAGE_A_EXACTNESS": ("HR010-006", "HR010-010", "HR010-011", "T028", "T029"),
    "STAGE_B_SCIENTIFIC": ("HR010-016", "T035", "T036", "T039"),
    "STAGE_C_EMULATED_WAN": ("T040", "T041", "T042", "T043", "T044"),
}


class Campaign02ContractError(ValueError):
    """Stable fail-closed Campaign 02 contract rejection."""


def _fail(code: str) -> Campaign02ContractError:
    return Campaign02ContractError(code)


def _positive_integer(value: object, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise _fail(code)
    return value


def _string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise _fail(code)
    return value


def _content_id(value: object, code: str) -> str:
    result = _string(value, code)
    if _CONTENT_ID.fullmatch(result) is None:
        raise _fail(code)
    return result


@dataclass(frozen=True, slots=True)
class DomainTicketCount:
    domain_id: str
    ticket_count: int

    @classmethod
    def from_dict(cls, value: object) -> DomainTicketCount:
        if not isinstance(value, dict) or set(value) != {"domain_id", "ticket_count"}:
            raise _fail("CAMPAIGN02_DOMAIN_TICKET_FIELDS_INVALID")
        return cls(
            _string(value["domain_id"], "CAMPAIGN02_DOMAIN_ID_INVALID"),
            _positive_integer(value["ticket_count"], "CAMPAIGN02_DOMAIN_TICKET_COUNT_INVALID"),
        )


@dataclass(frozen=True, slots=True)
class WorkloadContract:
    campaign_id: str
    tokens_per_optimizer_step: int
    optimizer_steps_per_ticket: int
    tokens_per_ticket: int
    ticket_count: int
    total_tokens_per_arm_run: int
    domain_ticket_counts: tuple[DomainTicketCount, ...]
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, value: object) -> WorkloadContract:
        if not isinstance(value, dict) or set(value) != _WORKLOAD_FIELDS:
            raise _fail("CAMPAIGN02_WORKLOAD_FIELDS_INVALID")
        if (
            value.get("type_name") != "CAMPAIGN_WORKLOAD"
            or value.get("schema_version") != "2.0.0"
            or value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
            or value.get("campaign_id") != "campaign-02"
            or value.get("execution_class") != "DESIGN_ONLY_NO_PRIMARY_EXECUTION"
        ):
            raise _fail("CAMPAIGN02_WORKLOAD_HEADER_INVALID")
        try:
            canonical_json_bytes(value)
        except TypeError as exc:
            raise _fail("CAMPAIGN02_WORKLOAD_NOT_CANONICAL") from exc
        tokens_per_step = _positive_integer(
            value["tokens_per_optimizer_step"], "CAMPAIGN02_TOKENS_PER_STEP_INVALID"
        )
        steps_per_ticket = _positive_integer(
            value["optimizer_steps_per_ticket"], "CAMPAIGN02_STEPS_PER_TICKET_INVALID"
        )
        tokens_per_ticket = _positive_integer(
            value["tokens_per_ticket"], "CAMPAIGN02_TOKENS_PER_TICKET_INVALID"
        )
        ticket_count = _positive_integer(value["ticket_count"], "CAMPAIGN02_TICKET_COUNT_INVALID")
        total_tokens = _positive_integer(
            value["total_tokens_per_arm_run"], "CAMPAIGN02_TOTAL_TOKENS_INVALID"
        )
        domains_raw = value["domain_ticket_counts"]
        if not isinstance(domains_raw, list) or not domains_raw:
            raise _fail("CAMPAIGN02_DOMAIN_TICKETS_MISSING")
        domains = tuple(DomainTicketCount.from_dict(item) for item in domains_raw)
        if len({item.domain_id for item in domains}) != len(domains):
            raise _fail("CAMPAIGN02_DOMAIN_TICKET_DUPLICATE")
        if tokens_per_ticket != tokens_per_step * steps_per_ticket:
            raise _fail("CAMPAIGN02_PER_TICKET_TOKEN_RECONCILIATION")
        if sum(item.ticket_count for item in domains) != ticket_count:
            raise _fail("CAMPAIGN02_DOMAIN_TICKET_RECONCILIATION")
        if total_tokens != sum(item.ticket_count * tokens_per_ticket for item in domains):
            raise _fail("CAMPAIGN02_ARM_TOKEN_RECONCILIATION")
        return cls(
            campaign_id="campaign-02",
            tokens_per_optimizer_step=tokens_per_step,
            optimizer_steps_per_ticket=steps_per_ticket,
            tokens_per_ticket=tokens_per_ticket,
            ticket_count=ticket_count,
            total_tokens_per_arm_run=total_tokens,
            domain_ticket_counts=domains,
            raw=dict(value),
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.raw)

    @property
    def content_id(self) -> str:
        return sha256_content_id(b"deltareduce.010.campaign-workload.v2\0" + self.canonical_bytes)


def load_workload_contract(path: Path) -> WorkloadContract:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail("CAMPAIGN02_WORKLOAD_JSON_INVALID") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) + b"\n" != raw:
        raise _fail("CAMPAIGN02_WORKLOAD_CANONICAL_BYTES_INVALID")
    return WorkloadContract.from_dict(value)


@dataclass(frozen=True, slots=True)
class CampaignDomain:
    domain_id: str
    dataset_id: str
    ticket_count: int
    numerator: int
    denominator: int

    @classmethod
    def from_dict(cls, value: object) -> CampaignDomain:
        if not isinstance(value, dict) or set(value) != _DOMAIN_ENTRY_FIELDS:
            raise _fail("CAMPAIGN02_DOMAIN_MANIFEST_ENTRY_FIELDS_INVALID")
        numerator = _positive_integer(
            value["numerator"], "CAMPAIGN02_DOMAIN_MIXTURE_NUMERATOR_INVALID"
        )
        denominator = _positive_integer(
            value["denominator"], "CAMPAIGN02_DOMAIN_MIXTURE_DENOMINATOR_INVALID"
        )
        if numerator != denominator:
            raise _fail("CAMPAIGN02_DOMAIN_MIXTURE_NOT_NORMALIZED")
        return cls(
            domain_id=_string(value["domain_id"], "CAMPAIGN02_DOMAIN_ID_INVALID"),
            dataset_id=_content_id(value["dataset_id"], "CAMPAIGN02_DOMAIN_DATASET_ID_INVALID"),
            ticket_count=_positive_integer(
                value["ticket_count"], "CAMPAIGN02_DOMAIN_TICKET_COUNT_INVALID"
            ),
            numerator=numerator,
            denominator=denominator,
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "denominator": self.denominator,
            "domain_id": self.domain_id,
            "numerator": self.numerator,
            "ticket_count": self.ticket_count,
        }


@dataclass(frozen=True, slots=True)
class CampaignDomainManifest:
    campaign_id: str
    domains: tuple[CampaignDomain, ...]
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, value: object) -> CampaignDomainManifest:
        if not isinstance(value, dict) or set(value) != _DOMAIN_MANIFEST_FIELDS:
            raise _fail("CAMPAIGN02_DOMAIN_MANIFEST_FIELDS_INVALID")
        if (
            value.get("type_name") != "CAMPAIGN_DOMAIN_MANIFEST"
            or value.get("schema_version") != "1.0.0"
            or value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
            or value.get("campaign_id") != "campaign-02"
        ):
            raise _fail("CAMPAIGN02_DOMAIN_MANIFEST_HEADER_INVALID")
        domains_raw = value["domains"]
        if not isinstance(domains_raw, list) or not domains_raw:
            raise _fail("CAMPAIGN02_DOMAIN_MANIFEST_EMPTY")
        domains = tuple(CampaignDomain.from_dict(item) for item in domains_raw)
        if tuple(item.domain_id for item in domains) != tuple(
            sorted(item.domain_id for item in domains)
        ) or len({item.domain_id for item in domains}) != len(domains):
            raise _fail("CAMPAIGN02_DOMAIN_MANIFEST_ORDER_INVALID")
        return cls("campaign-02", domains, dict(value))

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.raw)

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign-domain-manifest.v1\0" + self.canonical_bytes
        )


def load_domain_manifest(path: Path) -> CampaignDomainManifest:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail("CAMPAIGN02_DOMAIN_MANIFEST_JSON_INVALID") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) + b"\n" != raw:
        raise _fail("CAMPAIGN02_DOMAIN_MANIFEST_CANONICAL_BYTES_INVALID")
    return CampaignDomainManifest.from_dict(value)


@dataclass(frozen=True, slots=True)
class TicketAllocation:
    ticket_id: str
    domain_id: str
    ordinal: int
    tokens_per_optimizer_step: int
    optimizer_steps: int
    tokens_per_ticket: int

    @property
    def document(self) -> dict[str, object]:
        return {
            "domain_id": self.domain_id,
            "optimizer_steps": self.optimizer_steps,
            "ordinal": self.ordinal,
            "ticket_id": self.ticket_id,
            "tokens_per_optimizer_step": self.tokens_per_optimizer_step,
            "tokens_per_ticket": self.tokens_per_ticket,
        }


@dataclass(frozen=True, order=True, slots=True)
class ParameterShardKey:
    domain_id: str
    shard_id: str

    def __post_init__(self) -> None:
        if not self.domain_id or not self.shard_id:
            raise _fail("CAMPAIGN02_PARAMETER_SHARD_KEY_INVALID")

    @classmethod
    def from_dict(cls, value: object) -> ParameterShardKey:
        if not isinstance(value, dict) or set(value) != {"domain_id", "shard_id"}:
            raise _fail("CAMPAIGN02_PARAMETER_SHARD_KEY_INVALID")
        return cls(
            _string(value["domain_id"], "CAMPAIGN02_PARAMETER_SHARD_KEY_INVALID"),
            _string(value["shard_id"], "CAMPAIGN02_PARAMETER_SHARD_KEY_INVALID"),
        )

    @property
    def document(self) -> dict[str, str]:
        return {"domain_id": self.domain_id, "shard_id": self.shard_id}


@dataclass(frozen=True, slots=True)
class CertifiedRoundPolicy:
    round_id: str
    height: int
    view: int
    round_config_id: str
    validator_epoch_id: str
    parameter_schema_id: str
    arithmetic_profile_id: str
    accumulator_proof_id: str
    apply_arithmetic_profile_id: str
    validator_ids: tuple[str, ...]
    quorum_threshold: int
    required_shards: tuple[ParameterShardKey, ...]

    def __post_init__(self) -> None:
        if not self.round_id or self.height < 1 or self.view < 0:
            raise _fail("CAMPAIGN02_CERTIFIED_ROUND_COORDINATE_INVALID")
        identities = (
            self.round_config_id,
            self.validator_epoch_id,
            self.parameter_schema_id,
            self.arithmetic_profile_id,
            self.accumulator_proof_id,
            self.apply_arithmetic_profile_id,
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in identities):
            raise _fail("CAMPAIGN02_CERTIFIED_ROUND_IDENTITY_INVALID")
        if (
            not self.validator_ids
            or self.validator_ids != tuple(sorted(set(self.validator_ids)))
            or len(self.validator_ids) % 3 != 1
        ):
            raise _fail("CAMPAIGN02_CERTIFIED_VALIDATOR_SET_INVALID")
        fault_tolerance = (len(self.validator_ids) - 1) // 3
        if self.quorum_threshold != 2 * fault_tolerance + 1:
            raise _fail("CAMPAIGN02_CERTIFIED_QUORUM_INVALID")
        if not self.required_shards or self.required_shards != tuple(
            sorted(set(self.required_shards))
        ):
            raise _fail("CAMPAIGN02_REQUIRED_SHARD_MATRIX_INVALID")

    @classmethod
    def from_dict(cls, value: object) -> CertifiedRoundPolicy:
        fields = {
            "accumulator_proof_id",
            "apply_arithmetic_profile_id",
            "arithmetic_profile_id",
            "height",
            "parameter_schema_id",
            "quorum_threshold",
            "required_shards",
            "round_config_id",
            "round_id",
            "validator_epoch_id",
            "validator_ids",
            "view",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_CERTIFIED_ROUND_FIELDS_INVALID")
        validator_ids = value["validator_ids"]
        required_shards = value["required_shards"]
        if (
            not isinstance(validator_ids, list)
            or any(not isinstance(item, str) for item in validator_ids)
            or not isinstance(required_shards, list)
        ):
            raise _fail("CAMPAIGN02_CERTIFIED_ROUND_FIELDS_INVALID")
        height = value["height"]
        view = value["view"]
        quorum_threshold = value["quorum_threshold"]
        if (
            isinstance(height, bool)
            or not isinstance(height, int)
            or height < 1
            or isinstance(view, bool)
            or not isinstance(view, int)
            or view < 0
            or isinstance(quorum_threshold, bool)
            or not isinstance(quorum_threshold, int)
            or quorum_threshold < 1
        ):
            raise _fail("CAMPAIGN02_CERTIFIED_ROUND_COORDINATE_INVALID")
        result = cls(
            round_id=_string(value["round_id"], "CAMPAIGN02_CERTIFIED_ROUND_ID_INVALID"),
            height=height,
            view=view,
            round_config_id=_content_id(
                value["round_config_id"], "CAMPAIGN02_CERTIFIED_ROUND_IDENTITY_INVALID"
            ),
            validator_epoch_id=_content_id(
                value["validator_epoch_id"], "CAMPAIGN02_CERTIFIED_ROUND_IDENTITY_INVALID"
            ),
            parameter_schema_id=_content_id(
                value["parameter_schema_id"], "CAMPAIGN02_CERTIFIED_ROUND_IDENTITY_INVALID"
            ),
            arithmetic_profile_id=_content_id(
                value["arithmetic_profile_id"], "CAMPAIGN02_CERTIFIED_ROUND_IDENTITY_INVALID"
            ),
            accumulator_proof_id=_content_id(
                value["accumulator_proof_id"], "CAMPAIGN02_CERTIFIED_ROUND_IDENTITY_INVALID"
            ),
            apply_arithmetic_profile_id=_content_id(
                value["apply_arithmetic_profile_id"],
                "CAMPAIGN02_CERTIFIED_ROUND_IDENTITY_INVALID",
            ),
            validator_ids=tuple(validator_ids),
            quorum_threshold=quorum_threshold,
            required_shards=tuple(ParameterShardKey.from_dict(item) for item in required_shards),
        )
        if result.document != value:
            raise _fail("CAMPAIGN02_CERTIFIED_ROUND_DOCUMENT_MISMATCH")
        return result

    @property
    def document(self) -> dict[str, object]:
        return {
            "accumulator_proof_id": self.accumulator_proof_id,
            "apply_arithmetic_profile_id": self.apply_arithmetic_profile_id,
            "arithmetic_profile_id": self.arithmetic_profile_id,
            "height": self.height,
            "parameter_schema_id": self.parameter_schema_id,
            "quorum_threshold": self.quorum_threshold,
            "required_shards": [item.document for item in self.required_shards],
            "round_config_id": self.round_config_id,
            "round_id": self.round_id,
            "validator_epoch_id": self.validator_epoch_id,
            "validator_ids": list(self.validator_ids),
            "view": self.view,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.certified-round-policy.v1\0" + canonical_json_bytes(self.document)
        )


def allocate_tickets(workload: WorkloadContract) -> tuple[TicketAllocation, ...]:
    tickets: list[TicketAllocation] = []
    ordinal = 0
    for domain in workload.domain_ticket_counts:
        for domain_ordinal in range(domain.ticket_count):
            ticket_id = sha256_content_id(
                canonical_json_bytes(
                    {
                        "campaign_id": workload.campaign_id,
                        "domain_id": domain.domain_id,
                        "domain_ordinal": domain_ordinal,
                        "workload_id": workload.content_id,
                    }
                )
            )
            tickets.append(
                TicketAllocation(
                    ticket_id=ticket_id,
                    domain_id=domain.domain_id,
                    ordinal=ordinal,
                    tokens_per_optimizer_step=workload.tokens_per_optimizer_step,
                    optimizer_steps=workload.optimizer_steps_per_ticket,
                    tokens_per_ticket=workload.tokens_per_ticket,
                )
            )
            ordinal += 1
    if len(tickets) != workload.ticket_count:
        raise _fail("CAMPAIGN02_TICKET_PLAN_COUNT_MISMATCH")
    if sum(item.tokens_per_ticket for item in tickets) != workload.total_tokens_per_arm_run:
        raise _fail("CAMPAIGN02_TICKET_PLAN_TOKEN_MISMATCH")
    return tuple(tickets)


@dataclass(frozen=True, slots=True)
class CampaignTicketPlan:
    campaign_id: str
    workload_contract_id: str
    domain_manifest_id: str
    tickets: tuple[TicketAllocation, ...]
    raw: dict[str, Any]

    @classmethod
    def from_dict(
        cls,
        value: object,
        workload: WorkloadContract,
        domain_manifest: CampaignDomainManifest,
    ) -> CampaignTicketPlan:
        if not isinstance(value, dict) or set(value) != _TICKET_PLAN_FIELDS:
            raise _fail("CAMPAIGN02_TICKET_PLAN_FIELDS_INVALID")
        if (
            value.get("type_name") != "CAMPAIGN_TICKET_PLAN"
            or value.get("schema_version") != "1.0.0"
            or value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
            or value.get("campaign_id") != "campaign-02"
            or value.get("workload_contract_id") != workload.content_id
            or value.get("domain_manifest_id") != domain_manifest.content_id
        ):
            raise _fail("CAMPAIGN02_TICKET_PLAN_HEADER_INVALID")
        tickets_raw = value["tickets"]
        if not isinstance(tickets_raw, list):
            raise _fail("CAMPAIGN02_TICKET_PLAN_TICKETS_INVALID")
        tickets: list[TicketAllocation] = []
        for item in tickets_raw:
            if not isinstance(item, dict) or set(item) != {
                "domain_id",
                "optimizer_steps",
                "ordinal",
                "ticket_id",
                "tokens_per_optimizer_step",
                "tokens_per_ticket",
            }:
                raise _fail("CAMPAIGN02_TICKET_PLAN_TICKET_FIELDS_INVALID")
            ticket_id = _content_id(item["ticket_id"], "CAMPAIGN02_TICKET_ID_INVALID")
            ordinal = item["ordinal"]
            if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
                raise _fail("CAMPAIGN02_TICKET_ORDINAL_INVALID")
            tickets.append(
                TicketAllocation(
                    ticket_id=ticket_id,
                    domain_id=_string(item["domain_id"], "CAMPAIGN02_DOMAIN_ID_INVALID"),
                    ordinal=ordinal,
                    tokens_per_optimizer_step=_positive_integer(
                        item["tokens_per_optimizer_step"],
                        "CAMPAIGN02_TOKENS_PER_STEP_INVALID",
                    ),
                    optimizer_steps=_positive_integer(
                        item["optimizer_steps"], "CAMPAIGN02_STEPS_PER_TICKET_INVALID"
                    ),
                    tokens_per_ticket=_positive_integer(
                        item["tokens_per_ticket"], "CAMPAIGN02_TOKENS_PER_TICKET_INVALID"
                    ),
                )
            )
        expected = allocate_tickets(workload)
        if tuple(tickets) != expected:
            raise _fail("CAMPAIGN02_TICKET_PLAN_ALLOCATION_MISMATCH")
        manifest_counts = tuple(
            (item.domain_id, item.ticket_count) for item in domain_manifest.domains
        )
        workload_counts = tuple(
            (item.domain_id, item.ticket_count) for item in workload.domain_ticket_counts
        )
        if manifest_counts != workload_counts:
            raise _fail("CAMPAIGN02_DOMAIN_MANIFEST_WORKLOAD_MISMATCH")
        return cls(
            campaign_id="campaign-02",
            workload_contract_id=workload.content_id,
            domain_manifest_id=domain_manifest.content_id,
            tickets=tuple(tickets),
            raw=dict(value),
        )

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.raw)

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign-ticket-plan.v1\0" + self.canonical_bytes
        )


def build_ticket_plan(
    workload: WorkloadContract, domain_manifest: CampaignDomainManifest
) -> CampaignTicketPlan:
    value: dict[str, Any] = {
        "campaign_id": "campaign-02",
        "domain_manifest_id": domain_manifest.content_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "schema_version": "1.0.0",
        "tickets": [item.document for item in allocate_tickets(workload)],
        "type_name": "CAMPAIGN_TICKET_PLAN",
        "workload_contract_id": workload.content_id,
    }
    return CampaignTicketPlan.from_dict(value, workload, domain_manifest)


def load_ticket_plan(
    path: Path, workload: WorkloadContract, domain_manifest: CampaignDomainManifest
) -> CampaignTicketPlan:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail("CAMPAIGN02_TICKET_PLAN_JSON_INVALID") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) + b"\n" != raw:
        raise _fail("CAMPAIGN02_TICKET_PLAN_CANONICAL_BYTES_INVALID")
    return CampaignTicketPlan.from_dict(value, workload, domain_manifest)


@dataclass(frozen=True, slots=True)
class CampaignExecutionPlan:
    execution_class: str
    result_class: str
    campaign_id: str
    benchmark_definition_id: str
    definition_attestation_id: str
    execution_authorization_id: str | None
    arm_id: str
    round_id: str
    seed: int
    repetition: int
    source_commit: str
    source_tree: str
    environment_id: str
    image_id: str
    hardware_id: str
    runner_id: str
    evaluation_runner_id: str
    writer_id: str
    workload_id: str
    tokens_per_optimizer_step: int
    optimizer_steps_per_ticket: int
    tokens_per_ticket: int
    ticket_count: int
    total_tokens_per_arm_run: int
    model_id: str
    parent_checkpoint_id: str
    tokenizer_id: str
    dataset_ids: tuple[str, ...]
    evaluation_profile_ids: tuple[str, ...]
    evaluation_implementation_ids: tuple[str, ...]
    tickets: tuple[TicketAllocation, ...]
    certified_round_policy: CertifiedRoundPolicy | None = None
    domain_manifest_id: str | None = None
    ticket_plan_id: str | None = None
    qualified_runtime_lineage_id: str | None = None
    gate_stage: str | None = None

    def __post_init__(self) -> None:
        if self.execution_class not in {"NON_PRIMARY_SMOKE", "PRIMARY_MEASURED"}:
            raise _fail("CAMPAIGN02_EXECUTION_CLASS_INVALID")
        if self.result_class not in {"REFERENCE", "CERTIFIED_DELTAREDUCE"}:
            raise _fail("CAMPAIGN02_RESULT_CLASS_INVALID")
        if (self.result_class == "CERTIFIED_DELTAREDUCE") != (
            self.certified_round_policy is not None
        ):
            raise _fail("CAMPAIGN02_RESULT_CLASS_POLICY_MISMATCH")
        if self.campaign_id != "campaign-02":
            raise _fail("CAMPAIGN02_PLAN_CAMPAIGN_INVALID")
        if not self.round_id or (
            self.certified_round_policy is not None
            and self.certified_round_policy.round_id != self.round_id
        ):
            raise _fail("CAMPAIGN02_PLAN_ROUND_ID_INVALID")
        identities = (
            self.benchmark_definition_id,
            self.definition_attestation_id,
            self.arm_id,
            self.environment_id,
            self.image_id,
            self.hardware_id,
            self.runner_id,
            self.evaluation_runner_id,
            self.writer_id,
            self.workload_id,
            self.model_id,
            self.parent_checkpoint_id,
            self.tokenizer_id,
            *self.dataset_ids,
            *self.evaluation_profile_ids,
            *self.evaluation_implementation_ids,
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in identities):
            raise _fail("CAMPAIGN02_PLAN_IDENTITY_INVALID")
        if self.gate_stage is None:
            if (
                self.execution_authorization_id is None
                or _CONTENT_ID.fullmatch(self.execution_authorization_id) is None
            ):
                raise _fail("CAMPAIGN02_PLAN_IDENTITY_INVALID")
        elif (
            self.gate_stage not in CAMPAIGN02_GATE_STAGES
            or self.execution_class != "PRIMARY_MEASURED"
            or self.execution_authorization_id is not None
        ):
            raise _fail("CAMPAIGN02_PLAN_GATE_STAGE_INVALID")
        execution_binding_ids = (
            self.domain_manifest_id,
            self.ticket_plan_id,
            self.qualified_runtime_lineage_id,
        )
        if any(value is not None for value in execution_binding_ids) and (
            any(value is None for value in execution_binding_ids)
            or any(
                _CONTENT_ID.fullmatch(value) is None
                for value in execution_binding_ids
                if value is not None
            )
        ):
            raise _fail("CAMPAIGN02_PLAN_EXECUTION_BINDING_INVALID")
        if (
            _COMMIT_ID.fullmatch(self.source_commit) is None
            or _COMMIT_ID.fullmatch(self.source_tree) is None
        ):
            raise _fail("CAMPAIGN02_PLAN_SOURCE_INVALID")
        if self.seed < 0 or self.repetition < 1 or not self.tickets:
            raise _fail("CAMPAIGN02_PLAN_RUN_COORDINATE_INVALID")
        if (
            self.tokens_per_optimizer_step < 1
            or self.optimizer_steps_per_ticket < 1
            or self.tokens_per_ticket
            != self.tokens_per_optimizer_step * self.optimizer_steps_per_ticket
            or self.ticket_count != len(self.tickets)
            or self.total_tokens_per_arm_run != sum(item.tokens_per_ticket for item in self.tickets)
        ):
            raise _fail("CAMPAIGN02_PLAN_TOKEN_RECONCILIATION")
        if any(
            item.tokens_per_optimizer_step != self.tokens_per_optimizer_step
            or item.optimizer_steps != self.optimizer_steps_per_ticket
            or item.tokens_per_ticket != self.tokens_per_ticket
            for item in self.tickets
        ):
            raise _fail("CAMPAIGN02_PLAN_TICKET_BUDGET_MISMATCH")
        if len({item.ticket_id for item in self.tickets}) != len(self.tickets):
            raise _fail("CAMPAIGN02_PLAN_TICKET_DUPLICATE")
        if tuple(item.ordinal for item in self.tickets) != tuple(range(len(self.tickets))):
            raise _fail("CAMPAIGN02_PLAN_TICKET_ORDER_INVALID")
        if not (
            len(self.dataset_ids)
            == len(self.evaluation_profile_ids)
            == len(self.evaluation_implementation_ids)
        ):
            raise _fail("CAMPAIGN02_PLAN_EVALUATOR_BINDING_COUNT_MISMATCH")
        if (
            len(set(self.dataset_ids)) != len(self.dataset_ids)
            or len(set(self.evaluation_profile_ids)) != len(self.evaluation_profile_ids)
            or len(set(self.evaluation_implementation_ids))
            != len(self.evaluation_implementation_ids)
        ):
            raise _fail("CAMPAIGN02_PLAN_IDENTITY_DUPLICATE")

    @property
    def processed_tokens(self) -> int:
        """The only normative plan total: sum(ticket_count_d * tokens_per_ticket_d)."""
        return sum(item.tokens_per_ticket for item in self.tickets)

    @property
    def document(self) -> dict[str, object]:
        document: dict[str, object] = {
            "arm_id": self.arm_id,
            "benchmark_definition_id": self.benchmark_definition_id,
            "campaign_id": self.campaign_id,
            "certified_round_policy": (
                None
                if self.certified_round_policy is None
                else self.certified_round_policy.document
            ),
            "dataset_ids": list(self.dataset_ids),
            "definition_attestation_id": self.definition_attestation_id,
            "environment_id": self.environment_id,
            "evaluation_implementation_ids": list(self.evaluation_implementation_ids),
            "evaluation_runner_id": self.evaluation_runner_id,
            "evaluation_profile_ids": list(self.evaluation_profile_ids),
            "execution_class": self.execution_class,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "hardware_id": self.hardware_id,
            "image_id": self.image_id,
            "model_id": self.model_id,
            "optimizer_steps_per_ticket": self.optimizer_steps_per_ticket,
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "processed_tokens": self.processed_tokens,
            "repetition": self.repetition,
            "result_class": self.result_class,
            "round_id": self.round_id,
            "runner_id": self.runner_id,
            "schema_version": (
                "5.0.0"
                if self.gate_stage is not None
                else "3.0.0"
                if self.ticket_plan_id is not None
                else "2.0.0"
            ),
            "seed": self.seed,
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "tickets": [item.document for item in self.tickets],
            "ticket_count": self.ticket_count,
            "tokenizer_id": self.tokenizer_id,
            "tokens_per_optimizer_step": self.tokens_per_optimizer_step,
            "tokens_per_ticket": self.tokens_per_ticket,
            "total_tokens_per_arm_run": self.total_tokens_per_arm_run,
            "type_name": "PRIMARY_EXECUTION_PLAN",
            "workload_id": self.workload_id,
            "writer_id": self.writer_id,
        }
        if self.gate_stage is None:
            document["execution_authorization_id"] = self.execution_authorization_id
        else:
            document.update(
                {
                    "execution_authorized": False,
                    "gate_stage": self.gate_stage,
                    "ticket_identity_scope": "ROUND_ID_PLUS_TICKET_TEMPLATE_ID",
                }
            )
        if self.ticket_plan_id is not None:
            document.update(
                {
                    "domain_manifest_id": self.domain_manifest_id,
                    "qualified_runtime_lineage_id": self.qualified_runtime_lineage_id,
                    "ticket_plan_id": self.ticket_plan_id,
                }
            )
        return document

    @property
    def content_id(self) -> str:
        version = (
            b"v5"
            if self.gate_stage is not None
            else b"v3"
            if self.ticket_plan_id is not None
            else b"v2"
        )
        return sha256_content_id(
            b"deltareduce.010.primary-execution-plan."
            + version
            + b"\0"
            + canonical_json_bytes(self.document)
        )


def execution_authorization_id(authorization: dict[str, Any]) -> str:
    try:
        payload = canonical_json_bytes(authorization)
    except TypeError as exc:
        raise _fail("CAMPAIGN02_EXECUTION_AUTHORIZATION_INVALID") from exc
    return sha256_content_id(b"deltareduce.010.benchmark-execution-authorization.v1\0" + payload)


class Campaign02PlanCatalogView(Protocol):
    definition_id: str
    attestation_id: str
    definition_attestation_verified_at: datetime
    runtime_lineage_id: str
    stage_execution_identities_id: str
    plans: tuple[CampaignExecutionPlan, ...]

    @property
    def content_id(self) -> str: ...

    def plan_ids_for_stage(self, stage: str) -> tuple[str, ...]: ...


def authorize_non_primary_execution_class(
    authorization: dict[str, Any],
    plan: CampaignExecutionPlan,
) -> None:
    """Authorize only non-primary remediation smoke through its legacy document."""
    if plan.execution_class != "NON_PRIMARY_SMOKE":
        raise _fail("CAMPAIGN02_STAGE_AUTHORIZATION_PROOF_REQUIRED")
    if plan.execution_authorization_id != execution_authorization_id(authorization):
        raise _fail("CAMPAIGN02_EXECUTION_AUTHORIZATION_ID_MISMATCH")
    if (
        authorization.get("type_name") != "BENCHMARK_CAMPAIGN_REMEDIATION_AUTHORIZATION"
        or authorization.get("status") != "APPROVED_DESIGN_AND_QUALIFICATION_ONLY"
        or authorization.get("non_primary_smoke_tests_authorized") is not True
        or authorization.get("primary_execution_authorized") is not False
    ):
        raise _fail("CAMPAIGN02_NON_PRIMARY_SMOKE_NOT_AUTHORIZED")


def authorize_execution_class(
    authorization_proof: StageAuthorizationProof,
    plan: CampaignExecutionPlan,
    *,
    plan_catalog: Campaign02PlanCatalogView | None,
    predecessor_gate_receipts: Mapping[str, bytes],
    runner_role: str,
) -> VerifiedStageAuthorization:
    """Verify signed stage authority and exact typed predecessor receipts fail closed."""
    if plan.execution_class != "PRIMARY_MEASURED":
        raise _fail("CAMPAIGN02_EXECUTION_CLASS_INVALID")
    if not isinstance(runner_role, str) or not runner_role:
        raise _fail("CAMPAIGN02_STAGE_RUNNER_ROLE_REQUIRED")
    if not isinstance(authorization_proof, StageAuthorizationProof):
        raise _fail("CAMPAIGN02_STAGE_AUTHORIZATION_PROOF_REQUIRED")
    if plan.gate_stage is None or plan_catalog is None:
        raise _fail("CAMPAIGN02_PRIMARY_EXECUTION_NOT_AUTHORIZED")
    try:
        verified = verify_stage_authorization_proof(authorization_proof)
    except ValueError as exc:
        raise _fail(f"CAMPAIGN02_STAGE_AUTHORIZATION_CRYPTOGRAPHIC_PROOF_INVALID:{exc}") from exc
    authorization = verified.authorization
    stage = plan.gate_stage
    expected_flags = {
        "stage_a_authorized": stage == "STAGE_A_EXACTNESS",
        "stage_b_authorized": stage == "STAGE_B_SCIENTIFIC",
        "stage_c_authorized": stage == "STAGE_C_EMULATED_WAN",
    }
    expected_plan_ids = plan_catalog.plan_ids_for_stage(stage)
    allowed_plan_ids = authorization.allowed_plan_ids
    task_ids = authorization.authorized_task_ids
    predecessor_ids = authorization.required_predecessor_receipt_ids
    if (
        authorization.benchmark_definition_id != plan.benchmark_definition_id
        or authorization.benchmark_definition_id != plan_catalog.definition_id
        or authorization.definition_attestation_id != plan.definition_attestation_id
        or authorization.definition_attestation_id != plan_catalog.attestation_id
        or authorization.plan_catalog_id != plan_catalog.content_id
        or authorization.authorized_stage != stage
        or task_ids != CAMPAIGN02_STAGE_TASK_IDS[stage]
        or allowed_plan_ids != expected_plan_ids
        or authorization.source_commit != plan.source_commit
        or authorization.source_tree != plan.source_tree
        or authorization.issued_at < plan_catalog.definition_attestation_verified_at
        or any(getattr(authorization, key) is not value for key, value in expected_flags.items())
    ):
        raise _fail("CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED")
    required_predecessors = predecessor_ids
    if (
        (stage == "STAGE_A_EXACTNESS" and len(required_predecessors) != 0)
        or (stage == "STAGE_B_SCIENTIFIC" and len(required_predecessors) != 1)
        or (stage == "STAGE_C_EMULATED_WAN" and len(required_predecessors) != 2)
        or set(predecessor_gate_receipts) != set(required_predecessors)
    ):
        raise _fail("CAMPAIGN02_STAGE_PREDECESSOR_INVALID")
    receipts: list[StageGateReceipt] = []
    for receipt_id in required_predecessors:
        try:
            receipt = StageGateReceipt.from_canonical_bytes(predecessor_gate_receipts[receipt_id])
        except (KeyError, ValueError) as exc:
            raise _fail("CAMPAIGN02_STAGE_PREDECESSOR_INVALID") from exc
        if receipt.content_id != receipt_id:
            raise _fail("CAMPAIGN02_STAGE_PREDECESSOR_CONTENT_ID_MISMATCH")
        expected_receipt_plans = plan_catalog.plan_ids_for_stage(receipt.completed_stage)
        if (
            receipt.decision != "PASS"
            or receipt.benchmark_definition_id != plan_catalog.definition_id
            or receipt.definition_attestation_id != plan_catalog.attestation_id
            or receipt.plan_catalog_id != plan_catalog.content_id
            or receipt.qualified_runtime_lineage_id != plan_catalog.runtime_lineage_id
            or receipt.required_plan_ids != expected_receipt_plans
            or receipt.accepted_plan_ids != expected_receipt_plans
            or receipt.gate_analyzer_id != CAMPAIGN02_STAGE_GATE_ANALYZER_ID
            or receipt.source_commit != plan.source_commit
            or receipt.source_tree != plan.source_tree
            or receipt.finalized_at < plan_catalog.definition_attestation_verified_at
            or receipt.finalized_at > authorization.issued_at
        ):
            raise _fail("CAMPAIGN02_STAGE_PREDECESSOR_LINEAGE_INVALID")
        expected_runner_ids = {
            item.runner_id
            for item in plan_catalog.plans
            if item.gate_stage == receipt.completed_stage
        }
        if len(expected_runner_ids) != 1 or receipt.runner_id not in expected_runner_ids:
            raise _fail("CAMPAIGN02_STAGE_PREDECESSOR_RUNNER_INVALID")
        receipts.append(receipt)
    predecessor_stages = tuple(sorted(item.completed_stage for item in receipts))
    if (
        (stage == "STAGE_A_EXACTNESS" and predecessor_stages != ())
        or (stage == "STAGE_B_SCIENTIFIC" and predecessor_stages != ("STAGE_A_EXACTNESS",))
        or (
            stage == "STAGE_C_EMULATED_WAN"
            and predecessor_stages != ("STAGE_A_EXACTNESS", "STAGE_B_SCIENTIFIC")
        )
    ):
        raise _fail("CAMPAIGN02_STAGE_PREDECESSOR_STAGE_SET_INVALID")
    if plan.content_id not in expected_plan_ids or plan not in plan_catalog.plans:
        raise _fail("CAMPAIGN02_PLAN_NOT_AUTHORIZED")
    allowed_roles = {
        "STAGE_A_EXACTNESS": frozenset({"EXACTNESS_RUNNER"}),
        "STAGE_B_SCIENTIFIC": frozenset(
            {"SCIENTIFIC_RUNNER", "EVALUATION_RUNNER", "OBSERVATION_WRITER"}
        ),
        "STAGE_C_EMULATED_WAN": frozenset({"NETWORK_FAULT_RUNNER"}),
    }
    if runner_role not in allowed_roles[stage]:
        raise _fail("CAMPAIGN02_STAGE_RUNNER_ROLE_NOT_AUTHORIZED")
    return verified
