"""T047/T053 original Profile source association for the seed companion facet.

No imported cache, private key, durable flag or public-state success premise.
Public SIGN verification associates an original own signing invocation; it does
not prove private KDF behavior or remote honesty. Complete ISC/clock/native
legality and the independently pinned metadata call belong to the enclosing fold.
"""

from dataclasses import dataclass, replace

from formal.reference.isc_crypto import codec as c
from formal.reference.profile_source import metadata as m
from formal.reference.seed_source import agreement as a
from formal.reference.seed_source import durability as d

ACTION = "ACT-SEED-PRODUCER"
FIELDS = frozenset(
    "type_name schema_version profile_id bootstrap_id instance_id operation "
    "intent_ordinal commit_ids".split()
)
OPERATIONS = frozenset("RECEIVE INTENT SIGN SIGNED BARRIER COMMIT EXPOSE CRASH RECOVER".split())
ONE_INPUT = frozenset("RECEIVE INTENT SIGN SIGNED CRASH".split())
WITH_ORDINAL = frozenset("SIGN SIGNED EXPOSE".split())


def journal_id(expected):
    return d.JOURNAL + ":" + d.instance_id(expected)


def invocation(raw):
    row = m.closed(m.load(raw), FIELDS)
    c._require(
        row["type_name"] == "SEED_SOURCE_STEP"
        and row["schema_version"] == "1"
        and row["profile_id"] == m.PROFILE,
        "seed source dispatch",
    )
    for key in ("bootstrap_id", "instance_id"):
        c._id(row[key])
    op = row["operation"]
    c._require(type(op) is str and op in OPERATIONS, "known seed source operation")
    ordinal = c._decimal(row["intent_ordinal"])
    c._require((ordinal > 0) == (op in WITH_ORDINAL), "exact operation intent reference")
    c._require(type(row["commit_ids"]) is list, "original commit witnesses")
    for ident in row["commit_ids"]:
        c._id(ident)
    c._require(op == "INTENT" or row["commit_ids"] == [], "only intent has release witnesses")
    return row


def original_event(event, position):
    """Recheck every field of the original materialized occurrence, not a cache."""
    row = m.closed(
        m.load(event.original_descriptor),
        {"actor_id", "action_id", "original_ref", "input_refs", "dependencies"},
    )
    c._require(
        type(event.index) is int
        and event.index == position
        and row["actor_id"] == event.actor
        and row["action_id"] == event.action
        and type(event.inputs) is tuple
        and type(event.dependencies) is tuple
        and type(row["input_refs"]) is list
        and type(row["dependencies"]) is list,
        "complete original source occurrence",
    )
    m.text(event.actor, nonempty=True)
    m.text(event.action, nonempty=True)
    deps = tuple(c._decimal(x) for x in row["dependencies"])
    c._require(
        deps == event.dependencies
        and deps == tuple(sorted(set(deps)))
        and all(i < position for i in deps),
        "original strictly backward dependencies",
    )
    c._require(len(row["input_refs"]) == len(event.inputs), "all ordered original inputs")
    for ref, raw in zip(
        (row["original_ref"], *row["input_refs"]),
        (event.original, *event.inputs),
        strict=True,
    ):
        m.reference(ref)
        c._require(
            ref["content_id"] == m.raw_id(raw) and int(ref["byte_length"]) == len(raw),
            "exact original occurrence bytes",
        )


def observed_sign(state, ordinal, original):
    """Original own SIGN step, never inferred from RECEIVE/signature alone.

    The source fold calls this only at the independently retained invocation.
    This checks the public output of signing, not honest private KDF generation;
    the selected private producer and cryptographic assumptions remain explicit.
    """
    c._require(state.phase == "READY", "original SIGN after committed intent")
    before = state.inspect()
    selected = [item for item in before.intents if item.ordinal == ordinal]
    c._require(len(selected) == 1, "original committed own intent")
    d.verified_signed(
        state.group, state.boot, state.expected, state.actor, before, selected[0], original
    )
    prior = [raw for index, raw in (*before.signed, *state.produced) if index == ordinal]
    if prior:
        c._require(all(raw == original for raw in prior), "exact original signing retry")
        return state
    return replace(state, produced=(*state.produced, (ordinal, original)))


def invoke(state, row, inputs):
    c._require(
        row["bootstrap_id"] == state.bootstrap_id
        and row["instance_id"] == d.instance_id(state.expected),
        "independent original bootstrap/instance",
    )
    op, ordinal = row["operation"], int(row["intent_ordinal"])
    c._require(len(inputs) == int(op in ONE_INPUT), "exact original invocation arity")
    if op in ("RECEIVE", "INTENT", "SIGNED"):
        return d.append(
            state, op, inputs[0], intent_ordinal=ordinal, commit_ids=tuple(row["commit_ids"])
        )
    if op == "SIGN":
        return observed_sign(state, ordinal, inputs[0])
    if op == "CRASH":
        return d.crash(state, inputs[0])
    if op == "EXPOSE":
        return d.expose(state, ordinal)
    return {"BARRIER": d.barrier, "COMMIT": d.commit, "RECOVER": d.recover}[op](state)


@dataclass(frozen=True)
class Outcome:
    index: int
    disposition: str
    error: str | None
    before_phase: str
    after_phase: str


@dataclass(frozen=True)
class Trace:
    # Whole original prefix, not only accepted seed actions.
    events: tuple
    outcomes: tuple[Outcome, ...]
    cuts: tuple[tuple[int, d.Machine], ...]
    state: d.Machine
    unresolved: tuple[int, ...]
    # Exact successful COMMIT cuts, including recovery/retry. Not supplied OKs.
    commits: tuple[tuple[int, d.Machine], ...]


def fold(group, boot, expected, bootstrap_id, actor, native_wal, events, cuts=()):
    """Finite ordered facet from empty; preserves failed and unrelated actions.

    Metadata custody and the other source handlers are NOT established by this
    function. It returns no admitted-source/READY capability or R2 success flag.
    """
    c._require(type(events) is tuple and len(events) <= m.MAX_EVENTS, "whole Profile prefix")
    c._require(
        type(cuts) is tuple
        and all(type(i) is int and 0 <= i <= len(events) for i in cuts)
        and cuts == tuple(sorted(set(cuts))),
        "exact original prefix-length cuts",
    )
    state = d.initial(group, boot, expected, bootstrap_id, actor, native_wal)
    at_cut = [(0, state)] if 0 in cuts else []
    outcomes, unresolved, commits = [], [], []
    for position, event in enumerate(events):
        original_event(event, position)
        before = state
        error = None
        if event.action != ACTION or event.actor != actor:
            disposition = "other_original_source"
        else:
            try:
                row = invocation(event.original)
            except c.CodecError as exc:
                disposition, error = "unresolved_invocation", str(exc)
                unresolved.append(position)
            else:
                if row["bootstrap_id"] == bootstrap_id and row["instance_id"] != d.instance_id(
                    expected
                ):
                    # The complete prefix contains other original instances.
                    # Keep its position but leave its interpretation to its own
                    # facet; fold_family checks that none is left unaccounted.
                    outcomes.append(
                        Outcome(position, "other_original_source", None, before.phase, state.phase)
                    )
                    if position + 1 in cuts:
                        at_cut.append((position + 1, state))
                    continue
                try:
                    state = invoke(state, row, event.inputs)
                    disposition = "accepted"
                    if row["operation"] == "COMMIT":
                        commits.append((position, state))
                except c.CodecError as exc:
                    error = str(exc)
                    if row["operation"] in ("SIGN", "CRASH"):
                        # These inputs claim original producer/physical outputs,
                        # not a malformed incoming protocol command. A conflicting
                        # claim cannot disappear as a legal rejected/no-op event.
                        disposition = "unresolved_original_output"
                        unresolved.append(position)
                    else:
                        disposition = "rejected"
        outcomes.append(Outcome(position, disposition, error, before.phase, state.phase))
        if position + 1 in cuts:
            at_cut.append((position + 1, state))
    return Trace(events, tuple(outcomes), tuple(at_cut), state, tuple(unresolved), tuple(commits))


def recheck(trace):
    """A constructed/replaced Trace is not source authority; recompute its fold."""
    c._require(type(trace) is Trace and type(trace.state) is d.Machine, "source trace carrier")
    state = trace.state
    actual = fold(
        state.group,
        state.boot,
        state.expected,
        state.bootstrap_id,
        state.actor,
        state.native_wal,
        trace.events,
        tuple(index for index, _ in trace.cuts),
    )
    c._require(actual == trace, "entire recomputed original trace, not supplied caches")


def check_journal_tip(trace, actor, expected, original_own_journals):
    """Exact surviving original bytes, including incomplete/BLOCKED tails.

    The enclosing metadata verifier supplies the independently retained inventory.
    No missing journal is filled with empty bytes; this is not an activation test.
    """
    recheck(trace)
    c._require(type(original_own_journals) is tuple, "original own journal inventory")
    selected = [
        raw
        for owner, name, raw in original_own_journals
        if owner == actor and name == journal_id(expected)
    ]
    if not selected and not any(o.disposition == "accepted" for o in trace.outcomes):
        # Absence before instantiation is not an invented owned empty journal.
        c._require(not trace.unresolved, "no initial coverage through unresolved source")
        return None
    c._require(len(selected) == 1, "one original actor/instance companion, including empty")
    c._require(
        trace.state.actor == actor
        and d.instance_id(trace.state.expected) == d.instance_id(expected)
        and selected[0] == trace.state.volatile,
        "computed complete surviving companion equals independently retained original",
    )
    return selected[0]


@dataclass(frozen=True)
class Family:
    group: object
    boot: object
    bootstrap_id: str
    actor: str
    native_wal: bytes
    events: tuple
    cuts: tuple[int, ...]
    traces: tuple[tuple[str, Trace], ...]
    # Exactly one disposition for every original occurrence, including a
    # missing instance/invalid invocation. No cache is itself authority.
    outcomes: tuple[Outcome, ...]
    unresolved: tuple[int, ...]


def fold_family(group, boot, contexts, bootstrap_id, actor, native_wal, events, cuts=()):
    """Compose all original instance facets; not ISC/context-origin authority.

    The enclosing source join supplies each original own context exactly once.
    Completeness is checked against the full event inventory, never a filtered
    list. No new cap on the number of original instances is imposed.
    """
    c._require(type(contexts) is tuple and type(events) is tuple, "original instance catalog")
    c._require(len(events) <= m.MAX_EVENTS, "existing complete source budget")
    c._require(
        type(cuts) is tuple
        and all(type(i) is int and 0 <= i <= len(events) for i in cuts)
        and cuts == tuple(sorted(set(cuts))),
        "exact original family cuts",
    )
    traces = tuple(
        (d.instance_id(ctx), fold(group, boot, ctx, bootstrap_id, actor, native_wal, events, cuts))
        for ctx in contexts
    )
    by_id = dict(traces)
    c._require(len(by_id) == len(traces), "one original context per semantic instance")
    outcomes, unresolved = [], []
    for position, event in enumerate(events):
        original_event(event, position)
        if event.actor != actor or event.action != ACTION:
            outcome = Outcome(position, "other_original_source", None, "", "")
        else:
            try:
                row = invocation(event.original)
                if row["bootstrap_id"] != bootstrap_id:
                    # Preserve the existing primitive's rejection before any
                    # state change. SIGN/CRASH assert an original output, so a
                    # contradictory assertion cannot become a harmless no-op.
                    disposition = (
                        "unresolved_original_output"
                        if row["operation"] in ("SIGN", "CRASH")
                        else "rejected"
                    )
                    outcome = Outcome(position, disposition, "original family bootstrap", "", "")
                    outcomes.append(outcome)
                    if disposition.startswith("unresolved"):
                        unresolved.append(position)
                    continue
                selected = by_id.get(row["instance_id"])
                c._require(selected is not None, "missing original instance context")
                outcome = selected.outcomes[position]
                c._require(
                    outcome.disposition != "other_original_source", "selected instance coverage"
                )
            except c.CodecError as exc:
                outcome = Outcome(position, "unresolved_invocation", str(exc), "", "")
        outcomes.append(outcome)
        if outcome.disposition.startswith("unresolved"):
            unresolved.append(position)
    return Family(
        group,
        boot,
        bootstrap_id,
        actor,
        native_wal,
        events,
        cuts,
        traces,
        tuple(outcomes),
        tuple(unresolved),
    )


def recheck_family(family):
    c._require(type(family) is Family, "source family carrier")
    actual = fold_family(
        family.group,
        family.boot,
        tuple(t.state.expected for _, t in family.traces),
        family.bootstrap_id,
        family.actor,
        family.native_wal,
        family.events,
        family.cuts,
    )
    c._require(actual == family, "entire recomputed original family, not supplied coverage")


def check_family_journals(family, original_own_journals):
    """Check every owned companion without dropping an unrepresented instance."""
    recheck_family(family)
    c._require(not family.unresolved, "complete local instance source coverage required")
    c._require(type(original_own_journals) is tuple, "complete original own journals")
    names = [
        name
        for actor, name, _ in original_own_journals
        if actor == family.actor and name.startswith(d.JOURNAL + ":")
    ]
    known = {journal_id(trace.state.expected) for _, trace in family.traces}
    c._require(
        len(names) == len(set(names)) and set(names) <= known,
        "every original own seed journal has its original instance",
    )
    return tuple(
        (ident, check_journal_tip(trace, family.actor, trace.state.expected, original_own_journals))
        for ident, trace in family.traces
    )


@dataclass(frozen=True)
class LocalAction:
    source_position: int
    record_ordinal: int
    kind: str
    view: int
    value: tuple[str, ...] | None
    body: bytes


@dataclass(frozen=True)
class LocalAgreement:
    actions: tuple[LocalAction, ...]
    known: tuple[tuple[int, tuple[str, ...]], ...]
    commits: tuple[tuple[int, tuple[str, ...]], ...]
    reports: tuple[tuple[int, tuple[int, tuple[str, ...]] | None], ...]
    view: int
    records: tuple[bytes, ...]


def local_agreement(trace):
    """Derive the existing intent/knowledge kernel inputs from source COMMITs.

    No caller-supplied prepared/status/safe flags. Every learned certificate is
    reconstructed from the COMPLETE earlier byte prefix. Original identities
    remain in Trace; equal abstract values do not collapse those occurrences.
    This still requires the global authenticated/honest-source composition.
    """
    recheck(trace)
    c._require(not trace.unresolved, "no source coverage through unresolved outputs")
    before = d.Replay()
    known, commits, reports, actions = [], [], [], []
    view = 0
    for position, machine in trace.commits:
        after = machine.inspect()
        c._require(
            after.records[: len(before.records)] == before.records,
            "original committed records survive crash/recovery without replacement",
        )
        store = {m.raw_id(raw): raw for raw in machine.artifacts}
        for raw in after.records[len(before.records) :]:
            row = d.decode(raw)
            ordinal = int(row["ordinal"])
            payload = store[row["payload_raw_id"]]
            next_state = d.advance(
                machine.group,
                machine.boot,
                machine.expected,
                machine.bootstrap_id,
                machine.actor,
                before,
                raw,
                payload,
            )
            if row["type_name"] == "INTENT":
                body = c._load(payload)
                if body.get("profile") == a.PROFILE:
                    evidence = a.Evidence(
                        machine.group, machine.boot, machine.expected, before.knowledge
                    )
                    checked = evidence.unsigned(payload, machine.actor)
                    if checked.kind == "STATUS":
                        eligible = [entry for entry in known if entry[0] <= view]
                        highest = max((entry[0] for entry in eligible), default=None)
                        selected = [entry for entry in eligible if entry[0] == highest]
                        c._require(
                            not selected or all(x == selected[0] for x in selected),
                            "same highest prepared original value",
                        )
                        report = selected[0] if selected else None
                        actual = (
                            (checked.prepared_view, checked.deals)
                            if checked.prepared_view is not None
                            else None
                        )
                        c._require(view < checked.view and actual == report, "derived STATUS floor")
                        reports.append((checked.view, report))
                        view = checked.view
                    else:
                        c._require(checked.view == view, "derived same honest view")
                        if checked.kind == "COMMIT":
                            entry = (checked.view, checked.deals)
                            c._require(entry in known, "COMMIT has earlier learned prepared quorum")
                            commits.append(entry)
                    actions.append(
                        LocalAction(
                            position, ordinal, checked.kind, checked.view, checked.deals, payload
                        )
                    )
            if next_state.knowledge != before.knowledge:
                evidence = a.Evidence(
                    machine.group, machine.boot, machine.expected, next_state.knowledge
                )
                for ident, proposal in evidence.agreement.items():
                    if proposal.kind != "PROPOSE":
                        continue
                    signers = {
                        row.actor
                        for row in evidence.agreement.values()
                        if row.kind == "PREPARE"
                        and row.proposal == ident
                        and row.view == proposal.view
                    }
                    entry = (proposal.view, proposal.deals)
                    if len(signers) >= 3 and entry not in known:
                        known.append(entry)
                        actions.append(
                            LocalAction(position, ordinal, "LEARN", *entry, proposal.original)
                        )
            before = next_state
        c._require(before == after, "entire replay at original commit cut")
    # Derived causal property used by the existing global certificate induction.
    for target, report in reports:
        for committed_view, _ in commits:
            if committed_view < target:
                c._require(
                    report is not None and committed_view <= report[0],
                    "derived local commit/status floor",
                )
    return LocalAgreement(
        tuple(actions), tuple(known), tuple(commits), tuple(reports), view, before.records
    )
