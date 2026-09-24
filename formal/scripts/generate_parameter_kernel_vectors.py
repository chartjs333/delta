"""Pin oracle/Lean arithmetic vectors; no native-admission or parser proof claim."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/proposals"))
import arithmetic_binding as arithmetic  # noqa: E402
import native_binding as native  # noqa: E402

SOURCE = ROOT / "formal/fixtures/traces/native/normal-apply.json"
TARGET = ROOT / "formal/proofs/DeltaReduce/ParameterKernelVectors.lean"
EVIDENCE = ROOT / "formal/proposals/parameter-kernel-vectors.json"
MIN64, MAX64 = -(1 << 63), (1 << 63) - 1


def lean_list(values):
    return "[" + ", ".join(str(value) for value in values) + "]"


def generate(source=SOURCE, target=TARGET, evidence=EVIDENCE):
    bundle = native.decode(source.read_bytes())
    store = {key: raw.encode("ascii") for key, raw in bundle["artifacts"].items()}
    for key, raw in store.items():
        native.require(native.digest(raw) == key, "NATIVE_ARTIFACT_ID")
    snapshot = next(v for v in bundle["snapshots"].values() if v["action_id"] == "ACT-APPLY-VOTE")
    witness = native.Witness(
        native.NativeAnchor(**snapshot["anchor"]), snapshot["authority"], store
    )
    parameter_cases, conversion_cases = [], []

    def parameter(name, rows, denominator=2, bits=64, width=None, native_key=None):
        tickets = tuple(f"ticket-{i:04}" for i in range(len(rows)))
        terms = tuple(
            (ticket, (a, b), tuple(values))
            for ticket, (a, b, values) in zip(tickets, rows, strict=True)
        )
        try:
            result = list(
                arithmetic.parameter(
                    terms, native_ticket_ids=tickets, denominator=denominator, bits=bits
                )
            )
            reason = None
        except arithmetic.BindingError as error:
            result, reason = None, str(error)
        parameter_cases.append(
            {
                "name": name,
                "bits": bits,
                "denominator": denominator,
                "width": width if width is not None else (len(rows[0][2]) if rows else 2),
                "rows": rows,
                "result": result,
                "oracle_rejection": reason,
                "native_assignment": native_key,
            }
        )

    def conversion(name, numerators, denominator=2, q=(1, 1), apply=(1, 1), bits=64):
        try:
            result = list(
                arithmetic.domain_vector(
                    tuple(numerators), denominator, q_quantum=q, apply_quantum=apply, bits=bits
                )
            )
            reason = None
        except arithmetic.BindingError as error:
            result, reason = None, str(error)
        conversion_cases.append(
            {
                "name": name,
                "bits": bits,
                "denominator": denominator,
                "q_quantum": q,
                "apply_quantum": apply,
                "numerators": numerators,
                "result": result,
                "oracle_rejection": reason,
            }
        )

    for index, ((domain, shard), assignment) in enumerate(witness.assignments.items()):
        body = witness.expected_parameter(domain, shard)
        rows = []
        for contribution in assignment["contributions"]:
            q = native.resolve(store, contribution["q"], "Q_SHARD")
            rows.append([*contribution["weight"], q["values"]])
        parameter(
            f"native_{index}",
            rows,
            assignment["denominator"],
            witness.profile["accumulator_bits"],
            native_key=[domain, shard],
        )
        native.require(parameter_cases[-1]["result"] == body["numerators"], "ORACLE_DISAGREEMENT")
        conversion(
            f"native_{index}",
            body["numerators"],
            body["denominator"],
            assignment["quantum"],
            witness.quantum,
            witness.profile["accumulator_bits"],
        )

    for bits in (64, 128):
        suffix = f"_{bits}"
        parameter("half" + suffix, [[1, 2, [3, -3]], [1, 2, [4, -4]]], bits=bits)
        parameter("unequal_denominators" + suffix, [[1, 2, [3]], [1, 3, [-4]]], 6, bits)
        parameter("different_bound_denominator" + suffix, [[1, 2, [3]], [1, 3, [-4]]], 12, bits)
        parameter("zero_weight" + suffix, [[0, 1, [MIN64, MAX64]]], 1, bits)
        parameter("signed_endpoints" + suffix, [[1, 1, [MIN64, MAX64]]], 1, bits)
        parameter("nonreduced_weight" + suffix, [[2, 4, [1]]], 4, bits)
        parameter("negative_weight" + suffix, [[-1, 1, [1]]], 1, bits)
        parameter("zero_denominator" + suffix, [[1, 1, [1]]], 0, bits)
        parameter("nondividing_denominator" + suffix, [[1, 3, [1]]], 2, bits)
        parameter("shape_mismatch" + suffix, [[1, 2, [1, 2]], [1, 2, [3]]], 2, bits)
        parameter("empty_rows" + suffix, [], 1, bits)
        parameter("empty_vector" + suffix, [[1, 1, []]], 1, bits)
        parameter("q_outside_int64" + suffix, [[1, 1, [MAX64 + 1]]], 1, bits)
        parameter("weight_outside_int64" + suffix, [[MAX64 + 1, 1, [0]]], 1, bits)
        conversion("half_ties" + suffix, [1, -1, 3, -3], bits=bits)
        conversion("nonunit_quantum" + suffix, [7, -7], q=(3, 2), apply=(1, 4), bits=bits)
        conversion("signed_endpoints" + suffix, [MIN64, MAX64], 1, bits=bits)
        conversion("empty_vector" + suffix, [], bits=bits)
        conversion("nonreduced_quantum" + suffix, [1], q=(2, 4), bits=bits)
        conversion("zero_quantum" + suffix, [1], q=(0, 1), bits=bits)
        conversion("zero_denominator" + suffix, [1], 0, bits=bits)
        conversion("negative_denominator" + suffix, [1], -1, bits=bits)

    parameter("coefficient_overflow", [[MAX64, 1, [0]]], MAX64)
    parameter("coefficient_sum_overflow_zero_result", [[1, 1, [0]], [1, 1, [0]]], MAX64)
    parameter("product_overflow", [[2, 1, [MAX64]]], 1)
    parameter("unsafe_prefix_safe_final", [[1, 1, [MAX64]], [1, 1, [1]], [1, 1, [-1]]], 1)
    parameter("wide_product", [[MAX64, 1, [MAX64]]], 1, 128)
    parameter("wide_product_overflow", [[MAX64, 1, [3]]], MAX64, 128)
    conversion("cancellation_does_not_save_product", [MAX64], 2, q=(2, 1), apply=(2, 1))
    conversion("denominator_product_overflow", [0], MAX64, q=(1, 2))
    conversion("numerator_outside_accumulator", [MAX64 + 1], 2)
    conversion("wide_numerator", [MAX64 + 1], 2, bits=128)

    lines = [
        "-- Generated from the draft oracle and pinned native fixture; not a decoder proof.",
        "import DeltaReduce.ParameterKernel",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 8000000",
        "namespace DeltaReduce.ParameterKernelVectors",
        "open ParameterKernel",
        "",
    ]
    for case in parameter_cases:
        bits = case["bits"]
        rows = (
            "["
            + ", ".join(f"⟨{a}, {b}, {lean_list(values)}⟩" for a, b, values in case["rows"])
            + "]"
        )
        expected = "none" if case["result"] is None else "some " + lean_list(case["result"])
        lines.extend(
            [
                f"theorem parameter_{case['name']} :",
                f"    checkedParameter ({-(1 << (bits - 1))}) {(1 << (bits - 1)) - 1} "
                f"({MIN64}) {MAX64} ({case['denominator']}) {case['width']} {rows}",
                f"      = {expected} := by decide",
            ]
        )
    for case in conversion_cases:
        bits = case["bits"]
        scalars = [case["denominator"], *case["q_quantum"], *case["apply_quantum"]]
        expected = "none" if case["result"] is None else "some " + lean_list(case["result"])
        lines.extend(
            [
                f"theorem conversion_{case['name']} :",
                f"    checkedDomainVector ({-(1 << (bits - 1))}) {(1 << (bits - 1)) - 1} "
                f"({MIN64}) {MAX64} " + " ".join(f"({v})" for v in scalars),
                f"      {lean_list(case['numerators'])} = {expected} := by decide",
            ]
        )
    lines.extend(["end DeltaReduce.ParameterKernelVectors", ""])
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    payload = {
        "schema_version": "1.0.0",
        "scope": "ARITHMETIC_SUBLAYER_NOT_NATIVE_ADMISSION",
        "native_fixture_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "parameter_cases": parameter_cases,
        "conversion_cases": conversion_cases,
    }
    evidence.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"generated {len(parameter_cases)} parameter / {len(conversion_cases)} conversion vectors"
    )


if __name__ == "__main__":
    generate()
