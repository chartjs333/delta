"""Original norm/seed bytes referencing b, with all original C witnesses retained."""

import json
from hashlib import sha256

from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source.input_section_vectors import generate as inputs
from formal.reference.profile_source.isc_vectors import bs
from formal.reference.profile_source.native_header_vectors import policy_term
from formal.reference.profile_source.policy_vectors import projected


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "ascii"
    )


def generate():
    original_source, originals = inputs()
    body = synthetic_body()
    common = {
        "arithmetic_profile_id": body.arithmetic_profile_id,
        "formal_semantics_id": body.formal_semantics_id,
        "height": body.height,
        "input_set_certificate_id": originals["b"],
        "parameter_schema_id": body.parameter_schema_id,
        "round_config_id": body.round_config_id,
        "round_id": body.round_id,
        "schema_version": "2.0.0",
        "validator_epoch_id": body.validator_epoch_id,
        "view": body.view,
    }
    norm = {
        **common,
        "entries": [{"scale_denominator": 1, "squared_norm": "7", "ticket_id": "ticket-001"}],
        "norm_root": "sha256:" + "8" * 64,
        "type_name": "NORM_EVIDENCE",
    }
    seed = {
        **common,
        "seed_id": "sha256:" + "9" * 64,
        "seed_profile_id": "sha256:" + "a" * 64,
        "share_ids": ["sha256:" + digit * 64 for digit in ("b", "c", "d")],
        "type_name": "SEED_TRANSCRIPT",
    }
    norm_raw, seed_raw = canonical(norm), canonical(seed)
    p = policy.decode(bytes.fromhex(originals["whole_policy"]))
    ctx = p["snapshot"]["input_set_bodies"][0]["context"]
    p["snapshot"]["norm_evidence"] = [
        {
            "context": ctx,
            "entries": norm["entries"],
            "input_set_certificate_id": originals["b"],
            "norm_root": norm["norm_root"],
        }
    ]
    p["snapshot"]["seed_transcripts"] = [
        {
            "context": ctx,
            "input_set_certificate_id": originals["b"],
            "seed_id": seed["seed_id"],
            "seed_profile_id": seed["seed_profile_id"],
            "share_ids": seed["share_ids"],
        }
    ]
    tables = {}
    for domain, raw in (
        ("deltareduce.008.norm-evidence.v1", norm_raw),
        ("deltareduce.008.seed-transcript.v1", seed_raw),
    ):
        preimage = domain.encode("ascii") + b"\0" + raw
        tables[preimage] = sha256(preimage).digest()
    lines = [
        original_source.replace("import ProfileInputSection", "import ProfileLineage"),
        "namespace LineageVectors",
        "open InputSectionVectors DeltaReduce.ProfileSource.Lineage",
        f"def tree : DeltaReduce.NativePolicyCodec.Value := {policy_term('policy', p)}",
        f"def p : DeltaReduce.NativePolicyBytes.Policy := {projected(p)}",
        f"def normRaw : Bytes := {bs(norm_raw)}",
        f"def seedRaw : Bytes := {bs(seed_raw)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in tables.items()),
        "  InputSectionVectors.hash raw",
        "def result := bindSection hash sigma body.context body.parent p [bodyRaw] raws",
        "  [normRaw] [seedRaw]",
        "example : result.map (fun r => r.norms.map (fun n => n.value.evidence.isc)) =",
        "  some [b] := by decide +kernel",
        "example : result.map (fun r => r.seeds.map (fun s => s.value.transcript.isc)) =",
        "  some [b] := by decide +kernel",
        "example : result.map (fun r => WitnessIds r.inputs) = some witnesses := by decide +kernel",
        "example : (bindSection hash sigma body.context body.parent p [bodyRaw] raws",
        "  [] [seedRaw]).isNone = true := by decide +kernel",
        "example : (bindSection hash sigma body.context body.parent p [bodyRaw] raws",
        "  [normRaw] []).isNone = true := by decide +kernel",
        "example : (bindSection hash sigma body.context body.parent wrongIndex [bodyRaw] raws",
        "  [normRaw] [seedRaw]).isNone = true := by decide +kernel",
        "def originalNormTree : DeltaReduce.NativePolicyCodec.Value := "
        + policy_term("norm", p["snapshot"]["norm_evidence"][0]),
        "def originalSeedTree : DeltaReduce.NativePolicyCodec.Value := "
        + policy_term("seed", p["snapshot"]["seed_transcripts"][0]),
        "example : (bindNorm hash sigma body.context [b] originalNormTree",
        f"  {bs(canonical({**norm, 'schema_version': '1.0.0'}))}).isNone = true "
        ":= by decide +kernel",
        "example : (bindSeed hash sigma body.context [b] originalSeedTree",
        f"  {bs(canonical({**seed, 'schema_version': '1.0.0'}))}).isNone = true "
        ":= by decide +kernel",
        "end LineageVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_BYTE_LINEAGE_NOT_NATIVE_PRODUCER_OR_SEED_RELEASE",
        "input_collections": originals,
        "whole_policy": policy.encode(p).hex(),
        "approved_schema_version": "2.0.0",
        "negative_schema1_norm": canonical({**norm, "schema_version": "1.0.0"}).hex(),
        "negative_schema1_seed": canonical({**seed, "schema_version": "1.0.0"}).hex(),
        "norm": norm_raw.hex(),
        "seed": seed_raw.hex(),
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in tables.items()},
        "not_established": (
            "norm computation, seed randomness/authority or durable producer history"
        ),
    }
