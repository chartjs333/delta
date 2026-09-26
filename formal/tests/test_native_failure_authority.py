"""Native VIEW/ABORT source correspondence and explicit partial-admission scope."""

import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_failure_authority as g  # noqa: E402
import native_policy_codec as codec  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class NativeFailureAuthorityTests(unittest.TestCase):
    def test_reproduction(self):
        self.assertEqual(g.generate().encode(), g.TARGET.read_bytes())

    def test_original_vote_pin_rejects_changes(self):
        original = load_json_strict(g.votes.previous.FOLDER / "cpp-cross-check.json")
        changed = copy.deepcopy(original)
        changed["observed"][0]["frame_hex"] += "00"
        with patch.object(g, "load_json_strict", return_value=changed):
            with self.assertRaises(ValueError):
                g.source()

    def test_contexts_derive_from_original_bodies_and_vote_bytes(self):
        data = g.source()
        for i, (policy, body, pre, identifier) in enumerate(data):
            payload = g.prior.text64(policy["round_id"])
            if i == 0:
                payload += g.prior.u64(body["from_view"])
            self.assertEqual(pre, g.DOMAINS[i].encode() + b"\0" + payload)
            self.assertEqual(identifier, "sha256:" + hashlib.sha256(pre).hexdigest())
            self.assertEqual(identifier, policy["candidates"][0]["context_id"])

    def test_native_wire_ids_are_not_certificate_labels(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeFailurePayload.lean").read_text("utf-8")
        self.assertIn("WireId t.round", src)
        self.assertIn("WireId r.round", src)
        self.assertNotIn("Label", src)
        for value in ["round with spaces", "round/@!?", "a" * 129]:
            raw = codec.encode_value("text", value)
            reader = codec.Reader(raw)
            self.assertEqual(reader.value("text"), value)
        with self.assertRaises(ValueError):
            codec.encode_value("text", "a" * 4097)

    def test_every_parent_slot_has_a_kernel_countercheck(self):
        fields = codec.SCHEMAS["parents"]
        self.assertEqual(len(fields), 15)
        vectors = g.TARGET.read_text("utf-8")
        for field, _ in fields[2:-1]:
            self.assertIn("theorem forbidden_" + field, vectors)
        self.assertEqual(len(fields[2:-1]), 12)

    def test_original_candidate_membership_actual_prior_and_bytes(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeFailureAuthority.lean").read_text("utf-8")
        for marker in [
            "NativeFailureSection.bindSection sha p s",
            "t.views.find?",
            "t.timeouts.find?",
            "t.aborts.find?",
            "s.view < 256^8-1",
            "t.lineage.applies = []",
            "viewOriginalRow",
            "abortOriginalRow",
        ]:
            self.assertIn(marker, src)
        vote = (ROOT / "formal/proofs/DeltaReduce/NativeFailureVote.lean").read_text("utf-8")
        for marker in [
            "p.candidates.find? (matching s v)",
            "NativeFailureAuthority.bindCandidate sha p s c",
            "NativeVoteBytes.decodeFrame voteRaw",
            "exactVoteBytes",
            "r.recovery = true \u2228 r.ready = true",
            "r.invalidated = false",
        ]:
            self.assertIn(marker, vote)

    def test_guard_boundaries_and_scope_are_explicit(self):
        vectors = g.TARGET.read_text("utf-8")
        for name in [
            "viewTooEarly",
            "viewAtHard",
            "abortTooEarly",
            "foreignRequestBlocksView",
            "foreignRequestDoesNotEnableAbort",
            "exactRequestEnablesEarly",
            "replayWithoutReady",
            "uint64NoWrap",
            "scopeViewParentNotYetCurrent",
            "selectedParentMustBeCurrent",
            "noParameter",
            "noApply",
        ]:
            self.assertIn("theorem " + name, vectors)
        src = (ROOT / "formal/proofs/DeltaReduce/NativeFailureVote.lean").read_text("utf-8")
        self.assertIn("t.requests = []", src)
        self.assertIn("requested p t = true \u2228 p.hardDeadline ≤ r.tick", src)
        self.assertNotIn("otherAuthorized", src)

    def test_all_named_definitions_and_theorems_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for m in [
            "NativeFailurePayload",
            "NativeFailureAuthority",
            "NativeFailureVote",
            "NativeFailureAuthorityVectors",
        ]:
            self.assertIn("import DeltaReduce." + m, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{m}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", src, re.M):
                self.assertIn("#print axioms DeltaReduce." + m + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
