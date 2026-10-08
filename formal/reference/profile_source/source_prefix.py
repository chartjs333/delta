"""Original Profile-v1 event materialization and CONFIG producer projection.

The source index is authenticated by check_metadata's independent custody pin.
No event is manufactured from a certificate, public state or signature. Every
original occurrence and ordered input is retained, even when its protocol
handler is not CONFIG. This is not a complete all-action legality checker.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto.codec import _require
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


def materialize(meta: m.Metadata) -> Prefix:
    _require(type(meta) is m.Metadata, "checked original profile metadata required")
    source = m.validate(meta.source_index_bytes, "SOURCE_INDEX")
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
    _require(0 <= meta.cut <= meta.target <= len(events), "exact source prefix cuts")
    return Prefix(meta, resolve(source["genesis_ref"]), events)


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
            state = history.propose(
                state,
                occurrence,
                validators,
                storage,
                declaration_for(event, event.original),
            ).state
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
