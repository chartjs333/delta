"""T047/T053: selected isolated EC companion bytes and durability machine.

This is not a filesystem adapter or a legacy WAL format. The complete producing
fold supplies the original cut, admitted rows and journal cuts; neither a hash
nor this component certifies their origin. Barrier actions model the existing
Profile T primitive, not a caller-provided `durable` field in an imported record.
"""

from dataclasses import dataclass, replace
from hashlib import sha256

from formal.reference.isc_crypto.codec import _decimal, _id, _require, _uint
from formal.reference.isc_source.authentication import registry
from formal.reference.profile_source import ec_finalization as ec
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import source_prefix as source

JOURNAL = "PROFILE-EC-COMMIT-V1"
DOMAIN = b"deltareduce.profile.ec-commit.record.v1\0"
SOURCE_DOMAIN = b"deltareduce.profile.ec-commit.source.v1\0"
JOURNAL_DOMAIN = b"deltareduce.profile.ec-commit.journals.v1\0"
FIELDS = frozenset(
    "type_name schema_version profile_id bootstrap_id actor_id ordinal previous_record_id "
    "event_index source_prefix_id event_raw_id prior_policy_raw_id next_policy_raw_id "
    "round_state_raw_id certificate_raw_id seed_raw_id journal_prefix_id".split()
)
HASH_FIELDS = FIELDS - {
    "type_name",
    "schema_version",
    "profile_id",
    "actor_id",
    "ordinal",
    "event_index",
    "previous_record_id",
}


def identifier(domain, raw):
    return "sha256:" + sha256(domain + raw).hexdigest()


def decode(raw):
    row = m.closed(m.load(raw), FIELDS)
    _require(
        row["type_name"] == "EC_COMMIT"
        and row["schema_version"] == "1"
        and row["profile_id"] == m.PROFILE,
        "isolated EC record dispatch/profile",
    )
    m.text(row["actor_id"], nonempty=True)
    ordinal, event = _decimal(row["ordinal"]), _decimal(row["event_index"])
    _require(
        1 <= ordinal <= m.MAX_RECORDS and 1 <= event < m.MAX_EVENTS,
        "original companion ordinal/source event bounds",
    )
    for name in HASH_FIELDS:
        _id(row[name])
    if ordinal == 1:
        _require(row["previous_record_id"] == "GENESIS", "first companion predecessor")
    else:
        _id(row["previous_record_id"])
    return row


def frame(raw):
    decode(raw)
    return _uint(len(raw), 4) + raw + sha256(DOMAIN + raw).digest()


@dataclass(frozen=True)
class Record:
    raw: bytes
    original_frame: bytes

    @property
    def id(self):
        return identifier(DOMAIN, self.raw)

    @property
    def fields(self):
        return decode(self.raw)


def scan(original):
    """Complete original journal only. A torn/unknown tail is never ignored."""
    _require(type(original) is bytes, "original companion bytes required")
    rows, at, last_event = [], 0, -1
    while at < len(original):
        _require(
            len(rows) < m.MAX_RECORDS and len(original) - at >= 4,
            "companion count or truncated length",
        )
        size = int.from_bytes(original[at : at + 4], "big")
        _require(
            size <= m.MAX_CONTROL and at + 4 + size + 32 <= len(original),
            "complete bounded companion frame",
        )
        raw = original[at + 4 : at + 4 + size]
        whole = original[at : at + 4 + size + 32]
        _require(frame(raw) == whole, "exact original frame/digest")
        record = Record(raw, whole)
        value = record.fields
        _require(int(value["ordinal"]) == len(rows) + 1, "original contiguous ordinal")
        _require(
            value["previous_record_id"] == (rows[-1].id if rows else "GENESIS"),
            "original preceding record identity",
        )
        _require(last_event < int(value["event_index"]), "strict original finalization order")
        if rows:
            before = rows[-1].fields
            _require(
                all(before[k] == value[k] for k in ("bootstrap_id", "actor_id")),
                "same independent bootstrap/local journal owner",
            )
        rows.append(record)
        last_event = int(value["event_index"])
        at += len(whole)
    return tuple(rows)


def source_digest(bootstrap_id, descriptors):
    _id(bootstrap_id)
    _require(
        type(descriptors) is tuple and len(descriptors) < m.MAX_EVENTS,
        "complete original source prefix carrier",
    )
    h = sha256(SOURCE_DOMAIN + bootstrap_id.encode("ascii") + _uint(len(descriptors), 8))
    for index, original in enumerate(descriptors):
        # Descriptors are exact original canonical objects. Their full field,
        # reference and dependency interpretation belongs to Index/materialize.
        _require(type(m.load(original)) is dict, "original descriptor object")
        h.update(_uint(index, 8) + _uint(len(original), 4) + original)
    return "sha256:" + h.hexdigest()


def journal_digest(cuts):
    m.cuts(cuts)
    return identifier(JOURNAL_DOMAIN, m.canonical(cuts))


def companion_cut(cuts, actor, original):
    """Bind our prior companion when present; never invent an empty inventory.

    Other cut rows and their source bytes remain the enclosing fold's checks.
    A previously absent companion may have no inventory row. An explicit empty
    row, if present, must bind the exact empty bytes/count, not a guessed prefix.
    """
    m.cuts(cuts)
    rows = scan(original)
    selected = [row for row in cuts if (row["actor_id"], row["journal_id"]) == (actor, JOURNAL)]
    _require(not original or len(selected) == 1, "prior companion missing from original cuts")
    if selected:
        row = selected[0]
        _require(
            row["ref"]["content_id"] == m.raw_id(original)
            and int(row["ref"]["byte_length"]) == len(original)
            and int(row["entry_count"]) == len(rows)
            and int(row["first_sequence"]) == (1 if rows else 0)
            and int(row["last_sequence"]) == len(rows),
            "prior companion cut covers all original records/bytes",
        )
    return rows


def event_descriptor(event):
    row = m.closed(
        m.load(event.original_descriptor),
        {"actor_id", "action_id", "original_ref", "input_refs", "dependencies"},
    )
    _require(
        row["actor_id"] == event.actor and row["action_id"] == event.action,
        "original descriptor actor/action",
    )
    _require(
        type(row["input_refs"]) is list and len(row["input_refs"]) == len(event.inputs),
        "all original ordered input descriptors",
    )
    for reference, original in zip(
        [row["original_ref"], *row["input_refs"]], (event.original, *event.inputs), strict=True
    ):
        m.reference(reference)
        _require(
            reference["content_id"] == m.raw_id(original)
            and int(reference["byte_length"]) == len(original),
            "descriptor binds exact whole original bytes",
        )
    _require(
        type(row["dependencies"]) is list
        and tuple(_decimal(x) for x in row["dependencies"]) == event.dependencies,
        "descriptor retains all dependency positions",
    )
    return event.original_descriptor


@dataclass(frozen=True)
class Bound:
    candidate: ec.Candidate
    event: source.Event
    original_prefix: tuple[bytes, ...]
    original_journal_cuts: bytes
    prior_companion: bytes
    record: Record


def compute(
    authority,
    backend,
    bootstrap_id,
    original_event,
    original_descriptors,
    journal_cuts,
    prior_companion,
    original_rows,
    original_tick,
    prerequisite_positions,
):
    """Compute, do not accept supplied E/P1/durable or public success.

    This is the storage-association conjunct. The enclosing full producing fold
    must derive all rows/cuts/origins, match the bootstrap to Profile authority,
    and resolve every original journal/ref. It must not call this with a guessed
    prefix and portray the result as a verified full native history.
    """
    _require(
        type(original_event) is source.Event and len(original_event.inputs) == 6,
        "original six-input EC event",
    )
    e = original_event
    _require(len(original_descriptors) == e.index, "all original pre-event occurrences")
    _require(type(original_rows) is tuple, "complete admitted inventory carrier")
    # Re-observation may have later deliveries. The transaction is evaluated at
    # its original temporal cut; later occurrences remain in the outer full
    # source inventory and cannot change this record or its signer set.
    at_cut = tuple(row for row in original_rows if row.position < e.index)
    prior, state, body, parent, seed, norm = e.inputs
    candidate = ec.assemble_first(
        authority,
        backend,
        prior,
        state,
        body,
        at_cut,
        actor=e.actor,
        cut=e.index - 1,
        tick=original_tick,
    )
    ec.bind_event(candidate, e, parent, seed, norm, prerequisite_positions)
    event_descriptor(e)
    previous = companion_cut(journal_cuts, e.actor, prior_companion)
    if previous:
        last = previous[-1].fields
        _require(
            last["bootstrap_id"] == bootstrap_id
            and last["actor_id"] == e.actor
            and int(last["event_index"]) < e.index,
            "same original companion context/cut",
        )
    fields = {
        "type_name": "EC_COMMIT",
        "schema_version": "1",
        "profile_id": m.PROFILE,
        "bootstrap_id": bootstrap_id,
        "actor_id": e.actor,
        "ordinal": str(len(previous) + 1),
        "previous_record_id": previous[-1].id if previous else "GENESIS",
        "event_index": str(e.index),
        "source_prefix_id": source_digest(bootstrap_id, original_descriptors),
        "event_raw_id": m.raw_id(e.original_descriptor),
        "prior_policy_raw_id": m.raw_id(candidate.prior_policy),
        "next_policy_raw_id": m.raw_id(candidate.next_policy),
        "round_state_raw_id": m.raw_id(candidate.original_state),
        "certificate_raw_id": m.raw_id(candidate.certificate),
        "seed_raw_id": m.raw_id(seed),
        "journal_prefix_id": journal_digest(journal_cuts),
    }
    raw = m.canonical(fields)
    return Bound(
        candidate,
        e,
        original_descriptors,
        m.canonical(journal_cuts),
        prior_companion,
        Record(raw, frame(raw)),
    )


def bind_original(bound, original_frame):
    _require(
        type(bound) is Bound and type(original_frame) is bytes,
        "computed binding and original frame",
    )
    _require(original_frame == bound.record.original_frame, "whole computed original EC frame")
    return bound


@dataclass(frozen=True)
class Indexed:
    binding: Bound
    original_cut: source.RetainedCut
    complete_own_journal: bytes
    original_records: tuple[Record, ...]


def bind_profile(
    prefix,
    authority,
    backend,
    event_index,
    original_index,
    original_rows,
    original_tick,
    prerequisite_positions,
):
    """Join actual Profile T metadata, retained cut and original EC record.

    Metadata does NOT imply lawful history. The full producing fold still
    supplies the admitted rows/clock/origins; this function derives the source
    prefix, bootstrap ID and companion cut from checked original bytes instead
    of allowing free or shorter caller-provided inventories.
    """
    _require(type(prefix) is source.Prefix, "materialized complete original Profile input")
    meta = prefix.metadata
    boot = m.validate(meta.bootstrap_bytes, "BOOTSTRAP")
    native = authority.bootstrap
    _, keys = registry(native)
    _require(
        (native.formal_semantics_id, native.origin_id, native.validator_epoch_id)
        == (boot["formal_semantics_id"], boot["origin_id"], boot["validator_epoch_id"])
        and [(name, key) for name, (key, _) in keys.items()]
        == [(row["validator_id"], row["key_ref"]) for row in boot["validators"]],
        "same independently selected Profile validator authority",
    )
    _require(type(event_index) is int and 0 < event_index < meta.target, "original target event")
    event = prefix.events[event_index]
    _require(event.actor == boot["local_validator_id"], "own original EC producer")
    retained = source.retained_cut(
        prefix,
        original_index,
        m.document_id(original_index, "SOURCE_INDEX"),
        event_index - 1,
        event_index,
    )
    cuts = [m.load(row) for row, _ in retained.journals]
    own_cut = [
        raw
        for row, raw in retained.journals
        if (m.load(row)["actor_id"], m.load(row)["journal_id"]) == (event.actor, JOURNAL)
    ]
    _require(len(own_cut) <= 1, "unique own companion cut")
    prior = own_cut[0] if own_cut else b""
    binding = compute(
        authority,
        backend,
        m.document_id(meta.bootstrap_bytes, "BOOTSTRAP"),
        event,
        tuple(row.original_descriptor for row in retained.events),
        cuts,
        prior,
        original_rows,
        original_tick,
        prerequisite_positions,
    )
    candidates = [
        raw
        for actor, journal, raw in meta.original_own_journals
        if (actor, journal) == (event.actor, JOURNAL)
    ]
    _require(len(candidates) == 1, "complete original own companion from independent T")
    full = candidates[0]
    index = m.validate(meta.source_index_bytes, "SOURCE_INDEX")
    all_records = companion_cut(index["original_journal_refs"], event.actor, full)
    ordinal = int(binding.record.fields["ordinal"])
    _require(ordinal <= len(all_records), "original EC companion record unavailable")
    bind_original(binding, all_records[ordinal - 1].original_frame)
    _require(
        b"".join(row.original_frame for row in all_records[: ordinal - 1]) == prior,
        "retained cut is exact whole original companion prefix",
    )
    return Indexed(binding, retained, full, all_records)


@dataclass(frozen=True)
class Machine:
    """One computed EC transaction; full source fold remains the outer machine.

    `barrier` is a modeled successful T primitive, not an imported assertion.
    No filesystem/syscall or production-ready claim is made by this model.
    """

    binding: Bound
    native_wal: bytes
    volatile: bytes
    stable: bytes
    phase: str
    current_policy: bytes
    exposed: tuple[bytes, ...] = ()


def prepared(binding, native_wal):
    _require(type(binding) is Bound and type(native_wal) is bytes, "computed original transaction")
    return Machine(
        binding,
        native_wal,
        binding.prior_companion,
        binding.prior_companion,
        "PREPARED",
        binding.candidate.prior_policy,
    )


def append(state):
    _require(state.phase == "PREPARED", "append once after validation")
    return replace(
        state, volatile=state.volatile + state.binding.record.original_frame, phase="APPENDED"
    )


def barrier(state):
    _require(state.phase in ("APPENDED", "RECOVERY_VERIFIED"), "barrier after append/verification")
    _require(
        state.volatile == state.binding.prior_companion + state.binding.record.original_frame,
        "whole computed original pending bytes",
    )
    return replace(state, stable=state.volatile, phase="DURABLE")


def commit(state):
    _require(state.phase == "DURABLE", "commit only after successful barrier")
    _require(
        state.stable
        == state.volatile
        == state.binding.prior_companion + state.binding.record.original_frame,
        "commit exact complete durable transaction",
    )
    return replace(state, current_policy=state.binding.candidate.next_policy, phase="COMMITTED")


def expose(state):
    _require(state.phase == "COMMITTED", "no effect before barrier and commit")
    _require(
        state.stable == state.binding.prior_companion + state.binding.record.original_frame
        and state.current_policy == state.binding.candidate.next_policy,
        "expose exact committed transaction",
    )
    # Repeat returns the SAME original artifact; no new protocol identity/slot.
    return replace(state, exposed=(*state.exposed, state.binding.candidate.certificate))


def crash(state, surviving):
    """Explicit possible primitive outcomes, preserving every observed byte.

    Stable bytes must survive under Profile T. The unacknowledged region may
    contain arbitrary torn/out-of-order bytes, not just a prefix of the intended
    frame. No selection discards stable bytes or extends the attempted write.
    """
    _require(
        type(surviving) is bytes
        and surviving.startswith(state.stable)
        and len(surviving) <= len(state.volatile),
        "Profile stable prefix/write extent",
    )
    # current_policy/exposed are logical history, not a restart cache or storage
    # authority. A crash cannot erase a previously committed EC or its external
    # observations. Reconstructing runnable cache still needs recover/barrier.
    return replace(state, volatile=surviving, stable=surviving, phase="CRASHED")


def recover(state, recomputed):
    _require(state.phase == "CRASHED", "recovery after crash")
    _require(recomputed == state.binding, "independently recomputed original transaction")
    target = recomputed.prior_companion + recomputed.record.original_frame
    if state.volatile == target:
        # Re-verification does not prove the OLD barrier happened. A new
        # recovery barrier and commit are still required before exposure.
        scan(state.volatile)
        return replace(state, phase="RECOVERY_VERIFIED")
    if state.volatile == recomputed.prior_companion:
        return replace(state, phase="PREPARED")
    # Retain torn/unknown bytes, no truncate/empty-history fallback.
    return replace(state, phase="BLOCKED")
