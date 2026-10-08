"""Full original candidate/QC values; synthetic, not computation or producer truth."""

from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source.aggregate_vectors import generate as aggregate
from formal.reference.profile_source.isc_vectors import bs
from formal.reference.profile_source.lineage_vectors import canonical
from formal.reference.profile_source.policy_vectors import projected


def generate():
    _, originals = aggregate()
    p = policy.decode(bytes.fromhex(originals["whole_policy"]))
    ctx = p["snapshot"]["input_set_bodies"][0]["context"]
    body = synthetic_body()
    table = {}

    def identifier(domain, raw):
        preimage = domain.encode("ascii") + b"\0" + raw
        digest = sha256(preimage).digest()
        table[preimage] = digest
        return "sha256:" + digest.hex()

    def fraction(n, d):
        return {"numerator": n, "denominator": d}

    profile = {
        "accumulator_proof_id": p["snapshot"]["required_accumulator_proof_id"],
        "domain_weights": [{"domain_id": "code", "pi": fraction(1, 1)}],
        "learning_rate": fraction(1, 4),
        "momentum": fraction(0, 1),
        "nesterov": True,
        "rounding": "HALF_TOWARD_POSITIVE",
        "weight_decay": fraction(0, 1),
    }
    profile_json = deepcopy(profile)
    for key in ("learning_rate", "momentum", "weight_decay"):
        profile_json[key]["numerator"] = str(profile_json[key]["numerator"])
    profile_json["domain_weights"][0]["pi"]["numerator"] = "1"
    profile_json.update(
        formal_semantics_id=body.formal_semantics_id,
        schema_version="2.0.0",
        type_name="APPLY_ARITHMETIC_PROFILE",
    )
    profile_raw = canonical(profile_json)
    pid = identifier("deltareduce.008.apply-arithmetic-profile.v1", profile_raw)
    candidate = {
        "context": ctx,
        "aggregate_root_qc_id": originals["certificate_id"],
        "apply_arithmetic_profile_id": pid,
        "next_model_hash": "sha256:" + "3" * 64,
        "next_model_values": ["11", "12", "13", "14"],
        "next_optimizer_hash": "sha256:" + "4" * 64,
        "next_optimizer_values": ["0", "1", "0", "-1"],
        "parent_checkpoint_id": body.parent_checkpoint_id,
        "parent_optimizer_hash": "sha256:" + "5" * 64,
    }

    def json_payload(value, kind):
        return canonical(
            {
                **ctx,
                **{k: v for k, v in value.items() if k != "context"},
                "formal_semantics_id": body.formal_semantics_id,
                "schema_version": "2.0.0",
                "type_name": kind,
            }
        )

    candidate_raw = json_payload(candidate, "APPLY_CANDIDATE")
    bid = identifier("deltareduce.008.apply-candidate.v1", candidate_raw)
    cert = {
        k: v
        for k, v in candidate.items()
        if k not in ("next_model_values", "next_optimizer_values", "parent_optimizer_hash")
    }
    cert.update(apply_candidate_id=bid, quorum_threshold=3, signer_ids=["a", "b", "c"])
    cert_raw = json_payload(cert, "APPLY_QC")
    cid = identifier("deltareduce.008.apply-qc.v1", cert_raw)
    identifier(
        "deltareduce.008.apply-qc.v1",
        json_payload({**cert, "signer_ids": p["validator_ids"]}, "APPLY_QC"),
    )
    p["snapshot"].update(
        apply_profiles=[profile],
        apply_candidates=[candidate],
        apply_qcs=[{"certificate": cert, "candidate": candidate}],
        finalized_apply_ids=[cid],
    )
    wrong = deepcopy(p)
    wrong["snapshot"]["apply_qcs"][0]["candidate"]["next_model_values"][0] = "99"
    changed_candidate = wrong["snapshot"]["apply_qcs"][0]["candidate"]
    identifier(
        "deltareduce.008.apply-candidate.v1", json_payload(changed_candidate, "APPLY_CANDIDATE")
    )
    lines = [
        "import ProfileApply\nimport AggregateVectors",
        "open DeltaReduce.ISCSourceV2 DeltaReduce.NativeReceiptBytes",
        "open DeltaReduce.ProfileSource.InputSection",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace ApplyVectors",
        "open InputSectionVectors DeltaReduce.ProfileSource",
        f"def p : DeltaReduce.NativePolicyBytes.Policy := {projected(p)}",
        f"def wrong : DeltaReduce.NativePolicyBytes.Policy := {projected(wrong)}",
        f"def profileRaw : Bytes := {bs(profile_raw)}",
        f"def candidateRaw : Bytes := {bs(candidate_raw)}",
        f"def certRawA : Bytes := {bs(cert_raw)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(r)} then {bs(d)} else" for r, d in table.items()),
        "  AggregateVectors.hash raw",
        "def run (p : DeltaReduce.NativePolicyBytes.Policy) (certs : List Bytes) := do",
        "  let roots ← AggregateVectors.run p [AggregateVectors.certRawR]",
        "  Apply.bindCollections hash sigma body.context body.parent p roots",
        "    [profileRaw] [candidateRaw] certs",
        "example : (run p [certRawA]).map (fun x => x.finalized) =",
        f"  some [{bs(cid)}] := by decide +kernel",
        "example : (run p [certRawA]).map (fun x => x.certificates.map",
        "  (fun e => e.value.decoded.candidate.modelValues)) =",
        f"  some [[{','.join(bs(x) for x in candidate['next_model_values'])}]] :=",
        "  by decide +kernel",
        "example : (run p []).isNone = true := by decide +kernel",
        "example : (run wrong [certRawA]).isNone = true := by decide +kernel",
        "end ApplyVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_APPLY_BYTES_NOT_ARITHMETIC_OR_ORIGIN",
        "prior": originals,
        "whole_policy": policy.encode(p).hex(),
        "profile": profile_raw.hex(),
        "candidate": candidate_raw.hex(),
        "certificate": cert_raw.hex(),
        "profile_id": pid,
        "candidate_id": bid,
        "certificate_id": cid,
        "changed_candidate_policy": policy.encode(wrong).hex(),
        "sha256_preimages": {r.hex(): d.hex() for r, d in table.items()},
    }
