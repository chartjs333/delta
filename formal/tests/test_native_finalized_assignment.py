"""Original certificate/proposal wire distinction and kernel regression inventory."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_parameter as generator  # noqa: E402
import native_policy_codec as codec  # noqa: E402


class FinalizedAssignmentTests(unittest.TestCase):
    def test_original_certificate_has_no_proposal_context(self):
        _, certificate, proposal, _, _, _ = generator.source()
        self.assertNotIn("vote_context_id", certificate)
        self.assertEqual(proposal["vote_context_id"], "PARAMETER:domain-a:shard-a")
        self.assertEqual(
            {k: v for k, v in certificate.items() if k not in ("signer_ids", "quorum_threshold")},
            {k: v for k, v in proposal.items() if k != "vote_context_id"},
        )
        # Independently pinned production field inventories retain distinct wires.
        self.assertNotIn("vote_context_id", dict(codec.SCHEMAS["parameter"]))
        self.assertIn("vote_context_id", dict(codec.SCHEMAS["parameter_body"]))
        self.assertNotEqual(
            codec.encode_value("parameter", certificate),
            codec.encode_value("parameter_body", proposal),
        )

    def test_kernel_regression_and_audit_coverage(self):
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8")
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8")
        for module in (
            "NativeFinalizedAssignment",
            "NativeFinalizedAssignmentVectors",
            "NativeCertifiedCorpus",
        ):
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("import DeltaReduce." + module, imports)
            self.assertNotRegex(source, r"\b(?:sorry|admit|native_decide)\b")
            for name in re.findall(r"^(?:def|theorem|structure|inductive) (\w+)", source, re.M):
                self.assertIn(f"#print axioms DeltaReduce.{module}.{name}", audit)


if __name__ == "__main__":
    unittest.main()
