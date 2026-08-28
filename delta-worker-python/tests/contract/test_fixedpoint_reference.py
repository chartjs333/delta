from __future__ import annotations

import pytest
from deltatorrent.reference.fixedpoint_encoder import (
    ContractError,
    Rational,
    encode_payload,
    quantize,
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (Rational(0, 1), 0),
        (Rational(1, 2), 0),
        (Rational(3, 2), 2),
        (Rational(-1, 2), 0),
        (Rational(-3, 2), -2),
        (Rational(32_767, 1), 32_767),
        (Rational(-32_767, 1), -32_767),
    ],
)
def test_signed_ties_to_even(source: Rational, expected: int) -> None:
    assert quantize(source, Rational(1, 1)) == expected


def test_int16_payload_is_little_endian_and_symmetric() -> None:
    assert encode_payload([0, 1, -1, 32_767, -32_767]).hex() == "00000100ffffff7f0180"
    with pytest.raises(ContractError, match="Q_VALUE_OUT_OF_RANGE"):
        encode_payload([-32_768])


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ({"denominator": 0, "numerator": "1"}, "RATIONAL_ZERO_DENOMINATOR"),
        ({"denominator": 2, "numerator": "2"}, "RATIONAL_NOT_REDUCED"),
        ({"denominator": 2, "numerator": "0"}, "RATIONAL_ZERO_NOT_CANONICAL"),
        ({"denominator": 1, "numerator": "-0"}, "DECIMAL_NOT_CANONICAL"),
    ],
)
def test_noncanonical_rational_rejected(value: dict[str, object], code: str) -> None:
    with pytest.raises(ContractError) as error:
        Rational.parse(value)
    assert error.value.code == code


def test_quantization_fails_closed() -> None:
    with pytest.raises(ContractError) as range_error:
        quantize(Rational(32_768, 1), Rational(1, 1))
    assert range_error.value.code == "QUANTIZATION_RANGE_EXCEEDED"

    with pytest.raises(ContractError) as overflow_error:
        quantize(Rational((1 << 63) - 1, 1), Rational(1, 0xFFFFFFFF))
    assert overflow_error.value.code == "QUANTIZATION_INTERMEDIATE_OVERFLOW"
