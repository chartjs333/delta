import DeltaReduce.PublicPlanningHistory
import DeltaReduce.PublicEarlyBodyVectors
import DeltaReduce.NativePlanVectors

/-! Pinned individual EC/APC source components and synthetic public metadata.
No new whole native EC/APC snapshot or joined recovery execution is asserted. -/
namespace DeltaReduce.PublicPlanningBodyVectors
open NativeBinding PublicState PublicPlanningBody
open NativeWholeReplayVectors (selected)
set_option maxRecDepth 16384

def syntheticTrust : PublicPlanningBody.Trust := ⟨fun _ _ => True⟩
def names : Metadata PublicEarlyBodyVectors.syntheticTrust syntheticTrust :=
  ⟨PublicEarlyBodyVectors.names,(fun k => some (match k with
    | .seed _ _ => "seed1" | .norm _ _ _ => "norm1" | .coefficient _ _ _ => "coef1")),(by intros; trivial)⟩
def parent : IscBody names selected NativeIscCertificateVectors.checked :=
  ⟨PublicEarlyBodyVectors.header,.omitUnavailable,rfl,[PublicEarlyBodyVectors.entry],rfl⟩
def member : Member names.early NativeIscCertificateVectors.certificate.body.context :=
  ⟨NativeEligibilityVectors.entry.ticket,⟨"t1",rfl⟩⟩
def ec : EcBody names selected NativeEligibilityVectors.proposedEdge :=
  ⟨parent,⟨"seed1",rfl⟩,⟨"norm1",rfl⟩,[member],rfl⟩
def finalizedEc : EcBody names selected NativeEligibilityVectors.finalEdge :=
  ⟨parent,⟨"seed1",rfl⟩,⟨"norm1",rfl⟩,[member],rfl⟩
def apc : ApcBody names selected NativePlanVectors.proposedEdge :=
  ⟨⟨rfl,rfl,rfl,rfl⟩,finalizedEc,⟨"coef1",rfl⟩,[member],rfl,rfl⟩

theorem originalEcSource : NativeEligibilityLineage.Source NativeEligibilityVectors.sha .proposed
    NativeEligibilityVectors.certificate.common.context NativeIscCertificateVectors.committee
    [NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc]
    [NativeNormEvidenceVectors.checked] [NativeSeedTranscriptVectors.checked]
    NativeEligibilityVectors.bodyTree NativeEligibilityVectors.proposedEdge := NativeEligibilityVectors.proposalEdgeSource
theorem originalPlanSource : NativePlanLineage.Source NativePlanVectors.sha .proposed
    NativePlanVectors.certificate.common.context NativeIscCertificateVectors.committee
    [NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc]
    NativePlanVectors.certificate.common.accumulator [NativeEligibilityVectors.finalEdge]
    [NativeSeedTranscriptVectors.checked] NativePlanVectors.bodyTree NativePlanVectors.proposedEdge := NativePlanVectors.proposedEdgeSource
theorem loadedEcComponents : loadEcBody names selected NativeEligibilityVectors.proposedEdge = some ec := rfl
theorem loadedApcComponents : loadApcBody names selected NativePlanVectors.proposedEdge = some apc :=
  loadApcFromComponents apc rfl rfl
theorem originalIscTuples : parent.entries.map PublicEarlyBody.Entry.original =
    NativeIscCertificateVectors.certificate.body.tuples := completeOriginalIsc parent
theorem acceptedEcMembers : ec.members.map Member.original =
    NativePlan.acceptedTickets NativeEligibilityVectors.proposedEdge.certificate := ecOriginalMembers ec
theorem allPlanWeights : apc.members.map Member.original =
    NativePlanVectors.proposedEdge.certificate.common.weights.map NativePlan.Weight.ticket := apcOriginalMembers apc

def iscValue : Value := PublicEarlyBodyVectors.vote.body
def seed : Value := PublicAuthority.seedValue iscValue (.model "e1") (.model "seed1")
def ecValue : Value := PublicAuthority.ecValue iscValue seed (PublicAuthority.setValue [.model "t1"]) (.model "norm1")
def apcValue : Value := PublicAuthority.apcValue iscValue seed ecValue (PublicAuthority.setValue [.model "t1"]) (.model "coef1")
def ecVote : Vote := ⟨.model "v1",.text "EC",iscValue,ecValue⟩
def apcVote : Vote := ⟨.model "v1",.text "APC",ecValue,apcValue⟩
def models : List String := PublicEarlyBodyVectors.models ++ ["seed1","norm1","coef1"]
theorem wholeEcValue : ec.vote = ecVote := rfl
theorem wholeApcValue : apc.vote = apcVote := rfl
theorem canonicalEc : canonical models (.function (voteEntries ecVote)) = true := by decide
theorem canonicalApc : canonical models (.function (voteEntries apcVote)) = true := by decide
theorem separatedEc : ec.Separated := by constructor <;> change [_].Nodup <;> simp
theorem samePlanningParents : SamePlanParents NativePlanVectors.proposedEdge := ⟨rfl,rfl,rfl,rfl⟩
theorem completeSharedParent : readField apc.value "isc" = readField apc.ec.value "isc" := (apcParentShape apc).1
theorem completeSharedSeed : readField apc.value "seed" = readField apc.ec.value "seed" := (apcParentShape apc).2.1
theorem completeSharedMembers : readField apc.value "members" = readField apc.ec.value "members" := (apcParentShape apc).2.2.2

def noMetadata : Metadata PublicEarlyBodyVectors.syntheticTrust syntheticTrust :=
  ⟨PublicEarlyBodyVectors.names,fun _ => none,(by intros; trivial)⟩
theorem missingSeedRejects : loadEcBody noMetadata selected NativeEligibilityVectors.proposedEdge = none := rfl
theorem iscSourceCannotVoteEc : check PublicEarlyBodyVectors.loaded names models ecVote = none := rfl
theorem iscSourceCannotVoteApc : check PublicEarlyBodyVectors.loaded names models apcVote = none := rfl

def differentIsc : NativePlanLineage.Edge := {NativePlanVectors.proposedEdge with parent :=
  {NativePlanVectors.proposedEdge.parent with certificate :=
    {NativePlanVectors.proposedEdge.parent.certificate with body :=
      {NativePlanVectors.proposedEdge.parent.certificate.body with root := []}}}}
theorem changedIscPayloadRejects : loadApcBody names selected differentIsc = none := by
  apply differentPlanParentsReject
  intro h
  have eq := congrArg (fun c : NativeIscCertificate.Certificate => c.body.root) h.2.1
  contradiction
theorem coarseNativeParentGuardStillHolds : NativePlanLineage.NativeParentChecks
    [NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] NativePlanVectors.certificate.common.accumulator
    differentIsc.certificate differentIsc.parent differentIsc.ec differentIsc.seed := NativePlanVectors.proposalParents
-- The preceding coarse predicate is NOT a full checked native snapshot.
def differentSeed : NativePlanLineage.Edge := {NativePlanVectors.proposedEdge with seed :=
  {NativePlanVectors.proposedEdge.seed with transcript :=
    {NativePlanVectors.proposedEdge.seed.transcript with shares := []}}}
theorem changedSeedPayloadRejects : loadApcBody names selected differentSeed = none := by
  apply differentPlanParentsReject
  intro h
  have eq := congrArg NativeSeedTranscript.Transcript.shares h.2.2.2
  contradiction
theorem seedKeyIncludesShares : Key.seed NativeSeedTranscriptVectors.transcriptId NativeSeedTranscriptVectors.transcript ≠
    .seed NativeSeedTranscriptVectors.transcriptId {NativeSeedTranscriptVectors.transcript with shares := []} :=
  seedKeyRetainsShares (by decide)
theorem normKeyIncludesFullEntries : Key.norm NativeNormEvidenceVectors.evidenceId NativeNormEvidenceVectors.evidence
    NativeEligibilityVectors.certificate.common ≠ .norm NativeNormEvidenceVectors.evidenceId
      {NativeNormEvidenceVectors.evidence with entries := []} NativeEligibilityVectors.certificate.common :=
  normKeyRetainsEntries (by decide)
theorem coefficientKeyIncludesWeights : Key.coefficient NativePlanVectors.bid NativePlanVectors.certificate.common
    NativeEligibilityVectors.certificate.common ≠ .coefficient NativePlanVectors.bid
      {NativePlanVectors.certificate.common with weights := []} NativeEligibilityVectors.certificate.common :=
  coefficientKeyRetainsWeights (by decide)
theorem duplicateMemberAliasesPreserved : loadMembers names.early NativeIscCertificateVectors.certificate.body.context
    [member.original,member.original] = some [member,member] := rfl
theorem collapsedMemberAliases : ¬ [member.value,member.value].Nodup := by simp
theorem wrongEcVoteContext : {ecVote with context := .model "opaque-id"} ≠ ec.vote := by decide
theorem wrongApcVoteContext : {apcVote with context := iscValue} ≠ apc.vote := by decide
theorem changedApcProfile : {apcVote with body := PublicAuthority.apcValue iscValue seed ecValue (PublicAuthority.setValue [.model "t1"]) (.model "other-profile")} ≠ apc.vote := by decide

end DeltaReduce.PublicPlanningBodyVectors
