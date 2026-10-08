"""Exact original CONFIG/S0/P0 header vectors, not a complete source history."""

from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_source import policy
from formal.reference.profile_source import capsule_binding as native
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source.configuration_vectors import bytes_term, value_term
from formal.reference.profile_source.test_input_capsule import InputCapsuleTests


def policy_term(shape, value):
    if shape in ("u32", "u64", "i64", "bool"):
        return f"(.number {int(value) % 2**64})"
    if shape == "text":
        return f"(.text {bytes_term(value.encode('ascii'))})"
    if (vector := policy.vector_shape(shape)) is not None:
        return "(.items [" + ",".join(policy_term(vector[0], x) for x in value) + "])"
    result = ".end"
    for name, kind in reversed(policy.SCHEMAS[shape]):
        result = f"(.pair {policy_term(kind, value[name])} {result})"
    return result


def generate():
    InputCapsuleTests.setUpClass()
    f = InputCapsuleTests()
    f.setUp()
    configuration = cfg.decode(f.input.config)
    state = native.read_state(f.initial, f.boot.formal_semantics_id)
    p = policy.decode(f.policy)
    table = {}

    def hashed(domain, raw):
        preimage = domain.encode() + b"\0" + raw
        table[preimage] = sha256(preimage).digest()

    hashed(cfg.DOMAIN, f.input.config)
    variants = [(state, p, "original_view")]
    later_state = {**state, "view": "2", "durable_sequence": "7"}
    later_policy = deepcopy(p)
    later_policy["snapshot"]["state_id"] = cfg.content_id(
        "deltareduce:003:round-state:v1", native.envelope(5, later_state)
    )
    variants.append((later_state, later_policy, "later_view_same_configuration"))
    lines = [
        "import ProfileNativeHeader",
        "open DeltaReduce.ProfileSource.NativeHeader",
        "open DeltaReduce.NativeReceiptBytes (Bytes)",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 20000",
        "set_option maxHeartbeats 4000000",
        "namespace NativeHeaderVectors",
        f"def configRaw : Bytes := {bytes_term(f.input.config)}",
        f"def actor : Bytes := {bytes_term(f.actor.encode())}",
        "def enrolled : DeltaReduce.ProfileSource.Configuration.Enrollment := ⟨"
        + ",".join(
            (
                bytes_term(configuration["formal_semantics_id"].encode()),
                bytes_term(configuration["validator_epoch_id"].encode()),
                "["
                + ",".join(bytes_term(v.encode()) for v in configuration["validator_ids"])
                + "]",
                bytes_term(
                    configuration["availability_policy"]["storage_binding"][
                        "storage_epoch_id"
                    ].encode()
                ),
                bytes_term(
                    configuration["availability_policy"]["storage_binding"][
                        "storage_registry_id"
                    ].encode()
                ),
            )
        )
        + "⟩",
    ]
    originals = []
    for i, (s, p0, name) in enumerate(variants):
        raw_s, raw_p = native.envelope(5, s), policy.encode(p0)
        hashed("deltareduce:003:round-state:v1", raw_s)
        lines.extend(
            (
                f"def sv{i} : DeltaReduce.NativePolicyCodec.Value := {value_term(s)}",
                f"def pv{i} : DeltaReduce.NativePolicyCodec.Value := {policy_term('policy', p0)}",
                f"def sr{i} : Bytes := {bytes_term(raw_s)}",
                f"def pr{i} : Bytes := {bytes_term(raw_p)}",
                f"example : stateBytes sv{i} = some sr{i} := by decide +kernel",
                f"example : policyBytes pv{i} = some pr{i} := by decide +kernel",
            )
        )
        originals.append(
            {
                "case": name,
                "config": f.input.config.hex(),
                "state": raw_s.hex(),
                "policy": raw_p.hex(),
            }
        )
    bad_policy = {**p, "hard_deadline_tick": p["hard_deadline_tick"] + 1}
    bad_raw = policy.encode(bad_policy)
    lines.extend(
        (
            f"def bad : DeltaReduce.NativePolicyCodec.Value := {policy_term('policy', bad_policy)}",
            f"def badRaw : Bytes := {bytes_term(bad_raw)}",
            "def hash (raw : Bytes) : Bytes :=",
            *(
                f"  if raw = {bytes_term(preimage)} then {bytes_term(digest)} else"
                for preimage, digest in table.items()
            ),
            "  []",
            "example : (check hash enrolled actor configRaw sr0 pr0 sv0 pv0).isSome = true := "
            "by decide +kernel",
            "example : (check hash enrolled actor configRaw sr1 pr1 sv1 pv1).isSome = true := "
            "by decide +kernel",
            "example : (check hash enrolled actor configRaw sr0 badRaw sv0 bad).isNone = true := "
            "by decide +kernel",
            "example : (check hash enrolled actor configRaw sr0 pr0 sv0 bad).isNone = true := "
            "by decide +kernel",
            'example : (check hash enrolled (ascii "foreign") configRaw sr0 pr0 sv0 pv0).isNone = '
            "true := by decide +kernel",
            "end NativeHeaderVectors",
        )
    )
    originals.append({"case": "changed_deadline", "policy": bad_raw.hex()})
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_PARTIAL_HEADER_NOT_PRODUCTION_SNAPSHOT",
        "originals": originals,
        "hash_table": {raw.hex(): digest.hex() for raw, digest in table.items()},
    }
