"""Source-derived shared snapshot base and proposed certificate boundary checks."""

import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_policy_wal_vectors as native  # noqa: E402
import generate_native_snapshot_base as g  # noqa: E402
from formal_artifacts import canonical_json_bytes, load_json_strict  # noqa: E402


class NativeSnapshotBaseTests(unittest.TestCase):
    def test_reproduction(self):
        self.assertEqual(g.generate().encode(), g.TARGET.read_bytes())

    def test_original_policy_pin(self):
        doc = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        bad = copy.deepcopy(doc)
        bad["observed"][0]["policy_hex"] += "00"
        with patch.object(g, "load_json_strict", return_value=bad):
            with self.assertRaisesRegex(ValueError, "original policy observation"):
                g.source()

    def test_complete_proposal_certificate_is_derived(self):
        p, raw, digest = g.source()
        c, _, committee, _ = g.prior.source()
        self.assertEqual(committee, p["validator_ids"])
        expected = {**c, "signer_ids": committee, "quorum_threshold": 3}
        self.assertEqual(raw, canonical_json_bytes(expected))
        self.assertNotEqual(raw, canonical_json_bytes(c))
        self.assertEqual(
            digest, hashlib.sha256(b"deltareduce.008.input-set-certificate.v1\0" + raw).digest()
        )

    def test_native_constructor_scope(self):
        blobs = native.sources()
        admission = blobs["delta-core-cpp/src/certificates/vote_admission.cpp"].decode()
        verifier = blobs["delta-core-cpp/src/certificates/verifier.cpp"].decode()
        contracts = blobs["delta-core-cpp/src/certificates/contracts.cpp"].decode()
        constructor = verifier.split("ChainVerifier::ChainVerifier", 1)[1].split(
            "void ChainVerifier::validate_signers", 1
        )[0]
        self.assertIn("validate_context(expected_context_, expected_context_)", constructor)
        self.assertNotIn("require_label", constructor)
        self.assertIn('require_label(value.round_id, "round ID is invalid")', contracts)
        self.assertIn('require_label(signer, "signer ID is invalid")', contracts)
        self.assertIn("require_sorted_ids(policy.validator_ids, false)", admission)
        expansion = admission.split("as_input_certificate(", 1)[1].split("\n}", 1)[0]
        for marker in [
            "body.context",
            "body.input_root",
            "body.tuples",
            "quorum_threshold(policy)",
            "policy.validator_ids",
        ]:
            self.assertIn(marker, expansion)

    def test_actual_composition_and_original_sources(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeSnapshotBase.lean").read_text("utf-8")
        for marker in [
            "NativeFailureSection.bindSection sha p s",
            "NativePolicyBytes.decodePolicy policyRaw",
            "NativeStateBytes.decodeState stateRaw",
            "NativePolicyBytes.acceptedCanonical hp",
            "closedHasOriginalBody",
            "everyInputBounded",
        ]:
            self.assertIn(marker, src)
        for marker in ["with candidates :=", "graphEmpty", "otherAuthorized", "singleCandidate"]:
            self.assertNotIn(marker, src)
        proposed = (ROOT / "formal/proofs/DeltaReduce/NativeProposedIsc.lean").read_text("utf-8")
        for marker in [
            "NativeInputSetBody.check sha expected source",
            "NativeContractSize.contentId sha",
            "NativeIscCertificate.json c",
            "exactPosition",
            "nonLabelSignerRejected",
        ]:
            self.assertIn(marker, proposed)

    def test_missing_base_checks_have_kernel_negatives(self):
        vectors = g.TARGET.read_text("utf-8")
        for name in [
            "wrongProposedConfig",
            "wrongFinalizedConfig",
            "invalidAccumulator",
            "missingClosedBody",
            "certificateIsNotClosedBody",
            "duplicateClosed",
            "duplicateBody",
            "wrongRoundStillRejected",
            "unusedValidatorAllowed",
            "unusedNotASigner",
            "proposalUsesItRejects",
            "boundedProjectionRequired",
        ]:
            self.assertIn("theorem " + name, vectors)

    def test_actual_json_limit_is_independent_of_wire(self):
        # This is a mathematical size witness, not an accepted native policy or new native run.
        c, tree, _, _ = g.prior.source()
        large = {**c, "tuples": c["tuples"] * 18000}
        raw = canonical_json_bytes(large)
        proposed = {k: tree[k] for k in ["context", "input_root", "tuples"]}
        proposed["tuples"] *= 18000
        wire = g.codec.encode_value("input_set_body", proposed)
        self.assertGreater(len(raw), 4 * 1024 * 1024)
        self.assertLess(len(wire), 4 * 1024 * 1024)
        src = (ROOT / "formal/proofs/DeltaReduce/NativeProposedIsc.lean").read_text("utf-8")
        self.assertIn("NativeContractSize.contentId", src)
        self.assertIn("oversizedRejected", src)

    def test_all_named_declarations_audited(self):
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in [
            "NativeIscCertificate",
            "NativeProposedIsc",
            "NativeSnapshotBase",
            "NativeSnapshotBaseVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", src, re.M):
                self.assertTrue(
                    "#print axioms DeltaReduce." + module + "." + name in audit, module + "." + name
                )


if __name__ == "__main__":
    unittest.main()
