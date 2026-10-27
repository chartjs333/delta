"""T047/T053 independently pinned initial arithmetic source, not import authority.

Selected profile-genesis-source-contract. No prevalidated Metadata/Prefix input,
new trust root, fabricated ApplyQC, default units or public-refinement premise.
The complete producing history and certified imported floor remain mandatory.
"""

import re
from dataclasses import dataclass

from formal.reference.isc_crypto.codec import _decimal, _id, _require
from formal.reference.profile_source import arithmetic_units as units
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import source_prefix
from formal.reference.storage_source import codec

FIELDS = frozenset(
    "formal_semantics_id height model_values optimizer_values origin_id "
    "schema_version type_name validator_epoch_id".split()
)
MAX_VALUES = 100000  # Existing NativeCurrentValues.Checks, not a new source cap.
I64_MIN, I64_MAX = -(2**63), 2**63 - 1


def values(original):
    _require(type(original) is list and 0 < len(original) <= MAX_VALUES, "native value count")
    result = []
    for raw in original:
        _require(
            type(raw) is str and len(raw) <= 20 and re.fullmatch(r"0|-?[1-9][0-9]*", raw),
            "exact original signed decimal spelling",
        )
        value = int(raw)
        _require(I64_MIN <= value <= I64_MAX, "native INT64 initial value")
        result.append(value)
    return tuple(result)


def value_preimage(kind, original):
    _require(kind in ("model", "optimizer"), "existing native value-hash domain")
    values(original)
    return (
        ("deltareduce.008." + kind + ".v1").encode("ascii")
        + b"\0"
        + b"".join(raw.encode("ascii") + b";" for raw in original)
    )


@dataclass(frozen=True)
class Image:
    original: bytes
    height: int
    model: tuple[int, ...]
    optimizer: tuple[int, ...]
    model_preimage: bytes
    optimizer_preimage: bytes
    checkpoint_id: str
    optimizer_id: str
    # Base before any original ApplyQC-producing prefix. This never supplies
    # the nonempty certified floor required for an imported snapshot.
    apply_qc_id: str = ""


def decode(raw, semantics, origin, epoch):
    _require(type(raw) is bytes and len(raw) <= m.MAX_SOURCE_BYTES, "existing source budget")
    row = m.closed(codec.load(raw), FIELDS)
    units.future_semantics(semantics)
    for ident in (origin, epoch):
        _id(ident)
    _require(
        row["formal_semantics_id"] == semantics
        and row["origin_id"] == origin
        and row["validator_epoch_id"] == epoch
        and row["schema_version"] == "1.0.0"
        and row["type_name"] == "PROFILE_GENESIS_VALUES",
        "independent genesis context/generation",
    )
    height = _decimal(row["height"])
    model, optimizer = values(row["model_values"]), values(row["optimizer_values"])
    _require(len(model) == len(optimizer), "whole original model/optimizer coordinate count")
    mp = value_preimage("model", row["model_values"])
    op = value_preimage("optimizer", row["optimizer_values"])
    return Image(raw, height, model, optimizer, mp, op, m.raw_id(mp), m.raw_id(op))


@dataclass(frozen=True)
class Origin:
    source: source_prefix.Prefix
    initial_configuration: bytes
    initial_units: bytes
    parameter_schema_id: str
    quantum: units.Rational
    genesis: Image


def bind(trust, manifest, index, artifacts):
    """Resolve the original genesis/U jointly from the independent raw profile.

    This establishes initial value meaning and metadata custody only; it is not
    a complete source-history/READY checker and cannot accept an Origin cache.
    """
    meta = m.check_metadata(trust, manifest, index, artifacts)
    source = source_prefix.materialize(meta)
    boot = m.validate(meta.bootstrap_bytes, "BOOTSTRAP")
    original_config = dict(meta.original_artifacts)[boot["initial_config_ref"]["content_id"]]
    u = units.initial_member(original_config)
    image = decode(
        source.genesis, boot["formal_semantics_id"], boot["origin_id"], boot["validator_epoch_id"]
    )
    return Origin(
        source,
        original_config,
        m.canonical(u),
        u["parameter_schema_id"],
        units.rational(u["quantum"], quantum=True, control=True),
        image,
    )
