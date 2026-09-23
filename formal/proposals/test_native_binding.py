from __future__ import annotations

import copy
import unittest
from dataclasses import replace

import binding_fixture
import native_binding as n


class NativeBindingTests(unittest.TestCase):
    def setUp(self):
        self.anchor, self.root, self.store = binding_fixture.fixture()

    def witness(self):
        return n.Witness(self.anchor, self.root, self.store)

    def change(self, kind, mutate):
        """Rehash the entire fixture, including all parent refs, after a mutation.

        Tests deliberately supply a new trusted authority root. An arithmetic or
        parent-state inconsistency must still be rejected below that root.
        """
        old = self.store
        new, cache = dict(old), {}

        def rewrite(ref):
            if ref["id"] in cache:
                return cache[ref["id"]]
            item = n.decode(old[ref["id"]])
            payload = item["payload"]
            if item["kind"] == kind:
                mutate(payload)

            def walk(value):
                if type(value) is dict:
                    if set(value) == {"id", "kind", "length"}:
                        return rewrite(value)
                    return {key: walk(child) for key, child in value.items()}
                if type(value) is list:
                    return [walk(child) for child in value]
                return value

            result = n.put(new, item["kind"], walk(payload))
            cache[ref["id"]] = result
            return result

        self.root = rewrite(self.root)
        self.store = new
        self.anchor = replace(self.anchor, authority_id=self.root["id"])

    def parameter_bodies(self, witness):
        return [witness.expected_parameter(*key) for key in witness.assignments]

    def evaluate(self):
        witness = self.witness()
        return witness.expected_apply(self.parameter_bodies(witness))

    def test_joined_arithmetic(self):
        self.assertEqual(self.evaluate()["next_model"], [19, -21])
        self.assertEqual(self.evaluate()["next_optimizer"], [2, 0])

    def test_exact_parameter_and_apply_commands(self):
        witness = self.witness()
        expected = self.evaluate()
        self.assertEqual(
            witness.admit(n.canonical({"action": "ACT-APPLY-VOTE", "payload": expected})),
            n.canonical(expected),
        )
        self.anchor = replace(self.anchor, role="PARAMETER")
        witness = self.witness()
        body = witness.expected_parameter("d0", "s0")
        self.assertEqual(
            witness.admit(n.canonical({"action": "ACT-PARAM-VOTE", "payload": body})),
            n.canonical(body),
        )

    def test_rehashed_wrong_result(self):
        witness = self.witness()
        body = self.evaluate()
        body["next_model"][0] += 1
        body["next_model_hash"] = n.arithmetic.value_hash("model", tuple(body["next_model"]))
        with self.assertRaisesRegex(n.BindingError, "ARITHMETIC_RESULT_MISMATCH"):
            witness.admit(n.canonical({"action": "ACT-APPLY-VOTE", "payload": body}))

    def test_forged_authority_root(self):
        trusted = self.anchor
        self.change("Q_SHARD", lambda item: item["values"].__setitem__(0, 9))
        self.anchor = trusted
        with self.assertRaisesRegex(n.BindingError, "NATIVE_AUTHORITY_ROOT"):
            self.evaluate()

    def test_missing_or_corrupt_each_artifact(self):
        for key in list(self.store):
            original = self.store[key]
            for replacement in (None, original + b" "):
                with self.subTest(key=key, replacement=replacement is None):
                    if replacement is None:
                        del self.store[key]
                    else:
                        self.store[key] = replacement
                    with self.assertRaises(n.BindingError):
                        self.evaluate()
                    self.store[key] = original

    def test_rehashed_parent_model_and_optimizer(self):
        for kind in ("MODEL", "OPTIMIZER"):
            with self.subTest(kind=kind):
                self.setUp()
                self.change(kind, lambda item: item["values"].__setitem__(0, 99))
                with self.assertRaisesRegex(n.BindingError, "PARENT_" + kind):
                    self.evaluate()

    def test_profile_mutations(self):
        mutations = [
            ("rounding", "HALF_TO_EVEN"),
            ("nesterov", False),
            ("output_range", "SATURATING"),
            ("accumulator_bits", 32),
            ("accumulator_bits", True),
            ("learning_rate", [2, 4]),
            ("apply_quantum", [0, 1]),
        ]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                self.setUp()
                self.change("PROFILE", lambda item, f=field, v=value: item.__setitem__(f, v))
                with self.assertRaises(n.BindingError):
                    self.evaluate()

    def test_native_context_role_recovery_deadline(self):
        for field, value in (
            ("view", 1),
            ("height", 2),
            ("epoch", "other"),
            ("round_id", "other"),
            ("hard_deadline", 11),
            ("logical_time", 10),
            ("logical_time", True),
            ("recovered", False),
            ("role", "WORKER"),
            ("parent_checkpoint", "other"),
        ):
            with self.subTest(field=field):
                self.setUp()
                self.anchor = replace(self.anchor, **{field: value})
                with self.assertRaises(n.BindingError):
                    self.evaluate()

    def test_wrong_action_role(self):
        self.anchor = replace(self.anchor, role="PARAMETER")
        witness = self.witness()
        with self.assertRaisesRegex(n.BindingError, "ROLE"):
            witness.admit(n.canonical({"action": "ACT-APPLY-VOTE", "payload": self.evaluate()}))

    def test_q_context_and_quantum(self):
        for field, value in (
            ("ticket", "other"),
            ("domain", "d1"),
            ("shard", "s1"),
            ("quantum", [1, 4]),
            ("quantum", [True, 2]),
            ("values", [True]),
        ):
            with self.subTest(field=field):
                self.setUp()
                self.change("Q_SHARD", lambda item, f=field, v=value: item.__setitem__(f, v))
                with self.assertRaises(n.BindingError):
                    self.evaluate()

    def test_missing_and_duplicate_shard_partition(self):
        for mutation in (
            lambda item: item["shards"].pop(),
            lambda item: item["shards"][1].__setitem__("offset", 0),
        ):
            self.setUp()
            self.change("SCHEMA", mutation)
            with self.assertRaisesRegex(n.BindingError, "EXACT_SCHEMA_COVERAGE"):
                self.evaluate()

    def test_missing_duplicate_reordered_parameter_coverage(self):
        witness = self.witness()
        bodies = self.parameter_bodies(witness)
        for bad in (bodies[:-1], [*bodies, bodies[0]], list(reversed(bodies))):
            with self.assertRaisesRegex(n.BindingError, "COVERAGE"):
                witness.expected_apply(bad)

    def test_rehashed_inconsistent_plan(self):
        mutations = [
            lambda item: item["assignments"].pop(),
            lambda item: item["assignments"][1].__setitem__("context", "d0:s0"),
            lambda item: item["assignments"][0]["contributions"].clear(),
            lambda item: item["tickets"][0].__setitem__("domain", "d1"),
            lambda item: item["assignments"][0].__setitem__("quantum", [1, 3]),
        ]
        for mutation in mutations:
            self.setUp()
            self.change("PLAN", mutation)
            with self.assertRaises(n.BindingError):
                self.evaluate()

    def test_ec_cannot_add_non_isc_member(self):
        self.change("EC_PROJECTION", lambda item: item["eligible"].append("t9"))
        with self.assertRaisesRegex(n.BindingError, "EC_MEMBERS"):
            self.evaluate()

    def test_current_aggregate_is_mandatory(self):
        for changes in (
            {"aggregate_id": None},
            {"aggregate_length": 1},
            {"aggregate_id": self.root["id"]},
        ):
            self.setUp()
            self.anchor = replace(self.anchor, **changes)
            with self.assertRaises(n.BindingError):
                self.evaluate()

    def test_rehashed_bad_certified_parameter(self):
        ref = {
            "id": self.anchor.aggregate_id,
            "length": self.anchor.aggregate_length,
            "kind": "AGGREGATE_PROJECTION",
        }
        aggregate = n.resolve(self.store, ref, "AGGREGATE_PROJECTION")
        aggregate["parameters"][0]["numerators"][0] += 1
        ref = n.put(self.store, "AGGREGATE_PROJECTION", aggregate)
        self.anchor = replace(self.anchor, aggregate_id=ref["id"], aggregate_length=ref["length"])
        with self.assertRaisesRegex(n.BindingError, "CERTIFIED_PARAMETER_MISMATCH"):
            self.evaluate()

    def test_bool_is_not_context_integer(self):
        self.change("AUTHORITY", lambda item: item["context"].__setitem__("height", True))
        with self.assertRaisesRegex(n.BindingError, "NATIVE_CONTEXT"):
            self.evaluate()

    def test_canonical_bytes(self):
        for bad in (
            b'{"x":1,"x":1}',
            b'{ "x":1}',
            b'{"x":1.0}',
            b'{"x":NaN}',
            b'{"x":-0}',
            b'{"x":1}\n',
            b'{"x":"\\u0061"}',
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(n.BindingError):
                    n.decode(bad)

    def test_metadata_substitution(self):
        for field, value in (("length", self.root["length"] + 1), ("kind", "MODEL")):
            wrong = dict(self.root)
            wrong[field] = value
            with self.assertRaises(n.BindingError):
                n.Witness(self.anchor, wrong, self.store)

    def test_unknown_command_fields_and_bool_result(self):
        witness = self.witness()
        expected = self.evaluate()
        command = {"action": "ACT-APPLY-VOTE", "payload": expected, "native_sequence": 99}
        with self.assertRaisesRegex(n.BindingError, "OBJECT_SHAPE"):
            witness.admit(n.canonical(command))
        del command["native_sequence"]
        command["payload"]["next_optimizer"][1] = False
        with self.assertRaisesRegex(n.BindingError, "ARITHMETIC_RESULT_MISMATCH"):
            witness.admit(n.canonical(command))

    def test_recovery_reconstructs_same_expected_bytes(self):
        before = n.canonical(self.evaluate())
        self.store = copy.deepcopy(self.store)
        self.assertEqual(n.canonical(self.evaluate()), before)

    def test_no_writes_on_bad_candidate(self):
        witness = self.witness()
        before = copy.deepcopy(self.store)
        with self.assertRaises(n.BindingError):
            witness.admit(n.canonical({"action": "ACT-APPLY-VOTE", "payload": {}}))
        self.assertEqual(self.store, before)

    def test_malformed_parameter_keys_reject_without_host_exception(self):
        self.anchor = replace(self.anchor, role="PARAMETER")
        witness = self.witness()
        for key in (None, [], {}, True, 1, "", "unknown"):
            for field in ("domain", "shard"):
                with self.subTest(field=field, key=key):
                    body = witness.expected_parameter("d0", "s0")
                    body[field] = key
                    with self.assertRaises(n.BindingError):
                        witness.admit(n.canonical({"action": "ACT-PARAM-VOTE", "payload": body}))

    def test_rehashed_unhashable_assignment_key(self):
        for field in ("domain", "shard"):
            with self.subTest(field=field):
                self.setUp()
                self.change(
                    "PLAN", lambda item, key=field: item["assignments"][0].__setitem__(key, [])
                )
                with self.assertRaisesRegex(n.BindingError, "IDENTIFIER"):
                    self.witness()

    def test_oversized_json_integer_rejects_at_boundary(self):
        with self.assertRaises(n.BindingError):
            n.decode(b'{"n":' + b"1" * 5000 + b"}")


if __name__ == "__main__":
    unittest.main()
