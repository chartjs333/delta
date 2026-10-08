"""One whole four-coordinate source shard; no coordinate protocol identities."""

import json
from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source.eligibility_vectors import text64, u64
from formal.reference.profile_source.isc_vectors import bs
from formal.reference.profile_source.lineage_vectors import canonical
from formal.reference.profile_source.plan_vectors import generate as plan
from formal.reference.profile_source.policy_vectors import projected


def texts(items):
    return u64(len(items)) + b"".join(text64(x) for x in items)


def parameter_bytes(ctx, item):
    raw = text64(ctx["arithmetic_profile_id"]) + u64(ctx["height"])
    raw += text64(ctx["parameter_schema_id"]) + text64(ctx["round_config_id"])
    raw += text64(ctx["round_id"]) + text64(ctx["validator_epoch_id"]) + u64(ctx["view"])
    return (
        raw
        + text64(item["aggregation_plan_certificate_id"])
        + u64(item["denominator"])
        + text64(item["domain_id"])
        + text64(item["eligibility_certificate_id"])
        + texts(item["input_leaf_ids"])
        + text64(item["input_set_certificate_id"])
        + texts(item["result_numerators"])
        + text64(item["shard_id"])
    )


def generate():
    _, originals = plan()
    p = policy.decode(bytes.fromhex(originals["whole_policy"]))
    ctx = p["snapshot"]["input_set_bodies"][0]["context"]
    apc = p["snapshot"]["aggregation_plan_certificates"][0]
    common = {
        "context": ctx,
        "aggregation_plan_certificate_id": originals["certificate_id"],
        "denominator": 7,
        "domain_id": "code",
        "eligibility_certificate_id": apc["eligibility_certificate_id"],
        "input_leaf_ids": ["sha256:" + "1" * 64],
        "input_set_certificate_id": apc["input_set_certificate_id"],
        "result_numerators": ["1", "-2", "3", "0"],
        "shard_id": "original-shard-0",
    }
    body = {**common, "vote_context_id": "sha256:" + "2" * 64}
    cert = {**common, "quorum_threshold": 3, "signer_ids": ["a", "b", "c"]}
    cert_raw = canonical(
        {
            **ctx,
            **{k: v for k, v in cert.items() if k != "context"},
            "formal_semantics_id": synthetic_body().formal_semantics_id,
            "type_name": "PARAMETER_SHARD_QC",
            "schema_version": "2.0.0",
        }
    )
    body_raw = parameter_bytes(ctx, common)
    table = {}

    def identifier(domain, raw):
        preimage = domain.encode("ascii") + b"\0" + raw
        digest = sha256(preimage).digest()
        table[preimage] = digest
        return "sha256:" + digest.hex()

    bid = identifier("deltareduce.vote.parameter-body.v1", body_raw)
    cid = identifier("deltareduce.008.parameter-shard-qc.v1", cert_raw)
    # The existing native size gate also serializes proposed bodies with the
    # whole committee. These are size-check views, never new QC witnesses.
    for domain, raw in (
        (
            "deltareduce.008.eligibility-certificate.v1",
            bytes.fromhex(originals["prior"]["certificate"]),
        ),
        (
            "deltareduce.008.aggregation-plan-certificate.v1",
            bytes.fromhex(originals["certificate"]),
        ),
        ("deltareduce.008.parameter-shard-qc.v1", cert_raw),
    ):
        view = json.loads(raw)
        view["signer_ids"] = p["validator_ids"]
        identifier(domain, canonical(view))
    p["snapshot"].update(
        parameter_bodies=[body],
        parameter_qcs=[cert],
        finalized_parameter_ids=[cid],
        required_parameter_keys=[{"domain_id": "code", "shard_id": "original-shard-0"}],
    )
    wrong = deepcopy(p)
    wrong["snapshot"]["required_parameter_keys"] = []
    lines = [
        "import ProfileParameter\nimport PlanVectors",
        "open DeltaReduce.ISCSourceV2 DeltaReduce.NativeReceiptBytes",
        "open DeltaReduce.ProfileSource.InputSection",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace ParameterVectors",
        "open InputSectionVectors DeltaReduce.ProfileSource",
        f"def p : DeltaReduce.NativePolicyBytes.Policy := {projected(p)}",
        f"def wrong : DeltaReduce.NativePolicyBytes.Policy := {projected(wrong)}",
        f"def bodyRawP : Bytes := {bs(body_raw)}",
        f"def certRawP : Bytes := {bs(cert_raw)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(r)} then {bs(d)} else" for r, d in table.items()),
        "  PlanVectors.hash raw",
        "def run (p : DeltaReduce.NativePolicyBytes.Policy) (certs : List Bytes) := do",
        "  let ec ← Eligibility.bindSection hash sigma body.context body.parent p [bodyRaw] raws",
        "    [LineageVectors.normRaw] [LineageVectors.seedRaw]",
        "    [EligibilityVectors.bodyRawEC] [EligibilityVectors.certRawEC]",
        "  let apc ← Plan.bindCollections hash sigma body.context p ec",
        "    [PlanVectors.bodyRawAPC] [PlanVectors.certRawAPC]",
        "  Parameter.bindCollections hash sigma body.context p ec apc [bodyRawP] certs",
        "example : (run p [certRawP]).map (fun x => x.certificates.map",
        "  (fun e => e.value.certificate.common.numerators)) =",
        f"  some [[{','.join(bs(x) for x in common['result_numerators'])}]] := by decide +kernel",
        "example : (run p [certRawP]).map (fun x => x.finalized) =",
        f"  some [{bs(cid)}] := by decide +kernel",
        "example : (run p [certRawP]).map (fun x => (x.bodies.length,x.certificates.length))",
        "  = some (1,1) := by decide +kernel",
        "example : (run p []).isNone = true := by decide +kernel",
        "example : (run wrong [certRawP]).isNone = true := by decide +kernel",
        "end ParameterVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_WHOLE_VECTOR_BYTES_NOT_COMPUTATION_OR_PRODUCER",
        "prior": originals,
        "whole_policy": policy.encode(p).hex(),
        "body": body_raw.hex(),
        "certificate": cert_raw.hex(),
        "body_id": bid,
        "certificate_id": cid,
        "whole_numerators": common["result_numerators"],
        "missing_key_policy": policy.encode(wrong).hex(),
        "sha256_preimages": {r.hex(): d.hex() for r, d in table.items()},
    }
