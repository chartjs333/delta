"""Original Q/APC -> complete vector arithmetic inputs; NOT native authority.

The new coordinate naming profile is explicit. Neither its draft content IDs
nor an internally valid draft authority authenticate the original producer.
No APPLY profile, current-vector provenance or certificate translation is claimed.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "proposals"))
import native_binding as draft
from native_available_q import PlanAvailableQ, resolve_plan_available_q
from native_source_artifacts import MAX_TOTAL, canonical, require, schema_segments

VERSION = "deltareduce.original-vector-inputs.v1-candidate"
MAX_COORDINATES = 4096
MAX_CELLS = 65536
SHARED = (
    "parameter_schema_id",
    "profile_id",
    "proof_instance_id",
    "round_config_id",
    "scale_table_id",
    "shard_plan_id",
    "parent_checkpoint_id",
)


def schema_image(schema: dict, rows: tuple[dict, ...]) -> tuple[dict, list[dict]]:
    """Typed layout constructor only; project_inputs resolves original bytes.

    coordinate = original parameter name + ':' + ten decimal flat-offset digits.
    shard = 's' + ten decimal original plan-ordinal digits. Parameter names
    cannot contain ':'. Original dimensions/dtype/aliases/omission policy remain
    in the retained schema, not inferred from these names or discarded.
    """
    segments = schema_segments(schema)
    size = sum(s["element_count"] for s in segments)
    require(0 < size <= MAX_COORDINATES, "VECTOR_PROJECTION_SIZE")
    coordinates, locations = [], []
    for segment in segments:
        name = segment["segment_id"]
        for offset in range(segment["element_count"]):
            label = draft.identifier(f"{name}:{offset:010d}")
            coordinates.append(label)
            locations.append(
                {
                    "coordinate": label,
                    "parameter": name,
                    "flat_offset": offset,
                    "global_offset": segment["element_start"] + offset,
                }
            )
    require(coordinates == sorted(set(coordinates)), "COORDINATE_PROJECTION_ORDER")
    shards, cursor = [], 0
    for ordinal, row in enumerate(rows):
        require(row["ordinal"] == ordinal and row["element_start"] == cursor, "SHARD_PARTITION")
        length = row["element_count"]
        require(type(length) is int and 0 < length <= size - cursor, "SHARD_PARTITION")
        require(
            all(
                locations[cursor + i]["parameter"] == row["segment_id"]
                and locations[cursor + i]["flat_offset"] == row["segment_offset"] + i
                for i in range(length)
            ),
            "SHARD_PARAMETER_RANGE",
        )
        shards.append({"id": f"s{ordinal:010d}", "offset": cursor, "length": length})
        cursor += length
    require(cursor == size and 0 < len(shards) <= 4096, "SHARD_PARTITION")
    return {"coordinates": coordinates, "shards": shards}, locations


@dataclass(frozen=True)
class VectorInputs:
    source: PlanAvailableQ
    schema: dict
    locations: tuple[dict, ...]
    artifacts: dict[str, bytes]
    schema_ref: dict
    tickets: tuple[dict, ...]
    assignments: tuple[dict, ...]  # mathematical fields only; NO vote context
    results: tuple[dict, ...]


def project_inputs(
    store: Mapping[str, bytes],
    plan_id: str,
    ec_seed_bindings: Mapping[str, str],
    observation_ids: list[str],
) -> VectorInputs:
    source = resolve_plan_available_q(store, plan_id, ec_seed_bindings, observation_ids)
    first = source.inputs[0].source.q
    schema, locations = schema_image(first.schema, first.rows)
    require(len(locations) * len(source.inputs) <= MAX_CELLS, "VECTOR_PROJECTION_CELLS")
    require(len(schema["shards"]) * len(source.plan.domains) <= 4096, "ASSIGNMENT_BOUND")
    artifacts: dict[str, bytes] = {}
    schema_ref = draft.put(artifacts, "SCHEMA", schema)
    qrefs, tickets = {}, []
    for available in source.inputs:
        q = available.source.q
        require(all(q.manifest[k] == first.manifest[k] for k in SHARED), "SHARED_Q_SOURCE")
        ticket, domain = (draft.identifier(q.manifest[k]) for k in ("ticket_id", "domain_id"))
        tickets.append({"id": ticket, "domain": domain})
        require(len(q.rows) == len(schema["shards"]), "Q_SHARD_COVERAGE")
        for row, shard, original in zip(q.rows, schema["shards"], first.rows, strict=True):
            require(
                all(
                    row[k] == original[k]
                    for k in (
                        "ordinal",
                        "segment_id",
                        "segment_offset",
                        "element_start",
                        "element_count",
                        "quantum",
                    )
                ),
                "SHARED_Q_LAYOUT",
            )
            draft.fraction(row["quantum"], positive=True)
            qrefs[ticket, shard["id"]] = draft.put(
                artifacts,
                "Q_SHARD",
                {
                    "ticket": ticket,
                    "domain": domain,
                    "shard": shard["id"],
                    "schema": schema_ref,
                    "quantum": list(row["quantum"]),
                    "values": list(row["values"]),
                },
            )
    proof = source.plan.accumulator
    # Draft integer/fraction bounds are narrower than original uint64 fields.
    denominator = draft.integer(proof.denominator, 1)
    assignments, results = [], []
    for domain in source.plan.domains:
        rows = [r for r in source.plan.rows if r["domain_id"] == domain["domain_id"]]
        for ordinal, shard in enumerate(schema["shards"]):
            contributions, terms, prefixes = [], [], []
            total = [0] * shard["length"]
            for row in rows:
                qref = qrefs[row["ticket_id"], shard["id"]]
                q = draft.resolve(artifacts, qref, "Q_SHARD")
                weight = [row["numerator"], row["denominator"]]
                draft.fraction(weight)
                contributions.append({"ticket": row["ticket_id"], "weight": weight, "q": qref})
                terms.append((row["ticket_id"], tuple(weight), tuple(q["values"])))
                products = [
                    draft.arithmetic.checked(row["coefficient"] * v, proof.product_bits)
                    for v in q["values"]
                ]
                total = [
                    draft.arithmetic.checked(a + b, proof.accumulator_bits)
                    for a, b in zip(total, products, strict=True)
                ]
                prefixes.append(list(total))
            actual = draft.arithmetic.parameter(
                tuple(terms),
                native_ticket_ids=tuple(domain["tickets"]),
                denominator=denominator,
                bits=proof.accumulator_bits,
            )
            require(list(actual) == total, "VECTOR_RECURRENCE")
            assignments.append(
                {
                    "domain": domain["domain_id"],
                    "shard": shard["id"],
                    "denominator": denominator,
                    "quantum": list(first.rows[ordinal]["quantum"]),
                    "contributions": contributions,
                }
            )
            results.append(
                {
                    "domain": domain["domain_id"],
                    "shard": shard["id"],
                    "numerators": total,
                    "prefixes": prefixes,
                }
            )
    require(sum(len(raw) for raw in artifacts.values()) <= MAX_TOTAL, "DRAFT_ARTIFACT_TOTAL")
    return VectorInputs(
        source,
        schema,
        tuple(locations),
        artifacts,
        schema_ref,
        tuple(tickets),
        tuple(assignments),
        tuple(results),
    )


def check_draft_inputs(
    store: Mapping[str, bytes],
    plan_id: str,
    ec_seed_bindings: Mapping[str, str],
    observation_ids: list[str],
    draft_store: Mapping[str, bytes],
    anchor: draft.NativeAnchor,
    authority: dict,
) -> dict:
    """Resolve BOTH sources; compare derived complete vector input fields.

    NativeAnchor remains an independent authentication premise. This checker
    does not satisfy it. It checks existing draft Witness plus additional exact
    original-source arithmetic constraints. In particular, profile coefficients,
    current vectors, deadline and original-to-draft parent-QC identity are OPEN.
    """
    projected = project_inputs(store, plan_id, ec_seed_bindings, observation_ids)
    require(
        len(draft_store) <= 4096 and all(type(b) is bytes for b in draft_store.values()),
        "DRAFT_STORE_BOUND",
    )
    require(sum(len(b) for b in draft_store.values()) <= MAX_TOTAL, "DRAFT_STORE_BOUND")
    witness = draft.Witness(anchor, authority, draft_store)
    plan = projected.source.plan.members.plan
    original = projected.source.inputs[0].source.q.manifest
    for target, key in (
        ("round", "round_id"),
        ("height", "height"),
        ("view", "view"),
        ("epoch", "validator_epoch_id"),
    ):
        require(witness.context[target] == plan[key], "ORIGINAL_DRAFT_CONTEXT")
    require(
        witness.context["parent_checkpoint"] == original["parent_checkpoint_id"],
        "ORIGINAL_PARENT_CHECKPOINT",
    )
    require(witness.root["schema"] == projected.schema_ref, "ORIGINAL_DRAFT_SCHEMA")
    require(
        witness.profile["accumulator_bits"] == projected.source.plan.accumulator.accumulator_bits,
        "ORIGINAL_DRAFT_WIDTH",
    )
    require(
        list(witness.tickets.items()) == [(r["id"], r["domain"]) for r in projected.tickets],
        "ORIGINAL_DRAFT_TICKETS",
    )
    expected_keys = [(r["domain"], r["shard"]) for r in projected.assignments]
    require(list(witness.assignments) == expected_keys, "ORIGINAL_DRAFT_ASSIGNMENTS")
    parameters = []
    for key, expected, numeric in zip(
        expected_keys, projected.assignments, projected.results, strict=True
    ):
        assignment = witness.assignments[key]
        require(
            canonical({k: v for k, v in assignment.items() if k != "context"})
            == canonical(expected),
            "ORIGINAL_DRAFT_INPUTS",
        )
        parameter = witness.expected_parameter(*key)
        require(parameter["numerators"] == numeric["numerators"], "ORIGINAL_DRAFT_RESULT")
        parameters.append(parameter)
    return {
        "version": VERSION,
        "scope": "CONTENT_AND_VECTOR_INPUTS_NOT_AUTHENTICATED_ADMISSION",
        "native_export_authenticated": False,
        "source_plan_id": plan_id,
        "source_observations": list(observation_ids),
        "draft_authority": authority,
        "draft_schema": projected.schema_ref,
        "parameters": parameters,
    }
