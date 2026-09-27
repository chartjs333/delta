"""Original plan bytes and computed partition; hashes remain synthetic in Lean."""

from __future__ import annotations

import json
from pathlib import Path

from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import BOUNDARY_PIN, fixture_store
from native_source_artifacts import canonical, require, resolve_q_source

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeShardPlanVectors.lean"
TARGET = ROOT / "formal/proposals/native-shard-plan-vectors.json"


def generate() -> dict:
    store, golden, _ = fixture_store()
    source = resolve_q_source(store, golden["manifest"]["content_id"])
    identity = source.manifest["shard_plan_id"]
    raw = store[identity]
    doc = json.loads(raw)
    require(raw == canonical(doc), "PLAN_PREIMAGE")
    lines = [
        "import DeltaReduce.NativeShardPlanBinding",
        "import DeltaReduce.NativeSchemaVectors",
        "namespace DeltaReduce.NativeShardPlanVectors",
        "open NativeReceiptBytes (Bytes)",
        "open NativeVoteBytes (ascii)",
        "open NativeShardPlanBinding",
        "set_option maxRecDepth 6000",
        "set_option maxHeartbeats 1500000",
    ]
    pool = {}

    def val(x, numeric=False):
        key = (str(x), numeric)
        if key not in pool:
            i = len(pool)
            pool[key] = i
            data = list(str(x).encode())
            lines.append(f"def bytes{i} : Bytes := {data}")
            pred = "NativeVoteBytes.DecimalValid" if numeric else "NativeQJson.TextValid"
            lines.append(f"theorem valid{i} : {pred} bytes{i} := by decide")
        i = pool[key]
        return f"bytes{i}", f"valid{i}"

    names = []
    entries = []
    for i, row in enumerate(doc["entries"]):
        values = [
            val(row[k], k != "segment_id")
            for k in [
                "element_count",
                "element_start",
                "ordinal",
                "payload_bytes",
                "segment_id",
                "segment_offset",
            ]
        ]
        names.append(f"entry{i}")
        entries.append(
            f"⟨{row['element_count']},{row['element_start']},{row['ordinal']},"
            f"{row['payload_bytes']},{values[4][0]},{row['segment_offset']}⟩"
        )
        lines += [
            f"def entry{i} : NativeShardPlanBytes.EntryWire := ⟨"
            + ",".join(v[0] for v in values)
            + "⟩",
            f"theorem syntax{i} : NativeShardPlanBytes.EntrySyntax entry{i} := ⟨"
            + ",".join(v[1] for v in values)
            + "⟩",
        ]
    fields = [
        val(doc[k], k in ["target_payload_bytes", "total_elements"])
        for k in [
            "formal_semantics_id",
            "parameter_schema_id",
            "profile_id",
            "scale_table_id",
            "schema_version",
            "target_payload_bytes",
            "total_elements",
            "type_name",
        ]
    ]
    lines += [
        "def wire : NativeShardPlanBytes.Wire := ⟨["
        + ",".join(names)
        + "],"
        + ",".join(v[0] for v in fields)
        + "⟩",
        "theorem wireSyntax : NativeShardPlanBytes.Syntax wire := by",
        "  refine ⟨by decide,?_," + ",".join(v[1] for v in fields) + "⟩",
        "  change ∀ e ∈ [" + ",".join(names) + "], NativeShardPlanBytes.EntrySyntax e",
        "  simp only [List.forall_mem_cons]",
        "  exact ⟨" + ",".join(f"syntax{i}" for i in range(len(names))) + ",by simp⟩",
        "def original : Bytes := [" + ",".join(map(str, raw)) + "]",
        f"theorem originalLength : original.length = {len(raw)} := rfl",
        "theorem originalEncoded : NativeShardPlanBytes.encode wire = original := rfl",
        "theorem decodedWire : NativeShardPlanBytes.decode original = some wire := by",
        "  rw [← originalEncoded]",
        "  apply NativeShardPlanBytes.decodeEncoded wire wireSyntax",
        "  rw [originalEncoded,originalLength]; decide",
        "def plan : Plan := ⟨wire,["
        + ",".join(entries)
        + f"],{doc['target_payload_bytes']},{doc['total_elements']}⟩",
        "theorem interpretedPlan : interpret wire = some plan := by decide",
        "theorem computedPlan : NativeShardPartition.build NativeSchemaVectors.schema",
        "    plan.target = some plan.entries := by decide",
        f"def planId : Bytes := ascii {json.dumps(identity)}",
        "/-- THREE-PREIMAGE SYNTHETIC ADAPTER, NOT SHA OR SOURCE AUTHENTICATION. -/",
        "def fixtureHash (raw : Bytes) : Bytes :=",
        "  if raw = hashInput original then planId else NativeSchemaVectors.fixtureHash raw",
        "theorem planHash : fixtureHash (hashInput original) = planId := by simp [fixtureHash]",
    ]
    for name, expr, result, lemma in [
        (
            "schemaHash",
            "NativeSchemaVectors.original",
            "NativeSchemaVectors.schemaId",
            "NativeSchemaVectors.schemaHash",
        ),
        (
            "scaleHash",
            "NativeScaleBinding.hashInput NativeScaleVectors.original",
            "NativeScaleVectors.originalId",
            "NativeSchemaVectors.scaleHash",
        ),
    ]:
        lines += [
            f"theorem {name} : fixtureHash ({expr}) = {result} := by",
            f"  have different : {expr} ≠ hashInput original := by",
            "    intro same",
            "    have len := congrArg List.length same",
            (
                "    simp [hashInput,ascii,originalLength,"
                "NativeSchemaVectors.originalLength] at len"
                if name == "schemaHash"
                else "    simp [hashInput,NativeScaleBinding.hashInput,ascii,originalLength,"
                "NativeScaleVectors.originalLength] at len"
            ),
            f"  simp [fixtureHash,different,{lemma}]",
        ]
    lines += [
        "def inputs : NativeSchemaBinding.Bound :=",
        "  ⟨NativeSchemaVectors.schema,NativeScaleVectors.table⟩",
        "theorem decodedInputs : NativeSchemaBinding.bind fixtureHash NativeSchemaVectors.original",
        "    NativeScaleVectors.original = some inputs :=",
        "  NativeSchemaBinding.bindFromSource ⟨NativeSchemaVectors.decodedSchema,",
        "    NativeScaleVectors.decodedTable,schemaHash,by decide,by decide⟩",
        "theorem planLinks : Links fixtureHash NativeScaleVectors.original inputs plan :=",
        "  ⟨rfl,rfl,rfl,rfl,rfl,scaleHash.symm,rfl,by decide⟩",
        "def bound : Bound := ⟨inputs,plan⟩",
        "theorem boundPlan : bind fixtureHash NativeSchemaVectors.original",
        "    NativeScaleVectors.original original = some bound :=",
        "  bindFromSource ⟨decodedInputs,decodedWire,interpretedPlan,computedPlan,planLinks⟩",
        "theorem allCoordinatesCovered (c : Nat) (inside : c < 36) :",
        "    ∃ e ∈ plan.entries, e.start ≤ c ∧ c < e.start+e.count :=",
        "  completeCoverage boundPlan c inside",
        "theorem noOverlapOrOrdinalReuse : plan.entries.Pairwise",
        "    (fun x y => x.start+x.count ≤ y.start ∧ x.ordinal < y.ordinal) := noOverlap boundPlan",
    ]
    for i in range(len(source.rows)):
        lines += [
            f"theorem scaleQ{i} : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original",
            f"    NativeQBytesVectors.frame{i} = some NativeScaleVectors.bound{i} := by",
            "  apply NativeScaleBinding.bindFromSource",
            f"  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined{i},",
            "    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩",
            f"theorem joined{i} : bindQ fixtureHash NativeSchemaVectors.original",
            f"    NativeScaleVectors.original original NativeQBytesVectors.frame{i} =",
            f"    some ⟨bound,NativeScaleVectors.bound{i}⟩ :=",
            f"  qFromSource ⟨boundPlan,scaleQ{i},rfl,planHash.symm,by decide⟩",
        ]
    cases = {
        "emptyBytes": "NativeShardPlanBytes.decode [] = none",
        "zeroTarget": "NativeShardPartition.build NativeSchemaVectors.schema 0 = none",
        "oddTarget": "NativeShardPartition.build NativeSchemaVectors.schema 3 = none",
        "largeTarget": "NativeShardPartition.build NativeSchemaVectors.schema 1048578 = none",
        "fuelExhausted": 'NativeShardPartition.chunks 2 2 (ascii "x") 0 0 5 0 = none',
        "zeroWidth": 'NativeShardPartition.chunks 2 0 (ascii "x") 0 0 5 0 = none',
        "partialFinalShard": 'NativeShardPartition.chunks 3 2 (ascii "x") 0 0 5 0 = '
        'some [⟨2,0,0,4,ascii "x",0⟩,⟨2,2,1,4,ascii "x",2⟩,⟨1,4,2,2,ascii "x",4⟩]',
        "missingEntry": "NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ "
        "some (plan.entries.drop 1)",
        "duplicateEntry": "NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ "
        "some (plan.entries ++ plan.entries.take 1)",
        "reorderedEntries": "NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ "
        "some plan.entries.reverse",
        "changedCount": "NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ "
        "some (plan.entries.map fun e => {e with count := e.count+1})",
        "changedStart": "NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ "
        "some (plan.entries.map fun e => {e with start := e.start+1})",
        "changedOffset": "NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ "
        "some (plan.entries.map fun e => {e with offset := e.offset+1})",
        "changedOrdinal": "NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ "
        "some (plan.entries.map fun e => {e with ordinal := 0})",
        "changedPayloadBytes": "NativeShardPartition.build NativeSchemaVectors.schema "
        "plan.target ≠ "
        "some (plan.entries.map fun e => {e with payload := e.payload+1})",
        "changedSegment": "NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ "
        'some (plan.entries.map fun e => {e with name := ascii "other"})',
        "wrongVersion": "¬ Links (fun _ => plan.wire.scale) [] inputs "
        '{plan with wire := {wire with version := ascii "2.0.0"}}',
        "wrongTotal": "¬ Links (fun _ => plan.wire.scale) [] inputs {plan with total := 35}",
        "missingScaleHash": "¬ Links (fun _ => []) [] inputs plan",
        "quotedCount": "NativeShardPlanBytes.readEntry (ascii "
        '"{\\"element_count\\":\\"4\\"}") = none',
        "negativeCount": 'NativeShardPlanBytes.readEntry (ascii "{\\"element_count\\":-1}") = none',
        "trailingComma": 'NativeShardPlanBytes.readEntries (ascii ",]") = none',
    }
    for name, proposition in cases.items():
        lines.append(f"theorem {name} : {proposition} := by decide")
    lines += [
        "theorem changedPayloadStillJoins : bindQ fixtureHash NativeSchemaVectors.original",
        "    NativeScaleVectors.original original",
        "    (NativeQBytes.encodeFrame NativeQBytesVectors.header0 [2,0,254,255,0,0,4,0]) =",
        "    some ⟨bound,⟨NativeScaleVectors.table,NativeScaleVectors.changedBlock,",
        "      NativeScaleVectors.segment0⟩⟩ := by",
        "  apply qFromSource",
        "  refine ⟨boundPlan,?_,rfl,planHash.symm,by decide⟩",
        "  apply NativeScaleBinding.bindFromSource",
        "  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors."
        "changedPayloadWithOldShaStillAccepted,",
        "    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩",
        "end DeltaReduce.NativeShardPlanVectors",
        "",
    ]
    LEAN.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    result = {
        "scope": "ORIGINAL_PLAN_BYTES_AND_DERIVED_PARTITION_NOT_AUTHENTICATION",
        "source_boundary_sha256": BOUNDARY_PIN,
        "formal_go": False,
        "native_execution": False,
        "native_recovery_proved": False,
        "hash_adapter_authenticated": False,
        "manifest_admission_proved": False,
        "plan_bytes_hex": raw.hex(),
        "plan_id": identity,
        "plan": doc,
        "small_kernel_cases": [*cases, "changedPayloadStillJoins"],
    }
    write_canonical_json(TARGET, result)
    return result


if __name__ == "__main__":
    generate()
