"""Pure W1 candidate assembly; no provenance admission, append or exposure.

The complete P0 and source cut must subsequently be derived by the independent
origin checker. This helper checks the local FinalizeISC conjuncts and preserves
every other source field. A successfully assembled candidate is not READY/GO.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass

from formal.reference.isc_crypto.codec import _require, _uint
from formal.reference.isc_crypto.sodium_reference import SodiumReference
from formal.reference.isc_source.authentication import (
    Bootstrap,
    authenticate,
    bind_delivery,
    delivered_signers,
)
from formal.reference.isc_source.budget import inventory_size
from formal.reference.isc_source.identity import (
    Body,
    Certificate,
    InputTuple,
    body_id,
    certificate_bytes,
    certificate_id,
)
from formal.reference.isc_source.policy import decode, encode
from formal.reference.isc_w1.codec import Delivery


@dataclass(frozen=True)
class DeliverySource:
    event: Delivery
    original_g: bytes
    original_body: Body


@dataclass(frozen=True)
class Cut:
    """Primitive source values, not a boolean claiming legality or refinement.

    ordinary_active is deliberately absent: the full origin checker must derive
    that separate phase condition. This component cannot certify a transition.
    """

    state_id: str
    parent_checkpoint_id: str
    height: int
    view: int
    logical_tick: int
    frozen_inputs: tuple[InputTuple, ...]
    delivered: tuple[DeliverySource, ...]


@dataclass(frozen=True)
class Candidate:
    prior_policy: bytes
    next_policy: bytes
    certificate: bytes
    consensus_id: str
    witness_id: str
    original_deliveries: tuple[DeliverySource, ...]


def body_tree(body: Body) -> dict:
    fields = asdict(body)
    return {
        "context": {
            key: fields[key]
            for key in (
                "arithmetic_profile_id",
                "height",
                "parameter_schema_id",
                "round_config_id",
                "round_id",
                "validator_epoch_id",
                "view",
            )
        },
        "parent_checkpoint_id": body.parent_checkpoint_id,
        "input_root": body.input_root,
        "tuples": [asdict(value) for value in body.tuples],
    }


def certificate_tree(value: Certificate) -> dict:
    return {
        **body_tree(value.body),
        "quorum_threshold": value.quorum_threshold,
        "signer_ids": list(value.signer_ids),
    }


def read_certificate_tree(sigma: str, value: dict) -> Certificate:
    return Certificate(
        Body(
            formal_semantics_id=sigma,
            **value["context"],
            parent_checkpoint_id=value["parent_checkpoint_id"],
            input_root=value["input_root"],
            tuples=tuple(InputTuple(**row) for row in value["tuples"]),
        ),
        tuple(value["signer_ids"]),
        value["quorum_threshold"],
    )


def assemble_first(
    bootstrap: Bootstrap, backend: SodiumReference, prior: bytes, body: Body, cut: Cut
) -> Candidate:
    """No first-q selection, lineage clearing, byte migration or replay synthesis.

    Phase/complete origin/source-event provenance are NOT established here.
    Caller-supplied P0/cut never becomes authority through this return value.
    """
    policy = decode(prior)
    snapshot = policy["snapshot"]
    b = body_id(body)
    for value in (cut.height, cut.view, cut.logical_tick):
        _uint(value, 8)
    _require(
        body.formal_semantics_id == bootstrap.formal_semantics_id
        and body.validator_epoch_id == bootstrap.validator_epoch_id
        and policy["validator_epoch_id"] == bootstrap.validator_epoch_id
        and policy["validator_ids"] == [name for name, _ in bootstrap.validators]
        and policy["local_validator_id"] in policy["validator_ids"],
        "independent fixed-epoch binding",
    )
    _require(
        policy["round_id"] == body.round_id
        and policy["round_config_id"] == body.round_config_id
        and snapshot["parameter_schema_id"] == body.parameter_schema_id
        and snapshot["arithmetic_profile_id"] == body.arithmetic_profile_id
        and snapshot["state_id"] == cut.state_id
        and cut.parent_checkpoint_id == body.parent_checkpoint_id
        and cut.height == body.height
        and cut.view == body.view,
        "source cut context binding",
    )
    _require(
        body.round_config_id in snapshot["finalized_round_config_ids"]
        and b in snapshot["closed_input_set_ids"]
        and body_tree(body) in snapshot["input_set_bodies"]
        and body.tuples == cut.frozen_inputs,
        "exact finalized configuration and closed frozen body",
    )
    _require(
        policy["initial_logical_tick"] <= cut.logical_tick < policy["hard_deadline_tick"]
        and not snapshot["abort_requests"],
        "ordinary time/abort guard",
    )

    previous = tuple(
        read_certificate_tree(bootstrap.formal_semantics_id, row)
        for row in snapshot["input_set_certificates"]
    )
    previous_ids = [certificate_id(value) for value in previous]
    _require(previous_ids == sorted(set(previous_ids)), "original witness order/uniqueness")
    finalized = snapshot["finalized_input_set_ids"]
    _require(finalized == sorted(set(finalized)), "original finalized body order")
    represented = {body_id(value.body) for value in previous}
    _require(set(finalized) <= represented, "finalized body missing original witness")
    _require(
        b not in finalized
        and not any(
            value.body.round_id == body.round_id and body_id(value.body) in finalized
            for value in previous
        ),
        "already finalized round: original replay receipt required",
    )

    inventory_size(
        tuple(row.event for row in cut.delivered), body.round_id, body.validator_epoch_id
    )
    authenticated = []
    for source in cut.delivered:
        verified = authenticate(bootstrap, backend, source.original_g, source.original_body)
        bind_delivery(verified, source.event)
        authenticated.append(verified)
    signers = delivered_signers(body, tuple(authenticated))
    _require(len(signers) >= 3, "insufficient distinct matching original signers")
    certificate = Certificate(body, signers)
    raw, c = certificate_bytes(certificate), certificate_id(certificate)
    existing = dict(zip(previous_ids, previous, strict=True))
    _require(c not in existing or existing[c] == certificate, "original witness identity collision")
    existing[c] = certificate
    result = deepcopy(policy)
    result["snapshot"]["input_set_certificates"] = [
        certificate_tree(existing[key]) for key in sorted(existing)
    ]
    result["snapshot"]["finalized_input_set_ids"] = sorted(set(finalized) | {b})
    # Exact full generation size is checked before this candidate can be returned.
    following = encode(result)
    return Candidate(prior, following, raw, b, c, cut.delivered)
