"""Whole successor policy extraction; structural evidence, not producer origin."""

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.isc_source import policy
from formal.reference.profile_source.configuration_vectors import bytes_term
from formal.reference.profile_source.native_header_vectors import policy_term
from formal.reference.profile_source.test_input_capsule import InputCapsuleTests


def projected(value):
    def text(name):
        return bytes_term(value[name].encode("ascii"))

    candidates = []
    for c in value["candidates"]:
        candidates.append(
            "⟨"
            + ",".join(
                (
                    str(c["action"]),
                    bytes_term(c["body_hash"].encode()),
                    bytes_term(c["context_id"].encode()),
                    str(c["height"]),
                    str(c["view"]),
                    policy_term("parents", c["parents"]),
                    policy_term("candidate", c),
                )
            )
            + "⟩"
        )
    return (
        "⟨"
        + ",".join(
            (
                text("local_validator_id"),
                text("validator_epoch_id"),
                "[" + ",".join(bytes_term(x.encode()) for x in value["validator_ids"]) + "]",
                str(value["role"]),
                text("round_id"),
                text("round_config_id"),
                text("configured_abort_reason"),
                str(value["initial_logical_tick"]),
                str(value["soft_deadline_tick"]),
                str(value["hard_deadline_tick"]),
                policy_term("snapshot", value["snapshot"]),
                "[" + ",".join(candidates) + "]",
                "tree",
            )
        )
        + "⟩"
    )


def generate():
    InputCapsuleTests.setUpClass()
    fixture = InputCapsuleTests()
    fixture.setUp()
    raw = fixture.policy
    value = policy.decode(raw)
    assert policy.encode(value) == raw
    negatives = {
        "legacy_header": b"DVPOL001" + raw[8:],
        "trailing": raw + b"\x00",
        "truncated": raw[:-1],
    }
    for bad in negatives.values():
        try:
            policy.decode(bad)
        except CodecError:
            continue
        raise AssertionError("policy negative accepted")
    lines = [
        "import ProfilePolicy",
        "open DeltaReduce.ProfileSource.Policy",
        "open DeltaReduce.NativeReceiptBytes (Bytes)",
        "set_option maxRecDepth 20000",
        "set_option maxHeartbeats 4000000",
        "namespace PolicyVectors",
        f"def original : Bytes := {bytes_term(raw)}",
        f"def tree : DeltaReduce.NativePolicyCodec.Value := {policy_term('policy', value)}",
        f"def typed : DeltaReduce.NativePolicyBytes.Policy := {projected(value)}",
        "theorem source : Source original tree typed := by",
        "  constructor",
        "  · decide +kernel",
        "  · decide +kernel",
        "  · rfl",
        "  · decide +kernel",
        "example : decode original = some (tree,typed) := complete source",
        "example : typed.source = tree := extractionOriginal source.extraction",
        "example : DeltaReduce.ProfileSource.NativeHeader.policyBytes typed.source =",
        "    some original := (completeSourcePreserved (complete source)).1",
        "example (field : String) :",
        "    DeltaReduce.NativePolicyCodec.lookup",
        "      DeltaReduce.ProfileSource.NativeHeader.snapshotFormat typed.snapshot field =",
        "    DeltaReduce.NativePolicyCodec.lookup",
        "      DeltaReduce.NativePolicySchema.fmtSnapshot typed.snapshot field :=",
        "  sameSnapshotFields typed.snapshot field",
        "end PolicyVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_FULL_POLICY_STRUCTURE_NOT_VALID_PRODUCER_SNAPSHOT",
        "original": raw.hex(),
        "nonempty_snapshot_collections": [
            name for name, x in value["snapshot"].items() if isinstance(x, list) and x
        ],
        "negative_originals": {name: bad.hex() for name, bad in negatives.items()},
        "not_established": "collection validity, origin, phase, finality, authority or R2.3",
    }
