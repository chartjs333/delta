import DeltaReduce.NativeIscProjection
import DeltaReduce.NativeVectorCorpusVectors
import DeltaReduce.NativeVectorArtifactVectors

/-! Reuses the existing synthetic raw source and original004 manifest/Q bytes.
No new full native/draft Binding, real availability authentication or GO. -/
namespace DeltaReduce.NativeIscProjectionVectors
open NativeBinding
open NativeVectorCorpusVectors (input vectorContext)
open NativeVectorSourceVectors (sha sourceRow)
open NativeAvailableQVectors (permission0)

def originalRow : NativeIscCorpus.Row := ⟨sourceRow.member,input,NativeVectorCorpusVectors.bound⟩

theorem originalManifest : NativeIscCorpus.manifest sha input = some NativeVectorCorpusVectors.bound := by
  have h := NativeVectorCorpusVectors.wholeManifest
  unfold NativeVectorCorpusVectors.sourceHash at h
  exact h

theorem originalLinks : NativeIscCorpus.Links vectorContext sourceRow.member input NativeVectorCorpusVectors.bound :=
  ⟨rfl,rfl,rfl,rfl,rfl,rfl,rfl,⟨rfl,rfl,rfl⟩⟩

theorem originalLoaded : NativeIscCorpus.loadRow sha vectorContext permission0 sourceRow.member input = some originalRow :=
  NativeIscCorpus.rowFromSources originalManifest NativeAvailableQVectors.primitive0
    NativeAvailableQVectors.coverage0 originalLinks

def complete : NativeIscCorpus.Complete := ⟨[sourceRow.member],[originalRow]⟩

theorem originalAlignment : NativePlanMembers.align
    (NativeVectorAuthority.plan vectorContext).parent.certificate.body.tuples
    (NativeVectorAuthority.plan vectorContext).ec.certificate.common.entries = some [sourceRow.member] := by decide

theorem completeLoaded : NativeIscCorpus.collect sha vectorContext permission0 [input] = some complete :=
  NativeIscCorpus.collectFromSources ⟨originalAlignment,.cons originalLoaded .nil,rfl⟩

theorem completeRawLoaded : NativeIscCorpus.run sha NativeVectorSourceVectors.policyRaw
    NativeVectorSourceVectors.stateRaw NativeVectorSourceVectors.apcId NativeAccumulatorVectors.configOriginal
    NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes permission0 [input] [input]
      = some (vectorContext,complete) := by
  simp only [NativeIscCorpus.run,NativeVectorCorpusVectors.contextLoaded,completeLoaded,bind,Option.bind]

theorem originalFiveLeaves : input.observation.covered.length = originalRow.corpus.manifest.refs.length :=
  (NativeIscCorpus.exactAvailableLeaves originalLoaded).length_eq.trans (by simp)

theorem missingWholeMember : NativeIscCorpus.loadRows sha vectorContext permission0 [sourceRow.member] [] = none :=
  NativeIscCorpus.missingOrExtraRejected (by decide)

theorem extraWholeMember : NativeIscCorpus.loadRows sha vectorContext permission0 [sourceRow.member] [input,input] = none :=
  NativeIscCorpus.missingOrExtraRejected (by decide)

theorem wrongCommitmentRejected : NativeIscCorpus.loadRow sha vectorContext permission0
    {sourceRow.member with input := {sourceRow.member.input with commitment := []}} input = none := by
  apply NativeIscCorpus.wrongMemberRejected originalManifest
  intro h
  have bad := h.2.1
  have size := congrArg List.length bad
  change 71 = 0 at size
  omega

def rejected : NativePlanMembers.Member :=
  {sourceRow.member with eligibility := {sourceRow.member.eligibility with accepted := 0}}

theorem rejectedLoaded : NativeIscCorpus.loadRow sha vectorContext permission0 rejected input =
    some ⟨rejected,input,NativeVectorCorpusVectors.bound⟩ :=
  NativeIscCorpus.rowFromSources originalManifest NativeAvailableQVectors.primitive0
    NativeAvailableQVectors.coverage0 originalLinks

theorem rejectedStillNeedsInput {hash b p} :
    NativeIscCorpus.loadRows hash b p [rejected] [] = none :=
  NativeIscCorpus.missingOrExtraRejected (by decide)

theorem rejectedNotArithmetic : NativePlanMembers.eligible [rejected] = [] := rfl

theorem rejectedKeepsTuple : rejected.input = sourceRow.member.input := rfl

theorem originalQ0 : NativeIscProjection.qValue NativeVectorArtifactVectors.schemaRef
    sourceRow.member.input NativeScaleVectors.bound0 = NativeVectorArtifactVectors.q0 := by decide

theorem originalQ0Bytes : NativeVectorArtifacts.encodeQ
    (NativeIscProjection.qValue NativeVectorArtifactVectors.schemaRef sourceRow.member.input NativeScaleVectors.bound0)
      = NativeVectorArtifactVectors.qBytes0 := by
  rw [originalQ0]
  exact NativeVectorArtifactVectors.qExact0

theorem originalQ1 : NativeIscProjection.qValue NativeVectorArtifactVectors.schemaRef
    sourceRow.member.input NativeScaleVectors.bound1 = NativeVectorArtifactVectors.q1 := by decide

theorem rejectedQUnchanged : NativeIscProjection.qValue NativeVectorArtifactVectors.schemaRef rejected.input
    NativeScaleVectors.bound0 = NativeVectorArtifactVectors.q0 := originalQ0

theorem sourceOrderPreserved : (NativeVectorCorpusVectors.bound.blocks.map (fun q => q.block.header.ordinal)) =
    [0,1,2,3,4] := by decide

theorem missingQRejected {hash schema tuple} : NativeIscProjection.leaves hash schema tuple
    [NativeManifestVectors.ref0] [] = none := rfl

theorem extraQRejected {hash schema tuple} : NativeIscProjection.leaves hash schema tuple
    [] [NativeScaleVectors.bound0] = none := rfl

theorem rejectedEcIsEmpty : NativeIscProjection.eligibleIds ⟨[rejected],[]⟩ = [] := rfl

def tinyLeaf : Leaf := ⟨"s",⟨[],.qShard,1⟩⟩
def tinyCommitment : Commitment := ⟨"t","d",[tinyLeaf]⟩

theorem leafEncoding : NativeIscProjection.encodeLeaf tinyLeaf = asciiBytes
    "{\"q\":{\"id\":\"sha256:\",\"kind\":\"Q_SHARD\",\"length\":1},\"shard\":\"s\"}" := by rfl

theorem commitmentEncoding : NativeIscProjection.encodeCommitment tinyCommitment = asciiBytes
    "{\"domain\":\"d\",\"leaves\":[{\"q\":{\"id\":\"sha256:\",\"kind\":\"Q_SHARD\",\"length\":1},\"shard\":\"s\"}],\"ticket\":\"t\"}" := by rfl

set_option maxRecDepth 2048 in
theorem iscEncoding : NativeIscProjection.encodeIsc ["t"] [tinyCommitment] = asciiBytes
    "{\"kind\":\"ISC_PROJECTION\",\"payload\":{\"commitments\":[{\"domain\":\"d\",\"leaves\":[{\"q\":{\"id\":\"sha256:\",\"kind\":\"Q_SHARD\",\"length\":1},\"shard\":\"s\"}],\"ticket\":\"t\"}],\"members\":[\"t\"]}}" := by rfl

theorem ecEncoding : NativeIscProjection.encodeEc ⟨[],.isc,2⟩ ["t"] = asciiBytes
    "{\"kind\":\"EC_PROJECTION\",\"payload\":{\"eligible\":[\"t\"],\"isc\":{\"id\":\"sha256:\",\"kind\":\"ISC_PROJECTION\",\"length\":2}}}" := by rfl

theorem tinyIsNotAuthority : tinyLeaf.q.id.length ≠ 32 := by decide
end DeltaReduce.NativeIscProjectionVectors
