"""T047/T053 seed-purpose agreement evidence, isolated formal/reference only.

Authenticated records are not honest producer histories. This component checks
whole prior-reference certificates and preserves ALL occurrences. Honest local
durability/view/status/release guards must be composed by the producing fold.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from formal.reference.isc_crypto import codec as c
from formal.reference.seed_source import pvss as p

PROFILE = "SEED-SET-PBFT-REFERENCE-v1"
SIGN = b"deltareduce.seed-agreement.statement.v1\0"
DOMAIN = "deltareduce.seed-agreement.artifact.v1"
SEED = b"deltareduce.seed-output.v1\0"
COMMON = {"profile", "kind", "instance", "actor", "agreement_view"}


def instance(context):
    return {key: value for key, value in context.items() if key != "source_cut_id"}


def identifier(raw):
    return c.content_id(DOMAIN, raw)


def message(raw):
    return SIGN + len(raw).to_bytes(8, "big") + hashlib.sha512(raw).digest()


def sign(group, seed, body):
    """Synthetic fixture helper, not a production signer or key store."""
    raw = c._json(body)
    _, signature = group.backend.sign(seed, message(raw))
    return c._json({"body": raw.hex(), "signature": signature.hex()})


@dataclass(frozen=True)
class Checked:
    original: bytes
    kind: str
    actor: str
    view: int
    proposal: str = ""
    deals: tuple[str, ...] = ()
    prepared_view: int | None = None


@dataclass(frozen=True)
class Occurrence:
    position: int
    original: bytes
    accepted: Checked | p.Deal | None
    error: str | None


class Evidence:
    """Replay an entire supplied occurrence list from empty; never trust cached OKs."""

    def __init__(self, group, boot, expected, originals: tuple[bytes, ...]):
        c._require(type(originals) is tuple, "complete immutable occurrence inventory")
        self.group, self.boot, self.expected = group, boot, expected
        self.members = p.context(boot, expected)
        self.agreement = {}
        self.deals = {}
        self.occurrences = []
        for position, raw in enumerate(originals):
            # The retained inventory is never filtered into a shorter successful run.
            try:
                checked = self._read(raw)
                error = None
                target, ident = (
                    (self.deals, p.artifact_id(raw))
                    if isinstance(checked, p.Deal)
                    else (self.agreement, identifier(raw))
                )
                c._require(
                    ident not in target or target[ident].original == raw,
                    "artifact digest collision",
                )
                target.setdefault(ident, checked)
            except c.CodecError as failure:
                checked, error = None, str(failure)
            self.occurrences.append(Occurrence(position, raw, checked, error))
        self.occurrences = tuple(self.occurrences)

    def _reference(self, ident, kind):
        c._id(ident)
        found = self.agreement.get(ident)
        c._require(found is not None and found.kind == kind, "original prior " + kind)
        return found

    def _quorum(self, references, kind, proposal=None, view=None):
        c._require(type(references) is list and len(references) == 3, "three original witnesses")
        rows = [self._reference(ref, kind) for ref in references]
        actors = [row.actor for row in rows]
        c._require(actors == sorted(set(actors)), "distinct canonical signer identities")
        if proposal is not None:
            c._require(all(row.proposal == proposal for row in rows), "matching original proposal")
        if view is not None:
            c._require(all(row.view == view for row in rows), "matching agreement view")
        return rows

    def _value(self, identifiers):
        c._require(type(identifiers) is list and len(identifiers) in (3, 4), "qualified dealer set")
        rows = []
        for ident in identifiers:
            c._id(ident)
            row = self.deals.get(ident)
            c._require(row is not None, "original prior verified DEAL")
            rows.append(row)
        actors = [row.actor for row in rows]
        c._require(actors == sorted(set(actors)), "distinct ordered original dealers")
        return tuple(identifiers)

    def _read(self, raw):
        outer = c._closed(c._load(raw), {"body", "signature"})
        c._require(type(outer["body"]) is str, "original signed body")
        original = p.binary(outer["body"], len(outer["body"]) // 2)
        body = c._load(original)
        if body.get("profile") == p.PROFILE:
            candidate = body.get("context")
            c._require(
                type(candidate) is dict and instance(candidate) == instance(self.expected),
                "DEAL instance",
            )
            return p.verify_deal(self.group, self.boot, candidate, raw)
        c._require(COMMON <= set(body), "complete agreement body")
        c._label(body["actor"])
        c._require(
            body["profile"] == PROFILE
            and body["instance"] == instance(self.expected)
            and body["actor"] in self.members,
            "agreement context/actor/profile",
        )
        signature = p.binary(outer["signature"], 64)
        c._require(
            self.group.backend.verify(self.members[body["actor"]], message(original), signature),
            "existing-key agreement signature",
        )
        return self._body(body, raw)

    def unsigned(self, original: bytes, actor: str) -> Checked:
        """Pre-sign semantic guard only. Result is NEVER inserted as signed evidence."""
        body = c._load(original)
        c._require(COMMON <= set(body), "complete unsigned body")
        c._label(body["actor"])
        c._require(
            body["profile"] == PROFILE
            and body["instance"] == instance(self.expected)
            and body["actor"] == actor
            and actor in self.members,
            "own original unsigned context/actor",
        )
        return self._body(body, None)

    def _body(self, body, raw):
        view = c._decimal(body["agreement_view"])
        actor, kind = body["actor"], body["kind"]
        if kind == "PROPOSE":
            c._closed(body, COMMON | {"deals", "new_view"})
            c._require(actor == list(self.members)[view % 4], "selected view leader")
            deals = self._value(body["deals"])
            if view == 0:
                c._require(body["new_view"] == [], "no implicit genesis STATUS")
            else:
                statuses = self._quorum(body["new_view"], "STATUS", view=view)
                prepared = [row for row in statuses if row.prepared_view is not None]
                if prepared:
                    highest = max(row.prepared_view for row in prepared)
                    values = [row.deals for row in prepared if row.prepared_view == highest]
                    c._require(
                        all(value == values[0] for value in values) and deals == values[0],
                        "preserve highest prepared value",
                    )
            return Checked(
                raw, kind, actor, view, identifier(raw) if raw is not None else "", deals
            )
        if kind in ("PREPARE", "COMMIT"):
            extra = {"prepares"} if kind == "COMMIT" else set()
            c._closed(body, COMMON | {"proposal_id"} | extra)
            proposal = self._reference(body["proposal_id"], "PROPOSE")
            c._require(proposal.view == view, "proposal view")
            if kind == "COMMIT":
                self._quorum(body["prepares"], "PREPARE", body["proposal_id"], view)
            return Checked(raw, kind, actor, view, body["proposal_id"], proposal.deals)
        if kind == "STATUS":
            c._closed(body, COMMON | {"prepared_proposal", "prepares"})
            c._require(view > 0, "positive STATUS target view")
            if body["prepared_proposal"] == "":
                c._require(body["prepares"] == [], "empty unprepared witness")
                return Checked(raw, kind, actor, view)
            proposal = self._reference(body["prepared_proposal"], "PROPOSE")
            c._require(proposal.view < view, "prior prepared view")
            self._quorum(body["prepares"], "PREPARE", body["prepared_proposal"], proposal.view)
            return Checked(
                raw, kind, actor, view, body["prepared_proposal"], proposal.deals, proposal.view
            )
        raise c.CodecError("unknown seed agreement kind")

    def committed(self, witness: list[str]) -> Checked:
        rows = self._quorum(witness, "COMMIT")
        c._require(
            all(row.proposal == rows[0].proposal and row.view == rows[0].view for row in rows),
            "one committed original proposal",
        )
        return self._reference(rows[0].proposal, "PROPOSE")


def reconstruct_candidate(group, boot, expected, originals, commit_ids, openings):
    """Checked candidate only: complete honest-source/release fold still required.

    Do NOT expose this as an admitted seed based on certificates alone.
    openings selects a witness per deal, not a retained history replacement.
    """
    evidence = Evidence(group, boot, expected, originals)
    proposal = evidence.committed(commit_ids)
    c._require(
        type(openings) is dict and set(openings) == set(proposal.deals),
        "all selected original DEALs",
    )
    points = []
    for ident in proposal.deals:
        raw = evidence.deals[ident].original
        body = c._load(bytes.fromhex(c._load(raw)["body"]))
        points.append(p.reconstruct(group, boot, body["context"], raw, openings[ident]))
    preimage = SEED + p.frame(c._json(instance(expected))) + group.total(points)
    return "sha256:" + hashlib.sha256(preimage).hexdigest(), evidence
