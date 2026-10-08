"""Whole ROOT joins the original unsplit vector QC and all native size rows."""

from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source.eligibility_vectors import text64, u64
from formal.reference.profile_source.isc_vectors import bs
from formal.reference.profile_source.lineage_vectors import canonical
from formal.reference.profile_source.parameter_vectors import generate as parameter
from formal.reference.profile_source.policy_vectors import projected


def root_bytes(ctx, c):
    raw = text64(ctx["arithmetic_profile_id"]) + u64(ctx["height"])
    raw += text64(ctx["parameter_schema_id"]) + text64(ctx["round_config_id"])
    raw += text64(ctx["round_id"]) + text64(ctx["validator_epoch_id"]) + u64(ctx["view"])
    raw += text64(c["aggregation_plan_certificate_id"])
    raw += text64(c["eligibility_certificate_id"]) + text64(c["input_set_certificate_id"])
    raw += u64(len(c["leaves"]))
    for leaf in c["leaves"]:
        raw += (
            text64(leaf["domain_id"])
            + text64(leaf["parameter_shard_qc_id"])
            + text64(leaf["shard_id"])
        )
    raw += text64(c["merkle_root"]) + u64(len(c["required_keys"]))
    for key in c["required_keys"]:
        raw += text64(key["domain_id"]) + text64(key["shard_id"])
    return raw


def generate(body=None):
    body = synthetic_body() if body is None else body
    _, originals = parameter(body)
    p = policy.decode(bytes.fromhex(originals["whole_policy"]))
    ctx = p["snapshot"]["input_set_bodies"][0]["context"]
    shard = p["snapshot"]["parameter_qcs"][0]
    table = {}

    def identifier(domain, raw):
        preimage = domain.encode("ascii") + b"\0" + raw
        digest = sha256(preimage).digest()
        table[preimage] = digest
        return "sha256:" + digest.hex()

    leaf = {
        "domain_id": shard["domain_id"],
        "parameter_shard_qc_id": originals["certificate_id"],
        "shard_id": shard["shard_id"],
    }
    # One original whole shard has one leaf; none of its four coordinates
    # receives a new shard/vote/QC identity.
    root = identifier("deltareduce.008.aggregate-leaf.v1", canonical(leaf))
    common = {
        "context": ctx,
        "aggregation_plan_certificate_id": shard["aggregation_plan_certificate_id"],
        "eligibility_certificate_id": shard["eligibility_certificate_id"],
        "input_set_certificate_id": shard["input_set_certificate_id"],
        "leaves": [leaf],
        "merkle_root": root,
        "required_keys": p["snapshot"]["required_parameter_keys"],
    }
    cert = {**common, "quorum_threshold": 3, "signer_ids": ["a", "b", "c"]}

    def json_cert(c):
        return canonical(
            {
                **ctx,
                **{k: v for k, v in c.items() if k != "context"},
                "formal_semantics_id": body.formal_semantics_id,
                "schema_version": "2.0.0",
                "type_name": "AGGREGATE_ROOT_QC",
            }
        )

    body_raw, cert_raw = root_bytes(ctx, common), json_cert(cert)
    bid = identifier("deltareduce.vote.aggregate-root-body.v1", body_raw)
    cid = identifier("deltareduce.008.aggregate-root-qc.v1", cert_raw)
    identifier(
        "deltareduce.008.aggregate-root-qc.v1",
        json_cert({**cert, "signer_ids": p["validator_ids"]}),
    )
    p["snapshot"].update(
        aggregate_root_bodies=[common],
        aggregate_root_qcs=[cert],
        finalized_aggregate_root_ids=[cid],
    )
    wrong = deepcopy(p)
    wrong_cert = wrong["snapshot"]["aggregate_root_qcs"][0]
    wrong_cert["merkle_root"] = "sha256:" + "0" * 64
    wrong_raw = json_cert(wrong_cert)
    wrong["snapshot"]["finalized_aggregate_root_ids"] = [
        identifier("deltareduce.008.aggregate-root-qc.v1", wrong_raw)
    ]
    lines = [
        "import ProfileAggregate\nimport ParameterVectors",
        "open DeltaReduce.ISCSourceV2 DeltaReduce.NativeReceiptBytes",
        "open DeltaReduce.ProfileSource.InputSection",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace AggregateVectors",
        "open InputSectionVectors DeltaReduce.ProfileSource",
        f"def p : DeltaReduce.NativePolicyBytes.Policy := {projected(p)}",
        f"def wrong : DeltaReduce.NativePolicyBytes.Policy := {projected(wrong)}",
        f"def bodyRawR : Bytes := {bs(body_raw)}",
        f"def certRawR : Bytes := {bs(cert_raw)}",
        f"def wrongRawR : Bytes := {bs(wrong_raw)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(r)} then {bs(d)} else" for r, d in table.items()),
        "  ParameterVectors.hash raw",
        "def run (p : DeltaReduce.NativePolicyBytes.Policy) (certs : List Bytes) := do",
        "  let ec ← Eligibility.bindSection hash sigma body.context body.parent p [bodyRaw] raws",
        "    [LineageVectors.normRaw] [LineageVectors.seedRaw]",
        "    [EligibilityVectors.bodyRawEC] [EligibilityVectors.certRawEC]",
        "  let apc ← Plan.bindCollections hash sigma body.context p ec",
        "    [PlanVectors.bodyRawAPC] [PlanVectors.certRawAPC]",
        "  let params ← Parameter.bindCollections hash sigma body.context p ec apc",
        "    [ParameterVectors.bodyRawP] [ParameterVectors.certRawP]",
        "  Aggregate.bindCollections hash sigma body.context p ec apc params [bodyRawR] certs",
        "example : (run p [certRawR]).map (fun x => x.finalized) =",
        f"  some [{bs(cid)}] := by decide +kernel",
        "example : (run p [certRawR]).map (fun x => x.certificates.map",
        "  (fun e => e.value.shards.length))",
        "  = some [1] := by decide +kernel",
        "example : (run p [certRawR]).map (fun x => x.sizes.length) = some 10 := by decide +kernel",
        "example : (run p []).isNone = true := by decide +kernel",
        "example : (run wrong [wrongRawR]).isNone = true := by decide +kernel",
        "end AggregateVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_ROOT_BYTES_AND_COVERAGE_NOT_PRODUCER",
        "prior": originals,
        "whole_policy": policy.encode(p).hex(),
        "body": body_raw.hex(),
        "certificate": cert_raw.hex(),
        "body_id": bid,
        "certificate_id": cid,
        "wrong_root_policy": policy.encode(wrong).hex(),
        "wrong_root_certificate": wrong_raw.hex(),
        "sha256_preimages": {r.hex(): d.hex() for r, d in table.items()},
    }
