"""Source-derived exact membership and rehashed APC coefficient/count attacks."""

import copy
import hashlib
import json
import math
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_plan_weights as gen  # noqa: E402
import native_plan_weights as weights  # noqa: E402
import native_source_artifacts as src  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402


class NativePlanWeightsTests(unittest.TestCase):
    def setUp(self):
        self.store, self.docs = gen.synthetic_case()

    def check(self):
        plan, edges = gen.put_graph(self.store, self.docs)
        return weights.resolve_plan_weights(self.store, plan, edges)

    def reproof(self, coefficient=6, count=3, denominator=12, bits=64):
        p = json.loads(self.store[self.docs["APC"]["accumulator_proof_id"]])
        c = json.loads(self.store[p["config_id"]])
        for d in (p, c):
            d.update(coefficient_abs_max=str(coefficient), max_eligible_contributions=str(count))
        c["accumulator_width_bits"] = bits
        p.update(
            config_id=self.put(c, "config"),
            common_denominator=str(denominator),
            product_abs_bound=str(32767 * coefficient),
            max_incremental_prefix_abs=str(32767 * coefficient * count),
            final_abs_bound=str(32767 * coefficient * count),
            product_width_bits=bits,
            selected_accumulator_width_bits=bits,
        )
        self.docs["APC"]["accumulator_proof_id"] = self.put(p, "proof")

    def put(self, doc, kind):
        raw = src.canonical(doc)
        identifier = src.content_id(raw, src.DOMAINS[kind])
        self.store[identifier] = raw
        return identifier

    def test_original_members_preserved_and_missing_proof_rejects(self):
        store, plan, edges, _ = gen.original_store()
        members = weights.resolve_members(store, plan, edges)
        self.assertEqual([r["ticket_id"] for r in members.rows], ["ticket-a"])
        self.assertEqual(members.rows[0]["numerator"], 1)
        for source in members.sources:
            self.assertEqual(bytes.fromhex(source["bytes_hex"]), store[source["id"]])
        with self.assertRaisesRegex(src.SourceError, "MISSING_PREIMAGE:sha256:f{64}"):
            weights.resolve_plan_weights(store, plan, edges)
        original_proof_id = members.plan["accumulator_proof_id"]
        store[original_proof_id] = self.store[self.docs["APC"]["accumulator_proof_id"]]
        with self.assertRaisesRegex(src.SourceError, "SOURCE_HASH"):
            weights.resolve_plan_weights(store, plan, edges)

    def test_nonminimal_specific_denominator_and_exact_per_domain_rows(self):
        result = self.check()
        self.assertEqual(result.accumulator.denominator, 12)
        self.assertEqual([r["coefficient"] for r in result.rows], [0, 4, 6])
        self.assertEqual(
            [r["tickets"] for r in result.domains], [["ticket-a", "ticket-b"], ["ticket-c"]]
        )
        self.assertEqual(
            [r["worst_absolute_prefixes"] for r in result.domains], [[0, 4 * 32767], [6 * 32767]]
        )
        self.assertEqual(len(result.sources), 8)
        for source in result.sources:
            self.assertEqual(bytes.fromhex(source["bytes_hex"]), self.store[source["id"]])

    def test_gamma_is_retained_not_multiplied_into_final_alpha(self):
        result = self.check()
        self.assertEqual([r["ec_gamma"]["denominator"] for r in result.rows], [7, 7, 7])
        self.assertEqual([r["coefficient"] for r in result.rows], [0, 4, 6])
        self.docs["EC"]["entries"][1]["gamma"] = {"numerator": "0", "denominator": 1}
        self.assertEqual([r["coefficient"] for r in self.check().rows], [0, 4, 6])

    def test_exact_rational_scaling_grid_against_fraction(self):
        # Mathematical cross-check over many canonical source fractions. The
        # source checker must reject indivisibility rather than round a weight.
        for common in range(1, 13):
            self.reproof(coefficient=1000, denominator=common)
            for denominator in range(1, 8):
                for numerator in range(0, 5):
                    if math.gcd(numerator, denominator) != 1:
                        continue
                    for row in self.docs["APC"]["weights"]:
                        row["alpha"] = {"numerator": str(numerator), "denominator": denominator}
                    if common % denominator:
                        with self.assertRaisesRegex(src.SourceError, "DENOMINATOR_NOT_DIVISOR"):
                            self.check()
                    else:
                        result = self.check()
                        expected = Fraction(numerator, denominator) * common
                        self.assertEqual([r["coefficient"] for r in result.rows], [expected] * 3)

    def test_global_count_includes_zero_coefficients_and_rejected_not_counted(self):
        self.reproof(count=2)
        with self.assertRaisesRegex(src.SourceError, "CONTRIBUTION_BOUND"):
            self.check()
        self.reproof(count=3)
        self.assertEqual(len(self.check().rows), 3)  # four EC entries, one rejected
        for r in self.docs["APC"]["weights"]:
            r["alpha"] = {"numerator": "0", "denominator": 1}
        self.reproof(count=2)
        with self.assertRaisesRegex(src.SourceError, "CONTRIBUTION_BOUND"):
            self.check()

    def test_scaled_coefficient_bound_inclusive_and_one_past(self):
        self.reproof(coefficient=6)
        self.check()
        self.reproof(coefficient=5)
        with self.assertRaisesRegex(src.SourceError, "COEFFICIENT_BOUND"):
            self.check()
        self.reproof(coefficient=(1 << 63) - 1, denominator=(1 << 64) - 1, bits=128)
        self.docs["APC"]["weights"][0]["alpha"] = {"numerator": "1", "denominator": 1}
        with self.assertRaisesRegex(src.SourceError, "COEFFICIENT_BOUND"):
            self.check()

    def test_fraction_canonicality_sign_and_integer_aliases(self):
        saved = copy.deepcopy(self.docs["APC"]["weights"])
        for n, d in [
            ("2", 4),
            ("0", 2),
            ("-1", 1),
            ("01", 1),
            ("-0", 1),
            ("1", 0),
            ("1", True),
            (True, 1),
            ("1", 1 << 64),
            (str(1 << 63), 1),
        ]:
            self.docs["APC"]["weights"] = copy.deepcopy(saved)
            self.docs["APC"]["weights"][0]["alpha"] = {"numerator": n, "denominator": d}
            with self.subTest(n=n, d=d), self.assertRaises(src.SourceError):
                self.check()

    def test_weight_and_bucket_complete_coverage(self):
        for name in ("weights", "bucket_assignments"):
            original = copy.deepcopy(self.docs["APC"][name])
            for change in (
                lambda rs: rs.pop(),
                lambda rs: rs.reverse(),
                lambda rs: rs.append(rs[-1]),
                lambda rs: rs[0].update(ticket_id="ticket-d"),
            ):
                self.docs["APC"][name] = copy.deepcopy(original)
                change(self.docs["APC"][name])
                with self.subTest(field=name), self.assertRaises(src.SourceError):
                    self.check()
            self.docs["APC"][name] = original

    def test_changed_eligible_set_rejects_even_equal_count(self):
        self.docs["EC"]["entries"][2]["accepted"] = False
        self.docs["EC"]["entries"][3]["accepted"] = True
        with self.assertRaisesRegex(src.SourceError, "WEIGHT_COVERAGE"):
            self.check()

    def test_isc_ec_domain_identity_and_duplicate_ticket(self):
        self.docs["EC"]["entries"][1]["domain_id"] = "other-domain"
        with self.assertRaisesRegex(src.SourceError, "EC_MEMBERS"):
            self.check()
        self.docs["EC"]["entries"][1]["domain_id"] = "domain-a"
        self.docs["ISC"]["tuples"][1]["ticket_id"] = "ticket-a"
        self.docs["ISC"]["tuples"][1]["commitment_id"] = "sha256:" + "f" * 64
        with self.assertRaises(src.SourceError):
            self.check()

    def test_all_members_norm_coverage_including_rejected(self):
        self.docs["NORM"]["entries"].pop()
        with self.assertRaisesRegex(src.SourceError, "NORM_MEMBERS"):
            self.check()

    def test_all_context_fields_bound(self):
        plan, edges = gen.put_graph(self.store, self.docs)
        for key in weights.Context.__annotations__:
            for name in ("ISC", "EC", "SEED", "NORM"):
                docs = copy.deepcopy(self.docs)
                doc = docs[name]
                doc[key] = doc[key] + 1 if type(doc[key]) is int else "sha256:" + "e" * 64
                p, e = gen.put_graph(self.store, docs)
                with (
                    self.subTest(key=key, name=name),
                    self.assertRaisesRegex(src.SourceError, "MIXED_CONTEXT"),
                ):
                    weights.resolve_plan_weights(self.store, p, e)
        weights.resolve_plan_weights(self.store, plan, edges)

    def test_independently_bound_ec_seed_missing_wrong_and_boolean(self):
        plan, edges = gen.put_graph(self.store, self.docs)
        for edge in ({}, {next(iter(edges)): "sha256:" + "f" * 64}, {next(iter(edges)): True}):
            with self.assertRaisesRegex(src.SourceError, "INDEPENDENT_EC_SEED_EDGE"):
                weights.resolve_plan_weights(self.store, plan, edge)

    def test_rehashed_cross_parent_rejects(self):
        plan, edges = gen.put_graph(self.store, self.docs)
        for name in ("EC", "SEED", "NORM"):
            docs = copy.deepcopy(self.docs)
            docs[name]["input_set_certificate_id"] = "sha256:" + "a" * 64
            d = docs[name]
            self.store[content_id(d)] = src.canonical(d)
            if name == "NORM":
                docs["EC"]["norm_evidence_id"] = content_id(d)
                self.store[content_id(docs["EC"])] = src.canonical(docs["EC"])
            docs["APC"]["eligibility_certificate_id"] = content_id(docs["EC"])
            docs["APC"]["seed_transcript_id"] = content_id(docs["SEED"])
            self.store[content_id(docs["APC"])] = src.canonical(docs["APC"])
            edge = {content_id(docs["EC"]): content_id(docs["SEED"])}
            with self.subTest(name=name), self.assertRaisesRegex(src.SourceError, "ISC_PARENT"):
                weights.resolve_plan_weights(self.store, content_id(docs["APC"]), edge)
        weights.resolve_plan_weights(self.store, plan, edges)

    def test_config_schema_and_base_config_identity(self):
        for field, error in (
            ("parameter_schema_id", "CONFIG_SCHEMA"),
            ("round_config_id", "CONFIG_ROUND"),
        ):
            original = self.docs["APC"][field]
            for d in self.docs.values():
                d[field] = "sha256:" + "e" * 64
            with self.assertRaisesRegex(src.SourceError, error):
                self.check()
            for d in self.docs.values():
                d[field] = original

    def test_every_resolved_preimage_missing_or_corrupt(self):
        result = self.check()
        plan, edges = gen.put_graph(self.store, self.docs)
        for row in result.sources:
            for bad in (None, self.store[row["id"]] + b" "):
                store = dict(self.store)
                if bad is None:
                    del store[row["id"]]
                else:
                    store[row["id"]] = bad
                with (
                    self.subTest(source=row["kind"], missing=bad is None),
                    self.assertRaises(src.SourceError),
                ):
                    weights.resolve_plan_weights(store, plan, edges)

    def test_every_apc_field_and_extra_rejects(self):
        self.check()
        original = copy.deepcopy(self.docs["APC"])
        for field in [*original, "extra"]:
            d = copy.deepcopy(original)
            if field == "extra":
                d[field] = True
            else:
                del d[field]
            # Content-ID construction needs type_name; hash original domain
            # directly so omitted type_name reaches the checked decoder.
            raw = src.canonical(d)
            pid = src.content_id(raw, "deltareduce.008.aggregation-plan-certificate.v1")
            self.store[pid] = raw
            with self.subTest(field=field), self.assertRaises(src.SourceError):
                weights.resolve_plan_weights(self.store, pid, {})

    def test_rehashed_invalid_proof_cannot_pass_via_certificate_bytes(self):
        p = json.loads(self.store[self.docs["APC"]["accumulator_proof_id"]])
        p["product_abs_bound"] = str(int(p["product_abs_bound"]) + 1)
        self.docs["APC"]["accumulator_proof_id"] = self.put(p, "proof")
        plan, edges = gen.put_graph(self.store, self.docs)
        weights.resolve_members(self.store, plan, edges)  # content alone passes
        with self.assertRaisesRegex(src.SourceError, "DECLARED_PRODUCT"):
            weights.resolve_plan_weights(self.store, plan, edges)

    def test_resources_and_canonical_predecode(self):
        plan, edges = gen.put_graph(self.store, self.docs)
        for raw in (b"{}" * (src.MAX_JSON // 2 + 1), b'{"a":1,"a":1}', b'{"a":null}', b'{"a":1.0}'):
            store = {**self.store, plan: raw}
            with self.assertRaises(src.SourceError):
                weights.resolve_plan_weights(store, plan, edges)
        with (
            patch.object(weights, "MAX_TOTAL", 10),
            self.assertRaisesRegex(src.SourceError, "SOURCE_TOTAL_LIMIT"),
        ):
            weights.resolve_plan_weights(self.store, plan, edges)

    def test_no_aggregate_parameter_or_apply_dependency(self):
        result = self.check()
        needed = {s["id"]: self.store[s["id"]] for s in result.sources}
        plan, edges = gen.put_graph(self.store, self.docs)
        self.assertEqual(weights.resolve_plan_weights(needed, plan, edges).rows, result.rows)

    def test_content_relation_does_not_authenticate_signer_names(self):
        # Deliberate boundary countercheck: names with no configured committee
        # still pass this content/numeric helper. Do not call it admission.
        for d in self.docs.values():
            if "signer_ids" in d:
                d["signer_ids"] = ["unconfigured-a", "unconfigured-b", "unconfigured-c"]
        self.assertEqual([r["coefficient"] for r in self.check().rows], [0, 4, 6])

    def test_source_boundary_and_exact_regeneration(self):
        boundary = json.loads((gen.EVIDENCE / "native-source-boundary.json").read_bytes())
        for row in boundary["files"]:
            raw = subprocess.check_output(
                ["git", "show", boundary["commit"] + ":" + row["path"]], cwd=ROOT
            )
            self.assertEqual(raw, (ROOT / row["retained_path"]).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        self.assertEqual(
            gen.generate(),
            json.loads((ROOT / "formal/proposals/native-plan-weight-vectors.json").read_bytes()),
        )


if __name__ == "__main__":
    unittest.main()
