"""Original own intent/signature binding with S-RANK, including unsigned crash cuts.

Admission/producing legality remains a separate necessary source-prefix check.
Authenticity is not asserted for a durable intent with no signature artifact.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto import codec as c
from formal.reference.isc_crypto.sodium_reference import SodiumReference
from formal.reference.isc_source.authentication import Bootstrap, registry
from formal.reference.non_isc import codec as n
from formal.reference.profile_source.journals import Journal, Position


def decode(raw):
    reader = c._Reader(raw, max(c.MAX_VOTE_BYTES, n.MAX_VOTE_BYTES))
    c._require(reader.take(8) == b"DRC1\x01\x00\x00\x03", "original vote header")
    c._require(
        reader.u32() == reader.remaining and reader.take(1) == b"\x31" and reader.u32() == 12,
        "future original vote layout",
    )
    fields = {}
    for key in c.VOTE_KEYS:
        c._require(reader.text(tagged=True) == key, "original vote ordered field")
        fields[key] = reader.text(tagged=True)
    reader.finish()
    # Explicit disjoint codec dispatch, never try legacy/fallback on failure.
    kind = fields["kind"]
    if kind == "ISC":
        return kind, c.decode_vote(raw)
    return kind, n.decode_vote(raw).original


@dataclass(frozen=True)
class Intent:
    position: Position
    kind: str
    original_vote: bytes
    vote: c.Vote
    signed_artifacts: tuple[bytes, ...]

    @property
    def public_ordinal(self):
        # Projection only. Never rewrite the signed native Vote or its ID.
        return self.position.vote_count


def bind(
    bootstrap: Bootstrap,
    backend: SodiumReference,
    actor: str,
    journal: Journal,
    signatures: tuple[bytes, ...],
) -> tuple[Intent, ...]:
    expected_registry, keys = registry(bootstrap)
    c._require(
        actor in keys and type(backend) is SodiumReference,
        "independent original own actor/verifier",
    )
    c._require(type(signatures) is tuple, "original signature occurrences")
    by_vote = {}
    for artifact in signatures:
        c._require(type(artifact) is bytes, "original detached signature bytes")
        if artifact[:8] == b"NSG1\0\1\0\0":
            value = n.decode_artifact(artifact)
            signable = n.preimage
        else:
            value = c.decode_artifact(artifact)
            signable = c.preimage
        kind, vote = decode(value.vote_bytes)
        key_id, public = keys[actor]
        c._require(
            vote.validator_id == actor
            and value.registry_id == expected_registry
            and value.key_id == key_id
            and vote.validator_epoch_id == bootstrap.validator_epoch_id
            and vote.formal_semantics_id == bootstrap.formal_semantics_id,
            "original own signature/key/epoch association",
        )
        c._require(
            backend.verify(
                public, signable(value.registry_id, value.key_id, value.vote_bytes), value.signature
            ),
            "strict own signature",
        )
        by_vote.setdefault(value.vote_bytes, []).append(artifact)
    intents, no_double = [], set()
    for position in journal.original_votes:
        raw = position.decoded.sections[0]
        kind, vote = decode(raw)
        c._require(
            vote.validator_id == actor
            and vote.validator_epoch_id == bootstrap.validator_epoch_id
            and vote.formal_semantics_id == bootstrap.formal_semantics_id,
            "independent original own journal identity",
        )
        c._require(
            vote.durable_sequence == position.decoded.sequence,
            "signed native sequence must equal original physical WAL slot",
        )
        key = (
            vote.validator_id,
            vote.validator_epoch_id,
            vote.context_id,
        )
        # N:consensus.cpp vote_key is exactly validator/epoch/context. Round,
        # view and kind are signed non-key fields; changing one cannot reopen
        # an occupied durable context. No second slot is allocated on retry.
        c._require(
            key not in no_double,
            "original context already has a durable intent; retry cannot allocate another slot",
        )
        no_double.add(key)
        intents.append(Intent(position, kind, raw, vote, tuple(by_vote.pop(raw, ()))))
    c._require(not by_vote, "signed own vote lacks its exact original durable intent")
    return tuple(intents)
