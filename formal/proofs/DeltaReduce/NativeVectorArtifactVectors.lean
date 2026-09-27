import DeltaReduce.NativeVectorJoin
import DeltaReduce.NativeVectorArithmeticVectors

/-! Original layout/Q component bytes; row metadata remains a synthetic
component fixture. No complete run or authenticated source is instantiated. -/
set_option maxRecDepth 4096
namespace DeltaReduce.NativeVectorArtifactVectors
open NativeBinding NativeVectorLayout NativeVectorArtifacts
def plan := NativeShardPlanVectors.bound
def layout : Layout := ⟨plan,locations plan.inputs.schema⟩
theorem small : Small plan := by decide
theorem layoutChecks : LayoutChecks plan layout.positions := by decide
theorem originalLayout : construct plan = some layout := constructFromChecks small layoutChecks
theorem coordinateNames : layout.coordinates = ["decoder.bias:0000000000","decoder.bias:0000000001","decoder.bias:0000000002","decoder.bias:0000000003","embedding.weight:0000000000","embedding.weight:0000000001","embedding.weight:0000000002","embedding.weight:0000000003","embedding.weight:0000000004","embedding.weight:0000000005","embedding.weight:0000000006","embedding.weight:0000000007","embedding.weight:0000000008","embedding.weight:0000000009","embedding.weight:0000000010","embedding.weight:0000000011","embedding.weight:0000000012","embedding.weight:0000000013","embedding.weight:0000000014","embedding.weight:0000000015","embedding.weight:0000000016","embedding.weight:0000000017","embedding.weight:0000000018","embedding.weight:0000000019","embedding.weight:0000000020","embedding.weight:0000000021","embedding.weight:0000000022","embedding.weight:0000000023","embedding.weight:0000000024","embedding.weight:0000000025","embedding.weight:0000000026","embedding.weight:0000000027","embedding.weight:0000000028","embedding.weight:0000000029","embedding.weight:0000000030","embedding.weight:0000000031"] := by decide
theorem shardRanges : layout.shards = [⟨"s0000000000",0,4⟩,⟨"s0000000001",4,8⟩,⟨"s0000000002",12,8⟩,⟨"s0000000003",20,8⟩,⟨"s0000000004",28,8⟩] := by decide
theorem totalCoordinates : layout.positions.length = 36 := by decide
theorem noFrozen : layout.positions.all (fun l => l.parameter != NativeVoteBytes.ascii
    "frozen.scale") = true := by decide
theorem noAliasCoordinate : layout.positions.all (fun l => l.parameter != NativeVoteBytes.ascii
    "lm_head.weight") = true := by decide
theorem originalMetadata : layout.source.inputs.schema = NativeSchemaVectors.schema := rfl
theorem tenDigits : [digits 0,digits 9,digits 10,digits 4095] =
    ["0000000000","0000000009","0000000010","0000004095"] := by decide
theorem namingConflict : ¬ ([coordinate (asciiBytes "a") 0,coordinate (asciiBytes "a.b") 0]).Pairwise (· < ·) := by decide
theorem tooLong : validIdentifier (coordinate (List.replicate 118 97) 0) = false := by decide
theorem nonAscii : validIdentifier (text [255]) = false := by decide
theorem wrongGlobal : ¬ LayoutChecks plan
    ({ (layout.positions[0]) with global := 1 } :: layout.positions.tail) := by decide
theorem reversedPositions : ¬ LayoutChecks plan layout.positions.reverse := by decide
theorem missingCoordinate : ¬ LayoutChecks plan layout.positions.tail := by decide
theorem duplicateCoordinate : ¬ LayoutChecks plan (layout.positions.take 1 ++ layout.positions.dropLast) := by decide
theorem wrongShape : ¬ LayoutChecks {plan with plan := {plan.plan with entries := plan.plan.entries.reverse}}
    layout.positions := by decide
theorem labelBytes0 : quotedBytes (asciiBytes "decoder.bias:0000000000") = [34,100,101,99,111,100,101,114,46,98,105,97,115,58,48,48,48,48,48,48,48,48,48,48,34] := by decide
theorem labelBytes1 : quotedBytes (asciiBytes "decoder.bias:0000000001") = [34,100,101,99,111,100,101,114,46,98,105,97,115,58,48,48,48,48,48,48,48,48,48,49,34] := by decide
theorem labelBytes2 : quotedBytes (asciiBytes "decoder.bias:0000000002") = [34,100,101,99,111,100,101,114,46,98,105,97,115,58,48,48,48,48,48,48,48,48,48,50,34] := by decide
theorem labelBytes3 : quotedBytes (asciiBytes "decoder.bias:0000000003") = [34,100,101,99,111,100,101,114,46,98,105,97,115,58,48,48,48,48,48,48,48,48,48,51,34] := by decide
theorem labelBytes4 : quotedBytes (asciiBytes "embedding.weight:0000000000") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,48,34] := by decide
theorem labelBytes5 : quotedBytes (asciiBytes "embedding.weight:0000000001") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,49,34] := by decide
theorem labelBytes6 : quotedBytes (asciiBytes "embedding.weight:0000000002") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,50,34] := by decide
theorem labelBytes7 : quotedBytes (asciiBytes "embedding.weight:0000000003") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,51,34] := by decide
theorem labelBytes8 : quotedBytes (asciiBytes "embedding.weight:0000000004") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,52,34] := by decide
theorem labelBytes9 : quotedBytes (asciiBytes "embedding.weight:0000000005") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,53,34] := by decide
theorem labelBytes10 : quotedBytes (asciiBytes "embedding.weight:0000000006") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,54,34] := by decide
theorem labelBytes11 : quotedBytes (asciiBytes "embedding.weight:0000000007") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,55,34] := by decide
theorem labelBytes12 : quotedBytes (asciiBytes "embedding.weight:0000000008") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,56,34] := by decide
theorem labelBytes13 : quotedBytes (asciiBytes "embedding.weight:0000000009") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,57,34] := by decide
theorem labelBytes14 : quotedBytes (asciiBytes "embedding.weight:0000000010") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,48,34] := by decide
theorem labelBytes15 : quotedBytes (asciiBytes "embedding.weight:0000000011") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,49,34] := by decide
theorem labelBytes16 : quotedBytes (asciiBytes "embedding.weight:0000000012") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,50,34] := by decide
theorem labelBytes17 : quotedBytes (asciiBytes "embedding.weight:0000000013") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,51,34] := by decide
theorem labelBytes18 : quotedBytes (asciiBytes "embedding.weight:0000000014") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,52,34] := by decide
theorem labelBytes19 : quotedBytes (asciiBytes "embedding.weight:0000000015") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,53,34] := by decide
theorem labelBytes20 : quotedBytes (asciiBytes "embedding.weight:0000000016") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,54,34] := by decide
theorem labelBytes21 : quotedBytes (asciiBytes "embedding.weight:0000000017") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,55,34] := by decide
theorem labelBytes22 : quotedBytes (asciiBytes "embedding.weight:0000000018") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,56,34] := by decide
theorem labelBytes23 : quotedBytes (asciiBytes "embedding.weight:0000000019") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,57,34] := by decide
theorem labelBytes24 : quotedBytes (asciiBytes "embedding.weight:0000000020") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,48,34] := by decide
theorem labelBytes25 : quotedBytes (asciiBytes "embedding.weight:0000000021") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,49,34] := by decide
theorem labelBytes26 : quotedBytes (asciiBytes "embedding.weight:0000000022") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,50,34] := by decide
theorem labelBytes27 : quotedBytes (asciiBytes "embedding.weight:0000000023") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,51,34] := by decide
theorem labelBytes28 : quotedBytes (asciiBytes "embedding.weight:0000000024") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,52,34] := by decide
theorem labelBytes29 : quotedBytes (asciiBytes "embedding.weight:0000000025") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,53,34] := by decide
theorem labelBytes30 : quotedBytes (asciiBytes "embedding.weight:0000000026") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,54,34] := by decide
theorem labelBytes31 : quotedBytes (asciiBytes "embedding.weight:0000000027") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,55,34] := by decide
theorem labelBytes32 : quotedBytes (asciiBytes "embedding.weight:0000000028") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,56,34] := by decide
theorem labelBytes33 : quotedBytes (asciiBytes "embedding.weight:0000000029") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,57,34] := by decide
theorem labelBytes34 : quotedBytes (asciiBytes "embedding.weight:0000000030") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,51,48,34] := by decide
theorem labelBytes35 : quotedBytes (asciiBytes "embedding.weight:0000000031") = [34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,51,49,34] := by decide
theorem shardBytes0 : encodeShard ⟨"s0000000000",0,4⟩ = [123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,48,34,44,34,108,101,110,103,116,104,34,58,52,44,34,111,102,102,115,101,116,34,58,48,125] := by decide
theorem shardBytes1 : encodeShard ⟨"s0000000001",4,8⟩ = [123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,49,34,44,34,108,101,110,103,116,104,34,58,56,44,34,111,102,102,115,101,116,34,58,52,125] := by decide
theorem shardBytes2 : encodeShard ⟨"s0000000002",12,8⟩ = [123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,50,34,44,34,108,101,110,103,116,104,34,58,56,44,34,111,102,102,115,101,116,34,58,49,50,125] := by decide
theorem shardBytes3 : encodeShard ⟨"s0000000003",20,8⟩ = [123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,51,34,44,34,108,101,110,103,116,104,34,58,56,44,34,111,102,102,115,101,116,34,58,50,48,125] := by decide
theorem shardBytes4 : encodeShard ⟨"s0000000004",28,8⟩ = [123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,52,34,44,34,108,101,110,103,116,104,34,58,56,44,34,111,102,102,115,101,116,34,58,50,56,125] := by decide
def schemaBytes : Bytes := [123,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,112,97,121,108,111,97,100,34,58,123,34,99,111,111,114,100,105,110,97,116,101,115,34,58,91,34,100,101,99,111,100,101,114,46,98,105,97,115,58,48,48,48,48,48,48,48,48,48,48,34,44,34,100,101,99,111,100,101,114,46,98,105,97,115,58,48,48,48,48,48,48,48,48,48,49,34,44,34,100,101,99,111,100,101,114,46,98,105,97,115,58,48,48,48,48,48,48,48,48,48,50,34,44,34,100,101,99,111,100,101,114,46,98,105,97,115,58,48,48,48,48,48,48,48,48,48,51,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,48,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,49,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,50,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,51,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,52,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,53,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,54,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,55,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,56,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,48,57,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,48,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,49,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,50,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,51,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,52,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,53,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,54,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,55,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,56,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,49,57,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,48,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,49,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,50,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,51,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,52,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,53,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,54,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,55,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,56,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,50,57,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,51,48,34,44,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,58,48,48,48,48,48,48,48,48,51,49,34,93,44,34,115,104,97,114,100,115,34,58,91,123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,48,34,44,34,108,101,110,103,116,104,34,58,52,44,34,111,102,102,115,101,116,34,58,48,125,44,123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,49,34,44,34,108,101,110,103,116,104,34,58,56,44,34,111,102,102,115,101,116,34,58,52,125,44,123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,50,34,44,34,108,101,110,103,116,104,34,58,56,44,34,111,102,102,115,101,116,34,58,49,50,125,44,123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,51,34,44,34,108,101,110,103,116,104,34,58,56,44,34,111,102,102,115,101,116,34,58,50,48,125,44,123,34,105,100,34,58,34,115,48,48,48,48,48,48,48,48,48,52,34,44,34,108,101,110,103,116,104,34,58,56,44,34,111,102,102,115,101,116,34,58,50,56,125,93,125,125]
theorem schemaExact : encodeSchema layout = schemaBytes := by
  simp only [encodeSchema,coordinateNames,shardRanges,List.map_cons,List.map_nil,Function.comp_apply,
    labelBytes0,labelBytes1,labelBytes2,labelBytes3,labelBytes4,labelBytes5,labelBytes6,labelBytes7,labelBytes8,labelBytes9,labelBytes10,labelBytes11,labelBytes12,labelBytes13,labelBytes14,labelBytes15,labelBytes16,labelBytes17,labelBytes18,labelBytes19,labelBytes20,labelBytes21,labelBytes22,labelBytes23,labelBytes24,labelBytes25,labelBytes26,labelBytes27,labelBytes28,labelBytes29,labelBytes30,labelBytes31,labelBytes32,labelBytes33,labelBytes34,labelBytes35,shardBytes0,shardBytes1,shardBytes2,shardBytes3,shardBytes4]
  rfl
set_option maxRecDepth 16384 in
theorem schemaLength : schemaBytes.length = 1338 := rfl
def schemaRef : Ref := ⟨[82,12,123,162,144,34,144,91,214,232,59,188,185,19,59,83,104,221,222,44,20,223,179,122,196,245,34,58,72,244,112,2],.schema,1338⟩
theorem distinctHashPreimages : artifactHashInput schemaBytes ≠ NativeSchemaVectors.original := by
  intro h; have bad := congrArg List.head? h; revert bad; decide
def slice0 : NativeVectorContext.Slice :=
  let s := NativeVectorArithmeticVectors.sample 1 1 NativeScaleVectors.bound0
  { s with source := { s.source with term := { s.source.term with source :=
    { s.source.term.source with member := { s.source.term.source.member with input :=
      { s.source.term.source.member.input with
        ticket := asciiBytes "ticket-002-fixture", domain := asciiBytes "domain-text-en" } } } } } }
def q0 : QShard := ⟨"ticket-002-fixture","domain-text-en","s0000000000",schemaRef,
    ⟨1,4⟩,[1,-2,0,4]⟩
theorem qSource0 : qValue schemaRef slice0 = q0 := by decide
theorem qChecks0 : QChecks schemaRef slice0 := by decide
def qBytes0 : Bytes := [123,34,107,105,110,100,34,58,34,81,95,83,72,65,82,68,34,44,34,112,97,121,108,111,97,100,34,58,123,34,100,111,109,97,105,110,34,58,34,100,111,109,97,105,110,45,116,101,120,116,45,101,110,34,44,34,113,117,97,110,116,117,109,34,58,91,49,44,52,93,44,34,115,99,104,101,109,97,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,53,50,48,99,55,98,97,50,57,48,50,50,57,48,53,98,100,54,101,56,51,98,98,99,98,57,49,51,51,98,53,51,54,56,100,100,100,101,50,99,49,52,100,102,98,51,55,97,99,52,102,53,50,50,51,97,52,56,102,52,55,48,48,50,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,51,51,56,125,44,34,115,104,97,114,100,34,58,34,115,48,48,48,48,48,48,48,48,48,48,34,44,34,116,105,99,107,101,116,34,58,34,116,105,99,107,101,116,45,48,48,50,45,102,105,120,116,117,114,101,34,44,34,118,97,108,117,101,115,34,58,91,49,44,45,50,44,48,44,52,93,125,125]
theorem qExact0 : encodeQ q0 = qBytes0 := by decide
theorem qImage0 : encodeQ (qValue schemaRef slice0) = qBytes0 := by rw [qSource0]; exact qExact0
theorem qFullWidth0 : (qValue schemaRef slice0).values.length = 4 := by decide
def slice1 : NativeVectorContext.Slice :=
  let s := NativeVectorArithmeticVectors.sample 1 1 NativeScaleVectors.bound1
  { s with source := { s.source with term := { s.source.term with source :=
    { s.source.term.source with member := { s.source.term.source.member with input :=
      { s.source.term.source.member.input with
        ticket := asciiBytes "ticket-002-fixture", domain := asciiBytes "domain-text-en" } } } } } }
def q1 : QShard := ⟨"ticket-002-fixture","domain-text-en","s0000000001",schemaRef,
    ⟨1,16⟩,[-16,-15,-14,-13,-12,-11,-10,-9]⟩
theorem qSource1 : qValue schemaRef slice1 = q1 := by decide
theorem qChecks1 : QChecks schemaRef slice1 := by decide
def qBytes1 : Bytes := [123,34,107,105,110,100,34,58,34,81,95,83,72,65,82,68,34,44,34,112,97,121,108,111,97,100,34,58,123,34,100,111,109,97,105,110,34,58,34,100,111,109,97,105,110,45,116,101,120,116,45,101,110,34,44,34,113,117,97,110,116,117,109,34,58,91,49,44,49,54,93,44,34,115,99,104,101,109,97,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,53,50,48,99,55,98,97,50,57,48,50,50,57,48,53,98,100,54,101,56,51,98,98,99,98,57,49,51,51,98,53,51,54,56,100,100,100,101,50,99,49,52,100,102,98,51,55,97,99,52,102,53,50,50,51,97,52,56,102,52,55,48,48,50,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,51,51,56,125,44,34,115,104,97,114,100,34,58,34,115,48,48,48,48,48,48,48,48,48,49,34,44,34,116,105,99,107,101,116,34,58,34,116,105,99,107,101,116,45,48,48,50,45,102,105,120,116,117,114,101,34,44,34,118,97,108,117,101,115,34,58,91,45,49,54,44,45,49,53,44,45,49,52,44,45,49,51,44,45,49,50,44,45,49,49,44,45,49,48,44,45,57,93,125,125]
theorem qExact1 : encodeQ q1 = qBytes1 := by decide
theorem qImage1 : encodeQ (qValue schemaRef slice1) = qBytes1 := by rw [qSource1]; exact qExact1
theorem qFullWidth1 : (qValue schemaRef slice1).values.length = 8 := by decide
def slice2 : NativeVectorContext.Slice :=
  let s := NativeVectorArithmeticVectors.sample 1 1 NativeScaleVectors.bound2
  { s with source := { s.source with term := { s.source.term with source :=
    { s.source.term.source with member := { s.source.term.source.member with input :=
      { s.source.term.source.member.input with
        ticket := asciiBytes "ticket-002-fixture", domain := asciiBytes "domain-text-en" } } } } } }
def q2 : QShard := ⟨"ticket-002-fixture","domain-text-en","s0000000002",schemaRef,
    ⟨1,16⟩,[-8,-7,-6,-5,-4,-3,-2,-1]⟩
theorem qSource2 : qValue schemaRef slice2 = q2 := by decide
theorem qChecks2 : QChecks schemaRef slice2 := by decide
def qBytes2 : Bytes := [123,34,107,105,110,100,34,58,34,81,95,83,72,65,82,68,34,44,34,112,97,121,108,111,97,100,34,58,123,34,100,111,109,97,105,110,34,58,34,100,111,109,97,105,110,45,116,101,120,116,45,101,110,34,44,34,113,117,97,110,116,117,109,34,58,91,49,44,49,54,93,44,34,115,99,104,101,109,97,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,53,50,48,99,55,98,97,50,57,48,50,50,57,48,53,98,100,54,101,56,51,98,98,99,98,57,49,51,51,98,53,51,54,56,100,100,100,101,50,99,49,52,100,102,98,51,55,97,99,52,102,53,50,50,51,97,52,56,102,52,55,48,48,50,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,51,51,56,125,44,34,115,104,97,114,100,34,58,34,115,48,48,48,48,48,48,48,48,48,50,34,44,34,116,105,99,107,101,116,34,58,34,116,105,99,107,101,116,45,48,48,50,45,102,105,120,116,117,114,101,34,44,34,118,97,108,117,101,115,34,58,91,45,56,44,45,55,44,45,54,44,45,53,44,45,52,44,45,51,44,45,50,44,45,49,93,125,125]
theorem qExact2 : encodeQ q2 = qBytes2 := by decide
theorem qImage2 : encodeQ (qValue schemaRef slice2) = qBytes2 := by rw [qSource2]; exact qExact2
theorem qFullWidth2 : (qValue schemaRef slice2).values.length = 8 := by decide
def slice3 : NativeVectorContext.Slice :=
  let s := NativeVectorArithmeticVectors.sample 1 1 NativeScaleVectors.bound3
  { s with source := { s.source with term := { s.source.term with source :=
    { s.source.term.source with member := { s.source.term.source.member with input :=
      { s.source.term.source.member.input with
        ticket := asciiBytes "ticket-002-fixture", domain := asciiBytes "domain-text-en" } } } } } }
def q3 : QShard := ⟨"ticket-002-fixture","domain-text-en","s0000000003",schemaRef,
    ⟨1,16⟩,[0,1,2,3,4,5,6,7]⟩
theorem qSource3 : qValue schemaRef slice3 = q3 := by decide
theorem qChecks3 : QChecks schemaRef slice3 := by decide
def qBytes3 : Bytes := [123,34,107,105,110,100,34,58,34,81,95,83,72,65,82,68,34,44,34,112,97,121,108,111,97,100,34,58,123,34,100,111,109,97,105,110,34,58,34,100,111,109,97,105,110,45,116,101,120,116,45,101,110,34,44,34,113,117,97,110,116,117,109,34,58,91,49,44,49,54,93,44,34,115,99,104,101,109,97,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,53,50,48,99,55,98,97,50,57,48,50,50,57,48,53,98,100,54,101,56,51,98,98,99,98,57,49,51,51,98,53,51,54,56,100,100,100,101,50,99,49,52,100,102,98,51,55,97,99,52,102,53,50,50,51,97,52,56,102,52,55,48,48,50,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,51,51,56,125,44,34,115,104,97,114,100,34,58,34,115,48,48,48,48,48,48,48,48,48,51,34,44,34,116,105,99,107,101,116,34,58,34,116,105,99,107,101,116,45,48,48,50,45,102,105,120,116,117,114,101,34,44,34,118,97,108,117,101,115,34,58,91,48,44,49,44,50,44,51,44,52,44,53,44,54,44,55,93,125,125]
theorem qExact3 : encodeQ q3 = qBytes3 := by decide
theorem qImage3 : encodeQ (qValue schemaRef slice3) = qBytes3 := by rw [qSource3]; exact qExact3
theorem qFullWidth3 : (qValue schemaRef slice3).values.length = 8 := by decide
def slice4 : NativeVectorContext.Slice :=
  let s := NativeVectorArithmeticVectors.sample 1 1 NativeScaleVectors.bound4
  { s with source := { s.source with term := { s.source.term with source :=
    { s.source.term.source with member := { s.source.term.source.member with input :=
      { s.source.term.source.member.input with
        ticket := asciiBytes "ticket-002-fixture", domain := asciiBytes "domain-text-en" } } } } } }
def q4 : QShard := ⟨"ticket-002-fixture","domain-text-en","s0000000004",schemaRef,
    ⟨1,16⟩,[8,9,10,11,12,13,14,15]⟩
theorem qSource4 : qValue schemaRef slice4 = q4 := by decide
theorem qChecks4 : QChecks schemaRef slice4 := by decide
def qBytes4 : Bytes := [123,34,107,105,110,100,34,58,34,81,95,83,72,65,82,68,34,44,34,112,97,121,108,111,97,100,34,58,123,34,100,111,109,97,105,110,34,58,34,100,111,109,97,105,110,45,116,101,120,116,45,101,110,34,44,34,113,117,97,110,116,117,109,34,58,91,49,44,49,54,93,44,34,115,99,104,101,109,97,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,53,50,48,99,55,98,97,50,57,48,50,50,57,48,53,98,100,54,101,56,51,98,98,99,98,57,49,51,51,98,53,51,54,56,100,100,100,101,50,99,49,52,100,102,98,51,55,97,99,52,102,53,50,50,51,97,52,56,102,52,55,48,48,50,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,51,51,56,125,44,34,115,104,97,114,100,34,58,34,115,48,48,48,48,48,48,48,48,48,52,34,44,34,116,105,99,107,101,116,34,58,34,116,105,99,107,101,116,45,48,48,50,45,102,105,120,116,117,114,101,34,44,34,118,97,108,117,101,115,34,58,91,56,44,57,44,49,48,44,49,49,44,49,50,44,49,51,44,49,52,44,49,53,93,125,125]
theorem qExact4 : encodeQ q4 = qBytes4 := by decide
theorem qImage4 : encodeQ (qValue schemaRef slice4) = qBytes4 := by rw [qSource4]; exact qExact4
theorem qFullWidth4 : (qValue schemaRef slice4).values.length = 8 := by decide
theorem wrongSchemaKind : ¬ QChecks {schemaRef with kind := .model} slice0 := by decide
theorem wrongHashLength : ¬ QChecks {schemaRef with id := []} slice0 := by decide
theorem emptyVector : ¬ QChecks schemaRef {slice0 with block :=
    (NativeVectorArithmeticVectors.withValues slice0.block []) } := by decide
theorem int64Overflow : ¬ QChecks schemaRef {slice0 with block :=
    (NativeVectorArithmeticVectors.withValues slice0.block [9223372036854775808]) } := by decide
theorem rawBodyChanges : encodeQ {q0 with values := [2,-2,0,4]} ≠ qBytes0 := by decide
end DeltaReduce.NativeVectorArtifactVectors
