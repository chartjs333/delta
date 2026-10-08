"""Original index bytes/order vectors, deliberately not valid native histories."""

from hashlib import sha256

from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import source_prefix
from formal.reference.profile_source.configuration_vectors import bytes_term
from formal.reference.profile_source.control_vectors import fields, node
from formal.reference.profile_source.test_metadata import Package, ref


def generate():
    p = Package()
    first = {**p.event, "action_id": "ACT-MESSAGE-DELIVER"}
    second = {**first, "input_refs": [ref(b"configuration"), ref(b"configuration")]}
    third = {**first, "actor_id": "another-receiver", "dependencies": ["0", "1"]}
    p.index["events"] = [first, second, third]
    raw = m.canonical(p.index)
    m.validate(raw, "SOURCE_INDEX")
    # Materialization alone must retain even malformed protocol payloads. These
    # placeholders cannot pass the enclosing signature/producer checker.
    original_genesis, events = source_prefix._materialize(p.check(), p.index)
    assert original_genesis == b"genesis"
    assert events[0].original == events[1].original == b"delivery"
    assert events[1].inputs == (b"configuration", b"configuration")
    rows = tuple(raw for _, raw in p.artifacts)
    lines = [
        "import ProfileSourceIndex",
        "open DeltaReduce.ProfileSource",
        "open DeltaReduce.ProfileSource.Index",
        "open DeltaReduce.NativeReceiptBytes (Bytes)",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 20000",
        "set_option maxHeartbeats 8000000",
        "namespace OriginalSourceIndexVectors",
        f"def descriptor : Control.Fields := {fields(p.index)}",
        f"def raw : Bytes := {bytes_term(raw)}",
        "def store : List Bytes := [" + ",".join(map(bytes_term, rows)) + "]",
        "def declared : List Control.Node := [" + ",".join(map(node, p.index["artifacts"])) + "]",
        "def origin : Origin := ⟨"
        + ",".join(
            [
                bytes_term(p.context["origin_id"].encode()),
                bytes_term(p.context["validator_epoch_id"].encode()),
                bytes_term(p.context["local_validator_id"].encode()),
                node(p.index["genesis_ref"]),
            ]
        )
        + "⟩",
        "def hash (raw : Bytes) : Bytes :=",
        *(
            f"  if raw = {bytes_term(value)} then {bytes_term(sha256(value).digest())} else"
            for value in rows
        ),
        "  []",
        "example : (check hash origin descriptor raw store).map (fun b => b.events.length) "
        "= some 3 := by decide +kernel",
        "example : (check hash origin descriptor raw []).isNone = true := by decide +kernel",
        'example : (check hash {origin with epoch := ascii "wrong-epoch"} descriptor raw store)'
        ".isNone = true := by decide +kernel",
        "example : (check hash origin descriptor (raw ++ [32]) store).isNone = true "
        ":= by decide +kernel",
    ]
    for i, value in enumerate(p.index["events"]):
        lines.extend(
            [
                f"def descriptor{i} : Control.Node := {node(value)}",
                f"example : (event hash declared store {i} descriptor{i}).map Event.position "
                f"= some {i} := by decide +kernel",
                f"example : (event hash declared store {i} descriptor{i}).map Event.original "
                '= some (ascii "delivery") := by decide +kernel',
            ]
        )
    lines.extend(
        [
            "example : (event hash declared store 1 descriptor1).map Event.inputs "
            '= some [ascii "configuration",ascii "configuration"] := by decide +kernel',
            "example : (event hash declared store 2 descriptor2).map Event.dependencies "
            "= some [0,1] := by decide +kernel",
            "example : (event hash declared store 1 descriptor2).isNone = true "
            ":= by decide +kernel",
        ]
    )
    for value in (
        {**first, "dependencies": ["1"]},
        {**first, "dependencies": ["0", "0"]},
        {**first, "input_refs": [ref(b"not-in-original-inventory")]},
        {**first, "actor_id": ""},
    ):
        lines.append(
            f"example : (event hash declared store 1 {node(value)}).isNone = true "
            ":= by decide +kernel"
        )
    for value in (
        {**ref(b"delivery"), "locator": "../elsewhere"},
        {**ref(b"delivery"), "locator": "dir//file"},
        {**ref(b"delivery"), "schema_id": "SCHEMA-lower-V1"},
        {**ref(b"delivery"), "byte_length": "01"},
    ):
        lines.append(f"example : (reference {node(value)}).isNone = true := by decide +kernel")
    lines.extend(
        [
            "end OriginalSourceIndexVectors",
        ]
    )
    evidence = {
        "kind": "SYNTHETIC_MATERIALIZATION_NOT_PRODUCER_ORIGIN",
        "source_index_hex": raw.hex(),
        "inventory": [value.hex() for value in rows],
        "event_count": 3,
        "repeated_originals": [0, 1, 2],
        "ordered_duplicate_inputs_at": 1,
        "not_established": "genesis legality, actual delivery, signatures, journal ranges, R2.3",
    }
    return "\n".join(lines) + "\n", evidence
