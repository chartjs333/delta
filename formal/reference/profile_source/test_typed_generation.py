"""Approved ADR0015 generation, independent of the native legacy formatter."""

import json
import unittest

from formal.reference.profile_source.apply_vectors import generate


class TypedGenerationTests(unittest.TestCase):
    def test_whole_chain_has_exact_approved_typed_json_generation(self):
        _, originals = generate()
        expected = {
            "NORM_EVIDENCE",
            "SEED_TRANSCRIPT",
            "ELIGIBILITY_CERTIFICATE",
            "AGGREGATION_PLAN_CERTIFICATE",
            "PARAMETER_SHARD_QC",
            "AGGREGATE_ROOT_QC",
            "APPLY_ARITHMETIC_PROFILE",
            "APPLY_CANDIDATE",
            "APPLY_QC",
        }
        seen = set()

        def inspect(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if not key.startswith("negative_"):
                        inspect(item)
            elif isinstance(value, list):
                for item in value:
                    inspect(item)
            elif isinstance(value, str) and value.startswith("7b"):
                try:
                    obj = json.loads(bytes.fromhex(value))
                except (ValueError, UnicodeError):
                    return
                kind = obj.get("type_name") if isinstance(obj, dict) else None
                if kind in expected:
                    seen.add(kind)
                    self.assertEqual(obj["schema_version"], "2.0.0", kind)
                    self.assertEqual(obj["formal_semantics_id"], "sha256:" + "0" * 64, kind)

        inspect(originals)
        self.assertEqual(seen, expected)


if __name__ == "__main__":
    unittest.main()
