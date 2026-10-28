"""Full unit-bearing EC + original storage bytes, with synthetic source inputs.

The original descriptor positions are real codec inputs in this vector; they
are not a lawful complete producer or an independently trusted initial state.
"""

from hashlib import sha256

from formal.reference.profile_source import configuration_route as route
from formal.reference.profile_source import ec_durability as d
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.control_vectors import node
from formal.reference.profile_source.ec_finalization_vectors import generate as finalization
from formal.reference.profile_source.test_ec_durability import example


def generate():
    f, args, bound = example(generation=route.UNITS)
    generated, original_ec = finalization(generation=route.UNITS)
    c, e, record = bound.candidate, bound.event, bound.record
    assert original_ec["prior_policy"] == c.prior_policy.hex()
    assert original_ec["results"][0]["next_policy"] == c.next_policy.hex()
    # Reuse only the complete input declarations, not unrelated kernel examples.
    header = generated[: generated.index("example :")]
    header = header.replace("import ProfileUnitFinalization", "import ProfileUnitStorage")
    prefix = bound.original_prefix
    source_pre = d.SOURCE_DOMAIN + args["bootstrap_id"].encode() + len(prefix).to_bytes(8, "big")
    source_pre += b"".join(
        i.to_bytes(8, "big") + len(raw).to_bytes(4, "big") + raw for i, raw in enumerate(prefix)
    )
    preimages = (
        c.prior_policy,
        c.next_policy,
        c.original_state,
        c.certificate,
        e.inputs[4],
        e.original_descriptor,
        source_pre,
        d.JOURNAL_DOMAIN + bound.original_journal_cuts,
        d.DOMAIN + record.raw,
    )
    hashes = {
        bytes.fromhex(raw): bytes.fromhex(value)
        for raw, value in original_ec["sha256_preimages"].items()
    }
    hashes.update((raw, sha256(raw).digest()) for raw in preimages)
    start, end = header.index("def hash "), header.index("def wire0 ")
    # Name each exact literal before constructing the table. One deeply nested
    # expression otherwise exhausts Lean elaboration recursion; every original
    # preimage and digest still participates in the same kernel computation.
    entries = list(hashes.items())
    header = (
        header[:start]
        + "\n".join(
            f"def hashInput{i} : Bytes := {bs(raw)}\ndef hashOutput{i} : Bytes := {bs(value)}"
            for i, (raw, value) in enumerate(entries)
        )
        + "\n"
        + "def hash (raw : Bytes) : Bytes :=\n"
        + "\n".join(f"  if raw = hashInput{i} then hashOutput{i} else" for i in range(len(entries)))
        + "\n  []\n"
        + header[end:]
    )
    store = {
        m.raw_id(raw): raw
        for raw in (f["config_raw"], e.original, *e.inputs, *(row.original_g for row in f["rows"]))
    }
    descriptors = [*prefix, e.original_descriptor]
    lines = [header]
    for position, raw in enumerate(descriptors):
        row = m.load(raw)
        inputs = [store[r["content_id"]] for r in row["input_refs"]]
        lines.append(
            f"def originalEvent{position} : Index.Event := ⟨{position},{node(row)},"
            f"{bs(row['actor_id'].encode())},{bs(row['action_id'].encode())},"
            f"{bs(store[row['original_ref']['content_id']])},"
            "[" + ",".join(bs(x) for x in inputs) + "],"
            "[" + ",".join(row["dependencies"]) + "]⟩"
        )
    events = "[" + ",".join(f"originalEvent{i}" for i in range(len(descriptors))) + "]"
    lines += [
        "-- The enclosing Index.check establishes materialization/origin; this",
        "-- vector qualifies the joined storage conjunct only.",
        "def originalIndex : Index.Bound := ⟨[],.nil,[],[],[],[],",
        f"  ({events}).map Index.Event.descriptor,{events}⟩",
        f"def frame : Bytes := {bs(record.original_frame)}",
        f"def bootId : Bytes := {bs(args['bootstrap_id'].encode())}",
        "def stored := UnitStorage.checkStorage hash enrolled parent actor config state prior sv",
        f"  originals 4 0 bodyId rows originalEvent{e.index} [0] originalIndex",
        "  bootId [] [] [] frame",
        "example : stored.map (fun s => (s.before.header.config.original,",
        "  s.following.header.config.original,s.candidate.update.raw,",
        "  s.candidate.certificate.raw)) =",
        f"  some (config,config,{bs(c.next_policy)},{bs(c.certificate)}) := by decide +kernel",
        "-- These generic theorems qualify non-substitution and no source occurrence",
        "-- collapse for this same full binding, without repeating its large reduction.",
        "example (out : UnitFinalization.Ec) (accepted : stored = some out) :",
        "  UnitState.bind hash enrolled parent actor config state prior sv originals =",
        "    some out.before :=",
        "  (UnitStorage.completeUnitsRetained accepted).1",
        "end EcFinalizationVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_FULL_UNIT_STORAGE_CONJUNCT_NOT_LAWFUL_HISTORY",
        "configuration_generation": route.UNITS.name,
        "original_configuration": f["config_raw"].hex(),
        "prior_policy": c.prior_policy.hex(),
        "next_policy": c.next_policy.hex(),
        "original_state": c.original_state.hex(),
        "certificate": c.certificate.hex(),
        "original_frame": record.original_frame.hex(),
        "original_descriptors": [raw.hex() for raw in descriptors],
        "original_g": [row.original_g.hex() for row in f["rows"]],
        "sha256_preimages": {raw.hex(): value.hex() for raw, value in hashes.items()},
        "source_and_physical_barrier_remain_enclosing_obligations": True,
    }
