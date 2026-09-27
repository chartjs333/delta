"""Pin full SCHEMA/Q_SHARD byte images, retaining original source components."""

from __future__ import annotations

import json
import re
from pathlib import Path

import generate_native_available_q as original
import generate_native_vector_projection as source
from formal_artifacts import sha256_file, write_canonical_json
from native_vector_projection import project_inputs

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeVectorArtifactVectors.lean"
TARGET = ROOT / "formal/proposals/native-vector-artifacts-lean-vectors.json"


def quote(value):
    return json.dumps(value, ensure_ascii=True)


def ints(values):
    return "[" + ",".join(str(v) for v in values) + "]"


def generate():
    original.source_blobs()
    p = project_inputs(*source.source_fixture(False))
    schema = p.schema
    labels = "[" + ",".join(map(quote, schema["coordinates"])) + "]"
    shards = (
        "["
        + ",".join(f"⟨{quote(s['id'])},{s['offset']},{s['length']}⟩" for s in schema["shards"])
        + "]"
    )
    lines = [
        "import DeltaReduce.NativeVectorJoin",
        "import DeltaReduce.NativeVectorArithmeticVectors",
        "",
        "/-! Original layout/Q component bytes; row metadata remains a synthetic",
        "component fixture. No complete run or authenticated source is instantiated. -/",
        "set_option maxRecDepth 4096",
        "namespace DeltaReduce.NativeVectorArtifactVectors",
        "open NativeBinding NativeVectorLayout NativeVectorArtifacts",
        "def plan := NativeShardPlanVectors.bound",
        "def layout : Layout := ⟨plan,locations plan.inputs.schema⟩",
        "theorem small : Small plan := by decide",
        "theorem layoutChecks : LayoutChecks plan layout.positions := by decide",
        "theorem originalLayout : construct plan = some layout := "
        "constructFromChecks small layoutChecks",
        f"theorem coordinateNames : layout.coordinates = {labels} := by decide",
        f"theorem shardRanges : layout.shards = {shards} := by decide",
        "theorem totalCoordinates : layout.positions.length = 36 := by decide",
        "theorem noFrozen : layout.positions.all (fun l => l.parameter != NativeVoteBytes.ascii",
        '    "frozen.scale") = true := by decide',
        "theorem noAliasCoordinate : layout.positions.all "
        "(fun l => l.parameter != NativeVoteBytes.ascii",
        '    "lm_head.weight") = true := by decide',
        "theorem originalMetadata : layout.source.inputs.schema = "
        "NativeSchemaVectors.schema := rfl",
        "theorem tenDigits : [digits 0,digits 9,digits 10,digits 4095] =",
        '    ["0000000000","0000000009","0000000010","0000004095"] := by decide',
        'theorem namingConflict : ¬ ([coordinate (asciiBytes "a") 0,'
        'coordinate (asciiBytes "a.b") 0]).Pairwise (· < ·) := by decide',
        "theorem tooLong : validIdentifier (coordinate (List.replicate 118 97) 0) "
        "= false := by decide",
        "theorem nonAscii : validIdentifier (text [255]) = false := by decide",
        "theorem wrongGlobal : ¬ LayoutChecks plan",
        "    ({ (layout.positions[0]) with global := 1 } :: layout.positions.tail) := by decide",
        "theorem reversedPositions : ¬ LayoutChecks plan layout.positions.reverse := by decide",
        "theorem missingCoordinate : ¬ LayoutChecks plan layout.positions.tail := by decide",
        "theorem duplicateCoordinate : ¬ LayoutChecks plan "
        "(layout.positions.take 1 ++ layout.positions.dropLast) := by decide",
        "theorem wrongShape : ¬ LayoutChecks {plan with plan := "
        "{plan.plan with entries := plan.plan.entries.reverse}}",
        "    layout.positions := by decide",
    ]
    raw_schema = p.artifacts[p.schema_ref["id"]]
    # Decimal/string encoders are checked on complete fixed byte arrays, with
    # symbolic array assembly for the larger schema instead of one huge decide.
    for i, label in enumerate(schema["coordinates"]):
        lines += [
            f"theorem labelBytes{i} : quotedBytes (asciiBytes {quote(label)}) = "
            f"{ints(json.dumps(label).encode())} := by decide"
        ]
    for i, s in enumerate(schema["shards"]):
        data = json.dumps(s, sort_keys=True, separators=(",", ":")).encode()
        lines += [
            f"theorem shardBytes{i} : encodeShard ⟨{quote(s['id'])},{s['offset']},{s['length']}⟩ = "
            f"{ints(data)} := by decide"
        ]
    simp_names = [f"labelBytes{i}" for i in range(len(schema["coordinates"]))]
    simp_names += [f"shardBytes{i}" for i in range(len(schema["shards"]))]
    lines += [
        f"def schemaBytes : Bytes := {ints(raw_schema)}",
        "theorem schemaExact : encodeSchema layout = schemaBytes := by",
        "  simp only [encodeSchema,coordinateNames,shardRanges,"
        "List.map_cons,List.map_nil,Function.comp_apply,",
        "    " + ",".join(simp_names) + "]",
        "  rfl",
        "set_option maxRecDepth 16384 in",
        "theorem schemaLength : schemaBytes.length = 1338 := rfl",
        f"def schemaRef : Ref := ⟨{ints(bytes.fromhex(p.schema_ref['id'][7:]))},.schema,1338⟩",
        "theorem distinctHashPreimages : artifactHashInput schemaBytes "
        "≠ NativeSchemaVectors.original := by",
        "  intro h; have bad := congrArg List.head? h; revert bad; decide",
    ]
    cases = []
    for i, a in enumerate(p.assignments):
        c = a["contributions"][0]
        raw = p.artifacts[c["q"]["id"]]
        q = json.loads(raw)["payload"]
        lines += [
            f"def slice{i} : NativeVectorContext.Slice :=",
            f"  let s := NativeVectorArithmeticVectors.sample 1 1 NativeScaleVectors.bound{i}",
            "  { s with source := { s.source with term := { s.source.term with source :=",
            "    { s.source.term.source with member := { s.source.term.source.member with input :=",
            "      { s.source.term.source.member.input with",
            f"        ticket := asciiBytes {quote(q['ticket'])}, "
            f"domain := asciiBytes {quote(q['domain'])} }} }} }} }} }} }}",
            f"def q{i} : QShard := ⟨{quote(q['ticket'])},{quote(q['domain'])},"
            f"{quote(q['shard'])},schemaRef,",
            f"    ⟨{q['quantum'][0]},{q['quantum'][1]}⟩,{ints(q['values'])}⟩",
            f"theorem qSource{i} : qValue schemaRef slice{i} = q{i} := by decide",
            f"theorem qChecks{i} : QChecks schemaRef slice{i} := by decide",
            f"def qBytes{i} : Bytes := {ints(raw)}",
            f"theorem qExact{i} : encodeQ q{i} = qBytes{i} := by decide",
            f"theorem qImage{i} : encodeQ (qValue schemaRef slice{i}) = qBytes{i} "
            f":= by rw [qSource{i}]; exact qExact{i}",
            f"theorem qFullWidth{i} : (qValue schemaRef slice{i}).values.length "
            f"= {len(q['values'])} := by decide",
        ]
        cases.append({"payload": q, "bytes": raw.hex(), "ref": c["q"]})
    lines += [
        "theorem wrongSchemaKind : ¬ QChecks {schemaRef with kind := .model} slice0 := by decide",
        "theorem wrongHashLength : ¬ QChecks {schemaRef with id := []} slice0 := by decide",
        "theorem emptyVector : ¬ QChecks schemaRef {slice0 with block :=",
        "    (NativeVectorArithmeticVectors.withValues slice0.block []) } := by decide",
        "theorem int64Overflow : ¬ QChecks schemaRef {slice0 with block :=",
        "    (NativeVectorArithmeticVectors.withValues slice0.block "
        "[9223372036854775808]) } := by decide",
        "theorem rawBodyChanges : encodeQ {q0 with values := [2,-2,0,4]} ≠ qBytes0 := by decide",
        "end DeltaReduce.NativeVectorArtifactVectors",
        "",
    ]
    source_text = "\n".join(lines)
    LEAN.write_text(source_text, encoding="utf-8", newline="\n")
    write_canonical_json(
        TARGET,
        {
            "scope": "ORIGINAL_COMPONENT_BYTES_NOT_AUTHENTICATED_NATIVE_SOURCE",
            "source_fixture_sha256": sha256_file(
                ROOT / "formal/proposals/native-vector-projection-vectors.json"
            ),
            "schema": schema,
            "schema_bytes": raw_schema.hex(),
            "schema_ref": p.schema_ref,
            "locations": list(p.locations),
            "q_cases": cases,
            "kernel_theorems": re.findall(r"^theorem (\w+)", source_text, re.M),
            "formal_go": False,
            "native_execution": False,
            "native_export_authenticated": False,
            "whole_source_join_kernel_example": False,
        },
    )


if __name__ == "__main__":
    generate()
    print("Generated complete original layout and five draft Q byte component cases.")
