import DeltaReduce.PublicAbortAncestors
import DeltaReduce.PublicPlanningBodyVectors
import DeltaReduce.NativeParameterVectors

/-! Original certificate lookup components and separate synthetic ancestor
metadata. No combined nonempty native ABORT snapshot/execution is asserted. -/
namespace DeltaReduce.PublicAbortLineageVectors
open NativeBinding NativeFinalizedLookup PublicAbortAncestors
open PublicPlanningBodyVectors (names parent models)
open NativeWholeReplayVectors (selected)
set_option maxRecDepth 16384

def rows : List (Bytes × Nat) := [([1],10),([2],20),([3],30)]

theorem lookupOrdered : all Prod.fst rows [[3],[1]] = some [([3],30),([1],10)] := rfl
theorem missingId : all Prod.fst rows [[1],[4]] = none := rfl
theorem missingPayload : all Prod.fst rows.tail [[1]] = none := rfl
theorem changedId : one Prod.fst [([2],10)] [1] = none := rfl
theorem identicalDuplicate : one Prod.fst [([1],10),([1],10)] [1] = none := rfl
theorem conflictingDuplicate : one Prod.fst [([1],10),([1],99)] [1] = none := rfl
theorem unrelatedPayloadAllowed : one Prod.fst rows [2] = some ([2],20) := rfl
theorem queryDuplicatesRetained : all Prod.fst rows [[1],[1]] = some [([1],10),([1],10)] := rfl
-- Native snapshot strict finalized-list checks, not this generic resolver,
-- rule out the preceding duplicated query in accepted native snapshots.
theorem originalIscLookup : all NativeIscCertificate.Checked.qcId
    [NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc] = some [NativeIscCertificateVectors.checked] := rfl
theorem originalEcLookup : all NativeEligibilityLineage.Edge.id
    [NativeEligibilityVectors.finalEdge] [NativeEligibilityVectors.qc] = some [NativeEligibilityVectors.finalEdge] := rfl
theorem originalPlanLookup : all NativePlanLineage.Edge.id
    [NativePlanVectors.finalEdge] [NativePlanVectors.qc] = some [NativePlanVectors.finalEdge] := rfl
theorem originalParameterLookup : all NativeParameterLineage.Edge.id
    [NativeParameterVectors.finalizedEdge] [NativeParameterVectors.qc] = some [NativeParameterVectors.finalizedEdge] := rfl

def sameIdChangedIsc : NativeIscCertificate.Checked := {NativeIscCertificateVectors.checked with
  certificate := {NativeIscCertificateVectors.certificate with body :=
    {NativeIscCertificateVectors.certificate.body with root := []}}}

theorem sameIdDifferentIscRejects : one NativeIscCertificate.Checked.qcId
    [NativeIscCertificateVectors.checked,sameIdChangedIsc] NativeIscCertificateVectors.qc = none := rfl

def numbers (n : Nat) : Option PublicState.Value := if n < 4 then some (.integer n) else none
theorem collectOrder : collect numbers [3,1,2] = some [.integer 3,.integer 1,.integer 2] := rfl
theorem collectMissingFails : collect numbers [1,4,2] = none := rfl
theorem collectNoOmission : collect numbers [1,2] ≠ some [.integer 1] := by decide
theorem collectNoSubstitution : collect numbers [1,2] ≠ some [.integer 1,.integer 3] := by decide
theorem collectNoReordering : collect numbers [1,2] ≠ some [.integer 2,.integer 1] := by decide
theorem collectNoExtra : collect numbers [1,2] ≠ some [.integer 1,.integer 2,.integer 3] := by decide

theorem projectedIsc : isc names selected NativeIscCertificateVectors.checked = some parent.value := rfl
theorem projectedEc : ec names selected NativeEligibilityVectors.proposedEdge = some PublicPlanningBodyVectors.ec.value := by
  simp only [ec,PublicPlanningBodyVectors.loadedEcComponents,Bind.bind,Option.bind,
    if_pos PublicPlanningBodyVectors.separatedEc]
theorem projectedApc : apc names selected NativePlanVectors.proposedEdge = some PublicPlanningBodyVectors.apc.value := by
  have separated : PublicPlanningBodyVectors.apc.ec.Separated ∧
      (PublicPlanningBodyVectors.apc.members.map PublicPlanningBody.Member.value).Nodup := by
    constructor
    · exact PublicPlanningBodyVectors.separatedEc
    · change [_].Nodup; simp
  simp only [apc,PublicPlanningBodyVectors.loadedApcComponents,Bind.bind,Option.bind,if_pos separated]
theorem missingPrimitiveRejects : ec PublicPlanningBodyVectors.noMetadata selected NativeEligibilityVectors.proposedEdge = none := rfl
theorem changedParentRejects : apc names selected PublicPlanningBodyVectors.differentIsc = none := by
  simp only [apc,PublicPlanningBodyVectors.changedIscPayloadRejects,Bind.bind,Option.bind]
theorem duplicateProjectedValuesRetained : collect (isc names selected)
    [NativeIscCertificateVectors.checked,NativeIscCertificateVectors.checked] = some [parent.value,parent.value] := rfl
theorem duplicateProjectedValuesFailSeparation : ¬ [parent.value,parent.value].Nodup := by simp
theorem originalConfigAlias : PublicFailureBody.loadConfigs names.early [selected.policy.config] =
    some [⟨selected.policy.config,⟨"cfg1",rfl⟩⟩] := rfl

end DeltaReduce.PublicAbortLineageVectors
