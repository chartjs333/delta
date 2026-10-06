"""Exact approved ISC-EVIDENCE-BUDGET-v1 checks over complete W1 contents.

These resource guards neither authenticate a delivery nor derive source origin.
They do not truncate/reorder inventories or replace existing schema/admission checks.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto.codec import EVIDENCE_LIMITS, _id, _label, _require, decode_vote
from formal.reference.isc_w1.codec import (
    Delivery,
    Frame,
    decode_candidate_state,
    decode_receipt,
    decode_request_source,
    encode_frame,
)


@dataclass(frozen=True)
class Sizes:
    events: int
    delivery_bytes: int
    wal_bytes: int
    result_bytes: int


def limit(name: str) -> int:
    return int(EVIDENCE_LIMITS[name])


def delivery_size(delivery: Delivery) -> int:
    _label(delivery.peer_id)
    _id(delivery.key_id)
    _require(len(delivery.peer_id) <= limit("max_peer_id_bytes"), "peer byte budget")
    _require(len(delivery.vote_frame) <= limit("max_vote_frame_bytes"), "vote byte budget")
    _require(len(delivery.signed_payload) <= limit("max_signed_payload_bytes"), "payload budget")
    _require(len(delivery.signature_bytes) == limit("signature_bytes"), "signature size")
    return 28 + sum(
        len(value)
        for value in (
            delivery.peer_id,
            delivery.vote_frame,
            delivery.signed_payload,
            delivery.signature_bytes,
            delivery.key_id,
        )
    )


def inventory_size(deliveries: tuple[Delivery, ...], round_id: str, epoch: str) -> int:
    _require(len(deliveries) <= limit("max_delivery_events"), "cumulative delivery event budget")
    previous, size = 0, 0
    for delivery in deliveries:
        _require(
            type(delivery.event_index) is int and previous < delivery.event_index,
            "original event order",
        )
        previous = delivery.event_index
        size += delivery_size(delivery)
        _require(size <= limit("max_delivery_bytes"), "cumulative delivery byte budget")
        vote = decode_vote(delivery.vote_frame)
        _require(
            vote.round_id == round_id and vote.validator_epoch_id == epoch, "round/epoch inventory"
        )
    return size


def check_frame(frame: Frame, round_id: str, epoch: str) -> Sizes:
    _require(frame.kind == 3, "finalization frame required")
    raw = encode_frame(frame)
    source = decode_request_source(frame.sections[0])
    state = decode_candidate_state(frame.sections[1])
    receipt = decode_receipt(frame.sections[3])
    _id(source.source_index_id)
    requirements = (
        (len(source.command_bytes), "max_command_bytes"),
        (len(source.prior_state_bytes), "max_round_state_bytes"),
        (len(source.prior_policy_bytes), "max_policy_bytes"),
        (len(state.policy_bytes), "max_policy_bytes"),
        (len(state.certificate_bytes), "max_isc_bytes"),
        (len(frame.sections[2]), "max_effect_bytes"),
        (len(raw), "max_wal_frame_bytes"),
    )
    for size, name in requirements:
        _require(size <= limit(name), name)
    delivery_bytes = inventory_size(source.deliveries, round_id, epoch)
    expected_source = (
        76
        + len(source.command_bytes)
        + 71
        + len(source.prior_state_bytes)
        + len(source.prior_policy_bytes)
        + delivery_bytes
    )
    expected_state = 16 + len(state.policy_bytes) + len(state.certificate_bytes)
    _require(len(frame.sections[0]) == expected_source, "exact IFQ1 size")
    _require(len(frame.sections[1]) == expected_state, "exact IFS1 size")
    _require(
        len(frame.sections[3]) == 369 and receipt.sequence == frame.sequence, "exact IFR1 size"
    )
    expected_wal = 72 + expected_source + expected_state + len(frame.sections[2]) + 369
    _require(len(raw) == expected_wal, "exact DRW1 size")
    result = 12 + 369 + len(frame.sections[2]) + len(state.certificate_bytes)
    _require(result <= limit("max_output_bytes"), "exact output byte budget")
    return Sizes(len(source.deliveries), delivery_bytes, len(raw), result)
