"""Future original V/M byte binding, separate from signature or producer authority."""

from dataclasses import replace

from formal.reference.isc_crypto import codec as c
from formal.reference.non_isc import codec as n
from formal.reference.profile_source import votes
from formal.reference.profile_source.configuration_vectors import bytes_term


def wire_term(kind, v):
    fields = (
        v.body_hash,
        v.context_id,
        str(v.durable_sequence),
        str(v.height),
        kind,
        v.round_id,
        v.formal_semantics_id,
        v.validator_epoch_id,
        v.validator_id,
        str(v.view),
    )
    return "⟨" + ",".join(bytes_term(x.encode()) for x in fields) + "⟩"


def generate():
    # Synthetic deterministic byte vectors; neither these IDs nor their valid
    # signatures would establish legal histories or a qualified sigma.
    base = c.Vote(
        "sha256:" + "1" * 64,
        "isc:round-1",
        2,
        "sha256:" + "2" * 64,
        1,
        "round-1",
        "sha256:" + "3" * 64,
        "validator-A",
        0,
    )
    registry, key = "sha256:" + "4" * 64, "sha256:" + "5" * 64
    cases = [(kind, base) for kind in ["ISC", *sorted(n.KINDS)]]
    cases.append(
        (
            "AGGREGATE_ROOT",
            replace(
                base,
                durable_sequence=2**64 - 1,
                height=2**64 - 1,
                view=2**64 - 1,
                context_id="x" * 128,
                round_id="r" * 128,
                validator_id="v" * 128,
            ),
        )
    )
    lines = [
        "import SourceVote",
        "open DeltaReduce.ProfileSource.Vote",
        "open DeltaReduce.NativeReceiptBytes (Bytes)",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 20000",
        "set_option maxHeartbeats 4000000",
        "namespace SourceVoteVectors",
    ]
    originals = []
    for i, (kind, value) in enumerate(cases):
        raw = c.encode_vote(value) if kind == "ISC" else n.encode_vote(n.NonIscVote(value, kind))
        codec = c if kind == "ISC" else n
        signable = codec.preimage(registry, key, raw)
        artifact = c.Artifact(registry, key, raw, bytes(64))
        graw = codec.encode_artifact(artifact)
        assert votes.decode(raw) == (kind, value)
        lines.extend(
            (
                f"def w{i} : WireVote := {wire_term(kind, value)}",
                f"def v{i} : Vote := ⟨w{i},{value.durable_sequence},{value.height},{value.view}⟩",
                f"def r{i} : Bytes := {bytes_term(raw)}",
                f"theorem valid{i} : VoteValid v{i} := by decide +kernel",
                f"theorem encoded{i} : encodeFrame w{i} = r{i} := by decide +kernel",
                f"example : decodeFrame r{i} = some v{i} := "
                f"decodeFrameFromEncoding v{i} r{i} valid{i} encoded{i}",
                f"example : signaturePreimage {bytes_term(registry.encode())} "
                f"{bytes_term(key.encode())} r{i} = some {bytes_term(signable)} "
                ":= by decide +kernel",
                f"def g{i} : Artifact := ⟨{bytes_term(registry.encode())},"
                f"{bytes_term(key.encode())},r{i},{bytes_term(artifact.signature)}⟩",
                f"example : bindArtifact {bytes_term(graw)} g{i} = some v{i} := by decide +kernel",
                f"example : bindArtifact {bytes_term(graw[:-1] + bytes([1]))} g{i} = none "
                ":= by decide +kernel",
            )
        )
        originals.append(
            {
                "kind": kind,
                "vote_hex": raw.hex(),
                "signable_hex": signable.hex(),
                "artifact_hex": graw.hex(),
                "signature_status": "STRUCTURAL_ZERO_BYTES_NOT_AUTHENTICATED",
            }
        )
    duplicated_payload = (
        b"\x31"
        + (12).to_bytes(4, "big")
        + b"".join(
            c._txt("body_hash" if key == "context_id" else key) + c._txt(c._vote_fields(base)[key])
            for key in c.VOTE_KEYS
        )
    )
    duplicated = b"DRC1\x01\0\0\x03" + c._l(duplicated_payload)
    malformed = [
        # Duplicate key, noncanonical decimal, unsupported generation, invalid
        # label, old thirteen-member layout, trailing byte and zero sequence.
        duplicated,
        c.encode_vote(base).replace(b"\x21\0\0\0\x012", b"\x21\0\0\0\x010", 1),
        c.encode_vote(base).replace(b"2.0.0", b"1.0.0"),
        c.encode_vote(base).replace(b"isc:round-1", b"isc/round-1"),
        c.encode_vote(base)[:13] + (13).to_bytes(4, "big") + c.encode_vote(base)[17:],
        c.encode_vote(base) + b"x",
    ]
    for i, raw in enumerate(malformed):
        try:
            votes.decode(raw)
        except c.CodecError:
            pass
        else:
            raise AssertionError("Malformed original vote accepted")
        lines.append(f"example : decodeFrame {bytes_term(raw)} = none := by decide +kernel")
        originals.append({"case": f"rejected-{i}", "vote_hex": raw.hex(), "expected": "REJECT"})
    lines.extend(
        (
            'def own : DeltaReduce.NativeWalBytes.Entry := ⟨2,2,r0,[],[],ascii "original-policy"⟩',
            "example : bindOwn w0.semantics w0.epoch w0.validator own = some v0 "
            ":= by decide +kernel",
            "example : bindOwn w0.semantics w0.epoch w0.validator "
            "{ own with sequence := 1 } = none := by decide +kernel",
            "end SourceVoteVectors",
        )
    )
    return "\n".join(lines) + "\n", originals
