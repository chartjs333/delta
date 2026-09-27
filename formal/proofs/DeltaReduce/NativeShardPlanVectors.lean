import DeltaReduce.NativeShardPlanBinding
import DeltaReduce.NativeSchemaVectors
namespace DeltaReduce.NativeShardPlanVectors
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii)
open NativeShardPlanBinding
set_option maxRecDepth 6000
set_option maxHeartbeats 1500000
def bytes0 : Bytes := [52]
theorem valid0 : NativeVoteBytes.DecimalValid bytes0 := by decide
def bytes1 : Bytes := [48]
theorem valid1 : NativeVoteBytes.DecimalValid bytes1 := by decide
def bytes2 : Bytes := [56]
theorem valid2 : NativeVoteBytes.DecimalValid bytes2 := by decide
def bytes3 : Bytes := [100, 101, 99, 111, 100, 101, 114, 46, 98, 105, 97, 115]
theorem valid3 : NativeQJson.TextValid bytes3 := by decide
def entry0 : NativeShardPlanBytes.EntryWire := ⟨bytes0,bytes1,bytes1,bytes2,bytes3,bytes1⟩
theorem syntax0 : NativeShardPlanBytes.EntrySyntax entry0 := ⟨valid0,valid1,valid1,valid2,valid3,valid1⟩
def bytes4 : Bytes := [49]
theorem valid4 : NativeVoteBytes.DecimalValid bytes4 := by decide
def bytes5 : Bytes := [49, 54]
theorem valid5 : NativeVoteBytes.DecimalValid bytes5 := by decide
def bytes6 : Bytes := [101, 109, 98, 101, 100, 100, 105, 110, 103, 46, 119, 101, 105, 103, 104, 116]
theorem valid6 : NativeQJson.TextValid bytes6 := by decide
def entry1 : NativeShardPlanBytes.EntryWire := ⟨bytes2,bytes0,bytes4,bytes5,bytes6,bytes1⟩
theorem syntax1 : NativeShardPlanBytes.EntrySyntax entry1 := ⟨valid2,valid0,valid4,valid5,valid6,valid1⟩
def bytes7 : Bytes := [49, 50]
theorem valid7 : NativeVoteBytes.DecimalValid bytes7 := by decide
def bytes8 : Bytes := [50]
theorem valid8 : NativeVoteBytes.DecimalValid bytes8 := by decide
def entry2 : NativeShardPlanBytes.EntryWire := ⟨bytes2,bytes7,bytes8,bytes5,bytes6,bytes2⟩
theorem syntax2 : NativeShardPlanBytes.EntrySyntax entry2 := ⟨valid2,valid7,valid8,valid5,valid6,valid2⟩
def bytes9 : Bytes := [50, 48]
theorem valid9 : NativeVoteBytes.DecimalValid bytes9 := by decide
def bytes10 : Bytes := [51]
theorem valid10 : NativeVoteBytes.DecimalValid bytes10 := by decide
def entry3 : NativeShardPlanBytes.EntryWire := ⟨bytes2,bytes9,bytes10,bytes5,bytes6,bytes5⟩
theorem syntax3 : NativeShardPlanBytes.EntrySyntax entry3 := ⟨valid2,valid9,valid10,valid5,valid6,valid5⟩
def bytes11 : Bytes := [50, 56]
theorem valid11 : NativeVoteBytes.DecimalValid bytes11 := by decide
def bytes12 : Bytes := [50, 52]
theorem valid12 : NativeVoteBytes.DecimalValid bytes12 := by decide
def entry4 : NativeShardPlanBytes.EntryWire := ⟨bytes2,bytes11,bytes0,bytes5,bytes6,bytes12⟩
theorem syntax4 : NativeShardPlanBytes.EntrySyntax entry4 := ⟨valid2,valid11,valid0,valid5,valid6,valid12⟩
def bytes13 : Bytes := [115, 104, 97, 50, 53, 54, 58, 99, 99, 57, 56, 102, 49, 53, 97, 99, 50, 48, 102, 99, 51, 101, 100, 50, 54, 53, 99, 98, 55, 54, 54, 56, 50, 99, 97, 49, 53, 97, 57, 51, 54, 101, 50, 52, 54, 54, 48, 97, 54, 53, 49, 101, 50, 98, 56, 102, 56, 49, 54, 51, 56, 97, 98, 98, 51, 50, 54, 53, 99, 98, 54]
theorem valid13 : NativeQJson.TextValid bytes13 := by decide
def bytes14 : Bytes := [115, 104, 97, 50, 53, 54, 58, 102, 52, 51, 99, 48, 50, 53, 57, 55, 52, 57, 98, 49, 53, 97, 101, 48, 100, 48, 49, 53, 52, 97, 54, 101, 57, 48, 57, 52, 55, 55, 52, 99, 55, 101, 97, 54, 53, 101, 53, 53, 97, 100, 101, 102, 98, 97, 101, 97, 52, 48, 48, 97, 54, 50, 48, 49, 97, 99, 98, 54, 50, 51, 57]
theorem valid14 : NativeQJson.TextValid bytes14 := by decide
def bytes15 : Bytes := [115, 104, 97, 50, 53, 54, 58, 49, 55, 99, 56, 100, 50, 51, 55, 57, 48, 48, 52, 55, 57, 54, 54, 101, 52, 50, 102, 51, 50, 48, 52, 53, 48, 50, 54, 50, 51, 99, 55, 52, 97, 48, 102, 102, 48, 51, 56, 51, 51, 49, 57, 100, 50, 51, 101, 54, 55, 97, 98, 49, 53, 99, 102, 57, 50, 102, 101, 51, 101, 54, 49]
theorem valid15 : NativeQJson.TextValid bytes15 := by decide
def bytes16 : Bytes := [115, 104, 97, 50, 53, 54, 58, 52, 51, 52, 48, 57, 50, 102, 56, 50, 49, 56, 56, 51, 51, 55, 100, 48, 97, 50, 55, 51, 99, 100, 49, 51, 99, 57, 51, 101, 48, 54, 100, 101, 99, 53, 53, 97, 101, 56, 52, 50, 100, 102, 48, 52, 57, 56, 101, 52, 100, 53, 50, 99, 97, 97, 49, 100, 49, 56, 52, 52, 50, 48, 53]
theorem valid16 : NativeQJson.TextValid bytes16 := by decide
def bytes17 : Bytes := [49, 46, 48, 46, 48]
theorem valid17 : NativeQJson.TextValid bytes17 := by decide
def bytes18 : Bytes := [51, 54]
theorem valid18 : NativeVoteBytes.DecimalValid bytes18 := by decide
def bytes19 : Bytes := [83, 72, 65, 82, 68, 95, 80, 76, 65, 78]
theorem valid19 : NativeQJson.TextValid bytes19 := by decide
def wire : NativeShardPlanBytes.Wire := ⟨[entry0,entry1,entry2,entry3,entry4],bytes13,bytes14,bytes15,bytes16,bytes17,bytes5,bytes18,bytes19⟩
theorem wireSyntax : NativeShardPlanBytes.Syntax wire := by
  refine ⟨by decide,?_,valid13,valid14,valid15,valid16,valid17,valid5,valid18,valid19⟩
  change ∀ e ∈ [entry0,entry1,entry2,entry3,entry4], NativeShardPlanBytes.EntrySyntax e
  simp only [List.forall_mem_cons]
  exact ⟨syntax0,syntax1,syntax2,syntax3,syntax4,by simp⟩
def original : Bytes := [123,34,101,110,116,114,105,101,115,34,58,91,123,34,101,108,101,109,101,110,116,95,99,111,117,110,116,34,58,52,44,34,101,108,101,109,101,110,116,95,115,116,97,114,116,34,58,48,44,34,111,114,100,105,110,97,108,34,58,48,44,34,112,97,121,108,111,97,100,95,98,121,116,101,115,34,58,56,44,34,115,101,103,109,101,110,116,95,105,100,34,58,34,100,101,99,111,100,101,114,46,98,105,97,115,34,44,34,115,101,103,109,101,110,116,95,111,102,102,115,101,116,34,58,48,125,44,123,34,101,108,101,109,101,110,116,95,99,111,117,110,116,34,58,56,44,34,101,108,101,109,101,110,116,95,115,116,97,114,116,34,58,52,44,34,111,114,100,105,110,97,108,34,58,49,44,34,112,97,121,108,111,97,100,95,98,121,116,101,115,34,58,49,54,44,34,115,101,103,109,101,110,116,95,105,100,34,58,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,34,44,34,115,101,103,109,101,110,116,95,111,102,102,115,101,116,34,58,48,125,44,123,34,101,108,101,109,101,110,116,95,99,111,117,110,116,34,58,56,44,34,101,108,101,109,101,110,116,95,115,116,97,114,116,34,58,49,50,44,34,111,114,100,105,110,97,108,34,58,50,44,34,112,97,121,108,111,97,100,95,98,121,116,101,115,34,58,49,54,44,34,115,101,103,109,101,110,116,95,105,100,34,58,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,34,44,34,115,101,103,109,101,110,116,95,111,102,102,115,101,116,34,58,56,125,44,123,34,101,108,101,109,101,110,116,95,99,111,117,110,116,34,58,56,44,34,101,108,101,109,101,110,116,95,115,116,97,114,116,34,58,50,48,44,34,111,114,100,105,110,97,108,34,58,51,44,34,112,97,121,108,111,97,100,95,98,121,116,101,115,34,58,49,54,44,34,115,101,103,109,101,110,116,95,105,100,34,58,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,34,44,34,115,101,103,109,101,110,116,95,111,102,102,115,101,116,34,58,49,54,125,44,123,34,101,108,101,109,101,110,116,95,99,111,117,110,116,34,58,56,44,34,101,108,101,109,101,110,116,95,115,116,97,114,116,34,58,50,56,44,34,111,114,100,105,110,97,108,34,58,52,44,34,112,97,121,108,111,97,100,95,98,121,116,101,115,34,58,49,54,44,34,115,101,103,109,101,110,116,95,105,100,34,58,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,34,44,34,115,101,103,109,101,110,116,95,111,102,102,115,101,116,34,58,50,52,125,93,44,34,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100,34,58,34,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,34,44,34,112,97,114,97,109,101,116,101,114,95,115,99,104,101,109,97,95,105,100,34,58,34,115,104,97,50,53,54,58,102,52,51,99,48,50,53,57,55,52,57,98,49,53,97,101,48,100,48,49,53,52,97,54,101,57,48,57,52,55,55,52,99,55,101,97,54,53,101,53,53,97,100,101,102,98,97,101,97,52,48,48,97,54,50,48,49,97,99,98,54,50,51,57,34,44,34,112,114,111,102,105,108,101,95,105,100,34,58,34,115,104,97,50,53,54,58,49,55,99,56,100,50,51,55,57,48,48,52,55,57,54,54,101,52,50,102,51,50,48,52,53,48,50,54,50,51,99,55,52,97,48,102,102,48,51,56,51,51,49,57,100,50,51,101,54,55,97,98,49,53,99,102,57,50,102,101,51,101,54,49,34,44,34,115,99,97,108,101,95,116,97,98,108,101,95,105,100,34,58,34,115,104,97,50,53,54,58,52,51,52,48,57,50,102,56,50,49,56,56,51,51,55,100,48,97,50,55,51,99,100,49,51,99,57,51,101,48,54,100,101,99,53,53,97,101,56,52,50,100,102,48,52,57,56,101,52,100,53,50,99,97,97,49,100,49,56,52,52,50,48,53,34,44,34,115,99,104,101,109,97,95,118,101,114,115,105,111,110,34,58,34,49,46,48,46,48,34,44,34,116,97,114,103,101,116,95,112,97,121,108,111,97,100,95,98,121,116,101,115,34,58,49,54,44,34,116,111,116,97,108,95,101,108,101,109,101,110,116,115,34,58,51,54,44,34,116,121,112,101,95,110,97,109,101,34,58,34,83,72,65,82,68,95,80,76,65,78,34,125]
theorem originalLength : original.length = 1079 := rfl
theorem originalEncoded : NativeShardPlanBytes.encode wire = original := rfl
theorem decodedWire : NativeShardPlanBytes.decode original = some wire := by
  rw [← originalEncoded]
  apply NativeShardPlanBytes.decodeEncoded wire wireSyntax
  rw [originalEncoded,originalLength]; decide
def plan : Plan := ⟨wire,[⟨4,0,0,8,bytes3,0⟩,⟨8,4,1,16,bytes6,0⟩,⟨8,12,2,16,bytes6,8⟩,⟨8,20,3,16,bytes6,16⟩,⟨8,28,4,16,bytes6,24⟩],16,36⟩
theorem interpretedPlan : interpret wire = some plan := by decide
theorem computedPlan : NativeShardPartition.build NativeSchemaVectors.schema
    plan.target = some plan.entries := by decide
def planId : Bytes := ascii "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1"
/-- THREE-PREIMAGE SYNTHETIC ADAPTER, NOT SHA OR SOURCE AUTHENTICATION. -/
def fixtureHash (raw : Bytes) : Bytes :=
  if raw = hashInput original then planId else NativeSchemaVectors.fixtureHash raw
theorem planHash : fixtureHash (hashInput original) = planId := by simp [fixtureHash]
theorem schemaHash : fixtureHash (NativeSchemaVectors.original) = NativeSchemaVectors.schemaId := by
  have different : NativeSchemaVectors.original ≠ hashInput original := by
    intro same
    have len := congrArg List.length same
    simp [hashInput,ascii,originalLength,NativeSchemaVectors.originalLength] at len
  simp [fixtureHash,different,NativeSchemaVectors.schemaHash]
theorem scaleHash : fixtureHash (NativeScaleBinding.hashInput NativeScaleVectors.original) = NativeScaleVectors.originalId := by
  have different : NativeScaleBinding.hashInput NativeScaleVectors.original ≠ hashInput original := by
    intro same
    have len := congrArg List.length same
    simp [hashInput,NativeScaleBinding.hashInput,ascii,originalLength,NativeScaleVectors.originalLength] at len
  simp [fixtureHash,different,NativeSchemaVectors.scaleHash]
def inputs : NativeSchemaBinding.Bound :=
  ⟨NativeSchemaVectors.schema,NativeScaleVectors.table⟩
theorem decodedInputs : NativeSchemaBinding.bind fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original = some inputs :=
  NativeSchemaBinding.bindFromSource ⟨NativeSchemaVectors.decodedSchema,
    NativeScaleVectors.decodedTable,schemaHash,by decide,by decide⟩
theorem planLinks : Links fixtureHash NativeScaleVectors.original inputs plan :=
  ⟨rfl,rfl,rfl,rfl,rfl,scaleHash.symm,rfl,by decide⟩
def bound : Bound := ⟨inputs,plan⟩
theorem boundPlan : bind fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original original = some bound :=
  bindFromSource ⟨decodedInputs,decodedWire,interpretedPlan,computedPlan,planLinks⟩
theorem allCoordinatesCovered (c : Nat) (inside : c < 36) :
    ∃ e ∈ plan.entries, e.start ≤ c ∧ c < e.start+e.count :=
  completeCoverage boundPlan c inside
theorem noOverlapOrOrdinalReuse : plan.entries.Pairwise
    (fun x y => x.start+x.count ≤ y.start ∧ x.ordinal < y.ordinal) := noOverlap boundPlan
theorem scaleQ0 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame0 = some NativeScaleVectors.bound0 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined0,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined0 : bindQ fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original original NativeQBytesVectors.frame0 =
    some ⟨bound,NativeScaleVectors.bound0⟩ :=
  qFromSource ⟨boundPlan,scaleQ0,rfl,planHash.symm,by decide⟩
theorem scaleQ1 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame1 = some NativeScaleVectors.bound1 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined1,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined1 : bindQ fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original original NativeQBytesVectors.frame1 =
    some ⟨bound,NativeScaleVectors.bound1⟩ :=
  qFromSource ⟨boundPlan,scaleQ1,rfl,planHash.symm,by decide⟩
theorem scaleQ2 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame2 = some NativeScaleVectors.bound2 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined2,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined2 : bindQ fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original original NativeQBytesVectors.frame2 =
    some ⟨bound,NativeScaleVectors.bound2⟩ :=
  qFromSource ⟨boundPlan,scaleQ2,rfl,planHash.symm,by decide⟩
theorem scaleQ3 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame3 = some NativeScaleVectors.bound3 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined3,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined3 : bindQ fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original original NativeQBytesVectors.frame3 =
    some ⟨bound,NativeScaleVectors.bound3⟩ :=
  qFromSource ⟨boundPlan,scaleQ3,rfl,planHash.symm,by decide⟩
theorem scaleQ4 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame4 = some NativeScaleVectors.bound4 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined4,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined4 : bindQ fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original original NativeQBytesVectors.frame4 =
    some ⟨bound,NativeScaleVectors.bound4⟩ :=
  qFromSource ⟨boundPlan,scaleQ4,rfl,planHash.symm,by decide⟩
theorem emptyBytes : NativeShardPlanBytes.decode [] = none := by decide
theorem zeroTarget : NativeShardPartition.build NativeSchemaVectors.schema 0 = none := by decide
theorem oddTarget : NativeShardPartition.build NativeSchemaVectors.schema 3 = none := by decide
theorem largeTarget : NativeShardPartition.build NativeSchemaVectors.schema 1048578 = none := by decide
theorem fuelExhausted : NativeShardPartition.chunks 2 2 (ascii "x") 0 0 5 0 = none := by decide
theorem zeroWidth : NativeShardPartition.chunks 2 0 (ascii "x") 0 0 5 0 = none := by decide
theorem partialFinalShard : NativeShardPartition.chunks 3 2 (ascii "x") 0 0 5 0 = some [⟨2,0,0,4,ascii "x",0⟩,⟨2,2,1,4,ascii "x",2⟩,⟨1,4,2,2,ascii "x",4⟩] := by decide
theorem missingEntry : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some (plan.entries.drop 1) := by decide
theorem duplicateEntry : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some (plan.entries ++ plan.entries.take 1) := by decide
theorem reorderedEntries : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some plan.entries.reverse := by decide
theorem changedCount : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some (plan.entries.map fun e => {e with count := e.count+1}) := by decide
theorem changedStart : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some (plan.entries.map fun e => {e with start := e.start+1}) := by decide
theorem changedOffset : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some (plan.entries.map fun e => {e with offset := e.offset+1}) := by decide
theorem changedOrdinal : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some (plan.entries.map fun e => {e with ordinal := 0}) := by decide
theorem changedPayloadBytes : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some (plan.entries.map fun e => {e with payload := e.payload+1}) := by decide
theorem changedSegment : NativeShardPartition.build NativeSchemaVectors.schema plan.target ≠ some (plan.entries.map fun e => {e with name := ascii "other"}) := by decide
theorem wrongVersion : ¬ Links (fun _ => plan.wire.scale) [] inputs {plan with wire := {wire with version := ascii "2.0.0"}} := by decide
theorem wrongTotal : ¬ Links (fun _ => plan.wire.scale) [] inputs {plan with total := 35} := by decide
theorem missingScaleHash : ¬ Links (fun _ => []) [] inputs plan := by decide
theorem quotedCount : NativeShardPlanBytes.readEntry (ascii "{\"element_count\":\"4\"}") = none := by decide
theorem negativeCount : NativeShardPlanBytes.readEntry (ascii "{\"element_count\":-1}") = none := by decide
theorem trailingComma : NativeShardPlanBytes.readEntries (ascii ",]") = none := by decide
theorem changedPayloadStillJoins : bindQ fixtureHash NativeSchemaVectors.original
    NativeScaleVectors.original original
    (NativeQBytes.encodeFrame NativeQBytesVectors.header0 [2,0,254,255,0,0,4,0]) =
    some ⟨bound,⟨NativeScaleVectors.table,NativeScaleVectors.changedBlock,
      NativeScaleVectors.segment0⟩⟩ := by
  apply qFromSource
  refine ⟨boundPlan,?_,rfl,planHash.symm,by decide⟩
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.changedPayloadWithOldShaStillAccepted,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
end DeltaReduce.NativeShardPlanVectors
