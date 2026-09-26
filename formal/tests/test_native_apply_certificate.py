"""Source pins, complete native APPLY fields and honest structural scope."""

import copy
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_apply_certificate as g  # noqa: E402
import native_policy_codec as codec  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class NativeApplyCertificateTests(unittest.TestCase):
    def test_byte_reproduction(self):
        self.assertEqual(g.generate().encode(), g.TARGET.read_bytes())

    def test_complete_canonical_fields(self):
        data = g.source()
        for module, start, stop, doc, count in [
            ("NativeApplyProfile", "def fields ", "def json ", data[3], 10),
            ("NativeApplyCertificate", "def candidateFields ", "def candidateJSON ", data[4], 18),
            (
                "NativeApplyCertificate",
                "def certificateFields ",
                "def certificateJSON ",
                data[5],
                18,
            ),
        ]:
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            fields = re.findall(r'\("([a-z_]+)",', src.split(start)[1].split(stop)[0])
            self.assertEqual(fields, sorted(doc))
            self.assertEqual(len(fields), count)

    def test_original_wire_components_and_synthetic_qc(self):
        profile, candidate, cert, _, _, _, pid, cid, committee = g.source()
        self.assertEqual(candidate["apply_arithmetic_profile_id"], pid)
        self.assertEqual(cert["apply_candidate_id"], cid)
        self.assertEqual(cert["signer_ids"], committee)
        self.assertEqual(cert["quorum_threshold"], 3)
        self.assertEqual(profile["momentum"], {"numerator": 0, "denominator": 1})
        for kind, obj in [("apply_profile", profile), ("apply_candidate", candidate)]:
            raw = codec.encode_value(kind, obj)
            reader = codec.Reader(raw)
            self.assertEqual(reader.value(kind), obj)
            self.assertEqual(reader.at, len(raw))

    def test_original_policy_pin_rejects_changes(self):
        original = load_json_strict(
            ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
        )
        for name in ["codec-APPLY", "guard-APPLY"]:
            changed = copy.deepcopy(original)
            row = next(r for r in changed["observed"] if r["name"] == name)
            row["policy_hex"] = row["policy_hex"][:-2] + "ff"
            with self.subTest(name=name), patch.object(g, "load_json_strict", return_value=changed):
                with self.assertRaises(ValueError):
                    g.source()

    def test_rehashed_parent_substitution_rejects(self):
        original = g.prior.source()
        for key in ["merkle_root", "round_id", "eligibility_certificate_id"]:
            changed = copy.deepcopy(original)
            changed[0][key] += "x"
            with self.subTest(key=key), patch.object(g.prior, "source", return_value=changed):
                with self.assertRaises(ValueError):
                    g.source()

    def test_every_original_vector_and_parent_affects_candidate_id(self):
        _, _, _, _, original, _, _, cid, _ = g.source()
        for key in [
            "parent_optimizer_hash",
            "parent_checkpoint_id",
            "next_model_hash",
            "next_optimizer_hash",
            "aggregate_root_qc_id",
            "apply_arithmetic_profile_id",
        ]:
            changed = copy.deepcopy(original)
            changed[key] += "x"
            self.assertNotEqual(g.digest("deltareduce.008.apply-candidate.v1", changed), cid)
        for key in ["next_model_values", "next_optimizer_values"]:
            changed = copy.deepcopy(original)
            changed[key] = ["-00"]
            self.assertNotEqual(g.digest("deltareduce.008.apply-candidate.v1", changed), cid)
        # Original spellings are not silently normalized to a numeric value.
        a = copy.deepcopy(original)
        b = copy.deepcopy(original)
        a["next_model_values"] = ["-00"]
        b["next_model_values"] = ["0"]
        self.assertNotEqual(
            g.digest("deltareduce.008.apply-candidate.v1", a),
            g.digest("deltareduce.008.apply-candidate.v1", b),
        )

    def test_bounded_shared_prior_and_source_membership(self):
        source = (ROOT / "formal/proofs/DeltaReduce/NativeApplySection.lean").read_text("utf-8")
        for marker in [
            "NativeAggregateSection.bindSection sha p s",
            "selectedRoot",
            "selectedProfile",
            'trees p "apply_profiles"',
            'trees p "apply_candidates"',
            'trees p "apply_qcs"',
            '"finalized_apply_ids"',
        ]:
            self.assertIn(marker, source)
        src = (ROOT / "formal/proofs/DeltaReduce/NativeApplyLineage.lean").read_text("utf-8")
        for marker in [
            "root.id ∈ finalized",
            "d.candidate.parent = parent",
            "d.certificate.candidate = d.candidateId",
            "d.certificate.model = d.candidate.model",
            "d.certificate.optimizer = d.candidate.optimizer",
            "bothPayloadBounds",
        ]:
            self.assertIn(marker, src)
        self.assertNotIn("parentOptimizer =", src)
        for module in ["NativeApplyProfile", "NativeApplyCertificate"]:
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            self.assertIn("NativeContractSize.contentId", src)

    def test_explicit_counterchecks_and_all_axiom_audits(self):
        vectors = g.TARGET.read_text("utf-8")
        for name in [
            "valuesNotRecomputed",
            "parentOptimizerNotCompared",
            "retainedNegativeZero",
            "retainedNegativeLeadingZero",
            "negativeWireBits",
            "largeUnsignedDenominator",
        ]:
            self.assertIn("theorem " + name, vectors)
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text("utf-8").splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text("utf-8").splitlines()
        for module in [
            "NativeApplyProfile",
            "NativeApplyCertificate",
            "NativeApplyLineage",
            "NativeApplySection",
            "NativeApplyCertificateVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, imports)
            src = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", src, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
