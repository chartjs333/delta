import DeltaReduce.NativeFinalizedAssignment
import DeltaReduce.NativeParameterVectors

/-! Regression against original finalized PARAMETER components. This does not
instantiate the complete native vector source, corpus or authenticated ROOT. -/
namespace DeltaReduce.NativeFinalizedAssignmentVectors
open NativeBinding NativeFinalizedAssignment
open NativeParameterVectors (certificate finalizedEdge proposedEdge)

def fixtureFields (e : NativeParameterLineage.Edge) : Prop :=
  Fields certificate.common.context certificate.common.isc certificate.common.ec
    certificate.common.plan 1 e
instance (e) : Decidable (fixtureFields e) := by unfold fixtureFields; infer_instance

theorem originalDecodedContext : finalizedEdge.voteContext = [] :=
  originalContext NativeParameterVectors.finalizedChecked

theorem formerCorpusPredicateFails (b : NativeVectorContext.Bound) (a : Assignment) :
    ¬ NativeVectorAuthority.AssignmentChecks b a finalizedEdge :=
  proposedPredicateImpossible NativeParameterVectors.finalizedChecked b a

theorem originalCertificateMatches : fixtureFields finalizedEdge :=
  fieldsFromComponents originalDecodedContext rfl rfl rfl rfl rfl

theorem proposedBodyStillRejected : ¬ fixtureFields proposedEdge := by decide

theorem fabricatedVoteContextRejected : ¬ fixtureFields { finalizedEdge with voteContext := [1] } := by decide

theorem changedRoundRejected : ¬ fixtureFields { finalizedEdge with certificate :=
    { certificate with common := { certificate.common with context :=
      { certificate.common.context with round := [1] } } } } := by decide

theorem changedPlanRejected : ¬ fixtureFields { finalizedEdge with certificate :=
    { certificate with common := { certificate.common with plan := [1] } } } := by decide

theorem changedIscRejected : ¬ fixtureFields { finalizedEdge with certificate :=
    { certificate with common := { certificate.common with isc := [1] } } } := by decide

theorem changedEcRejected : ¬ fixtureFields { finalizedEdge with certificate :=
    { certificate with common := { certificate.common with ec := [1] } } } := by decide

theorem changedDenominatorRejected : ¬ fixtureFields { finalizedEdge with certificate :=
    { certificate with common := { certificate.common with denominator := 2 } } } := by decide

theorem zeroDenominatorRejected : ¬ fixtureFields { finalizedEdge with certificate :=
    { certificate with common := { certificate.common with denominator := 0 } } } := by decide

theorem negativeDenominatorRejected : ¬ Fields certificate.common.context certificate.common.isc
    certificate.common.ec certificate.common.plan (-1) finalizedEdge := by decide

theorem missingNativeContextRejected : ¬ Fields
    { certificate.common.context with round := [] } certificate.common.isc
    certificate.common.ec certificate.common.plan 1 finalizedEdge := by decide

theorem originalPayloadUnchanged : finalizedEdge.source = NativeParameter.value certificate :=
  NativeParameterLineage.originalRetained NativeParameterVectors.finalizedChecked

theorem certificateIdUnchanged : NativeParameter.id NativeParameterVectors.sha certificate =
    some finalizedEdge.id := NativeParameterVectors.qcComputed

theorem proposalAndCertificateRemainDifferent : finalizedEdge.id ≠ proposedEdge.id :=
  NativeParameterVectors.distinctIdentities

end DeltaReduce.NativeFinalizedAssignmentVectors
