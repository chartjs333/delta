"""Complete structural collection preservation, not policy/provenance authority."""

import ast
import copy
import unittest
from pathlib import Path

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.isc_source.policy import HEADER, SCHEMAS, decode, encode, vector_shape


def example(shape):
    if shape in {"u32", "u64"}:
        return 1
    if shape == "i64":
        return -1
    if shape == "bool":
        return False
    if shape == "text":
        return "synthetic-opaque"
    if (vector := vector_shape(shape)) is not None:
        return [example(vector[0])]
    return {key: example(kind) for key, kind in SCHEMAS[shape]}


def structural_policy():
    result = example("policy")
    result["configured_abort_reason"] = "HARD_DEADLINE"
    return result


class PolicyTests(unittest.TestCase):
    def test_only_two_approved_parent_insertions(self):
        path = Path(__file__).resolve().parents[3] / "formal/scripts/native_policy_codec.py"
        original = {}
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
                continue
            if getattr(node.value.func, "id", None) == "record":
                name, fields = map(ast.literal_eval, node.value.args)
                original[name] = tuple(
                    tuple(s.split(":")) if ":" in s else (s, "text") for s in fields.split()
                )
        self.assertEqual(set(original), set(SCHEMAS))
        self.assertEqual(len(SCHEMAS["snapshot"]), 33)
        for name, fields in original.items():
            expected = fields
            if name in {"input_set_body", "input_set"}:
                expected = (*fields[:1], ("parent_checkpoint_id", "text"), *fields[1:])
            self.assertEqual(SCHEMAS[name], expected, name)

    def test_complete_nonempty_inventory_round_trip_without_erasure(self):
        policy = structural_policy()
        raw = encode(policy)
        self.assertEqual(raw[:16], HEADER)
        self.assertEqual(decode(raw), policy)
        self.assertEqual(len(decode(raw)["snapshot"]), 33)
        for name, kind in SCHEMAS["snapshot"]:
            if vector_shape(kind) is not None:
                self.assertEqual(len(decode(raw)["snapshot"][name]), 1)
        # This arbitrary structural fixture is deliberately NOT a legal source history.
        self.assertEqual(policy["snapshot"]["apply_profiles"][0]["momentum"]["numerator"], -1)

    def test_no_parent_invention_or_legacy_upgrade(self):
        original = structural_policy()
        for field in ("input_set_bodies", "input_set_certificates"):
            changed = copy.deepcopy(original)
            del changed["snapshot"][field][0]["parent_checkpoint_id"]
            with self.assertRaisesRegex(CodecError, "fields"):
                encode(changed)
        raw = encode(original)
        with self.assertRaisesRegex(CodecError, "header"):
            decode(b"DVPOL001" + raw[8:])
        for changed in (raw + b"x", raw[:-1]):
            with self.assertRaises(CodecError):
                decode(changed)

    def test_no_unknown_collection_or_reordered_candidates(self):
        original = structural_policy()
        changed = copy.deepcopy(original)
        changed["snapshot"]["extra"] = []
        with self.assertRaisesRegex(CodecError, "fields"):
            encode(changed)
        changed = copy.deepcopy(original)
        changed["candidates"] *= 2
        with self.assertRaises(CodecError):
            encode(changed)

    def test_parent_bytes_preserved_in_both_policy_positions(self):
        original = structural_policy()
        parent = "sha256:" + "7" * 64
        for field in ("input_set_bodies", "input_set_certificates"):
            original["snapshot"][field][0]["parent_checkpoint_id"] = parent
        raw = encode(original)
        self.assertEqual(raw.count(len(parent).to_bytes(4, "big") + parent.encode()), 2)
        self.assertEqual(decode(raw), original)


if __name__ == "__main__":
    unittest.main()
