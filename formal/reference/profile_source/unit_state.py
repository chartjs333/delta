"""T047/T053: complete original P / typed policy core-view association.

The verifier generation is independently selected. These static joins do not
authenticate a source cut, finalize an APC or select a profile for arithmetic.
No whole inventory is filtered to the current configuration's numeric values.
"""

from copy import deepcopy
from dataclasses import dataclass

from formal.reference.isc_crypto.codec import _require, content_id
from formal.reference.isc_source import policy
from formal.reference.profile_source import arithmetic_units as units


@dataclass(frozen=True)
class Profile:
    original: bytes
    core: dict
    numeric: dict
    identifier: str


def core_view(profile):
    """Exact existing typed coefficient view; never a serializer of whole P."""
    result = deepcopy(profile)
    for name in ("apply_quantum", "formal_semantics_id", "schema_version", "type_name"):
        del result[name]
    for name in ("learning_rate", "momentum", "weight_decay"):
        result[name]["numerator"] = int(result[name]["numerator"])
    for row in result["domain_weights"]:
        row["pi"]["numerator"] = int(row["pi"]["numerator"])
    return result


def bind_profile(semantics, original, core):
    decoded = units.decode_profile(original, semantics)
    # Encoding checks original typed scalar distinctions, including bool vs int.
    # Python dict equality alone would equate True and 1.
    supplied = policy._Writer()
    supplied.value("apply_profile", core)
    expected_core = core_view(decoded)
    expected = policy._Writer()
    expected.value("apply_profile", expected_core)
    _require(
        b"".join(supplied.parts) == b"".join(expected.parts),
        "whole original profile/core field association",
    )
    return Profile(
        original,
        expected_core,
        {key: deepcopy(decoded[key]) for key in units.NUMERIC_FIELDS},
        content_id(units.DOMAIN, original),
    )


def bind_inventory(semantics, original_policy, originals):
    _require(type(originals) in (list, tuple), "original profile inventory")
    decoded = policy.decode(original_policy)
    cores = decoded["snapshot"]["apply_profiles"]
    _require(len(cores) == len(originals), "complete original profile inventory")
    out = tuple(
        bind_profile(semantics, raw, core) for raw, core in zip(originals, cores, strict=True)
    )
    identifiers = [row.identifier for row in out]
    _require(identifiers == sorted(set(identifiers)), "original profile ID order/uniqueness")
    return out
