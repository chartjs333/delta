"""Execute the independent C++ oracle in a caller-selected immutable local image."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
from pathlib import Path

import arithmetic_binding as a


def cases() -> list[tuple[str, str]]:
    output = []

    def case(line, operation):
        try:
            result = operation()
            expected = "OK " + str(result)
        except a.BindingError:
            expected = "REJECT"
        output.append((line, expected))

    for n in [*range(-33, 34), -(1 << 127), (1 << 127) - 1, -(1 << 63), (1 << 63) - 1]:
        for d in [0, 1, 2, 3, 7, (1 << 63) - 1]:
            case(f"R {n} {d}", lambda n=n, d=d: a.rounding(n, d))
    for bits in (64, 128):
        for n in [-1, 0, 1, -(1 << 63), (1 << 63) - 1, (1 << 127) - 1]:
            for q, model in [((1, 1), (1, 1)), ((1, 2), (1, 4)), ((2, 1), (1, 1))]:
                for d in (1, 2):
                    line = f"D {bits} {n} {d} {q[0]} {q[1]} {model[0]} {model[1]}"
                    case(
                        line,
                        lambda n=n, d=d, q=q, model=model, bits=bits: a.domain_vector(
                            (n,), d, q_quantum=q, apply_quantum=model, bits=bits
                        )[0],
                    )
    rng = random.Random(10001)
    for index in range(256):
        bits = (64, 128)[index % 2]
        denominator = (1, 2, 6)[index % 3]
        terms = tuple((str(i), (1, denominator), (rng.randint(-1000, 1000),)) for i in range(3))
        line = f"P {bits} {denominator} 3 " + " ".join(
            f"{a0} {b} {q[0]}" for _, (a0, b), q in terms
        )
        case(
            line,
            lambda terms=terms, denominator=denominator, bits=bits: a.parameter(
                terms, native_ticket_ids=("0", "1", "2"), denominator=denominator, bits=bits
            )[0],
        )
    for bits in (64, 128):
        terms = (("0", (1, 1), ((1 << 63) - 1,)), ("1", (1, 1), (1,)), ("2", (1, 1), (-1,)))
        line = f"P {bits} 1 3 1 1 {(1 << 63) - 1} 1 1 1 1 1 -1"
        case(
            line,
            lambda terms=terms, bits=bits: a.parameter(
                terms, native_ticket_ids=("0", "1", "2"), denominator=1, bits=bits
            )[0],
        )
    for index in range(256):
        theta, momentum = rng.randint(-1000, 1000), rng.randint(-100, 100)
        values = (rng.randint(-100, 100), rng.randint(-100, 100))
        lr, mu, wd = (1, (1, 2, 3)[index % 3]), (1, 2), (1, 10)
        line = f"A {theta} {momentum} 2 {values[0]} 1 2 {values[1]} 1 2 "
        line += f"{lr[0]} {lr[1]} {mu[0]} {mu[1]} {wd[0]} {wd[1]}"

        def result(theta=theta, momentum=momentum, values=values, lr=lr, mu=mu, wd=wd):
            parent = a.Parent("s", (theta,), (momentum,))
            answer = a.apply(
                parent,
                (("d0", (values[0],)), ("d1", (values[1],))),
                (("d0", (1, 2)), ("d1", (1, 2))),
                native_schema="s",
                native_model_hash=a.value_hash("model", parent.model),
                native_optimizer_hash=a.value_hash("optimizer", parent.momentum),
                learning_rate=lr,
                momentum=mu,
                weight_decay=wd,
            )
            return (
                a.value_bytes(tuple(answer["next_model"])).decode()
                + "|"
                + a.value_bytes(tuple(answer["next_optimizer"])).decode()
            )

        case(line, result)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if re.fullmatch(r"sha256:[0-9a-f]{64}", args.image) is None:
        parser.error("image must be an exact local sha256 ID")
    source = Path(__file__).resolve().parent
    vectors = cases()
    payload = "\n".join(line for line, _ in vectors) + "\n"
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--tmpfs",
        "/build:rw,exec,size=128m",
        "--workdir",
        "/build",
        "--env",
        "TMPDIR=/build",
        "-i",
        "--mount",
        f"type=bind,source={source},target=/src,readonly",
        args.image,
        "sh",
        "-c",
        "g++ -std=c++20 -O1 -Wall -Wextra -Werror -fsanitize=undefined "
        "-fno-sanitize-recover=all /src/arithmetic_oracle.cpp -o /build/oracle && /build/oracle",
    ]
    result = subprocess.run(command, input=payload, capture_output=True, text=True, timeout=180)
    lines = result.stdout.splitlines()
    mismatches = [
        {
            "case": index,
            "input": case[0],
            "expected": case[1],
            "actual": lines[index] if index < len(lines) else None,
        }
        for index, case in enumerate(vectors)
        if index >= len(lines) or lines[index] != case[1]
    ]
    passed = (
        result.returncode == 0
        and not result.stderr
        and not mismatches
        and len(lines) == len(vectors)
    )
    report = {
        "status": "PASS" if passed else "FAIL",
        "formal_go": False,
        "scope": "CANDIDATE_ARITHMETIC_NOT_NATIVE_RUNTIME_CONFORMANCE",
        "image_id": args.image,
        "cases": len(vectors),
        "returncode": result.returncode,
        "input_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "output_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "oracle_sha256": hashlib.sha256(
            (source / "arithmetic_oracle.cpp").read_bytes()
        ).hexdigest(),
        "sanitizer": "UBSan_no_recovery",
        "stderr": result.stderr,
        "mismatches": mismatches,
    }
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "inputs.txt").write_bytes(payload.encode())
    (args.output / "outputs.txt").write_bytes(result.stdout.encode())
    (args.output / "report.json").write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {**report, "mismatches": mismatches[:5], "mismatch_count": len(mismatches)},
            sort_keys=True,
        )
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
