"""Independent exact-arithmetic oracle for the finite TLA fixture, not authority."""

from __future__ import annotations

import json
from fractions import Fraction
from itertools import accumulate

from arithmetic_binding import Parent, apply, domain_vector, parameter, rounding, value_hash


def main() -> int:
    a = parameter(
        (
            ("1", (1, 2), (1, 2)),
            ("2", (1, 3), (0, 5)),
            ("4", (0, 1), (0, 0)),
        ),
        native_ticket_ids=("1", "2", "4"),
        denominator=6,
    )
    b = parameter((("3", (1, 1), (-1, -3)),), native_ticket_ids=("3",), denominator=1)
    domains = (("1", domain_vector(a, 6)), ("2", domain_vector(b, 1, q_quantum=(1, 2))))
    parent = Parent("heterogeneous-finite-fixture", (20, -20), (2, -2))

    def result(weights: tuple) -> dict:
        return apply(
            parent,
            domains,
            weights,
            native_schema=parent.schema,
            native_model_hash=value_hash("model", parent.model),
            native_optimizer_hash=value_hash("optimizer", parent.momentum),
            learning_rate=(1, 2),
            momentum=(1, 2),
            weight_decay=(0, 1),
        )

    expected = result((("1", (2, 3)), ("2", (1, 3))))
    equal_weights = result((("1", (1, 2)), ("2", (1, 2))))
    assert a == (3, 16) and b == (-1, -3)
    assert expected["next_model"] == [19, -22]
    assert expected["next_optimizer"] == [2, 1]
    assert equal_weights["next_model"] == [19, -21]
    assert equal_weights["next_optimizer"] == [2, 0]
    late_exact = Fraction(2, 3) * Fraction(1, 2) + Fraction(1, 3) * Fraction(-1, 2)
    early = rounding(2 * rounding(1, 2) + rounding(-1, 2), 3)
    late = rounding(late_exact.numerator, late_exact.denominator)
    assert (early, late) == (1, 0)

    def fits(value: int) -> bool:
        return -128 <= value <= 127

    prefix_terms = [3 * 40, 2 * 4, 1 * -40]
    product_terms = [3 * -40, 2 * 80, 0]
    assert all(map(fits, prefix_terms)) and fits(sum(prefix_terms))
    assert not all(map(fits, accumulate(prefix_terms)))
    assert not all(map(fits, product_terms))
    assert all(map(fits, accumulate(product_terms)))
    conversion_product = 3 * 50
    conversion_result = rounding(conversion_product, 6)
    assert not fits(conversion_product) and fits(conversion_result)
    print(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "status": "PASS",
                "scope": "FINITE_TLA_FIXTURE_MATHEMATICAL_ORACLE_ONLY",
                "parameter_numerators": [list(a), list(b)],
                "domain_vectors": [list(values) for _, values in domains],
                "model": expected["next_model"],
                "optimizer": expected["next_optimizer"],
                "wrong_equal_mixture": {
                    "model": equal_weights["next_model"],
                    "optimizer": equal_weights["next_optimizer"],
                },
                "rounding_placement": {"before_mixture": early, "after_mixture": late},
                "signed_finite_interval": [-128, 127],
                "rejected_prefix": {
                    "terms": prefix_terms,
                    "prefixes": list(accumulate(prefix_terms)),
                },
                "rejected_product": {
                    "terms": product_terms,
                    "prefixes": list(accumulate(product_terms)),
                },
                "rejected_conversion": {
                    "product": conversion_product,
                    "otherwise_safe_result": conversion_result,
                },
                "formal_go": False,
                "native_byte_binding_proved": False,
                "cross_language_conformance_claimed": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
