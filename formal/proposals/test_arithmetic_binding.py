from __future__ import annotations

import unittest

import arithmetic_binding as a


class BindingProposalTests(unittest.TestCase):
    def test_rounding_negative_and_positive_ties(self):
        self.assertEqual(
            [a.rounding(n, 2) for n in (-7, -5, -3, -1, 1, 3, 5, 7)], [-3, -2, -1, 0, 1, 2, 3, 4]
        )

    def test_negative_non_ties(self):
        self.assertEqual(a.rounding(-4, 3), -1)
        self.assertEqual(a.rounding(-5, 3), -2)

    def test_weighted_sum_and_candidate(self):
        vector = a.vectors()
        self.assertEqual(vector["parameter_numerators"], [7, -7])
        self.assertEqual(vector["domain_vector"], [4, -3])
        self.assertEqual(vector["result"]["next_optimizer"], [5, -4])
        self.assertEqual(vector["result"]["next_model"], [16, -18])

    def test_rounding_cannot_move_across_mixture(self):
        first = a.rounding(a.rounding(1, 2) + a.rounding(-1, 2), 2)
        second = a.rounding(1 - 1, 4)
        self.assertEqual((first, second), (1, 0))

    def test_quantum_is_bound_not_assumed_one(self):
        self.assertEqual(
            a.domain_vector((7, -7), 2, q_quantum=(1, 2), apply_quantum=(1, 4)), (7, -7)
        )

    def test_overflow_before_cancellation_is_rejected(self):
        with self.assertRaisesRegex(a.BindingError, "OVERFLOW"):
            a.domain_vector(((1 << 63) - 1,), 2, q_quantum=(2, 1))

    def test_noncanonical_weight_rejected(self):
        with self.assertRaisesRegex(a.BindingError, "NONCANONICAL_WEIGHT"):
            a.parameter(
                (("ticket-a", (2, 4), (1,)),), native_ticket_ids=("ticket-a",), denominator=4
            )

    def test_missing_or_reordered_ticket_rejected(self):
        for contributions in (
            (("ticket-a", (1, 1), (1,)),),
            (("ticket-b", (1, 1), (1,)), ("ticket-a", (1, 1), (1,))),
        ):
            with self.assertRaisesRegex(a.BindingError, "COVERAGE_OR_ORDER"):
                a.parameter(
                    contributions, native_ticket_ids=("ticket-a", "ticket-b"), denominator=1
                )

    def test_unsafe_prefix_sum_rejected(self):
        maximum = (1 << 63) - 1
        with self.assertRaisesRegex(a.BindingError, "OVERFLOW"):
            a.parameter(
                (("a", (1, 1), (maximum,)), ("b", (1, 1), (1,)), ("c", (1, 1), (-1,))),
                native_ticket_ids=("a", "b", "c"),
                denominator=1,
            )

    def test_zero_denominator_and_float_rejected(self):
        for numerator, denominator in ((1, 0), (1.0, 2), (True, 2)):
            with self.assertRaises(a.BindingError):
                a.rounding(numerator, denominator)

    def test_model_optimizer_and_schema_substitutions_rejected(self):
        original = a.Parent("schema", (20,), (2,))
        for bad, reason in (
            (a.Parent("schema", (21,), (2,)), "MODEL"),
            (a.Parent("schema", (20,), (3,)), "OPTIMIZER"),
            (a.Parent("other", (20,), (2,)), "SCHEMA"),
        ):
            with self.assertRaisesRegex(a.BindingError, reason):
                a.verify_parent(
                    bad,
                    native_schema=original.schema,
                    native_model_hash=a.value_hash("model", original.model),
                    native_optimizer_hash=a.value_hash("optimizer", original.momentum),
                )

    def test_signed_minimum_is_explicit(self):
        minimum = -(1 << 63)
        self.assertEqual(a.domain_vector((minimum,), 1), (minimum,))
        with self.assertRaisesRegex(a.BindingError, "OVERFLOW"):
            a.domain_vector((minimum - 1,), 1)

    def test_value_bytes_and_hash_domains_are_distinct(self):
        self.assertEqual(a.value_bytes((1, -2, 0)), b"1;-2;0;")
        self.assertNotEqual(a.value_hash("model", (1,)), a.value_hash("optimizer", (1,)))


if __name__ == "__main__":
    unittest.main()
