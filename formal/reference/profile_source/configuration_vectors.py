"""Kernel checks of original full configuration bytes, with no finality premise."""

from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source.test_configuration import ConfigurationTests


def bytes_term(raw):
    return "[" + ",".join(map(str, raw)) + "]"


def value_term(value):
    if type(value) is str:
        return f"(.text {bytes_term(value.encode('ascii'))})"
    if type(value) is int:
        return f"(.number {value})"
    if type(value) is list:
        return "(.items [" + ",".join(map(value_term, value)) + "])"
    if type(value) is dict:
        result = ".end"
        for _, item in reversed(sorted(value.items())):
            result = f"(.pair {value_term(item)} {result})"
        return result
    raise TypeError("Not an existing DRC1 configuration value")


def generate():
    ConfigurationTests.setUpClass()
    fixture = ConfigurationTests()
    lines = [
        "import ProfileConfiguration",
        "open DeltaReduce.ProfileSource.Configuration",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 20000",
        "set_option maxHeartbeats 4000000",
        "namespace OriginalConfigVectors",
    ]
    originals = []
    for i, name in enumerate(("OMIT_UNAVAILABLE", "ABORT_ON_INCOMPLETE")):
        body = fixture.body()
        body["availability_policy"]["close_policy"] = name
        raw = cfg.encode(body)
        originals.append({"policy": name, "original_hex": raw.hex()})
        lines.extend(
            [
                f"def value{i} : DeltaReduce.NativePolicyCodec.Value := {value_term(body)}",
                f"def raw{i} : DeltaReduce.NativeReceiptBytes.Bytes := {bytes_term(raw)}",
                f"example : encodeFrame value{i} = some raw{i} := by decide",
                f"example : decodeFrame raw{i} = some value{i} := frameEncoded (by decide)",
                f'example : closePolicy raw{i} = some (ascii "{name}") := by decide',
                f'example : (check raw{i}).map Body.policy = some (ascii "{name}") := by decide',
                f"def enrolled{i} : Enrollment := "
                + "⟨"
                + ",".join(
                    (
                        bytes_term(body["formal_semantics_id"].encode()),
                        bytes_term(body["validator_epoch_id"].encode()),
                        "[" + ",".join(bytes_term(v.encode()) for v in body["validator_ids"]) + "]",
                        bytes_term(
                            body["availability_policy"]["storage_binding"][
                                "storage_epoch_id"
                            ].encode()
                        ),
                        bytes_term(
                            body["availability_policy"]["storage_binding"][
                                "storage_registry_id"
                            ].encode()
                        ),
                    )
                )
                + "⟩",
                f"example : (checkEnrolled enrolled{i} raw{i}).map Body.policy = "
                f'some (ascii "{name}") := by decide',
                f'example : checkEnrolled {{enrolled{i} with epoch := ascii "wrong"}} raw{i} '
                "= none := by decide",
                f"example : decodeFrame (raw{i} ++ [32]) = none := by decide",
            ]
        )
        # Change an original key to a duplicate same-length key; the decoder
        # must reject before there can be first/last-wins semantics.
        damaged = raw.replace(b"hard_deadline_tick", b"soft_deadline_tick", 1)
        lines.append(f"example : decodeFrame {bytes_term(damaged)} = none := by decide")
    lines.append("end OriginalConfigVectors")
    return "\n".join(lines) + "\n", originals
