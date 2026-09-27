import DeltaReduce.NativeApplyResult
import DeltaReduce.NativePointerWal

/-! Composition with the actual original complete APPLY snapshot and pointer
command. This strengthens the proposal relation, not the guarded native runtime.
Unmatched config/schema/ROOT/Q-artifact identities remain an explicit gap. -/
namespace DeltaReduce.NativeApplyResultJoin
open NativeBinding
open NativeParameterLineage (Mode)
variable {codec store trust anchor} (binding : Binding codec trust anchor store)

def entries (b : NativeApplySection.Bound) : Mode → List NativeApplyLineage.Edge
  | .proposed => b.bodies
  | .finalized => b.certificates
structure Selected where
  bound : NativeApplySection.Bound
  edge : NativeApplyLineage.Edge
  arithmetic : NativeApplyResult.Checked binding
def select (sha : Bytes → Bytes) (policy : NativePolicyBytes.Policy) (state : NativeStateBytes.State)
    (mode : Mode) (id : Bytes) : Option (Selected binding) := do
  let bound ← NativeApplySection.bindSection sha policy state
  let edge ← (entries bound mode).find? (fun e => e.id == id)
  if mode = .finalized → id ∈ bound.finalized then
    let arithmetic ← NativeApplyResult.check binding sha edge
    some ⟨bound,edge,arithmetic⟩
  else none
theorem selectedSource {sha policy state mode id out}
    (h : select binding sha policy state mode id = some out) :
    NativeApplySection.bindSection sha policy state = some out.bound ∧
    (entries out.bound mode).find? (fun e => e.id == id) = some out.edge ∧
    (mode = .finalized → id ∈ out.bound.finalized) ∧
    NativeApplyResult.check binding sha out.edge = some out.arithmetic := by
  unfold select at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨b,hb,e,he,last⟩ := h
  split at last <;> try contradiction
  rename_i finalized
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨a,ha,last⟩ := last
  cases Option.some.inj last
  exact ⟨hb,he,finalized,ha⟩
theorem selectedLineage {sha policy state mode id out}
    (h : select binding sha policy state mode id = some out) :
    NativeApplyLineage.check sha mode
      (NativeParameterSection.expected policy state out.bound.roots.parameters.prior.plans)
      policy.validators state.wire.parent out.bound.roots.finalized
      out.bound.roots.certificates out.bound.profiles out.edge.source = some out.edge := by
  have src := selectedSource binding h
  have mem := List.mem_of_find?_eq_some src.2.1
  cases mode with
  | proposed => exact NativeApplySection.proposedChecked src.1 mem
  | finalized => exact NativeApplySection.certificateChecked src.1 mem
theorem originalCandidateAndQc {sha policy state mode id out}
    (h : select binding sha policy state mode id = some out) :
    NativeApplyCertificate.candidateId sha out.edge.decoded.candidate = some out.edge.decoded.candidateId ∧
    NativeApplyCertificate.certificateId sha out.edge.decoded.certificate = some out.edge.qc ∧
    out.edge.source = NativeApplyLineage.original mode out.edge.decoded := by
  have lineage := selectedLineage binding h
  exact ⟨(NativeApplyLineage.originalPayload lineage).2,
    (NativeApplyLineage.checkedSource lineage).qc,(NativeApplyLineage.originalPayload lineage).1⟩
theorem selectedProfile {sha policy state mode id out}
    (h : select binding sha policy state mode id = some out) :
    NativeApplyProfile.check sha out.edge.profile.source = some out.edge.profile :=
  NativeApplySection.selectedProfile (selectedSource binding h).1 (selectedLineage binding h)
theorem selectedComputed {sha policy state mode id out}
    (h : select binding sha policy state mode id = some out) :
    deriveNativeApply binding = some out.arithmetic.result ∧
    out.edge.decoded.candidate.modelValues = NativeApplyResult.decimalValues out.arithmetic.result.body.nextModel ∧
    out.edge.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues out.arithmetic.result.body.nextOptimizer :=
  ⟨(NativeApplyResult.checkedSource binding (selectedSource binding h).2.2.2).1,
    NativeApplyResult.exactComputedValues binding (selectedSource binding h).2.2.2⟩
theorem certifiedComputedHashes {sha policy state mode id out}
    (h : select binding sha policy state mode id = some out) :
    out.edge.decoded.certificate.model = idBytes out.arithmetic.result.body.nextModelHash ∧
    out.edge.decoded.certificate.optimizer = idBytes out.arithmetic.result.body.nextOptimizerHash ∧
    out.edge.decoded.candidate.parentOptimizer = idBytes anchor.currentOptimizerHash := by
  have fields := NativeApplyLineage.certifiedFields (selectedLineage binding h)
  have hashes := NativeApplyResult.exactComputedHashes binding (selectedSource binding h).2.2.2
  exact ⟨fields.2.2.1.trans hashes.1,fields.2.2.2.trans hashes.2.1,hashes.2.2.2⟩

structure Pointer where
  original : NativeCurrentPointer.Finalized
  arithmetic : NativeApplyResult.Checked binding
def pointer (sha : Bytes → Bytes) (policy : NativePolicyBytes.Policy) (state : NativeStateBytes.State)
    (command : NativeCurrentPointer.Command) : Option (Pointer binding) := do
  let original ← NativeCurrentPointer.fromFinalized sha policy state command
  let arithmetic ← NativeApplyResult.check binding sha original.edge
  some ⟨original,arithmetic⟩
theorem pointerSource {sha policy state command out}
    (h : pointer binding sha policy state command = some out) :
    NativeCurrentPointer.fromFinalized sha policy state command = some out.original ∧
    NativeApplyResult.check binding sha out.original.edge = some out.arithmetic := by
  unfold pointer at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨original,ho,arithmetic,ha,last⟩ := h
  cases Option.some.inj last
  exact ⟨ho,ha⟩
theorem exactCommandOutput {sha policy state command out}
    (h : pointer binding sha policy state command = some out) :
    command.checkpoint = idBytes out.arithmetic.result.body.nextModelHash ∧
    command.optimizer = idBytes out.arithmetic.result.body.nextOptimizerHash ∧
    command.parent = idBytes anchor.currentModelHash := by
  have src := pointerSource binding h
  have links := NativeCurrentPointer.finalizedCandidate src.1
  have hashes := NativeApplyResult.exactComputedHashes binding src.2
  have final := NativeCurrentPointer.finalizedSource src.1
  have parent := NativeApplyLineage.exactCurrent (NativeApplySection.certificateChecked final.1 final.2.1)
  exact ⟨links.2.1.trans hashes.1,links.2.2.1.trans hashes.2.1,
    links.2.2.2.trans (parent.symm.trans hashes.2.2.1)⟩
theorem nextComputed {sha policy state command out}
    (h : pointer binding sha policy state command = some out) :
    (NativeCurrentPointer.next out.original.prepared).checkpoint = idBytes out.arithmetic.result.body.nextModelHash ∧
    (NativeCurrentPointer.next out.original.prepared).optimizer = idBytes out.arithmetic.result.body.nextOptimizerHash := by
  have src := pointerSource binding h
  have prepare := (NativeCurrentPointer.finalizedSource src.1).2.2.2
  have same := (NativeCurrentPointer.preparedSource prepare).command
  simpa only [NativeCurrentPointer.next,same] using (show command.checkpoint = _ ∧ command.optimizer = _ from
    ⟨(exactCommandOutput binding h).1,(exactCommandOutput binding h).2.1⟩)

-- Only fresh commands: a historical retry must use its original admitted anchor,
-- not impose old-parent freshness against an already advanced pointer.
def FreshAnchor (current : NativeCurrentPointer.State) : Prop :=
  current.checkpoint = idBytes anchor.currentModelHash ∧ current.optimizer = idBytes anchor.currentOptimizerHash
instance (current) : Decidable (FreshAnchor (anchor := anchor) current) := by unfold FreshAnchor; infer_instance
def fresh (sha : Bytes → Bytes) (policy : NativePolicyBytes.Policy) (state : NativeStateBytes.State)
    (command : NativeCurrentPointer.Command) (current : NativeCurrentPointer.State) : Option (Pointer binding) := do
  let out ← pointer binding sha policy state command
  if FreshAnchor (anchor := anchor) current ∧
      NativeCurrentPointer.choose current out.original.prepared = some .advanced then some out else none
theorem freshSource {sha policy state command current out}
    (h : fresh binding sha policy state command current = some out) :
    pointer binding sha policy state command = some out ∧ FreshAnchor (anchor := anchor) current ∧
    NativeCurrentPointer.choose current out.original.prepared = some .advanced := by
  unfold fresh at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨out,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨ho,by assumption⟩
theorem freshRecoveredRecord {sha policy state command current out}
    (h : fresh binding sha policy state command current = some out) :
    NativePointerWal.step current (NativePointerWal.record out.original.prepared) =
      some (NativeCurrentPointer.next out.original.prepared) ∧
    NativeCurrentPointer.choose (NativeCurrentPointer.next out.original.prepared)
      out.original.prepared = some .replay ∧
    (NativeCurrentPointer.next out.original.prepared).checkpoint = idBytes out.arithmetic.result.body.nextModelHash ∧
    (NativeCurrentPointer.next out.original.prepared).optimizer = idBytes out.arithmetic.result.body.nextOptimizerHash := by
  have src := freshSource binding h
  have prepared := (NativeCurrentPointer.finalizedSource (pointerSource binding src.1).1).2.2.2
  have recovered := NativePointerWal.durableReplayRepair prepared src.2.2
  exact ⟨recovered.1,recovered.2,nextComputed binding src.1⟩
end DeltaReduce.NativeApplyResultJoin
