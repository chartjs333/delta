"""Independent bootstrap/index/floor bytes; synthetic, not lawful native genesis."""

from hashlib import sha256

from formal.reference.profile_source import metadata as m
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.control_vectors import fields
from formal.reference.profile_source.test_metadata import Package, frame, identifier


def generate():
    p = Package()
    activation = p.activate()
    after = {
        **activation,
        "kind": "ANCHOR",
        "ordinal": "2",
        "previous_record_id": m.document_id(m.canonical(activation), "TRUST_RECORD"),
    }
    originals = [p.record, activation, after]
    bads = [
        {**after, "anchor": p.anchor},
        {**after, "anchor": {**after["anchor"], "checkpoint_id": identifier("fork")}},
        {**after, "generation_id": identifier("different-generation")},
    ]
    variants = [*originals, *bads]
    raws = [m.canonical(v) for v in variants]
    all_raw = [p.boot_raw, p.index_raw, *(raw for _, raw in p.artifacts), *raws]
    table = {raw: sha256(raw).digest() for raw in all_raw}
    for kind, raw in [("BOOTSTRAP", p.boot_raw), *(("TRUST_RECORD", raw) for raw in raws)]:
        preimage = m.DOMAINS[kind].encode() + b"\0" + raw
        table[preimage] = sha256(preimage).digest()
    log = b"".join(frame(row) for row in originals)
    names = (
        "runtime_build_id",
        "formal_semantics_id",
        "schema_set_id",
        "signature_codec_id",
        "producer_rules_id",
    )
    pins = "⟨" + ",".join(bs(p.boot[name].encode()) for name in names) + "⟩"
    lines = [
        "import ProfileOrigin",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace OriginVectors",
        f"def pins : Origin.Pins := {pins}",
        f"def known : Origin.Independent := ⟨{bs(sha256(p.boot_raw).digest())},"
        f"{bs(sha256(p.index_raw).digest())},pins⟩",
        f"def bootstrap : Control.Fields := {fields(p.boot)}",
        f"def index : Control.Fields := {fields(p.index)}",
        f"def bootRaw : Bytes := {bs(p.boot_raw)}",
        f"def indexRaw : Bytes := {bs(p.index_raw)}",
        "def store : List Bytes := [" + ",".join(bs(raw) for _, raw in p.artifacts) + "]",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in table.items()),
        "  []",
        "def origin (k : Origin.Independent) := "
        "Origin.bind hash k bootstrap index bootRaw indexRaw store",
        "example : (origin known).map (fun x => (x.source.events.length,x.initialConfiguration))",
        f"  = some (2,{bs(b'configuration')}) := by decide +kernel",
        "example : (origin {known with bootstrapDigest := []}).isNone = true := by decide +kernel",
        "example : (origin {known with indexDigest := []}).isNone = true := by decide +kernel",
        "example : (origin {known with pins := {pins with producers := []}}).isNone = true "
        ":= by decide +kernel",
    ]
    for i, (document, raw) in enumerate(zip(variants, raws, strict=True)):
        kind = {"INIT": "init", "ACTIVATE": "activate", "ANCHOR": "anchor"}[document["kind"]]
        lines.append(f"def f{i} : Origin.FloorInput := ⟨.{kind},{fields(document)},{bs(raw)}⟩")
    lines += [
        f"def trustedLog : Bytes := {bs(log)}",
        "def floor (inputs : List Origin.FloorInput) (raw : Bytes) := do",
        "  let b ← Origin.checkBootstrap hash known bootstrap bootRaw",
        "  Origin.bindFloor hash b inputs raw",
        "example : (floor [f0,f1,f2] trustedLog).map "
        "(fun x => (x.rows.length,x.tip.anchor.height))",
        "  = some (3,2) := by decide +kernel",
        "example : (floor [f0,f1] trustedLog).isNone = true := by decide +kernel",
        "example : (floor [f0,f1,f2] (trustedLog ++ [0])).isNone = true := by decide +kernel",
        "example : (floor [] []).isNone = true := by decide +kernel",
    ]
    for i in range(3):
        bad_raw = frame(p.record) + frame(activation) + frame(bads[i])
        lines += [
            f"example : (floor [f0,f1,f{i + 3}] {bs(bad_raw)}).isNone = true := by decide +kernel",
        ]
    lines.append("end OriginVectors")
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_ORIGINAL_METADATA_NOT_LAWFUL_GENESIS_OR_APPLY_QC",
        "original_bootstrap": p.boot_raw.hex(),
        "original_index": p.index_raw.hex(),
        "original_artifacts": {key: raw.hex() for key, raw in p.artifacts},
        "original_trusted_log": log.hex(),
        "floor_payloads": [raw.hex() for raw in raws],
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in table.items()},
    }
