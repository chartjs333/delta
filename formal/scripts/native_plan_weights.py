"""Original APC membership/weight-to-accumulator relation; no signer authority.

This bounded proposal resolves original bytes before doing coefficient math.
The independently supplied EC-to-seed edge is primitive metadata, not an
approval callback. Its provenance and the APC anchor remain external premises.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import native_certificate_chain as certificates
from native_accumulator_source import Accumulator, rational, resolve_accumulator
from native_isc_body import Context
from native_source_artifacts import MAX_TOTAL, SourceError, cid, decode, require

VERSION = "deltareduce.original-plan-weights.v1-candidate"


@dataclass(frozen=True)
class PlanMembers:
    plan_id: str
    plan: dict
    rows: tuple[dict, ...]
    ec_seed: tuple[str, str]
    sources: tuple[dict, ...]


def resolve_members(
    store: Mapping[str, bytes], plan_id: str, ec_seed_bindings: Mapping[str, str]
) -> PlanMembers:
    """Complete original ordered membership, without requiring a later ROOT.

    Cross-parent/context and norm membership checks are deliberately stronger
    than the isolated native verify_plan predicate. This is not native error
    order/equivalence, certificate finality or a clipping/seed computation proof.
    """
    loaded: dict[str, dict] = {}
    total = 0

    def load(identifier, kind):
        nonlocal total
        cid(identifier)
        require(identifier in store, "MISSING_PREIMAGE:" + identifier)
        raw = store[identifier]
        # Resource/canonical checks precede the existing original certificate
        # codec. No generic unbounded JSON decode is a trusted entry point.
        decode(raw)
        try:
            doc = certificates.decode_certificate(raw, identifier, kind)
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            raise SourceError("CERTIFICATE:" + str(exc)) from exc
        if loaded:
            first = next(iter(loaded.values()))["document"]
            require(all(doc[k] == first[k] for k in Context.__annotations__), "MIXED_CONTEXT")
        if identifier not in loaded:
            total += len(raw)
            require(total <= MAX_TOTAL, "SOURCE_TOTAL_LIMIT")
            loaded[identifier] = {
                "id": identifier,
                "kind": kind,
                "document": doc,
                "bytes_hex": raw.hex(),
            }
        require(loaded[identifier]["kind"] == kind, "SOURCE_KIND")
        return doc

    plan = load(plan_id, "AGGREGATION_PLAN_CERTIFICATE")
    ec_id, isc_id, seed_id = (
        plan[k]
        for k in ("eligibility_certificate_id", "input_set_certificate_id", "seed_transcript_id")
    )
    ec = load(ec_id, "ELIGIBILITY_CERTIFICATE")
    isc = load(isc_id, "INPUT_SET_CERTIFICATE")
    seed = load(seed_id, "SEED_TRANSCRIPT")
    norm = load(ec["norm_evidence_id"], "NORM_EVIDENCE")
    require(ec_seed_bindings.get(ec_id) == seed_id, "INDEPENDENT_EC_SEED_EDGE")
    require(all(d["input_set_certificate_id"] == isc_id for d in (ec, seed, norm)), "ISC_PARENT")
    members = [(r["ticket_id"], r["domain_id"]) for r in isc["tuples"]]
    # An ISC can sort (ticket, commitment) while containing two entries for one
    # ticket; that cannot align with the unique ordered EC/APC ticket namespace.
    require(len({t for t, _ in members}) == len(members), "ISC_DUPLICATE_TICKET")
    require(members == [(r["ticket_id"], r["domain_id"]) for r in ec["entries"]], "EC_MEMBERS")
    require([r["ticket_id"] for r in norm["entries"]] == [t for t, _ in members], "NORM_MEMBERS")
    eligible = [
        (e, source) for e, source in zip(ec["entries"], isc["tuples"], strict=True) if e["accepted"]
    ]
    tickets = [e["ticket_id"] for e, _ in eligible]
    require(tickets == [r["ticket_id"] for r in plan["weights"]], "WEIGHT_COVERAGE")
    require(tickets == [r["ticket_id"] for r in plan["bucket_assignments"]], "BUCKET_COVERAGE")
    rows = []
    for (entry, source), weight, bucket in zip(
        eligible, plan["weights"], plan["bucket_assignments"], strict=True
    ):
        # APC alpha is the final coefficient. EC gamma is retained as source
        # metadata and MUST NOT be multiplied into alpha a second time.
        numerator, denominator = rational(weight["alpha"])
        rows.append(
            {
                "ticket_id": entry["ticket_id"],
                "domain_id": entry["domain_id"],
                "bucket_id": bucket["bucket_id"],
                "numerator": numerator,
                "denominator": denominator,
                "ec_gamma": entry["gamma"],
                "commitment_id": source["commitment_id"],
                "availability_certificate_id": source["availability_certificate_id"],
            }
        )
    return PlanMembers(
        plan_id,
        plan,
        tuple(rows),
        (ec_id, seed_id),
        tuple({k: v for k, v in s.items() if k != "document"} for s in loaded.values()),
    )


@dataclass(frozen=True)
class PlanWeights:
    members: PlanMembers
    accumulator: Accumulator
    rows: tuple[dict, ...]
    domains: tuple[dict, ...]
    sources: tuple[dict, ...]


def resolve_plan_weights(
    store: Mapping[str, bytes], plan_id: str, ec_seed_bindings: Mapping[str, str]
) -> PlanWeights:
    """Derive coefficients from the APC's specific original proof denominator.

    Global eligible count <= N is an explicit sufficient projection restriction;
    every per-domain accumulation consequently has <= N terms. Zero coefficients
    still count. This API neither establishes Q values nor native admission.
    """
    members = resolve_members(store, plan_id, ec_seed_bindings)
    proof = resolve_accumulator(store, members.plan["accumulator_proof_id"])
    sources = members.sources + proof.sources
    require(sum(len(s["bytes_hex"]) // 2 for s in sources) <= MAX_TOTAL, "SOURCE_TOTAL_LIMIT")
    config = decode(
        bytes.fromhex(next(s["bytes_hex"] for s in proof.sources if s["kind"] == "config"))
    )
    require(config["parameter_schema_id"] == members.plan["parameter_schema_id"], "CONFIG_SCHEMA")
    require(config["base_round_config_id"] == members.plan["round_config_id"], "CONFIG_ROUND")
    require(len(members.rows) <= proof.contribution_max, "CONTRIBUTION_BOUND")
    rows = []
    for row in members.rows:
        n, d = row["numerator"], row["denominator"]
        require(proof.denominator % d == 0, "DENOMINATOR_NOT_DIVISOR")
        coefficient = n * (proof.denominator // d)
        require(coefficient <= proof.coefficient_max, "COEFFICIENT_BOUND")
        rows.append({**row, "coefficient": coefficient})
    domains = []
    for domain in sorted({r["domain_id"] for r in rows}):
        selected = [r for r in rows if r["domain_id"] == domain]
        prefix, bounds = 0, []
        for row in selected:
            product = 32767 * row["coefficient"]
            prefix += product
            require(product <= proof.product and prefix <= proof.prefix, "DERIVED_BOUND")
            bounds.append(prefix)
        domains.append(
            {
                "domain_id": domain,
                "tickets": [r["ticket_id"] for r in selected],
                "coefficients": [r["coefficient"] for r in selected],
                "common_denominator": proof.denominator,
                "worst_absolute_prefixes": bounds,
            }
        )
    return PlanWeights(members, proof, tuple(rows), tuple(domains), sources)
