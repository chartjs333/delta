"""T047/T053: exact CONFIG QC and its complete original delivered-vote join.

Preserves the existing DRC1 QUORUM_CERTIFICATE fields/identity. This checks the
certificate conjunct of FinalizeRoundConfig, not delivery occurrence or the
complete producing prefix. Those are not inferred from valid signatures.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto.codec import _decimal, _id, _label, _require, _uint
from formal.reference.non_isc.authentication import CONTRACT, AuthorityInputs, authenticate
from formal.reference.non_isc.codec import decode_artifact, preimage
from formal.reference.profile_source import configuration as cfg

FIELDS = {
    "body_hash",
    "context_id",
    "formal_semantics_id",
    "height",
    "kind",
    "qc_id",
    "quorum_threshold",
    "round_id",
    "schema_version",
    "signer_ids",
    "type_name",
    "validator_epoch_id",
    "view",
    "vote_ids",
}
HEADER = b"DRC1\x01\x00\x00\x04"


def validate(value):
    cfg.closed(value, FIELDS)
    for name in ("body_hash", "context_id", "formal_semantics_id", "qc_id", "validator_epoch_id"):
        _id(value[name])
    _decimal(value["height"])
    _decimal(value["view"])
    _label(value["round_id"])
    _uint(value["quorum_threshold"], 4)
    _require(
        value["schema_version"] == "1.0.0"
        and value["type_name"] == "QUORUM_CERTIFICATE"
        and value["kind"] == "ROUND_CONFIG",
        "original QC shape/kind",
    )
    signers, votes = value["signer_ids"], value["vote_ids"]
    _require(type(signers) is list and type(votes) is list, "original QC collections")
    for signer in signers:
        _label(signer)
    for vote in votes:
        _id(vote)
    _require(
        signers == sorted(set(signers))
        and len(votes) == len(set(votes))
        and len(signers) == len(votes) >= value["quorum_threshold"] > 0,
        "original canonical distinct QC signer/vote pairing",
    )
    return value


def encode(value):
    validate(value)
    payload = cfg.encode_value(value)
    result = HEADER + _uint(len(payload), 4) + payload
    _require(len(result) <= cfg.MAX_FRAME, "existing DRC1 envelope bound")
    return result


def decode(raw):
    reader = cfg.Reader(raw)
    _require(reader.take(8) == HEADER and reader.count() == len(raw) - 12, "QC exact header/length")
    value = reader.value()
    _require(reader.at == len(raw), "QC trailing bytes")
    validate(value)
    _require(encode(value) == raw, "QC canonical original bytes")
    return value


@dataclass(frozen=True)
class DeliverySource:
    # Existing complete W1 delivery record is also usable for a non-ISC Vote;
    # signature dispatch below is NSG1 only. No signature-id fallback.
    event: object
    original_artifact: bytes


@dataclass(frozen=True)
class BoundQC:
    original: bytes
    original_qc_id: str
    config: cfg.BoundConfig
    deliveries: tuple[DeliverySource, ...]
    matching_signers: tuple[str, ...]
    original_vote_ids: tuple[str, ...]


def bind(
    bootstrap,
    storage_bootstrap,
    backend,
    original_config,
    declaration,
    original_qc,
    delivered,
    *,
    source_cut,
):
    from formal.reference.isc_w1.codec import Delivery

    config = cfg.bind(bootstrap, storage_bootstrap, original_config, declaration)
    qc = decode(original_qc)
    _require(
        qc["body_hash"] == config.body_id
        and qc["context_id"] == config.context_id
        and int(qc["height"]) == config.height
        and int(qc["view"]) == config.view
        and qc["round_id"] == config.round_id
        and qc["validator_epoch_id"] == bootstrap.validator_epoch_id
        and qc["formal_semantics_id"] == bootstrap.formal_semantics_id
        and qc["quorum_threshold"] == 3,
        "whole original CONFIG QC context",
    )
    _uint(source_cut, 8)
    _require(type(delivered) is tuple, "complete original delivery inventory")
    matching, previous = {}, -1
    for source in delivered:
        _require(
            type(source) is DeliverySource and type(source.event) is Delivery,
            "original delivery shape",
        )
        event = source.event
        _uint(event.event_index, 8)
        _require(
            previous < event.event_index <= source_cut, "original ordered delivery occurrences"
        )
        previous = event.event_index
        signed = authenticate(
            AuthorityInputs(bootstrap, CONTRACT), backend, source.original_artifact
        )
        artifact = decode_artifact(source.original_artifact)
        _require(
            event.vote_frame == artifact.vote_bytes
            and event.key_id == artifact.key_id
            and event.signature_bytes == artifact.signature
            and event.signed_payload
            == preimage(artifact.registry_id, artifact.key_id, artifact.vote_bytes),
            "original delivery/artifact exact material",
        )
        vote = signed.vote.original
        # Unrelated retained votes stay in the inventory. Only the exact full
        # context/body group contributes to this certificate; no first-q cut.
        if (
            signed.vote.kind == "ROUND_CONFIG"
            and vote.body_hash == config.body_id
            and vote.context_id == config.context_id
        ):
            cfg.bind_vote(config, signed)
            prior = matching.get(vote.validator_id)
            _require(
                prior is None or prior == signed.vote_id,
                "same original signer/context has different durable vote identity",
            )
            matching[vote.validator_id] = signed.vote_id
    names = tuple(sorted(matching))
    vote_ids = tuple(matching[name] for name in names)
    _require(
        len(names) >= 3 and tuple(qc["signer_ids"]) == names and tuple(qc["vote_ids"]) == vote_ids,
        "FinalizeRoundConfig uses all matching delivered original signers/votes",
    )
    # qc_id remains the original field. Never invent a self-referential hash
    # equation or relabel a witness as its body identity.
    return BoundQC(original_qc, qc["qc_id"], config, delivered, names, vote_ids)
