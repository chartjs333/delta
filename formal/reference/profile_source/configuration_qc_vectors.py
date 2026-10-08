"""Exact CONFIG/QC/V/G join vectors; synthetic signatures, not origin evidence."""

from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto import codec as crypto
from formal.reference.non_isc import codec as vote_codec
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import configuration_qc as qc
from formal.reference.profile_source.configuration_vectors import bytes_term, value_term
from formal.reference.profile_source.test_configuration_qc import ConfigQcTests
from formal.reference.profile_source.vote_vectors import wire_term


def generate():
    ConfigQcTests.setUpClass()
    f = ConfigQcTests()
    f.setUp()
    repeat = replace(f.delivered[0], event=replace(f.delivered[0].event, event_index=5))
    other = f.delivery(6, f.names[0], durable_sequence=2)
    originals = (*f.delivered, repeat, other)
    # Existing pinned strict verifier checks real signatures generated with the
    # public synthetic keys; it proves neither production origin nor delivery.
    f.check(originals)
    alternate = {**f.qc, "qc_id": "sha256:" + "8" * 64, "vote_ids": list(f.qc["vote_ids"])}
    alternate["vote_ids"][0] = crypto.content_id(vote_codec.VOTE_DOMAIN, other.event.vote_frame)
    f.check(originals, alternate)
    malformed_context = f.delivery(7, f.names[0], height=2)
    try:
        f.check((*originals, malformed_context))
    except crypto.CodecError:
        pass
    else:
        raise AssertionError("same body/context with wrong height was silently omitted")
    table = {}

    def hashed(domain, raw):
        preimage = domain.encode() + b"\0" + raw
        table[preimage] = sha256(preimage).digest()

    hashed(cfg.DOMAIN, f.raw)
    epoch = f.body["validator_epoch_id"].encode()
    ctx = b"deltareduce.vote-context.config.v1\0" + (1).to_bytes(8, "big")
    ctx += len(epoch).to_bytes(8, "big") + epoch
    table[ctx] = sha256(ctx).digest()
    lines = [
        "import ProfileConfigurationQC",
        "open DeltaReduce.ProfileSource",
        "open DeltaReduce.ProfileSource.ConfigurationQC",
        "open DeltaReduce.NativeReceiptBytes (Bytes)",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace ConfigurationQCVectors",
        f"def configRaw : Bytes := {bytes_term(f.raw)}",
        f"def receiver : Bytes := {bytes_term(f.names[0].encode())}",
    ]
    registry = f.body["availability_policy"]["storage_binding"]
    lines.append(
        "def enrolled : Configuration.Enrollment := ⟨"
        + ",".join(
            [
                bytes_term(f.body["formal_semantics_id"].encode()),
                bytes_term(epoch),
                "[" + ",".join(bytes_term(n.encode()) for n in f.names) + "]",
                bytes_term(registry["storage_epoch_id"].encode()),
                bytes_term(registry["storage_registry_id"].encode()),
            ]
        )
        + "⟩"
    )
    retained = []
    for i, source in enumerate((*originals, malformed_context)):
        g = vote_codec.decode_artifact(source.original_artifact)
        v = vote_codec.decode_vote(g.vote_bytes).original
        hashed(vote_codec.VOTE_DOMAIN, g.vote_bytes)
        lines.extend(
            [
                f"def w{i} : Vote.WireVote := {wire_term('ROUND_CONFIG', v)}",
                f"def v{i} : Vote.Vote := ⟨w{i},{v.durable_sequence},{v.height},{v.view}⟩",
                f"def g{i} : Vote.Artifact := ⟨{bytes_term(g.registry_id.encode())},"
                f"{bytes_term(g.key_id.encode())},{bytes_term(g.vote_bytes)},"
                f"{bytes_term(g.signature)}⟩",
                f"def raw{i} : Bytes := {bytes_term(source.original_artifact)}",
                f"def row{i} : Received := ⟨{source.event.event_index},receiver,raw{i},g{i},v{i},"
                "by decide +kernel⟩",
            ]
        )
        retained.append(
            {
                "position": source.event.event_index,
                "receiver": f.names[0],
                "original_artifact_hex": source.original_artifact.hex(),
                "case": "wrong_height" if i == 6 else "retained",
            }
        )
    lines.extend(
        [
            "def hash (raw : Bytes) : Bytes :=",
            *(
                f"  if raw = {bytes_term(preimage)} then {bytes_term(digest)} else"
                for preimage, digest in table.items()
            ),
            "  []",
            "def rows : List Received := [row0,row1,row2,row3,row4,row5]",
        ]
    )
    for i, value in enumerate((f.qc, alternate)):
        raw = qc.encode(value)
        fields = [
            f"value{i}",
            *[
                bytes_term(value[name].encode())
                for name in (
                    "body_hash",
                    "context_id",
                    "formal_semantics_id",
                    "validator_epoch_id",
                    "round_id",
                    "qc_id",
                )
            ],
            value["height"],
            value["view"],
            str(value["quorum_threshold"]),
            "[" + ",".join(bytes_term(n.encode()) for n in value["signer_ids"]) + "]",
            "[" + ",".join(bytes_term(n.encode()) for n in value["vote_ids"]) + "]",
        ]
        lines.extend(
            [
                f"def value{i} : DeltaReduce.NativePolicyCodec.Value := {value_term(value)}",
                f"def qc{i} : Certificate := ⟨" + ",".join(fields) + "⟩",
                f"def original{i} : Bytes := {bytes_term(raw)}",
                f"theorem encoded{i} : encode value{i} = some original{i} := by decide +kernel",
                f"theorem parsed{i} : read value{i} = some qc{i} := by rfl",
                f"theorem decoded{i} : decode original{i} value{i} = some qc{i} := "
                f"complete parsed{i} encoded{i}",
                f"theorem pairs{i} : Pairing hash qc{i} rows := by decide +kernel",
                f"theorem selected{i} : selected receiver 6 qc{i} rows = rows := by rfl",
                f"theorem compatible{i} : GroupCompatible receiver 6 qc{i} rows "
                ":= by decide +kernel",
                f"example : join hash receiver 6 original{i} value{i} rows = "
                f"some ⟨original{i},qc{i},rows,selected receiver 6 qc{i} rows⟩ := "
                f"joinComplete decoded{i} (by decide) (selected{i} ▸ pairs{i}) compatible{i}",
            ]
        )
    lines.extend(
        [
            "example : (check hash enrolled receiver 6 configRaw original0 value0 rows).isSome "
            "= true "
            ":= by decide +kernel",
            "example : (join hash receiver 2 original0 value0 rows).isNone = true "
            ":= by decide +kernel",
            'example : (join hash (ascii "other-receiver") 6 original0 value0 rows).isNone = true '
            ":= by decide +kernel",
            "example : (join hash receiver 7 original0 value0 (rows ++ [row6])).isNone = true "
            ":= by decide +kernel",
            "example : (decode original0 value1).isNone = true := by decide +kernel",
            "example : qc0.id ≠ qc0.body := by decide +kernel",
            "example : qc0.id ≠ qc1.id := by decide +kernel",
            "example : rows.length = 6 := rfl",
            "example : qc0.signers.length = 4 := rfl",
            "end ConfigurationQCVectors",
        ]
    )
    evidence = {
        "kind": "SYNTHETIC_BYTE_JOIN_NOT_PRODUCTION_HISTORY",
        "signature_check": "PINNED_STRICT_VERIFIER_ON_PUBLIC_SYNTHETIC_KEYS",
        "config_hex": f.raw.hex(),
        "original_qc_hex": [qc.encode(value).hex() for value in (f.qc, alternate)],
        "received": retained,
        "preserved": "six distinct original occurrences, four signers, two original witnesses",
        "not_established": "source origin, delivery, producer permission or complete R2.3",
    }
    return "\n".join(lines) + "\n", evidence
