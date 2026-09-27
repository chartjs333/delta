"""Small component checks; no fabricated native execution or full source bridge."""

from __future__ import annotations

import hashlib
from pathlib import Path

from formal_artifacts import load_json_strict, sha256_file, write_canonical_json

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "formal/proposals/evidence/native-apply-result"
PIN = "adb42ccc2619007913cb4cacb8587a42d3a699b115fc20666db78436b685b108"


def bs(value: bytes) -> str:
    return "[" + ",".join(map(str, value)) + "]"


def generate() -> tuple[str, dict]:
    golden = EVIDENCE / "delta-protocol__fixtures__008__cross-language__golden-v1.json"
    if sha256_file(golden) != PIN:
        raise ValueError("original 008 golden substituted")
    original = load_json_strict(golden)
    countercheck = []
    for kind in ("model", "optimizer"):
        c = original["apply_candidate"]["value"]
        preimage = f"deltareduce.008.{kind}.v1".encode() + b"\0"
        preimage += b"".join(x.encode() + b";" for x in c[f"next_{kind}_values"])
        computed = "sha256:" + hashlib.sha256(preimage).hexdigest()
        stored = c[f"next_{kind}_hash"]
        label = "sha256:" + hashlib.sha256(f"next-{kind}".encode()).hexdigest()
        if stored != label or computed == stored:
            raise ValueError("original label-hash countercheck changed")
        countercheck.append(
            {
                "kind": kind,
                "preimage_hex": preimage.hex(),
                "stored": stored,
                "computed_from_values": computed,
                "fixture_label": f"next-{kind}",
                "matches_values": False,
            }
        )
    samples = []
    for kind, numbers in [("model", [19, -19]), ("optimizer", [2, -2]), ("model", [20, -20])]:
        raw = f"deltareduce.008.{kind}.v1".encode() + b"\0"
        raw += b"".join(str(n).encode() + b";" for n in numbers)
        samples.append((raw, hashlib.sha256(raw).digest()))
    chunks = [
        "import DeltaReduce.NativeApplyResultJoin",
        "import DeltaReduce.NativeApplyCertificateVectors",
        "import DeltaReduce.NativeGraphVectors",
        "",
        "/-! Original graph computation reused by component proof. Constructed",
        "candidate is SYNTHETIC, not an original native capture or authority. -/",
        "namespace DeltaReduce.NativeApplyResultVectors",
        "open NativeBinding NativeApplyResult",
        "set_option maxRecDepth 12000",
        "set_option maxHeartbeats 3000000",
        "set_option Elab.async false",
    ]
    for i, (raw, digest) in enumerate(samples):
        chunks.extend([f"def pre{i} : Bytes := {bs(raw)}", f"def hash{i} : Bytes := {bs(digest)}"])
    chunks.append("def sha (raw : Bytes) : Bytes :=")
    for i in range(len(samples)):
        chunks.append(f"  if raw = pre{i} then hash{i} else")
    chunks.append("  []")
    for i in range(len(samples)):
        chunks.append(f"theorem sample{i} : sha pre{i} = hash{i} := by decide")
    chunks.extend(
        [
            "def values : Values := ⟨[19,-19],[2,-2],[20,-20],[2,-2]⟩",
            "def expectedHashes : Digests := ⟨hash0,hash1,hash2,hash1⟩",
            "def candidate : NativeApplyCertificate.Candidate :=",
            "  { NativeApplyCertificateVectors.candidate with",
            "    modelValues := decimalValues values.model, optimizerValues := "
            "decimalValues values.optimizer,",
            "    model := idBytes hash0, optimizer := idBytes hash1,",
            "    parent := idBytes hash2, parentOptimizer := idBytes hash1 }",
            "theorem computedDigests : digests sha values = expectedHashes := by decide",
            "theorem accepted : checkValues sha values candidate = some "
            "expectedHashes := by decide",
            "theorem exactPreimages :",
            "    rawValueInput .model candidate.modelValues = pre0 ∧",
            "    rawValueInput .optimizer candidate.optimizerValues = pre1 := by decide",
            "theorem originalGraphResult (native : NativeApply NativeGraphVectors.fixtureBinding)",
            "    (computed : deriveNativeApply NativeGraphVectors.fixtureBinding = some native) :",
            "    checkValues sha (nativeValues NativeGraphVectors.fixtureBinding "
            "native) candidate =",
            "      some expectedHashes := by",
            "  have body : native.body = NativeGraphVectors.expectedApply := by",
            "    have pinned := NativeGraphVectors.nativeApplyMatchesOracle",
            "    rw [computed] at pinned",
            "    exact Option.some.inj pinned",
            "  change checkValues sha "
            "⟨native.body.nextModel,native.body.nextOptimizer,_,_⟩ candidate = _",
            "  rw [body]",
            "  exact accepted",
            "theorem missingCoordinate : checkValues sha values {candidate with "
            "modelValues := [[49,57]]} = none := by decide",
            "theorem reordered : checkValues sha values {candidate with "
            "modelValues := candidate.modelValues.reverse} = none := by decide",
            "theorem wrongNumber : checkValues sha values {candidate with "
            "modelValues := [[57,57,57],[45,49,57]]} = none := by decide",
            "theorem extraCoordinate : checkValues sha values {candidate with "
            "modelValues := candidate.modelValues ++ [[48]]} = none := by decide",
            "theorem wrongOptimizer : checkValues sha values {candidate with "
            "optimizerValues := candidate.modelValues} = none := by decide",
            "theorem wrongModelHash : checkValues sha values {candidate with model "
            ":= candidate.optimizer} = none := by decide",
            "theorem wrongOptimizerHash : checkValues sha values {candidate with "
            "optimizer := candidate.model} = none := by decide",
            "theorem wrongParentModel : checkValues sha values {candidate with "
            "parent := candidate.model} = none := by decide",
            "theorem wrongParentOptimizer : checkValues sha values {candidate with "
            "parentOptimizer := candidate.parent} = none := by decide",
            "theorem changedPreimageNotApproved : checkValues sha {values with "
            "model := [999,-19]} candidate = none := by decide",
            "theorem unavailableHash : checkValues (fun _ => []) values candidate "
            "= none := by decide",
            "theorem shortHash : checkValues (fun _ => [1]) values candidate = none := by decide",
            "theorem originalLabelHashesNotRewritten : checkValues sha values "
            "NativeApplyCertificateVectors.candidate = none := by decide",
            "theorem signedEndpoints : decimalValues [-9223372036854775808,9223372036854775807] =",
            f"  [{bs(b'-9223372036854775808')},{bs(b'9223372036854775807')}] := by decide",
            "theorem oldNegativeZeroStillAccepted : NativeCertificateDecimal.parse "
            "false [45,48,48] = some 0 := by decide",
            "theorem oldNegativeAliasStillAccepted : "
            "NativeCertificateDecimal.parse false [45,48,49] = some (-1) := by "
            "decide",
            "theorem negativeZeroNotComputed : [45,48,48] ≠ asciiBytes (toString "
            "(0 : Int)) := by decide",
            "theorem negativeAliasNotComputed : [45,48,49] ≠ asciiBytes (toString "
            "(-1 : Int)) := by decide",
            "def sourceProfile : NativeApplyProfile.Profile :=",
            "  "
            "⟨NativeApplyCertificateVectors.profile.accumulator,[⟨[100,49],⟨1,1⟩⟩],"
            "⟨1,2⟩,⟨1,2⟩,1,",
            '    asciiBytes "HALF_TOWARD_POSITIVE",⟨0,1⟩⟩',
            "theorem numericProfile : ProfileMatches sourceProfile "
            "NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem wrongLearning : ¬ ProfileMatches {sourceProfile with learning "
            ":= ⟨1,3⟩} NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem wrongMomentum : ¬ ProfileMatches {sourceProfile with momentum "
            ":= ⟨0,1⟩} NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem wrongDecay : ¬ ProfileMatches {sourceProfile with decay := "
            "⟨1,1⟩} NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem wrongDomain : ¬ ProfileMatches {sourceProfile with weights := "
            "[⟨[120],⟨1,1⟩⟩]} NativeGraphVectors.fixtureBinding.profile := by "
            "decide",
            "theorem missingWeight : ¬ ProfileMatches {sourceProfile with weights "
            ":= []} NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem duplicateWeight : ¬ ProfileMatches {sourceProfile with "
            "weights := sourceProfile.weights ++ sourceProfile.weights} "
            "NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem wrongRounding : ¬ ProfileMatches {sourceProfile with rounding "
            ":= []} NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem wrongNesterov : ¬ ProfileMatches {sourceProfile with nesterov "
            ":= 0} NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem numericGateDoesNotAuthenticateMetadata : checkValues sha values",
            "    {candidate with context := {candidate.context with schema := "
            "[],config := [],arithmetic := []}, root := [],profile := []}",
            "      = some expectedHashes := by decide",
            "theorem numericProfileDoesNotAuthenticateAccumulator :",
            "    ProfileMatches {sourceProfile with accumulator := []} "
            "NativeGraphVectors.fixtureBinding.profile := by decide",
            "theorem opaqueAnchorCheckpointNotValueIdentity :",
            "    asciiBytes NativeGraphVectors.anchor.context.parentCheckpoint ≠ "
            "idBytes hash2 := by decide",
            "def leaf (p : ParameterBody) : NativeParameterLineage.Edge :=",
            "  { NativeParameterVectors.finalizedEdge with certificate :=",
            "    { NativeParameterVectors.finalizedEdge.certificate with common :=",
            "      { NativeParameterVectors.finalizedEdge.certificate.common with",
            "        domain := asciiBytes p.domain,shard := asciiBytes "
            "p.shard,denominator := p.denominator.toNat,",
            "        numerators := decimalValues p.numerators } } }",
            "def leaves := NativeGraphVectors.expectedBodies.map leaf",
            "theorem allLeafNumbers : LeafMatches leaves "
            "NativeGraphVectors.expectedBodies := by decide",
            "theorem missingLeaf : ¬ LeafMatches leaves.tail "
            "NativeGraphVectors.expectedBodies := by decide",
            "theorem extraLeaf : ¬ LeafMatches (leaves ++ leaves) "
            "NativeGraphVectors.expectedBodies := by decide",
            "theorem reorderedLeaves : ¬ LeafMatches leaves.reverse "
            "NativeGraphVectors.expectedBodies := by decide",
            "theorem wrongNumerator : ¬ LeafMatches leaves",
            "    (NativeGraphVectors.expectedBodies.map (fun p => {p with "
            "numerators := [999]})) := by decide",
            "theorem scaledFractionNotEqual : ¬ LeafMatches leaves",
            "    (NativeGraphVectors.expectedBodies.map (fun p => {p with "
            "denominator := p.denominator * 2, numerators := p.numerators.map (· * "
            "2)})) := by decide",
            "theorem missingSourceLeavesStillNumeric : LeafMatches",
            "    (leaves.map (fun e => {e with certificate := {e.certificate with "
            "common := {e.certificate.common with leaves := []}}}))",
            "    NativeGraphVectors.expectedBodies := by decide",
            "end DeltaReduce.NativeApplyResultVectors",
        ]
    )
    doc = {
        "scope": "SYNTHETIC_COMPONENTS_AND_EXISTING_KERNEL_GRAPH_NOT_NATIVE_EXECUTION",
        "golden_sha256": PIN,
        "original_golden_value_hash_countercheck": countercheck,
        "original_candidate_id": original["apply_candidate"]["content_id"],
        "hash_samples": [{"preimage_hex": a.hex(), "sha256": b.hex()} for a, b in samples],
        "model": [19, -19],
        "optimizer": [2, -2],
        "parent_model": [20, -20],
        "parent_optimizer": [2, -2],
        "full_source_join_example": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
        "unmatched_source_identities": [
            "configuration",
            "schema",
            "arithmetic_profile",
            "accumulator_proof",
            "ISC_EC_APC_Q_artifacts",
            "ROOT_to_draft_aggregate",
        ],
    }
    return "\n".join(chunks) + "\n", doc


def main() -> None:
    lean, doc = generate()
    (ROOT / "formal/proofs/DeltaReduce/NativeApplyResultVectors.lean").write_text(
        lean, encoding="utf-8", newline="\n"
    )
    write_canonical_json(ROOT / "formal/proposals/native-apply-result-vectors.json", doc)


if __name__ == "__main__":
    main()
