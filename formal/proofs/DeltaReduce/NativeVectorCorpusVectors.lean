import DeltaReduce.NativeVectorSourceVectors
namespace DeltaReduce.NativeVectorCorpusVectors
open NativeReceiptBytes (Bytes)
open NativeManifestBinding
open NativeManifestVectors
open NativeVectorSourceVectors
@[irreducible]
def sourceHash (raw : Bytes) := NativePlanCoefficients.contentHash sha raw
set_option maxRecDepth 16384
set_option maxHeartbeats 60000
theorem hashChecked0 : sourceHash ((NativeSchemaVectors.original)) = hashOutput0 := by unfold sourceHash; exact contentAdapter rfl hashmanifest0 rfl rfl
theorem hashChecked1 : sourceHash ((NativeScaleBinding.hashInput NativeScaleVectors.original)) = hashOutput1 := by unfold sourceHash; exact contentAdapter rfl hashmanifest1 rfl rfl
theorem hashChecked2 : sourceHash ((NativeShardPlanBinding.hashInput NativeShardPlanVectors.original)) = hashOutput2 := by unfold sourceHash; exact contentAdapter rfl hashmanifest2 rfl rfl
theorem hashChecked3 : sourceHash ((manifestInput original)) = hashOutput3 := by unfold sourceHash; exact contentAdapter rfl hashmanifest3 rfl rfl
theorem hashChecked4 : sourceHash ((NativeScaleVectors.bound0.block.frame.payload)) = hashOutput4 := by unfold sourceHash; exact contentAdapter rfl hashmanifest4 rfl rfl
theorem hashChecked5 : sourceHash ((leafInput NativeQBytesVectors.frame0)) = hashOutput5 := by unfold sourceHash; exact contentAdapter rfl hashmanifest5 rfl rfl
theorem hashChecked6 : sourceHash ((NativeScaleVectors.bound1.block.frame.payload)) = hashOutput6 := by unfold sourceHash; exact contentAdapter rfl hashmanifest6 rfl rfl
theorem hashChecked7 : sourceHash ((leafInput NativeQBytesVectors.frame1)) = hashOutput7 := by unfold sourceHash; exact contentAdapter rfl hashmanifest7 rfl rfl
theorem hashChecked8 : sourceHash ((NativeScaleVectors.bound2.block.frame.payload)) = hashOutput8 := by unfold sourceHash; exact contentAdapter rfl hashmanifest8 rfl rfl
theorem hashChecked9 : sourceHash ((leafInput NativeQBytesVectors.frame2)) = hashOutput9 := by unfold sourceHash; exact contentAdapter rfl hashmanifest9 rfl rfl
theorem hashChecked10 : sourceHash ((NativeScaleVectors.bound3.block.frame.payload)) = hashOutput10 := by unfold sourceHash; exact contentAdapter rfl hashmanifest10 rfl rfl
theorem hashChecked11 : sourceHash ((leafInput NativeQBytesVectors.frame3)) = hashOutput11 := by unfold sourceHash; exact contentAdapter rfl hashmanifest11 rfl rfl
theorem hashChecked12 : sourceHash ((NativeScaleVectors.bound4.block.frame.payload)) = hashOutput12 := by unfold sourceHash; exact contentAdapter rfl hashmanifest12 rfl rfl
theorem hashChecked13 : sourceHash ((leafInput NativeQBytesVectors.frame4)) = hashOutput13 := by unfold sourceHash; exact contentAdapter rfl hashmanifest13 rfl rfl
theorem hashChecked14 : sourceHash (([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 211, 30, 219, 120, 192, 250, 181, 117, 1, 92, 80, 133, 188, 109, 149, 73, 180, 108, 93, 128, 175, 160, 213, 27, 82, 151, 254, 206, 213, 161, 102, 123, 41, 18, 169, 69, 156, 55, 50, 155, 195, 199, 86, 30, 159, 236, 237, 115, 99, 31, 246, 250, 62, 222, 59, 167, 33, 79, 190, 242, 65, 42, 185, 76])) = hashOutput14 := by unfold sourceHash; exact contentAdapter rfl hashmanifest14 rfl rfl
theorem hashChecked15 : sourceHash (([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 55, 105, 181, 214, 190, 160, 38, 205, 45, 86, 73, 125, 249, 183, 225, 143, 219, 140, 202, 196, 253, 117, 253, 179, 46, 34, 220, 68, 203, 173, 176, 59, 184, 51, 104, 44, 89, 72, 240, 52, 42, 188, 225, 93, 162, 74, 217, 49, 182, 113, 18, 249, 163, 124, 192, 51, 225, 183, 140, 61, 229, 32, 194, 254])) = hashOutput15 := by unfold sourceHash; exact contentAdapter rfl hashmanifest15 rfl rfl
theorem hashChecked16 : sourceHash (([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237, 152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237])) = hashOutput16 := by unfold sourceHash; exact contentAdapter rfl hashmanifest16 rfl rfl
theorem hashChecked17 : sourceHash (([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 111, 178, 191, 226, 223, 202, 250, 110, 22, 251, 82, 83, 98, 187, 25, 246, 11, 31, 223, 79, 0, 73, 117, 82, 117, 168, 67, 64, 79, 88, 66, 168, 176, 253, 162, 122, 206, 247, 129, 105, 40, 185, 49, 236, 191, 172, 179, 56, 72, 29, 181, 24, 97, 31, 214, 249, 139, 216, 251, 21, 154, 6, 86, 242])) = hashOutput17 := by unfold sourceHash; exact contentAdapter rfl hashmanifest17 rfl rfl
theorem hashChecked18 : sourceHash (([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11, 20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11])) = hashOutput18 := by unfold sourceHash; exact contentAdapter rfl hashmanifest18 rfl rfl
theorem hashChecked19 : sourceHash (([100, 101, 108, 116, 97, 114, 101, 100, 117, 99, 101, 46, 48, 48, 52, 46, 109, 101, 114, 107, 108, 101, 45, 110, 111, 100, 101, 46, 118, 49, 0, 68, 105, 142, 135, 198, 149, 236, 182, 8, 146, 90, 199, 69, 212, 12, 255, 135, 28, 112, 237, 180, 238, 140, 61, 2, 28, 222, 249, 65, 186, 62, 133, 213, 218, 126, 108, 225, 110, 146, 196, 225, 163, 170, 23, 206, 166, 114, 42, 137, 139, 89, 14, 94, 134, 53, 157, 243, 27, 54, 188, 221, 73, 65, 79])) = hashOutput19 := by unfold sourceHash; exact contentAdapter rfl hashmanifest19 rfl rfl
theorem pairChecked14 : NativeManifestMerkle.pair sourceHash hashOutput5 hashOutput7 = some hashOutput14 :=
  NativeManifestMerkle.pairFromSource (da := [211, 30, 219, 120, 192, 250, 181, 117, 1, 92, 80, 133, 188, 109, 149, 73, 180, 108, 93, 128, 175, 160, 213, 27, 82, 151, 254, 206, 213, 161, 102, 123]) (db := [41, 18, 169, 69, 156, 55, 50, 155, 195, 199, 86, 30, 159, 236, 237, 115, 99, 31, 246, 250, 62, 222, 59, 167, 33, 79, 190, 242, 65, 42, 185, 76]) (by decide) (by decide) hashChecked14 (by decide)
theorem pairChecked15 : NativeManifestMerkle.pair sourceHash hashOutput9 hashOutput11 = some hashOutput15 :=
  NativeManifestMerkle.pairFromSource (da := [55, 105, 181, 214, 190, 160, 38, 205, 45, 86, 73, 125, 249, 183, 225, 143, 219, 140, 202, 196, 253, 117, 253, 179, 46, 34, 220, 68, 203, 173, 176, 59]) (db := [184, 51, 104, 44, 89, 72, 240, 52, 42, 188, 225, 93, 162, 74, 217, 49, 182, 113, 18, 249, 163, 124, 192, 51, 225, 183, 140, 61, 229, 32, 194, 254]) (by decide) (by decide) hashChecked15 (by decide)
theorem pairChecked16 : NativeManifestMerkle.pair sourceHash hashOutput13 hashOutput13 = some hashOutput16 :=
  NativeManifestMerkle.pairFromSource (da := [152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237]) (db := [152, 42, 104, 49, 16, 216, 71, 246, 158, 110, 24, 82, 60, 3, 106, 102, 69, 251, 77, 163, 81, 27, 142, 88, 106, 64, 240, 223, 117, 10, 141, 237]) (by decide) (by decide) hashChecked16 (by decide)
theorem pairChecked17 : NativeManifestMerkle.pair sourceHash hashOutput14 hashOutput15 = some hashOutput17 :=
  NativeManifestMerkle.pairFromSource (da := [111, 178, 191, 226, 223, 202, 250, 110, 22, 251, 82, 83, 98, 187, 25, 246, 11, 31, 223, 79, 0, 73, 117, 82, 117, 168, 67, 64, 79, 88, 66, 168]) (db := [176, 253, 162, 122, 206, 247, 129, 105, 40, 185, 49, 236, 191, 172, 179, 56, 72, 29, 181, 24, 97, 31, 214, 249, 139, 216, 251, 21, 154, 6, 86, 242]) (by decide) (by decide) hashChecked17 (by decide)
theorem pairChecked18 : NativeManifestMerkle.pair sourceHash hashOutput16 hashOutput16 = some hashOutput18 :=
  NativeManifestMerkle.pairFromSource (da := [20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11]) (db := [20, 7, 220, 120, 149, 182, 111, 222, 172, 177, 25, 129, 211, 220, 203, 250, 228, 138, 192, 163, 137, 55, 154, 248, 163, 76, 246, 83, 123, 177, 170, 11]) (by decide) (by decide) hashChecked18 (by decide)
theorem pairChecked19 : NativeManifestMerkle.pair sourceHash hashOutput17 hashOutput18 = some hashOutput19 :=
  NativeManifestMerkle.pairFromSource (da := [68, 105, 142, 135, 198, 149, 236, 182, 8, 146, 90, 199, 69, 212, 12, 255, 135, 28, 112, 237, 180, 238, 140, 61, 2, 28, 222, 249, 65, 186, 62, 133]) (db := [213, 218, 126, 108, 225, 110, 146, 196, 225, 163, 170, 23, 206, 166, 114, 42, 137, 139, 89, 14, 94, 134, 53, 157, 243, 27, 54, 188, 221, 73, 65, 79]) (by decide) (by decide) hashChecked19 (by decide)
theorem levelChecked0 : NativeManifestMerkle.level sourceHash [hashOutput5,hashOutput7,hashOutput9,hashOutput11,hashOutput13] = some [hashOutput14,hashOutput15,hashOutput16] := by
  simp only [NativeManifestMerkle.level,pairChecked14,pairChecked15,pairChecked16,Bind.bind,Option.bind,Option.map]
theorem levelChecked1 : NativeManifestMerkle.level sourceHash [hashOutput14,hashOutput15,hashOutput16] = some [hashOutput17,hashOutput18] := by
  simp only [NativeManifestMerkle.level,pairChecked17,pairChecked18,Bind.bind,Option.bind,Option.map]
theorem levelChecked2 : NativeManifestMerkle.level sourceHash [hashOutput17,hashOutput18] = some [hashOutput19] := by
  simp only [NativeManifestMerkle.level,pairChecked19,Bind.bind,Option.bind]
def planBound := NativeShardPlanVectors.bound
theorem boundPlan : NativeShardPlanBinding.bind sourceHash NativeSchemaVectors.original
    NativeScaleVectors.original NativeShardPlanVectors.original = some planBound := by
  apply NativeShardPlanBinding.bindFromSource
  refine ⟨?_,NativeShardPlanVectors.decodedWire,NativeShardPlanVectors.interpretedPlan,
    NativeShardPlanVectors.computedPlan,?_⟩
  · apply NativeSchemaBinding.bindFromSource
    exact ⟨NativeSchemaVectors.decodedSchema,NativeScaleVectors.decodedTable,hashChecked0,by decide,by decide⟩
  · exact ⟨rfl,rfl,rfl,rfl,rfl,hashChecked1.symm,rfl,by decide⟩
theorem scaleQ0 : NativeScaleBinding.bind sourceHash NativeScaleVectors.original
    NativeQBytesVectors.frame0 = some NativeScaleVectors.bound0 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined0,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks0 : LeafLinks sourceHash planBound wire ref0
    NativeQBytesVectors.frame0 NativeScaleVectors.bound0 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked5⟩
  unfold expectedHeader
  rw [hashChecked4]
  rfl
theorem scaleQ1 : NativeScaleBinding.bind sourceHash NativeScaleVectors.original
    NativeQBytesVectors.frame1 = some NativeScaleVectors.bound1 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined1,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks1 : LeafLinks sourceHash planBound wire ref1
    NativeQBytesVectors.frame1 NativeScaleVectors.bound1 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked7⟩
  unfold expectedHeader
  rw [hashChecked6]
  rfl
theorem scaleQ2 : NativeScaleBinding.bind sourceHash NativeScaleVectors.original
    NativeQBytesVectors.frame2 = some NativeScaleVectors.bound2 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined2,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks2 : LeafLinks sourceHash planBound wire ref2
    NativeQBytesVectors.frame2 NativeScaleVectors.bound2 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked9⟩
  unfold expectedHeader
  rw [hashChecked8]
  rfl
theorem scaleQ3 : NativeScaleBinding.bind sourceHash NativeScaleVectors.original
    NativeQBytesVectors.frame3 = some NativeScaleVectors.bound3 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined3,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks3 : LeafLinks sourceHash planBound wire ref3
    NativeQBytesVectors.frame3 NativeScaleVectors.bound3 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked11⟩
  unfold expectedHeader
  rw [hashChecked10]
  rfl
theorem scaleQ4 : NativeScaleBinding.bind sourceHash NativeScaleVectors.original
    NativeQBytesVectors.frame4 = some NativeScaleVectors.bound4 := by
  apply NativeScaleBinding.bindFromSource
  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined4,
    by decide,hashChecked1,rfl,rfl,rfl,by decide,by decide⟩
theorem leafLinks4 : LeafLinks sourceHash planBound wire ref4
    NativeQBytesVectors.frame4 NativeScaleVectors.bound4 := by
  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked13⟩
  unfold expectedHeader
  rw [hashChecked12]
  rfl
def raws : List Bytes := [NativeQBytesVectors.frame0,NativeQBytesVectors.frame1,NativeQBytesVectors.frame2,NativeQBytesVectors.frame3,NativeQBytesVectors.frame4]
def blocks : List NativeScaleBinding.Bound := [NativeScaleVectors.bound0,NativeScaleVectors.bound1,NativeScaleVectors.bound2,NativeScaleVectors.bound3,NativeScaleVectors.bound4]
theorem corpusChecked : corpus sourceHash NativeScaleVectors.original planBound wire manifest.refs raws = some blocks := by
  apply corpusFromSource
  exact .cons scaleQ0 leafLinks0 (.cons scaleQ1 leafLinks1 (.cons scaleQ2 leafLinks2 (.cons scaleQ3 leafLinks3 (.cons scaleQ4 leafLinks4 (.nil)))))
theorem manifestLinks : Links sourceHash NativeShardPlanVectors.original planBound manifest := by
  refine ⟨rfl,rfl,rfl,rfl,rfl,rfl,hashChecked2.symm,?_⟩
  decide
set_option maxHeartbeats 200000 in
theorem rootChecked : NativeManifestMerkle.root sourceHash (manifest.refs.map (fun r => r.wire.leaf)) = some wire.root := by
  unfold NativeManifestMerkle.root
  rw [if_pos (by decide)]
  change NativeManifestMerkle.tree sourceHash 13 [hashOutput5,hashOutput7,hashOutput9,hashOutput11,hashOutput13] = some wire.root
  rw [NativeManifestMerkle.tree,levelChecked0]
  dsimp only [Bind.bind,Option.bind]
  rw [NativeManifestMerkle.tree,levelChecked1]
  dsimp only [Bind.bind,Option.bind]
  rw [NativeManifestMerkle.tree,levelChecked2]
  dsimp only [Bind.bind,Option.bind]
  rw [NativeManifestMerkle.tree]
  exact if_pos (show NativeVoteBytes.ContentId hashOutput19 by decide)
def bound : Bound := ⟨planBound,manifest,blocks⟩
theorem wholeManifest : bind sourceHash NativeSchemaVectors.original NativeScaleVectors.original
    NativeShardPlanVectors.original original hashOutput3 raws = some bound :=
  bindFromSource ⟨boundPlan,decodedWire,interpretedManifest,manifestLinks,
    ⟨by decide,hashChecked3⟩,corpusChecked,rootChecked⟩


def input : NativeAvailableQ.Input :=
  ⟨NativeSchemaVectors.original,NativeScaleVectors.original,NativeShardPlanVectors.original,
    original,hashOutput3,raws,NativeAvailableQVectors.observation0⟩
def available : NativeAccumulatorBinding.BoundCorpus := ⟨bound,NativeAccumulatorVectors.bound⟩
theorem availableLoaded : NativeAvailableQ.load (NativePlanCoefficients.contentHash sha)
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes input = some available :=
  by
    have bounds : NativeAccumulatorBinding.load sourceHash NativeAccumulatorVectors.configOriginal
        NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes
        apc.common.accumulator = some NativeAccumulatorVectors.bound := by
      delta sourceHash
      exact accumulatorLoaded
    have joined : NativeAvailableQ.load sourceHash NativeAccumulatorVectors.configOriginal
        NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes input =
          some available := NativeAccumulatorBinding.corpusFromSources wholeManifest bounds
      (show NativeAccumulatorBinding.CorpusLinks bound NativeAccumulatorVectors.bound from
        ⟨rfl,rfl,rfl,rfl,rfl,rfl⟩)
    have sameHash : sourceHash = NativePlanCoefficients.contentHash sha := by
      unfold sourceHash
      rfl
    exact (congrArg (fun h => NativeAvailableQ.load h NativeAccumulatorVectors.configOriginal
      NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes input =
        some available) sameHash).mp joined
def row : NativePlanQCorpus.Row := ⟨⟨sourceRow,1⟩,available⟩
theorem rowLoaded : NativePlanQCorpus.loadRow sha NativeAccumulatorVectors.configOriginal
    NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes
        coefficients
    NativeAvailableQVectors.permission0 row.term input = some row :=
  NativePlanQCorpus.rowFromSources availableLoaded NativeAvailableQVectors.primitive0
    NativeAvailableQVectors.coverage0
      ⟨rfl,rfl,rfl,rfl,rfl,rfl,rfl⟩
def corpusBound : NativePlanQCorpus.Bound := ⟨coefficients,[row]⟩
theorem corpusLoaded : NativePlanQCorpus.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes NativeAvailableQVectors.permission0 [input] = some
        corpusBound :=
  NativePlanQCorpus.bindFromSources rawCoefficients
    (NativePlanQCorpus.rowsFromSources (.cons rowLoaded .nil))
def vectorContext : NativeVectorContext.Bound := ⟨corpusBound,row⟩
theorem contextLoaded : NativeVectorContext.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes NativeAvailableQVectors.permission0 [input] = some
        vectorContext :=
  NativeVectorContext.bindFromSources corpusLoaded (NativeVectorContext.alignFromSources rfl (by
      intro r h
      have same : r = row := List.mem_singleton.mp h
      subst r
      exact ⟨rfl,rfl,rfl⟩))
theorem completeRawInputs : vectorContext.source.rows.map (fun r => r.term.source) = members.rows
    ∧
    vectorContext.source.rows.length = 1 := NativeVectorContext.completeOriginalRows contextLoaded
theorem originalCurrentParentOnly : vectorContext.first.corpus.manifest.manifest.wire.parent =
    state.wire.parent := rfl
theorem candidateRetainedOnly : policy.candidates = [candidate] := rfl
theorem missingInputsRejected : NativePlanQCorpus.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes NativeAvailableQVectors.permission0 [] = none :=
  NativePlanQCorpus.bindFromAbsentRows rawCoefficients rfl
theorem extraInputsRejected : NativePlanQCorpus.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes NativeAvailableQVectors.permission0 [input,input]
        = none :=
  NativePlanQCorpus.bindFromAbsentRows rawCoefficients
    (NativePlanQCorpus.extraSingleInput rowLoaded)


def result0 : NativeVectorArithmetic.Result := ⟨row.term.source.member.input.domain,0,NativeScaleVectors.bound0,[⟨row,NativeScaleVectors.bound0⟩],[1,-2,0,4]⟩
theorem computed0 : NativeVectorArithmetic.compute NativeAccumulatorVectors.numbers 4 [⟨row,NativeScaleVectors.bound0⟩] = some [1,-2,0,4] := by
  change ParameterKernel.checkedParameter (-9223372036854775808) 9223372036854775807 NativeBinding.minInput NativeBinding.maxInput 1 4 [⟨1,1,[1,-2,0,4]⟩] = some [1,-2,0,4]
  decide
theorem reduced0 : NativeVectorArithmetic.reduce vectorContext row.term.source.member.input.domain 0 = some result0 := NativeVectorArithmetic.reducedFromSources rfl rfl computed0
def result1 : NativeVectorArithmetic.Result := ⟨row.term.source.member.input.domain,1,NativeScaleVectors.bound1,[⟨row,NativeScaleVectors.bound1⟩],[-16,-15,-14,-13,-12,-11,-10,-9]⟩
theorem computed1 : NativeVectorArithmetic.compute NativeAccumulatorVectors.numbers 8 [⟨row,NativeScaleVectors.bound1⟩] = some [-16,-15,-14,-13,-12,-11,-10,-9] := by
  change ParameterKernel.checkedParameter (-9223372036854775808) 9223372036854775807 NativeBinding.minInput NativeBinding.maxInput 1 8 [⟨1,1,[-16,-15,-14,-13,-12,-11,-10,-9]⟩] = some [-16,-15,-14,-13,-12,-11,-10,-9]
  decide
theorem reduced1 : NativeVectorArithmetic.reduce vectorContext row.term.source.member.input.domain 1 = some result1 := NativeVectorArithmetic.reducedFromSources rfl rfl computed1
def result2 : NativeVectorArithmetic.Result := ⟨row.term.source.member.input.domain,2,NativeScaleVectors.bound2,[⟨row,NativeScaleVectors.bound2⟩],[-8,-7,-6,-5,-4,-3,-2,-1]⟩
theorem computed2 : NativeVectorArithmetic.compute NativeAccumulatorVectors.numbers 8 [⟨row,NativeScaleVectors.bound2⟩] = some [-8,-7,-6,-5,-4,-3,-2,-1] := by
  change ParameterKernel.checkedParameter (-9223372036854775808) 9223372036854775807 NativeBinding.minInput NativeBinding.maxInput 1 8 [⟨1,1,[-8,-7,-6,-5,-4,-3,-2,-1]⟩] = some [-8,-7,-6,-5,-4,-3,-2,-1]
  decide
theorem reduced2 : NativeVectorArithmetic.reduce vectorContext row.term.source.member.input.domain 2 = some result2 := NativeVectorArithmetic.reducedFromSources rfl rfl computed2
def result3 : NativeVectorArithmetic.Result := ⟨row.term.source.member.input.domain,3,NativeScaleVectors.bound3,[⟨row,NativeScaleVectors.bound3⟩],[0,1,2,3,4,5,6,7]⟩
theorem computed3 : NativeVectorArithmetic.compute NativeAccumulatorVectors.numbers 8 [⟨row,NativeScaleVectors.bound3⟩] = some [0,1,2,3,4,5,6,7] := by
  change ParameterKernel.checkedParameter (-9223372036854775808) 9223372036854775807 NativeBinding.minInput NativeBinding.maxInput 1 8 [⟨1,1,[0,1,2,3,4,5,6,7]⟩] = some [0,1,2,3,4,5,6,7]
  decide
theorem reduced3 : NativeVectorArithmetic.reduce vectorContext row.term.source.member.input.domain 3 = some result3 := NativeVectorArithmetic.reducedFromSources rfl rfl computed3
def result4 : NativeVectorArithmetic.Result := ⟨row.term.source.member.input.domain,4,NativeScaleVectors.bound4,[⟨row,NativeScaleVectors.bound4⟩],[8,9,10,11,12,13,14,15]⟩
theorem computed4 : NativeVectorArithmetic.compute NativeAccumulatorVectors.numbers 8 [⟨row,NativeScaleVectors.bound4⟩] = some [8,9,10,11,12,13,14,15] := by
  change ParameterKernel.checkedParameter (-9223372036854775808) 9223372036854775807 NativeBinding.minInput NativeBinding.maxInput 1 8 [⟨1,1,[8,9,10,11,12,13,14,15]⟩] = some [8,9,10,11,12,13,14,15]
  decide
theorem reduced4 : NativeVectorArithmetic.reduce vectorContext row.term.source.member.input.domain 4 = some result4 := NativeVectorArithmetic.reducedFromSources rfl rfl computed4

theorem originalCoefficientCoordinate (i : Nat) (within : i < 4) :
    ∃ v, result0.values[i]? = some v ∧
      checkedAccumulate (NativeVectorArithmetic.lo NativeAccumulatorVectors.numbers)
        (NativeVectorArithmetic.hi NativeAccumulatorVectors.numbers)
        (NativeVectorArithmetic.lo NativeAccumulatorVectors.numbers)
        (NativeVectorArithmetic.hi NativeAccumulatorVectors.numbers) 0
        (result0.slices.map (fun s => ((s.source.term.coefficient : Int),
          (s.block.block.frame.values[i]?).getD 0))) = some v :=
  NativeVectorArithmetic.originalCoordinateRefines contextLoaded reduced0 i within
theorem allCoordinatesRetained : (result0.values ++ result1.values ++ result2.values ++
    result3.values ++ result4.values).length = 36 := rfl
theorem sourceEntryReachesDraftJoin {codec store trust anchor}
    (binding : NativeBinding.Binding codec trust anchor store) (domain : Bytes) (index : Nat) :
    NativeVectorJoin.run binding sha policyRaw stateRaw apcId
        NativeAccumulatorVectors.configOriginal
      NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes
      NativeAvailableQVectors.permission0 [input] domain index =
    (NativeVectorJoin.join binding vectorContext domain index).map (fun j => ⟨vectorContext,j⟩) :=
  NativeVectorJoin.runFromContext binding contextLoaded domain index

end DeltaReduce.NativeVectorCorpusVectors
