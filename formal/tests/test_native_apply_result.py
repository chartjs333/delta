"""Provenance, generated component vectors and explicit missing source bindings."""

import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_apply_result as generator  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class NativeApplyResultTests(unittest.TestCase):
    def test_pinned_source_copies(self):
        boundary = load_json_strict(generator.EVIDENCE / "native-source-boundary.json")
        self.assertEqual(boundary["commit"], "60c692f6e391f839829dfc64e93380db54cd507b")
        for row in boundary["files"]:
            raw = subprocess.check_output(
                ["git", "show", boundary["commit"] + ":" + row["path"]], cwd=ROOT
            )
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
            self.assertEqual(raw, (generator.EVIDENCE / row["copy"]).read_bytes())

    def test_byte_exact_regeneration_and_real_hash_samples(self):
        lean, fixture = generator.generate()
        self.assertEqual(
            lean, (ROOT / "formal/proofs/DeltaReduce/NativeApplyResultVectors.lean").read_text()
        )
        self.assertEqual(
            fixture, load_json_strict(ROOT / "formal/proposals/native-apply-result-vectors.json")
        )
        self.assertEqual(len(fixture["hash_samples"]), 3)
        for row in fixture["hash_samples"]:
            self.assertEqual(
                hashlib.sha256(bytes.fromhex(row["preimage_hex"])).hexdigest(), row["sha256"]
            )
        self.assertFalse(fixture["full_source_join_example"])
        self.assertFalse(fixture["gate_eligible"])

    def test_native_engine_hash_preimage_and_candidate_fields(self):
        engine = (generator.EVIDENCE / "delta-core-cpp__src__apply__engine.cpp").read_text()
        for part in [
            "std::to_string(value)",
            "transcript.push_back(';')",
            "std::byte{0}",
            'values_hash("deltareduce.008.model.v1", next_model)',
            'values_hash("deltareduce.008.optimizer.v1", next_momentum)',
            ".parent_optimizer_hash = parent.optimizer_id",
            ".parent_checkpoint_id = parent.checkpoint_id",
            "(void)certificates::content_id(result)",
        ]:
            self.assertIn(part, engine)
        ordering = [
            engine.index(part)
            for part in [
                "const auto gradient =",
                "const auto momentum =",
                "const auto direction =",
                "const auto decay =",
                "const auto step =",
            ]
        ]
        self.assertEqual(ordering, sorted(ordering))

    def test_original_candidate_is_not_rewritten(self):
        golden = load_json_strict(
            generator.EVIDENCE / "delta-protocol__fixtures__008__cross-language__golden-v1.json"
        )
        candidate = golden["apply_candidate"]["value"]
        for kind in ("model", "optimizer"):
            raw = f"deltareduce.008.{kind}.v1".encode() + b"\0"
            raw += b"".join(x.encode() + b";" for x in candidate[f"next_{kind}_values"])
            self.assertNotEqual(
                "sha256:" + hashlib.sha256(raw).hexdigest(), candidate[f"next_{kind}_hash"]
            )
            self.assertEqual(
                "sha256:" + hashlib.sha256(f"next-{kind}".encode()).hexdigest(),
                candidate[f"next_{kind}_hash"],
            )
        self.assertEqual(candidate["parent_checkpoint_id"], "sha256:" + "b" * 64)
        producer = (
            generator.EVIDENCE
            / "specs__008-certificates-and-consensus__scripts__certificate_contracts.py"
        ).read_text()
        self.assertIn('"next_model_hash": cid("next-model")', producer)
        self.assertIn('"next_optimizer_hash": cid("next-optimizer")', producer)

    def test_kernel_cases_keep_unclosed_boundaries_visible(self):
        lean, _ = generator.generate()
        for name in [
            "originalGraphResult",
            "originalLabelHashesNotRewritten",
            "numericGateDoesNotAuthenticateMetadata",
            "numericProfileDoesNotAuthenticateAccumulator",
            "opaqueAnchorCheckpointNotValueIdentity",
            "missingSourceLeavesStillNumeric",
            "oldNegativeZeroStillAccepted",
            "oldNegativeAliasStillAccepted",
            "negativeZeroNotComputed",
            "negativeAliasNotComputed",
            "scaledFractionNotEqual",
            "wrongParentOptimizer",
            "missingCoordinate",
            "reorderedLeaves",
        ]:
            self.assertIn("theorem " + name, lean)

    def test_all_new_declarations_imported_and_audited(self):
        top = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeApplyResult", "NativeApplyResultJoin", "NativeApplyResultVectors"]:
            self.assertIn("import DeltaReduce." + module, top)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            for name in re.findall(r"^(?:def|theorem) ([\w.]+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)

    def test_join_computes_source_and_arithmetic(self):
        source = (ROOT / "formal/proofs/DeltaReduce/NativeApplyResult.lean").read_text()
        join = (ROOT / "formal/proofs/DeltaReduce/NativeApplyResultJoin.lean").read_text()
        for part in [
            "let r ← deriveNativeApply binding",
            "checkValues sha (nativeValues binding r)",
            "r.core.conversion.certified.corpus.entries.map BoundParameter.body",
        ]:
            self.assertIn(part, source)
        for part in [
            "NativeApplySection.bindSection sha policy state",
            "NativeCurrentPointer.fromFinalized sha policy state command",
            "NativeApplyResult.check binding sha original.edge",
            "NativePointerWal.durableReplayRepair prepared src.2.2",
        ]:
            self.assertIn(part, join)
        self.assertNotIn("applyAuthenticated", source + join)


if __name__ == "__main__":
    unittest.main()
