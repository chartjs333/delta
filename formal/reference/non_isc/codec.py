"""Exact scope-5 Vn/Mn/Gn; no legacy conversion or implicit ISC dispatch.

The derived per-object bounds are not source-history admission limits.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto.codec import (
    VOTE_KEYS,
    Artifact,
    Vote,
    _bytes,
    _decimal,
    _id,
    _l,
    _Reader,
    _require,
    _txt,
    _uint,
    _vote_fields,
)

KINDS = frozenset(
    {"ROUND_CONFIG", "EC", "APC", "PARAMETER", "AGGREGATE_ROOT", "APPLY", "VIEW_CHANGE", "ABORT"}
)
VOTE_DOMAIN = "deltareduce:003:vote:v2"
ARTIFACT_DOMAIN = "deltareduce.non-isc-signature.v1"
M_DOMAIN = b"deltareduce.non-isc-vote.ed25519.v1\0"
MAX_VOTE_BYTES, MAX_PREIMAGE_BYTES, MAX_ARTIFACT_BYTES = 946, 1136, 1172


@dataclass(frozen=True)
class NonIscVote:
    original: Vote
    kind: str


def encode_vote(value: NonIscVote) -> bytes:
    _require(type(value) is NonIscVote and type(value.original) is Vote, "typed original vote")
    _require(type(value.kind) is str and value.kind in KINDS, "non-ISC kind dispatch")
    # Reuse only the common field grammar. ISC signing/decoding is never called.
    fields = _vote_fields(value.original)
    fields["kind"] = value.kind
    payload = b"\x31" + _uint(12, 4)
    payload += b"".join(_txt(key) + _txt(fields[key]) for key in VOTE_KEYS)
    return _bytes(b"DRC1\x01\x00\x00\x03" + _l(payload), MAX_VOTE_BYTES)


def decode_vote(raw: bytes) -> NonIscVote:
    reader = _Reader(raw, MAX_VOTE_BYTES)
    _require(reader.take(8) == b"DRC1\x01\x00\x00\x03", "vote header")
    _require(reader.u32() == reader.remaining, "vote payload length")
    _require(reader.take(1) == b"\x31" and reader.u32() == 12, "vote map shape")
    fields = {}
    for key in VOTE_KEYS:
        _require(reader.text(tagged=True) == key, "vote field order/unknown/duplicate")
        fields[key] = reader.text(tagged=True)
    reader.finish()
    _require(
        fields["kind"] in KINDS
        and fields["schema_version"] == "2.0.0"
        and fields["type_name"] == "VOTE",
        "non-ISC kind/schema dispatch",
    )
    value = NonIscVote(
        Vote(
            fields["body_hash"],
            fields["context_id"],
            _decimal(fields["durable_sequence"], positive=True),
            fields["formal_semantics_id"],
            _decimal(fields["height"]),
            fields["round_id"],
            fields["validator_epoch_id"],
            fields["validator_id"],
            _decimal(fields["view"]),
        ),
        fields["kind"],
    )
    _require(encode_vote(value) == raw, "canonical vote bytes")
    return value


def preimage(registry_id: str, key_id: str, vote_bytes: bytes) -> bytes:
    decode_vote(vote_bytes)
    raw = M_DOMAIN + _l(_id(registry_id).encode("ascii"))
    raw += _l(_id(key_id).encode("ascii")) + _l(vote_bytes)
    return _bytes(raw, MAX_PREIMAGE_BYTES)


def decode_preimage(raw: bytes) -> tuple[str, str, bytes]:
    reader = _Reader(raw, MAX_PREIMAGE_BYTES)
    _require(reader.take(len(M_DOMAIN)) == M_DOMAIN, "non-ISC preimage domain")
    registry_id, key_id = reader.text(content=True), reader.text(content=True)
    vote_bytes = reader.blob(MAX_VOTE_BYTES)
    reader.finish()
    _require(preimage(registry_id, key_id, vote_bytes) == raw, "canonical preimage")
    return registry_id, key_id, vote_bytes


def encode_artifact(artifact: Artifact) -> bytes:
    _require(type(artifact) is Artifact, "typed artifact")
    decode_vote(artifact.vote_bytes)
    raw = b"NSG1\x00\x01\x00\x00"
    raw += _l(_id(artifact.registry_id).encode("ascii"))
    raw += _l(_id(artifact.key_id).encode("ascii")) + _l(artifact.vote_bytes)
    return _bytes(raw + _bytes(artifact.signature, 64, exact=64), MAX_ARTIFACT_BYTES)


def decode_artifact(raw: bytes) -> Artifact:
    reader = _Reader(raw, MAX_ARTIFACT_BYTES)
    _require(reader.take(8) == b"NSG1\x00\x01\x00\x00", "non-ISC artifact header")
    registry_id, key_id = reader.text(content=True), reader.text(content=True)
    vote_bytes, signature = reader.blob(MAX_VOTE_BYTES), reader.take(64)
    reader.finish()
    value = Artifact(registry_id, key_id, vote_bytes, signature)
    _require(encode_artifact(value) == raw, "canonical artifact")
    return value
