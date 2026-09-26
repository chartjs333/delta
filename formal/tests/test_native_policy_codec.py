# ruff: noqa: E402 -- repository scripts are loaded from the explicit local path
import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import check_native_policy_codec as check
import generate_native_policy_schema as generator
import native_policy_codec as codec
from formal_artifacts import load_json_strict


class PolicyCodecTests(unittest.TestCase):
    def test_native_all_primitive_projection(self):
        doc = check.verify_document(load_json_strict(check.FOLDER / "cpp-cross-check.json"))
        self.assertEqual(len(doc["observed"]), 51)
        row = next(x for x in doc["observed"] if x["name"] == "all-nested-fields")
        self.assertEqual(row["value"], check.dense_policy())
        self.assertEqual(len(row["value"]["snapshot"]), 33)

    def test_source_inventory(self):
        blobs = check.source.sources()
        self.assertEqual(
            check.source.snapshot_inventory(blobs), [k for k, _ in codec.SCHEMAS["snapshot"]]
        )
        source = blobs["delta-runtime-cpp/src/vote_codec.cpp"].decode()
        pairs = {
            "input_set": "input_set",
            "input_set_body": "input_set_body",
            "seed": "seed",
            "norm": "norm",
            "eligibility": "eligibility",
            "eligibility_body": "eligibility_body",
            "plan": "plan",
            "plan_body": "plan_body",
            "parameter": "parameter",
            "parameter_body": "parameter_body",
            "root": "root",
            "root_body": "root_body",
            "apply_profile": "apply_profile",
            "apply_candidate": "apply_candidate",
            "apply_qc": "apply_qc",
        }
        for grammar, native in pairs.items():
            text = source.split("read_" + native + "(", 1)[1].split("return result;", 1)[0]
            names = re.findall(r"result\.(\w+)\s*=", text)
            self.assertEqual(names, [k for k, _ in codec.SCHEMAS[grammar]], grammar)
        self.assertEqual(sum(map(len, codec.SCHEMAS.values())), 238)

    def test_roundtrip_every_subrecord_and_field_omissions(self):
        for kind, fields in codec.SCHEMAS.items():
            value = check.specimen(kind)
            raw = codec.encode_value(kind, value)
            reader = codec.Reader(raw)
            self.assertEqual(reader.value(kind), value)
            self.assertEqual(reader.at, len(raw))
            for key, _ in fields:
                broken = copy.deepcopy(value)
                del broken[key]
                with self.assertRaises(ValueError, msg=kind + "." + key):
                    codec.encode_value(kind, broken)
            with self.assertRaises(ValueError):
                codec.encode_value(kind, {**value, "invented": 0})

    def test_all_truncated_prefixes_minimal_original(self):
        raw = dict(check.cases())["codec-ISC"]
        for n in range(len(raw)):
            with self.assertRaises(ValueError, msg=str(n)):
                codec.decode(raw[:n])

    def test_bounds_and_sign(self):
        for n in [-(2**63), -1, 0, 2**63 - 1]:
            raw = codec.encode_value("i64", n)
            self.assertEqual(codec.Reader(raw).value("i64"), n)
        for n in [-(2**63) - 1, 2**63]:
            with self.assertRaises(ValueError):
                codec.encode_value("i64", n)
        self.assertEqual(
            codec.Reader(codec.encode_value("text", "x" * 4096)).value("text"), "x" * 4096
        )
        with self.assertRaises(ValueError):
            codec.encode_value("text", "x" * 4097)
        for kind, n in [("text[]", 100001), ("validators", 4097), ("candidates", 8193)]:
            with self.assertRaises(ValueError):
                codec.Reader(n.to_bytes(4, "big")).value(kind)
        with self.assertRaises(ValueError):
            codec.Reader(b"x" * (codec.MAX_BYTES + 1))

    def test_codec_does_not_claim_admission(self):
        rows = {
            x["name"]: x
            for x in load_json_strict(check.FOLDER / "cpp-cross-check.json")["observed"]
        }
        for name in [
            "empty-local-codec-allowed",
            "unordered-deadlines-codec-allowed",
            "empty-candidate-body-codec-allowed",
            "rational-zero-codec-allowed",
        ]:
            self.assertEqual(rows[name]["status"], "ACCEPT")
        p = check.dense_policy()
        p["snapshot"]["finalized_apply_ids"] = ["z", "a", "z"]
        self.assertEqual(
            codec.decode(codec.encode(p))["snapshot"]["finalized_apply_ids"], ["z", "a", "z"]
        )

    def test_rehashed_native_value_substitution(self):
        doc = load_json_strict(check.FOLDER / "cpp-cross-check.json")
        row = next(x for x in doc["observed"] if x["name"] == "all-nested-fields")
        row["value"]["snapshot"]["input_set_bodies"][0]["context"]["height"] ^= 1
        with self.assertRaises(ValueError):
            check.verify_document(doc)
        doc = load_json_strict(check.FOLDER / "cpp-cross-check.json")
        doc["gate_eligible"] = True
        with self.assertRaises(ValueError):
            check.verify_document(doc)

    def test_byte_exact_generated_modules(self):
        files = [
            ROOT / "formal/proofs/DeltaReduce" / (name + ".lean")
            for name in ["NativePolicySchema", "NativePolicyCodecVectors"]
        ]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        generator.generate()
        generator.generate_vectors()
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

    def test_mandatory_imports_and_all_named_audits(self):
        root = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in [
            "NativePolicyCodec",
            "NativePolicySchema",
            "NativePolicyBytes",
            "NativePolicyCodecVectors",
        ]:
            self.assertIn("import DeltaReduce." + module, root)
            text = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            code = re.sub(r"/\-.*?\-/|--[^\n]*", "", text, flags=re.S)
            self.assertNotRegex(code, r"\b(sorry|admit|native_decide)\b|^axiom\b")
            for name in re.findall(r"^(?:def|theorem|abbrev) ([\w.]+)", text, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)


if __name__ == "__main__":
    unittest.main()
