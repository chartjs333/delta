"""Exact original native command capture and mixed-slot source composition."""

import json
import unittest
from dataclasses import replace
from pathlib import Path

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.isc_w1.codec import Frame, encode_frame
from formal.reference.profile_source import capsule_binding as w
from formal.reference.profile_source import commands as c

ROOT = Path(__file__).resolve().parents[3]
LEGACY = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"


class CommandsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(
            (ROOT / "formal/proposals/native-transition-vectors.json").read_text()
        )["cases"]
        cls.native = json.loads(
            (ROOT / "formal/proposals/evidence/native-transition/cpp-cross-check.json").read_text()
        )
        assert cls.native["source_commit"] == c.PIN

    def setUp(self):
        self.case = self.cases[0]
        self.state = bytes.fromhex(self.case["prior_hex"])
        self.command = bytes.fromhex(self.case["command_hex"])
        self.output = c.execute(LEGACY, self.state, self.command)
        self.frame = Frame(
            2,
            1,
            (self.command, self.output.next_state, self.output.effects, self.output.record),
        )

    def test_all_original_native_captured_commands_keep_exact_bytes_and_errors(self):
        for case, observed in zip(self.cases, self.native["observed"], strict=True):
            with self.subTest(case=case["name"]):
                self.assertEqual(case["expected"], observed)
                if not observed["accepted"]:
                    with self.assertRaisesRegex(CodecError, observed["error"]):
                        c.execute(
                            LEGACY,
                            bytes.fromhex(case["prior_hex"]),
                            bytes.fromhex(case["command_hex"]),
                        )
                    continue
                result = c.execute(
                    LEGACY, bytes.fromhex(case["prior_hex"]), bytes.fromhex(case["command_hex"])
                )
                for field, raw in (
                    ("state_hex", result.next_state),
                    ("effects_hex", result.effects),
                    ("record_hex", result.record),
                ):
                    self.assertEqual(raw.hex(), observed[field])
                for field in ("command_id", "next_id", "effects_id", "record_id"):
                    self.assertEqual(getattr(result, field), observed[field])

    def test_coarse_counter_is_not_physical_slot_and_retry_does_not_allocate(self):
        m = c.initial(LEGACY, self.state, 10)
        result = c.persisted(LEGACY, m, self.frame)
        self.assertEqual(w.read_state(result.state, LEGACY)["durable_sequence"], "1")
        self.assertEqual(result.requests[0].physical_slot, 2)
        self.assertTrue(result.invalidated)
        self.assertEqual(result.tick, 11)
        self.assertIs(c.retry(LEGACY, result, self.command), result.requests[0])
        self.assertEqual(len(result.requests), 1)
        with self.assertRaisesRegex(CodecError, "duplicate original request"):
            c.persisted(LEGACY, result, replace(self.frame, sequence=3))

    def test_whole_effect_and_inner_record_substitution_rejects(self):
        m = c.initial(LEGACY, self.state, 10)
        for index in (1, 2, 3):
            parts = list(self.frame.sections)
            parts[index] += b"ignored-suffix"
            with self.assertRaisesRegex(CodecError, "whole original command output"):
                c.persisted(LEGACY, m, replace(self.frame, sections=tuple(parts)))
        with self.assertRaisesRegex(CodecError, "time moved backwards"):
            c.persisted(LEGACY, c.initial(LEGACY, self.state, 12), self.frame)

    def test_future_generation_is_selected_independently_no_legacy_fallback(self):
        # New synthetic objects of an independently supplied symbolic generation.
        # No existing object is rewritten by execute, and no sigma is assigned.
        sigma = "sha256:" + "9" * 64
        s = w.read_state(self.state, LEGACY)
        command = w.read_command(self.command, LEGACY)
        s["formal_semantics_id"] = sigma
        command["formal_semantics_id"] = sigma
        new_state, new_command = w.envelope(5, s), w.envelope(6, command)
        result = c.execute(sigma, new_state, new_command)
        self.assertEqual(result.original_state, new_state)
        self.assertEqual(result.original_command, new_command)
        self.assertNotEqual(result.command_id, self.output.command_id)
        self.assertNotEqual(result.effects_id, self.output.effects_id)
        with self.assertRaisesRegex(CodecError, "independent semantics"):
            c.execute(sigma, self.state, self.command)
        with self.assertRaisesRegex(CodecError, "independent semantics"):
            c.execute(LEGACY, new_state, new_command)

    def test_complete_mixed_positions_without_forging_vote_legality(self):
        # Deliberately opaque nonempty vote: this projection must retain it as
        # unqualified, never turn structural scan success into full admission.
        vote = Frame(1, 2, (b"original-vote", b"", b"", b"original-policy"))
        raw = encode_frame(vote) + encode_frame(self.frame)
        folded = c.prefix(LEGACY, self.state, 10, raw, cut_slot=1, required_prefix=raw)
        self.assertEqual(folded.cut.state, self.state)
        self.assertEqual(folded.target.state, self.output.next_state)
        self.assertEqual(folded.before(2), folded.initial)
        self.assertEqual(folded.pending_protocol, (folded.journal.positions[0],))
        self.assertEqual(folded.pending_protocol[0].original, encode_frame(vote))
        self.assertEqual(folded.target.requests[0].physical_slot, 2)


if __name__ == "__main__":
    unittest.main()
