"""Exact W1 output binding to a supplied independently derived predecessor.

This is the byte-composition edge, not the origin verifier. The enclosing native
fold must produce S0/P0/Cut and the complete delivery inventory independently.
None of the bytes inside IFQ1 may substitute for that missing derivation. No
append/barrier/exposure is performed or inferred by this reference checker.
"""

from dataclasses import dataclass
from hashlib import sha256

from formal.reference.isc_crypto.codec import _decimal, _id, _require, _uint, content_id
from formal.reference.isc_source import budget, finalization
from formal.reference.isc_source.authentication import registry
from formal.reference.isc_source.policy import decode as decode_policy
from formal.reference.isc_w1.codec import (
    decode_candidate_state,
    decode_frame,
    decode_receipt,
    decode_request_source,
)
from formal.reference.profile_source import configuration as wire
from formal.reference.profile_source import journals
from formal.reference.profile_source.metadata import closed

COMMAND_FIELDS = set(
    "actor_id body_hash command_kind formal_semantics_id height logical_tick "
    "request_id round_id schema_version type_name view".split()
)
STATE_FIELDS = set(
    "available_ticket_count committed_ticket_count config_id durable_sequence "
    "formal_semantics_id height parent_checkpoint_id phase round_id schema_version "
    "state_root ticket_count type_name view".split()
)
PHASES = {"TICKETING_OPEN", "COMMITTED", "AVAILABLE", "ELIGIBLE", "AGGREGATED", "ABORTED"}


def envelope(kind, fields):
    payload = wire.encode_value(fields)
    raw = b"DRC1\x01\x00" + _uint(kind, 2) + _uint(len(payload), 4) + payload
    _require(len(raw) <= wire.MAX_FRAME, "existing DRC1 envelope bound")
    return raw


def read_envelope(raw, kind, fields, sigma, type_name):
    reader = wire.Reader(raw)
    _require(
        reader.take(8) == b"DRC1\x01\x00" + _uint(kind, 2) and reader.count() == len(raw) - 12,
        "original DRC1 header and length",
    )
    value = closed(reader.value(), fields)
    _require(reader.at == len(raw) and envelope(kind, value) == raw, "exact whole canonical DRC1")
    _require(
        value["formal_semantics_id"] == sigma
        and value["type_name"] == type_name
        and value["schema_version"] == "1.0.0",
        "independent semantics, original unchanged DRC1 type schema",
    )
    return value


def native_identifier(value):
    wire.ascii_text(value)
    _require(bool(value), "existing nonempty native identifier")


def read_command(raw, sigma):
    value = read_envelope(raw, 6, COMMAND_FIELDS, sigma, "COMMAND")
    for key in ("height", "view", "logical_tick"):
        _decimal(value[key])
    for key in ("actor_id", "command_kind", "request_id", "round_id"):
        native_identifier(value[key])
    _id(value["body_hash"])
    return value


def read_state(raw, sigma):
    value = read_envelope(raw, 5, STATE_FIELDS, sigma, "ROUND_STATE")
    for key in ("available_ticket_count", "committed_ticket_count", "ticket_count"):
        _uint(value[key], 4)
    for key in ("durable_sequence", "height", "view"):
        _decimal(value[key])
    for key in ("config_id", "parent_checkpoint_id", "state_root"):
        _id(value[key])
    native_identifier(value["round_id"])
    _require(
        value["phase"] in PHASES
        and value["available_ticket_count"] <= value["committed_ticket_count"]
        and value["committed_ticket_count"] <= value["ticket_count"],
        "existing native phase and ticket count order",
    )
    return value


def publish_bytes(sigma, command, original_state, witness_id):
    state_id = content_id("deltareduce:003:round-state:v1", original_state)
    return envelope(
        7,
        {
            "effects": [
                {
                    "body_hash": witness_id,
                    "effect_id": "effect:" + command["request_id"] + ":02:publish",
                    "kind": "PUBLISH_CERTIFICATE",
                    "target_id": "validators",
                }
            ],
            "formal_semantics_id": sigma,
            "next_state_root": state_id,
            "prior_state_root": state_id,
            "request_id": command["request_id"],
            "round_id": command["round_id"],
            "schema_version": "1.0.0",
            "type_name": "EFFECT_BATCH",
        },
    )


@dataclass(frozen=True)
class Predecessor:
    # These are outputs required from the independent producer fold. Constructing
    # this dataclass is not itself evidence that the fold has been implemented.
    original_wal: bytes
    source_index_id: str
    source_cut: int
    native_state: bytes
    policy: bytes
    cut: finalization.Cut


@dataclass(frozen=True)
class BoundCapsule:
    original: bytes
    predecessor: Predecessor
    candidate: finalization.Candidate
    physical_slot: int
    original_command: bytes
    original_effects: bytes
    original_receipt: bytes


def bind(bootstrap, backend, original, prior, body):
    _require(type(prior) is Predecessor, "derived complete predecessor required")
    frame = decode_frame(original)
    _require(frame.kind == 3, "original finalization capsule kind")
    prefix = journals.inspect(prior.original_wal, cut_slot=0, required_prefix=prior.original_wal)
    _require(frame.sequence == len(prefix.positions) + 1, "next original physical WAL slot")
    request = decode_request_source(frame.sections[0])
    state = decode_candidate_state(frame.sections[1])
    receipt = decode_receipt(frame.sections[3])
    _id(prior.source_index_id)
    _uint(prior.source_cut, 8)
    _require(
        request.prior_wal_byte_length == len(prior.original_wal)
        and request.prior_wal_sha256 == sha256(prior.original_wal).digest()
        and request.source_index_id == prior.source_index_id
        and request.source_cut_event_index == prior.source_cut
        and request.prior_state_bytes == prior.native_state
        and request.prior_policy_bytes == prior.policy
        and request.deliveries == tuple(row.event for row in prior.cut.delivered),
        "exact independent predecessor and full original delivery cut",
    )
    command = read_command(request.command_bytes, bootstrap.formal_semantics_id)
    native = read_state(prior.native_state, bootstrap.formal_semantics_id)
    policy = decode_policy(prior.policy)
    _require(
        command["command_kind"] == "FINALIZE_ISC"
        and command["actor_id"] == policy["local_validator_id"]
        and command["round_id"] == native["round_id"] == body.round_id
        and int(command["height"]) == int(native["height"]) == prior.cut.height
        and int(command["view"]) == int(native["view"]) == prior.cut.view
        and int(command["logical_tick"]) == prior.cut.logical_tick
        and native["config_id"] == body.round_config_id
        and native["parent_checkpoint_id"] == prior.cut.parent_checkpoint_id
        and content_id("deltareduce:003:round-state:v1", prior.native_state) == prior.cut.state_id,
        "exact original command/native cut context; no implicit clock advance",
    )
    candidate = finalization.assemble_first(bootstrap, backend, prior.policy, body, prior.cut)
    _require(command["body_hash"] == candidate.consensus_id, "command references consensus b")
    _require(
        state.policy_bytes == candidate.next_policy
        and state.certificate_bytes == candidate.certificate,
        "independently reconstructed full P1/C; no lineage erasure",
    )
    effects = publish_bytes(
        bootstrap.formal_semantics_id, command, prior.native_state, candidate.witness_id
    )
    _require(
        frame.sections[2] == effects, "exact unchanged S0 and single original witness publication"
    )
    _require(
        receipt.command_id == content_id("deltareduce:003:command:v1", request.command_bytes)
        and receipt.certificate_id == candidate.witness_id
        and receipt.effect_batch_id == content_id("deltareduce:003:effect-batch:v1", effects),
        "exact original receipt IDs; c is never replaced by b",
    )
    budget.check_frame(frame, body.round_id, body.validator_epoch_id)
    return BoundCapsule(
        original,
        prior,
        candidate,
        frame.sequence,
        request.command_bytes,
        effects,
        frame.sections[3],
    )


@dataclass(frozen=True)
class IndexedCapsule:
    bound: BoundCapsule
    original_source_cut: object
    original_deliveries: object
    command_prefix: object


def bind_indexed(
    bootstrap,
    backend,
    prefix,
    *,
    journal_id,
    physical_slot,
    consumer_index,
    original_prior_index,
    initial_state,
    initial_tick,
    original_policy,
    logical_tick,
    frozen_inputs,
    body,
):
    """Join W1 to original source and own command prefix, not supplied S0/Gs.

    Remaining inputs are explicit: initial native authority, full derived P0,
    logical-clock/control state and frozen ledger. This function does not claim
    their origin, kind-2 admission, barrier completion or whole R2.3 closure.
    """
    from formal.reference.profile_source import commands, metadata, source_prefix

    boot = metadata.validate(prefix.metadata.bootstrap_bytes, "BOOTSTRAP")
    actor = boot["local_validator_id"]
    _, enrolled = registry(bootstrap)
    _require(
        bootstrap.formal_semantics_id == boot["formal_semantics_id"]
        and bootstrap.validator_epoch_id == boot["validator_epoch_id"]
        and bootstrap.origin_id == boot["origin_id"]
        and [(name, key) for name, (key, _) in enrolled.items()]
        == [(row["validator_id"], row["key_ref"]) for row in boot["validators"]],
        "independent original profile origin/generation/epoch/keys",
    )
    originals = [
        raw
        for a, name, raw in prefix.metadata.original_own_journals
        if (a, name) == (actor, journal_id)
    ]
    _require(len(originals) == 1, "one original own journal, no missing-as-empty")
    journal = journals.inspect(originals[0], cut_slot=0, required_prefix=originals[0])
    before = journals.finalization_prefix(journal, physical_slot)
    position = journal.positions[physical_slot - 1]
    request = decode_request_source(position.decoded.sections[0])
    _require(
        type(consumer_index) is int and 0 <= consumer_index < prefix.metadata.target,
        "finalization event in original selected source prefix",
    )
    event = prefix.events[consumer_index]
    _require(
        event.actor == actor
        and event.action == "ACT-ISC-FINALIZE"
        and (
            event.original == position.original
            or (event.original == request.command_bytes and position.original in event.inputs)
        ),
        "original own finalization invocation/record association",
    )
    retained = source_prefix.retained_cut(
        prefix,
        original_prior_index,
        request.source_index_id,
        request.source_cut_event_index,
        consumer_index,
    )
    own = [
        (metadata.load(descriptor), raw)
        for descriptor, raw in retained.journals
        if (metadata.load(descriptor)["actor_id"], metadata.load(descriptor)["journal_id"])
        == (actor, journal_id)
    ]
    _require(len(own) == 1 and own[0][1] == before, "exact retained own pre-finalization WAL")
    folded = commands.prefix(
        bootstrap.formal_semantics_id,
        initial_state,
        initial_tick,
        before,
        cut_slot=physical_slot - 1,
        required_prefix=before,
    )
    journals.verify_inventory_row(folded.journal, own[0][0])
    received = source_prefix.isc_inventory(retained, bootstrap, backend, actor, body.round_id)
    _require(not received.unresolved, "complete original delivery source inputs required")
    native = read_state(folded.target.state, bootstrap.formal_semantics_id)
    cut = finalization.Cut(
        content_id("deltareduce:003:round-state:v1", folded.target.state),
        native["parent_checkpoint_id"],
        int(native["height"]),
        int(native["view"]),
        logical_tick,
        frozen_inputs,
        received.admitted,
    )
    prior = Predecessor(
        before, retained.index_id, retained.inclusive_cut, folded.target.state, original_policy, cut
    )
    result = bind(bootstrap, backend, position.original, prior, body)
    return IndexedCapsule(result, retained, received, folded)


@dataclass(frozen=True)
class InputBoundCapsule:
    capsule: IndexedCapsule
    input_source: object
    configuration_header: object


def bind_input_indexed(
    authorities,
    backend,
    prefix,
    *,
    journal_id,
    physical_slot,
    consumer_index,
    original_prior_index,
    initial_state,
    initial_tick,
    original_policy,
    logical_tick,
    plan,
    original_config,
    declaration,
):
    """Derive the full closed B/tuples from the same original retained W1 cut.

    This removes caller-selected body/tuple lists from this composition. It
    does not remove the remaining genesis, complete P0, producer/control and
    full configuration origin obligations. There is no R2 success premise.
    """
    from formal.reference.profile_source import (
        authority,
        configuration,
        configuration_history,
        input_history,
        metadata,
        source_prefix,
    )

    resolved = authority.resolve(
        prefix.metadata,
        authorities.original_validator_keys,
        authorities.original_storage_registry,
        authorities.original_storage_keys,
    )
    _require(resolved == authorities, "exact independent profile authority sources")
    boot = metadata.validate(prefix.metadata.bootstrap_bytes, "BOOTSTRAP")
    actor = boot["local_validator_id"]
    own = [
        raw
        for a, name, raw in prefix.metadata.original_own_journals
        if (a, name) == (actor, journal_id)
    ]
    _require(len(own) == 1, "one original own journal")
    journal = journals.inspect(own[0], cut_slot=0, required_prefix=own[0])
    _require(
        type(physical_slot) is int and 1 <= physical_slot <= len(journal.positions),
        "original finalization physical position",
    )
    frame = journal.positions[physical_slot - 1].decoded
    _require(frame.kind == 3, "original finalization kind")
    request = decode_request_source(frame.sections[0])
    cut = source_prefix.retained_cut(
        prefix,
        original_prior_index,
        request.source_index_id,
        request.source_cut_event_index,
        consumer_index,
    )
    inputs = input_history.reconstruct(
        cut.events,
        resolved.validators,
        resolved.storage,
        backend,
        plan,
        original_config,
        declaration,
        actor=actor,
    )
    _require(not inputs.unresolved, "complete original input source at retained cut")
    command = read_command(request.command_bytes, resolved.validators.formal_semantics_id)
    from formal.reference.isc_source.identity import body_id

    selected = tuple(row for row in inputs.closed if body_id(row.body) == command["body_hash"])
    _require(
        bool(selected) and all(row.body == selected[0].body for row in selected),
        "original closed body at exact source cut",
    )
    body = selected[0].body
    bound = bind_indexed(
        resolved.validators,
        backend,
        prefix,
        journal_id=journal_id,
        physical_slot=physical_slot,
        consumer_index=consumer_index,
        original_prior_index=original_prior_index,
        initial_state=initial_state,
        initial_tick=initial_tick,
        original_policy=original_policy,
        logical_tick=logical_tick,
        frozen_inputs=body.tuples,
        body=body,
    )
    finalized = configuration_history.finalized_config(inputs.configuration, body.round_config_id)
    header = configuration.bind_native_header(
        finalized.bound.config,
        bound.bound.predecessor.native_state,
        bound.bound.predecessor.policy,
        actor,
    )
    return InputBoundCapsule(bound, inputs, header)
