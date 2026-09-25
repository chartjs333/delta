"""Executable arithmetic design vectors for amendment 0001, NOT authority.

This is a mathematical proposal oracle. It imports no production runtime, emits
no votes/certificates, and is intentionally outside the accepted semantic set.
Production TLA/Lean/refinement integration is still required before runtime work.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import gcd, lcm


class BindingError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise BindingError(reason)


def checked(value: int, bits: int = 64) -> int:
    require(type(value) is int and bits in (64, 128), "INTEGER_PROFILE")
    require(-(1 << (bits - 1)) <= value < (1 << (bits - 1)), "OVERFLOW")
    return value


def rounding(numerator: int, denominator: int) -> int:
    require(type(numerator) is int and type(denominator) is int and denominator > 0, "RATIONAL")
    quotient, remainder = divmod(numerator, denominator)
    return quotient if remainder < denominator - remainder else quotient + 1


def rational(numerator: int, denominator: int) -> None:
    checked(numerator)
    require(type(denominator) is int and 0 < denominator <= (1 << 63) - 1, "DENOMINATOR")
    require(numerator >= 0 and gcd(numerator, denominator) == 1, "NONCANONICAL_WEIGHT")


def value_bytes(values: tuple[int, ...]) -> bytes:
    require(bool(values), "EMPTY_VECTOR")
    for value in values:
        checked(value)
    return "".join(f"{value};" for value in values).encode("ascii")


def value_hash(kind: str, values: tuple[int, ...]) -> str:
    require(kind in {"model", "optimizer"}, "ARTIFACT_KIND")
    data = f"deltareduce.008.{kind}.v1".encode() + b"\x00" + value_bytes(values)
    return "sha256:" + hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Parent:
    schema: str
    model: tuple[int, ...]
    momentum: tuple[int, ...]


def verify_parent(
    parent: Parent, *, native_schema: str, native_model_hash: str, native_optimizer_hash: str
) -> None:
    require(parent.schema == native_schema, "PARENT_SCHEMA")
    require(len(parent.model) == len(parent.momentum), "PARENT_SHAPE")
    require(value_hash("model", parent.model) == native_model_hash, "PARENT_MODEL")
    require(value_hash("optimizer", parent.momentum) == native_optimizer_hash, "PARENT_OPTIMIZER")


def parameter(
    contributions: tuple[tuple[str, tuple[int, int], tuple[int, ...]], ...],
    *,
    native_ticket_ids: tuple[str, ...],
    denominator: int,
    bits: int = 64,
) -> tuple[int, ...]:
    """Expected numerators under the specific native-bound common denominator."""
    require(
        native_ticket_ids == tuple(sorted(set(native_ticket_ids))) and bool(native_ticket_ids),
        "NATIVE_TICKET_SET",
    )
    require(
        tuple(item[0] for item in contributions) == native_ticket_ids, "TICKET_COVERAGE_OR_ORDER"
    )
    require(type(denominator) is int and denominator > 0, "DENOMINATOR")
    checked(denominator, bits)
    width = len(contributions[0][2])
    require(width > 0, "EMPTY_VECTOR")
    result = [0] * width
    coefficient_sum = 0
    for _ticket, (a, b), values in contributions:
        rational(a, b)
        require(denominator % b == 0, "DENOMINATOR_NOT_DIVISIBLE")
        require(len(values) == width, "SHARD_SHAPE")
        coefficient = checked(a * (denominator // b), bits)
        coefficient_sum = checked(coefficient_sum + coefficient, bits)
        for index, value in enumerate(values):
            checked(value)
            term = checked(coefficient * value, bits)
            result[index] = checked(result[index] + term, bits)
    return tuple(result)


def domain_vector(
    numerators: tuple[int, ...],
    denominator: int,
    *,
    q_quantum: tuple[int, int] = (1, 1),
    apply_quantum: tuple[int, int] = (1, 1),
    bits: int = 64,
) -> tuple[int, ...]:
    """One rounding before mixture, including explicitly ordered quantum conversion."""
    require(bool(numerators), "EMPTY_VECTOR")
    require(type(denominator) is int and denominator > 0, "DENOMINATOR")
    checked(denominator, bits)
    u, v = q_quantum
    x, y = apply_quantum
    rational(u, v)
    rational(x, y)
    require(u > 0 and x > 0, "QUANTUM_POSITIVE")
    d = checked(checked(denominator * v, bits) * x, bits)
    result = []
    for numerator in numerators:
        checked(numerator, bits)
        p = checked(checked(numerator * u, bits) * y, bits)
        result.append(checked(rounding(p, d)))
    return tuple(result)


def apply(
    parent: Parent,
    domains: tuple[tuple[str, tuple[int, ...]], ...],
    weights: tuple[tuple[str, tuple[int, int]], ...],
    *,
    native_schema: str,
    native_model_hash: str,
    native_optimizer_hash: str,
    learning_rate: tuple[int, int],
    momentum: tuple[int, int],
    weight_decay: tuple[int, int],
) -> dict:
    verify_parent(
        parent,
        native_schema=native_schema,
        native_model_hash=native_model_hash,
        native_optimizer_hash=native_optimizer_hash,
    )
    ids = tuple(item[0] for item in weights)
    require(bool(ids) and ids == tuple(sorted(set(ids))), "DOMAIN_ORDER")
    require(tuple(item[0] for item in domains) == ids, "DOMAIN_COVERAGE")
    require(all(len(values) == len(parent.model) for _, values in domains), "DOMAIN_SHAPE")
    denominator = 1
    for _, (a, b) in weights:
        rational(a, b)
        denominator = checked(lcm(denominator, b))
    require(sum(a * (denominator // b) for _, (a, b) in weights) == denominator, "DOMAIN_MIXTURE")
    for pair in (learning_rate, momentum, weight_decay):
        rational(*pair)

    def scaled(value: int, coefficient: tuple[int, int]) -> int:
        a, b = coefficient
        return checked(rounding(checked(value * a), b))

    next_model = []
    next_optimizer = []
    for coordinate, theta in enumerate(parent.model):
        total = 0
        for (_, values), (_, (a, b)) in zip(domains, weights, strict=True):
            checked(values[coordinate])
            term = checked(checked(values[coordinate] * a) * (denominator // b))
            total = checked(total + term)
        gradient = checked(rounding(total, denominator))
        m = checked(scaled(parent.momentum[coordinate], momentum) + gradient)
        direction = checked(scaled(m, momentum) + gradient)
        decay = scaled(theta, weight_decay)
        step = scaled(checked(direction + decay), learning_rate)
        next_optimizer.append(m)
        next_model.append(checked(theta - step))
    return {
        "next_model": next_model,
        "next_optimizer": next_optimizer,
        "next_model_hash": value_hash("model", tuple(next_model)),
        "next_optimizer_hash": value_hash("optimizer", tuple(next_optimizer)),
    }


def vectors() -> dict:
    parent = Parent("schema-proposal", (20, -20), (2, -2))
    numerators = parameter(
        (("ticket-a", (1, 2), (3, -3)), ("ticket-b", (1, 2), (4, -4))),
        native_ticket_ids=("ticket-a", "ticket-b"),
        denominator=2,
    )
    domain = domain_vector(numerators, 2)
    result = apply(
        parent,
        (("domain-a", domain),),
        (("domain-a", (1, 1)),),
        native_schema=parent.schema,
        native_model_hash=value_hash("model", parent.model),
        native_optimizer_hash=value_hash("optimizer", parent.momentum),
        learning_rate=(1, 2),
        momentum=(1, 2),
        weight_decay=(0, 1),
    )
    return {
        "status": "DRAFT_NOT_AUTHORITY",
        "formal_go": False,
        "parameter_numerators": list(numerators),
        "denominator": 2,
        "domain_vector": list(domain),
        "parent_model": list(parent.model),
        "parent_momentum": list(parent.momentum),
        "result": result,
        "rounding": [[n, 2, rounding(n, 2)] for n in range(-7, 8)],
        "limitations": [
            "no_TLA_integration",
            "no_Lean_integration",
            "no_refinement_integration",
            "no_cross_language_claim",
            "no_production_artifact_graph_decoder",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(vectors(), sort_keys=True, separators=(",", ":")))
