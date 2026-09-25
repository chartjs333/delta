"""Necessary frozen-input relations; no root/availability/native-state authority."""

from native_certificate_chain import decode_certificate, keys
from native_isc_body import require


def bind_frozen_isc(raw, identifier, frozen, domain_by_ticket):
    """Derive tuple fields, not a caller-supplied full body translation.

    Frozen rows must originate from a separately authenticated native ledger;
    this function cannot establish that premise from a list or its hash.
    Native FrozenInput has no domain or content/root preimage.
    """
    isc = decode_certificate(raw, identifier, "INPUT_SET_CERTIFICATE")
    require(type(frozen) is list and 0 < len(frozen) <= 4096, "frozen row bound")
    require(type(domain_by_ticket) is dict, "domain mapping type")
    projected, tickets = [], []
    for row in frozen:
        keys(row, "ticket_id commitment_id availability_certificate_id")
        ticket = row["ticket_id"]
        require(type(ticket) is str and ticket in domain_by_ticket, "missing domain metadata")
        projected.append({**row, "domain_id": domain_by_ticket[ticket]})
        tickets.append(ticket)
    require(tickets == sorted(set(tickets)), "frozen row order/uniqueness")
    require(projected == isc["tuples"], "frozen ISC tuple mismatch")
    return {
        "tuples": projected,
        "input_root": isc["input_root"],
        "root_preimage_verified": False,
        "native_export_authenticated": False,
        "full_public_close_relation": False,
    }


def check_required_ticket_coverage(frozen, required, policy):
    """Only the CloseInput ticket-coverage conjunct, NOT production Next/admission."""
    require(type(required) is list and all(type(t) is str for t in required), "required tickets")
    require(required == sorted(set(required)), "required ticket order")
    require(type(frozen) is list, "frozen rows")
    for row in frozen:
        keys(row, "ticket_id commitment_id availability_certificate_id")
        require(type(row["ticket_id"]) is str, "ticket type")
    tickets = [row["ticket_id"] for row in frozen]
    require(tickets == sorted(set(tickets)), "frozen row order/uniqueness")
    require(set(tickets) <= set(required), "foreign frozen ticket")
    require(policy in ("OMIT_UNAVAILABLE", "ABORT_ON_INCOMPLETE"), "close policy")
    require(policy == "OMIT_UNAVAILABLE" or tickets == required, "incomplete required tickets")
    return tickets
