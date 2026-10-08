"""Join whole decoded collections to original-cut targets and numeric membership.

These are synthetic successor objects, not an authenticated production history.
The generated test uses the full collection decoder before any target is formed.
"""

import json
from hashlib import sha256

from formal.reference.profile_source.certificate_vote_vectors import generate as votes
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.eligibility_vectors import text64


def generate():
    _, corpus = votes()
    contexts = {}
    # Derive the exact same contexts from the whole original certificate fields.
    for case, domain, field in zip(
        corpus["cases"],
        ("ec", "apc", None, "root", "apply"),
        (
            "input_set_certificate_id",
            "eligibility_certificate_id",
            None,
            "aggregation_plan_certificate_id",
            "aggregate_root_qc_id",
        ),
        strict=True,
    ):
        if domain is not None:
            certificate = json.loads(bytes.fromhex(case["original_certificate"]))
            preimage = f"deltareduce.vote-context.{domain}.v1".encode() + b"\0"
            preimage += text64(certificate[field])
            contexts[preimage] = sha256(preimage).digest()
    lines = [
        "import CollectionsVectors",
        "import CertificateVoteVectors",
        "import ProfilePlanMembers",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "open CertificateVoteVectors",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "set_option synthInstance.maxSize 512",
        "namespace TypedCertificateVectors",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in contexts.items()),
        "  CollectionsVectors.hash raw",
        "def result : Option (List CertificateVotes.Target \u00d7 List (Bytes \u00d7 Nat) \u00d7 "
        "List (Bytes \u00d7 Nat \u00d7 Nat)) := do",
        "  let s ← NativeHeader.readCoarse CollectionsVectors.state",
        "  let b ← Collections.bind hash s CollectionsVectors.p CollectionsVectors.originals",
        "  let ec ← b.eligibility.certificates[0]?",
        "  let apc ← b.plans.certificates[0]?",
        "  let assignment ← b.parameters.bodies[0]?",
        "  let parameter ← b.parameters.certificates[0]?",
        "  let root ← b.roots.certificates[0]?",
        "  let apply ← b.applies.certificates[0]?",
        "  let t0 ← CertificateVotes.derive hash s.semantics (.ec ec)",
        "  let t1 ← CertificateVotes.derive hash s.semantics (.apc apc)",
        "  let t2 ← CertificateVotes.derive hash s.semantics (.parameter assignment parameter)",
        "  let t3 ← CertificateVotes.derive hash s.semantics (.root root)",
        "  let t4 ← CertificateVotes.derive hash s.semantics (.apply apply)",
        "  let q0 ← CertificateVotes.bind committee actor 5 t0 rows0",
        "  let q1 ← CertificateVotes.bind committee actor 5 t1 rows1",
        "  let q2 ← CertificateVotes.bind committee actor 5 t2 rows2",
        "  let q3 ← CertificateVotes.bind committee actor 5 t3 rows3",
        "  let q4 ← CertificateVotes.bind committee actor 5 t4 rows4",
        "  let members ← PlanMembers.derive apc",
        "  some ([q0,q1,q2,q3,q4].map CertificateVotes.Bound.target,",
        "    members.members.map (fun m : DeltaReduce.NativePlanMembers.Member => "
        "(m.input.ticket,m.eligibility.accepted)),",
        "    members.rows.map (fun r : DeltaReduce.NativePlanMembers.Row => "
        "(r.weight.ticket,r.weight.numerator,r.weight.denominator)))",
        "example : result = some ([target0,target1,target2,target3,target4],",
        '  [(DeltaReduce.NativeVoteBytes.ascii "ticket-001",1)],',
        '  [(DeltaReduce.NativeVoteBytes.ascii "ticket-001",1,1)]) := by decide +kernel',
        "end TypedCertificateVectors",
    ]
    return "\n".join(lines) + "\n"
