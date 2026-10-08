"""Original typed targets and delivery-cut joins; no authentic history claim."""

import json
from hashlib import sha256

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.non_isc import codec
from formal.reference.profile_source.apply_vectors import generate as apply_vectors
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.eligibility_vectors import text64
from formal.reference.profile_source.vote_vectors import wire_term


def generate():
    _, apply = apply_vectors()
    root, parameter, plan, ec = (
        apply["prior"],
        apply["prior"]["prior"],
        apply["prior"]["prior"]["prior"],
        apply["prior"]["prior"]["prior"]["prior"],
    )
    p = policy.decode(bytes.fromhex(apply["whole_policy"]))
    ctx = p["snapshot"]["input_set_bodies"][0]["context"]
    sigma = synthetic_body().formal_semantics_id
    context_term = (
        "⟨"
        + ",".join(
            str(ctx[k]) if k in ("height", "view") else bs(ctx[k].encode())
            for k in (
                "arithmetic_profile_id",
                "height",
                "parameter_schema_id",
                "round_config_id",
                "round_id",
                "validator_epoch_id",
                "view",
            )
        )
        + "⟩"
    )
    profiles = [
        ("EC", ec, "ec", "input_set_certificate_id", "eligibility-certificate"),
        (
            "APC",
            plan,
            "apc",
            "eligibility_certificate_id",
            "aggregation-plan-certificate",
        ),
        ("PARAMETER", parameter, None, None, "parameter-shard-qc"),
        (
            "AGGREGATE_ROOT",
            root,
            "root",
            "aggregation_plan_certificate_id",
            "aggregate-root-qc",
        ),
        ("APPLY", apply, "apply", "aggregate_root_qc_id", "apply-qc"),
    ]
    lines = [
        "import ProfileCertificateVotes",
        "open DeltaReduce.ProfileSource DeltaReduce.ProfileSource.CertificateVotes",
        "open DeltaReduce.NativeReceiptBytes (Bytes)",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace CertificateVoteVectors",
        'def committee : List Bytes := [ascii "a",ascii "b",ascii "c",ascii "d"]',
        'def actor : Bytes := ascii "a"',
        f"def context : DeltaReduce.NativeInputSetBody.Context := {context_term}",
    ]
    corpus = []
    for i, (kind, original, domain, parent, cert_domain) in enumerate(profiles):
        raw = bytes.fromhex(original["certificate"])
        c = json.loads(raw)
        if kind == "PARAMETER":
            vote_context = p["snapshot"]["parameter_bodies"][0]["vote_context_id"]
        else:
            preimage = f"deltareduce.vote-context.{domain}.v1".encode() + b"\0" + text64(c[parent])
            vote_context = "sha256:" + sha256(preimage).hexdigest()
        body = original.get("body_id", original.get("candidate_id"))
        target = [
            bs(kind.encode()),
            bs(sigma.encode()),
            "context",
            bs(vote_context.encode()),
            bs(body.encode()),
            bs(original["certificate_id"].encode()),
            bs(raw),
            '[ascii "a",ascii "b",ascii "c"]',
            "3",
        ]
        lines.append(f"def target{i} : Target := ⟨" + ",".join(target) + "⟩")
        retained = []
        for j, (signer, sequence, position) in enumerate(
            (
                ("a", 2, 1),
                ("b", 2, 2),
                ("c", 2, 3),
                ("a", 2, 4),
                ("a", 3, 5),
                ("d", 2, 7),
            )
        ):
            v = crypto.Vote(
                body,
                vote_context,
                sequence,
                sigma,
                ctx["height"],
                ctx["round_id"],
                ctx["validator_epoch_id"],
                signer,
                ctx["view"],
            )
            frame = codec.encode_vote(codec.NonIscVote(v, kind))
            artifact = crypto.Artifact("sha256:" + "4" * 64, "sha256:" + "5" * 64, frame, bytes(64))
            g = codec.encode_artifact(artifact)
            name = f"{i}_{j}"
            lines += [
                f"def w{name} : Vote.WireVote := {wire_term(kind, v)}",
                f"def v{name} : Vote.Vote := ⟨w{name},{sequence},{v.height},{v.view}⟩",
                f"def g{name} : Vote.Artifact := ⟨{bs(artifact.registry_id.encode())},"
                f"{bs(artifact.key_id.encode())},{bs(frame)},{bs(artifact.signature)}⟩",
                f"def row{name} : ConfigurationQC.Received := ⟨{position},actor,"
                f"{bs(g)},g{name},v{name},by decide +kernel⟩",
            ]
            retained.append(
                {
                    "position": position,
                    "original_G": g.hex(),
                    "signature_status": "ZERO_BYTES_STRUCTURAL_ONLY",
                }
            )
        lines += [
            f"def rows{i} : List ConfigurationQC.Received := ["
            + ",".join(f"row{i}_{j}" for j in range(6))
            + "]",
            f"example : (bind committee actor 5 target{i} rows{i}).map (fun b => "
            "(b.originalRows.length,b.matchingRows.length,b.target.signers.length)) "
            "= some (6,5,3) := by decide +kernel",
            f"example : (bind committee actor 2 target{i} rows{i}).isNone "
            "= true := by decide +kernel",
            f"example : (bind committee actor 7 target{i} rows{i}).isNone "
            "= true := by decide +kernel",
            f'example : (bind committee (ascii "other") 5 target{i} rows{i}).isNone '
            "= true := by decide +kernel",
            f"example : (bind committee actor 5 {{ target{i} with threshold := 2 }} "
            f"rows{i}).isNone "
            "= true := by decide +kernel",
        ]
        expanded = {**c, "signer_ids": ["a", "b", "c", "d"]}
        expanded_raw = json.dumps(
            expanded, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
        expanded_id = (
            "sha256:"
            + sha256(
                f"deltareduce.008.{cert_domain}.v1".encode() + b"\0" + expanded_raw
            ).hexdigest()
        )
        lines += [
            f"def later{i} : Target := {{ target{i} with signers := committee, "
            f"certificateId := {bs(expanded_id.encode())}, "
            f"originalCertificate := {bs(expanded_raw)} }}",
            f"example : (bind committee actor 7 later{i} rows{i}).map "
            f"(fun b => b.target.certificateId) = some {bs(expanded_id.encode())} "
            ":= by decide +kernel",
            f"example : target{i}.certificateId ≠ later{i}.certificateId := by decide +kernel",
        ]
        corpus.append(
            {
                "kind": kind,
                "original_certificate": raw.hex(),
                "certificate_id": original["certificate_id"],
                "body_id": body,
                "vote_context": vote_context,
                "received": retained,
                "later_certificate": expanded_raw.hex(),
                "later_certificate_id": expanded_id,
            }
        )
    # A repeated delivery has a distinct source position; a second original
    # vote has a distinct signed durable sequence. Both remain in the output.
    lines += [
        "example : row0_0.originalG = row0_3.originalG ∧ row0_0.position ≠ row0_3.position "
        ":= by decide +kernel",
        "example : row0_0.originalG ≠ row0_4.originalG ∧ "
        "row0_0.vote.sequence ≠ row0_4.vote.sequence := by decide +kernel",
        "example : (bind committee actor 5 target0 [row0_0,row0_3,row0_4,row0_1]).isNone "
        "= true := by decide +kernel",
        "example : (bind committee actor 5 { target0 with body := target0.certificateId } "
        "rows0).isNone "
        "= true := by decide +kernel",
        "example : (bind committee actor 5 { target0 with context := "
        "{ context with height := context.height+1 } } rows0).isNone = true := by decide +kernel",
        "example : (bind committee actor 6 target0 (rows0 ++ [{ row1_0 with position := 6 }])).map "
        "(fun b => (b.originalRows.length,b.matchingRows.length)) = some (7,5) "
        ":= by decide +kernel",
        "end CertificateVoteVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_ORIGINAL_CUT_QUORUM_COMPONENT_NOT_AUTHENTIC_HISTORY",
        "cases": corpus,
    }
