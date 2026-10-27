"""T047/T053 deterministic agreement intent guards over complete original prefixes.

No caller-provided prepared/committed/accepted boolean. This is the pure protocol
guard conjunct: binding these intents to actual durable companion bytes remains
separate and must precede any claim that a signature was lawfully exposed.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto import codec as c
from formal.reference.seed_source import agreement as a


@dataclass(frozen=True)
class Intent:
    original_body: bytes
    knowledge_cut: int


def highest_prepared(evidence, current_view):
    """Derive from original known proposal/prepare bytes, not claimed STATUS fields."""
    found = []
    for proposal_id, proposal in evidence.agreement.items():
        if proposal.kind != "PROPOSE" or proposal.view > current_view:
            continue
        signers = {
            row.actor
            for row in evidence.agreement.values()
            if row.kind == "PREPARE" and row.proposal == proposal_id and row.view == proposal.view
        }
        if len(signers) >= 3:
            found.append(proposal)
    if not found:
        return None
    highest = max(row.view for row in found)
    at_highest = [row for row in found if row.view == highest]
    c._require(
        all(row.deals == at_highest[0].deals for row in at_highest),
        "conflicting highest prepared evidence",
    )
    return highest, at_highest[0].deals


@dataclass(frozen=True)
class GuardState:
    view: int = 0
    intents: tuple[Intent, ...] = ()
    retained_knowledge: tuple[bytes, ...] = ()


def guard_sequence(
    group, boot, expected, actor, originals: tuple[bytes, ...], intents: tuple[Intent, ...]
) -> GuardState:
    """Recompute from empty, checking every original intent and ordered source cut.

    originals is this actor's retained receive/self-store inventory. A selected
    prefix denotes knowledge at an intent, not deletion of later or rejected
    occurrences. The storage/source join must bind these original cuts.
    """
    c._require(type(originals) is tuple and type(intents) is tuple, "immutable originals")
    # Independent key/context validation is performed even for an empty history.
    a.Evidence(group, boot, expected, ())
    c._require(actor in dict(boot.validators), "enrolled own producer")
    state = GuardState()
    seen = {}
    old_cut = 0
    for intent in intents:
        c._require(
            type(intent) is Intent
            and type(intent.knowledge_cut) is int
            and old_cut <= intent.knowledge_cut <= len(originals),
            "monotone original knowledge cut",
        )
        evidence = a.Evidence(group, boot, expected, originals[: intent.knowledge_cut])
        checked = evidence.unsigned(intent.original_body, actor)
        key = (checked.kind, checked.view)
        # Exact retry is lawful even after view advancement, but cannot create a
        # different body/signature intent. Physical replay identity is joined later.
        if key in seen:
            c._require(seen[key] == intent.original_body, "conflicting original intent")
        else:
            if checked.kind == "STATUS":
                c._require(checked.view > state.view, "monotone honest view entry")
                highest = highest_prepared(evidence, state.view)
                actual = (
                    (checked.prepared_view, checked.deals)
                    if checked.prepared_view is not None
                    else None
                )
                c._require(actual == highest, "honest STATUS must report highest prepared value")
                state = GuardState(checked.view, state.intents, state.retained_knowledge)
            else:
                c._require(checked.view == state.view, "no new intent for an old/future view")
            seen[key] = intent.original_body
        state = GuardState(state.view, (*state.intents, intent), originals)
        old_cut = intent.knowledge_cut
    # Preserve even a wholly incomplete/invalid inventory and an empty intent prefix.
    return GuardState(state.view, state.intents, originals)
