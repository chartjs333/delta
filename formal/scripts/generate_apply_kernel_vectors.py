"""Checked APPLY operation vectors from the proposal oracle, not native authority."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/proposals"))
import arithmetic_binding as arithmetic  # noqa: E402
import native_binding as native  # noqa: E402

SOURCES = [
    ROOT / "formal/fixtures/traces/native" / (name + ".json")
    for name in ("normal-apply", "native-coordinate-matrix")
]
TARGET = ROOT / "formal/proofs/DeltaReduce/ApplyKernelVectors.lean"
EVIDENCE = ROOT / "formal/proposals/apply-kernel-vectors.json"
MIN64, MAX64 = -(1 << 63), (1 << 63) - 1


def lean_list(values):
    return "[" + ", ".join(str(value) for value in values) + "]"


def weight(pair):
    return "⟨" + str(pair[0]) + ", " + str(pair[1]) + "⟩"


def generate(sources=SOURCES, target=TARGET, evidence=EVIDENCE):
    cases, source_records = [], []

    def case(name, model, optimizer, rows, lr=(1, 2), mu=(1, 2), wd=(0, 1), native_source=None):
        parent = arithmetic.Parent("apply-kernel", tuple(model), tuple(optimizer))
        names = [f"domain-{index:04}" for index in range(len(rows))]
        try:
            expected = arithmetic.apply(
                parent,
                tuple((name, tuple(row[2])) for name, row in zip(names, rows, strict=True)),
                tuple((name, (row[0], row[1])) for name, row in zip(names, rows, strict=True)),
                native_schema=parent.schema,
                native_model_hash=arithmetic.value_hash("model", tuple(model)),
                native_optimizer_hash=arithmetic.value_hash("optimizer", tuple(optimizer)),
                learning_rate=lr,
                momentum=mu,
                weight_decay=wd,
            )
            result = [expected["next_model"], expected["next_optimizer"]]
            reason = None
        except arithmetic.BindingError as error:
            result, reason = None, str(error)
        cases.append(
            dict(
                name=name,
                model=model,
                optimizer=optimizer,
                rows=rows,
                lr=lr,
                mu=mu,
                wd=wd,
                result=result,
                oracle_rejection=reason,
                native_source=native_source,
            )
        )

    for index, source in enumerate(sources):
        bundle = native.decode(source.read_bytes())
        store = {key: raw.encode("ascii") for key, raw in bundle["artifacts"].items()}
        for key, raw in store.items():
            native.require(native.digest(raw) == key, "NATIVE_ARTIFACT_ID")
        snapshot = next(
            v for v in bundle["snapshots"].values() if v["action_id"] == "ACT-APPLY-VOTE"
        )
        witness = native.Witness(
            native.NativeAnchor(**snapshot["anchor"]), snapshot["authority"], store
        )
        bodies = [witness.expected_parameter(*key) for key in witness.assignments]
        expected = witness.expected_apply(bodies)
        domains = {domain: [0] * witness.size for domain in witness.domains}
        for body in bodies:
            key = (body["domain"], body["shard"])
            assignment = witness.assignments[key]
            values = arithmetic.domain_vector(
                tuple(body["numerators"]),
                body["denominator"],
                q_quantum=tuple(assignment["quantum"]),
                apply_quantum=witness.quantum,
                bits=witness.profile["accumulator_bits"],
            )
            offset, width = witness.shards[key[1]]
            domains[key[0]][offset : offset + width] = values
        rows = [[*pair, domains[domain]] for domain, pair in witness.weights]
        case(
            f"native_{index}",
            list(witness.parent_state.model),
            list(witness.parent_state.momentum),
            rows,
            tuple(witness.profile["learning_rate"]),
            tuple(witness.profile["momentum"]),
            tuple(witness.profile["weight_decay"]),
            native_source=source.name,
        )
        assert cases[-1]["result"] == [expected["next_model"], expected["next_optimizer"]]
        source_records.append(
            dict(
                path=source.name,
                sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                authority=snapshot["authority"]["id"],
                size=witness.size,
                domain_count=len(witness.domains),
                parameter_ids=expected["parameter_body_ids"],
            )
        )

    case("signed_rounding", [20, -20, 0, 1], [1, -1, 1, -1], [[1, 1, [3, -3, 0, 0]]])
    case("coprime_lcm", [10, -10], [2, -2], [[1, 2, [3, -3]], [1, 3, [-2, 2]], [1, 6, [7, -7]]])
    case("zero_weight_domain", [0], [0], [[0, 1, [MAX64]], [1, 1, [2]]])
    case("minimum_survives", [MIN64], [0], [[1, 1, [0]]], lr=(0, 1), mu=(0, 1))
    case("maximum_survives", [MAX64], [0], [[1, 1, [0]]], lr=(0, 1), mu=(0, 1))
    case("zero_learning_rate", [10], [2], [[1, 1, [3]]], lr=(0, 1))
    case("nonzero_decay", [20, -20], [2, -2], [[1, 1, [3, -3]]], wd=(1, 2))
    case("nonunit_learning_rate", [20, -20], [0, 0], [[1, 1, [3, -3]]], lr=(2, 3))
    case("not_normalized", [0], [0], [[1, 3, [0]], [1, 3, [0]]])
    case("over_normalized", [0], [0], [[1, 1, [0]], [1, 1, [0]]])
    case("noncanonical_weight", [0], [0], [[2, 4, [0]], [1, 2, [0]]])
    case("negative_weight", [0], [0], [[-1, 1, [0]]])
    case("zero_denominator", [0], [0], [[1, 0, [0]]])
    case("empty_domains", [0], [0], [])
    case("empty_model", [], [], [[1, 1, []]])
    case("optimizer_shape", [0, 0], [0], [[1, 1, [0, 0]]])
    case("domain_shape", [0, 0], [0, 0], [[1, 1, [0]]])
    case("zero_weight_bad_value", [0], [0], [[0, 1, [MAX64 + 1]], [1, 1, [0]]])
    case("lcm_overflow_zero_output", [0], [0], [[1, 3037000499, [0]], [1, 3037000503, [0]]])
    case("first_product_overflow_safe_rational", [0], [0], [[2, 3, [MAX64]], [1, 3, [0]]])
    case("second_product_overflow", [0], [0], [[1, 2, [MAX64 // 2]], [1, 3, [0]], [1, 6, [0]]])
    case("unsafe_prefix_safe_final", [0], [0], [[1, 3, [MAX64]], [1, 3, [MAX64]], [1, 3, [-MAX64]]])
    case("momentum_product_overflow", [0], [MAX64], [[1, 1, [0]]], mu=(2, 3))
    case("next_momentum_overflow", [0], [MAX64], [[1, 1, [1]]], mu=(1, 1))
    case("direction_overflow", [0], [0], [[1, 1, [MAX64]]], mu=(1, 1))
    case("decay_product_overflow", [MAX64], [0], [[1, 1, [0]]], wd=(2, 3))
    case(
        "sum_overflow_before_zero_lr", [MAX64], [0], [[1, 1, [1]]], lr=(0, 1), mu=(0, 1), wd=(1, 1)
    )
    case("step_product_overflow", [0], [0], [[1, 1, [MAX64]]], lr=(2, 3), mu=(0, 1))
    case("model_subtraction_underflow", [MIN64], [0], [[1, 1, [1]]], lr=(1, 1), mu=(0, 1))
    case("invalid_momentum_fraction", [0], [0], [[1, 1, [0]]], mu=(2, 4))

    lines = [
        "-- Generated by formal/scripts/generate_apply_kernel_vectors.py; DO NOT EDIT.",
        "-- Proposal-oracle vectors, not native decoder/admission/refinement evidence.",
        "import DeltaReduce.ApplyKernel",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 8000000",
        "namespace DeltaReduce.ApplyKernelVectors",
        "open ApplyKernel",
        f"def lo : Int := {MIN64}",
        f"def hi : Int := {MAX64}",
    ]
    for item in cases:
        rows = (
            "["
            + ", ".join(
                "⟨" + weight(row[:2]) + ", " + lean_list(row[2]) + "⟩" for row in item["rows"]
            )
            + "]"
        )
        lines += [
            f"theorem {item['name']} :",
            f"    (deriveApply lo hi {lean_list(item['model'])} {lean_list(item['optimizer'])}",
            f"      {rows} {weight(item['lr'])} {weight(item['mu'])} {weight(item['wd'])}).map",
            "      (fun result => (result.nextModel, result.nextOptimizer)) =",
        ]
        if item["result"] is None:
            lines += ["      none := by decide"]
        else:
            lines += [
                "      some ("
                + lean_list(item["result"][0])
                + ", "
                + lean_list(item["result"][1])
                + ") := by decide"
            ]
    lines += ["end DeltaReduce.ApplyKernelVectors", ""]
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    evidence.write_text(
        json.dumps(
            dict(
                schema_version="1.0.0",
                status="SCOPED_VECTORS_NOT_AUTHORITY",
                formal_go=False,
                native_runtime=False,
                source_artifacts=source_records,
                cases=cases,
            ),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"generated {len(cases)} APPLY cases from {len(sources)} native-fixture graphs")


if __name__ == "__main__":
    generate()
