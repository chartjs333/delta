"""EC-SOURCE-STEP-v1 computation over original native inputs.

Isolated feature000 reference only. The enclosing independent history must derive
P0, the admitted inventory and prerequisite origins. This computes a candidate
and checks its original event; it cannot grant those premises, READY, durability,
or whole R2.3 from the fact that a Python carrier can be constructed.
"""

from copy import deepcopy
from dataclasses import dataclass
from math import gcd

from formal.reference.isc_crypto.codec import _id, _label, _require, _uint, content_id
from formal.reference.isc_source import identity, policy
from formal.reference.isc_source.finalization import read_certificate_tree
from formal.reference.non_isc.authentication import authenticate
from formal.reference.profile_source import capsule_binding as wire
from formal.reference.profile_source import source_prefix

BODY_DOMAIN = "deltareduce.vote.eligibility-body.v1"
EC_DOMAIN = "deltareduce.008.eligibility-certificate.v1"


def text64(text):
    raw = text.encode("ascii")
    return _uint(len(raw), 8) + raw


def body_bytes(body):
    c = body["context"]
    for key in (
        "arithmetic_profile_id",
        "parameter_schema_id",
        "round_config_id",
        "validator_epoch_id",
    ):
        _id(c[key])
    _label(c["round_id"])
    raw = text64(c["arithmetic_profile_id"]) + _uint(c["height"], 8)
    raw += text64(c["parameter_schema_id"]) + text64(c["round_config_id"])
    raw += text64(c["round_id"]) + text64(c["validator_epoch_id"]) + _uint(c["view"], 8)
    entries = body["entries"]
    _require(0 < len(entries) <= 100000, "existing EC entry count")
    tickets = [row["ticket_id"] for row in entries]
    _require(tickets == sorted(set(tickets)), "original EC entry order")
    raw += _uint(len(entries), 8)
    for row in entries:
        n, d = row["gamma"]["numerator"], row["gamma"]["denominator"]
        _require(type(row["accepted"]) is bool, "original accepted bit")
        _require(
            type(n) is int
            and 0 <= n < 2**63
            and type(d) is int
            and 0 < d < 2**64
            and gcd(n, d) == 1,
            "native gamma domain/reduction",
        )
        for key in ("domain_id", "reason_code", "ticket_id"):
            _label(row[key])
        raw += bytes([int(row["accepted"])]) + text64(row["domain_id"])
        raw += _uint(n, 8) + _uint(d, 8) + text64(row["reason_code"]) + text64(row["ticket_id"])
    for key in (
        "input_set_certificate_id",
        "norm_evidence_id",
        "robust_profile_id",
        "seed_transcript_id",
    ):
        raw += text64(_id(body[key]))
    return raw


def certificate_bytes(sigma, certificate):
    # Existing schema-2 semantic field substitution; no seed or new wire field.
    value = {
        **certificate["context"],
        **{k: v for k, v in certificate.items() if k != "context"},
        "formal_semantics_id": _id(sigma),
        "schema_version": "2.0.0",
        "type_name": "ELIGIBILITY_CERTIFICATE",
    }
    value["entries"] = [
        {**row, "gamma": {**row["gamma"], "numerator": str(row["gamma"]["numerator"])}}
        for row in certificate["entries"]
    ]
    return identity._json(value)


def context_id(b):
    return content_id("deltareduce.vote-context.ec.v1", text64(_id(b)))


@dataclass(frozen=True)
class Delivery:
    # Original source index and receiver, not new vote/transport/WAL identities.
    position: int
    receiver: str
    original_g: bytes


@dataclass(frozen=True)
class Candidate:
    actor: str
    cut: int
    semantics: str
    prior_policy: bytes
    next_policy: bytes
    original_state: bytes
    body: bytes
    seed_id: str
    certificate: bytes
    certificate_id: str
    signers: tuple[str, ...]
    original_deliveries: tuple[Delivery, ...]
    matching_positions: tuple[int, ...]


def assemble_first(authority, backend, prior, state_raw, body_raw, rows, *, actor, cut, tick):
    """No supplied successor state, successful public action or durable flag.

    Every row here belongs to the independently derived admitted inventory.
    Rejected attempts and other events remain in the enclosing complete prefix;
    this function does not reinterpret invalid rows as verified rejections.
    """
    p = policy.decode(prior)
    snapshot = p["snapshot"]
    boot = authority.bootstrap
    state = wire.read_state(state_raw, boot.formal_semantics_id)
    for number in (cut, tick):
        _uint(number, 8)
    _require(
        p["local_validator_id"] == actor
        and p["validator_epoch_id"] == boot.validator_epoch_id
        and p["validator_ids"] == [n for n, _ in boot.validators]
        and len(p["validator_ids"]) == 4,
        "independent enrolled actor/epoch/committee",
    )
    bodies = [b for b in snapshot["eligibility_bodies"] if body_bytes(b) == body_raw]
    _require(len(bodies) == 1, "exact original body present once")
    body = bodies[0]
    c = body["context"]
    _require(
        c["round_id"] == p["round_id"] == state["round_id"]
        and c["round_config_id"] == p["round_config_id"] == state["config_id"]
        and c["validator_epoch_id"] == boot.validator_epoch_id
        and c["height"] == int(state["height"])
        and c["view"] == int(state["view"])
        and c["parameter_schema_id"] == snapshot["parameter_schema_id"]
        and c["arithmetic_profile_id"] == snapshot["arithmetic_profile_id"]
        and snapshot["state_id"] == content_id("deltareduce:003:round-state:v1", state_raw),
        "whole native context binding",
    )
    _require(
        p["round_config_id"] in snapshot["finalized_round_config_ids"]
        and p["initial_logical_tick"] <= tick < p["hard_deadline_tick"]
        and state["phase"] not in ("ABORTED", "AGGREGATED")
        and not snapshot["abort_requests"],
        "original active/time/abort guard",
    )
    b = body["input_set_certificate_id"]
    parents = [
        read_certificate_tree(boot.formal_semantics_id, row)
        for row in snapshot["input_set_certificates"]
    ]
    parent = next((v for v in parents if identity.body_id(v.body) == b), None)
    _require(
        parent is not None
        and b in snapshot["finalized_input_set_ids"]
        and parent.body.parent_checkpoint_id == state["parent_checkpoint_id"]
        and [(v["ticket_id"], v["domain_id"]) for v in body["entries"]]
        == [(v.ticket_id, v.domain_id) for v in parent.body.tuples],
        "original finalized ISC b/members",
    )
    # Full native norm/seed validity and arithmetic generation are independent
    # prerequisite checks (Lean's complete installed-state join checks their
    # typed bytes). Presence or these IDs alone never supplies their origin.
    previous = [
        (content_id(EC_DOMAIN, certificate_bytes(boot.formal_semantics_id, v["certificate"])), v)
        for v in snapshot["eligibility_certificates"]
    ]
    ids = [key for key, _ in previous]
    finalized = snapshot["finalized_eligibility_ids"]
    _require(
        ids == sorted(set(ids)) and finalized == sorted(set(finalized)), "original EC ordering"
    )
    stored = dict(previous)
    _require(all(key in stored for key in finalized), "finalized EC ID missing original witness")
    _require(
        not any(stored[key]["certificate"]["input_set_certificate_id"] == b for key in finalized),
        "first EC for b already finalized; original replay required",
    )
    h, k = content_id(BODY_DOMAIN, body_raw), context_id(b)
    _require(type(rows) is tuple, "complete original admitted inventory carrier")
    positions, signers, last = [], set(), -1
    for row in rows:
        _require(
            type(row) is Delivery and type(row.position) is int and last < row.position,
            "original delivery order/occurrence identity",
        )
        last = row.position
        if row.receiver != actor or row.position > cut:
            continue
        signed = authenticate(authority, backend, row.original_g)
        v = signed.vote.original
        if signed.vote.kind == "EC" and v.body_hash == h and v.context_id == k:
            _require(
                v.height == c["height"] and v.view == c["view"] and v.round_id == c["round_id"],
                "inconsistent admitted full-context group",
            )
            positions.append(row.position)
            signers.add(v.validator_id)
    names = tuple(sorted(signers))
    _require(len(names) >= 3, "insufficient distinct original cut signers")
    certificate = {k: deepcopy(v) for k, v in body.items() if k != "seed_transcript_id"}
    certificate.update(quorum_threshold=3, signer_ids=list(names))
    raw = certificate_bytes(boot.formal_semantics_id, certificate)
    e = content_id(EC_DOMAIN, raw)
    item = {"certificate": certificate, "seed_transcript_id": body["seed_transcript_id"]}
    _require(e not in stored or stored[e] == item, "same EC identity with different seed/witness")
    stored[e] = item
    following = deepcopy(p)
    following["snapshot"]["eligibility_certificates"] = [stored[key] for key in sorted(stored)]
    following["snapshot"]["finalized_eligibility_ids"] = sorted([*finalized, e])
    return Candidate(
        actor,
        cut,
        boot.formal_semantics_id,
        prior,
        policy.encode(following),
        state_raw,
        body_raw,
        body["seed_transcript_id"],
        raw,
        e,
        names,
        rows,
        tuple(positions),
    )


def bind_event(candidate, event, isc_raw, seed_raw, norm_raw, prerequisite_positions):
    """Original six-ref/dependency conjunct; not legal-origin certification.

    The enclosing native fold must derive prerequisite_positions and all admitted
    rows. This check cannot supply that fold by searching equal bytes or treating
    a source action label as an authority. No EC WAL slot is manufactured here.
    """
    _require(
        type(event) is source_prefix.Event
        and event.action == "ACT-EC-FINALIZE"
        and event.index > 0
        and event.index == candidate.cut + 1
        and event.actor == candidate.actor,
        "original EC source action/actor/cut",
    )
    _require(
        event.original == candidate.certificate
        and event.inputs
        == (
            candidate.prior_policy,
            candidate.original_state,
            candidate.body,
            isc_raw,
            seed_raw,
            norm_raw,
        ),
        "exact original EC witness and six ordered references",
    )
    snapshot = policy.decode(candidate.prior_policy)["snapshot"]
    body = next(row for row in snapshot["eligibility_bodies"] if body_bytes(row) == candidate.body)
    parent = identity.decode_certificate(isc_raw)
    parents = tuple(
        read_certificate_tree(candidate.semantics, row)
        for row in snapshot["input_set_certificates"]
    )
    _require(
        parent.body.formal_semantics_id == candidate.semantics
        and identity.body_id(parent.body) == body["input_set_certificate_id"]
        and parent in parents,
        "original ISC witness resolves b and is retained",
    )
    _require(
        content_id("deltareduce.008.seed-transcript.v1", seed_raw) == body["seed_transcript_id"]
        and content_id("deltareduce.008.norm-evidence.v1", norm_raw) == body["norm_evidence_id"],
        "exact seed/norm references",
    )
    _require(
        all(type(i) is int and 0 <= i < event.index for i in prerequisite_positions),
        "original backward prerequisite positions",
    )
    _require(all(i < event.index for i in candidate.matching_positions), "original delivery cut")
    expected = tuple(sorted(set((*prerequisite_positions, *candidate.matching_positions))))
    _require(event.dependencies == expected, "whole original dependency union, no omitted delivery")
    return candidate


@dataclass(frozen=True)
class Reobservation:
    original: Candidate
    current_policy: bytes
    current_state: bytes
    current_deliveries: tuple[Delivery, ...]


def reobserve(
    authority,
    backend,
    original_event,
    original_rows,
    original_tick,
    prerequisite_positions,
    *,
    current_policy,
    current_state,
    current_rows,
):
    """Recompute the original event, then return the current bytes unchanged.

    No later delivery cut, new finalization ID, vote or WAL slot is allocated.
    The full fold must establish this event's origin and the complete current
    installed state (including current journals/ABORT); presence of these bytes
    alone does not confer that authority. Lean checkReplay includes both full
    static InstalledState joins, separately from those origin premises.
    """
    _require(type(original_event) is source_prefix.Event, "original event required")
    _require(len(original_event.inputs) == 6, "exact original six-ref event")
    prior, state, body, parent, seed, norm = original_event.inputs
    original = assemble_first(
        authority,
        backend,
        prior,
        state,
        body,
        original_rows,
        actor=original_event.actor,
        cut=original_event.index - 1,
        tick=original_tick,
    )
    bind_event(original, original_event, parent, seed, norm, prerequisite_positions)
    p = policy.decode(current_policy)
    _require(p["local_validator_id"] == original.actor, "same original actor")
    snapshot = p["snapshot"]
    _require(
        original.certificate_id in snapshot["finalized_eligibility_ids"],
        "original EC remains finalized",
    )
    retained = [
        v
        for v in snapshot["eligibility_certificates"]
        if certificate_bytes(original.semantics, v["certificate"]) == original.certificate
    ]
    _require(
        len(retained) == 1 and retained[0]["seed_transcript_id"] == original.seed_id,
        "exact original retained witness and seed",
    )
    _require(type(current_rows) is tuple, "complete current delivery carrier retained")
    return Reobservation(original, current_policy, current_state, current_rows)
