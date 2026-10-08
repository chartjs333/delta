"""Original APC coverage and full parent bytes under parameterized future semantics."""

from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source.eligibility_vectors import generate as eligibility
from formal.reference.profile_source.eligibility_vectors import text64, u64
from formal.reference.profile_source.isc_vectors import bs
from formal.reference.profile_source.lineage_vectors import canonical
from formal.reference.profile_source.native_header_vectors import policy_term
from formal.reference.profile_source.policy_vectors import projected


def plan_bytes(ctx, item):
    raw = text64(ctx["arithmetic_profile_id"]) + u64(ctx["height"])
    raw += text64(ctx["parameter_schema_id"]) + text64(ctx["round_config_id"])
    raw += text64(ctx["round_id"]) + text64(ctx["validator_epoch_id"]) + u64(ctx["view"])
    raw += text64(item["accumulator_proof_id"]) + u64(len(item["bucket_assignments"]))
    for bucket in item["bucket_assignments"]:
        raw += text64(bucket["bucket_id"]) + text64(bucket["ticket_id"])
    raw += text64(item["eligibility_certificate_id"]) + text64(item["input_set_certificate_id"])
    raw += u64(item["iteration_count"]) + text64(item["seed_transcript_id"])
    raw += text64(item["transcript_root"]) + u64(len(item["weights"]))
    for w in item["weights"]:
        raw += (
            u64(w["alpha"]["numerator"]) + u64(w["alpha"]["denominator"]) + text64(w["ticket_id"])
        )
    return raw


def generate():
    _, originals = eligibility()
    p = policy.decode(bytes.fromhex(originals["whole_policy"]))
    ctx = p["snapshot"]["input_set_bodies"][0]["context"]
    ec = p["snapshot"]["eligibility_certificates"][0]
    common = {
        "context": ctx,
        "accumulator_proof_id": "sha256:" + "f" * 64,
        "bucket_assignments": [{"bucket_id": "bucket-0", "ticket_id": "ticket-001"}],
        "eligibility_certificate_id": originals["certificate_id"],
        "input_set_certificate_id": originals["prior"]["input_collections"]["b"],
        "iteration_count": 1,
        "seed_transcript_id": ec["seed_transcript_id"],
        "transcript_root": "sha256:" + "8" * 64,
        "weights": [{"alpha": {"numerator": 1, "denominator": 1}, "ticket_id": "ticket-001"}],
    }
    cert = {**common, "quorum_threshold": 3, "signer_ids": ["a", "b", "c"]}

    def json_cert(c):
        return canonical(
            {
                **ctx,
                **{k: v for k, v in c.items() if k not in ("context", "weights")},
                "weights": [
                    {**w, "alpha": {**w["alpha"], "numerator": str(w["alpha"]["numerator"])}}
                    for w in c["weights"]
                ],
                "formal_semantics_id": synthetic_body().formal_semantics_id,
                "type_name": "AGGREGATION_PLAN_CERTIFICATE",
                "schema_version": "1.0.0",
            }
        )

    body_raw, cert_raw = plan_bytes(ctx, common), json_cert(cert)
    table = {}

    def identifier(domain, raw):
        preimage = domain.encode("ascii") + b"\0" + raw
        digest = sha256(preimage).digest()
        table[preimage] = digest
        return "sha256:" + digest.hex()

    bid = identifier("deltareduce.vote.aggregation-plan-body.v1", body_raw)
    cid = identifier("deltareduce.008.aggregation-plan-certificate.v1", cert_raw)
    p["snapshot"].update(
        required_accumulator_proof_id=common["accumulator_proof_id"],
        aggregation_plan_bodies=[common],
        aggregation_plan_certificates=[cert],
        finalized_aggregation_plan_ids=[cid],
    )
    wrong = deepcopy(p)
    wrong["snapshot"]["aggregation_plan_certificates"][0]["weights"][0]["ticket_id"] = (
        "ticket-other"
    )
    wrong_raw = json_cert(wrong["snapshot"]["aggregation_plan_certificates"][0])
    wrong["snapshot"]["finalized_aggregation_plan_ids"] = [
        identifier("deltareduce.008.aggregation-plan-certificate.v1", wrong_raw)
    ]
    lines = [
        "import ProfilePlan\nimport EligibilityVectors",
        "open DeltaReduce.ISCSourceV2 DeltaReduce.NativeReceiptBytes",
        "open DeltaReduce.ProfileSource.InputSection",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace PlanVectors",
        "open InputSectionVectors DeltaReduce.ProfileSource",
        f"def p : DeltaReduce.NativePolicyBytes.Policy := {projected(p)}",
        f"def original : DeltaReduce.NativePolicyCodec.Value := {policy_term('policy', p)}",
        f"def wrong : DeltaReduce.NativePolicyBytes.Policy := {projected(wrong)}",
        f"def bodyRawAPC : Bytes := {bs(body_raw)}",
        f"def certRawAPC : Bytes := {bs(cert_raw)}",
        f"def wrongRawAPC : Bytes := {bs(wrong_raw)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in table.items()),
        "  EligibilityVectors.hash raw",
        "def run (p : DeltaReduce.NativePolicyBytes.Policy) (apcs : List Bytes) := do",
        "  let ec ← Eligibility.bindSection hash sigma body.context body.parent p [bodyRaw] raws",
        "    [LineageVectors.normRaw] [LineageVectors.seedRaw]",
        "    [EligibilityVectors.bodyRawEC] [EligibilityVectors.certRawEC]",
        "  let apc ← Plan.bindCollections hash sigma body.context p ec [bodyRawAPC] apcs",
        "  some (ec,apc)",
        "example : (run p [certRawAPC]).map (fun x => x.2.finalized) =",
        f"  some [{bs(cid)}] := by decide +kernel",
        "example : (run p [certRawAPC]).map (fun x => x.2.bodies.map (fun e => e.value.id)) =",
        f"  some [{bs(bid)}] := by decide +kernel",
        "example : (run p [certRawAPC]).map (fun x => WitnessIds x.1.lineage.inputs) =",
        "  some witnesses := by decide +kernel",
        "example : (run p []).isNone = true := by decide +kernel",
        "example : (run wrong [wrongRawAPC]).isNone = true := by decide +kernel",
        "end PlanVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_APC_BYTE_COVERAGE_NOT_PRODUCER",
        "prior": originals,
        "whole_policy": policy.encode(p).hex(),
        "body": body_raw.hex(),
        "certificate": cert_raw.hex(),
        "body_id": bid,
        "certificate_id": cid,
        "wrong_coverage_policy": policy.encode(wrong).hex(),
        "wrong_certificate": wrong_raw.hex(),
        "sha256_preimages": {r.hex(): d.hex() for r, d in table.items()},
    }
