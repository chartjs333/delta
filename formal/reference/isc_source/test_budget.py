"""Exact sizes and retained multiplicity; opaque policy bytes confer no authority."""

import unittest
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto.codec import CodecError, Vote, encode_vote, preimage
from formal.reference.isc_source.budget import check_frame, inventory_size
from formal.reference.isc_w1.codec import (
    CandidateState,
    Delivery,
    Frame,
    Receipt,
    RequestSource,
    encode_candidate_state,
    encode_frame,
    encode_receipt,
    encode_request_source,
)


def synthetic_delivery(index=1, view=0):
    # Synthetic canonical bytes; an all-zero signature is intentionally not authenticated.
    identifier = "sha256:" + "0" * 64
    vote = Vote(identifier, identifier, 2, identifier, 1, "round-1", identifier, "a", view)
    raw = encode_vote(vote)
    return Delivery(
        index, "relay", raw, preimage(identifier, identifier, raw), bytes(64), identifier
    )


def synthetic_frame(deliveries=(), command_bytes=65536, effects=1048576, certificate=4194304):
    source = RequestSource(
        b"x" * command_bytes,
        0,
        sha256(b"").digest(),
        "sha256:" + "0" * 64,
        max((d.event_index for d in deliveries), default=0),
        b"state",
        b"policy-0",
        deliveries,
    )
    candidate = CandidateState(b"policy-1", b"c" * certificate)
    receipt = Receipt(
        1,
        "sha256:" + "1" * 64,
        "sha256:" + "2" * 64,
        "sha256:" + "3" * 64,
        sha256(source.prior_policy_bytes).hexdigest(),
        sha256(candidate.policy_bytes).hexdigest(),
    )
    return Frame(
        1,
        3,
        (
            encode_request_source(source),
            encode_candidate_state(candidate),
            b"e" * effects,
            encode_receipt(receipt),
        ),
    )


class BudgetTests(unittest.TestCase):
    def test_complete_w1_and_result_sizes_are_exact(self):
        frame = synthetic_frame((synthetic_delivery(),))
        sizes = check_frame(frame, "round-1", "sha256:" + "0" * 64)
        self.assertEqual(sizes.events, 1)
        self.assertEqual(sizes.wal_bytes, len(encode_frame(frame)))
        self.assertEqual(sizes.result_bytes, 5243261)

    def test_finer_command_and_effect_budget_fail_before_append(self):
        for frame in (
            synthetic_frame(command_bytes=65537),
            synthetic_frame(effects=1048577),
        ):
            # Approved legacy framing permits these, successor admission does not.
            encode_frame(frame)
            with self.assertRaises(CodecError):
                check_frame(frame, "round-1", "sha256:" + "0" * 64)

    def test_repeated_delivery_and_view_change_do_not_reset_counter(self):
        first = synthetic_delivery()
        inventory = tuple(replace(first, event_index=i) for i in range(1, 4097))
        size = inventory_size(inventory, "round-1", "sha256:" + "0" * 64)
        self.assertEqual(size, 4096 * inventory_size((first,), "round-1", "sha256:" + "0" * 64))
        additional = synthetic_delivery(4097, view=1)
        with self.assertRaisesRegex(CodecError, "cumulative delivery event"):
            inventory_size((*inventory, additional), "round-1", "sha256:" + "0" * 64)
        self.assertEqual(len(inventory), 4096)

    def test_duplicate_event_index_is_not_normalized(self):
        first = synthetic_delivery()
        with self.assertRaisesRegex(CodecError, "event order"):
            inventory_size((first, first), "round-1", "sha256:" + "0" * 64)


if __name__ == "__main__":
    unittest.main()
