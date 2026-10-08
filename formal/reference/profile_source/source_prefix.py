"""Original Profile-v1 event materialization and CONFIG producer projection.

The source index is authenticated by check_metadata's independent custody pin.
No event is manufactured from a certificate, public state or signature. Every
original occurrence and ordered input is retained, even when its protocol
handler is not CONFIG. This is not a complete all-action legality checker.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_crypto.codec import CodecError, _require
from formal.reference.isc_crypto.sodium_reference import SodiumReference
from formal.reference.isc_source import authentication as isc_auth
from formal.reference.isc_source import budget as isc_budget
from formal.reference.isc_source import finalization as isc_final
from formal.reference.isc_source import identity as isc_identity
from formal.reference.isc_w1 import codec as wal
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import configuration_history as history
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source.availability_ledger import Occurrence


@dataclass(frozen=True)
class Event:
    index: int
    actor: str
    action: str
    original: bytes
    inputs: tuple[bytes, ...]
    dependencies: tuple[int, ...]
    original_descriptor: bytes

    def occurrence(self):
        return Occurrence(self.index, self.actor, self.original)


@dataclass(frozen=True)
class Prefix:
    metadata: m.Metadata
    genesis: bytes
    # Complete source inventory, including events beyond the selected target.
    events: tuple[Event, ...]

    @property
    def before_cut(self):
        return self.events[: self.metadata.cut]

    @property
    def before_target(self):
        return self.events[: self.metadata.target]


def _materialize(meta: m.Metadata, source):
    store = dict(meta.original_artifacts)
    descriptors = {r["content_id"]: r for r in source["artifacts"]}

    def resolve(reference):
        m.reference(reference)
        raw = store.get(reference["content_id"])
        _require(
            descriptors.get(reference["content_id"]) == reference
            and type(raw) is bytes
            and len(raw) == int(reference["byte_length"])
            and m.raw_id(raw) == reference["content_id"],
            "complete exact original source reference",
        )
        return raw

    events = tuple(
        Event(
            i,
            row["actor_id"],
            row["action_id"],
            resolve(row["original_ref"]),
            tuple(resolve(r) for r in row["input_refs"]),
            tuple(map(int, row["dependencies"])),
            m.canonical(row),
        )
        for i, row in enumerate(source["events"])
    )
    # Materialize all original refs, including retained but currently unused
    # artifacts. The enclosing producer determines their legal creation/use.
    for row in source["artifacts"]:
        resolve(row)
    for row in source["original_journal_refs"]:
        resolve(row["ref"])
    return resolve(source["genesis_ref"]), events


def materialize(meta: m.Metadata) -> Prefix:
    _require(type(meta) is m.Metadata, "checked original profile metadata required")
    source = m.validate(meta.source_index_bytes, "SOURCE_INDEX")
    genesis, events = _materialize(meta, source)
    _require(0 <= meta.cut <= meta.target <= len(events), "exact source prefix cuts")
    return Prefix(meta, genesis, events)


@dataclass(frozen=True)
class RetainedCut:
    original_index: bytes
    index_id: str
    # W1's cut is an inclusive original event index. Profile manifest cut/target
    # counts are prefix lengths. Never use one as the other without +1.
    inclusive_cut: int
    before_event: int
    events: tuple[Event, ...]
    # Original journal descriptors and bytes, without a fabricated empty journal.
    journals: tuple[tuple[bytes, bytes], ...]


def retained_cut(prefix: Prefix, original_index, index_id, inclusive_cut, before_event):
    """Bind an already retained W1 source cut to the complete Profile inventory.

    W1 §4's source bundle precedes finalization. It is not the later complete
    index that also references the new capsule. This verifies original index,
    event order/multiplicity and journal byte prefixes; it does not infer native
    event legality, barrier success or complete journal decoding from hashes.
    """
    meta = prefix.metadata
    _require(
        type(original_index) is bytes
        and dict(meta.original_artifacts).get(m.raw_id(original_index)) == original_index,
        "independently retained original pre-finalization source index",
    )
    old = m.validate(original_index, "SOURCE_INDEX")
    current = m.validate(meta.source_index_bytes, "SOURCE_INDEX")
    _require(
        index_id == m.document_id(original_index, "SOURCE_INDEX"),
        "exact domain-separated original source-index identity",
    )
    _require(
        all(
            old[key] == current[key]
            for key in ("origin_id", "validator_epoch_id", "local_validator_id", "genesis_ref")
        ),
        "same independently pinned source origin/epoch/identity/genesis",
    )
    _, events = _materialize(meta, old)
    _require(
        type(inclusive_cut) is int
        and type(before_event) is int
        and 0 <= inclusive_cut < len(events) <= before_event < len(prefix.events),
        "retained source cut precedes its consuming finalization",
    )
    _require(
        events == prefix.events[: len(events)],
        "whole original event prefix including actors/dependencies/multiplicity",
    )
    originals = dict(meta.original_artifacts)
    current_rows = {
        (row["actor_id"], row["journal_id"]): row for row in current["original_journal_refs"]
    }
    retained = []
    for row in old["original_journal_refs"]:
        target = current_rows.get((row["actor_id"], row["journal_id"]))
        _require(target is not None, "original journal identity retained at target")
        raw, tip = originals[row["ref"]["content_id"]], originals[target["ref"]["content_id"]]
        count, total = int(row["entry_count"]), int(target["entry_count"])
        _require(
            tip.startswith(raw)
            and count <= total
            and (count == 0 or row["first_sequence"] == target["first_sequence"]),
            "original journal byte/sequence prefix, never a synthesized history",
        )
        retained.append((m.canonical(row), raw))
    return RetainedCut(
        original_index,
        index_id,
        inclusive_cut,
        before_event,
        events[: inclusive_cut + 1],
        tuple(retained),
    )


def dependency_inputs(events, event):
    """Only this occurrence's actual inputs and prior dependency inputs.

    The original order/multiplicity remains on every Event. This lookup visits
    dependencies once for byte resolution; it does not replace the event list
    or merge any delivery/vote identity. No later bundle artifact is a fallback.
    """
    _require(events[event.index] == event, "exact original event position")
    selected, pending, visited = [*event.inputs], list(event.dependencies), set()
    while pending:
        index = pending.pop()
        _require(type(index) is int and 0 <= index < event.index, "backward source dependency")
        if index in visited:
            continue
        visited.add(index)
        original = events[index]
        _require(
            original.index == index and all(0 <= i < index for i in original.dependencies),
            "complete original dependency positions",
        )
        selected.extend((original.original, *original.inputs))
        pending.extend(original.dependencies)
    return tuple(selected)


class MissingInput(CodecError):
    """An authentic received object lacks its original required source input.

    This is an incomplete source check, not an invalid Vote and not permission
    to silently omit that delivery from an otherwise qualifying W1 inventory.
    """


def signed_isc_occurrence(events, event, bootstrap, backend):
    """Re-read the existing inline W1 delivery fields and their original G/B.

    Inline records use precisely W1's existing bytes; no new transport envelope,
    certificate, source authority or protocol ID is defined here. The native
    source fold still establishes producer/transport admission and local phase.
    """
    delivery = wal.decode_delivery(event.original)
    if delivery.event_index != event.index:
        raise MissingInput("original delivery/source position mismatch")
    registry_id, key_id, vote_raw = crypto.decode_preimage(delivery.signed_payload)
    _require(
        vote_raw == delivery.vote_frame and key_id == delivery.key_id,
        "original inline delivery material",
    )
    vote = crypto.decode_vote(vote_raw)
    expected, keys = isc_auth.registry(bootstrap)
    _require(
        type(backend) is SodiumReference and registry_id == expected and vote.validator_id in keys,
        "independent original validator registry/backend",
    )
    enrolled_key, public = keys[vote.validator_id]
    _require(
        key_id == enrolled_key
        and vote.validator_epoch_id == bootstrap.validator_epoch_id
        and vote.formal_semantics_id == bootstrap.formal_semantics_id
        and backend.verify(public, delivery.signed_payload, delivery.signature_bytes),
        "strict original ISC signature/key/epoch",
    )
    raw_g = crypto.encode_artifact(
        crypto.Artifact(registry_id, key_id, vote_raw, delivery.signature_bytes)
    )
    inputs = dependency_inputs(events, event)
    if raw_g not in inputs:
        raise MissingInput("authentic delivery missing original G input")
    bodies = []
    for raw in inputs:
        try:
            body = isc_identity.decode_body_preimage(raw)
        except CodecError:
            continue
        if isc_identity.body_id(body) == vote.body_hash:
            bodies.append(body)
    if not bodies:
        raise MissingInput("authentic delivery missing original B input")
    if not all(body == bodies[0] for body in bodies):
        raise MissingInput("original body identity collision")
    verified = isc_auth.authenticate(bootstrap, backend, raw_g, bodies[0])
    isc_auth.bind_delivery(verified, delivery)
    return isc_final.DeliverySource(delivery, raw_g, bodies[0])


@dataclass(frozen=True)
class DeliveryInventory:
    source: RetainedCut
    actor: str
    round_id: str
    admitted: tuple[isc_final.DeliverySource, ...]
    # Every original occurrence stays here, including invalid/foreign/repeated
    # messages. Unhandled and missing-input cases are not source qualifications.
    outcomes: tuple[tuple[int, str], ...]
    unresolved: tuple[Event, ...]


def isc_inventory(cut: RetainedCut, bootstrap, backend, actor, round_id):
    """Compute full original admitted ISC inventory, without selecting first-q.

    This is the received-byte/budget facet. It is not proof that every original
    event is legal, that an actor persisted a first vote, or that W1 is durable.
    """
    admitted, outcomes, unresolved = [], [], []
    for event in cut.events:
        if event.action != "ACT-MESSAGE-DELIVER" or event.actor != actor:
            outcomes.append((event.index, "other_source_action_or_actor"))
            continue
        try:
            source = signed_isc_occurrence(cut.events, event, bootstrap, backend)
        except MissingInput:
            unresolved.append(event)
            outcomes.append((event.index, "missing_original_input"))
            continue
        except wal.CodecError:
            # Other protocol/transport source encodings need their own handler;
            # failed inline parsing alone cannot prove a rejected native event.
            unresolved.append(event)
            outcomes.append((event.index, "other_delivery_encoding_requires_handler"))
            continue
        except CodecError:
            outcomes.append((event.index, "rejected_isc_bytes_or_signature"))
            continue
        if source.original_body.round_id != round_id:
            outcomes.append((event.index, "other_original_round"))
            continue
        try:
            isc_budget.inventory_size(
                tuple(row.event for row in (*admitted, source)),
                round_id,
                bootstrap.validator_epoch_id,
            )
        except CodecError:
            outcomes.append((event.index, "rejected_admission_budget"))
            continue
        admitted.append(source)
        outcomes.append((event.index, "admitted_original_isc"))
    return DeliveryInventory(
        cut, actor, round_id, tuple(admitted), tuple(outcomes), tuple(unresolved)
    )


def declaration_for(event: Event, bound_config: bytes) -> bytes:
    """R selects E by exact raw bytes/length/epoch, never by source list position."""
    body = cfg.decode(bound_config)
    ref = body["availability_policy"]["storage_binding"]["retention_policy_source"][
        "obligation_ref"
    ]
    candidates = tuple(
        raw
        for raw in event.inputs
        if len(raw) == int(ref["byte_length"]) and m.raw_id(raw)[7:] == ref["sha256"]
    )
    _require(bool(candidates), "original E missing at proposal input cut")
    _require(all(raw == candidates[0] for raw in candidates), "retention digest collision")
    # Repeated original input occurrences remain on Event.inputs. Returning the
    # bytes for verification neither merges those occurrences nor rewrites R.
    return candidates[0]


@dataclass(frozen=True)
class ConfigPrefix:
    source: Prefix
    cut: history.History
    target: history.History
    # Explicit coverage inventory. These actions need their own producer rules;
    # this result must not be used as a complete prefix-admission certificate.
    other_actions: tuple[Event, ...]


def configuration_prefix(prefix: Prefix, validators, storage, backend) -> ConfigPrefix:
    state = history.History()
    cut, other = state if prefix.metadata.cut == 0 else None, []
    for event in prefix.before_target:
        occurrence = event.occurrence()
        if event.action == "ACT-CONFIG-PROPOSE":
            try:
                declaration = declaration_for(event, event.original)
            except CodecError:
                # Malformed or incomplete attempts are original occurrences,
                # not fabricated proposals and not permission to drop history.
                state = history.observed(state, occurrence)
            else:
                state = history.propose(state, occurrence, validators, storage, declaration).state
        elif event.action == "ACT-CONFIG-FINALIZE":
            state = history.finalize(state, occurrence, validators, storage, backend).state
        elif event.action == "ACT-MESSAGE-DELIVER":
            state = history.deliver(state, occurrence, validators, backend).state
        else:
            other.append(event)
            state = history.observed(state, occurrence)
        if event.index + 1 == prefix.metadata.cut:
            cut = state
    _require(cut is not None, "original snapshot cut not reached")
    _require(
        tuple(e.original for e in state.events) == tuple(e.original for e in prefix.before_target),
        "source occurrence preservation",
    )
    return ConfigPrefix(prefix, cut, state, tuple(other))
