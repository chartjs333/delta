import DeltaReduce.NativePlanProjection
import DeltaReduce.NativeIscProjectionVectors

/-! Existing source-row components and small canonical encodings. The tiny
references and partial image below deliberately do not instantiate admission. -/
namespace DeltaReduce.NativePlanProjectionVectors
open NativeBinding
open NativePlanAssignments
open NativePlanProjection
open NativeVectorCorpusVectors (vectorContext)

def tinyRef (kind : Kind) : Ref := ⟨[],kind,1⟩
def tinyContribution : Contribution := ⟨"t",⟨1,2⟩,tinyRef .qShard⟩
def tinyAssignment : Assignment := ⟨"d","s","c",2,⟨1,16⟩,[tinyContribution]⟩
def tinyPlan : Plan := ⟨tinyRef .schema,tinyRef .profile,[⟨"t","d"⟩],[tinyAssignment]⟩

def originalSlice : NativeVectorContext.Slice :=
  ⟨NativeVectorCorpusVectors.row,NativeScaleVectors.bound0⟩
def partialLeaf : NativeIscProjection.LeafImage :=
  ⟨NativeManifestVectors.ref0,NativeScaleVectors.bound0,
    ⟨NativeVectorArtifactVectors.qBytes0,.qShard NativeVectorArtifactVectors.q0,tinyRef .qShard⟩⟩
def partialMember : NativeIscProjection.RowImage := ⟨NativeIscProjectionVectors.originalRow,[partialLeaf]⟩
def originalContribution : ContributionRow := ⟨originalSlice,partialMember,partialLeaf⟩

theorem sameOriginalSource : SameSource originalSlice partialMember := ⟨rfl,rfl⟩
theorem exactOriginalWeight : (contribution originalContribution).weight = ⟨1,1⟩ := rfl
theorem exactOriginalTicket : (contribution originalContribution).ticket = "ticket-002-fixture" := rfl
theorem originalQuantum : originalSlice.block.quantum = ⟨1,4⟩ := rfl
theorem retainedQBytes : partialLeaf.artifact.raw = NativeVectorArtifacts.encodeQ
    (NativeIscProjection.qValue NativeVectorArtifactVectors.schemaRef
      NativeVectorSourceVectors.sourceRow.member.input originalSlice.block) :=
  NativeIscProjectionVectors.originalQ0Bytes.symm
theorem originalRationalNotCoefficient :
    (contribution {originalContribution with source := {originalSlice with source :=
      {originalSlice.source with term := {originalSlice.source.term with coefficient := 7}}}}).weight = ⟨1,1⟩ := rfl
theorem explicitOrdinalKey : nativeKey (asciiBytes "d",3) = ⟨asciiBytes "d",asciiBytes "s0000000003"⟩ := by decide
theorem noNativeShardAlias : (nativeKey (asciiBytes "d",3)).shard ≠ asciiBytes "shard-3" := by decide

theorem tinyProfileRejected : ¬ ProfileRefValid (tinyRef .profile) := by decide
theorem wrongProfileKind : ¬ ProfileRefValid ⟨List.replicate 32 0,.schema,1⟩ := by decide
theorem emptyProfileBytes : ¬ ProfileRefValid ⟨List.replicate 32 0,.profile,0⟩ := by decide
theorem oversizedProfile : ¬ ProfileRefValid ⟨List.replicate 32 0,.profile,4194305⟩ := by decide
theorem profileShapeIsNotAuthentication : ProfileRefValid ⟨List.replicate 32 0,.profile,1⟩ := by decide
theorem invalidProfileCannotConstruct {sha codec store b permission inputs} :
    construct sha codec store b permission inputs (tinyRef .profile) = none := by
  simp only [construct,if_neg tinyProfileRejected]

theorem emptyContributions {image index} : loadContributions image index [] = some [] := rfl
theorem emptyAssignments {b image sec} : loadAssignments b image sec [] = some [] := rfl
theorem partialImageNotFull : partialMember.leaves.length ≠
    partialMember.source.corpus.manifest.refs.length := by decide

theorem fractionEncoding : encodeFraction ⟨1,16⟩ = asciiBytes "[1,16]" := rfl
theorem ticketEncoding : encodeTicket ⟨"t","d"⟩ = asciiBytes "{\"domain\":\"d\",\"id\":\"t\"}" := rfl

def contributionBytes : Bytes := [123,34,113,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,81,95,83,72,65,82,68,34,44,34,108,101,110,103,116,104,34,58,49,125,44,34,116,105,99,107,101,116,34,58,34,116,34,44,34,119,101,105,103,104,116,34,58,91,49,44,50,93,125]
theorem contributionEncoding : encodeContribution tinyContribution = contributionBytes := by decide

def assignmentBytes : Bytes := [123,34,99,111,110,116,101,120,116,34,58,34,99,34,44,34,99,111,110,116,114,105,98,117,116,105,111,110,115,34,58,91,123,34,113,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,81,95,83,72,65,82,68,34,44,34,108,101,110,103,116,104,34,58,49,125,44,34,116,105,99,107,101,116,34,58,34,116,34,44,34,119,101,105,103,104,116,34,58,91,49,44,50,93,125,93,44,34,100,101,110,111,109,105,110,97,116,111,114,34,58,50,44,34,100,111,109,97,105,110,34,58,34,100,34,44,34,113,117,97,110,116,117,109,34,58,91,49,44,49,54,93,44,34,115,104,97,114,100,34,58,34,115,34,125]
set_option maxRecDepth 1024 in
theorem assignmentEncoding : encodeAssignment tinyAssignment = assignmentBytes := by decide

def planBytes : Bytes := [123,34,107,105,110,100,34,58,34,80,76,65,78,34,44,34,112,97,121,108,111,97,100,34,58,123,34,97,115,115,105,103,110,109,101,110,116,115,34,58,91,123,34,99,111,110,116,101,120,116,34,58,34,99,34,44,34,99,111,110,116,114,105,98,117,116,105,111,110,115,34,58,91,123,34,113,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,81,95,83,72,65,82,68,34,44,34,108,101,110,103,116,104,34,58,49,125,44,34,116,105,99,107,101,116,34,58,34,116,34,44,34,119,101,105,103,104,116,34,58,91,49,44,50,93,125,93,44,34,100,101,110,111,109,105,110,97,116,111,114,34,58,50,44,34,100,111,109,97,105,110,34,58,34,100,34,44,34,113,117,97,110,116,117,109,34,58,91,49,44,49,54,93,44,34,115,104,97,114,100,34,58,34,115,34,125,93,44,34,112,114,111,102,105,108,101,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,80,82,79,70,73,76,69,34,44,34,108,101,110,103,116,104,34,58,49,125,44,34,115,99,104,101,109,97,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,125,44,34,116,105,99,107,101,116,115,34,58,91,123,34,100,111,109,97,105,110,34,58,34,100,34,44,34,105,100,34,58,34,116,34,125,93,125,125]
set_option maxRecDepth 2048 in
theorem planEncoding : encodePlan tinyPlan = planBytes := by decide

def apcBytes : Bytes := [123,34,107,105,110,100,34,58,34,65,80,67,95,80,82,79,74,69,67,84,73,79,78,34,44,34,112,97,121,108,111,97,100,34,58,123,34,101,99,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,69,67,95,80,82,79,74,69,67,84,73,79,78,34,44,34,108,101,110,103,116,104,34,58,49,125,44,34,112,108,97,110,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,80,76,65,78,34,44,34,108,101,110,103,116,104,34,58,49,125,125,125]
theorem apcEncoding : encodeApc (tinyRef .ec) (tinyRef .plan) = apcBytes := by decide

end DeltaReduce.NativePlanProjectionVectors
