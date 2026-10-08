"""O input use: original full bytes, owned buffers, loss and process lifetime.

No storage statement, AC, successful callback, pathname or old read receipt can
populate this state. The enclosing source fold supplies original occurrences
and complete original metadata; this component validates the actual byte input.
Buffer coordinates are source positions, never new protocol object identities.
The arithmetic operation and its durable vote still need their own producer rule.
"""

from dataclasses import dataclass, replace

from formal.reference.isc_crypto.codec import CodecError, _require
from formal.reference.profile_source import manifest_context as manifests
from formal.reference.profile_source.availability_ledger import Occurrence
from formal.scripts.native_source_artifacts import SourceError


@dataclass(frozen=True)
class Buffer:
    source: Occurrence
    manifest: manifests.Metadata
    # Complete corpus in the original manifest's order, not an observed subset.
    shards: tuple[manifests.DataUse, ...]


@dataclass(frozen=True)
class Observation:
    source: Occurrence
    kind: str
    manifest_id: str | None
    original_inputs: tuple[bytes, ...]
    disposition: str
    target_read: int | None = None


@dataclass(frozen=True)
class State:
    owned: tuple[Buffer, ...] = ()
    observations: tuple[Observation, ...] = ()


def append(state, event, kind, manifest_id, originals, disposition, target_read=None):
    _require(type(state) is State and type(event) is Occurrence, "original input occurrence")
    _require(type(event.index) is int and event.index >= 0, "original input position")
    _require(type(event.original) is bytes, "complete original input event")
    _require(type(event.actor) is str and bool(event.actor), "original input actor")
    _require(event.index == len(state.observations), "complete original source prefix positions")
    _require(
        type(originals) is tuple and all(type(raw) is bytes for raw in originals),
        "immutable complete byte inputs",
    )
    return replace(
        state,
        observations=(
            *state.observations,
            Observation(event, kind, manifest_id, originals, disposition, target_read),
        ),
    )


def read_complete(state, event, originals, semantics, manifest_id, actual):
    """Validate every actual shard before the complete corpus becomes usable.

    An invalid read remains an observation and does not partially insert good
    prefixes. A failed later read does not mutate an already owned immutable
    buffer. Discard/restart, not a claim about external disk, ends ownership.
    """
    _require(type(actual) is tuple and all(type(x) is bytes for x in actual), "actual read bytes")
    try:
        metadata = manifests.resolve(originals, semantics, manifest_id)
        _require(len(actual) == len(metadata.required_leaves), "complete original input corpus")
        checked = tuple(
            manifests.read_q(originals, semantics, manifest_id, i, raw)
            for i, raw in enumerate(actual)
        )
    except (CodecError, SourceError):
        return append(state, event, "READ", manifest_id, actual, "rejected_bytes")
    following = append(state, event, "READ", manifest_id, actual, "verified_owned")
    return replace(following, owned=(*state.owned, Buffer(event, metadata, checked)))


def failed_read(state, event, manifest_id):
    """A local failure observation proves no global absence and changes no AC."""
    return append(state, event, "READ_FAILURE", manifest_id, (), "no_new_buffer")


def other_event(state, event, originals=()):
    """The complete source fold retains unrelated events without claiming them valid."""
    return append(state, event, "OTHER", None, originals, "other_handler_required")


def release(state, event, original_read_index):
    selected = tuple(
        b
        for b in state.owned
        if b.source.actor == event.actor and b.source.index == original_read_index
    )
    _require(len(selected) == 1, "owned original buffer required for release")
    following = append(
        state,
        event,
        "RELEASE",
        selected[0].manifest.manifest_id,
        (),
        "released",
        original_read_index,
    )
    return replace(following, owned=tuple(b for b in state.owned if b != selected[0]))


def process_lost(state, event):
    """Crash/restart cannot revive a volatile original buffer from a read ID."""
    following = append(state, event, "PROCESS_LOST", None, (), "volatile_buffers_discarded")
    return replace(following, owned=tuple(b for b in state.owned if b.source.actor != event.actor))


def external_loss(state, event, manifest_id):
    """External loss/corruption is retained; it cannot mutate retained bytes.

    This records the given event, not a truthful complete physical-history oracle.
    Hidden physical events are permitted by O and imply no certified fact here.
    """
    return append(state, event, "EXTERNAL_LOSS", manifest_id, (), "retained")


def at_use(state, actor, original_read_index, manifest_id):
    """Select the same still-owned bytes, never resolve a path or fetch a subset."""
    _require(type(state) is State, "original observation state")
    found = tuple(
        b
        for b in state.owned
        if b.source.actor == actor
        and b.source.index == original_read_index
        and b.manifest.manifest_id == manifest_id
    )
    _require(len(found) == 1, "same actor still owns this exact complete original buffer")
    return found[0]


def verify_state(state, originals, semantics):
    """Re-derive every surviving buffer from its original successful read.

    This supports import checking; constructing a dataclass is not authority.
    Equality with this fold is necessary, but original occurrence/authenticity
    and interleaving with the rest of the producer prefix are separate joins.
    """
    rebuilt = State()
    for item in state.observations:
        if item.kind == "READ":
            rebuilt = read_complete(
                rebuilt, item.source, originals, semantics, item.manifest_id, item.original_inputs
            )
        elif item.kind == "READ_FAILURE":
            rebuilt = failed_read(rebuilt, item.source, item.manifest_id)
        elif item.kind == "PROCESS_LOST":
            rebuilt = process_lost(rebuilt, item.source)
        elif item.kind == "EXTERNAL_LOSS":
            rebuilt = external_loss(rebuilt, item.source, item.manifest_id)
        elif item.kind == "RELEASE":
            rebuilt = release(rebuilt, item.source, item.target_read)
        elif item.kind == "OTHER":
            rebuilt = other_event(rebuilt, item.source, item.original_inputs)
        else:
            raise CodecError("unknown input observation")
        _require(rebuilt.observations[-1] == item, "original observation result differs")
    _require(rebuilt == state, "imported owned buffers not derived from originals")
    return rebuilt
