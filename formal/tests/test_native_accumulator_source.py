"""Rehashed numeric/source attacks and explicit accumulator trust boundaries."""

import copy
import hashlib
import json
import struct
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_accumulator_source as generator  # noqa: E402
import generate_native_source_artifacts as sources  # noqa: E402
import native_accumulator_source as bound  # noqa: E402
import native_source_artifacts as source  # noqa: E402


class NativeAccumulatorSourceTests(unittest.TestCase):
    def setUp(self):
        self.store, self.golden, self.other = sources.fixture_store()
        self.proof = copy.deepcopy(self.golden["proof_instance"]["value"])
        self.config = copy.deepcopy(self.golden["fixedpoint_config"]["value"])
        self.proof_id = self.golden["proof_instance"]["content_id"]
        self.manifest_id = self.golden["manifest"]["content_id"]

    def put(self, value, kind):
        raw = source.canonical(value)
        identifier = source.content_id(raw, source.DOMAINS[kind])
        self.store[identifier] = raw
        return identifier

    def check(self, proof=None, config=None):
        p = copy.deepcopy(self.proof if proof is None else proof)
        if config is not None:
            p["config_id"] = self.put(config, "config")
        return bound.resolve_accumulator(self.store, self.put(p, "proof"))

    def case(self, coefficient=1, count=1, bits=64, product_bits=64, headroom=0, denominator=1):
        p, c = copy.deepcopy(self.proof), copy.deepcopy(self.config)
        for d in (p, c):
            d["coefficient_abs_max"] = str(coefficient)
            d["max_eligible_contributions"] = str(count)
        c["accumulator_width_bits"] = bits
        p.update(
            selected_accumulator_width_bits=bits,
            product_width_bits=product_bits,
            product_abs_bound=str(32767 * coefficient),
            max_incremental_prefix_abs=str(32767 * coefficient * count),
            final_abs_bound=str(32767 * coefficient * count + headroom),
            common_denominator=str(denominator),
        )
        return self.check(p, c)

    def rewritten_manifest(self, proof):
        # Consistent rehash through every leaf and manifest: content validation
        # alone will pass, so rejection must come from the new bound relation.
        proof_id = self.put(proof, "proof")
        m = copy.deepcopy(self.golden["manifest"]["value"])
        m["proof_instance_id"] = proof_id
        total = 0
        for leaf, original in zip(m["shards"], self.golden["shards"], strict=True):
            h = copy.deepcopy(original["header"])
            h["proof_instance_id"] = proof_id
            header, payload = source.canonical(h), bytes.fromhex(original["payload_hex"])
            raw = (
                struct.pack("<4sHHII", b"DRQ1", 1, 0, len(header), len(payload)) + header + payload
            )
            leaf["leaf_id"] = source.content_id(raw, source.DOMAINS["leaf"])
            self.store[leaf["leaf_id"]] = raw
            leaf["envelope_bytes"] = len(raw)
            total += len(raw)
        m["total_envelope_bytes"] = total
        m["commitment_root"] = source.merkle_root([s["leaf_id"] for s in m["shards"]])
        return self.put(m, "manifest")

    def apply(self, change=None):
        p = copy.deepcopy(self.other["apply_arithmetic_profile"]["value"])
        p["accumulator_proof_id"] = self.proof_id
        if change:
            change(p)
        raw = source.canonical(p)
        identifier = source.content_id(raw, bound.APPLY_DOMAIN)
        self.store[identifier] = raw
        return bound.resolve_apply_accumulator(self.store, identifier)

    def test_pins_and_exact_regeneration(self):
        boundary = json.loads((generator.EVIDENCE / "native-source-boundary.json").read_bytes())
        for row in boundary["files"]:
            raw = subprocess.check_output(
                ["git", "show", boundary["commit"] + ":" + row["path"]], cwd=ROOT
            )
            self.assertEqual(raw, (ROOT / row["retained_path"]).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        self.assertEqual(
            generator.generate(),
            json.loads(
                (ROOT / "formal/proposals/native-accumulator-source-vectors.json").read_bytes()
            ),
        )

    def test_original_bounds_and_complete_q_composition(self):
        q = bound.resolve_bound_q_source(self.store, self.manifest_id)
        p = q.accumulator
        self.assertEqual(
            (p.product, p.prefix, p.final), (2147483646, 9223372026117357570, 9223372026117357570)
        )
        self.assertEqual(
            (p.coefficient_max, p.contribution_max, p.denominator), (65538, (1 << 32) - 1, 1)
        )
        self.assertEqual((p.product_bits, p.accumulator_bits, p.inferred_headroom), (64, 64, 0))
        self.assertEqual([v for r in q.q.rows for v in r["values"]], self.golden["q_values"])
        self.assertEqual(len(q.q.sources), 12)
        for s in p.sources:
            self.assertEqual(bytes.fromhex(s["bytes_hex"]), self.store[s["id"]])

    def test_proof_hash_and_every_dependency_fail_closed(self):
        for identifier in (self.proof_id, self.proof["config_id"], source.PROFILE):
            for data in (None, self.store[identifier] + b" "):
                store = dict(self.store)
                if data is None:
                    del store[identifier]
                else:
                    store[identifier] = data
                with (
                    self.subTest(identifier=identifier, missing=data is None),
                    self.assertRaises(source.SourceError),
                ):
                    bound.resolve_accumulator(store, self.proof_id)

    def test_every_field_omission_and_extra_reject(self):
        for kind, value in (("proof", self.proof), ("config", self.config)):
            for key in [*value, "extra"]:
                v = copy.deepcopy(value)
                if key == "extra":
                    v[key] = "unexpected"
                else:
                    del v[key]
                with self.subTest(kind=kind, key=key), self.assertRaises(source.SourceError):
                    self.check(v) if kind == "proof" else self.check(config=v)

    def test_pass_string_cannot_approve_wrong_arithmetic(self):
        for key in ("product_abs_bound", "max_incremental_prefix_abs"):
            for delta in (-1, 1):
                p = copy.deepcopy(self.proof)
                p[key] = str(int(p[key]) + delta)
                with self.subTest(key=key, delta=delta), self.assertRaises(source.SourceError):
                    self.check(p)
        p = copy.deepcopy(self.proof)
        p["final_abs_bound"] = str(int(p["max_incremental_prefix_abs"]) - 1)
        with self.assertRaisesRegex(source.SourceError, "NEGATIVE_INFERRED_HEADROOM"):
            self.check(p)

    def test_metadata_ids_result_and_theorem_order(self):
        variants = []
        for key, value in (
            ("result", "REJECT"),
            ("lean_artifact_sha256", "sha256:" + "0" * 64),
            ("formal_semantics_id", "sha256:" + "0" * 64),
            ("schema_version", "2.0.0"),
            ("type_name", "OTHER"),
            ("profile_id", "sha256:" + "1" * 64),
            ("scale_table_id", "sha256:" + "2" * 64),
        ):
            p = copy.deepcopy(self.proof)
            p[key] = value
            variants.append(p)
        for change in (
            lambda ts: ts.reverse(),
            lambda ts: ts.append(ts[0]),
            lambda ts: ts.pop(),
            lambda ts: ts[0]["theorem_names"].reverse(),
            lambda ts: ts[0]["theorem_names"].append("DeltaReduce.fabricated"),
        ):
            p = copy.deepcopy(self.proof)
            change(p["theorems"])
            variants.append(p)
        for p in variants:
            with self.subTest(p=p), self.assertRaises(source.SourceError):
                self.check(p)

    def test_specific_denominator_retained_not_reduced_or_inferred(self):
        p = self.case(denominator=bound.U64)
        self.assertEqual(p.denominator, bound.U64)
        for bad in (0, -1, bound.U64 + 1):
            with self.subTest(bad=bad), self.assertRaises(source.SourceError):
                self.case(denominator=bad)
        # Merely changing this primitive creates a different proof identity. No
        # certified ticket-weight relation follows from its positivity.
        self.assertNotEqual(self.case(denominator=2).proof_id, self.case(denominator=3).proof_id)

    def test_canonical_decimal_and_boolean_aliases_reject(self):
        for key in (
            "coefficient_abs_max",
            "max_eligible_contributions",
            "q_abs_max",
            "common_denominator",
            "product_abs_bound",
            "max_incremental_prefix_abs",
            "final_abs_bound",
        ):
            for bad in (True, False, 1, "01", "-0", "+1", "1.0", "1e3", " 1", "1 ", "9" * 40):
                p = copy.deepcopy(self.proof)
                p[key] = bad
                with self.subTest(key=key, bad=bad), self.assertRaises(source.SourceError):
                    self.check(p)
        for key in ("product_width_bits", "selected_accumulator_width_bits"):
            for bad in (True, "64", 63, 256, 0):
                p = copy.deepcopy(self.proof)
                p[key] = bad
                with self.subTest(key=key, bad=bad), self.assertRaises(source.SourceError):
                    self.check(p)

    def test_coefficient_count_and_q_limits(self):
        for coefficient, count in (
            (0, 1),
            (-1, 1),
            (bound.I64 + 1, 1),
            (1, 0),
            (1, -1),
            (1, bound.U64 + 1),
        ):
            with (
                self.subTest(coefficient=coefficient, count=count),
                self.assertRaises(source.SourceError),
            ):
                self.case(coefficient, count, bits=128, product_bits=128)
        p = copy.deepcopy(self.proof)
        c = copy.deepcopy(self.config)
        p["q_abs_max"] = c["q_abs_max"] = "32768"
        with self.assertRaisesRegex(source.SourceError, "PROOF_Q_BOUND"):
            self.check(p, c)

    def test_exact_int64_headroom_boundary_and_request_observation(self):
        p = self.case(headroom=bound.I64 - 32767)
        self.assertEqual(p.final, bound.I64)
        bound.check_request_headroom(p, bound.I64 - 32767)
        for wrong in (0, p.inferred_headroom - 1, p.inferred_headroom + 1, -1, True):
            with self.subTest(wrong=wrong), self.assertRaises(source.SourceError):
                bound.check_request_headroom(p, wrong)
        with self.assertRaisesRegex(source.SourceError, "ACCUMULATOR_WIDTH_OVERFLOW"):
            self.case(headroom=bound.I64 - 32767 + 1)

    def test_nonzero_headroom_is_unique_admissible_value_not_zero_assumption(self):
        p = self.case(headroom=7)
        self.assertEqual((p.prefix, p.final, p.inferred_headroom), (32767, 32774, 7))
        for candidate in range(12):
            self.assertEqual(p.prefix + candidate == p.final, candidate == p.inferred_headroom)
        self.assertNotIn("headroom", json.loads(bytes.fromhex(p.sources[0]["bytes_hex"])))
        self.assertNotEqual(p.proof_id, self.case().proof_id)

    def test_int128_and_separate_product_width(self):
        p = self.case(bound.I64, (1 << 32) - 1, bits=128, product_bits=128)
        self.assertEqual(p.product, 32767 * bound.I64)
        self.assertEqual(p.prefix, p.product * ((1 << 32) - 1))
        with self.assertRaisesRegex(source.SourceError, "PRODUCT_WIDTH_OVERFLOW"):
            self.case(bound.I64, bits=128, product_bits=64)
        with self.assertRaisesRegex(source.SourceError, "ACCUMULATOR_WIDTH_OVERFLOW"):
            self.case(65539, (1 << 32) - 1, product_bits=128)
        self.assertEqual(self.case(bits=64, product_bits=128).accumulator_bits, 64)

    def test_int128_prefix_and_final_overflow(self):
        p = self.case(bits=128, headroom=bound.I128 - 32767)
        self.assertEqual(p.final, bound.I128)
        with self.assertRaises(source.SourceError):
            self.case(bits=128, headroom=bound.I128 - 32766)
        with self.assertRaises(source.SourceError):
            self.case(bound.I64, bound.U64, bits=128, product_bits=128)
        # Keep declared bounds small to ensure independently computed prefix is
        # rejected too, even if an attacker hides the oversized declaration.
        p, c = copy.deepcopy(self.proof), copy.deepcopy(self.config)
        for d in (p, c):
            d["coefficient_abs_max"], d["max_eligible_contributions"] = (
                str(bound.I64),
                str(bound.U64),
            )
        p["product_abs_bound"] = str(bound.I64 * 32767)
        with self.assertRaisesRegex(source.SourceError, "PREFIX_INT128_OVERFLOW"):
            self.check(p, c)

    def test_all_configuration_links_are_checked(self):
        for key, value in (
            ("coefficient_abs_max", "2"),
            ("max_eligible_contributions", "2"),
            ("q_abs_max", "2"),
            ("accumulator_width_bits", 128),
            ("profile_id", "sha256:" + "2" * 64),
            ("scale_table_id", "sha256:" + "3" * 64),
        ):
            c = copy.deepcopy(self.config)
            c[key] = value
            with self.subTest(key=key), self.assertRaises(source.SourceError):
                self.check(config=c)
        for key in ("base_round_config_id", "parameter_schema_id", "shard_plan_id"):
            c = copy.deepcopy(self.config)
            c[key] = "not-an-id"
            with self.subTest(key=key), self.assertRaises(source.SourceError):
                self.check(config=c)

    def test_rehashed_complete_q_source_cannot_approve_bad_proof(self):
        for key, value in (
            ("product_abs_bound", "0"),
            ("max_incremental_prefix_abs", "0"),
            ("final_abs_bound", "0"),
            ("result", "UNTRUSTED"),
        ):
            p = copy.deepcopy(self.proof)
            p[key] = value
            manifest = self.rewritten_manifest(p)
            source.resolve_q_source(self.store, manifest)
            with self.subTest(key=key), self.assertRaises(source.SourceError):
                bound.resolve_bound_q_source(self.store, manifest)

    def test_original008_proof_preimage_still_missing(self):
        row = self.other["apply_arithmetic_profile"]
        self.store[row["content_id"]] = bytes.fromhex(row["bytes_hex"])
        with self.assertRaisesRegex(source.SourceError, "MISSING_PREIMAGE"):
            bound.resolve_apply_accumulator(self.store, row["content_id"])
        self.store[row["value"]["accumulator_proof_id"]] = self.store[self.proof_id]
        with self.assertRaisesRegex(source.SourceError, "SOURCE_HASH"):
            bound.resolve_apply_accumulator(self.store, row["content_id"])

    def test_separately_synthetic_profile_edge_preserves_original_values(self):
        p, proof = self.apply()
        self.assertEqual(proof.proof_id, self.proof_id)
        self.assertEqual(
            p["domain_weights"], self.other["apply_arithmetic_profile"]["value"]["domain_weights"]
        )
        self.assertNotIn("apply_quantum", p)
        # Native profile does not impose unit sum here; no extra native rule.
        p, _ = self.apply(
            lambda p: p["domain_weights"][0].update(pi={"numerator": "2", "denominator": 1})
        )
        self.assertEqual(p["domain_weights"][0]["pi"]["numerator"], "2")

    def test_rehashed_apply_profile_fraction_mode_and_coverage_errors(self):
        mutations = [
            lambda p: p.update(nesterov=1),
            lambda p: p.update(rounding="ROUND_TO_NEAREST_TIES_TO_EVEN"),
            lambda p: p.update(formal_semantics_id="sha256:" + "0" * 64),
            lambda p: p.update(schema_version="2.0.0"),
            lambda p: p.update(type_name="OTHER"),
            lambda p: p.update(domain_weights=[]),
            lambda p: p["domain_weights"].reverse(),
            lambda p: p["domain_weights"].append(p["domain_weights"][0]),
            lambda p: p.update(extra="field"),
            lambda p: p.pop("momentum"),
        ]
        for key in ("learning_rate", "momentum", "weight_decay"):
            for f in (
                {"numerator": "-1", "denominator": 1},
                {"numerator": "2", "denominator": 2},
                {"numerator": "0", "denominator": 2},
                {"numerator": "1", "denominator": True},
                {"numerator": str(bound.I64 + 1), "denominator": 1},
                {"numerator": "1", "denominator": bound.U64 + 1},
            ):
                mutations.append(lambda p, key=key, f=f: p.update({key: f}))
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i), self.assertRaises(source.SourceError):
                self.apply(mutate)

    def test_original008_label_grammar_is_not004_segment_grammar(self):
        p, _ = self.apply(lambda p: p["domain_weights"][0].update(domain_id="a:b"))
        self.assertEqual(p["domain_weights"][0]["domain_id"], "a:b")
        self.apply(lambda p: p["domain_weights"][0].update(domain_id="a" * 128))
        for bad in ("a/b", "a" * 129, "", "a b", True):
            with self.subTest(bad=bad), self.assertRaises(source.SourceError):
                self.apply(lambda p, bad=bad: p["domain_weights"][0].update(domain_id=bad))


if __name__ == "__main__":
    unittest.main()
