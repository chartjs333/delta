"""Original pointer-store source boundary and kernel fixture provenance."""

import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_current_pointer as generator  # noqa: E402
from formal_artifacts import load_json_strict  # noqa: E402


class NativeCurrentPointerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = generator.EVIDENCE
        cls.runtime = (cls.folder / "delta-runtime-cpp__src__certificate_runtime.cpp").read_text()
        cls.advance = cls.runtime.split("PointerDisposition CurrentPointerStore::advance(")[1]
        cls.recover = cls.runtime.split("void CurrentPointerStore::recover() {")[1].split(
            "PointerDisposition CurrentPointerStore::advance("
        )[0]

    def test_source_copies_are_exact_pinned_git_blobs(self):
        doc = load_json_strict(self.folder / "native-source-boundary.json")
        self.assertEqual(doc["commit"], "60c692f6e391f839829dfc64e93380db54cd507b")
        for row in doc["files"]:
            original = subprocess.check_output(
                ["git", "show", doc["commit"] + ":" + row["path"]], cwd=ROOT
            )
            self.assertEqual(hashlib.sha256(original).hexdigest(), row["sha256"])
            self.assertEqual(original, (self.folder / row["copy"]).read_bytes())

    def test_original_command_and_qc_identity(self):
        original = generator.inputs()
        c = original["current_pointer_command"]["value"]
        q = original["apply_qc"]["value"]
        self.assertEqual(c["apply_qc_id"], original["apply_qc"]["content_id"])
        for a, b in [
            ("next_checkpoint_id", "next_model_hash"),
            ("expected_parent_checkpoint_id", "parent_checkpoint_id"),
            ("next_optimizer_hash", "next_optimizer_hash"),
        ]:
            self.assertEqual(c[a], q[b])
        self.assertEqual(len(c), 14)
        self.assertEqual(len(q), 18)

    def test_actual_pointer_checks_and_replay_before_cas(self):
        for relation in [
            "command.apply_qc_id == apply_qc_id",
            "command.context == apply_qc.context",
            "command.expected_parent_checkpoint_id == apply_qc.parent_checkpoint_id",
            "command.next_checkpoint_id == apply_qc.next_model_hash",
            "command.next_optimizer_hash == apply_qc.next_optimizer_hash",
        ]:
            self.assertIn(relation, self.advance)
        ordered = [
            "content_id(command)",
            "content_id(apply_qc)",
            "if (state_.apply_qc_id == apply_qc_id)",
            "return PointerDisposition::replay",
            "command.expected_parent_checkpoint_id == state_.checkpoint_id",
            "command.context.height > state_.height",
        ]
        self.assertEqual(
            [self.advance.index(x) for x in ordered], sorted(self.advance.index(x) for x in ordered)
        )

    def test_actual_crash_order_and_distinct_text_wal(self):
        ordered = [
            "CrashPoint::before_wal_append",
            "CrashPoint::after_wal_append_before_durability",
            "CrashPoint::during_wal_append",
            '"truncated"',
            "const auto payload",
            "payload +",
            "CrashPoint::after_durability_before_commit",
            "state_ = PointerState",
            "CrashPoint::after_commit_before_effect_return",
            "CrashPoint::after_effect_copy_before_return",
            "return PointerDisposition::advanced",
        ]
        self.assertEqual(
            [self.advance.index(x) for x in ordered], sorted(self.advance.index(x) for x in ordered)
        )
        self.assertIn('"current-pointer.wal"', self.runtime)
        self.assertNotIn("DRW1", self.runtime)
        self.assertIn("_commit(_fileno(file))", self.runtime)
        self.assertIn("fsync(fileno(file))", self.runtime)

    def test_recovery_limits_not_silent_qc_authentication(self):
        for marker in [
            "resize_file(path, retained)",
            "fields.size() == 6U",
            "checksum(payload) == fields[5]",
            "parse_u64_decimal(fields[0])",
            "height > state_.height",
            "fields[1] == state_.checkpoint_id",
        ]:
            self.assertIn(marker, self.recover)
        self.assertNotIn("ApplyQc", self.recover)
        self.assertNotIn("ChainVerifier", self.advance)
        vectors = (ROOT / "formal/proofs/DeltaReduce/NativeCurrentPointerVectors.lean").read_text()
        for marker in [
            "unconfiguredSignerShape",
            "rehashedUncertifiedRecovery",
            "unknownNotEmpty",
            "tornRetained",
            "onlyTornNoAdvance",
            "doubleRecord",
            "crlfRejected",
        ]:
            self.assertIn("theorem " + marker, vectors)

    def test_generated_bytes_exact_and_finite_hashes_real(self):
        lean, doc = generator.generate()
        self.assertEqual(
            lean, (ROOT / "formal/proofs/DeltaReduce/NativeCurrentPointerVectors.lean").read_text()
        )
        self.assertEqual(
            doc, load_json_strict(ROOT / "formal/proposals/native-current-pointer-vectors.json")
        )
        for row in doc["hash_samples"]:
            self.assertEqual(
                hashlib.sha256(bytes.fromhex(row["preimage_hex"])).hexdigest(), row["sha256"]
            )
        line = bytes.fromhex(doc["line_hex"])
        self.assertTrue(line.endswith(b"\n"))
        payload, checksum = line[:-1].rsplit(b"|", 1)
        self.assertEqual(hashlib.sha256(payload).hexdigest().encode(), checksum)
        self.assertEqual(len(line[:-1].split(b"|")), 6)
        self.assertFalse(doc["native_execution"])

    def test_finalized_bridge_computes_original_section(self):
        src = (ROOT / "formal/proofs/DeltaReduce/NativeCurrentPointer.lean").read_text()
        for marker in [
            "NativeApplySection.bindSection sha policy state",
            "c.qc ∈ bound.finalized",
            "prepare sha c edge.decoded.certificate",
            "NativeApplySection.certificateChecked",
            "NativeApplyLineage.certifiedFields",
            "NativeApplyLineage.exactCurrent",
        ]:
            self.assertIn(marker, src)
        self.assertNotIn("applyAuthenticated", src)
        self.assertNotIn("nativeArithmeticRecoveryRefines", src)

    def test_named_declarations_audited(self):
        proofs = ROOT / "formal/proofs/DeltaReduce"
        audit = (proofs / "AxiomAudit.lean").read_text().splitlines()
        imports = (ROOT / "formal/proofs/DeltaReduce.lean").read_text().splitlines()
        for module in ["NativeCurrentPointer", "NativePointerWal", "NativeCurrentPointerVectors"]:
            self.assertIn("import DeltaReduce." + module, imports)
            for name in re.findall(
                r"^(?:def|theorem) (\w+)", (proofs / (module + ".lean")).read_text(), re.M
            ):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
