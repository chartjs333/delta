"""Exact ISC source byte/Merkle kernel vectors; not a native producer capture.

The finite hash table contains actual SHA-256 preimages/digests, with no success
fallback. It checks cross-language byte construction; it is not a SHA proof.
"""

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from formal.reference.isc_source.identity import (
    BODY_DOMAIN,
    CERTIFICATE_DOMAIN,
    LEAF_DOMAIN,
    NODE_DOMAIN,
    Certificate,
    InputTuple,
    body_id,
    body_preimage,
    certificate_bytes,
    certificate_id,
    tuple_bytes,
)
from formal.reference.isc_source.test_identity import synthetic_body

ROOT = Path(__file__).resolve().parents[3]


def bs(raw):
    if isinstance(raw, str):
        raw = raw.encode("ascii")
    return "[" + ",".join(map(str, raw)) + "]"


def lean_body(body):
    context = (
        "⟨"
        + ",".join(
            (
                bs(body.arithmetic_profile_id),
                str(body.height),
                bs(body.parameter_schema_id),
                bs(body.round_config_id),
                bs(body.round_id),
                bs(body.validator_epoch_id),
                str(body.view),
            )
        )
        + "⟩"
    )
    rows = [
        "⟨"
        + ",".join(
            map(bs, (r.availability_certificate_id, r.commitment_id, r.domain_id, r.ticket_id))
        )
        + "⟩"
        for r in body.tuples
    ]
    return f"⟨{context},{bs(body.parent_checkpoint_id)},{bs(body.input_root)},[{','.join(rows)}]⟩"


def generate():
    vectors = json.loads(
        (ROOT / "docs/adr/evidence/0014-isc-commitment-profile-v1-vectors.json").read_text()
    )
    leaves = {row["name"]: InputTuple(**row["tuple"]) for row in vectors["leaves"]}
    table, originals, definitions, checks = {}, [], [], []

    def hashed(raw):
        result = sha256(raw).digest()
        table[raw] = result
        return result

    bodies = []
    for i, vector in enumerate(vectors["positive_vectors"]):
        tuples = tuple(leaves[name] for name in vector["tuples"])
        level = [hashed(LEAF_DOMAIN + tuple_bytes(t)) for t in tuples]
        while len(level) > 1:
            if len(level) % 2:
                level.append(level[-1])
            level = [
                hashed(NODE_DOMAIN + a + b) for a, b in zip(level[::2], level[1::2], strict=True)
            ]
        assert "sha256:" + level[0].hex() == vector["input_root"]
        body = replace(synthetic_body(), tuples=tuples, input_root=vector["input_root"])
        bodies.append(body)
        definitions.append(f"def body{i} : Body := {lean_body(body)}")
        checks.append(f"example : inputRoot hash body{i}.tuples = some body{i}.root := by decide")

    # Two distinct original C artifacts over one B, not a relabel/migration.
    for i, signers in enumerate((("a", "b", "c"), ("a", "b", "c", "d"))):
        body = bodies[0]
        cert = Certificate(body, signers)
        raw = certificate_bytes(cert)
        hashed(BODY_DOMAIN.encode() + b"\0" + body_preimage(body))
        hashed(CERTIFICATE_DOMAIN.encode() + b"\0" + raw)
        definitions.extend(
            (
                f"def c{i} : Certificate := ⟨body0,3,[{','.join(map(bs, signers))}]⟩",
                f"def raw{i} : Bytes := {bs(raw)}",
            )
        )
        call = (
            f"bindCertificate hash sigma body0.context body0.parent committee "
            f"(certificateValue c{i})"
        )
        checks.extend(
            (
                f"example : certificateJSON sigma c{i} = raw{i} := by decide",
                f"example : bodyBytes sigma body0 = {bs(body_preimage(body))} := by decide",
                f"example : ({call} raw{i}).map BoundCertificate.consensusId = "
                f"some {bs(body_id(body))} := by decide",
                f"example : ({call} raw{i}).map BoundCertificate.witnessId = "
                f"some {bs(certificate_id(cert))} := by decide",
                f"example : ({call} (raw{i} ++ [32])).isNone = true := by decide",
            )
        )
        duplicate = b'{"parent_checkpoint_id":"sha256:' + b"8" * 64 + b'",' + raw[1:]
        checks.append(f"example : ({call} {bs(duplicate)}).isNone = true := by decide")
        originals.append(
            {"certificate_hex": raw.hex(), "b": body_id(body), "c": certificate_id(cert)}
        )
    checks.extend(
        (
            "example : c0.body = c1.body := by decide",
            "example : certificateJSON sigma c0 ≠ certificateJSON sigma c1 := by decide",
            "example : inputRoot hash [] = none := by decide",
            "example : ¬ BodyShape body0.context body0.parent "
            "{body0 with tuples := body0.tuples ++ body0.tuples} := by decide",
        )
    )
    dispatch = "\n  else ".join(f"if raw = {bs(k)} then {bs(v)}" for k, v in table.items())
    lines = [
        "import SourcePolicy",
        "open DeltaReduce.ISCSourceV2 DeltaReduce.NativeReceiptBytes",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace ISCOriginalByteVectors",
        "-- Finite actual digest table, no fallback success or crypto theorem.",
        f"def hash (raw : Bytes) : Bytes :=\n  {dispatch}\n  else []",
        f"def sigma : Bytes := {bs(bodies[0].formal_semantics_id)}",
        f"def committee : List Bytes := [{','.join(map(bs, ('a', 'b', 'c', 'd')))}]",
        *definitions,
        *checks,
        "end ISCOriginalByteVectors",
    ]
    return "\n".join(lines) + "\n", {
        "original_certificates": originals,
        "sha256_preimages": [
            {"input_hex": k.hex(), "digest_hex": v.hex()} for k, v in table.items()
        ],
        "claim": "synthetic exact bytes/finite hashes; no source legality or cryptography proof",
    }
