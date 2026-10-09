"""T047/T053, scope 15: exact U/R/P source codecs for the selected generation.

These checks establish bytes and the acyclic numeric/proof join only. A caller
must still derive the original initial/config/APC authority and parent history.
In particular, an inventory profile or a claimed proof ID is not authority.
No production semantics ID, default quantum or legacy fallback is supplied.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import gcd

from formal.reference.isc_crypto.codec import (
    CodecError,
    _ascii,
    _decimal,
    _id,
    _label,
    _pairs,
    _require,
    content_id,
)
from formal.reference.profile_source import metadata

MAX_BYTES = 4 * 1024**2
MAX_WEIGHTS = 100000
I64_MAX, U64_MAX = 2**63 - 1, 2**64 - 1
DOMAIN = "deltareduce.008.apply-arithmetic-profile.v1"
LEGACY_SEMANTICS = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
NUMERIC_FIELDS = {
    "apply_quantum",
    "domain_weights",
    "learning_rate",
    "momentum",
    "nesterov",
    "rounding",
    "weight_decay",
}
PROFILE_FIELDS = NUMERIC_FIELDS | {
    "accumulator_proof_id",
    "formal_semantics_id",
    "schema_version",
    "type_name",
}


@dataclass(frozen=True)
class Rational:
    numerator: int
    denominator: int


def future_semantics(value):
    _id(value)
    _require(value != LEGACY_SEMANTICS, "new source bytes cannot use the legacy semantics ID")
    return value


def rational(value, *, quantum=False, control=False):
    metadata.closed(value, {"denominator", "numerator"})
    n = _decimal(value["numerator"], positive=quantum)
    d = value["denominator"]
    if control:
        d = _decimal(d, positive=True)
    _require(type(d) is int and 1 <= d <= U64_MAX, "native rational U64 denominator")
    _require(n <= I64_MAX, "native nonnegative I64 numerator")
    _require(not quantum or d <= I64_MAX, "positiveQuantum denominator")
    _require(gcd(n, d) == 1, "original reduced rational, no admission normalization")
    return Rational(n, d)


def validate_numeric(value):
    metadata.closed(value, NUMERIC_FIELDS)
    rational(value["apply_quantum"], quantum=True)
    rows = value["domain_weights"]
    _require(type(rows) is list and 1 <= len(rows) <= MAX_WEIGHTS, "native weight count")
    names = []
    for row in rows:
        metadata.closed(row, {"domain_id", "pi"})
        names.append(_label(row["domain_id"]))
        rational(row["pi"])
    _require(names == sorted(set(names)), "native complete ordered unique domain weights")
    for key in ("learning_rate", "momentum", "weight_decay"):
        rational(value[key])
    _require(value["nesterov"] is True, "native Nesterov requirement")
    _require(value["rounding"] == "HALF_TOWARD_POSITIVE", "native rounding requirement")
    return value


def _tree(value):
    if type(value) is str:
        _ascii(value)
    elif type(value) in (int, bool):
        pass
    elif type(value) is list:
        for item in value:
            _tree(item)
    elif type(value) is dict:
        for key, item in value.items():
            _ascii(key)
            _tree(item)
    else:
        raise CodecError("native source JSON scalar type")


def canonical(value):
    """Exact native spelling; validity of the closed source is checked separately."""
    try:
        _require(type(value) is dict, "native source object")
        _tree(value)
        raw = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
            "ascii"
        )
    except (UnicodeError, RecursionError, ValueError) as exc:
        raise CodecError("native source JSON encoding") from exc
    _require(len(raw) <= MAX_BYTES, "actual encoded native object budget")
    return raw


def _no_fraction(_):
    raise CodecError("exact native integer token required")


def load(raw):
    _require(type(raw) is bytes and len(raw) <= MAX_BYTES, "original bounded native source")
    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_pairs,
            parse_float=_no_fraction,
            parse_constant=_no_fraction,
        )
        _require(canonical(value) == raw, "exact native source re-encoding")
        return value
    except (UnicodeError, RecursionError, ValueError) as exc:
        raise CodecError("native source JSON decoding") from exc


def decode_initial(raw):
    value = metadata.closed(
        metadata.load(raw), {"parameter_schema_id", "quantum", "schema_version", "type_name"}
    )
    _id(value["parameter_schema_id"])
    _require(
        value["schema_version"] == "1.0.0" and value["type_name"] == "INITIAL_ARITHMETIC_UNITS",
        "initial arithmetic units generation",
    )
    rational(value["quantum"], quantum=True, control=True)
    return value


def decode_numeric(raw):
    return validate_numeric(load(raw))


def decode_profile(raw, semantics):
    future_semantics(semantics)
    value = metadata.closed(load(raw), PROFILE_FIELDS)
    _require(
        value["formal_semantics_id"] == semantics
        and value["schema_version"] == "2.0.0"
        and value["type_name"] == "APPLY_ARITHMETIC_PROFILE",
        "independently selected profile generation",
    )
    _id(value["accumulator_proof_id"])
    validate_numeric({key: value[key] for key in NUMERIC_FIELDS})
    return value


def derive_profile(numeric_source, accumulator_proof_id, semantics):
    """Unique P bytes once the ORIGINAL enclosing APC/proof join supplies its ID.

    This function does not verify that enclosing join, authorize a configuration
    or resolve an inventory. It deliberately needs no later candidate/result.
    """
    source = decode_numeric(numeric_source)
    _id(accumulator_proof_id)
    future_semantics(semantics)
    raw = canonical(
        {
            **source,
            "accumulator_proof_id": accumulator_proof_id,
            "formal_semantics_id": semantics,
            "schema_version": "2.0.0",
            "type_name": "APPLY_ARITHMETIC_PROFILE",
        }
    )
    decode_profile(raw, semantics)
    return raw


def bind_profile_bytes(numeric_source, accumulator_proof_id, semantics, original_profile):
    expected = derive_profile(numeric_source, accumulator_proof_id, semantics)
    _require(
        type(original_profile) is bytes and original_profile == expected,
        "exact R/original-proof/P byte join",
    )
    return content_id(DOMAIN, original_profile)


def initial_member(original_configuration):
    """Read U without discarding the complete original configuration.

    The whole initial configuration must be resolved using its independent
    bootstrap reference and joined to genesis. U alone never certifies genesis.
    """
    value = metadata.load(original_configuration)
    _require("arithmetic_units" in value, "mandatory initial arithmetic units")
    return decode_initial(metadata.canonical(value["arithmetic_units"]))
