"""Strict flat DRC1 diagnostic subset, not the production general-purpose decoder."""

import hashlib
import re

from native_certificate_chain import NATIVE_SEMANTICS

STATE_FIELDS = set(
    "available_ticket_count committed_ticket_count config_id durable_sequence "
    "formal_semantics_id height parent_checkpoint_id phase round_id schema_version "
    "state_root ticket_count type_name view".split()
)
VOTE_FIELDS = set(
    "body_hash context_id durable_sequence formal_semantics_id height kind round_id "
    "schema_version signature_id type_name validator_epoch_id validator_id view".split()
)
COUNT_FIELDS = {"available_ticket_count", "committed_ticket_count", "ticket_count"}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def decode_flat(raw, kind):
    """Accept only the exact pinned state/vote shapes; resource limits are proposal limits."""
    require(type(raw) is bytes and 12 <= len(raw) <= 16384, "diagnostic byte bound")
    require(kind in {3, 5}, "diagnostic kind")
    require(raw[:6] == b"DRC1\x01\x00", "DRC1 header")
    require(int.from_bytes(raw[6:8], "big") == kind, "DRC1 type")
    require(int.from_bytes(raw[8:12], "big") == len(raw) - 12, "DRC1 length")
    cursor = 12

    def take(count):
        nonlocal cursor
        require(cursor + count <= len(raw), "truncated DRC1")
        result = raw[cursor : cursor + count]
        cursor += count
        return result

    def text():
        require(take(1) == b"\x21", "DRC1 text tag")
        count = int.from_bytes(take(4), "big")
        require(count <= 4096, "DRC1 text bound")
        value = take(count)
        require(all(32 <= c <= 126 for c in value), "DRC1 ASCII")
        return value.decode("ascii")

    require(take(1) == b"\x31", "DRC1 flat map")
    count = int.from_bytes(take(4), "big")
    fields = STATE_FIELDS if kind == 5 else VOTE_FIELDS
    require(count == len(fields), "DRC1 exact field count")
    result = {}
    prior = ""
    for _ in range(count):
        key = text()
        require(key in fields and prior < key, "DRC1 field/order")
        prior = key
        if kind == 5 and key in COUNT_FIELDS:
            require(take(1) == b"\x10", "DRC1 unsigned count")
            value = int.from_bytes(take(8), "big")
            require(value < 2**32, "DRC1 uint32 count")
        else:
            value = text()
        result[key] = value
    require(cursor == len(raw), "DRC1 trailing bytes")
    require(result["formal_semantics_id"] == NATIVE_SEMANTICS, "native old semantics")
    require(result["schema_version"] == "1.0.0", "native schema")
    require(result["type_name"] == ("ROUND_STATE" if kind == 5 else "VOTE"), "native type name")
    for key in ["height", "view", "durable_sequence"]:
        require(re.fullmatch(r"0|[1-9][0-9]*", result[key]) is not None, "native decimal")
        require(int(result[key]) < 2**64, "native uint64")
    ids = (
        ["config_id", "parent_checkpoint_id", "state_root"]
        if kind == 5
        else ["body_hash", "signature_id", "validator_epoch_id"]
    )
    for key in ids:
        require(re.fullmatch(r"sha256:[0-9a-f]{64}", result[key]) is not None, "native content ID")
    if kind == 5:
        require(
            result["available_ticket_count"]
            <= result["committed_ticket_count"]
            <= result["ticket_count"],
            "native count order",
        )
    # Phase/kind/identifier semantic admission is still executed by pinned C++.
    return result


def state_id(raw):
    decode_flat(raw, 5)
    return "sha256:" + hashlib.sha256(b"deltareduce:003:round-state:v1\0" + raw).hexdigest()


def bind_state(raw, expected):
    require(state_id(raw) == expected, "native state preimage")
    return {
        "fields": decode_flat(raw, 5),
        "native_state_id": expected,
        "inner_state_root_preimage_verified": False,
        "closed_input_origin_authenticated": False,
        "full_public_state_relation": False,
        "native_export_authenticated": False,
    }
