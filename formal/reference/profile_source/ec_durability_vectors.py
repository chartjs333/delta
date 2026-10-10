"""Exact synthetic EC companion bytes + independent Lean transition cases.

SHA256 preimages/digests are explicit finite codec inputs, not a proof of hash
collision resistance or producer origin. No native historical evidence claim.
"""

from hashlib import sha256

from formal.reference.profile_source import ec_durability as d
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.test_ec_durability import example


def generate():
    _, args, bound = example()
    c, e, r = bound.candidate, bound.event, bound.record
    prefix = bound.original_prefix
    source_pre = d.SOURCE_DOMAIN + args["bootstrap_id"].encode() + len(prefix).to_bytes(8, "big")
    source_pre += b"".join(
        i.to_bytes(8, "big") + len(raw).to_bytes(4, "big") + raw for i, raw in enumerate(prefix)
    )
    journal_pre = d.JOURNAL_DOMAIN + bound.original_journal_cuts
    preimages = [
        c.prior_policy,
        c.next_policy,
        c.original_state,
        c.certificate,
        e.inputs[4],
        e.original_descriptor,
        source_pre,
        journal_pre,
        d.DOMAIN + r.raw,
    ]
    hashes = {raw: sha256(raw).digest() for raw in preimages}
    lines = [
        "import ProfileEcDurability",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "open EcDurability",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 12000000",
        "namespace EcDurabilityVectors",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(value)} else" for raw, value in hashes.items()),
        "  []",
        "def m : Material := ⟨"
        + ",".join(
            [
                bs(args["bootstrap_id"].encode()),
                bs(e.actor.encode()),
                bs(b"GENESIS"),
                "1",
                str(e.index),
                "[" + ",".join(bs(x) for x in prefix) + "]",
                bs(e.original_descriptor),
                bs(c.prior_policy),
                bs(c.next_policy),
                bs(c.original_state),
                bs(c.certificate),
                bs(e.inputs[4]),
                "[]",
            ]
        )
        + "⟩",
        f"def original : Bytes := {bs(r.original_frame)}",
        f"example : raw hash m = {bs(r.raw)} := by decide",
        f"example : sourcePreimage m.bootstrap m.originals = {bs(source_pre)} := by decide",
        "example : encode hash m = some original := by decide",
        "example : bindOriginal hash m original = some original := by decide",
        "example : bindOriginal hash m (original ++ [0]) = none := by decide",
        "example : bindOriginal hash {m with eventIndex := m.eventIndex + 1} "
        "original = none := by decide",
        "example : bindOriginal hash {m with actor := [120]} original = none := by decide",
        "example : bindOriginal hash {m with originals := m.originals ++ m.originals} "
        "original = none := by decide",
        "-- Small machine words make crash behavior inspectable independently of codec size.",
        "def tx : Transaction := ⟨[1],[2,3],[10],[11],[12]⟩",
        "def start := initial tx [50,51,52]",
        "def advance (s : Machine) (actions : List Action) := "
        "actions.foldl (fun current action => current >>= fun before => "
        "step tx before action) (some s)",
        "example : advance start [.append,.expose] = none := by decide",
        "example : advance start [.append,.commit] = none := by decide",
        "example : (advance start [.append,.barrier,.commit,.expose]).map Machine.exposed "
        "= some [[12]] := by decide",
        "example : advance start [.append,.crash [1,2,3],.recover,.commit] = none := by decide",
        "example : advance start [.append,.crash [1,2,3],.recover,.expose] = none := by decide",
        "example : (advance start [.append,.crash [1,2,3],.recover,.barrier,.commit,.expose])"
        ".map Machine.exposed = some [[12]] := by decide",
        "example : (advance start [.append,.crash [1,99],.recover]).map Machine.volatile "
        "= some [1,99] := by decide",
        "example : (advance start [.append,.crash [1,99],.recover]).map Machine.phase "
        "= some .blocked := by decide",
        "example : (advance start [.append,.barrier,.commit,.expose,.crash [1,2,3],"
        ".recover,.barrier,.commit,.expose]).map Machine.exposed = some [[12],[12]] := by decide",
        "example : (advance start [.append,.barrier,.commit,.expose,.crash [1,2,3],"
        ".recover,.barrier,.commit,.expose]).map Machine.nativeWal = some [50,51,52] := by decide",
        "end EcDurabilityVectors",
    ]
    evidence = {
        "classification": "SYNTHETIC_CODEC_AND_TRANSITION_VECTORS",
        "not_complete_producer_history": True,
        "record_hex": r.raw.hex(),
        "frame_hex": r.original_frame.hex(),
        "record_id": r.id,
        "original_prefix_hex": [x.hex() for x in prefix],
        "source_preimage_hex": source_pre.hex(),
        "journal_preimage_hex": journal_pre.hex(),
        "sha256_preimages": {x.hex(): value.hex() for x, value in hashes.items()},
    }
    return "\n".join(lines) + "\n", evidence
