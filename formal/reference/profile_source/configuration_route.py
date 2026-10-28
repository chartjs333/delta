"""Closed reference generation selection, supplied by the independent verifier.

Never select from imported schema/version strings or retry another decoder.
This only routes existing byte/authority conjuncts, not producer permission,
original parent provenance, full source legality, READY or Formal GO.
"""

from enum import Enum

from formal.reference.isc_crypto.codec import _require
from formal.reference.profile_source import configuration as legacy
from formal.reference.profile_source import configuration_units as units


class Generation(Enum):
    SCHEMA2 = "original-schema-2"
    UNITS = "selected-unit-bearing-schema-3"


LEGACY = Generation.SCHEMA2
UNITS = Generation.UNITS


def selected(generation):
    _require(type(generation) is Generation, "independently selected configuration generation")
    return units if generation is UNITS else legacy


def decode(original, *, generation=LEGACY):
    return selected(generation).decode(original)


def bind(validators, storage, original, declaration, *, generation=LEGACY):
    return selected(generation).bind(validators, storage, original, declaration)


def bind_native_header(config, state, policy, actor, *, generation=LEGACY):
    _require(type(config) is legacy.BoundConfig, "original bound configuration required")
    body = decode(config.original, generation=generation)
    return legacy._bind_native_header(config, state, policy, actor, body)
