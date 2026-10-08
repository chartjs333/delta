"""Original 004 metadata -> S/O context, without requiring physical Q presence.

Feature003 §3/US2 gives Commitment.commitment_id its Merkle-root meaning;
feature004 FR008-014 fixes the manifest/plan/leaf identities. The source-prefix
checker must still establish actual ticket issuance and commitment admission.
This module resolves their complete byte inputs, never a public-state premise.
Actual Q bytes are required separately at data use, not at AC authentication.
"""

import copy
import json
import math
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from formal.reference.isc_crypto.codec import CodecError, _id, _pairs, _require
from formal.reference.profile_source import configuration as cfg
from formal.reference.storage_source import codec as storage
from formal.scripts import native_source_artifacts as source

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = {
    "profile": "fixed-point-profile-v1.json",
    "scale": "scale-table-v1.json",
    "plan": "shard-plan-v1.json",
    "config": "fixedpoint-config-v1.json",
    "proof": "accumulator-proof-instance-v1.json",
    "manifest": "encoded-contribution-manifest-v1.json",
}


def _bad_number(_):
    raise CodecError("004 integers only")


def decode(raw):
    # No proposal-only 8 MiB source-total cap, no imported verifier/semantics ID.
    # The enclosing profile bounds the complete referenced source inventory.
    _require(type(raw) is bytes, "original 004 bytes")
    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_pairs,
            parse_float=_bad_number,
            parse_constant=_bad_number,
        )
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise CodecError("004 JSON decode") from exc
    _require(type(value) is dict and source.canonical(value) == raw, "004 canonical bytes")
    return value


def validate_schema(kind, obj, semantics):
    # Trusted local verifier source, never a URI supplied by the import. This
    # isolated successor reference parameterizes only the existing semantics
    # constant; it does not mutate legacy schemas/objects or choose sigma_next.
    schema = json.loads((ROOT / "delta-protocol/schemas/004" / SCHEMAS[kind]).read_text())
    schema = copy.deepcopy(schema)
    if kind == "profile":
        schema["properties"]["formal_semantics_id"] = {"const": semantics}
    _require(Draft202012Validator(schema).is_valid(obj), "original 004 schema: " + kind)
    _require(obj["formal_semantics_id"] == semantics, "independently selected semantics")


class Resolver:
    def __init__(self, originals, semantics):
        self.originals, self.semantics = originals, semantics
        self.used = []

    def document(self, identifier, kind):
        _id(identifier)
        _require(identifier in self.originals, "missing original " + kind)
        raw = self.originals[identifier]
        _require(type(raw) is bytes, "immutable original " + kind)
        _require(
            source.content_id(raw, source.DOMAINS[kind]) == identifier,
            "original domain-separated " + kind + " identity",
        )
        obj = decode(raw)
        if kind != "schema":
            validate_schema(kind, obj, self.semantics)
        self.used.append((kind, identifier, raw))
        return obj


@dataclass(frozen=True)
class Metadata:
    original_manifest: bytes
    manifest_id: str
    commitment_id: str
    ticket_id: str
    domain_id: str
    parent_id: str
    schema_id: str
    profile_id: str
    fixed_config_id: str
    base_config_id: str
    steps: int
    # Original ordered leaf IDs/full lengths, not present/observed subsets.
    required_leaves: tuple[tuple[str, int], ...]
    original_sources: tuple[tuple[str, str, bytes], ...]


def resolve(originals, semantics, manifest_id):
    """All metadata preimages and associations, including aliases and units.

    Arithmetic proof metadata is retained, not treated as a proof or authority.
    The existing R2.2 arithmetic checker must establish its concrete bounds.
    """
    _id(semantics)
    r = Resolver(originals, semantics)
    m = r.document(manifest_id, "manifest")
    r.document(m["profile_id"], "profile")
    schema = r.document(m["parameter_schema_id"], "schema")
    segments = source.schema_segments(schema)
    scale = r.document(m["scale_table_id"], "scale")
    plan = r.document(m["shard_plan_id"], "plan")
    config = r.document(m["round_config_id"], "config")
    proof = r.document(m["proof_instance_id"], "proof")
    for obj in (scale, plan, config):
        for field in ("parameter_schema_id", "profile_id"):
            _require(obj[field] == m[field], "original common " + field)
    for obj in (plan, config, proof):
        _require(obj["scale_table_id"] == m["scale_table_id"], "complete scale link")
    _require(config["shard_plan_id"] == m["shard_plan_id"], "complete plan link")
    _require(
        proof["config_id"] == m["round_config_id"] and proof["profile_id"] == m["profile_id"],
        "original proof metadata context",
    )
    _require(
        proof["selected_accumulator_width_bits"] == config["accumulator_width_bits"],
        "proof metadata width association",
    )
    for field in ("coefficient_abs_max", "max_eligible_contributions", "q_abs_max"):
        source.decimal(config[field], 2**64 - 1, 1)
        _require(proof[field] == config[field], "original proof metadata input")
    source.decimal(proof["common_denominator"], 2**64 - 1, 1)
    _require(len(scale["segments"]) == len(segments), "full scale coverage")
    for expected, row in zip(segments, scale["segments"], strict=True):
        _require({k: row[k] for k in expected} == expected, "schema/scale segment")
        q = row["quantum"]
        numerator = source.decimal(q["numerator"], 2**32 - 1, 1)
        denominator = source.uint(q["denominator"], 2**32 - 1, 1)
        _require(math.gcd(numerator, denominator) == 1, "original reduced scale")
    target = plan["target_payload_bytes"]
    _require(target % 2 == 0, "int16 plan target")
    entries = []
    for segment in segments:
        offset = 0
        while offset < segment["element_count"]:
            _require(len(entries) < 4096, "existing 004 shard bound")
            count = min(target // 2, segment["element_count"] - offset)
            entries.append(
                {
                    "ordinal": len(entries),
                    "segment_id": segment["segment_id"],
                    "segment_offset": offset,
                    "element_start": segment["element_start"] + offset,
                    "element_count": count,
                    "payload_bytes": 2 * count,
                }
            )
            offset += count
    _require(plan["entries"] == entries, "complete ordered original partition")
    total = sum(segment["element_count"] for segment in segments)
    _require(all(obj["total_elements"] == total for obj in (m, scale, plan)), "full total")
    _require(len(m["shards"]) == len(entries), "full committed leaf inventory")
    leaves = []
    for entry, ref in zip(entries, m["shards"], strict=True):
        _require({k: ref[k] for k in entry} == entry, "original manifest ordinal/range")
        # DRQ1 has a 16-byte prefix, a nonempty bounded JSON header and payload.
        # Header contents/actual lengths/hash are checked at first data use.
        _require(
            16 + entry["payload_bytes"]
            < ref["envelope_bytes"]
            <= 16 + 65536 + entry["payload_bytes"],
            "original full envelope declaration",
        )
        leaves.append((ref["leaf_id"], ref["envelope_bytes"]))
    _require(len({leaf for leaf, _ in leaves}) == len(leaves), "no duplicate original leaf")
    _require(
        source.merkle_root([leaf for leaf, _ in leaves]) == m["commitment_root"],
        "original ordered commitment root (not manifest ID)",
    )
    _require(
        m["total_payload_bytes"] == 2 * total
        and m["total_envelope_bytes"] == sum(length for _, length in leaves),
        "complete manifest byte totals",
    )
    return Metadata(
        originals[manifest_id],
        manifest_id,
        m["commitment_root"],
        m["ticket_id"],
        m["domain_id"],
        m["parent_checkpoint_id"],
        m["parameter_schema_id"],
        m["profile_id"],
        m["round_config_id"],
        config["base_round_config_id"],
        m["aggregation_steps"],
        tuple(leaves),
        tuple(r.used),
    )


def bind_context(
    validators,
    storage_bootstrap,
    original_config,
    declaration,
    originals,
    manifest_id,
    original_commitment,
):
    """Derive S context from config + original manifest/root, never caller fields.

    No claim of config finality, ticket issuance, or commitment event legality;
    those are prefix obligations, not assumptions that R2 succeeds.
    """
    configuration = cfg.bind(validators, storage_bootstrap, original_config, declaration)
    body = cfg.decode(original_config)
    m = resolve(originals, validators.formal_semantics_id, manifest_id)
    _require(
        m.base_config_id == configuration.body_id
        and m.parent_id == configuration.parent
        and m.schema_id == body["parameter_schema_id"],
        "enclosing RoundConfig / fixedpoint config / manifest join",
    )
    _require(m.steps == body["step_budget"], "completed original fixed local steps")
    _require(
        m.domain_id in {row["domain_id"] for row in body["domain_ticket_counts"]},
        "original configured domain",
    )
    _require(
        original_commitment.ticket_id == m.ticket_id
        and original_commitment.commitment_id == m.commitment_id,
        "original native ticket/commitment root",
    )
    binding = configuration.storage_binding
    value = storage.Context(
        storage.canonical(
            {
                "schema_version": "1.0.0",
                "formal_semantics_id": validators.formal_semantics_id,
                "origin_id": validators.origin_id,
                "height": str(configuration.height),
                "round_id": configuration.round_id,
                "round_config_id": configuration.body_id,
                "parent_checkpoint_id": m.parent_id,
                "ticket_id": m.ticket_id,
                "commitment_id": m.commitment_id,
                "storage_epoch_id": binding.storage_epoch_id,
                "storage_registry_id": binding.storage_registry_id,
                "retention_epoch_id": binding.source.retention_epoch_id,
            }
        ),
        binding.threshold,
        m.required_leaves,
    )
    storage.context(storage_bootstrap, value)
    return m, value


@dataclass(frozen=True)
class DataUse:
    metadata: Metadata
    ordinal: int
    original_envelope: bytes
    values: tuple[int, ...]


def read_q(originals, semantics, manifest_id, ordinal, original_envelope):
    """An exact current read/retained immutable buffer, not an AC availability claim.

    Call at a real first data-use event; previous successful reads do not authorize
    a different present buffer. The outer producer distinguishes durable retry.
    """
    m = resolve(originals, semantics, manifest_id)
    _require(type(ordinal) is int and 0 <= ordinal < len(m.required_leaves), "original ordinal")
    leaf, length = m.required_leaves[ordinal]
    _require(type(original_envelope) is bytes, "actual original Q bytes required at use")
    _require(len(original_envelope) == length, "exact full envelope length at use")
    _require(
        source.content_id(original_envelope, source.DOMAINS["leaf"]) == leaf,
        "original committed leaf bytes at use",
    )
    manifest = decode(m.original_manifest)
    row = manifest["shards"][ordinal]
    header, values = source.read_drq1(original_envelope)
    expected = {
        key: manifest[key]
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
    expected.update(
        {
            key: row[key]
            for key in (
                "ordinal",
                "segment_id",
                "segment_offset",
                "element_start",
                "element_count",
            )
        }
    )
    expected.update(
        schema_version="1.0.0",
        type_name="ENCODED_INT16_SHARD",
        payload_sha256=source.content_id(original_envelope[-row["payload_bytes"] :]),
    )
    _require(header == expected and len(values) == row["element_count"], "exact Q source context")
    return DataUse(m, ordinal, original_envelope, values)
