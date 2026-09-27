"""Source-pinned scale-table bytes/quantum proofs with explicit unverified hash scope."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import BOUNDARY_PIN, fixture_store
from native_source_artifacts import canonical, require, resolve_q_source

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeScaleVectors.lean"
TARGET = ROOT / "formal/proposals/native-scale-binding-vectors.json"


def generate() -> dict:
    store, golden, _ = fixture_store()
    source = resolve_q_source(store, golden["manifest"]["content_id"])
    scale = golden["scale_table"]
    raw = bytes.fromhex(scale["bytes_hex"])
    require(raw == store[scale["content_id"]] == canonical(scale["value"]), "ORIGINAL_SCALE_BYTES")
    doc = scale["value"]
    lines = [
        "import DeltaReduce.NativeScaleBinding",
        "import DeltaReduce.NativeQHeaderVectors",
        "namespace DeltaReduce.NativeScaleVectors",
        "open NativeReceiptBytes (Bytes)",
        "open NativeVoteBytes (ascii ContentId)",
        "open NativeScaleBinding",
        "set_option maxRecDepth 4000",
        "set_option maxHeartbeats 1000000",
        "",
    ]
    pool: dict[str, int] = {}
    proofs: set[tuple[str, str]] = set()

    def val(value: object, kind: str = "text") -> tuple[str, str]:
        text = str(value)
        if text not in pool:
            n = len(pool)
            pool[text] = n
            literal = "[" + ",".join(str(b) for b in text.encode("ascii")) + "]"
            lines.append(f"def bytes{n} : Bytes := {literal}")
        n = pool[text]
        if (kind, text) not in proofs:
            proofs.add((kind, text))
            lines.append(
                f"theorem {kind}{n} : NativeQJson.ValueValid .{kind} bytes{n} := by decide"
            )
        return f"bytes{n}", f"{kind}{n}"

    wires, segments, syntax, valid = [], [], [], []
    for i, seg in enumerate(doc["segments"]):
        fields = [
            val(seg["element_count"], "natural"),
            val(seg["element_start"], "natural"),
            val(seg["quantum"]["denominator"], "natural"),
            val(seg["quantum"]["numerator"]),
            val(seg["segment_id"]),
            val(seg["segment_ordinal"], "natural"),
        ]
        wires.append(f"wire{i}")
        segments.append(f"segment{i}")
        syntax.append(f"syntax{i}")
        valid.append(f"valid{i}")
        lines += [
            f"def wire{i} : NativeScaleBytes.SegmentWire := ⟨"
            + ",".join(x[0] for x in fields)
            + "⟩",
            f"theorem syntax{i} : NativeScaleBytes.SegmentSyntax wire{i} := ⟨"
            + ",".join(x[1] for x in fields)
            + "⟩",
            f"def segment{i} : Segment := ⟨wire{i},{seg['element_count']},{seg['element_start']},"
            f"{seg['quantum']['numerator']},{seg['quantum']['denominator']},{seg['segment_ordinal']}⟩",
            f"theorem valid{i} : SegmentValid segment{i} := by decide",
        ]
    common_keys = ["formal_semantics_id", "parameter_schema_id", "profile_id", "schema_version"]
    common = [val(doc[k]) for k in common_keys]
    total = val(doc["total_elements"], "natural")
    typename = val(doc["type_name"])
    wire_list = "[" + ",".join(wires) + "]"
    segment_list = "[" + ",".join(segments) + "]"
    lines += [
        "def scaleWire : NativeScaleBytes.Wire := ⟨"
        + ",".join(x[0] for x in common)
        + f",{wire_list},{total[0]},{typename[0]}⟩",
        "def original : Bytes := [" + ",".join(map(str, raw)) + "]",
        f"theorem originalLength : original.length = {len(raw)} := by rfl",
        "theorem originalBytes : NativeScaleBytes.encode scaleWire = original := by rfl",
        "theorem segmentsSyntax : ∀ w ∈ scaleWire.segments, NativeScaleBytes.SegmentSyntax w := by",
        "  change ∀ w ∈ " + wire_list + ", NativeScaleBytes.SegmentSyntax w",
        "  simp only [List.forall_mem_cons]",
        "  exact ⟨" + ",".join(syntax) + ",by simp⟩",
        "theorem wireSyntax : NativeScaleBytes.Syntax scaleWire := ⟨"
        + ",".join(x[1] for x in common)
        + f",segmentsSyntax,by decide,{total[1]},{typename[1]}⟩",
        "theorem decodedWire : NativeScaleBytes.decode original = some scaleWire := by",
        "  rw [← originalBytes]",
        "  apply NativeScaleBytes.decodeEncoded scaleWire wireSyntax",
        "  rw [originalBytes,originalLength]; decide",
        f"def table : Table := ⟨scaleWire,{segment_list},{doc['total_elements']}⟩",
        "theorem segmentsValid : ∀ s ∈ table.segments, SegmentValid s := by",
        "  change ∀ s ∈ " + segment_list + ", SegmentValid s",
        "  simp only [List.forall_mem_cons]",
        "  exact ⟨" + ",".join(valid) + ",by simp⟩",
        "theorem tableSource : Source scaleWire table := by",
        "  exact ⟨rfl,loadValidSegments table.segments segmentsValid,by decide,by decide⟩",
        "theorem decodedTable : decode original = some table :=",
        "  decodedFromComponents decodedWire (interpretFromSource tableSource)",
        "/-- One-entry synthetic adapter; not SHA or exporter authentication. -/",
        f"def originalId : Bytes := ascii {json.dumps(scale['content_id'])}",
        "def fixtureHash (raw : Bytes) : Bytes := "
        "if raw = hashInput original then originalId else []",
        "theorem originalHash : fixtureHash (hashInput original) = originalId := if_pos rfl",
    ]
    for i, row in enumerate(source.rows):
        seg = next(j for j, s in enumerate(doc["segments"]) if s["segment_id"] == row["segment_id"])
        values = "[" + ",".join(map(str, row["values"])) + "]"
        lines += [
            f"def block{i} : NativeQHeader.Joined := ⟨⟨NativeQBytesVectors.header{i},"
            f"NativeQBytesVectors.payload{i},{values}⟩,NativeQHeaderVectors.header{i}⟩",
            f"def bound{i} : Bound := ⟨table,block{i},segment{seg}⟩",
            f"theorem source{i} : BoundSource fixtureHash original "
            f"NativeQBytesVectors.frame{i} bound{i} := by",
            f"  refine ⟨decodedTable,NativeQHeaderVectors.joined{i},by decide,?_⟩",
            "  exact ⟨originalHash,rfl,rfl,rfl,by decide,by decide⟩",
            f"theorem boundDecoded{i} : bind fixtureHash original NativeQBytesVectors.frame{i} "
            f"= some bound{i} :=",
            f"  bindFromSource source{i}",
            f"theorem quantum{i} : bound{i}.quantum = "
            f"⟨{row['quantum'][0]},{row['quantum'][1]}⟩ := rfl",
        ]
    cases = {
        "zeroNumerator": 'interpretSegment {wire0 with numerator := ascii "0"} = none',
        "zeroDenominator": 'interpretSegment {wire0 with denominator := ascii "0"} = none',
        "nonReduced": 'interpretSegment {wire0 with numerator := ascii "2"} = none',
        "negativeQuantum": 'interpretSegment {wire0 with numerator := ascii "-1"} = none',
        "leadingZeroQuantum": 'interpretSegment {wire0 with numerator := ascii "01"} = none',
        "wideNumerator": 'interpretSegment {wire0 with numerator := ascii "4294967296"} = none',
        "wideDenominator": 'interpretSegment {wire0 with denominator := ascii "4294967296"} = none',
        "zeroCount": 'interpretSegment {wire0 with count := ascii "0"} = none',
        "overflowRange": 'interpretSegment {wire0 with start := ascii "1073741824"} = none',
        "ordinalBound": 'interpretSegment {wire0 with ordinal := ascii "65536"} = none',
        "wrongTotal": "¬ TableChecks {table with total := 35}",
        "missingSegment": "¬ TableChecks {table with segments := [segment0]}",
        "duplicateName": "¬ TableChecks {table with segments := [segment0, "
        "{segment1 with wire := {wire1 with name := wire0.name}}]}",
        "reordered": "¬ TableChecks {table with segments := [segment1,segment0]}",
        "gap": "¬ TableChecks {table with segments := [segment0,{segment1 with start := 5}]}",
        "wrongProfile": "¬ TableChecks {table with wire := {scaleWire with profile := []}}",
        "wrongVersion": "¬ TableChecks {table with wire := "
        '{scaleWire with version := ascii "2.0.0"}}',
        "wrongType": "¬ TableChecks {table with wire := "
        '{scaleWire with kind := ascii "SHARD_PLAN"}}',
        "crossBoundary": "¬ Links (fun _ => originalId) original table "
        "{block0 with header := {block0.header with count := 5}} segment0",
        "wrongOffset": "¬ Links (fun _ => originalId) original table "
        "{block0 with header := {block0.header with offset := 1}} segment0",
        "wrongStart": "¬ Links (fun _ => originalId) original table "
        "{block0 with header := {block0.header with start := 1}} segment0",
        "wrongSchema": "¬ Links (fun _ => originalId) original "
        "{table with wire := {scaleWire with schema := []}} block0 segment0",
        "missingHash": "¬ Links (fun _ => []) original table block0 segment0",
        "emptyBytes": "decode [] = none",
        "notObject": "decode [91,93] = none",
        "emptyListAtZeroBound": "NativeScaleBytes.readSegments 0 [93] = some ([],[])",
        "nonemptyListAtZeroBound": "NativeScaleBytes.readSegments 0 [123] = none",
    }
    for name, raw_case in {
        "wrongNestedType": '{"element_count":4,"element_start":0,"quantum":"1/4"}',
        "duplicateSegmentKey": '{"element_count":4,"element_count":4}',
        "reorderedSegmentKey": '{"element_start":0,"element_count":4}',
        "negativeCount": '{"element_count":-1,',
    }.items():
        cases[name] = f"NativeScaleBytes.readSegment (ascii {json.dumps(raw_case)}) = none"
    for name, prop in cases.items():
        lines.append(f"theorem {name} : {prop} := by decide")
    lines += [
        "def changedBlock : NativeQHeader.Joined := ⟨⟨NativeQBytesVectors.header0,"
        "[2,0,254,255,0,0,4,0],[2,-2,0,4]⟩,NativeQHeaderVectors.header0⟩",
        "theorem changedPayloadStillBinds : bind fixtureHash original",
        "    (NativeQBytes.encodeFrame NativeQBytesVectors.header0 [2,0,254,255,0,0,4,0]) =",
        "    some ⟨table,changedBlock,segment0⟩ := by",
        "  apply bindFromSource",
        "  exact ⟨decodedTable,NativeQHeaderVectors.changedPayloadWithOldShaStillAccepted,",
        "    by decide,originalHash,rfl,rfl,rfl,by decide,by decide⟩",
        "",
        "end DeltaReduce.NativeScaleVectors",
        "",
    ]
    LEAN.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    result = {
        "version": "deltareduce.original-scale-header-join.v1-candidate",
        "scope": "ORIGINAL_SCALE_BYTES_QUANTUM_AND_RANGE_WITH_UNVERIFIED_HASH_ADAPTER",
        "source_boundary_sha256": BOUNDARY_PIN,
        "scale_id": scale["content_id"],
        "scale_bytes_hex": raw.hex(),
        "scale_value": doc,
        "rows": list(source.rows),
        "small_kernel_cases": [*cases, "changedPayloadStillBinds"],
        "formal_go": False,
        "native_execution": False,
        "sha_implementation_proved": False,
        "hash_adapter_authenticated": False,
        "schema_plan_source_binding_proved": False,
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
                "segments": len(result["scale_value"]["segments"]),
                "rows": len(result["rows"]),
                "small_cases": len(result["small_kernel_cases"]),
            }
        )
    )
