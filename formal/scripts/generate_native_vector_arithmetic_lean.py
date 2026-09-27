"""Original layout and full-vector component checks; no whole-source attestation."""

from __future__ import annotations

import re
from pathlib import Path

import generate_native_available_q as original
import generate_native_vector_projection as source
from formal_artifacts import sha256_file, write_canonical_json
from native_vector_projection import project_inputs

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeVectorArithmeticVectors.lean"
TARGET = ROOT / "formal/proposals/native-vector-arithmetic-lean-vectors.json"


def ints(values):
    return "[" + ",".join(str(v) for v in values) + "]"


def generate():
    original.source_blobs()
    projected = project_inputs(*source.source_fixture(True))
    quanta = ",".join(
        f"⟨{r['quantum'][0]},{r['quantum'][1]}⟩" for r in projected.source.inputs[0].source.q.rows
    )
    lines = [
        "import DeltaReduce.NativeVectorArithmetic",
        "import DeltaReduce.NativeManifestVectors",
        "import DeltaReduce.NativeAccumulatorVectors",
        "import DeltaReduce.NativePlanCoefficientVectors",
        "",
        "/-! Original layout/components plus separately synthetic mathematical rows.",
        "No combined whole-policy/Q source-load execution or authenticated source. -/",
        "namespace DeltaReduce.NativeVectorArithmeticVectors",
        "open NativeVectorContext NativeVectorArithmetic",
        "open NativeVoteBytes (ascii)",
        "",
        "def original := NativeManifestVectors.bound",
        "theorem originalCompatible : Compatible original original := ⟨rfl,rfl,rfl⟩",
        "theorem originalSlots : original.blocks.map (fun q => (shape q).entry) =",
        "    original.plan.plan.entries := originalPlanSlots NativeManifestVectors.wholeManifest",
        "theorem actualWidths : original.blocks.map (fun q => (shape q).entry.count) =",
        "    [4,8,8,8,8] := by decide",
        "theorem actualLocations : original.blocks.map (fun q => (shape q).entry.start) =",
        "    [0,4,12,20,28] := by decide",
        "theorem actualQuanta : original.blocks.map (fun q => (shape q).quantum) =",
        f"    [{quanta}] := by decide",
        "theorem shapesKeepFullWidth : (original.blocks.map (fun q =>"
        " q.block.frame.values.length)).sum",
        "    = 36 := by decide",
    ]
    for index, field in enumerate(
        ("schema", "profile", "proof", "config", "scale", "plan", "parent")
    ):
        lines += [
            f"theorem changed{field.title()} : ¬ Compatible original",
            "    { original with manifest := { original.manifest with wire :=",
            f'      {{ original.manifest.wire with {field} := ascii "changed" }} }} }} := by',
            "  intro h",
            f"  have bad := congrArg (fun xs => xs[{index}]?) h.1",
            "  revert bad; decide",
        ]
    for name, expr, getter in (
        ("missingBlock", "original.blocks.drop 1", "List.length"),
        ("extraBlock", "original.blocks ++ original.blocks.take 1", "List.length"),
        ("reorderedBlocks", "original.blocks.reverse", "fun xs => xs[0]?"),
        (
            "duplicatedBlock",
            "original.blocks.take 1 ++ original.blocks.dropLast",
            "fun xs => xs[1]?",
        ),
    ):
        lines += [
            f"theorem {name} : ¬ Compatible original {{ original with blocks := {expr} }} := by",
            f"  intro h; have bad := congrArg ({getter}) h.2.2",
            "  revert bad; decide",
        ]
    lines += [
        "def badQuantum := { NativeScaleVectors.bound0 with segment :=",
        "  { NativeScaleVectors.bound0.segment with denominator := 5 } }",
        "theorem changedQuantum : ¬ Compatible original",
        "    { original with blocks := badQuantum :: original.blocks.tail } := by",
        "  intro h; have bad := congrArg (fun xs => xs[0]?) h.2.2; revert bad; decide",
        "def badOffset := { NativeScaleVectors.bound0 with block :=",
        "  { NativeScaleVectors.bound0.block with header :=",
        "    { NativeScaleVectors.bound0.block.header with offset := 1 } } }",
        "theorem changedOffset : ¬ Compatible original",
        "    { original with blocks := badOffset :: original.blocks.tail } := by",
        "  intro h; have bad := congrArg (fun xs => xs[0]?) h.2.2; revert bad; decide",
        "theorem changedDecodedPlan : ¬ Compatible original",
        "    { original with plan := { original.plan with plan :=",
        "      { original.plan.plan with target := 0 } } } := by",
        "  intro h; have bad := congrArg (fun p => p.plan.target) h.2.1; revert bad; decide",
        "theorem parentIsOnlyIdentity : context { original with manifest :=",
        "    { original.manifest with wire := { original.manifest.wire with steps :="
        ' ascii "9" } } }',
        "    = context original := rfl",
        "",
        "/-- Low-level mathematical fixture builder; does NOT authenticate changed rows. -/",
        "def sample (a d : Nat) (q : NativeScaleBinding.Bound) : Slice :=",
        "  let base := NativePlanCoefficientVectors.rows[0]",
        "  let weight := { base.weight with numerator := a, denominator := d }",
        "  let row := { base with weight := weight }",
        "  ⟨⟨⟨row,a*(12/d)⟩,⟨original,NativeAccumulatorVectors.bound⟩⟩,q⟩",
        "def withValues (q : NativeScaleBinding.Bound) (values : List Int) :"
        " NativeScaleBinding.Bound :=",
        "  { q with block := { q.block with frame := { q.block.frame with values := values } } }",
        "def numbers := { NativeAccumulatorVectors.numbers with denominator := 12 }",
    ]
    cases = []
    for i, result in enumerate(projected.results):
        shard = int(result["shard"][1:])
        assignment = projected.assignments[i]
        slices = []
        terms = []
        for item in assignment["contributions"]:
            q = source.draft.resolve(projected.artifacts, item["q"], "Q_SHARD")
            a, d = item["weight"]
            terms.append({"ticket": item["ticket"], "weight": [a, d], "values": q["values"]})
            slices.append(
                f"sample {a} {d} (withValues NativeScaleVectors.bound{shard} {ints(q['values'])})"
            )
        lines += [
            f"def slices{i} : List Slice := [" + ",".join(slices) + "]",
            f"theorem vector{i} : compute numbers {len(result['numerators'])} slices{i} =",
            f"    some {ints(result['numerators'])} := by decide",
            f"theorem count{i} : slices{i}.length = {len(terms)} := rfl",
        ]
        cases.append({"ordinal": shard, "terms": terms, **result})
    lines += [
        "theorem actualPayloadWithSyntheticWeight : compute numbers 4",
        "    [sample 1 3 NativeScaleVectors.bound0] = some [4,-8,0,16] := by decide",
        "theorem zeroWeightRetained : (slices5.map kernelRow).length = 1 ∧",
        "    (slices5.map kernelRow)[0]?.map (·.numerator) = some 0 := by decide",
        "theorem missingCoordinate : compute numbers 4",
        "    [sample 1 3 (withValues NativeScaleVectors.bound0 [1,2,3])] = none := by decide",
        "theorem extraCoordinate : compute numbers 4",
        "    [sample 1 3 (withValues NativeScaleVectors.bound0 [1,2,3,4,5])] = none := by decide",
        "theorem emptyMembers : compute numbers 4 [] = none := by decide",
        "theorem wrongDenominator : compute { numbers with denominator := 5 } 4 slices0 ="
        " none := by decide",
        "theorem substitutedMinimumLCM : compute { numbers with denominator := 6 } 4 slices0 =",
        "    some [-1,2,0,-4] := by decide",
        "theorem signedFractionLimit : compute numbers 4",
        "    [sample (2^63) 1 NativeScaleVectors.bound0] = none := by decide",
        "theorem unsafePrefixCancellation : compute numbers 1",
        "    [sample 1 1 (withValues NativeScaleVectors.bound0 [9223372036854775807]),",
        "     sample 1 1 (withValues NativeScaleVectors.bound0 [-9223372036854775807])] ="
        " none := by decide",
        "theorem emptySlice {index} : sliceRows index [] = some [] := rfl",
        "end DeltaReduce.NativeVectorArithmeticVectors",
    ]
    text = "\n".join(lines) + "\n"
    document = {
        "scope": "ORIGINAL_LAYOUT_AND_SEPARATE_SYNTHETIC_VECTOR_COMPONENTS",
        "formal_go": False,
        "native_execution": False,
        "native_export_authenticated": False,
        "whole_source_kernel_example": False,
        "draft_schema_q_bytes_joined": False,
        "source_fixture_sha256": sha256_file(
            ROOT / "formal/proposals/native-vector-projection-vectors.json"
        ),
        "denominator": 12,
        "cases": cases,
        "kernel_theorems": re.findall(r"^theorem (\w+)", text, re.M),
    }
    LEAN.write_text(text, encoding="utf-8", newline="\n")
    write_canonical_json(TARGET, document)


if __name__ == "__main__":
    generate()
