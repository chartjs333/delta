import DeltaReduce.NativeScaleBinding
import DeltaReduce.NativeQHeaderVectors
namespace DeltaReduce.NativeScaleVectors
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii ContentId)
open NativeScaleBinding
set_option maxRecDepth 4000
set_option maxHeartbeats 1000000

def bytes0 : Bytes := [52]
theorem natural0 : NativeQJson.ValueValid .natural bytes0 := by decide
def bytes1 : Bytes := [48]
theorem natural1 : NativeQJson.ValueValid .natural bytes1 := by decide
def bytes2 : Bytes := [49]
theorem text2 : NativeQJson.ValueValid .text bytes2 := by decide
def bytes3 : Bytes := [100,101,99,111,100,101,114,46,98,105,97,115]
theorem text3 : NativeQJson.ValueValid .text bytes3 := by decide
def wire0 : NativeScaleBytes.SegmentWire := ⟨bytes0,bytes1,bytes0,bytes2,bytes3,bytes1⟩
theorem syntax0 : NativeScaleBytes.SegmentSyntax wire0 := ⟨natural0,natural1,natural0,text2,text3,natural1⟩
def segment0 : Segment := ⟨wire0,4,0,1,4,0⟩
theorem valid0 : SegmentValid segment0 := by decide
def bytes4 : Bytes := [51,50]
theorem natural4 : NativeQJson.ValueValid .natural bytes4 := by decide
def bytes5 : Bytes := [49,54]
theorem natural5 : NativeQJson.ValueValid .natural bytes5 := by decide
def bytes6 : Bytes := [101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116]
theorem text6 : NativeQJson.ValueValid .text bytes6 := by decide
theorem natural2 : NativeQJson.ValueValid .natural bytes2 := by decide
def wire1 : NativeScaleBytes.SegmentWire := ⟨bytes4,bytes0,bytes5,bytes2,bytes6,bytes2⟩
theorem syntax1 : NativeScaleBytes.SegmentSyntax wire1 := ⟨natural4,natural0,natural5,text2,text6,natural2⟩
def segment1 : Segment := ⟨wire1,32,4,1,16,1⟩
theorem valid1 : SegmentValid segment1 := by decide
def bytes7 : Bytes := [115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54]
theorem text7 : NativeQJson.ValueValid .text bytes7 := by decide
def bytes8 : Bytes := [115,104,97,50,53,54,58,102,52,51,99,48,50,53,57,55,52,57,98,49,53,97,101,48,100,48,49,53,52,97,54,101,57,48,57,52,55,55,52,99,55,101,97,54,53,101,53,53,97,100,101,102,98,97,101,97,52,48,48,97,54,50,48,49,97,99,98,54,50,51,57]
theorem text8 : NativeQJson.ValueValid .text bytes8 := by decide
def bytes9 : Bytes := [115,104,97,50,53,54,58,49,55,99,56,100,50,51,55,57,48,48,52,55,57,54,54,101,52,50,102,51,50,48,52,53,48,50,54,50,51,99,55,52,97,48,102,102,48,51,56,51,51,49,57,100,50,51,101,54,55,97,98,49,53,99,102,57,50,102,101,51,101,54,49]
theorem text9 : NativeQJson.ValueValid .text bytes9 := by decide
def bytes10 : Bytes := [49,46,48,46,48]
theorem text10 : NativeQJson.ValueValid .text bytes10 := by decide
def bytes11 : Bytes := [51,54]
theorem natural11 : NativeQJson.ValueValid .natural bytes11 := by decide
def bytes12 : Bytes := [81,85,65,78,84,73,90,65,84,73,79,78,95,83,67,65,76,69,95,84,65,66,76,69]
theorem text12 : NativeQJson.ValueValid .text bytes12 := by decide
def scaleWire : NativeScaleBytes.Wire := ⟨bytes7,bytes8,bytes9,bytes10,[wire0,wire1],bytes11,bytes12⟩
def original : Bytes := [123,34,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100,34,58,34,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,34,44,34,112,97,114,97,109,101,116,101,114,95,115,99,104,101,109,97,95,105,100,34,58,34,115,104,97,50,53,54,58,102,52,51,99,48,50,53,57,55,52,57,98,49,53,97,101,48,100,48,49,53,52,97,54,101,57,48,57,52,55,55,52,99,55,101,97,54,53,101,53,53,97,100,101,102,98,97,101,97,52,48,48,97,54,50,48,49,97,99,98,54,50,51,57,34,44,34,112,114,111,102,105,108,101,95,105,100,34,58,34,115,104,97,50,53,54,58,49,55,99,56,100,50,51,55,57,48,48,52,55,57,54,54,101,52,50,102,51,50,48,52,53,48,50,54,50,51,99,55,52,97,48,102,102,48,51,56,51,51,49,57,100,50,51,101,54,55,97,98,49,53,99,102,57,50,102,101,51,101,54,49,34,44,34,115,99,104,101,109,97,95,118,101,114,115,105,111,110,34,58,34,49,46,48,46,48,34,44,34,115,101,103,109,101,110,116,115,34,58,91,123,34,101,108,101,109,101,110,116,95,99,111,117,110,116,34,58,52,44,34,101,108,101,109,101,110,116,95,115,116,97,114,116,34,58,48,44,34,113,117,97,110,116,117,109,34,58,123,34,100,101,110,111,109,105,110,97,116,111,114,34,58,52,44,34,110,117,109,101,114,97,116,111,114,34,58,34,49,34,125,44,34,115,101,103,109,101,110,116,95,105,100,34,58,34,100,101,99,111,100,101,114,46,98,105,97,115,34,44,34,115,101,103,109,101,110,116,95,111,114,100,105,110,97,108,34,58,48,125,44,123,34,101,108,101,109,101,110,116,95,99,111,117,110,116,34,58,51,50,44,34,101,108,101,109,101,110,116,95,115,116,97,114,116,34,58,52,44,34,113,117,97,110,116,117,109,34,58,123,34,100,101,110,111,109,105,110,97,116,111,114,34,58,49,54,44,34,110,117,109,101,114,97,116,111,114,34,58,34,49,34,125,44,34,115,101,103,109,101,110,116,95,105,100,34,58,34,101,109,98,101,100,100,105,110,103,46,119,101,105,103,104,116,34,44,34,115,101,103,109,101,110,116,95,111,114,100,105,110,97,108,34,58,49,125,93,44,34,116,111,116,97,108,95,101,108,101,109,101,110,116,115,34,58,51,54,44,34,116,121,112,101,95,110,97,109,101,34,58,34,81,85,65,78,84,73,90,65,84,73,79,78,95,83,67,65,76,69,95,84,65,66,76,69,34,125]
theorem originalLength : original.length = 643 := by rfl
theorem originalBytes : NativeScaleBytes.encode scaleWire = original := by rfl
theorem segmentsSyntax : ∀ w ∈ scaleWire.segments, NativeScaleBytes.SegmentSyntax w := by
  change ∀ w ∈ [wire0,wire1], NativeScaleBytes.SegmentSyntax w
  simp only [List.forall_mem_cons]
  exact ⟨syntax0,syntax1,by simp⟩
theorem wireSyntax : NativeScaleBytes.Syntax scaleWire := ⟨text7,text8,text9,text10,segmentsSyntax,by decide,natural11,text12⟩
theorem decodedWire : NativeScaleBytes.decode original = some scaleWire := by
  rw [← originalBytes]
  apply NativeScaleBytes.decodeEncoded scaleWire wireSyntax
  rw [originalBytes,originalLength]; decide
def table : Table := ⟨scaleWire,[segment0,segment1],36⟩
theorem segmentsValid : ∀ s ∈ table.segments, SegmentValid s := by
  change ∀ s ∈ [segment0,segment1], SegmentValid s
  simp only [List.forall_mem_cons]
  exact ⟨valid0,valid1,by simp⟩
theorem tableSource : Source scaleWire table := by
  exact ⟨rfl,loadValidSegments table.segments segmentsValid,by decide,by decide⟩
theorem decodedTable : decode original = some table :=
  decodedFromComponents decodedWire (interpretFromSource tableSource)
/-- One-entry synthetic adapter; not SHA or exporter authentication. -/
def originalId : Bytes := ascii "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205"
def fixtureHash (raw : Bytes) : Bytes := if raw = hashInput original then originalId else []
theorem originalHash : fixtureHash (hashInput original) = originalId := if_pos rfl
def block0 : NativeQHeader.Joined := ⟨⟨NativeQBytesVectors.header0,NativeQBytesVectors.payload0,[1,-2,0,4]⟩,NativeQHeaderVectors.header0⟩
def bound0 : Bound := ⟨table,block0,segment0⟩
theorem source0 : BoundSource fixtureHash original NativeQBytesVectors.frame0 bound0 := by
  refine ⟨decodedTable,NativeQHeaderVectors.joined0,by decide,?_⟩
  exact ⟨originalHash,rfl,rfl,rfl,by decide,by decide⟩
theorem boundDecoded0 : bind fixtureHash original NativeQBytesVectors.frame0 = some bound0 :=
  bindFromSource source0
theorem quantum0 : bound0.quantum = ⟨1,4⟩ := rfl
def block1 : NativeQHeader.Joined := ⟨⟨NativeQBytesVectors.header1,NativeQBytesVectors.payload1,[-16,-15,-14,-13,-12,-11,-10,-9]⟩,NativeQHeaderVectors.header1⟩
def bound1 : Bound := ⟨table,block1,segment1⟩
theorem source1 : BoundSource fixtureHash original NativeQBytesVectors.frame1 bound1 := by
  refine ⟨decodedTable,NativeQHeaderVectors.joined1,by decide,?_⟩
  exact ⟨originalHash,rfl,rfl,rfl,by decide,by decide⟩
theorem boundDecoded1 : bind fixtureHash original NativeQBytesVectors.frame1 = some bound1 :=
  bindFromSource source1
theorem quantum1 : bound1.quantum = ⟨1,16⟩ := rfl
def block2 : NativeQHeader.Joined := ⟨⟨NativeQBytesVectors.header2,NativeQBytesVectors.payload2,[-8,-7,-6,-5,-4,-3,-2,-1]⟩,NativeQHeaderVectors.header2⟩
def bound2 : Bound := ⟨table,block2,segment1⟩
theorem source2 : BoundSource fixtureHash original NativeQBytesVectors.frame2 bound2 := by
  refine ⟨decodedTable,NativeQHeaderVectors.joined2,by decide,?_⟩
  exact ⟨originalHash,rfl,rfl,rfl,by decide,by decide⟩
theorem boundDecoded2 : bind fixtureHash original NativeQBytesVectors.frame2 = some bound2 :=
  bindFromSource source2
theorem quantum2 : bound2.quantum = ⟨1,16⟩ := rfl
def block3 : NativeQHeader.Joined := ⟨⟨NativeQBytesVectors.header3,NativeQBytesVectors.payload3,[0,1,2,3,4,5,6,7]⟩,NativeQHeaderVectors.header3⟩
def bound3 : Bound := ⟨table,block3,segment1⟩
theorem source3 : BoundSource fixtureHash original NativeQBytesVectors.frame3 bound3 := by
  refine ⟨decodedTable,NativeQHeaderVectors.joined3,by decide,?_⟩
  exact ⟨originalHash,rfl,rfl,rfl,by decide,by decide⟩
theorem boundDecoded3 : bind fixtureHash original NativeQBytesVectors.frame3 = some bound3 :=
  bindFromSource source3
theorem quantum3 : bound3.quantum = ⟨1,16⟩ := rfl
def block4 : NativeQHeader.Joined := ⟨⟨NativeQBytesVectors.header4,NativeQBytesVectors.payload4,[8,9,10,11,12,13,14,15]⟩,NativeQHeaderVectors.header4⟩
def bound4 : Bound := ⟨table,block4,segment1⟩
theorem source4 : BoundSource fixtureHash original NativeQBytesVectors.frame4 bound4 := by
  refine ⟨decodedTable,NativeQHeaderVectors.joined4,by decide,?_⟩
  exact ⟨originalHash,rfl,rfl,rfl,by decide,by decide⟩
theorem boundDecoded4 : bind fixtureHash original NativeQBytesVectors.frame4 = some bound4 :=
  bindFromSource source4
theorem quantum4 : bound4.quantum = ⟨1,16⟩ := rfl
theorem zeroNumerator : interpretSegment {wire0 with numerator := ascii "0"} = none := by decide
theorem zeroDenominator : interpretSegment {wire0 with denominator := ascii "0"} = none := by decide
theorem nonReduced : interpretSegment {wire0 with numerator := ascii "2"} = none := by decide
theorem negativeQuantum : interpretSegment {wire0 with numerator := ascii "-1"} = none := by decide
theorem leadingZeroQuantum : interpretSegment {wire0 with numerator := ascii "01"} = none := by decide
theorem wideNumerator : interpretSegment {wire0 with numerator := ascii "4294967296"} = none := by decide
theorem wideDenominator : interpretSegment {wire0 with denominator := ascii "4294967296"} = none := by decide
theorem zeroCount : interpretSegment {wire0 with count := ascii "0"} = none := by decide
theorem overflowRange : interpretSegment {wire0 with start := ascii "1073741824"} = none := by decide
theorem ordinalBound : interpretSegment {wire0 with ordinal := ascii "65536"} = none := by decide
theorem wrongTotal : ¬ TableChecks {table with total := 35} := by decide
theorem missingSegment : ¬ TableChecks {table with segments := [segment0]} := by decide
theorem duplicateName : ¬ TableChecks {table with segments := [segment0, {segment1 with wire := {wire1 with name := wire0.name}}]} := by decide
theorem reordered : ¬ TableChecks {table with segments := [segment1,segment0]} := by decide
theorem gap : ¬ TableChecks {table with segments := [segment0,{segment1 with start := 5}]} := by decide
theorem wrongProfile : ¬ TableChecks {table with wire := {scaleWire with profile := []}} := by decide
theorem wrongVersion : ¬ TableChecks {table with wire := {scaleWire with version := ascii "2.0.0"}} := by decide
theorem wrongType : ¬ TableChecks {table with wire := {scaleWire with kind := ascii "SHARD_PLAN"}} := by decide
theorem crossBoundary : ¬ Links (fun _ => originalId) original table {block0 with header := {block0.header with count := 5}} segment0 := by decide
theorem wrongOffset : ¬ Links (fun _ => originalId) original table {block0 with header := {block0.header with offset := 1}} segment0 := by decide
theorem wrongStart : ¬ Links (fun _ => originalId) original table {block0 with header := {block0.header with start := 1}} segment0 := by decide
theorem wrongSchema : ¬ Links (fun _ => originalId) original {table with wire := {scaleWire with schema := []}} block0 segment0 := by decide
theorem missingHash : ¬ Links (fun _ => []) original table block0 segment0 := by decide
theorem emptyBytes : decode [] = none := by decide
theorem notObject : decode [91,93] = none := by decide
theorem emptyListAtZeroBound : NativeScaleBytes.readSegments 0 [93] = some ([],[]) := by decide
theorem nonemptyListAtZeroBound : NativeScaleBytes.readSegments 0 [123] = none := by decide
theorem wrongNestedType : NativeScaleBytes.readSegment (ascii "{\"element_count\":4,\"element_start\":0,\"quantum\":\"1/4\"}") = none := by decide
theorem duplicateSegmentKey : NativeScaleBytes.readSegment (ascii "{\"element_count\":4,\"element_count\":4}") = none := by decide
theorem reorderedSegmentKey : NativeScaleBytes.readSegment (ascii "{\"element_start\":0,\"element_count\":4}") = none := by decide
theorem negativeCount : NativeScaleBytes.readSegment (ascii "{\"element_count\":-1,") = none := by decide
def changedBlock : NativeQHeader.Joined := ⟨⟨NativeQBytesVectors.header0,[2,0,254,255,0,0,4,0],[2,-2,0,4]⟩,NativeQHeaderVectors.header0⟩
theorem changedPayloadStillBinds : bind fixtureHash original
    (NativeQBytes.encodeFrame NativeQBytesVectors.header0 [2,0,254,255,0,0,4,0]) =
    some ⟨table,changedBlock,segment0⟩ := by
  apply bindFromSource
  exact ⟨decodedTable,NativeQHeaderVectors.changedPayloadWithOldShaStillAccepted,
    by decide,originalHash,rfl,rfl,rfl,by decide,by decide⟩

end DeltaReduce.NativeScaleVectors
