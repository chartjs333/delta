"""Checked original004 accumulator fields, not formal/native exporter authority.

All products are recomputed from original bytes. The canonical proof omits the
request's headroom: final-minus-prefix reconstructs its only *admissible* value,
not an observation that a native caller actually supplied that value.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

from native_source_artifacts import (
    PROFILE,
    SEMANTICS,
    QSource,
    Resolver,
    canonical,
    cid,
    content_id,
    decimal,
    decode,
    items,
    require,
    resolve_q_source,
    shape,
    uint,
)

VERSION = "deltareduce.original-accumulator-source.v1-candidate"
LEAN_SOURCE = "sha256:6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736"
U64, I64, I128 = (1 << 64) - 1, (1 << 63) - 1, (1 << 127) - 1
APPLY_DOMAIN = "deltareduce.008.apply-arithmetic-profile.v1"
THEOREMS = (
    ("PO-A1", ("signedProductBound", "intermediateProductFits")),
    ("PO-A2", ("flatAccumulatorBound", "everyCanonicalPrefixFits")),
    (
        "PO-A3",
        (
            "commonDenominatorNumeratorSafe",
            "reducedRationalDenominatorPositive",
            "reducedRationalIsCoprime",
            "commonDenominatorPositive",
            "eachDenominatorDividesCommon",
            "canonicalRoundBelowHalf",
            "canonicalRoundAtOrAboveHalf",
            "canonicalRoundTieTowardPositive",
            "canonicalRoundDeterministic",
        ),
    ),
)
PROOF_FIELDS = (
    "coefficient_abs_max common_denominator config_id final_abs_bound formal_semantics_id "
    "lean_artifact_sha256 max_eligible_contributions max_incremental_prefix_abs "
    "product_abs_bound product_width_bits profile_id q_abs_max result scale_table_id "
    "schema_version selected_accumulator_width_bits theorems type_name"
)
CONFIG_FIELDS = (
    "accumulator_width_bits base_round_config_id coefficient_abs_max formal_semantics_id "
    "max_eligible_contributions parameter_schema_id profile_id q_abs_max scale_table_id "
    "schema_version shard_plan_id type_name"
)


def width(value: object) -> int:
    require(type(value) is int and value in (64, 128), "ACCUMULATOR_WIDTH")
    return value


def limit(bits: int) -> int:
    return (1 << (width(bits) - 1)) - 1


def theorem_metadata() -> list[dict]:
    return [
        {"obligation_id": key, "theorem_names": ["DeltaReduce." + name for name in names]}
        for key, names in THEOREMS
    ]


@dataclass(frozen=True)
class Accumulator:
    proof_id: str
    config_id: str
    scale_id: str
    coefficient_max: int
    contribution_max: int
    denominator: int
    product: int
    prefix: int
    final: int
    inferred_headroom: int
    product_bits: int
    accumulator_bits: int
    sources: tuple[dict, ...]


def resolve_accumulator(store: Mapping[str, bytes], proof_id: str) -> Accumulator:
    """Resolve original proof/config/profile and recompute their numeric contract.

    Schema/scale/plan/base-config references are retained here. Only the composed
    Q API below resolves their payloads; base-config authority remains external.
    Matching historical formal/Lean IDs and theorem names is NOT current GO.
    """
    r = Resolver(store)
    p = shape(r.document(proof_id, "proof"), PROOF_FIELDS)
    c = shape(r.document(p["config_id"], "config"), CONFIG_FIELDS)
    require(p["profile_id"] == c["profile_id"] == PROFILE, "PROOF_PROFILE")
    # The immutable profile ID checks the entire original canonical profile,
    # including ties-to-even quantization; no APPLY rounding is inferred.
    r.document(PROFILE, "profile")
    for key in ("base_round_config_id", "parameter_schema_id", "shard_plan_id", "scale_table_id"):
        cid(c[key])
    require(cid(p["scale_table_id"]) == c["scale_table_id"], "PROOF_SCALE")
    require(p["lean_artifact_sha256"] == LEAN_SOURCE, "HISTORICAL_LEAN_ID")
    require(p["result"] == "PASS", "PROOF_RESULT_METADATA")
    require(canonical(p["theorems"]) == canonical(theorem_metadata()), "THEOREM_METADATA")
    for key in ("coefficient_abs_max", "max_eligible_contributions", "q_abs_max"):
        require(type(p[key]) is str and p[key] == c[key], "CONFIG_INPUT:" + key)
    require(p["q_abs_max"] == "32767", "PROOF_Q_BOUND")
    coefficient = decimal(p["coefficient_abs_max"], I64, 1)
    count = decimal(p["max_eligible_contributions"], U64, 1)
    denominator = decimal(p["common_denominator"], U64, 1)
    bits = width(p["selected_accumulator_width_bits"])
    require(bits == width(c["accumulator_width_bits"]), "CONFIG_WIDTH")
    product_bits = width(p["product_width_bits"])
    declared_product = decimal(p["product_abs_bound"], I128)
    declared_prefix = decimal(p["max_incremental_prefix_abs"], I128)
    final = decimal(p["final_abs_bound"], I128)
    product = 32767 * coefficient
    require(product <= I128, "PRODUCT_INT128_OVERFLOW")
    prefix = product * count
    require(prefix <= I128, "PREFIX_INT128_OVERFLOW")
    require(declared_product == product, "DECLARED_PRODUCT")
    require(declared_prefix == prefix, "DECLARED_PREFIX")
    require(final >= prefix, "NEGATIVE_INFERRED_HEADROOM")
    headroom = final - prefix
    # Mathematical Python ints are explicitly bounded at every native stage.
    require(prefix + headroom <= I128, "FINAL_INT128_OVERFLOW")
    require(product <= limit(product_bits), "PRODUCT_WIDTH_OVERFLOW")
    require(final <= limit(bits), "ACCUMULATOR_WIDTH_OVERFLOW")
    return Accumulator(
        proof_id,
        p["config_id"],
        p["scale_table_id"],
        coefficient,
        count,
        denominator,
        product,
        prefix,
        final,
        headroom,
        product_bits,
        bits,
        tuple(r.sources.values()),
    )


def check_request_headroom(proof: Accumulator, observed_headroom: int) -> None:
    """Check an additional primitive observation; does not authenticate it."""
    uint(observed_headroom, I128)
    require(observed_headroom == proof.inferred_headroom, "REQUEST_HEADROOM_MISMATCH")


@dataclass(frozen=True)
class BoundQSource:
    q: QSource
    accumulator: Accumulator


def resolve_bound_q_source(store: Mapping[str, bytes], manifest_id: str) -> BoundQSource:
    q = resolve_q_source(store, manifest_id)
    p = resolve_accumulator(store, q.manifest["proof_instance_id"])
    # Resolve again from original bytes, not a caller-built QSource/proof record.
    original = {s["id"]: s["bytes_hex"] for s in q.sources}
    require(all(original.get(s["id"]) == s["bytes_hex"] for s in p.sources), "SOURCE_CHANGED")
    return BoundQSource(q, p)


def rational(value: object) -> tuple[int, int]:
    f = shape(value, "numerator denominator")
    n, d = decimal(f["numerator"], I64), uint(f["denominator"], U64, 1)
    require(math.gcd(n, d) == 1, "APPLY_FRACTION_NOT_REDUCED")
    return n, d


def resolve_apply_accumulator(
    store: Mapping[str, bytes], profile_id: str
) -> tuple[dict, Accumulator]:
    """Check the original008 profile's actual edge to the original004 proof.

    This does not equate the worker and APPLY profiles. The original008 profile
    has no apply_quantum, weights/plan binding or source-width proof for optimizer
    intermediates. All of those relations remain separate obligations.
    """
    cid(profile_id)
    require(profile_id in store, "MISSING_APPLY_PROFILE")
    raw = store[profile_id]
    p = decode(raw)
    require(content_id(raw, APPLY_DOMAIN) == profile_id, "APPLY_PROFILE_HASH")
    shape(
        p,
        "accumulator_proof_id domain_weights formal_semantics_id learning_rate momentum "
        "nesterov rounding schema_version type_name weight_decay",
    )
    require(
        p["formal_semantics_id"] == SEMANTICS
        and p["schema_version"] == "1.0.0"
        and p["type_name"] == "APPLY_ARITHMETIC_PROFILE",
        "APPLY_PROFILE_METADATA",
    )
    require(p["nesterov"] is True and p["rounding"] == "HALF_TOWARD_POSITIVE", "APPLY_MODE")
    for key in ("learning_rate", "momentum", "weight_decay"):
        rational(p[key])
    domains = []
    for w in items(p["domain_weights"], 100000):
        shape(w, "domain_id pi")
        name = w["domain_id"]
        require(
            type(name) is str and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", name) is not None,
            "APPLY_DOMAIN_LABEL",
        )
        domains.append(name)
        rational(w["pi"])
    require(domains == sorted(set(domains)), "APPLY_DOMAIN_ORDER")
    proof = resolve_accumulator(store, p["accumulator_proof_id"])
    return p, proof
