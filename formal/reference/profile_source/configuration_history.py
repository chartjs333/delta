"""Original CONFIG proposal/delivery/finalization facet, derived from empty.

The full source fold must additionally derive phase/time, local durability and
transport/control legality. This facet never certifies a complete native prefix
or fills those premises from an authenticated message. It replaces a supplied
finalized-config collection with a replayed collection for these operations.
"""

from dataclasses import dataclass, replace

from formal.reference.isc_crypto.codec import CodecError, _require
from formal.reference.non_isc.authentication import CONTRACT, AuthorityInputs, authenticate
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import configuration_qc as qc
from formal.reference.profile_source.availability_ledger import Occurrence


@dataclass(frozen=True)
class Proposal:
    source: Occurrence
    config: cfg.BoundConfig
    original_declaration: bytes


@dataclass(frozen=True)
class Received:
    source: Occurrence
    original: qc.SignedOccurrence
    vote_id: str
    signer: str
    context: str
    body: str


@dataclass(frozen=True)
class Finalized:
    source: Occurrence
    bound: qc.BoundQC


@dataclass(frozen=True)
class History:
    proposals: tuple[Proposal, ...] = ()
    received: tuple[Received, ...] = ()
    finalized: tuple[Finalized, ...] = ()
    # All original attempts/deliveries remain, including invalid/repeated/other
    # kinds. An unknown kind is not claimed to have been handled by this facet.
    events: tuple[Occurrence, ...] = ()


@dataclass(frozen=True)
class Result:
    state: History
    disposition: str


def observed(state, event):
    _require(type(event) is Occurrence and type(event.original) is bytes, "original event")
    _require(type(event.index) is int and event.index >= 0, "original event index")
    _require(not state.events or event.index > state.events[-1].index, "original event order")
    return replace(state, events=(*state.events, event))


def propose(state, event, validators, storage, declaration):
    result = observed(state, event)
    try:
        bound = cfg.bind(validators, storage, event.original, declaration)
    except CodecError:
        return Result(result, "rejected_configuration_bytes")
    prior = next((p for p in state.proposals if p.config.body_id == bound.body_id), None)
    if prior is not None:
        _require(prior.config.original == bound.original, "original configuration ID collision")
        return Result(result, "replay")
    return Result(
        replace(result, proposals=(*state.proposals, Proposal(event, bound, declaration))),
        "recorded",
    )


def deliver(state, event, validators, backend):
    result = observed(state, event)
    try:
        signed = authenticate(AuthorityInputs(validators, CONTRACT), backend, event.original)
        if signed.vote.kind != "ROUND_CONFIG":
            return Result(result, "other_kind_requires_its_own_handler")
    except CodecError:
        return Result(result, "rejected_signature_or_encoding")
    vote = signed.vote.original
    original = qc.SignedOccurrence(event.index, event.original)
    received = Received(
        event, original, signed.vote_id, vote.validator_id, vote.context_id, vote.body_hash
    )
    # Do not erase or reinterpret a distinct signed original, even for the same
    # signer. Native admission/Byzantine constraints must classify equivocation
    # in the enclosing producer; the QC join will not silently choose one.
    return Result(replace(result, received=(*state.received, received)), "recorded")


def finalize(state, event, validators, storage, backend):
    result = observed(state, event)
    try:
        certificate = qc.decode(event.original)
        prior = next(
            (
                c
                for c in state.finalized
                if c.bound.config.context_id == certificate["context_id"]
                and c.bound.config.body_id == certificate["body_hash"]
            ),
            None,
        )
        if prior is not None:
            # FinalizeRoundConfig's existing context/body first-finalization
            # guard. An exact retry refers to its original artifact; a new
            # arrival cut cannot elect a replacement certificate witness.
            return Result(
                result,
                "replay" if prior.source.original == event.original else "already_finalized",
            )
        proposal = next(
            (p for p in state.proposals if p.config.body_id == certificate["body_hash"]), None
        )
        _require(proposal is not None, "original configuration proposal missing")
        bound = qc.bind(
            validators,
            storage,
            backend,
            proposal.config.original,
            proposal.original_declaration,
            event.original,
            tuple(row.original for row in state.received if row.source.actor == event.actor),
            source_cut=event.index - 1,
        )
    except CodecError:
        return Result(result, "rejected_configuration_quorum")
    return Result(
        replace(result, finalized=(*state.finalized, Finalized(event, bound))), "recorded"
    )


def finalized_config(state, identifier):
    """No caller-supplied finalized-ID flag: select an actual original event result."""
    matches = tuple(c for c in state.finalized if c.bound.config.body_id == identifier)
    _require(len(matches) == 1, "one original finalized configuration required")
    return matches[0]
