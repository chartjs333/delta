"""Q preimages against native InputLedger primitives, not commitment authority.

The observation format is a NEW tooling envelope. Native InputLedger has no
manifest-ID field or commitment preimage decoder. Its missing identity bridge
is deliberately not supplied as a Boolean, a hash convention or a translation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from native_accumulator_source import BoundQSource, resolve_bound_q_source
from native_plan_weights import PlanWeights, resolve_plan_weights
from native_source_artifacts import (
    MAX_TOTAL,
    canonical,
    cid,
    content_id,
    decode,
    items,
    require,
    shape,
    uint,
)

VERSION = "deltareduce.available-q-observation.v1-candidate"
DOMAIN = "deltareduce.000.available-q-observation.v1-candidate"
SOURCE = "60c692f6e391f839829dfc64e93380db54cd507b"


def identifiers(values: object, content: bool = False) -> list[str]:
    rows = items(values, 4096, 1)
    for value in rows:
        require(type(value) is str and 0 < len(value) <= 255, "IDENTIFIER_BOUND")
        if content:
            cid(value)
    require(rows == sorted(set(rows)), "ORDERED_UNIQUE_IDS")
    return rows


def ledger_inputs(observation: dict) -> dict:
    """Typed first-insert/freeze conditions, not the replay/late/WAL machine.

    Native IDs only require nonempty text. The canonical observation's ASCII,
    255-character, 4096-entry restrictions are a narrower proposal profile.
    Native canonical ID sets must be nonempty, including the required leaf set.
    """
    tickets = identifiers(observation["permitted_ticket_ids"])
    attesters = identifiers(observation["permitted_attester_ids"])
    required = identifiers(observation["required_leaf_ids"], True)
    threshold = uint(observation["required_threshold"], (1 << 32) - 1, 1)
    commitment = shape(observation["commitment"], "ticket_id commitment_id")
    proof = shape(
        observation["availability"],
        "ticket_id commitment_id certificate_id covered_leaf_ids attester_ids threshold",
    )
    for record in (commitment, proof):
        identifiers([record["ticket_id"]])
        cid(record["commitment_id"])
    cid(proof["certificate_id"])
    require(commitment["ticket_id"] in tickets, "UNKNOWN_TICKET")
    require(proof["ticket_id"] == commitment["ticket_id"], "COMMITMENT_MISSING")
    require(proof["commitment_id"] == commitment["commitment_id"], "COMMITMENT_MISMATCH")
    covered = identifiers(proof["covered_leaf_ids"], True)
    require(covered == required, "AVAILABILITY_COVERAGE")
    signers = identifiers(proof["attester_ids"])
    require(uint(proof["threshold"], (1 << 32) - 1, 1) == threshold, "THRESHOLD_MISMATCH")
    require(len(signers) >= threshold and set(signers) <= set(attesters), "ATTESTER_QUORUM")
    return {
        "ticket_id": commitment["ticket_id"],
        "commitment_id": commitment["commitment_id"],
        "availability_certificate_id": proof["certificate_id"],
    }


@dataclass(frozen=True)
class AvailableQ:
    observation_id: str
    observation_bytes_hex: str
    source: BoundQSource
    frozen_input: dict
    required_leaves: tuple[str, ...]


def resolve_available_q(store: Mapping[str, bytes], observation_id: str) -> AvailableQ:
    cid(observation_id)
    require(observation_id in store, "MISSING_PREIMAGE:" + observation_id)
    raw = store[observation_id]
    observation = shape(
        decode(raw),
        "version source_commit provenance manifest_id permitted_ticket_ids commitment "
        "availability required_leaf_ids permitted_attester_ids required_threshold",
    )
    require(content_id(raw, DOMAIN) == observation_id, "OBSERVATION_HASH")
    require(observation["version"] == VERSION, "OBSERVATION_VERSION")
    require(observation["source_commit"] == SOURCE, "SOURCE_COMMIT")
    require(
        observation["provenance"] == "UNAUTHENTICATED_COMPONENT_INPUT",
        "NO_AUTHENTICATED_EXPORT_IN_THIS_VERSION",
    )
    frozen = ledger_inputs(observation)
    q = resolve_bound_q_source(store, observation["manifest_id"])
    require(frozen["ticket_id"] == q.q.manifest["ticket_id"], "MANIFEST_TICKET")
    # Manifest order is schema/range order; native coverage is lexicographic
    # content-ID order. Retain the former, derive the latter without relabeling.
    leaves = [r["leaf_id"] for r in q.q.manifest["shards"]]
    require(len(set(leaves)) == len(leaves), "DUPLICATE_MANIFEST_LEAF")
    required = sorted(leaves)
    require(observation["required_leaf_ids"] == required, "REQUIRED_Q_LEAF_SET")
    require(
        len(raw) + sum(len(s["bytes_hex"]) // 2 for s in q.q.sources) <= MAX_TOTAL,
        "SOURCE_TOTAL_LIMIT",
    )
    # Deliberately NO equality of commitment_id with manifest ID or Merkle root:
    # neither convention is established by the pinned native InputLedger API.
    return AvailableQ(observation_id, raw.hex(), q, frozen, tuple(required))


@dataclass(frozen=True)
class PlanAvailableQ:
    plan: PlanWeights
    inputs: tuple[AvailableQ, ...]


def resolve_plan_available_q(
    store: Mapping[str, bytes],
    plan_id: str,
    ec_seed_bindings: Mapping[str, str],
    observation_ids: list[str],
) -> PlanAvailableQ:
    """Join ALL eligible APC rows to exact Q observations, still unauthenticated.

    Rejected ISC members remain in the original certificate preimages; their Q
    objects are not needed by this accepted arithmetic input relation. This does
    not assert complete frozen-ledger or first-freeze history reconstruction.
    """
    plan = resolve_plan_weights(store, plan_id, ec_seed_bindings)
    items(observation_ids, 4096, 1)
    require(len(observation_ids) == len(plan.rows), "PLAN_INPUT_COUNT")
    inputs, all_sources = [], {s["id"]: s["bytes_hex"] for s in plan.sources}
    for row, oid in zip(plan.rows, observation_ids, strict=True):
        q = resolve_available_q(store, oid)
        require(q.frozen_input == {k: row[k] for k in q.frozen_input}, "PLAN_INPUT_IDENTITY")
        m = q.source.q.manifest
        require(m["domain_id"] == row["domain_id"], "PLAN_INPUT_DOMAIN")
        require(
            m["parameter_schema_id"] == plan.members.plan["parameter_schema_id"],
            "PLAN_INPUT_SCHEMA",
        )
        require(m["proof_instance_id"] == plan.accumulator.proof_id, "PLAN_INPUT_PROOF")
        require(m["round_config_id"] == plan.accumulator.config_id, "PLAN_INPUT_CONFIG")
        for s in (*q.source.q.sources, {"id": oid, "bytes_hex": q.observation_bytes_hex}):
            require(
                s["id"] not in all_sources or all_sources[s["id"]] == s["bytes_hex"],
                "SOURCE_CHANGED",
            )
            all_sources[s["id"]] = s["bytes_hex"]
        inputs.append(q)
    require(sum(len(v) // 2 for v in all_sources.values()) <= MAX_TOTAL, "SOURCE_TOTAL_LIMIT")
    return PlanAvailableQ(plan, tuple(inputs))


def observation_bytes(observation: dict) -> tuple[str, bytes]:
    """Encoding helper only; resolution, not this helper, checks source contents."""
    raw = canonical(observation)
    return content_id(raw, DOMAIN), raw
