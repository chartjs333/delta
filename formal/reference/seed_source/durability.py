"""T047/T053 isolated seed companion and existing Profile T primitive model.

No file adapter, native WAL mutation, imported durable flag or trusted callback.
Complete source-index/barrier provenance remains an enclosing fold obligation;
constructing a Machine/Replay dataclass does not grant source authority.
"""

from dataclasses import dataclass, replace
from hashlib import sha256

from formal.reference.isc_crypto import codec as c
from formal.reference.profile_source import metadata as m
from formal.reference.seed_source import agreement as a
from formal.reference.seed_source import generation as gen
from formal.reference.seed_source import producer_guards as guards
from formal.reference.seed_source import pvss as p

JOURNAL = "PROFILE-SEED-PRODUCER-V1"
DOMAIN = b"deltareduce.profile.seed-producer.record.v1\0"
INSTANCE = b"deltareduce.profile.seed-producer.instance.v1\0"
KNOWLEDGE = b"deltareduce.profile.seed-producer.knowledge.v1\0"
FIELDS = set(
    "type_name schema_version profile_id bootstrap_id actor_id instance_id ordinal "
    "previous_record_id payload_raw_id payload_bytes knowledge_count knowledge_id "
    "intent_ordinal commit_ids".split()
)


def identifier(domain, raw):
    return "sha256:" + sha256(domain + raw).hexdigest()


def knowledge_id(originals):
    return identifier(
        KNOWLEDGE,
        len(originals).to_bytes(8, "big") + b"".join(p.frame(raw) for raw in originals),
    )


def instance_id(expected):
    return identifier(INSTANCE, c._json(a.instance(expected)))


def decode(raw):
    row = m.closed(m.load(raw), FIELDS)
    c._require(
        row["type_name"] in ("RECEIVE", "INTENT", "SIGNED")
        and row["schema_version"] == "1"
        and row["profile_id"] == m.PROFILE,
        "seed companion dispatch",
    )
    m.text(row["actor_id"], nonempty=True)
    for key in ("bootstrap_id", "instance_id", "payload_raw_id", "knowledge_id"):
        c._id(row[key])
    ordinal = c._decimal(row["ordinal"], positive=True)
    c._require(ordinal <= m.MAX_RECORDS, "existing whole Profile record budget")
    if ordinal == 1:
        c._require(row["previous_record_id"] == "GENESIS", "companion genesis")
    else:
        c._id(row["previous_record_id"])
    for key in ("payload_bytes", "knowledge_count", "intent_ordinal"):
        c._decimal(row[key])
    c._require(type(row["commit_ids"]) is list, "original commit references")
    for ident in row["commit_ids"]:
        c._id(ident)
    c._require(
        row["type_name"] == "INTENT" or not row["commit_ids"],
        "commit witnesses only on intent",
    )
    c._require(
        (row["type_name"] == "SIGNED") == (int(row["intent_ordinal"]) > 0),
        "signed record references original intent",
    )
    return row


def frame(raw):
    decode(raw)
    return len(raw).to_bytes(4, "big") + raw + sha256(DOMAIN + raw).digest()


def scan(original):
    """All bytes, all records. A corrupt/torn tail is an error, never truncated."""
    c._require(type(original) is bytes, "original companion bytes")
    rows, at = [], 0
    while at < len(original):
        c._require(len(original) - at >= 4, "torn seed frame length")
        length = int.from_bytes(original[at : at + 4], "big")
        end = at + 4 + length + 32
        c._require(length <= m.MAX_CONTROL and end <= len(original), "complete bounded frame")
        raw = original[at + 4 : end - 32]
        row = decode(raw)
        c._require(frame(raw) == original[at:end], "original seed frame digest")
        c._require(int(row["ordinal"]) == len(rows) + 1, "contiguous companion ordinal")
        previous = identifier(DOMAIN, rows[-1]) if rows else "GENESIS"
        c._require(row["previous_record_id"] == previous, "original companion predecessor")
        rows.append(raw)
        at = end
    return tuple(rows)


@dataclass(frozen=True)
class StoredIntent:
    ordinal: int
    body: bytes
    knowledge_count: int
    commit_ids: tuple[str, ...]
    key: tuple[str, str]


@dataclass(frozen=True)
class Replay:
    records: tuple[bytes, ...] = ()
    knowledge: tuple[bytes, ...] = ()
    intents: tuple[StoredIntent, ...] = ()
    signed: tuple[tuple[int, bytes], ...] = ()
    agreement_view: int = 0


def intent_key(body):
    if body.get("profile") == a.PROFILE:
        return body["kind"], body["agreement_view"]
    c._require(body.get("profile") == p.PROFILE, "selected seed purpose")
    return body["kind"], body.get("deal_id", "")


def check_intent(group, boot, expected, actor, before, original, commit_ids):
    body = c._load(original)
    evidence = a.Evidence(group, boot, expected, before.knowledge)
    if body.get("profile") == a.PROFILE:
        c._require(not commit_ids, "agreement intent has no OPEN witness")
        selected = tuple(
            guards.Intent(item.body, item.knowledge_count)
            for item in before.intents
            if c._load(item.body).get("profile") == a.PROFILE
        )
        state = guards.guard_sequence(
            group,
            boot,
            expected,
            actor,
            before.knowledge,
            (*selected, guards.Intent(original, len(before.knowledge))),
        )
        return intent_key(body), state.view
    context = body.get("context")
    c._require(
        type(context) is dict and a.instance(context) == a.instance(expected),
        "same original seed instance",
    )
    if body.get("kind") == "DEAL":
        c._require(not commit_ids, "DEAL has no OPEN witness")
        p.verify_unsigned(group, boot, context, original, actor)
    elif body.get("kind") == "OPEN":
        proposal = evidence.committed(list(commit_ids))
        c._require(body.get("deal_id") in proposal.deals, "OPEN only committed dealer selection")
        original_deal = evidence.deals[body["deal_id"]].original
        p.verify_unsigned(group, boot, context, original, actor, original_deal)
    else:
        raise c.CodecError("unknown unsigned seed purpose")
    return intent_key(body), before.agreement_view


def verified_signed(group, boot, expected, actor, before, intent, original):
    outer = c._closed(c._load(original), {"body", "signature"})
    c._require(outer["body"] == intent.body.hex(), "exact durable unsigned body")
    body = c._load(intent.body)
    prior = a.Evidence(group, boot, expected, before.knowledge[: intent.knowledge_count])
    if body["profile"] == a.PROFILE:
        checked = prior._read(original)
        c._require(type(checked) is a.Checked and checked.actor == actor, "own agreement artifact")
    elif body["kind"] == "DEAL":
        p.verify_deal(group, boot, body["context"], original)
    else:
        deal = prior.deals[body["deal_id"]].original
        p.verify_open(group, boot, body["context"], deal, original)


def advance(group, boot, expected, bootstrap_id, actor, before, raw, payload):
    row = decode(raw)
    c._require(
        row["bootstrap_id"] == bootstrap_id
        and row["actor_id"] == actor
        and row["instance_id"] == instance_id(expected)
        and int(row["ordinal"]) == len(before.records) + 1
        and row["previous_record_id"]
        == (identifier(DOMAIN, before.records[-1]) if before.records else "GENESIS")
        and int(row["knowledge_count"]) == len(before.knowledge)
        and row["knowledge_id"] == knowledge_id(before.knowledge),
        "complete own original prefix and independent context",
    )
    c._require(
        type(payload) is bytes
        and row["payload_raw_id"] == m.raw_id(payload)
        and int(row["payload_bytes"]) == len(payload),
        "exact retained payload bytes",
    )
    after = replace(before, records=(*before.records, raw))
    if row["type_name"] == "RECEIVE":
        return replace(after, knowledge=(*before.knowledge, payload))
    if row["type_name"] == "INTENT":
        key, view = check_intent(group, boot, expected, actor, before, payload, row["commit_ids"])
        c._require(all(item.key != key for item in before.intents), "retry uses original ordinal")
        intent = StoredIntent(
            len(after.records), payload, len(before.knowledge), tuple(row["commit_ids"]), key
        )
        return replace(after, intents=(*before.intents, intent), agreement_view=view)
    ordinal = int(row["intent_ordinal"])
    selected = [item for item in before.intents if item.ordinal == ordinal]
    c._require(len(selected) == 1, "prior committed original intent")
    c._require(all(old != ordinal for old, _ in before.signed), "signed retry uses original record")
    verified_signed(group, boot, expected, actor, before, selected[0], payload)
    return replace(
        after,
        knowledge=(*before.knowledge, payload),
        signed=(*before.signed, (ordinal, payload)),
    )


def replay(group, boot, expected, bootstrap_id, actor, original, artifacts):
    c._id(bootstrap_id)
    c._require(actor in p.context(boot, expected), "independent enrolled journal owner")
    c._require(
        type(artifacts) is tuple and all(type(x) is bytes for x in artifacts), "raw inventory"
    )
    store = {m.raw_id(raw): raw for raw in artifacts}
    c._require(
        all(store[m.raw_id(raw)] == raw for raw in artifacts), "original payload digest collision"
    )
    before = Replay()
    for raw in scan(original):
        payload = store.get(decode(raw)["payload_raw_id"])
        before = advance(group, boot, expected, bootstrap_id, actor, before, raw, payload)
    return before


@dataclass(frozen=True)
class Machine:
    group: object
    boot: object
    expected: dict
    bootstrap_id: str
    actor: str
    native_wal: bytes
    volatile: bytes = b""
    stable: bytes = b""
    committed: bytes = b""
    artifacts: tuple[bytes, ...] = ()
    phase: str = "READY"
    exposed: tuple[bytes, ...] = ()
    produced: tuple[tuple[int, bytes], ...] = ()
    recovery_base: bytes = b""
    recovery_target: bytes = b""

    def inspect(self, original=None):
        return replay(
            self.group,
            self.boot,
            self.expected,
            self.bootstrap_id,
            self.actor,
            self.committed if original is None else original,
            self.artifacts,
        )


def initial(group, boot, expected, bootstrap_id, actor, native_wal):
    c._require(type(native_wal) is bytes, "original native WAL retained unchanged")
    result = Machine(group, boot, expected, bootstrap_id, actor, native_wal)
    result.inspect()
    return result


def append(state, kind, payload, *, intent_ordinal=0, commit_ids=()):
    c._require(state.phase == "READY", "one outstanding validated append")
    before = state.inspect()
    c._require(type(payload) is bytes and type(commit_ids) is tuple, "original candidate material")
    if kind == "INTENT":
        key, _ = check_intent(
            state.group, state.boot, state.expected, state.actor, before, payload, commit_ids
        )
        found = [item for item in before.intents if item.key == key]
        if found:
            c._require(found[0].body == payload, "conflicting intent, no append")
            return state  # Reuse the first original release witness/record.
    if kind == "SIGNED":
        found = [raw for ordinal, raw in before.signed if ordinal == intent_ordinal]
        if found:
            c._require(found[0] == payload, "conflicting signed retry, no append")
            return state
        c._require(
            (intent_ordinal, payload) in state.produced,
            "original own signing action after durable intent",
        )
    raw = m.canonical(
        dict(
            type_name=kind,
            schema_version="1",
            profile_id=m.PROFILE,
            bootstrap_id=state.bootstrap_id,
            actor_id=state.actor,
            instance_id=instance_id(state.expected),
            ordinal=str(len(before.records) + 1),
            previous_record_id=identifier(DOMAIN, before.records[-1])
            if before.records
            else "GENESIS",
            payload_raw_id=m.raw_id(payload),
            payload_bytes=str(len(payload)),
            knowledge_count=str(len(before.knowledge)),
            knowledge_id=knowledge_id(before.knowledge),
            intent_ordinal=str(intent_ordinal),
            commit_ids=list(commit_ids),
        )
    )
    advance(
        state.group,
        state.boot,
        state.expected,
        state.bootstrap_id,
        state.actor,
        before,
        raw,
        payload,
    )
    return replace(
        state,
        volatile=state.committed + frame(raw),
        artifacts=(*state.artifacts, payload),
        phase="APPENDED",
    )


def barrier(state):
    c._require(
        state.phase in ("APPENDED", "RECOVERY_VERIFIED"), "validated append/recovery before barrier"
    )
    state.inspect(state.volatile)
    return replace(state, stable=state.volatile, phase="DURABLE")


def commit(state):
    c._require(
        state.phase == "DURABLE" and state.volatile == state.stable,
        "successful barrier before commit",
    )
    state.inspect(state.stable)
    return replace(state, committed=state.stable, phase="READY")


def sign(state, intent_ordinal, private_seed):
    """Reference private producer using caller's PUBLIC synthetic test seed only.

    No key loading, persistence, or exposure. Does not store the seed in Machine.
    The internal produced artifact still requires SIGNED/barrier/commit before expose.
    """
    c._require(state.phase == "READY", "sign only committed intent after barrier")
    before = state.inspect()
    selected = [item for item in before.intents if item.ordinal == intent_ordinal]
    c._require(len(selected) == 1, "original durable intent to sign")
    prior = [raw for ordinal, raw in (*before.signed, *state.produced) if ordinal == intent_ordinal]
    if prior:
        return state, prior[0]
    original = selected[0].body
    body = c._load(original)
    members = p.context(state.boot, state.expected)
    gen.key_scalar(state.group, private_seed, members[state.actor])
    if body["profile"] == p.PROFILE:
        if body["kind"] == "DEAL":
            generated = gen.deal_body(
                state.group, state.boot, body["context"], state.actor, private_seed
            )
        else:
            prior = a.Evidence(
                state.group,
                state.boot,
                state.expected,
                before.knowledge[: selected[0].knowledge_count],
            )
            generated = gen.opening_body(
                state.group,
                state.boot,
                body["context"],
                state.actor,
                private_seed,
                prior.deals[body["deal_id"]].original,
            )
        c._require(generated == original, "exact selected private deterministic producer")
        message = p.message(original)
    else:
        message = a.message(original)
    _, signature = state.group.backend.sign(private_seed, message)
    raw = c._json({"body": original.hex(), "signature": signature.hex()})
    return replace(state, produced=(*state.produced, (intent_ordinal, raw))), raw


def expose(state, intent_ordinal):
    c._require(state.phase == "READY", "no effect before signed artifact barrier/commit")
    selected = [raw for ordinal, raw in state.inspect().signed if ordinal == intent_ordinal]
    c._require(len(selected) == 1, "committed signed original required")
    return replace(state, exposed=(*state.exposed, selected[0]))


def crash(state, surviving):
    c._require(
        type(surviving) is bytes
        and surviving.startswith(state.stable)
        and len(surviving) <= len(state.volatile),
        "existing T stable prefix/write extent",
    )
    # Artifacts/exposed are retained original history, never a restart authority.
    return replace(
        state,
        volatile=surviving,
        stable=surviving,
        committed=b"",
        produced=(),
        phase="CRASHED",
        recovery_base=state.stable,
        recovery_target=state.volatile,
    )


def recover(state):
    c._require(state.phase == "CRASHED", "recovery follows modeled crash")
    if state.volatile not in (state.recovery_base, state.recovery_target):
        # These originals belong to the retained producing trace, NOT a restart
        # cache. A parseable foreign/torn record cannot become another history.
        return replace(state, phase="BLOCKED")
    try:
        state.inspect(state.volatile)
    except c.CodecError:
        return replace(state, phase="BLOCKED")
    # Even a complete surviving unacknowledged record needs a new barrier.
    return replace(state, phase="RECOVERY_VERIFIED")
