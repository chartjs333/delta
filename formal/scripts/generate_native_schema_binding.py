"""Retain original schema bytes/shapes/aliases; hash adapters remain synthetic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import BOUNDARY_PIN, fixture_store
from native_source_artifacts import canonical, require, resolve_q_source, schema_segments

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeSchemaVectors.lean"
TARGET = ROOT / "formal/proposals/native-schema-binding-vectors.json"


def generate() -> dict:
    store, golden, _ = fixture_store()
    source = resolve_q_source(store, golden["manifest"]["content_id"])
    identity = source.manifest["parameter_schema_id"]
    raw = store[identity]
    require(raw == canonical(source.schema), "ORIGINAL_SCHEMA_PREIMAGE")
    doc = source.schema
    segments = schema_segments(doc)
    lines = [
        "import DeltaReduce.NativeSchemaBinding",
        "import DeltaReduce.NativeScaleVectors",
        "namespace DeltaReduce.NativeSchemaVectors",
        "open NativeReceiptBytes (Bytes)",
        "open NativeVoteBytes (ascii)",
        "open NativeSchemaBinding",
        "set_option maxRecDepth 4000",
        "set_option maxHeartbeats 1000000",
        "",
    ]
    pool: dict[str, int] = {}
    proofs: set[tuple[str, str]] = set()

    def val(value: object, numeric: bool = False) -> tuple[str, str]:
        text = str(value)
        if text not in pool:
            pool[text] = len(pool)
            lines.append(
                f"def bytes{pool[text]} : Bytes := [" + ",".join(map(str, text.encode())) + "]"
            )
        n = pool[text]
        kind = "decimal" if numeric else "text"
        if (kind, text) not in proofs:
            proofs.add((kind, text))
            predicate = "NativeVoteBytes.DecimalValid" if numeric else "NativeQJson.TextValid"
            lines.append(f"theorem {kind}{n} : {predicate} bytes{n} := by decide")
        return f"bytes{n}", f"{kind}{n}"

    tensors, wires, syntax, checks = [], [], [], []
    for i, p in enumerate(doc["parameters"]):
        dtype, name = val(p["logical_dtype"]), val(p["name"])
        dimensions = [val(x, True) for x in p["shape"]]
        shape = "[" + ",".join(d[0] for d in dimensions) + "]"
        actual = "[" + ",".join(map(str, p["shape"])) + "]"
        wires.append(f"parameter{i}")
        tensors.append(f"tensor{i}")
        syntax.append(f"parameterSyntax{i}")
        checks.append(f"tensorChecks{i}")
        lines += [
            f"def parameter{i} : NativeSchemaBytes.Parameter := "
            f"⟨{dtype[0]},{name[0]},{shape},{str(p['trainable']).lower()}⟩",
            f"theorem parameterSyntax{i} : NativeSchemaBytes.ParameterSyntax parameter{i} := by",
            f"  refine ⟨{dtype[1]},{name[1]},by decide,?_⟩",
            (f"  change ∀ d ∈ {shape}, NativeVoteBytes.DecimalValid d"),
            ("  simp only [List.forall_mem_cons]" if dimensions else "  simp"),
            ("  exact ⟨" + ",".join(d[1] for d in dimensions) + ",by simp⟩" if dimensions else ""),
            f"def tensor{i} : Tensor := ⟨parameter{i},{actual}⟩",
            f"theorem tensorChecks{i} : TensorChecks tensor{i} := by decide",
        ]
    aliases = []
    alias_syntax = []
    for key, value in doc["tied_aliases"].items():
        k, v = val(key), val(value)
        aliases.append(f"({k[0]},{v[0]})")
        alias_syntax.append(f"⟨{k[1]},{v[1]}⟩")
    policy, version = val(doc["frozen_omission_policy"]), val(doc["schema_version"])
    params = "[" + ",".join(wires) + "]"
    ts = "[" + ",".join(tensors) + "]"
    lines += [
        f"def wire : NativeSchemaBytes.Wire := ⟨{policy[0]},{params},{version[0]},"
        "[" + ",".join(aliases) + "]⟩",
        "theorem parametersSyntax : ∀ p ∈ wire.parameters, NativeSche"
        "maBytes.ParameterSyntax p := by",
        f"  change ∀ p ∈ {params}, NativeSchemaBytes.ParameterSyntax p",
        "  simp only [List.forall_mem_cons]",
        "  exact ⟨" + ",".join(syntax) + ",by simp⟩",
        "theorem aliasesSyntax : ∀ a ∈ wire.aliases, NativeSchemaBytes.AliasSyntax a := by",
        "  simp only [wire,List.forall_mem_cons]",
        "  exact ⟨" + ",".join(alias_syntax) + ",by simp⟩",
        "theorem wireSyntax : NativeSchemaBytes.Syntax wire :=",
        f"  ⟨{policy[1]},by decide,parametersSyntax,{version[1]},by decide,aliasesSyntax⟩",
        "def original : Bytes := [" + ",".join(map(str, raw)) + "]",
        f"theorem originalLength : original.length = {len(raw)} := rfl",
        "theorem originalEncoded : NativeSchemaBytes.encode wire = original := rfl",
        "theorem decodedWire : NativeSchemaBytes.decode original = some wire := by",
        "  rw [← originalEncoded]",
        "  apply NativeSchemaBytes.decodeEncoded wire wireSyntax",
        "  rw [originalEncoded,originalLength]; decide",
        f"def schema : Schema := ⟨wire,{ts}⟩",
        "theorem allTensors : ∀ p ∈ schema.parameters, TensorChecks p := by",
        f"  change ∀ p ∈ {ts}, TensorChecks p",
        "  simp only [List.forall_mem_cons]",
        "  exact ⟨" + ",".join(checks) + ",by simp⟩",
        "theorem schemaSource : Source wire schema :=",
        "  ⟨rfl,tensorsFromChecks schema.parameters allTensors,by decide⟩",
        "theorem decodedSchema : decode original = some schema :=",
        "  decodedFromComponents decodedWire (interpretFromSource schemaSource)",
        f"def schemaId : Bytes := ascii {json.dumps(identity)}",
        "/-- TWO-PREIMAGE SYNTHETIC ADAPTER, NOT VERIFIED SHA OR PRODUCER AUTHORITY. -/",
        "def fixtureHash (raw : Bytes) : Bytes :=",
        "  if raw = original then schemaId else NativeScaleVectors.fixtureHash raw",
        "theorem schemaHash : fixtureHash original = schemaId := by simp [fixtureHash]",
        "theorem scaleHash : fixtureHash (NativeScaleBinding.hashInpu"
        "t NativeScaleVectors.original) =",
        "    NativeScaleVectors.originalId := by",
        "  have different : NativeScaleBinding.hashInput NativeScaleV"
        "ectors.original ≠ original := by",
        "    intro same",
        "    have len := congrArg List.length same",
        "    simp [NativeScaleBinding.hashInput,ascii,",
        "      NativeScaleVectors.originalLength,originalLength] at len",
        "  simp [fixtureHash,different,NativeScaleVectors.originalHash]",
        "theorem scaleLinks : Links fixtureHash original schema NativeScaleVectors.table :=",
        "  ⟨schemaHash,by decide,by decide⟩",
        "theorem boundTable : bind fixtureHash original NativeScaleVectors.original =",
        "    some ⟨schema,NativeScaleVectors.table⟩ :=",
        "  bindFromSource ⟨decodedSchema,NativeScaleVectors.decodedTable,scaleLinks⟩",
        "theorem frozenStillPresent : tensor2 ∈ schema.parameters := by decide",
        "theorem frozenExcluded : tensor2 ∉ schema.included := by decide",
        "theorem scalarSize : tensor2.count = 1 := rfl",
        "theorem orderedIncluded : schema.included = [tensor0,tensor1] := by decide",
        "theorem exactTotal : schema.total = 36 := rfl",
    ]
    for i in range(len(source.rows)):
        lines += [
            f"theorem scaleQ{i} : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original",
            f"    NativeQBytesVectors.frame{i} = some NativeScaleVectors.bound{i} := by",
            "  apply NativeScaleBinding.bindFromSource",
            f"  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined{i},",
            "    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩",
            f"theorem joined{i} : bindQ fixtureHash original NativeScaleVectors.original",
            f"    NativeQBytesVectors.frame{i} = some ⟨schema,NativeScaleVectors.bound{i}⟩ :=",
            f"  qFromSource ⟨decodedSchema,scaleQ{i},scaleLinks⟩",
        ]
    cases = {
        "zeroDimension": 'tensor {parameter0 with shape := [ascii "0"]} = none',
        "negativeDimension": 'tensor {parameter0 with shape := [ascii "-1"]} = none',
        "leadingZeroDimension": 'tensor {parameter0 with shape := [ascii "04"]} = none',
        "productOverflow": 'tensor {parameter0 with shape := [ascii "1073741824",ascii "'
        '2"]} = none',
        "rankOverflow": 'tensor {parameter0 with shape := List.replicate 33 (ascii "1")} = none',
        "wrongDtype": 'tensor {parameter0 with dtype := ascii "int16"} = none',
        "badFirstName": 'tensor {parameter0 with name := ascii ".weight"} = none',
        "badRestName": 'tensor {parameter0 with name := ascii "a/b"} = none',
        "schemaName256": "NameValid (List.replicate 256 97)",
        "nativeName256Rejects": "¬ NativeQHeader.Token (List.replicate 256 97)",
        "schemaName257Rejects": "¬ NameValid (List.replicate 257 97)",
        "wrongVersion": '¬ Checks {schema with wire := {wire with version := ascii "2.0.0"}}',
        "wrongPolicy": '¬ Checks {schema with wire := {wire with policy := ascii "OMIT_ALL"}}',
        "duplicateParameter": "¬ Checks {schema with parameters := [tensor0,tensor0,tensor1]}",
        "reorderedParameters": "¬ Checks {schema with parameters := [tensor1,tensor0,tensor2]}",
        "missingAliasOwner": "¬ Checks {schema with wire := {wire with aliases := [(ascii "
        '"head",ascii "missing")]}}',
        "aliasIsParameter": "¬ Checks {schema with wire := {wire with aliases := [(parame"
        "ter0.name,parameter1.name)]}}",
        "duplicateAlias": "¬ Checks {schema with wire := {wire with aliases := wire.ali"
        "ases ++ wire.aliases}}",
        "reorderedAliases": "¬ Checks {schema with wire := {wire with aliases := [(ascii "
        '"z",parameter0.name),(ascii "a",parameter1.name)]}}',
        "includeFrozenChangesRows": "¬ Links fixtureHash original {schema with wire := {wire with"
        ' policy := ascii "INCLUDE_ALL"}} NativeScaleVectors.table',
        "changedShape": "¬ Links fixtureHash original {schema with parameters := [ten"
        "sor0,{tensor1 with dims := [4,4]},tensor2]} NativeScaleVecto"
        "rs.table",
        "changedSameSizeName": "¬ Links fixtureHash original {schema with parameters := [{te"
        'nsor0 with wire := {parameter0 with name := ascii "decoder.o'
        'ther"}},tensor1,tensor2]} NativeScaleVectors.table',
        "extraScaleRow": "¬ Links fixtureHash original schema {NativeScaleVectors.tabl"
        "e with segments := NativeScaleVectors.table.segments ++ [Nat"
        "iveScaleVectors.segment0]}",
        "missingHash": "¬ Links (fun _ => []) original schema NativeScaleVectors.table",
        "emptyBytes": "decode [] = none",
        "wrongShapeDelimiter": 'NativeSchemaBytes.readShape (ascii "4}") = none',
        "trailingShapeComma": 'NativeSchemaBytes.readShape (ascii "4,]") = none',
        "quotedTrainable": 'NativeSchemaBytes.readBool (ascii ""true"") = none',
        "numericTrainable": 'NativeSchemaBytes.readBool (ascii "1") = none',
        "booleanDimension": 'NativeSchemaBytes.readShape (ascii "true]") = none',
        "emptyShape": 'NativeSchemaBytes.readShape (ascii "]") = some ([],[])',
        "extraAliasComma": 'NativeSchemaBytes.readAliases (ascii ""a":"b",}") = none',
    }
    cases["quotedTrainable"] = (
        f"NativeSchemaBytes.readBool (ascii {json.dumps(chr(34) + 'true' + chr(34))}) = none"
    )
    alias_trailing = json.dumps(chr(34) + "a" + chr(34) + ":" + chr(34) + "b" + chr(34) + ",}")
    cases["extraAliasComma"] = f"NativeSchemaBytes.readAliases (ascii {alias_trailing}) = none"
    cases["allFrozen"] = (
        "¬ Checks {schema with wire := {wire with aliases := []}, parameters := [tensor2]}"
    )
    cases["includeAllHasScalar"] = (
        '({schema with wire := {wire with policy := ascii "INCLUDE_ALL"}} : Schema).total = 37'
    )
    cases = {
        name: prop.replace("Links fixtureHash original", "Links (fun _ => schemaId) []")
        for name, prop in cases.items()
    }
    for name, prop in cases.items():
        lines.append(f"theorem {name} : {prop} := by decide")
    lines += [
        "theorem changedPayloadStillJoins : bindQ fixtureHash original NativeScaleVectors.original",
        "    (NativeQBytes.encodeFrame NativeQBytesVectors.header0 [2,0,254,255,0,0,4,0]) =",
        "    some ⟨schema,⟨NativeScaleVectors.table,NativeScaleVectors.changedBlock,",
        "      NativeScaleVectors.segment0⟩⟩ := by",
        "  apply qFromSource",
        "  refine ⟨decodedSchema,?_,scaleLinks⟩",
        "  apply NativeScaleBinding.bindFromSource",
        "  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVector"
        "s.changedPayloadWithOldShaStillAccepted,",
        "    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩",
        "end DeltaReduce.NativeSchemaVectors",
        "",
    ]
    LEAN.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    result = {
        "version": "deltareduce.original-schema-scale-q.v1-candidate",
        "scope": "ORIGINAL_SCHEMA_BYTES_SHAPES_OMISSION_ALIASES_WITH_UNVERIFIED_HASH_ADAPTER",
        "source_boundary_sha256": BOUNDARY_PIN,
        "schema_id": identity,
        "schema_bytes_hex": raw.hex(),
        "schema_value": doc,
        "segments": segments,
        "rows": list(source.rows),
        "small_kernel_cases": [*cases, "changedPayloadStillJoins"],
        "formal_go": False,
        "native_execution": False,
        "sha_implementation_proved": False,
        "hash_adapter_authenticated": False,
        "plan_manifest_admission_proved": False,
        "loaded_row_composition_proved": False,
        "native_recovery_proved": False,
        "lean_sha256": hashlib.sha256(LEAN.read_bytes()).hexdigest(),
    }
    write_canonical_json(TARGET, result)
    return result


if __name__ == "__main__":
    result = generate()
    print(
        json.dumps(
            {
                "parameters": len(result["schema_value"]["parameters"]),
                "segments": len(result["segments"]),
                "small_cases": len(result["small_kernel_cases"]),
            }
        )
    )
