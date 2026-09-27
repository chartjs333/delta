import DeltaReduce.NativeSchemaBinding
import DeltaReduce.NativeScaleVectors
namespace DeltaReduce.NativeSchemaVectors
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii)
open NativeSchemaBinding
set_option maxRecDepth 4000
set_option maxHeartbeats 1000000

def bytes0 : Bytes := [102,108,111,97,116,51,50]
theorem text0 : NativeQJson.TextValid bytes0 := by decide
def bytes1 : Bytes := [100,101,99,111,100,101,114,46,98,105,97,115]
theorem text1 : NativeQJson.TextValid bytes1 := by decide
def bytes2 : Bytes := [52]
theorem decimal2 : NativeVoteBytes.DecimalValid bytes2 := by decide
def parameter0 : NativeSchemaBytes.Parameter := ⟨bytes0,bytes1,[bytes2],true⟩
theorem parameterSyntax0 : NativeSchemaBytes.ParameterSyntax parameter0 := by
  refine ⟨text0,text1,by decide,?_⟩
  change ∀ d ∈ [bytes2], NativeVoteBytes.DecimalValid d
  simp only [List.forall_mem_cons]
  exact ⟨decimal2,by simp⟩
def tensor0 : Tensor := ⟨parameter0,[4]⟩
theorem tensorChecks0 : TensorChecks tensor0 := by decide
def bytes3 : Bytes := [101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116]
theorem text3 : NativeQJson.TextValid bytes3 := by decide
def bytes4 : Bytes := [56]
theorem decimal4 : NativeVoteBytes.DecimalValid bytes4 := by decide
def parameter1 : NativeSchemaBytes.Parameter := ⟨bytes0,bytes3,[bytes4,bytes2],true⟩
theorem parameterSyntax1 : NativeSchemaBytes.ParameterSyntax parameter1 := by
  refine ⟨text0,text3,by decide,?_⟩
  change ∀ d ∈ [bytes4,bytes2], NativeVoteBytes.DecimalValid d
  simp only [List.forall_mem_cons]
  exact ⟨decimal4,decimal2,by simp⟩
def tensor1 : Tensor := ⟨parameter1,[8,4]⟩
theorem tensorChecks1 : TensorChecks tensor1 := by decide
def bytes5 : Bytes := [102,114,111,122,101,110,46,115,99,97,108,101]
theorem text5 : NativeQJson.TextValid bytes5 := by decide
def parameter2 : NativeSchemaBytes.Parameter := ⟨bytes0,bytes5,[],false⟩
theorem parameterSyntax2 : NativeSchemaBytes.ParameterSyntax parameter2 := by
  refine ⟨text0,text5,by decide,?_⟩
  change ∀ d ∈ [], NativeVoteBytes.DecimalValid d
  simp

def tensor2 : Tensor := ⟨parameter2,[]⟩
theorem tensorChecks2 : TensorChecks tensor2 := by decide
def bytes6 : Bytes := [108,109,95,104,101,97,100,46,119,101,105,103,104,116]
theorem text6 : NativeQJson.TextValid bytes6 := by decide
def bytes7 : Bytes := [79,77,73,84,95,70,82,79,90,69,78]
theorem text7 : NativeQJson.TextValid bytes7 := by decide
def bytes8 : Bytes := [49,46,48,46,48]
theorem text8 : NativeQJson.TextValid bytes8 := by decide
def wire : NativeSchemaBytes.Wire := ⟨bytes7,[parameter0,parameter1,parameter2],bytes8,[(bytes6,bytes3)]⟩
theorem parametersSyntax : ∀ p ∈ wire.parameters, NativeSchemaBytes.ParameterSyntax p := by
  change ∀ p ∈ [parameter0,parameter1,parameter2], NativeSchemaBytes.ParameterSyntax p
  simp only [List.forall_mem_cons]
  exact ⟨parameterSyntax0,parameterSyntax1,parameterSyntax2,by simp⟩
theorem aliasesSyntax : ∀ a ∈ wire.aliases, NativeSchemaBytes.AliasSyntax a := by
  simp only [wire,List.forall_mem_cons]
  exact ⟨⟨text6,text3⟩,by simp⟩
theorem wireSyntax : NativeSchemaBytes.Syntax wire :=
  ⟨text7,by decide,parametersSyntax,text8,by decide,aliasesSyntax⟩
def original : Bytes := [123,34,102,114,111,122,101,110,95,111,109,105,115,115,105,111,110,95,112,111,108,105,99,121,34,58,34,79,77,73,84,95,70,82,79,90,69,78,34,44,34,112,97,114,97,109,101,116,101,114,115,34,58,91,123,34,108,111,103,105,99,97,108,95,100,116,121,112,101,34,58,34,102,108,111,97,116,51,50,34,44,34,110,97,109,101,34,58,34,100,101,99,111,100,101,114,46,98,105,97,115,34,44,34,115,104,97,112,101,34,58,91,52,93,44,34,116,114,97,105,110,97,98,108,101,34,58,116,114,117,101,125,44,123,34,108,111,103,105,99,97,108,95,100,116,121,112,101,34,58,34,102,108,111,97,116,51,50,34,44,34,110,97,109,101,34,58,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,34,44,34,115,104,97,112,101,34,58,91,56,44,52,93,44,34,116,114,97,105,110,97,98,108,101,34,58,116,114,117,101,125,44,123,34,108,111,103,105,99,97,108,95,100,116,121,112,101,34,58,34,102,108,111,97,116,51,50,34,44,34,110,97,109,101,34,58,34,102,114,111,122,101,110,46,115,99,97,108,101,34,44,34,115,104,97,112,101,34,58,91,93,44,34,116,114,97,105,110,97,98,108,101,34,58,102,97,108,115,101,125,93,44,34,115,99,104,101,109,97,95,118,101,114,115,105,111,110,34,58,34,49,46,48,46,48,34,44,34,116,105,101,100,95,97,108,105,97,115,101,115,34,58,123,34,108,109,95,104,101,97,100,46,119,101,105,103,104,116,34,58,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,34,125,125]
theorem originalLength : original.length = 376 := rfl
theorem originalEncoded : NativeSchemaBytes.encode wire = original := rfl
theorem decodedWire : NativeSchemaBytes.decode original = some wire := by
  rw [← originalEncoded]
  apply NativeSchemaBytes.decodeEncoded wire wireSyntax
  rw [originalEncoded,originalLength]; decide
def schema : Schema := ⟨wire,[tensor0,tensor1,tensor2]⟩
theorem allTensors : ∀ p ∈ schema.parameters, TensorChecks p := by
  change ∀ p ∈ [tensor0,tensor1,tensor2], TensorChecks p
  simp only [List.forall_mem_cons]
  exact ⟨tensorChecks0,tensorChecks1,tensorChecks2,by simp⟩
theorem schemaSource : Source wire schema :=
  ⟨rfl,tensorsFromChecks schema.parameters allTensors,by decide⟩
theorem decodedSchema : decode original = some schema :=
  decodedFromComponents decodedWire (interpretFromSource schemaSource)
def schemaId : Bytes := ascii "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239"
/-- TWO-PREIMAGE SYNTHETIC ADAPTER, NOT VERIFIED SHA OR PRODUCER AUTHORITY. -/
def fixtureHash (raw : Bytes) : Bytes :=
  if raw = original then schemaId else NativeScaleVectors.fixtureHash raw
theorem schemaHash : fixtureHash original = schemaId := by simp [fixtureHash]
theorem scaleHash : fixtureHash (NativeScaleBinding.hashInput NativeScaleVectors.original) =
    NativeScaleVectors.originalId := by
  have different : NativeScaleBinding.hashInput NativeScaleVectors.original ≠ original := by
    intro same
    have len := congrArg List.length same
    simp [NativeScaleBinding.hashInput,ascii,
      NativeScaleVectors.originalLength,originalLength] at len
  simp [fixtureHash,different,NativeScaleVectors.originalHash]
theorem scaleLinks : Links fixtureHash original schema NativeScaleVectors.table :=
  ⟨schemaHash,by decide,by decide⟩
theorem boundTable : bind fixtureHash original NativeScaleVectors.original =
    some ⟨schema,NativeScaleVectors.table⟩ :=
  bindFromSource ⟨decodedSchema,NativeScaleVectors.decodedTable,scaleLinks⟩
theorem frozenStillPresent : tensor2 ∈ schema.parameters := by decide
theorem frozenExcluded : tensor2 ∉ schema.included := by decide
theorem scalarSize : tensor2.count = 1 := rfl
theorem orderedIncluded : schema.included = [tensor0,tensor1] := by decide
theorem exactTotal : schema.total = 36 := rfl
theorem scaleQ0 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame0 = some NativeScaleVectors.bound0 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined0,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined0 : bindQ fixtureHash original NativeScaleVectors.original
    NativeQBytesVectors.frame0 = some ⟨schema,NativeScaleVectors.bound0⟩ :=
  qFromSource ⟨decodedSchema,scaleQ0,scaleLinks⟩
theorem scaleQ1 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame1 = some NativeScaleVectors.bound1 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined1,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined1 : bindQ fixtureHash original NativeScaleVectors.original
    NativeQBytesVectors.frame1 = some ⟨schema,NativeScaleVectors.bound1⟩ :=
  qFromSource ⟨decodedSchema,scaleQ1,scaleLinks⟩
theorem scaleQ2 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame2 = some NativeScaleVectors.bound2 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined2,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined2 : bindQ fixtureHash original NativeScaleVectors.original
    NativeQBytesVectors.frame2 = some ⟨schema,NativeScaleVectors.bound2⟩ :=
  qFromSource ⟨decodedSchema,scaleQ2,scaleLinks⟩
theorem scaleQ3 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame3 = some NativeScaleVectors.bound3 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined3,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined3 : bindQ fixtureHash original NativeScaleVectors.original
    NativeQBytesVectors.frame3 = some ⟨schema,NativeScaleVectors.bound3⟩ :=
  qFromSource ⟨decodedSchema,scaleQ3,scaleLinks⟩
theorem scaleQ4 : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original
    NativeQBytesVectors.frame4 = some NativeScaleVectors.bound4 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined4,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
theorem joined4 : bindQ fixtureHash original NativeScaleVectors.original
    NativeQBytesVectors.frame4 = some ⟨schema,NativeScaleVectors.bound4⟩ :=
  qFromSource ⟨decodedSchema,scaleQ4,scaleLinks⟩
theorem zeroDimension : tensor {parameter0 with shape := [ascii "0"]} = none := by decide
theorem negativeDimension : tensor {parameter0 with shape := [ascii "-1"]} = none := by decide
theorem leadingZeroDimension : tensor {parameter0 with shape := [ascii "04"]} = none := by decide
theorem productOverflow : tensor {parameter0 with shape := [ascii "1073741824",ascii "2"]} = none := by decide
theorem rankOverflow : tensor {parameter0 with shape := List.replicate 33 (ascii "1")} = none := by decide
theorem wrongDtype : tensor {parameter0 with dtype := ascii "int16"} = none := by decide
theorem badFirstName : tensor {parameter0 with name := ascii ".weight"} = none := by decide
theorem badRestName : tensor {parameter0 with name := ascii "a/b"} = none := by decide
theorem schemaName256 : NameValid (List.replicate 256 97) := by decide
theorem nativeName256Rejects : ¬ NativeQHeader.Token (List.replicate 256 97) := by decide
theorem schemaName257Rejects : ¬ NameValid (List.replicate 257 97) := by decide
theorem wrongVersion : ¬ Checks {schema with wire := {wire with version := ascii "2.0.0"}} := by decide
theorem wrongPolicy : ¬ Checks {schema with wire := {wire with policy := ascii "OMIT_ALL"}} := by decide
theorem duplicateParameter : ¬ Checks {schema with parameters := [tensor0,tensor0,tensor1]} := by decide
theorem reorderedParameters : ¬ Checks {schema with parameters := [tensor1,tensor0,tensor2]} := by decide
theorem missingAliasOwner : ¬ Checks {schema with wire := {wire with aliases := [(ascii "head",ascii "missing")]}} := by decide
theorem aliasIsParameter : ¬ Checks {schema with wire := {wire with aliases := [(parameter0.name,parameter1.name)]}} := by decide
theorem duplicateAlias : ¬ Checks {schema with wire := {wire with aliases := wire.aliases ++ wire.aliases}} := by decide
theorem reorderedAliases : ¬ Checks {schema with wire := {wire with aliases := [(ascii "z",parameter0.name),(ascii "a",parameter1.name)]}} := by decide
theorem includeFrozenChangesRows : ¬ Links (fun _ => schemaId) [] {schema with wire := {wire with policy := ascii "INCLUDE_ALL"}} NativeScaleVectors.table := by decide
theorem changedShape : ¬ Links (fun _ => schemaId) [] {schema with parameters := [tensor0,{tensor1 with dims := [4,4]},tensor2]} NativeScaleVectors.table := by decide
theorem changedSameSizeName : ¬ Links (fun _ => schemaId) [] {schema with parameters := [{tensor0 with wire := {parameter0 with name := ascii "decoder.other"}},tensor1,tensor2]} NativeScaleVectors.table := by decide
theorem extraScaleRow : ¬ Links (fun _ => schemaId) [] schema {NativeScaleVectors.table with segments := NativeScaleVectors.table.segments ++ [NativeScaleVectors.segment0]} := by decide
theorem missingHash : ¬ Links (fun _ => []) original schema NativeScaleVectors.table := by decide
theorem emptyBytes : decode [] = none := by decide
theorem wrongShapeDelimiter : NativeSchemaBytes.readShape (ascii "4}") = none := by decide
theorem trailingShapeComma : NativeSchemaBytes.readShape (ascii "4,]") = none := by decide
theorem quotedTrainable : NativeSchemaBytes.readBool (ascii "\"true\"") = none := by decide
theorem numericTrainable : NativeSchemaBytes.readBool (ascii "1") = none := by decide
theorem booleanDimension : NativeSchemaBytes.readShape (ascii "true]") = none := by decide
theorem emptyShape : NativeSchemaBytes.readShape (ascii "]") = some ([],[]) := by decide
theorem extraAliasComma : NativeSchemaBytes.readAliases (ascii "\"a\":\"b\",}") = none := by decide
theorem allFrozen : ¬ Checks {schema with wire := {wire with aliases := []}, parameters := [tensor2]} := by decide
theorem includeAllHasScalar : ({schema with wire := {wire with policy := ascii "INCLUDE_ALL"}} : Schema).total = 37 := by decide
theorem changedPayloadStillJoins : bindQ fixtureHash original NativeScaleVectors.original
    (NativeQBytes.encodeFrame NativeQBytesVectors.header0 [2,0,254,255,0,0,4,0]) =
    some ⟨schema,⟨NativeScaleVectors.table,NativeScaleVectors.changedBlock,
      NativeScaleVectors.segment0⟩⟩ := by
  apply qFromSource
  refine ⟨decodedSchema,?_,scaleLinks⟩
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.changedPayloadWithOldShaStillAccepted,
    by decide,scaleHash,rfl,rfl,rfl,by decide,by decide⟩
end DeltaReduce.NativeSchemaVectors
