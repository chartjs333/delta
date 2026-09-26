"""Original-source pinning and formal candidate authority integration checks."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_candidate_authority as g  # noqa: E402
import generate_native_policy_wal_vectors as native  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class NativeCandidateAuthorityTests(unittest.TestCase):
    def test_reproduction(self):
        self.assertEqual(g.generate().encode(), g.TARGET.read_bytes())

    def test_original_observation_pin(self):
        doc = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        bad = copy.deepcopy(doc)
        bad["observed"][0]["policy_hex"] += "00"
        with patch.object(g, "load_json_strict", return_value=bad):
            with self.assertRaisesRegex(ValueError, "original candidate observation"):
                g.sources()

    def test_original_parent_inventory(self):
        ps = g.sources()
        schema = (ROOT / "formal/proofs/DeltaReduce/NativePolicySchema.lean").read_text()
        parents = schema.split("def fmtParents", 1)[1].split("def fmtCandidate", 1)[0]
        self.assertEqual(re.findall(r'\.field "([^"]+)"', parents), g.FIELDS)
        self.assertEqual([p["candidates"][0]["action"] for p in ps], list(range(1, 10)))
        for p in ps:
            self.assertEqual(set(p["candidates"][0]["parents"]), set(g.FIELDS))

    def test_source_contexts_and_assignment(self):
        src = native.sources()["delta-core-cpp/src/consensus.cpp"].decode()
        fn = src.split("std::string vote_context_id(", 1)[1].split(
            "VoteInputSetBody project_input_set_vote_body", 1
        )[0]
        self.assertIn("return std::string(formal_parent_or_assignment);", fn)
        for name in ["config", "isc", "ec", "apc", "root", "apply", "view", "abort"]:
            self.assertIn("deltareduce.vote-context." + name + ".v1", fn)
        p = g.sources()[4]
        self.assertEqual(
            p["candidates"][0]["context_id"],
            p["snapshot"]["parameter_bodies"][0]["vote_context_id"],
        )
        self.assertFalse(p["candidates"][0]["context_id"].startswith("sha256:"))

    def test_source_checkpoint_guard_scope(self):
        src = native.sources()["delta-core-cpp/src/certificates/vote_admission.cpp"].decode()
        shape = src.split("void validate_candidate_shape(", 1)[1].split(
            "void validate_snapshot_sets(", 1
        )[0]
        self.assertIn("parent.parent_checkpoint_id, true, true", shape)
        self.assertNotIn("state.parent_checkpoint_id", shape)
        authority = src.split("void validate_candidate_authority(", 1)[1]
        self.assertIn("body->parent_checkpoint_id == state.parent_checkpoint_id", authority)
        self.assertIn("parent.norm_evidence_id == ec->certificate.norm_evidence_id", authority)
        self.assertIn("parent.seed_transcript_id == plan->seed_transcript_id", authority)
        self.assertIn("parent.parameter_matrix_root == body->merkle_root", authority)

    def test_source_composition_and_scope(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeCandidateAuthority.lean").read_text()
        for marker in [
            "NativeSnapshotBase.bindSnapshot sha p s",
            "checkAll sha p s b p.candidates",
            "NativePolicyBytes.decodePolicy policyRaw",
            "sourceSections",
            "iscOriginalBody",
            "ecOriginalBody",
            "failureTailOriginal",
            "NativeFailureAuthority.checkView sha p s b.prior.tail c",
            "NativeFailureAuthority.checkAbort sha p s b.prior.tail c",
        ]:
            self.assertIn(marker, src)
        for marker in ["with candidates :=", "graphEmpty", "otherAuthorized", "singleCandidate"]:
            self.assertNotIn(marker, src)
        vectors = g.TARGET.read_text()
        for name in [
            "wholeOriginalConfigBytes",
            "authorityDoesNotPrematurelyRequireCurrent",
            "changedNormParent",
            "changedSeedParent",
            "changedMatrix",
            "changedApplyIdentity",
            "changedCurrent",
            "missingTimeout",
            "abortAfterApply",
            "badSecondCannotBeSkipped",
            "duplicateContextRejected",
            "reversedOrderRejected",
        ]:
            self.assertIn("theorem " + name, vectors)
        self.assertIn("explicitly synthetic mixed", vectors)

    def test_all_actions_and_parents_have_kernel_cases(self):
        vectors = g.TARGET.read_text()
        for i in range(1, 10):
            for prefix in ["shape", "authority", "accepted", "wrongHeight", "wrongContext"]:
                self.assertIn("theorem " + prefix + str(i) + " ", vectors)
        self.assertEqual(len(re.findall(r"^theorem rejectParent_", vectors, re.M)), 15)
        self.assertEqual(len(re.findall(r"^def contextPre", vectors, re.M)), 8)
        # Hashes are independently derived from original observations, never fabricated digests.
        self.assertIn("hashlib.sha256(pre).digest()", Path(g.__file__).read_text())

    def test_all_named_declarations_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text().splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text().splitlines()
        for module in [
            "NativeCandidateShape",
            "NativeCandidateAuthority",
            "NativeCandidateAuthorityVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", src, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
