"""Whole original EC body/certificate section over successor b, not origin."""

from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source.isc_vectors import bs
from formal.reference.profile_source.lineage_vectors import canonical
from formal.reference.profile_source.lineage_vectors import generate as lineage
from formal.reference.profile_source.native_header_vectors import policy_term
from formal.reference.profile_source.policy_vectors import projected


def u64(value):
    return value.to_bytes(8, "big")


def text64(value):
    raw = value.encode("ascii")
    return u64(len(raw)) + raw


def body_bytes(ctx, item):
    raw = text64(ctx["arithmetic_profile_id"]) + u64(ctx["height"])
    raw += text64(ctx["parameter_schema_id"]) + text64(ctx["round_config_id"])
    raw += text64(ctx["round_id"]) + text64(ctx["validator_epoch_id"]) + u64(ctx["view"])
    raw += u64(len(item["entries"]))
    for e in item["entries"]:
        raw += bytes([int(e["accepted"])]) + text64(e["domain_id"])
        raw += u64(int(e["gamma"]["numerator"])) + u64(e["gamma"]["denominator"])
        raw += text64(e["reason_code"]) + text64(e["ticket_id"])
    return raw + b"".join(
        text64(item[k])
        for k in (
            "input_set_certificate_id",
            "norm_evidence_id",
            "robust_profile_id",
            "seed_transcript_id",
        )
    )


def generate():
    _, originals = lineage()
    p = policy.decode(bytes.fromhex(originals["whole_policy"]))
    body = synthetic_body()
    ctx = p["snapshot"]["input_set_bodies"][0]["context"]
    entries = [
        {
            "accepted": True,
            "domain_id": "code",
            "gamma": {"numerator": 1, "denominator": 1},
            "reason_code": "ACCEPT",
            "ticket_id": "ticket-001",
        }
    ]
    nid = (
        "sha256:"
        + sha256(
            b"deltareduce.008.norm-evidence.v1\0" + bytes.fromhex(originals["norm"])
        ).hexdigest()
    )
    sid = (
        "sha256:"
        + sha256(
            b"deltareduce.008.seed-transcript.v1\0" + bytes.fromhex(originals["seed"])
        ).hexdigest()
    )
    ec_body = {
        "context": ctx,
        "entries": entries,
        "input_set_certificate_id": originals["input_collections"]["b"],
        "norm_evidence_id": nid,
        "robust_profile_id": "sha256:" + "e" * 64,
        "seed_transcript_id": sid,
    }
    ec_cert = {k: v for k, v in ec_body.items() if k != "seed_transcript_id"}
    ec_cert.update(quorum_threshold=3, signer_ids=["a", "b", "c"])
    cert_json = {
        **ctx,
        **{k: v for k, v in ec_cert.items() if k not in ("context", "entries")},
        "entries": [
            {**e, "gamma": {**e["gamma"], "numerator": str(e["gamma"]["numerator"])}}
            for e in entries
        ],
        "formal_semantics_id": body.formal_semantics_id,
        "type_name": "ELIGIBILITY_CERTIFICATE",
        "schema_version": "1.0.0",
    }
    body_raw, cert_raw = body_bytes(ctx, ec_body), canonical(cert_json)
    table = {}

    def identifier(domain, raw):
        preimage = domain.encode("ascii") + b"\0" + raw
        digest = sha256(preimage).digest()
        table[preimage] = digest
        return "sha256:" + digest.hex()

    bid = identifier("deltareduce.vote.eligibility-body.v1", body_raw)
    cid = identifier("deltareduce.008.eligibility-certificate.v1", cert_raw)
    p["snapshot"].update(
        eligibility_bodies=[ec_body],
        eligibility_certificates=[{"certificate": ec_cert, "seed_transcript_id": sid}],
        finalized_eligibility_ids=[cid],
    )
    wrong = deepcopy(p)
    wrong_cert = wrong["snapshot"]["eligibility_certificates"][0]["certificate"]
    wrong_cert["input_set_certificate_id"] = originals["input_collections"]["c"][0]
    wrong_json = {**cert_json, "input_set_certificate_id": wrong_cert["input_set_certificate_id"]}
    wrong_raw = canonical(wrong_json)
    wrong["snapshot"]["finalized_eligibility_ids"] = [
        identifier("deltareduce.008.eligibility-certificate.v1", wrong_raw)
    ]
    source = [
        "import ProfileEligibility\nimport LineageVectors",
        "open DeltaReduce.ISCSourceV2 DeltaReduce.NativeReceiptBytes",
        "open DeltaReduce.ProfileSource.InputSection",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace EligibilityVectors",
        "open InputSectionVectors DeltaReduce.ProfileSource.Eligibility",
        f"def p : DeltaReduce.NativePolicyBytes.Policy := {projected(p)}",
        f"def original : DeltaReduce.NativePolicyCodec.Value := {policy_term('policy', p)}",
        f"def wrong : DeltaReduce.NativePolicyBytes.Policy := {projected(wrong)}",
        f"def bodyRawEC : Bytes := {bs(body_raw)}",
        f"def certRawEC : Bytes := {bs(cert_raw)}",
        f"def wrongRawEC : Bytes := {bs(wrong_raw)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in table.items()),
        "  LineageVectors.hash raw",
        "def result := bindSection hash sigma body.context body.parent p [bodyRaw] raws",
        "  [LineageVectors.normRaw] [LineageVectors.seedRaw] [bodyRawEC] [certRawEC]",
        f"example : result.map (fun r => r.finalized) = some [{bs(cid)}] := by decide +kernel",
        "example : result.map (fun r => r.bodies.map (fun x => x.value.id)) =",
        f"  some [{bs(bid)}] := by decide +kernel",
        "example : result.map (fun r => WitnessIds r.lineage.inputs) =",
        "  some witnesses := by decide +kernel",
        "example : result.map (fun r => r.certificates.map",
        "  (fun x => x.value.certificate.common.isc)) = some [b] := by decide +kernel",
        "example : (bindSection hash sigma body.context body.parent p [bodyRaw] raws",
        "  [LineageVectors.normRaw] [LineageVectors.seedRaw] [bodyRawEC] []).isNone =",
        "  true := by decide +kernel",
        "example : (bindSection hash sigma body.context body.parent wrong [bodyRaw] raws",
        "  [LineageVectors.normRaw] [LineageVectors.seedRaw] [bodyRawEC] [wrongRawEC]).isNone =",
        "  true := by decide +kernel",
        "end EligibilityVectors",
    ]
    return "\n".join(source) + "\n", {
        "evidence_kind": "SYNTHETIC_EC_BYTE_LINEAGE_NOT_PRODUCER_OR_QUORUM",
        "prior": originals,
        "whole_policy": policy.encode(p).hex(),
        "body": body_raw.hex(),
        "certificate": cert_raw.hex(),
        "body_id": bid,
        "certificate_id": cid,
        "wrong_b_c_policy": policy.encode(wrong).hex(),
        "wrong_certificate": wrong_raw.hex(),
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in table.items()},
    }
