"""Construct the immutable feature-004 protocol fixtures from exact integer rules."""

from __future__ import annotations

import argparse
import hashlib
import sys
from fractions import Fraction
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
WORKER_SRC: Final = ROOT / "delta-worker-python" / "src"
if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from deltatorrent.reference.fixedpoint_encoder import (  # noqa: E402
    FORMAL_SEMANTICS_ID,
    Rational,
    canonical_json_bytes,
    content_id,
    encode_envelope,
    encode_payload,
    leaf_id,
    merkle_root,
    quantize,
)

PARAMETER_SCHEMA_ID: Final = (
    "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239"
)
BASE_ROUND_CONFIG_ID: Final = "sha256:" + "1" * 64
PARENT_CHECKPOINT_ID: Final = "sha256:" + "b" * 64
TICKET_ID: Final = "ticket-002-fixture"
LEAN_SOURCE_ID: Final = "sha256:6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736"

THEOREMS: Final = [
    {
        "obligation_id": "PO-A1",
        "theorem_names": [
            "DeltaReduce.signedProductBound",
            "DeltaReduce.intermediateProductFits",
        ],
    },
    {
        "obligation_id": "PO-A2",
        "theorem_names": [
            "DeltaReduce.flatAccumulatorBound",
            "DeltaReduce.everyCanonicalPrefixFits",
        ],
    },
    {
        "obligation_id": "PO-A3",
        "theorem_names": [
            "DeltaReduce.commonDenominatorNumeratorSafe",
            "DeltaReduce.reducedRationalDenominatorPositive",
            "DeltaReduce.reducedRationalIsCoprime",
            "DeltaReduce.commonDenominatorPositive",
            "DeltaReduce.eachDenominatorDividesCommon",
            "DeltaReduce.canonicalRoundBelowHalf",
            "DeltaReduce.canonicalRoundAtOrAboveHalf",
            "DeltaReduce.canonicalRoundTieTowardPositive",
            "DeltaReduce.canonicalRoundDeterministic",
        ],
    },
]


def profile_value() -> dict[str, object]:
    return {
        "accumulator_widths": [64, 128],
        "byte_order": "LITTLE_ENDIAN",
        "element_encoding": "SIGNED_TWOS_COMPLEMENT_INT16",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "limits": {
            "max_header_bytes": 65_536,
            "max_payload_bytes": 1_048_576,
            "max_segments": 65_536,
            "max_shards": 4_096,
            "max_total_elements": 1_073_741_824,
        },
        "out_of_range_action": "REJECT",
        "profile_name": "int16-fixed-v1",
        "q_max": 32_767,
        "q_min": -32_767,
        "residual_mode": "FORBIDDEN",
        "rounding": "ROUND_TO_NEAREST_TIES_TO_EVEN",
        "scale_granularity": "CANONICAL_PARAMETER_SEGMENT",
        "scale_representation": "REDUCED_POSITIVE_RATIONAL_U32",
        "schema_version": "1.0.0",
        "source_representation": "REDUCED_RATIONAL_I64_U32",
        "trailing_bytes_action": "REJECT",
        "type_name": "FIXED_POINT_PROFILE",
    }


def _identified(domain: str, value: object) -> dict[str, object]:
    encoded = canonical_json_bytes(value)
    return {
        "bytes_hex": encoded.hex(),
        "content_id": content_id(domain, encoded),
        "value": value,
    }


def _proof(
    profile_id: str,
    scale_table_id: str,
    config_id: str,
    *,
    coefficient_abs_max: int,
    max_eligible: int,
    result: str = "PASS",
    selected_width: int | None = None,
) -> dict[str, object]:
    product = 32_767 * coefficient_abs_max
    final = product * max_eligible
    required_width = 64 if product <= (1 << 63) - 1 and final <= (1 << 63) - 1 else 128
    width = required_width if selected_width is None else selected_width
    return {
        "coefficient_abs_max": str(coefficient_abs_max),
        "common_denominator": "1",
        "config_id": config_id,
        "final_abs_bound": str(final),
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "lean_artifact_sha256": LEAN_SOURCE_ID,
        "max_eligible_contributions": str(max_eligible),
        "max_incremental_prefix_abs": str(final),
        "product_abs_bound": str(product),
        "product_width_bits": width,
        "profile_id": profile_id,
        "q_abs_max": "32767",
        "result": result,
        "scale_table_id": scale_table_id,
        "schema_version": "1.0.0",
        "selected_accumulator_width_bits": width,
        "theorems": THEOREMS,
        "type_name": "ACCUMULATOR_PROOF_INSTANCE",
    }


def contract_components() -> dict[str, object]:
    profile = _identified("deltareduce.004.profile.v1", profile_value())
    profile_id = str(profile["content_id"])
    scale_value = {
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "parameter_schema_id": PARAMETER_SCHEMA_ID,
        "profile_id": profile_id,
        "schema_version": "1.0.0",
        "segments": [
            {
                "element_count": 4,
                "element_start": 0,
                "quantum": {"denominator": 4, "numerator": "1"},
                "segment_id": "decoder.bias",
                "segment_ordinal": 0,
            },
            {
                "element_count": 32,
                "element_start": 4,
                "quantum": {"denominator": 16, "numerator": "1"},
                "segment_id": "embedding.weight",
                "segment_ordinal": 1,
            },
        ],
        "total_elements": 36,
        "type_name": "QUANTIZATION_SCALE_TABLE",
    }
    scale_table = _identified("deltareduce.004.scale-table.v1", scale_value)
    scale_table_id = str(scale_table["content_id"])
    entries: list[dict[str, object]] = [
        {
            "element_count": 4,
            "element_start": 0,
            "ordinal": 0,
            "payload_bytes": 8,
            "segment_id": "decoder.bias",
            "segment_offset": 0,
        }
    ]
    for chunk in range(4):
        entries.append(
            {
                "element_count": 8,
                "element_start": 4 + chunk * 8,
                "ordinal": 1 + chunk,
                "payload_bytes": 16,
                "segment_id": "embedding.weight",
                "segment_offset": chunk * 8,
            }
        )
    plan_value = {
        "entries": entries,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "parameter_schema_id": PARAMETER_SCHEMA_ID,
        "profile_id": profile_id,
        "scale_table_id": scale_table_id,
        "schema_version": "1.0.0",
        "target_payload_bytes": 16,
        "total_elements": 36,
        "type_name": "SHARD_PLAN",
    }
    plan = _identified("deltareduce.004.shard-plan.v1", plan_value)
    plan_id = str(plan["content_id"])
    config64_value = {
        "accumulator_width_bits": 64,
        "base_round_config_id": BASE_ROUND_CONFIG_ID,
        "coefficient_abs_max": "65538",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "max_eligible_contributions": str((1 << 32) - 1),
        "parameter_schema_id": PARAMETER_SCHEMA_ID,
        "profile_id": profile_id,
        "q_abs_max": "32767",
        "scale_table_id": scale_table_id,
        "schema_version": "1.0.0",
        "shard_plan_id": plan_id,
        "type_name": "FIXEDPOINT_ROUND_CONFIG",
    }
    config128_value = {
        **config64_value,
        "accumulator_width_bits": 128,
        "coefficient_abs_max": str((1 << 63) - 1),
    }
    config64 = _identified("deltareduce.004.fixedpoint-config.v1", config64_value)
    config128 = _identified("deltareduce.004.fixedpoint-config.v1", config128_value)
    proof64_value = _proof(
        profile_id,
        scale_table_id,
        str(config64["content_id"]),
        coefficient_abs_max=65_538,
        max_eligible=(1 << 32) - 1,
    )
    proof128_value = _proof(
        profile_id,
        scale_table_id,
        str(config128["content_id"]),
        coefficient_abs_max=(1 << 63) - 1,
        max_eligible=(1 << 32) - 1,
    )
    return {
        "profile": profile,
        "fixedpoint_config_int128": config128,
        "fixedpoint_config_int64": config64,
        "proof_int128": _identified("deltareduce.004.proof-instance.v1", proof128_value),
        "proof_int64_maximum_safe": _identified("deltareduce.004.proof-instance.v1", proof64_value),
        "scale_table": scale_table,
        "shard_plan": plan,
    }


def _source_values() -> list[dict[str, object]]:
    values = [Fraction(1, 4), Fraction(-1, 2), Fraction(0), Fraction(1)]
    values.extend(Fraction(index, 16) for index in range(-16, 16))
    records: list[dict[str, object]] = []
    for index, value in enumerate(values):
        records.append(
            {
                "denominator": value.denominator,
                "element_index": index,
                "numerator": str(value.numerator),
                "segment_id": "decoder.bias" if index < 4 else "embedding.weight",
            }
        )
    return records


def golden_fixture() -> dict[str, object]:
    components = contract_components()
    profile_id = str(components["profile"]["content_id"])  # type: ignore[index]
    scale_table_id = str(components["scale_table"]["content_id"])  # type: ignore[index]
    plan_id = str(components["shard_plan"]["content_id"])  # type: ignore[index]
    proof_id = str(components["proof_int64_maximum_safe"]["content_id"])  # type: ignore[index]
    config_id = str(components["fixedpoint_config_int64"]["content_id"])  # type: ignore[index]
    source = _source_values()
    quantized: list[int] = []
    for item in source:
        quantum = Rational(1, 4) if int(item["element_index"]) < 4 else Rational(1, 16)
        quantized.append(
            quantize(Rational(int(str(item["numerator"])), int(item["denominator"])), quantum)
        )
    plan_value = components["shard_plan"]["value"]  # type: ignore[index]
    shards: list[dict[str, object]] = []
    leaves: list[str] = []
    for entry in plan_value["entries"]:  # type: ignore[index]
        start = int(entry["element_start"])
        count = int(entry["element_count"])
        payload = encode_payload(quantized[start : start + count])
        payload_id = "sha256:" + hashlib.sha256(payload).hexdigest()
        header = {
            "element_count": count,
            "element_start": start,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "ordinal": int(entry["ordinal"]),
            "parameter_schema_id": PARAMETER_SCHEMA_ID,
            "payload_sha256": payload_id,
            "profile_id": profile_id,
            "proof_instance_id": proof_id,
            "round_config_id": config_id,
            "scale_table_id": scale_table_id,
            "schema_version": "1.0.0",
            "segment_id": str(entry["segment_id"]),
            "segment_offset": int(entry["segment_offset"]),
            "shard_plan_id": plan_id,
            "ticket_id": TICKET_ID,
            "type_name": "ENCODED_INT16_SHARD",
        }
        envelope = encode_envelope(header, payload)
        current_leaf = leaf_id(envelope)
        leaves.append(current_leaf)
        shards.append(
            {
                "element_count": count,
                "element_start": start,
                "envelope_bytes": len(envelope),
                "envelope_hex": envelope.hex(),
                "header": header,
                "header_bytes_hex": canonical_json_bytes(header).hex(),
                "leaf_id": current_leaf,
                "ordinal": int(entry["ordinal"]),
                "payload_bytes": len(payload),
                "payload_hex": payload.hex(),
                "segment_id": str(entry["segment_id"]),
                "segment_offset": int(entry["segment_offset"]),
            }
        )
    root = merkle_root(leaves)
    manifest = {
        "aggregation_steps": 2,
        "commitment_root": root,
        "domain_id": "domain-text-en",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "parameter_schema_id": PARAMETER_SCHEMA_ID,
        "parent_checkpoint_id": PARENT_CHECKPOINT_ID,
        "profile_id": profile_id,
        "proof_instance_id": proof_id,
        "round_config_id": config_id,
        "scale_table_id": scale_table_id,
        "schema_version": "1.0.0",
        "shard_plan_id": plan_id,
        "shards": [
            {
                key: shard[key]
                for key in (
                    "element_count",
                    "element_start",
                    "envelope_bytes",
                    "leaf_id",
                    "ordinal",
                    "payload_bytes",
                    "segment_id",
                    "segment_offset",
                )
            }
            for shard in shards
        ],
        "ticket_id": TICKET_ID,
        "total_elements": len(quantized),
        "total_envelope_bytes": sum(int(shard["envelope_bytes"]) for shard in shards),
        "total_payload_bytes": sum(int(shard["payload_bytes"]) for shard in shards),
        "type_name": "ENCODED_CONTRIBUTION_MANIFEST",
    }
    boundary_vectors = [
        {
            "expected_payload_hex": "0000",
            "expected_q": 0,
            "id": "positive-zero",
            "input_class": "+0",
            "normalized_source": {"denominator": 1, "numerator": "0"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "0000",
            "expected_q": 0,
            "id": "negative-zero",
            "input_class": "-0",
            "normalized_source": {"denominator": 1, "numerator": "0"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "0100",
            "expected_q": 1,
            "id": "smallest-positive-nonzero",
            "normalized_source": {"denominator": 1, "numerator": "1"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "ffff",
            "expected_q": -1,
            "id": "smallest-negative-nonzero",
            "normalized_source": {"denominator": 1, "numerator": "-1"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "0000",
            "expected_q": 0,
            "id": "positive-half-even-zero",
            "normalized_source": {"denominator": 2, "numerator": "1"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "0200",
            "expected_q": 2,
            "id": "positive-half-even-two",
            "normalized_source": {"denominator": 2, "numerator": "3"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "0000",
            "expected_q": 0,
            "id": "negative-half-even-zero",
            "normalized_source": {"denominator": 2, "numerator": "-1"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "feff",
            "expected_q": -2,
            "id": "negative-half-even-two",
            "normalized_source": {"denominator": 2, "numerator": "-3"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "ff7f",
            "expected_q": 32_767,
            "id": "positive-maximum",
            "normalized_source": {"denominator": 1, "numerator": "32767"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
        {
            "expected_payload_hex": "0180",
            "expected_q": -32_767,
            "id": "negative-maximum",
            "normalized_source": {"denominator": 1, "numerator": "-32767"},
            "quantum": {"denominator": 1, "numerator": "1"},
            "status": "ACCEPT",
        },
    ]
    return {
        "boundary_vectors": boundary_vectors,
        "expected": {"code": "OK", "proof_result": "PASS", "status": "ACCEPT"},
        "fixedpoint_config": components["fixedpoint_config_int64"],
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "manifest": _identified("deltareduce.004.manifest.v1", manifest),
        "normalized_source": source,
        "profile": components["profile"],
        "proof_instance": components["proof_int64_maximum_safe"],
        "q_values": quantized,
        "scale_table": components["scale_table"],
        "schema_version": "1.0.0",
        "shard_plan": components["shard_plan"],
        "shards": shards,
        "source_fixture_id": "FEATURE002-NORMALIZED-FP32-REFERENCE-V1",
        "type_name": "FIXEDPOINT_CROSS_LANGUAGE_GOLDEN",
    }


def valid_fixture() -> dict[str, object]:
    components = contract_components()
    return {
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "instances": components,
        "schema_version": "1.0.0",
        "type_name": "FIXEDPOINT_VALID_CONTRACTS",
    }


def invalid_fixture() -> dict[str, object]:
    components = contract_components()
    profile_id = str(components["profile"]["content_id"])  # type: ignore[index]
    scale_id = str(components["scale_table"]["content_id"])  # type: ignore[index]
    unsafe_config_value = dict(components["fixedpoint_config_int64"]["value"])  # type: ignore[index]
    unsafe_config_value["coefficient_abs_max"] = "65539"
    unsafe_config = _identified("deltareduce.004.fixedpoint-config.v1", unsafe_config_value)
    config_id = str(unsafe_config["content_id"])
    first_unsafe = _proof(
        profile_id,
        scale_id,
        config_id,
        coefficient_abs_max=65_539,
        max_eligible=(1 << 32) - 1,
        result="REJECT",
        selected_width=64,
    )
    return {
        "cases": [
            {
                "category": "source",
                "expected_code": "RATIONAL_ZERO_DENOMINATOR",
                "id": "zero-denominator",
                "source": {"denominator": 0, "numerator": "1"},
            },
            {
                "category": "source",
                "expected_code": "RATIONAL_NOT_REDUCED",
                "id": "non-reduced",
                "source": {"denominator": 2, "numerator": "2"},
            },
            {
                "category": "source",
                "expected_code": "RATIONAL_ZERO_NOT_CANONICAL",
                "id": "non-canonical-zero",
                "source": {"denominator": 2, "numerator": "0"},
            },
            {
                "category": "adapter",
                "expected_code": "SOURCE_NON_FINITE",
                "id": "positive-infinity",
                "source_class": "+INF",
            },
            {
                "category": "adapter",
                "expected_code": "SOURCE_NON_FINITE",
                "id": "nan",
                "source_class": "NAN",
            },
            {
                "category": "quantization",
                "expected_code": "QUANTIZATION_RANGE_EXCEEDED",
                "id": "first-positive-out-of-range",
                "quantum": {"denominator": 1, "numerator": "1"},
                "source": {"denominator": 1, "numerator": "32768"},
            },
            {
                "category": "quantization",
                "expected_code": "QUANTIZATION_RANGE_EXCEEDED",
                "id": "first-negative-out-of-range",
                "quantum": {"denominator": 1, "numerator": "1"},
                "source": {"denominator": 1, "numerator": "-32768"},
            },
            {
                "category": "quantization",
                "expected_code": "QUANTIZATION_INTERMEDIATE_OVERFLOW",
                "id": "huge-scaled-numerator",
                "quantum": {"denominator": 4294967295, "numerator": "1"},
                "source": {"denominator": 1, "numerator": "9223372036854775807"},
            },
            {
                "category": "payload",
                "expected_code": "Q_VALUE_OUT_OF_RANGE",
                "id": "raw-minus-32768",
                "q_values": [-32768],
            },
            {
                "category": "context",
                "expected_code": "TICKET_MISMATCH",
                "id": "wrong-ticket",
                "replacement": "ticket-wrong",
            },
            {
                "category": "context",
                "expected_code": "PARAMETER_SCHEMA_MISMATCH",
                "id": "wrong-schema",
                "replacement": "sha256:" + "e" * 64,
            },
            {
                "category": "context",
                "expected_code": "PROFILE_MISMATCH",
                "id": "wrong-profile",
                "replacement": "sha256:" + "d" * 64,
            },
            {
                "category": "envelope",
                "expected_code": "SHARD_TRUNCATED",
                "id": "truncated-prefix",
                "mutation": "REMOVE_LAST_BYTE",
            },
            {
                "category": "envelope",
                "expected_code": "SHARD_HEADER_TOO_LARGE",
                "id": "oversized-header",
                "declared_header_bytes": 65537,
            },
            {
                "category": "envelope",
                "expected_code": "TRAILING_BYTES",
                "id": "trailing-data",
                "mutation": "APPEND_00",
            },
            {
                "category": "plan",
                "expected_code": "DUPLICATE_ORDINAL",
                "id": "duplicate-ordinal",
                "ordinals": [0, 0],
            },
            {
                "category": "plan",
                "expected_code": "SHARD_RANGE_OVERLAP",
                "id": "overlap",
                "ranges": [[0, 4], [3, 4]],
            },
            {
                "category": "plan",
                "expected_code": "SHARD_RANGE_GAP",
                "id": "gap",
                "ranges": [[0, 4], [5, 4]],
            },
            {
                "category": "plan",
                "expected_code": "SHARD_COUNT_LIMIT",
                "id": "too-many-shards",
                "declared_shards": 4097,
            },
            {
                "category": "profile",
                "expected_code": "PROFILE_NOT_ALLOWED",
                "id": "float-profile",
                "profile_name": "fp16",
            },
            {
                "category": "profile",
                "expected_code": "DYNAMIC_SCALE_FORBIDDEN",
                "id": "worker-dynamic-scale",
                "scale_granularity": "WORKER",
            },
            {
                "category": "profile",
                "expected_code": "RESIDUAL_FORBIDDEN",
                "id": "residual-field",
                "residual": {"mode": "ERROR_FEEDBACK"},
            },
            {
                "category": "proof",
                "expected_code": "ACCUMULATOR_BOUND_UNSAFE",
                "fixedpoint_config": unsafe_config,
                "id": "int64-first-unsafe",
                "proof": first_unsafe,
            },
        ],
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "schema_version": "1.0.0",
        "type_name": "FIXEDPOINT_NEGATIVE_CONTRACTS",
    }


FIXTURES = {
    "cross-language/golden-v1.json": golden_fixture,
    "invalid/fixedpoint-negative-v1.json": invalid_fixture,
    "valid/fixedpoint-contract-v1.json": valid_fixture,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument("--print", choices=sorted(FIXTURES))
    output.add_argument("--write-all", action="store_true")
    args = parser.parse_args()
    if args.write_all:
        root = ROOT / "delta-protocol" / "fixtures" / "004"
        for relative, factory in sorted(FIXTURES.items()):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(canonical_json_bytes(factory()) + b"\n")
        return 0
    assert args.print is not None
    print(canonical_json_bytes(FIXTURES[args.print]()).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
