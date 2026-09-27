"""Formal proposal: resolve original 004 preimages; no exporter authentication.

The independent caller chooses a contribution manifest identity, never its decoded
header or expected Q values. All projections are derived from retained original
bytes. This is a bounded Python relation, not a native decoder equivalence proof.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from collections.abc import Mapping
from dataclasses import dataclass

VERSION = "deltareduce.original-q-source.v1-candidate"
SEMANTICS = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
PROFILE = "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61"
MAX_JSON = 4 * 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024  # proposal resource bound, not a native limit
MAX_HEADER, MAX_PAYLOAD, MAX_ELEMENTS = 65536, 1048576, 1073741824
DOMAINS = {
    "schema": "",
    "profile": "deltareduce.004.profile.v1",
    "scale": "deltareduce.004.scale-table.v1",
    "plan": "deltareduce.004.shard-plan.v1",
    "config": "deltareduce.004.fixedpoint-config.v1",
    "proof": "deltareduce.004.proof-instance.v1",
    "manifest": "deltareduce.004.manifest.v1",
    "leaf": "deltareduce.004.shard-leaf.v1",
}
TYPES = {
    "profile": "FIXED_POINT_PROFILE",
    "scale": "QUANTIZATION_SCALE_TABLE",
    "plan": "SHARD_PLAN",
    "config": "FIXEDPOINT_ROUND_CONFIG",
    "proof": "ACCUMULATOR_PROOF_INSTANCE",
    "manifest": "ENCODED_CONTRIBUTION_MANIFEST",
}


class SourceError(ValueError):
    """Missing, incompatible or corrupt source; never a protocol outcome."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SourceError(code)


def content_id(raw: bytes, domain: str = "") -> str:
    preimage = (domain.encode("ascii") + b"\0" if domain else b"") + raw
    return "sha256:" + hashlib.sha256(preimage).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def cid(value: object) -> str:
    require(
        isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None,
        "CONTENT_ID",
    )
    return value


def token(value: object) -> str:
    require(
        isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._/-]{1,255}", value) is not None,
        "ASCII_TOKEN",
    )
    return value


def uint(value: object, maximum: int, minimum: int = 0) -> int:
    require(type(value) is int and minimum <= value <= maximum, "INTEGER_RANGE")
    return value


def decimal(value: object, maximum: int, minimum: int = 0) -> int:
    require(
        isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]{0,38}", value) is not None, "DECIMAL"
    )
    return uint(int(value), maximum, minimum)


def shape(value: object, keys: str) -> dict:
    require(type(value) is dict and set(value) == set(keys.split()), "FIELDS")
    return value


def items(value: object, maximum: int, minimum: int = 1) -> list:
    require(type(value) is list and minimum <= len(value) <= maximum, "ITEM_COUNT")
    return value


def decode(raw: bytes) -> dict:
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, "JSON_SIZE")

    def pairs(rows):
        require(len(dict(rows)) == len(rows), "DUPLICATE_KEY")
        return dict(rows)

    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=pairs)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SourceError("JSON_DECODE") from exc
    stack, count = [(value, 0)], 0
    while stack:
        child, depth = stack.pop()
        count += 1
        require(count <= 250000 and depth <= 32, "JSON_RESOURCE_BOUND")
        require(type(child) in (dict, list, str, int, bool), "JSON_TYPE")
        if isinstance(child, str):
            require(all(32 <= ord(c) <= 126 for c in child), "JSON_ASCII")
        if type(child) is dict:
            stack.extend((x, depth + 1) for pair in child.items() for x in pair)
        if type(child) is list:
            stack.extend((x, depth + 1) for x in child)
    require(type(value) is dict and canonical(value) == raw, "NONCANONICAL_JSON")
    return value


class Resolver:
    """Content resolution only. A matching digest does not establish provenance."""

    def __init__(self, store: Mapping[str, bytes]):
        self.store = store
        self.sources: dict[str, dict] = {}
        self.total = 0

    def raw(self, identifier: str, kind: str) -> bytes:
        cid(identifier)
        require(identifier in self.store, "MISSING_PREIMAGE:" + identifier)
        raw = self.store[identifier]
        require(type(raw) is bytes and len(raw) <= MAX_JSON, "SOURCE_SIZE")
        require(content_id(raw, DOMAINS[kind]) == identifier, "SOURCE_HASH")
        if identifier not in self.sources:
            self.total += len(raw)
            require(self.total <= MAX_TOTAL, "SOURCE_TOTAL_LIMIT")
            self.sources[identifier] = {"id": identifier, "kind": kind, "bytes_hex": raw.hex()}
        require(self.sources[identifier]["kind"] == kind, "SOURCE_KIND")
        return raw

    def document(self, identifier: str, kind: str) -> dict:
        value = decode(self.raw(identifier, kind))
        require(value.get("schema_version") == "1.0.0", "SOURCE_VERSION")
        if kind != "schema":
            require(value.get("type_name") == TYPES[kind], "SOURCE_TYPE")
            require(value.get("formal_semantics_id") == SEMANTICS, "SOURCE_SEMANTICS")
        return value


def schema_segments(schema: dict) -> list[dict]:
    shape(schema, "frozen_omission_policy parameters schema_version tied_aliases")
    require(schema["frozen_omission_policy"] in ("INCLUDE_ALL", "OMIT_FROZEN"), "OMISSION")
    names, segments, cursor = [], [], 0
    for p in items(schema["parameters"], 65536):
        shape(p, "logical_dtype name shape trainable")
        name = p["name"]
        require(
            isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,255}", name),
            "PARAMETER_NAME",
        )
        names.append(name)
        require(type(p["trainable"]) is bool, "TRAINABLE")
        require(p["logical_dtype"] in ("bfloat16", "float16", "float32", "float64"), "DTYPE")
        count = 1
        for size in items(p["shape"], 32, 0):
            count *= uint(size, MAX_ELEMENTS, 1)
            require(count <= MAX_ELEMENTS, "SHAPE_BOUND")
        if p["trainable"] or schema["frozen_omission_policy"] == "INCLUDE_ALL":
            # ParameterSchema permits256 characters; the original004 native
            # segment/header contract permits at most255. Check that boundary.
            token(name)
            segments.append(
                {
                    "segment_id": name,
                    "element_start": cursor,
                    "element_count": count,
                    "segment_ordinal": len(segments),
                }
            )
            cursor += count
            require(cursor <= MAX_ELEMENTS, "TOTAL_ELEMENTS")
    require(names == sorted(set(names)), "PARAMETER_ORDER")
    aliases = schema["tied_aliases"]
    require(type(aliases) is dict, "ALIASES")
    for alias, owner in aliases.items():
        require(
            re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,255}", alias)
            and alias not in names
            and owner in names,
            "ALIAS_OWNER",
        )
    require(bool(segments), "EMPTY_INCLUDED_SCHEMA")
    return segments


def read_drq1(raw: bytes) -> tuple[dict, tuple[int, ...]]:
    require(type(raw) is bytes and 16 <= len(raw) <= 16 + MAX_HEADER + MAX_PAYLOAD, "ENVELOPE_SIZE")
    magic, major, minor, hsize, psize = struct.unpack("<4sHHII", raw[:16])
    require((magic, major, minor) == (b"DRQ1", 1, 0), "ENVELOPE_VERSION")
    require(0 < hsize <= MAX_HEADER and 0 < psize <= MAX_PAYLOAD and psize % 2 == 0, "LENGTHS")
    require(len(raw) == 16 + hsize + psize, "TRUNCATED_OR_TRAILING")
    header = decode(raw[16 : 16 + hsize])
    payload = raw[16 + hsize :]
    require(header.get("payload_sha256") == content_id(payload), "PAYLOAD_HASH")
    values = tuple(x[0] for x in struct.iter_unpack("<h", payload))
    require(all(-32767 <= x <= 32767 for x in values), "Q_RANGE")
    return header, values


def merkle_root(leaves: list[str]) -> str:
    require(bool(leaves), "EMPTY_MERKLE")
    nodes = [bytes.fromhex(cid(x)[7:]) for x in leaves]
    while len(nodes) > 1:
        if len(nodes) % 2:
            nodes.append(nodes[-1])
        nodes = [
            bytes.fromhex(content_id(nodes[i] + nodes[i + 1], "deltareduce.004.merkle-node.v1")[7:])
            for i in range(0, len(nodes), 2)
        ]
    return "sha256:" + nodes[0].hex()


@dataclass(frozen=True)
class QSource:
    manifest_id: str
    manifest: dict
    schema: dict
    proof: dict
    rows: tuple[dict, ...]
    sources: tuple[dict, ...]


def resolve_q_source(store: Mapping[str, bytes], manifest_id: str) -> QSource:
    """Derive all expected headers from complete resolved source records.

    Proof theorem metadata is retained, not authenticated or accepted as proof.
    Base RoundConfig, parent checkpoint and certificate authority remain external.
    """
    r = Resolver(store)
    m = r.document(manifest_id, "manifest")
    shape(
        m,
        "aggregation_steps commitment_root domain_id formal_semantics_id parameter_schema_id "
        "parent_checkpoint_id profile_id proof_instance_id round_config_id scale_table_id "
        "schema_version shard_plan_id shards ticket_id total_elements total_envelope_bytes "
        "total_payload_bytes type_name",
    )
    token(m["ticket_id"])
    token(m["domain_id"])
    cid(m["parent_checkpoint_id"])
    uint(m["aggregation_steps"], (1 << 32) - 1, 1)
    require(m["profile_id"] == PROFILE, "FIXED_PROFILE")
    r.document(m["profile_id"], "profile")
    schema = r.document(m["parameter_schema_id"], "schema")
    segments = schema_segments(schema)
    scale = r.document(m["scale_table_id"], "scale")
    plan = r.document(m["shard_plan_id"], "plan")
    config = r.document(m["round_config_id"], "config")
    proof = r.document(m["proof_instance_id"], "proof")
    shape(
        scale,
        "formal_semantics_id parameter_schema_id profile_id schema_version segments "
        "total_elements type_name",
    )
    shape(
        plan,
        "entries formal_semantics_id parameter_schema_id profile_id scale_table_id "
        "schema_version target_payload_bytes total_elements type_name",
    )
    shape(
        config,
        "accumulator_width_bits base_round_config_id coefficient_abs_max formal_semantics_id "
        "max_eligible_contributions parameter_schema_id profile_id q_abs_max scale_table_id "
        "schema_version shard_plan_id type_name",
    )
    shape(
        proof,
        "coefficient_abs_max common_denominator config_id final_abs_bound formal_semantics_id "
        "lean_artifact_sha256 max_eligible_contributions max_incremental_prefix_abs "
        "product_abs_bound "
        "product_width_bits profile_id q_abs_max result scale_table_id schema_version "
        "selected_accumulator_width_bits theorems type_name",
    )
    for doc in (scale, plan, config):
        for key in ("parameter_schema_id", "profile_id"):
            require(doc.get(key) == m[key], "SOURCE_CONTEXT:" + key)
    for doc in (plan, config, proof):
        require(doc.get("scale_table_id") == m["scale_table_id"], "SCALE_LINK")
    require(config.get("shard_plan_id") == m["shard_plan_id"], "PLAN_LINK")
    require(
        proof.get("config_id") == m["round_config_id"] and proof.get("profile_id") == PROFILE,
        "PROOF_LINK",
    )
    # Deliberately do not derive authority from these metadata strings.
    cid(config["base_round_config_id"])
    require(
        config.get("accumulator_width_bits") in (64, 128)
        and type(config.get("accumulator_width_bits")) is int,
        "WIDTH",
    )
    require(
        proof.get("selected_accumulator_width_bits") == config["accumulator_width_bits"]
        and type(proof.get("selected_accumulator_width_bits")) is int,
        "PROOF_WIDTH",
    )
    for key in ("coefficient_abs_max", "max_eligible_contributions", "q_abs_max"):
        decimal(config.get(key), (1 << 64) - 1, 1)
        require(proof.get(key) == config[key], "PROOF_INPUT_LINK")
    decimal(proof.get("common_denominator"), (1 << 64) - 1, 1)
    require(config["q_abs_max"] == "32767", "Q_BOUND")
    scale_rows = items(scale.get("segments"), 65536)
    require(len(scale_rows) == len(segments), "SCALE_COVERAGE")
    quanta = {}
    for expected, row in zip(segments, scale_rows, strict=True):
        shape(row, "segment_id segment_ordinal element_start element_count quantum")
        require(canonical({k: row[k] for k in expected}) == canonical(expected), "SCALE_SEGMENT")
        q = shape(row["quantum"], "numerator denominator")
        a, b = decimal(q["numerator"], (1 << 32) - 1, 1), uint(q["denominator"], (1 << 32) - 1, 1)
        require(math.gcd(a, b) == 1, "SCALE_NOT_REDUCED")
        quanta[row["segment_id"]] = (a, b)
    target = uint(plan.get("target_payload_bytes"), MAX_PAYLOAD, 2)
    require(target % 2 == 0, "PLAN_TARGET")
    entries = []
    for segment in segments:
        offset = 0
        while offset < segment["element_count"]:
            require(len(entries) < 4096, "SHARD_COUNT")
            count = min(target // 2, segment["element_count"] - offset)
            entries.append(
                {
                    "ordinal": len(entries),
                    "segment_id": segment["segment_id"],
                    "segment_offset": offset,
                    "element_start": segment["element_start"] + offset,
                    "element_count": count,
                    "payload_bytes": count * 2,
                }
            )
            offset += count
    require(canonical(plan.get("entries")) == canonical(entries), "PLAN_PARTITION")
    total = sum(s["element_count"] for s in segments)
    require(
        all(
            type(d.get("total_elements")) is int and d["total_elements"] == total
            for d in (m, scale, plan)
        ),
        "ELEMENT_TOTAL",
    )
    refs = items(m["shards"], 4096)
    require(len(refs) == len(entries), "LEAF_COVERAGE")
    rows, leaves, envelope_total = [], [], 0
    links = {
        key: m[key]
        for key in (
            "formal_semantics_id",
            "parameter_schema_id",
            "profile_id",
            "proof_instance_id",
            "round_config_id",
            "scale_table_id",
            "shard_plan_id",
            "ticket_id",
        )
    }
    for entry, ref in zip(entries, refs, strict=True):
        shape(
            ref,
            "ordinal segment_id segment_offset element_start element_count payload_bytes "
            "envelope_bytes leaf_id",
        )
        require(canonical({k: ref[k] for k in entry}) == canonical(entry), "MANIFEST_RANGE")
        raw = r.raw(ref["leaf_id"], "leaf")
        require(
            type(ref["envelope_bytes"]) is int and len(raw) == ref["envelope_bytes"], "LEAF_LENGTH"
        )
        header, values = read_drq1(raw)
        expected = {
            **links,
            **{k: v for k, v in entry.items() if k != "payload_bytes"},
            "payload_sha256": content_id(raw[-entry["payload_bytes"] :]),
            "schema_version": "1.0.0",
            "type_name": "ENCODED_INT16_SHARD",
        }
        require(canonical(header) == canonical(expected), "HEADER_CONTEXT")
        require(len(values) == entry["element_count"], "Q_COUNT")
        rows.append(
            {
                **entry,
                "leaf_id": ref["leaf_id"],
                "quantum": list(quanta[entry["segment_id"]]),
                "values": list(values),
            }
        )
        leaves.append(ref["leaf_id"])
        envelope_total += len(raw)
    require(len(set(leaves)) == len(leaves), "DUPLICATE_LEAF")
    require(m["commitment_root"] == merkle_root(leaves), "MERKLE_ROOT")
    require(
        type(m["total_payload_bytes"]) is int
        and m["total_payload_bytes"] == total * 2
        and type(m["total_envelope_bytes"]) is int
        and m["total_envelope_bytes"] == envelope_total,
        "BYTE_TOTALS",
    )
    return QSource(manifest_id, m, schema, proof, tuple(rows), tuple(r.sources.values()))
