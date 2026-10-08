"""Native InputLedger facet with the approved O witness guard, from empty state.

The full producer checker must derive configuration, committed manifest/context,
permitted tickets and occurrence inputs from the independent prefix and enforce
the outer phase/deadline gates. This component does not assert those premises,
invent remote physical facts, or accept a supplied nonempty ledger.
"""

from dataclasses import dataclass, replace

from formal.reference.isc_crypto.codec import CodecError, _id, _require
from formal.reference.isc_source.identity import InputTuple
from formal.reference.profile_source import configuration as config
from formal.reference.profile_source.metadata import text
from formal.reference.storage_source import codec as s
from formal.reference.storage_source import retention as r
from formal.scripts.native_source_artifacts import SourceError


@dataclass(frozen=True)
class Occurrence:
    # Original source-index position/actor are provenance coordinates, not new
    # protocol objects. Their custody is verified by the enclosing profile.
    index: int
    actor: str
    original: bytes


@dataclass(frozen=True)
class Commitment:
    ticket_id: str
    commitment_id: str


@dataclass(frozen=True)
class Accepted:
    occurrence: Occurrence
    bound: r.BoundWitness
    ticket_id: str
    commitment_id: str


@dataclass(frozen=True)
class Ledger:
    permitted: tuple[str, ...]
    commitments: tuple[Commitment, ...] = ()
    availabilities: tuple[Accepted, ...] = ()
    late_commitments: tuple[Commitment, ...] = ()
    late_availabilities: tuple[Accepted, ...] = ()
    deliveries: tuple[Occurrence, ...] = ()
    # Retained source events include replays, rejected attempts and alternate ACs.
    events: tuple[Occurrence, ...] = ()
    frozen: tuple[tuple[str, str, str], ...] | None = None


@dataclass(frozen=True)
class Result:
    state: Ledger
    disposition: str


def empty(permitted):
    _require(type(permitted) is tuple and bool(permitted), "original native permitted tickets")
    for ticket in permitted:
        _require(type(ticket) is str and bool(ticket), "native nonempty identifier")
    _require(list(permitted) == sorted(set(permitted)), "native canonical permitted tickets")
    return Ledger(permitted)


def observed(state, event):
    _require(type(event) is Occurrence, "original occurrence required")
    _require(type(event.index) is int and event.index >= 0, "original source position")
    _require(type(event.original) is bytes, "original complete event bytes")
    text(event.actor, nonempty=True)
    _require(not state.events or state.events[-1].index < event.index, "original event order")
    return replace(state, events=(*state.events, event))


def record_commitment(state, event, value):
    """Exact native first/replay/late/conflict disposition; preserve each attempt."""
    next_state = observed(state, event)
    _require(type(value) is Commitment, "original commitment fields")
    _require(type(value.ticket_id) is str and bool(value.ticket_id), "native nonempty identifier")
    _id(value.commitment_id)
    if value.ticket_id not in state.permitted:
        return Result(next_state, "unknown_ticket")
    existing = next((c for c in state.commitments if c.ticket_id == value.ticket_id), None)
    if existing is not None:
        return Result(next_state, "replay" if existing == value else "commitment_equivocation")
    if state.frozen is not None:
        late = next((c for c in state.late_commitments if c.ticket_id == value.ticket_id), None)
        if late is not None:
            return Result(next_state, "late" if late == value else "commitment_equivocation")
        return Result(
            replace(
                next_state,
                late_commitments=tuple(
                    sorted((*state.late_commitments, value), key=lambda c: c.ticket_id)
                ),
            ),
            "late",
        )
    return Result(
        replace(
            next_state,
            commitments=tuple(sorted((*state.commitments, value), key=lambda c: c.ticket_id)),
        ),
        "recorded",
    )


def deliver(state, event):
    """Retain even invalid/unrelated/raw repeated Gs; no signing credit is implied."""
    return replace(observed(state, event), deliveries=(*state.deliveries, event))


def record_availability(
    state, event, validators, bootstrap, backend, original_configuration, context, declaration
):
    """S + R + enclosing config + exact original pre-cut witness, then native ledger.

    The Context's committed leaf table and configuration finality must be derived
    by the complete native source checker. No arbitrary availability boolean or
    caller-chosen list of successful signature outcomes substitutes for them.
    """
    next_state = observed(state, event)
    try:
        configuration = config.bind(validators, bootstrap, original_configuration, declaration)
        common = s.context(bootstrap, context)
        _require(
            common["round_config_id"] == configuration.body_id
            and common["round_id"] == configuration.round_id
            and int(common["height"]) == configuration.height
            and common["parent_checkpoint_id"] == configuration.parent,
            "whole original enclosing configuration/context",
        )
        bound = r.authenticate_bound_witness(
            r.CONTRACT,
            bootstrap,
            backend,
            context,
            configuration.storage_binding.original_binding,
            declaration,
            event.original,
            tuple(d.original for d in state.deliveries),
        )
    except CodecError:
        # This is a reference disposition, NOT a new ABI status. Failed evidence
        # stays in events; no partial admission or witness list mutation occurs.
        return Result(next_state, "rejected_authenticated_witness")
    ticket, commitment = common["ticket_id"], common["commitment_id"]
    prior = next((c for c in state.commitments if c.ticket_id == ticket), None)
    if prior is None:
        return Result(next_state, "commitment_missing")
    if prior.commitment_id != commitment:
        return Result(next_state, "availability_commitment_mismatch")
    accepted = Accepted(event, bound, ticket, commitment)
    existing = next((a for a in state.availabilities if a.ticket_id == ticket), None)
    if existing is not None:
        return Result(
            next_state,
            "replay"
            if existing.bound.witness.original_certificate == event.original
            else "availability_conflict",
        )
    if state.frozen is not None:
        late = next((a for a in state.late_availabilities if a.ticket_id == ticket), None)
        if late is not None:
            return Result(
                next_state,
                "late"
                if late.bound.witness.original_certificate == event.original
                else "availability_conflict",
            )
        return Result(
            replace(
                next_state,
                late_availabilities=tuple(
                    sorted((*state.late_availabilities, accepted), key=lambda a: a.ticket_id)
                ),
            ),
            "late",
        )
    return Result(
        replace(
            next_state,
            availabilities=tuple(
                sorted((*state.availabilities, accepted), key=lambda a: a.ticket_id)
            ),
        ),
        "recorded",
    )


def freeze(state, event):
    next_state = observed(state, event)
    if state.frozen is not None:
        return Result(next_state, "replay")
    if not state.availabilities:
        return Result(next_state, "input_set_empty")
    rows = tuple(
        (a.ticket_id, a.commitment_id, a.bound.witness.certificate_id) for a in state.availabilities
    )
    return Result(replace(next_state, frozen=rows), "recorded")


def record_source_availability(
    state,
    event,
    validators,
    bootstrap,
    backend,
    original_configuration,
    declaration,
    original_artifacts,
    manifest_id,
):
    """Join original metadata to the already retained native commitment.

    No caller-supplied expected storage Context enters this path. Finalized
    configuration/ticket/commitment producer provenance remains the outer
    prefix check; invalid events stay retained without an admitted AC.
    """
    from formal.reference.profile_source import manifest_context

    try:
        manifest = manifest_context.resolve(
            original_artifacts, validators.formal_semantics_id, manifest_id
        )
        commitment = next((c for c in state.commitments if c.ticket_id == manifest.ticket_id), None)
        if commitment is None:
            return Result(observed(state, event), "commitment_missing")
        _, context = manifest_context.bind_context(
            validators,
            bootstrap,
            original_configuration,
            declaration,
            original_artifacts,
            manifest_id,
            commitment,
        )
    except (CodecError, SourceError):
        return Result(observed(state, event), "rejected_original_manifest")
    return record_availability(
        state, event, validators, bootstrap, backend, original_configuration, context, declaration
    )


def original_tuples(state, domains):
    """No new coordinate identities; domains come from original issued WorkTickets."""
    _require(state.frozen is not None, "native freeze must have occurred")
    return tuple(
        InputTuple(ac, commitment, domains[ticket], ticket)
        for ticket, commitment, ac in state.frozen
    )
