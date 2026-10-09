"""Full schema-3 CONFIG byte and pre-APC unit conjunct examples; no origin claim."""

import copy

from formal.reference.profile_source import configuration_units as config
from formal.reference.profile_source.configuration_vectors import bytes_term, value_term
from formal.reference.profile_source.test_arithmetic_units import SCHEMA, configuration


def generate():
    value = configuration()
    raw = config.encode(value)
    bs = bytes_term
    source = value["apply_arithmetic_profile_source"].encode("ascii")
    validators = "[" + ",".join(bs(v.encode()) for v in value["validator_ids"]) + "]"
    storage = value["availability_policy"]["storage_binding"]
    definitions = [
        "import ProfileConfigurationUnits",
        "open DeltaReduce.ProfileSource.ConfigurationUnits",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 40000",
        "set_option maxHeartbeats 12000000",
        "namespace ConfigUnitVectors",
        f"def value : DeltaReduce.NativePolicyCodec.Value := {value_term(value)}",
        f"def raw : DeltaReduce.NativeReceiptBytes.Bytes := {bs(raw)}",
        f"def source : DeltaReduce.NativeReceiptBytes.Bytes := {bs(source)}",
        "def parent : Parent := ⟨⟨"
        + bs(value["parent_checkpoint_id"].encode())
        + ","
        + bs(("sha256:" + "4" * 64).encode())
        + ",[],0⟩,"
        + bs(SCHEMA.encode())
        + ",⟨1,4⟩,⟨1,4⟩⟩",
        "def enrollment : DeltaReduce.ProfileSource.Configuration.Enrollment := ⟨"
        + ",".join(
            (
                bs(value["formal_semantics_id"].encode()),
                bs(value["validator_epoch_id"].encode()),
                validators,
                bs(storage["storage_epoch_id"].encode()),
                bs(storage["storage_registry_id"].encode()),
            )
        )
        + "⟩",
    ]
    assertions = [
        "example : encodeFrame value = some raw := by decide +kernel",
        "example : decodeFrame raw = some value := frameEncoded (by decide +kernel)",
        "example : (check raw).map Bound.source = some source := by decide +kernel",
        "example : (admit enrollment parent raw).isSome = true := by decide +kernel",
        "example : admit enrollment {parent with modelQuantum := ⟨1,2⟩} "
        "raw = none := by decide +kernel",
        "example : admit enrollment {parent with optimizerQuantum := ⟨1,2⟩} "
        "raw = none := by decide +kernel",
        'example : admit enrollment {parent with schema := ascii "wrong"} '
        "raw = none := by decide +kernel",
        "example : admit enrollment {parent with current := {parent.current with height := 1}} "
        "raw = none := by decide +kernel",
        'example : admit {enrollment with epoch := ascii "wrong"} '
        "parent raw = none := by decide +kernel",
        "example : decodeFrame (raw ++ [32]) = none := by decide +kernel",
        "example : DeltaReduce.ProfileSource.Configuration.decodeFrame "
        "raw = none := by decide +kernel",
    ]
    # These are newly constructed malformed inputs, never relabeled originals.
    malformed = raw.replace(b"hard_deadline_tick", b"soft_deadline_tick", 1)
    assertions.append(f"example : decodeFrame {bs(malformed)} = none := by decide +kernel")
    old_version = copy.deepcopy(value)
    old_version["schema_version"] = "2.0.0"
    from formal.reference.profile_source import configuration as common

    payload = common.encode_value(old_version)
    wrong = common.HEADER + len(payload).to_bytes(4, "big") + payload
    assertions.append(f"example : check {bs(wrong)} = none := by decide +kernel")
    return definitions, assertions
