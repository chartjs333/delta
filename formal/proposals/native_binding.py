"""Content-addressed arithmetic witness for amendment 0001 (NOT runtime authority).

The anchor is an independently authenticated native snapshot, never a field in a
vote request. Certificate validity is a named premise; this oracle proves neither
signatures nor durable storage. It checks the concrete bytes under that premise.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import arithmetic_binding as arithmetic

require = arithmetic.require
BindingError = arithmetic.BindingError
DOMAIN = b"deltareduce.000.arithmetic-binding.draft1\x00"
MAX_BYTES = 4 * 1024 * 1024
MAX_ITEMS = 4096


def shape(value: Any, keys: str) -> dict:
    require(type(value) is dict and set(value) == set(keys.split()), "OBJECT_SHAPE")
    return value


def sequence(value: Any) -> list:
    require(type(value) is list and 0 < len(value) <= MAX_ITEMS, "ARRAY_BOUND")
    return value


def identifier(value: Any) -> str:
    require(
        type(value) is str and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value) is not None,
        "IDENTIFIER",
    )
    return value


def integer(value: Any, minimum: int = 0) -> int:
    require(type(value) is int and minimum <= value <= (1 << 63) - 1, "INTEGER_RANGE")
    return value


def fraction(value: Any, *, positive: bool = False) -> tuple[int, int]:
    require(type(value) is list and len(value) == 2, "FRACTION_SHAPE")
    arithmetic.rational(*value)
    require(not positive or value[0] > 0, "POSITIVE_QUANTUM")
    return tuple(value)


def vector(value: Any, size: int, bits: int = 64) -> tuple[int, ...]:
    require(len(sequence(value)) == size, "VECTOR_SIZE")
    return tuple(arithmetic.checked(item, bits) for item in value)


def canonical(value: Any) -> bytes:
    """Draft witness JSON: ASCII, integers, sorted keys, no insignificant bytes."""

    def visit(item: Any, depth: int = 0) -> None:
        require(depth <= 32, "DEPTH_BOUND")
        if type(item) is dict:
            require(all(type(key) is str and key.isascii() for key in item), "ASCII_KEYS")
            for child in item.values():
                visit(child, depth + 1)
        elif type(item) is list:
            require(len(item) <= MAX_ITEMS, "ARRAY_BOUND")
            for child in item:
                visit(child, depth + 1)
        elif type(item) is str:
            require(item.isascii(), "ASCII_STRING")
        elif type(item) is int:
            arithmetic.checked(item, 128)
        else:
            require(item is None or type(item) is bool, "JSON_TYPE")

    visit(value)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    require(len(encoded) <= MAX_BYTES, "ARTIFACT_BOUND")
    return encoded


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(DOMAIN + data).hexdigest()


def decode(data: bytes) -> Any:
    require(type(data) is bytes and 0 < len(data) <= MAX_BYTES, "ARTIFACT_BOUND")

    def pairs(entries: list[tuple[str, Any]]) -> dict:
        result = {}
        for key, value in entries:
            require(key not in result, "DUPLICATE_KEY")
            result[key] = value
        return result

    try:
        result = json.loads(data, object_pairs_hook=pairs)
        require(canonical(result) == data, "NONCANONICAL_BYTES")
        return result
    except BindingError:
        raise
    except (UnicodeError, ValueError, RecursionError) as error:
        raise BindingError("INVALID_JSON") from error


def put(store: dict[str, bytes], kind: str, payload: dict) -> dict:
    data = canonical({"kind": kind, "payload": payload})
    ref = {"id": digest(data), "kind": kind, "length": len(data)}
    store[ref["id"]] = data
    return ref


def resolve(store: Mapping[str, bytes], ref: dict, kind: str) -> dict:
    shape(ref, "id kind length")
    require(
        type(ref["id"]) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", ref["id"]) is not None,
        "CONTENT_ID",
    )
    require(ref["kind"] == kind, "ARTIFACT_KIND")
    integer(ref["length"], 1)
    require(ref["length"] <= MAX_BYTES, "ARTIFACT_BOUND")
    data = store.get(ref["id"])
    require(type(data) is bytes, "ARTIFACT_MISSING")
    require(len(data) == ref["length"] and digest(data) == ref["id"], "ARTIFACT_BYTES")
    item = shape(decode(data), "kind payload")
    require(item["kind"] == kind and type(item["payload"]) is dict, "ARTIFACT_KIND")
    return item["payload"]


@dataclass(frozen=True)
class NativeAnchor:
    """Trusted pre-state projection. Authenticating this anchor is a separate obligation."""

    authority_id: str
    current_model_hash: str
    current_optimizer_hash: str
    round_id: str
    height: int
    view: int
    epoch: str
    logical_time: int
    hard_deadline: int
    role: str
    recovered: bool
    parent_checkpoint: str
    aggregate_id: str | None = None
    aggregate_length: int = 0


class Witness:
    def __init__(self, anchor: NativeAnchor, authority: dict, store: Mapping[str, bytes]):
        require(anchor.recovered is True, "RECOVERY_REQUIRED")
        require(type(anchor.role) is str and anchor.role in {"PARAMETER", "APPLY"}, "ROLE")
        for number in (anchor.height, anchor.view, anchor.logical_time, anchor.hard_deadline):
            integer(number)
        require(anchor.logical_time < anchor.hard_deadline, "HARD_DEADLINE")
        shape(authority, "id kind length")
        require(authority["id"] == anchor.authority_id, "NATIVE_AUTHORITY_ROOT")
        # Copy bytes so a mutable transport map cannot change the computation mid-check.
        self.store = dict(store)
        self.anchor = anchor
        self.authority = dict(authority)
        root = shape(
            resolve(self.store, authority, "AUTHORITY"),
            "context schema profile plan model optimizer parents",
        )
        context = shape(root["context"], "round height view epoch hard_deadline parent_checkpoint")
        require(
            canonical(context)
            == canonical(
                {
                    "round": anchor.round_id,
                    "height": anchor.height,
                    "view": anchor.view,
                    "epoch": anchor.epoch,
                    "hard_deadline": anchor.hard_deadline,
                    "parent_checkpoint": anchor.parent_checkpoint,
                }
            ),
            "NATIVE_CONTEXT",
        )
        identifier(context["round"])
        identifier(context["epoch"])
        identifier(context["parent_checkpoint"])
        self.root = root
        self.context = context
        schema = shape(resolve(self.store, root["schema"], "SCHEMA"), "coordinates shards")
        coordinates = sequence(schema["coordinates"])
        require(all(identifier(item) for item in coordinates), "COORDINATES")
        require(coordinates == sorted(set(coordinates)), "COORDINATE_ORDER")
        self.size = len(coordinates)
        self.shards = {}
        covered = []
        for item in sequence(schema["shards"]):
            shape(item, "id offset length")
            shard = identifier(item["id"])
            require(shard not in self.shards, "DUPLICATE_SHARD")
            offset, length = integer(item["offset"]), integer(item["length"], 1)
            require(offset + length <= self.size, "SHARD_RANGE")
            covered.extend(range(offset, offset + length))
            self.shards[shard] = (offset, length)
        require(list(self.shards) == sorted(self.shards), "SHARD_ORDER")
        require(sorted(covered) == list(range(self.size)), "EXACT_SCHEMA_COVERAGE")
        self.profile = shape(
            resolve(self.store, root["profile"], "PROFILE"),
            "accumulator_bits apply_quantum domain_weights learning_rate momentum "
            "weight_decay rounding nesterov output_range",
        )
        require(
            type(self.profile["accumulator_bits"]) is int
            and self.profile["accumulator_bits"] in (64, 128),
            "ACCUMULATOR_WIDTH",
        )
        require(
            self.profile["rounding"] == "HALF_TOWARD_POSITIVE"
            and self.profile["nesterov"] is True
            and self.profile["output_range"] == "FULL_SIGNED_INT64",
            "APPLY_PROFILE",
        )
        self.quantum = fraction(self.profile["apply_quantum"], positive=True)
        self.weights = []
        for weight in sequence(self.profile["domain_weights"]):
            shape(weight, "domain weight")
            self.weights.append((identifier(weight["domain"]), fraction(weight["weight"])))
        self.domains = [domain for domain, _ in self.weights]
        require(self.domains == sorted(set(self.domains)), "DOMAIN_ORDER")
        for key in ("learning_rate", "momentum", "weight_decay"):
            fraction(self.profile[key])
        model = self.parent("MODEL", root["model"])
        optimizer = self.parent("OPTIMIZER", root["optimizer"])
        self.parent_state = arithmetic.Parent(root["schema"]["id"], model, optimizer)
        arithmetic.verify_parent(
            self.parent_state,
            native_schema=root["schema"]["id"],
            native_model_hash=anchor.current_model_hash,
            native_optimizer_hash=anchor.current_optimizer_hash,
        )
        # These are projections of independently verified certificates, not signatures.
        parents = shape(root["parents"], "isc ec apc")
        isc = shape(resolve(self.store, parents["isc"], "ISC_PROJECTION"), "members commitments")
        ec = shape(resolve(self.store, parents["ec"], "EC_PROJECTION"), "isc eligible")
        apc = shape(resolve(self.store, parents["apc"], "APC_PROJECTION"), "ec plan")
        require(
            ec["isc"] == parents["isc"]
            and apc["ec"] == parents["ec"]
            and apc["plan"] == root["plan"],
            "CERTIFICATE_PARENTAGE",
        )
        members = sequence(isc["members"])
        require(
            all(identifier(item) for item in members) and members == sorted(set(members)),
            "ISC_MEMBERS",
        )
        eligible = sequence(ec["eligible"])
        require(
            all(identifier(item) for item in eligible)
            and eligible == sorted(set(eligible))
            and set(eligible) <= set(members),
            "EC_MEMBERS",
        )
        plan = shape(
            resolve(self.store, root["plan"], "PLAN"), "schema profile tickets assignments"
        )
        require(
            plan["schema"] == root["schema"] and plan["profile"] == root["profile"], "PLAN_BINDING"
        )
        self.tickets = {}
        for item in sequence(plan["tickets"]):
            shape(item, "id domain")
            ticket = identifier(item["id"])
            require(ticket not in self.tickets and item["domain"] in self.domains, "TICKET_DOMAIN")
            self.tickets[ticket] = item["domain"]
        require(list(self.tickets) == eligible, "ELIGIBLE_TICKET_COVERAGE")
        self.committed_q = {}
        committed_tickets = []
        for item in sequence(isc["commitments"]):
            shape(item, "ticket domain leaves")
            ticket = identifier(item["ticket"])
            committed_tickets.append(ticket)
            require(item["domain"] in self.domains, "ISC_DOMAIN")
            if ticket in self.tickets:
                require(self.tickets[ticket] == item["domain"], "ISC_PLAN_DOMAIN")
            shards = []
            for leaf in sequence(item["leaves"]):
                shape(leaf, "shard q")
                shard = identifier(leaf["shard"])
                shards.append(shard)
                self.committed_q[(ticket, shard)] = leaf["q"]
            require(shards == list(self.shards), "ISC_Q_COVERAGE")
        require(committed_tickets == members, "ISC_COMMITMENT_COVERAGE")
        self.assignments = {}
        for item in sequence(plan["assignments"]):
            shape(item, "domain shard context denominator quantum contributions")
            key = (identifier(item["domain"]), identifier(item["shard"]))
            require(
                key not in self.assignments and key[0] in self.domains and key[1] in self.shards,
                "ASSIGNMENT_KEY",
            )
            identifier(item["context"])
            integer(item["denominator"], 1)
            fraction(item["quantum"], positive=True)
            self.assignments[key] = item
        expected_keys = [(domain, shard) for domain in self.domains for shard in self.shards]
        require(list(self.assignments) == expected_keys, "EXACT_DOMAIN_SHARD_COVERAGE")
        contexts = [item["context"] for item in self.assignments.values()]
        require(len(contexts) == len(set(contexts)), "DUPLICATE_VOTE_CONTEXT")

    def parent(self, kind: str, ref: dict) -> tuple[int, ...]:
        payload = shape(resolve(self.store, ref, kind), "schema quantum values")
        require(payload["schema"] == self.root["schema"], "PARENT_SCHEMA")
        require(fraction(payload["quantum"], positive=True) == self.quantum, "PARENT_QUANTUM")
        return vector(payload["values"], self.size)

    def expected_parameter(self, domain: str, shard: str) -> dict:
        identifier(domain)
        identifier(shard)
        require((domain, shard) in self.assignments, "UNPLANNED_PARAMETER")
        assignment = self.assignments[(domain, shard)]
        expected_tickets = tuple(
            ticket for ticket, value in self.tickets.items() if value == domain
        )
        terms, leaf_ids = [], []
        _, length = self.shards[shard]
        for contribution in sequence(assignment["contributions"]):
            shape(contribution, "ticket weight q")
            ticket = identifier(contribution["ticket"])
            weight = fraction(contribution["weight"])
            require(
                contribution["q"] == self.committed_q.get((ticket, shard)), "COMMITMENT_Q_BINDING"
            )
            q = shape(
                resolve(self.store, contribution["q"], "Q_SHARD"),
                "ticket domain shard schema quantum values",
            )
            require((q["ticket"], q["domain"], q["shard"]) == (ticket, domain, shard), "Q_CONTEXT")
            require(q["schema"] == self.root["schema"], "Q_SCHEMA")
            require(
                fraction(q["quantum"], positive=True) == tuple(assignment["quantum"]), "Q_QUANTUM"
            )
            terms.append((ticket, weight, vector(q["values"], length)))
            leaf_ids.append(contribution["q"]["id"])
        numerators = arithmetic.parameter(
            tuple(terms),
            native_ticket_ids=expected_tickets,
            denominator=assignment["denominator"],
            bits=self.profile["accumulator_bits"],
        )
        return {
            "kind": "PARAMETER_EXPECTED",
            "authority_id": self.authority["id"],
            "context": assignment["context"],
            "domain": domain,
            "shard": shard,
            "denominator": assignment["denominator"],
            "numerators": list(numerators),
            "input_leaf_ids": leaf_ids,
        }

    def expected_apply(self, parameter_bodies: list[dict]) -> dict:
        expected = [self.expected_parameter(*key) for key in self.assignments]
        # Exact bytes as well as integers: Python's bool/int equality is insufficient.
        require(
            canonical(parameter_bodies) == canonical(expected), "PARAMETER_ARITHMETIC_OR_COVERAGE"
        )
        aggregate_ref = {
            "id": self.anchor.aggregate_id,
            "kind": "AGGREGATE_PROJECTION",
            "length": self.anchor.aggregate_length,
        }
        aggregate = shape(
            resolve(self.store, aggregate_ref, "AGGREGATE_PROJECTION"), "authority_id parameters"
        )
        require(aggregate["authority_id"] == self.authority["id"], "NATIVE_AGGREGATE_CONTEXT")
        require(
            canonical(aggregate["parameters"]) == canonical(expected),
            "CERTIFIED_PARAMETER_MISMATCH",
        )
        domains = {domain: [0] * self.size for domain in self.domains}
        for body in expected:
            assignment = self.assignments[(body["domain"], body["shard"])]
            values = arithmetic.domain_vector(
                tuple(body["numerators"]),
                body["denominator"],
                q_quantum=tuple(assignment["quantum"]),
                apply_quantum=self.quantum,
                bits=self.profile["accumulator_bits"],
            )
            offset, length = self.shards[body["shard"]]
            domains[body["domain"]][offset : offset + length] = values
        result = arithmetic.apply(
            self.parent_state,
            tuple((domain, tuple(values)) for domain, values in domains.items()),
            tuple(self.weights),
            native_schema=self.root["schema"]["id"],
            native_model_hash=self.anchor.current_model_hash,
            native_optimizer_hash=self.anchor.current_optimizer_hash,
            learning_rate=tuple(self.profile["learning_rate"]),
            momentum=tuple(self.profile["momentum"]),
            weight_decay=tuple(self.profile["weight_decay"]),
        )
        return {
            "kind": "APPLY_EXPECTED",
            "authority_id": self.authority["id"],
            "aggregate_id": self.anchor.aggregate_id,
            "parameter_body_ids": [digest(canonical(body)) for body in expected],
            **result,
        }

    def admit(self, request: bytes) -> bytes:
        command = shape(decode(request), "action payload")
        if command["action"] == "ACT-PARAM-VOTE":
            require(self.anchor.role == "PARAMETER", "ROLE")
            candidate = command["payload"]
            require(type(candidate) is dict, "PARAMETER_BODY")
            expected = self.expected_parameter(candidate.get("domain"), candidate.get("shard"))
        elif command["action"] == "ACT-APPLY-VOTE":
            require(self.anchor.role == "APPLY", "ROLE")
            candidate = command["payload"]
            expected = self.expected_apply(
                [self.expected_parameter(*key) for key in self.assignments]
            )
        else:
            raise BindingError("ACTION")
        require(canonical(candidate) == canonical(expected), "ARITHMETIC_RESULT_MISMATCH")
        # A pre-WAL expected body, never a durable receipt or sendable certificate.
        return canonical(expected)
