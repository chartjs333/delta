import DeltaReduce.PublicRootParents
import DeltaReduce.PublicPlanningBodyVectors
import DeltaReduce.NativeAggregateVectors
import DeltaReduce.PublicAuthorityVectors

/-! Original parent components and small primitive-name checks. Metadata is
synthetic; these cases do not execute a positive full raw ROOT/corpus join. -/
namespace DeltaReduce.PublicRootParentsVectors
open NativeBinding PublicState PublicParentNames
open PublicEarlyBodyVectors (entry)

def commitment : Commitment :=
  ⟨NativeVectorLayout.text entry.original.ticket,NativeVectorLayout.text entry.original.domain,
    [⟨"s0000000000",NativeGraphVectors.a4Ref⟩]⟩

def source : PublicAuthority.Metadata PublicAuthorityVectors.metadataTrust := {
  atom := fun key => if key = .content NativeGraphVectors.a8Ref commitment then some "q1" else none
  policy := fun _ _ => none
  atomAuthentic := by intros; trivial
  policyAuthentic := by intros; trivial }

def vocabulary : PublicArithmeticInputs.Vocabulary := { PublicAuthorityVectors.vocabulary with
  ticket := fun t => if t = commitment.ticket then some "t1" else none }

def second : PublicEarlyBody.Entry PublicEarlyBodyVectors.names
    PublicEarlyBodyVectors.isc.original.body.id PublicEarlyBodyVectors.isc.original.body.body :=
  ⟨{entry.original with ticket := asciiBytes "second"},⟨"t1",rfl⟩,⟨"q1",rfl⟩⟩

theorem exactNamesAgree : entriesAgree source NativeGraphVectors.a8Ref vocabulary [commitment] [entry] = true := by decide

theorem completePublicEntry :
    [PublicAuthority.record [("content",.model "q1"),("ticket",.model "t1")]] =
    [entry].map PublicEarlyBody.Entry.value :=
  completeEntries (.cons ⟨"t1",by decide,⟨"q1",by decide⟩⟩ .nil) [entry] exactNamesAgree

theorem droppedEntryRejects : entriesAgree source NativeGraphVectors.a8Ref vocabulary [commitment]
    ([] : List (PublicEarlyBody.Entry PublicEarlyBodyVectors.names PublicEarlyBodyVectors.isc.original.body.id
      PublicEarlyBodyVectors.isc.original.body.body)) = false := rfl

theorem extraEntryRejects : entriesAgree source NativeGraphVectors.a8Ref vocabulary [commitment] [entry,entry] = false := by decide

theorem extraCommitmentRejects : entriesAgree source NativeGraphVectors.a8Ref vocabulary [commitment,commitment] [entry] = false := by decide

theorem substitutedOriginalTicketRejects : entriesAgree source NativeGraphVectors.a8Ref vocabulary [commitment] [second] = false := by decide

theorem missingAliasRejects : entriesAgree source NativeGraphVectors.a8Ref {vocabulary with ticket := fun _ => none}
    [commitment] [entry] = false := by decide

theorem changedAliasRejects : entriesAgree source NativeGraphVectors.a8Ref {vocabulary with ticket := fun _ => some "other"}
    [commitment] [entry] = false := by decide

theorem changedIscReferenceRejects : entriesAgree source NativeGraphVectors.a0Ref vocabulary [commitment] [entry] = false := by decide

theorem changedDomainRejects : entriesAgree source NativeGraphVectors.a8Ref vocabulary
    [{commitment with domain := "other"}] [entry] = false := by decide

theorem deletedQReferenceRejects : entriesAgree source NativeGraphVectors.a8Ref vocabulary
    [{commitment with leaves := []}] [entry] = false := by decide

theorem changedQReferenceRejects : entriesAgree source NativeGraphVectors.a8Ref vocabulary
    [{commitment with leaves := [⟨"s0000000000",NativeGraphVectors.a3Ref⟩]}] [entry] = false := by decide

theorem originalMemberAgrees : membersAgree vocabulary [commitment.ticket] [PublicPlanningBodyVectors.member] = true := by decide

theorem missingMemberRejects : membersAgree vocabulary ([] : List String) [PublicPlanningBodyVectors.member] = false := rfl

theorem duplicateMembersRetained : membersAgree vocabulary [commitment.ticket,commitment.ticket]
    [PublicPlanningBodyVectors.member,PublicPlanningBodyVectors.member] = true := by decide

theorem duplicateSetRejectedSeparately : canonical vocabulary.models
    (PublicAuthority.setValue [PublicPlanningBodyVectors.member.value,PublicPlanningBodyVectors.member.value]) = false := by decide

theorem originalRootPlanParents :
    NativeAggregateVectors.proposedEdge.parent = NativeAggregateVectors.proposedEdge.plan.parent ∧
    NativeAggregateVectors.proposedEdge.ec = NativeAggregateVectors.proposedEdge.plan.ec := ⟨rfl,rfl⟩

theorem originalRootIscCertificate :
    NativeAggregateVectors.proposedEdge.parent.certificate =
    NativeAggregateVectors.proposedEdge.plan.ec.parent.certificate := rfl

end DeltaReduce.PublicRootParentsVectors
