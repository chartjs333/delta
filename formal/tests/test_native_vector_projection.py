# ruff: noqa: E402
from __future__ import annotations

import copy
import sys
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "formal/scripts"), str(ROOT / "formal/proposals")]
import generate_native_vector_projection as gen
import native_vector_projection as projection
from generate_native_available_q import fixture, joined_fixture
from native_available_q import resolve_plan_available_q
from native_source_artifacts import SourceError, canonical

draft = projection.draft


class NativeVectorProjectionTests(unittest.TestCase):
    def setUp(self):
        self.args = gen.source_fixture()
        self.image = projection.project_inputs(*self.args)
        self.draft_args = gen.draft_example(self.image)

    def check(self, change=None):
        return projection.check_draft_inputs(*self.args, *gen.draft_example(self.image, change))

    def test_actual_source_bytes_and_full_vector_layout(self):
        store, golden, _ = fixture()
        retained = self.image.source.inputs[0].source.q.sources
        self.assertEqual(len(retained), 12)
        for row in retained:
            self.assertEqual(bytes.fromhex(row["bytes_hex"]), store[row["id"]])
        self.assertEqual([s["length"] for s in self.image.schema["shards"]], [4, 8, 8, 8, 8])
        values = [v for r in self.image.results for v in r["numerators"]]
        self.assertEqual(values, golden["q_values"])
        self.assertEqual([x["global_offset"] for x in self.image.locations], list(range(36)))
        self.assertEqual(self.image.schema["coordinates"][4], "embedding.weight:0000000000")

    def test_original_aliases_dimensions_and_omission_are_retained(self):
        source = self.image.source.inputs[0].source.q
        self.assertEqual(source.schema["tied_aliases"], {"lm_head.weight": "embedding.weight"})
        self.assertEqual(source.schema["parameters"][1]["shape"], [8, 4])
        self.assertEqual(source.schema["parameters"][2]["name"], "frozen.scale")
        self.assertNotIn("frozen.scale:0000000000", self.image.schema["coordinates"])
        self.assertFalse(any(s.startswith("lm_head") for s in self.image.schema["coordinates"]))

    def test_full_draft_oracle_parameter_path_and_distinct_ids(self):
        ds, anchor, authority = self.draft_args
        witness = draft.Witness(anchor, authority, ds)
        joined = self.check()
        self.assertEqual(
            joined["parameters"], [witness.expected_parameter(*k) for k in witness.assignments]
        )
        original = self.image.source.inputs[0].source.q
        self.assertNotEqual(original.manifest["parameter_schema_id"], self.image.schema_ref["id"])
        for assignment, row in zip(self.image.assignments, original.rows, strict=True):
            self.assertNotEqual(assignment["contributions"][0]["q"]["id"], row["leaf_id"])
        self.assertFalse(joined["native_export_authenticated"])

    def test_original_quantum_and_q_values_in_every_draft_artifact(self):
        original = self.image.source.inputs[0].source.q
        for assignment, row in zip(self.image.assignments, original.rows, strict=True):
            q = draft.resolve(self.image.artifacts, assignment["contributions"][0]["q"], "Q_SHARD")
            self.assertEqual(q["values"], row["values"])
            self.assertEqual(q["quantum"], row["quantum"])
            self.assertEqual(q["quantum"], assignment["quantum"])

    def test_all_original_preimages_remain_required(self):
        store, pid, edges, observations = self.args
        for row in self.image.source.inputs[0].source.q.sources:
            for replacement in (None, store[row["id"]] + b" "):
                altered = dict(store)
                if replacement is None:
                    del altered[row["id"]]
                else:
                    altered[row["id"]] = replacement
                with self.subTest(kind=row["kind"]), self.assertRaises(SourceError):
                    projection.project_inputs(altered, pid, edges, observations)

    def test_rehashed_correct_draft_with_wrong_weight_or_denominator_rejects(self):
        for field, value in (("weight", [2, 1]), ("denominator", 2)):

            def change(data, _store, field=field, value=value):
                a = data["assignments"][0]
                if field == "weight":
                    a["contributions"][0][field] = value
                else:
                    a[field] = value

            ds, anchor, authority = gen.draft_example(self.image, change)
            w = draft.Witness(anchor, authority, ds)
            w.expected_parameter(*next(iter(w.assignments)))  # internally valid, different math
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(SourceError, "ORIGINAL_DRAFT_INPUTS"),
            ):
                projection.check_draft_inputs(*self.args, ds, anchor, authority)

    def test_rehashed_wrong_q_values_and_quantum_do_not_translate(self):
        for field, value in (("values", [2, -2, 0, 4]), ("quantum", [1, 8])):

            def change(data, store, field=field, value=value):
                a = data["assignments"][0]
                c = a["contributions"][0]
                q = copy.deepcopy(draft.resolve(store, c["q"], "Q_SHARD"))
                q[field] = value
                c["q"] = draft.put(store, "Q_SHARD", q)
                if field == "quantum":
                    a["quantum"] = value

            ds, anchor, authority = gen.draft_example(self.image, change)
            w = draft.Witness(anchor, authority, ds)
            w.expected_parameter(*next(iter(w.assignments)))
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(SourceError, "ORIGINAL_DRAFT_INPUTS"),
            ):
                projection.check_draft_inputs(*self.args, ds, anchor, authority)

    def test_wholly_rehashed_valid_schema_renaming_rejects(self):
        def change(data, store):
            data["schema"]["coordinates"] = [f"x{i:010d}" for i in range(36)]
            sr = draft.put(store, "SCHEMA", data["schema"])
            for a in data["assignments"]:
                for c in a["contributions"]:
                    q = copy.deepcopy(draft.resolve(store, c["q"], "Q_SHARD"))
                    q["schema"] = sr
                    c["q"] = draft.put(store, "Q_SHARD", q)

        ds, anchor, authority = gen.draft_example(self.image, change)
        w = draft.Witness(anchor, authority, ds)
        for key in w.assignments:
            w.expected_parameter(*key)
        with self.assertRaisesRegex(SourceError, "ORIGINAL_DRAFT_SCHEMA"):
            projection.check_draft_inputs(*self.args, ds, anchor, authority)

    def test_original_context_and_parent_checkpoint_match(self):
        for field, value in (
            ("round", "other"),
            ("height", 2),
            ("view", 1),
            ("epoch", "other"),
            ("parent_checkpoint", "sha256:" + "a" * 64),
        ):

            def change(data, _store, field=field, value=value):
                data["context"][field] = value

            with self.subTest(field=field), self.assertRaisesRegex(SourceError, "ORIGINAL_"):
                self.check(change)

    def test_anchor_cannot_be_changed_independently_of_graph(self):
        ds, anchor, authority = self.draft_args
        for changed in (
            replace(anchor, authority_id="sha256:" + "f" * 64),
            replace(anchor, recovered=False),
            replace(anchor, logical_time=100),
        ):
            with self.assertRaises(draft.BindingError):
                projection.check_draft_inputs(*self.args, ds, changed, authority)

    def test_width_is_original_proof_width(self):
        with self.assertRaisesRegex(SourceError, "ORIGINAL_DRAFT_WIDTH"):
            self.check(lambda data, _: data["profile"].update(accumulator_bits=128))

    def test_missing_duplicate_or_reordered_assignment_rejects(self):
        changes = (
            lambda a: a.pop(),
            lambda a: a.append(copy.deepcopy(a[0])),
            lambda a: a.reverse(),
        )
        for fn in changes:
            with self.assertRaises((SourceError, draft.BindingError)):
                self.check(lambda data, _, fn=fn: fn(data["assignments"]))

    def test_missing_or_corrupt_draft_artifact_rejects(self):
        ds, anchor, authority = self.draft_args
        for ref in [
            self.image.schema_ref,
            *[a["contributions"][0]["q"] for a in self.image.assignments],
        ]:
            for value in (None, ds[ref["id"]] + b" "):
                altered = dict(ds)
                if value is None:
                    del altered[ref["id"]]
                else:
                    altered[ref["id"]] = value
                with self.assertRaises(draft.BindingError):
                    projection.check_draft_inputs(*self.args, altered, anchor, authority)

    def test_profile_current_and_vote_context_are_explicit_remaining_boundaries(self):
        # Exact source inputs do not establish the rest of the authority graph.
        for fn in (
            lambda d: d["profile"].update(learning_rate=[2, 1]),
            lambda d: d["model"].__setitem__(0, 99),
            lambda d: d["assignments"][0].update(context="other-valid-context"),
        ):
            out = self.check(lambda data, _, fn=fn: fn(data))
            self.assertFalse(out["native_export_authenticated"])
            self.assertEqual(out["scope"], "CONTENT_AND_VECTOR_INPUTS_NOT_AUTHENTICATED_ADMISSION")

    def test_multi_ticket_domain_nonminimal_denominator_and_zero(self):
        args = gen.source_fixture(True)
        image = projection.project_inputs(*args)
        joined = projection.check_draft_inputs(*args, *gen.draft_example(image))
        self.assertEqual(len(joined["parameters"]), 10)
        self.assertEqual(len(image.tickets), 3)
        self.assertTrue(all(a["denominator"] == 12 for a in image.assignments))
        original = image.source.inputs[0].source.q.rows
        for index, result in enumerate(image.results):
            expected = (
                [-2 * v for v in original[index % 5]["values"]]
                if index < 5
                else [0] * len(result["numerators"])
            )
            self.assertEqual(result["numerators"], expected)
        # Explicit zero-weight contribution stays present and consumes a prefix.
        self.assertEqual(image.assignments[5]["contributions"][0]["weight"], [0, 1])
        self.assertEqual(len(image.results[5]["prefixes"]), 1)

    def test_all_vector_coordinates_against_independent_fraction_sum(self):
        image = projection.project_inputs(*gen.source_fixture(True))
        for a, result in zip(image.assignments, image.results, strict=True):
            qs = [
                (
                    Fraction(*c["weight"]),
                    draft.resolve(image.artifacts, c["q"], "Q_SHARD")["values"],
                )
                for c in a["contributions"]
            ]
            expected = [
                sum((w * q[i] for w, q in qs), Fraction()) * a["denominator"]
                for i in range(len(result["numerators"]))
            ]
            self.assertTrue(all(x.denominator == 1 for x in expected))
            self.assertEqual(result["numerators"], [x.numerator for x in expected])

    def test_rehashed_source_parent_mismatch_is_not_hidden_by_draft(self):
        store, pid, edges, _observations, _, obs = joined_fixture()
        _, golden, _ = fixture()
        # Single changed parent remains valid source data; unchanged target rejects.
        oid = gen.rewrite_q(store, golden, obs, parent="sha256:" + "e" * 64)
        resolve_plan_available_q(store, pid, edges, [oid])
        with self.assertRaisesRegex(SourceError, "ORIGINAL_PARENT_CHECKPOINT"):
            projection.check_draft_inputs(store, pid, edges, [oid], *self.draft_args)

    def test_shared_parent_for_entire_source_corpus(self):
        store, pid, edges, observations = gen.source_fixture(True)
        prior = resolve_plan_available_q(store, pid, edges, observations)
        _, golden, obs = fixture()
        q = prior.inputs[1].source.q
        observations[1] = gen.rewrite_q(
            store,
            golden,
            obs,
            ticket=q.manifest["ticket_id"],
            domain=q.manifest["domain_id"],
            proof=q.manifest["proof_instance_id"],
            parent="sha256:" + "e" * 64,
            negate=True,
        )
        resolve_plan_available_q(store, pid, edges, observations)
        with self.assertRaisesRegex(SourceError, "SHARED_Q_SOURCE"):
            projection.project_inputs(store, pid, edges, observations)

    def test_changed_original_apc_weight_recomputes_instead_of_trusting_target(self):
        store, _pid, _edges, observations, docs, _obs = joined_fixture()
        docs["APC"]["weights"][0]["alpha"] = {"numerator": "2", "denominator": 1}
        pid, edges = gen.plans.put_graph(store, docs)
        image = projection.project_inputs(store, pid, edges, observations)
        self.assertEqual(image.results[0]["numerators"], [2, -4, 0, 8])
        with self.assertRaisesRegex(SourceError, "ORIGINAL_DRAFT_INPUTS"):
            projection.check_draft_inputs(store, pid, edges, observations, *self.draft_args)

    def test_naming_profile_explicitly_rejects_changed_lexicographic_order(self):
        schema = {
            "schema_version": "1.0.0",
            "frozen_omission_policy": "INCLUDE_ALL",
            "tied_aliases": {},
            "parameters": [
                {"name": name, "logical_dtype": "float32", "trainable": True, "shape": []}
                for name in ("a", "a.b")
            ],
        }
        rows = tuple(
            {
                "ordinal": i,
                "element_start": i,
                "element_count": 1,
                "segment_id": name,
                "segment_offset": 0,
            }
            for i, name in enumerate(("a", "a.b"))
        )
        # Both names are valid native parameters. This projection cannot silently
        # sort its derived names, because that would reorder original coordinates.
        with self.assertRaisesRegex(SourceError, "COORDINATE_PROJECTION_ORDER"):
            projection.schema_image(schema, rows)

    def test_coordinate_names_size_and_scalar_shape_boundaries(self):
        def layout(name, count, shape=None):
            schema = {
                "schema_version": "1.0.0",
                "frozen_omission_policy": "INCLUDE_ALL",
                "tied_aliases": {},
                "parameters": [
                    {
                        "name": name,
                        "logical_dtype": "float32",
                        "trainable": True,
                        "shape": [count] if shape is None else shape,
                    }
                ],
            }
            rows = (
                {
                    "ordinal": 0,
                    "element_start": 0,
                    "element_count": count,
                    "segment_id": name,
                    "segment_offset": 0,
                },
            )
            return projection.schema_image(schema, rows)

        self.assertEqual(len(layout("a" * 117, 1)[0]["coordinates"][0]), 128)
        with self.assertRaises(draft.BindingError):
            layout("a" * 118, 1)
        self.assertEqual(len(layout("p", 4096)[0]["coordinates"]), 4096)
        with self.assertRaisesRegex(SourceError, "VECTOR_PROJECTION_SIZE"):
            layout("p", 4097)
        self.assertEqual(layout("scalar", 1, [])[0]["coordinates"], ["scalar:0000000000"])

    def test_coordinate_range_partition_has_no_gap_overlap_or_segment_alias(self):
        source = self.image.source.inputs[0].source.q
        for field, value in (
            ("ordinal", 4),
            ("element_start", 1),
            ("element_count", 3),
            ("segment_id", "embedding.weight"),
            ("segment_offset", 1),
        ):
            rows = copy.deepcopy(source.rows)
            rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(SourceError):
                projection.schema_image(source.schema, rows)

    def test_resource_bounds_and_missing_observation(self):
        store, pid, edges, observations = self.args
        for value in ([], observations * 2):
            with self.assertRaises(SourceError):
                projection.project_inputs(store, pid, edges, value)
        with (
            patch.object(projection, "MAX_CELLS", 1),
            self.assertRaisesRegex(SourceError, "VECTOR_PROJECTION_CELLS"),
        ):
            projection.project_inputs(*self.args)
        with patch.object(projection, "MAX_TOTAL", 1), self.assertRaises(SourceError):
            self.check()

    def test_byte_exact_generation_and_explicit_synthetic_scope(self):
        evidence = gen.generate()
        self.assertEqual(canonical(evidence), gen.TARGET.read_bytes().rstrip(b"\n"))
        self.assertFalse(evidence["native_execution"])
        self.assertFalse(evidence["full_authority_binding"])
        self.assertEqual(
            evidence["examples"][0]["source_kind"], "ORIGINAL004_Q_SYNTHETIC_APC_AND_DRAFT"
        )


if __name__ == "__main__":
    unittest.main()
