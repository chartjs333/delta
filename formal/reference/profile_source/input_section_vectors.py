"""Complete original B/C collection binding; deliberately not a legal full state."""

from hashlib import sha256

from formal.reference.isc_source import finalization, identity, policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.isc_source.test_policy import structural_policy
from formal.reference.profile_source.isc_vectors import bs, lean_body
from formal.reference.profile_source.native_header_vectors import policy_term
from formal.reference.profile_source.policy_vectors import projected


def generate():
    body = synthetic_body()
    certificates = sorted(
        (
            identity.Certificate(body, signers)
            for signers in (("a", "b", "c"), ("a", "b", "c", "d"))
        ),
        key=identity.certificate_id,
    )
    raws = [identity.certificate_bytes(c) for c in certificates]
    b = identity.body_id(body)
    witnesses = [identity.certificate_id(c) for c in certificates]
    assert witnesses[0] != witnesses[1] and b not in witnesses
    p = structural_policy()
    p["validator_ids"] = ["a", "b", "c", "d"]
    p["snapshot"].update(
        input_set_bodies=[finalization.body_tree(body)],
        input_set_certificates=[finalization.certificate_tree(c) for c in certificates],
        closed_input_set_ids=[b],
        finalized_input_set_ids=[b],
    )
    raw_p = policy.encode(p)
    assert policy.decode(raw_p) == p
    preimages = [
        identity.LEAF_DOMAIN + identity.tuple_bytes(body.tuples[0]),
        identity.BODY_DOMAIN.encode() + b"\0" + identity.body_preimage(body),
        *(identity.CERTIFICATE_DOMAIN.encode() + b"\0" + raw for raw in raws),
    ]
    table = {raw: sha256(raw).digest() for raw in preimages}
    lines = [
        "import ProfileInputSection",
        "open DeltaReduce.ISCSourceV2 DeltaReduce.NativeReceiptBytes",
        "open DeltaReduce.ProfileSource.InputSection",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace InputSectionVectors",
        f"def body : Body := {lean_body(body)}",
        f"def sigma : Bytes := {bs(body.formal_semantics_id)}",
        f"def bodyRaw : Bytes := {bs(identity.body_preimage(body))}",
        f"def raws : List Bytes := [{','.join(map(bs, raws))}]",
        f"def b : Bytes := {bs(b)}",
        f"def witnesses : List Bytes := [{','.join(map(bs, witnesses))}]",
        f"def tree : DeltaReduce.NativePolicyCodec.Value := {policy_term('policy', p)}",
        f"def p : DeltaReduce.NativePolicyBytes.Policy := {projected(p)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in table.items()),
        "  []",
        "def run (state : DeltaReduce.NativePolicyBytes.Policy) (originals : List Bytes) :=",
        "  bindAt hash sigma body.context body.parent state [bodyRaw] originals",
        "example : (run p raws).map WitnessIds = some witnesses := by decide +kernel",
        "example : (run p raws).map RepresentedBodies = some [b,b] := by decide +kernel",
        "example : (run p raws).map (fun x => x.certificates.length) = some 2 := by decide +kernel",
        "example : (run p raws).map Bound.finalized = some [b] := by decide +kernel",
        "example : (run p (raws.take 1)).isNone = true := by decide +kernel",
        "example : (run p raws.reverse).isNone = true := by decide +kernel",
        "def wrongIndex : DeltaReduce.NativePolicyBytes.Policy :=",
        "  {p with snapshot := (snapshotDelta p.snapshot",
        '    (.items ((trees p "input_set_certificates").getD []))',
        "    (.items (witnesses.map DeltaReduce.NativePolicyCodec.Value.text))).getD p.snapshot}",
        "example : (run wrongIndex raws).isNone = true := by decide +kernel",
        "end InputSectionVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_ORIGINAL_COLLECTIONS_NOT_FULL_SOURCE_VALIDITY",
        "whole_policy": raw_p.hex(),
        "body": identity.body_preimage(body).hex(),
        "certificates": [raw.hex() for raw in raws],
        "b": b,
        "c": witnesses,
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in table.items()},
        "not_established": "signature/producer origin, other collections or complete R2.3",
    }
