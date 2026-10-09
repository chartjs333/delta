"""Scope-15 RoundConfig schema 3: retain the complete original DRC1 frame.

The entry point is selected by the independent verifier generation. It never
falls back to schema 2 or chooses a schema from an imported version string.
This codec is not config admission, original delivery/quorum or finalization.
"""

from formal.reference.isc_crypto.codec import _id, _require, _uint
from formal.reference.profile_source import arithmetic_units as units
from formal.reference.profile_source import configuration as config
from formal.reference.profile_source.metadata import closed

FIELD = "apply_arithmetic_profile_source"
FIELDS = config.FIELDS | {FIELD}


def validate(value):
    closed(value, FIELDS)
    _require(
        value["type_name"] == "ROUND_CONFIG" and value["schema_version"] == "3.0.0",
        "selected unit-bearing configuration generation",
    )
    config.validate_fields(value)
    units.future_semantics(value["formal_semantics_id"])
    config.ascii_text(value[FIELD])
    units.decode_numeric(value[FIELD].encode("ascii"))
    return value


def encode(value):
    validate(value)
    payload = config.encode_value(value)
    raw = config.HEADER + _uint(len(payload), 4) + payload
    _require(len(raw) <= config.MAX_FRAME, "actual complete DRC1 frame budget")
    return raw


def decode(raw):
    reader = config.Reader(raw)
    _require(reader.take(8) == config.HEADER, "RoundConfig DRC1 header/type")
    _require(reader.count() == len(raw) - 12, "RoundConfig exact payload size")
    value = reader.value()
    _require(reader.at == len(raw), "RoundConfig trailing bytes")
    validate(value)
    _require(encode(value) == raw, "complete original configuration canonical bytes")
    return value


def check_parent_units(original, parent_schema, model_quantum, optimizer_quantum):
    """Unit conjunct of config admission, valid even BEFORE an APC exists.

    The enclosing lawful source history must supply the exact original parent
    tuple/schema/units. This function neither creates nor authenticates it.
    """
    value = decode(original)
    _id(parent_schema)
    numeric = units.decode_numeric(value[FIELD].encode("ascii"))
    q = units.rational(numeric["apply_quantum"], quantum=True)
    for parent in (model_quantum, optimizer_quantum):
        _require(
            type(parent) is units.Rational
            and type(parent.numerator) is int
            and type(parent.denominator) is int,
            "exact integer parent units",
        )
    _require(
        value["parameter_schema_id"] == parent_schema and q == model_quantum == optimizer_quantum,
        "original parent schema and common-unit continuity",
    )
    return q
