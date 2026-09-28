import DeltaReduce.NativeFinalizedLookup

/-! All original ABORT finalized lists resolved against the actual checked
snapshot. CONFIG is natively an ID list; no missing config payload is invented.
Numerical replay/public translation and environment authentication are separate. -/
namespace DeltaReduce.NativeAbortLineage
open NativeBinding NativeCandidateAuthority

def snapshot (x : NativeSelectedVote.Checked) := x.admitted.checked.snapshot

def iscSection (x : NativeSelectedVote.Checked) := (ecSection (snapshot x)).norms.isc

structure Image where
  configs : List Bytes
  inputs : List NativeIscCertificate.Checked
  eligibility : List NativeEligibilityLineage.Edge
  plans : List NativePlanLineage.Edge
  parameters : List NativeParameterLineage.Edge
  roots : List NativeAggregateLineage.Edge
  applies : List NativeApplyLineage.Edge

def Image.ids (p : Image) : NativeFailureSection.Lineage :=
  ⟨p.configs,p.inputs.map (·.qcId),p.eligibility.map (·.id),p.plans.map (·.id),
    p.parameters.map (·.id),p.roots.map (·.id),p.applies.map (·.id)⟩

def compute {sha} (x : NativeSelectedVote.Checked) (a : NativeFailureSource.Abort sha x) : Option Image := do
  let inputs ← NativeFinalizedLookup.all (·.qcId) (iscSection x).certificates a.original.row.body.inputs
  let eligibility ← NativeFinalizedLookup.all (·.id) (ecSection (snapshot x)).certificates a.original.row.body.eligibility
  let plans ← NativeFinalizedLookup.all (·.id) (planSection (snapshot x)).certificates a.original.row.body.plans
  let parameters ← NativeFinalizedLookup.all (·.id) (parameterSection (snapshot x)).certificates a.original.row.body.parameters
  let roots ← NativeFinalizedLookup.all (·.id) (rootSection (snapshot x)).certificates a.original.row.body.roots
  let applies ← NativeFinalizedLookup.all (·.id) (applySection (snapshot x)).certificates a.original.row.body.applies
  some ⟨a.original.row.body.configs,inputs,eligibility,plans,parameters,roots,applies⟩

structure Checked {sha} (x : NativeSelectedVote.Checked) (a : NativeFailureSource.Abort sha x) where
  image : Image
  executed : compute x a = some image

def load {sha} (x : NativeSelectedVote.Checked) (a : NativeFailureSource.Abort sha x) : Option (Checked x a) :=
  match h : compute x a with | none => none | some image => some ⟨image,h⟩

variable {sha policy state vote facts} (loaded : NativeEarlySource.Loaded sha policy state vote facts)
    (abort : NativeFailureSource.Abort sha loaded.original) (checked : Checked loaded.original abort)

theorem originalSnapshot : NativeSnapshotBase.bindSnapshot sha loaded.original.policy loaded.original.state =
    some (snapshot loaded.original) := (NativeSelectedVote.originalByteAuthority loaded.computed).2.1

theorem originalSections :
    NativeApplySection.bindSection sha loaded.original.policy loaded.original.state = some (applySection (snapshot loaded.original)) ∧
    NativeAggregateSection.bindSection sha loaded.original.policy loaded.original.state = some (rootSection (snapshot loaded.original)) ∧
    NativeParameterSection.bindSection sha loaded.original.policy loaded.original.state = some (parameterSection (snapshot loaded.original)) ∧
    NativePlanSection.bindSection sha loaded.original.policy loaded.original.state = some (planSection (snapshot loaded.original)) ∧
    NativeEligibilitySection.bindSection sha loaded.original.policy loaded.original.state = some (ecSection (snapshot loaded.original)) := NativeCandidateAuthority.sourceSections (originalSnapshot loaded)

theorem originalIscSection : NativeFinalizedIscSection.bindSection sha loaded.original.policy loaded.original.state =
    some (iscSection loaded.original) :=
  (NativeNormSection.checkedSource (NativeEligibilitySection.checkedSource (originalSections loaded).2.2.2.2).norms).1

theorem computed : checked.image.configs = abort.original.row.body.configs ∧
    NativeFinalizedLookup.all (·.qcId) (iscSection loaded.original).certificates abort.original.row.body.inputs = some checked.image.inputs ∧
    NativeFinalizedLookup.all (·.id) (ecSection (snapshot loaded.original)).certificates abort.original.row.body.eligibility = some checked.image.eligibility ∧
    NativeFinalizedLookup.all (·.id) (planSection (snapshot loaded.original)).certificates abort.original.row.body.plans = some checked.image.plans ∧
    NativeFinalizedLookup.all (·.id) (parameterSection (snapshot loaded.original)).certificates abort.original.row.body.parameters = some checked.image.parameters ∧
    NativeFinalizedLookup.all (·.id) (rootSection (snapshot loaded.original)).certificates abort.original.row.body.roots = some checked.image.roots ∧
    NativeFinalizedLookup.all (·.id) (applySection (snapshot loaded.original)).certificates abort.original.row.body.applies = some checked.image.applies := by
  have h := checked.executed
  simp only [compute,bind,Option.bind_eq_some_iff] at h
  obtain ⟨iscs,hi,ecs,he,plans,hp,parameters,hs,roots,hr,applies,ha,last⟩ := h
  have same := Option.some.inj last
  rw [← same]
  exact ⟨rfl,hi,he,hp,hs,hr,ha⟩

theorem exactSevenLists : checked.image.ids =
    ⟨abort.original.row.body.configs,abort.original.row.body.inputs,abort.original.row.body.eligibility,
      abort.original.row.body.plans,abort.original.row.body.parameters,abort.original.row.body.roots,abort.original.row.body.applies⟩ := by
  have h := computed loaded abort checked
  simp only [Image.ids,h.1,NativeFinalizedLookup.entireOrder _ h.2.1,
    NativeFinalizedLookup.entireOrder _ h.2.2.1,NativeFinalizedLookup.entireOrder _ h.2.2.2.1,
    NativeFinalizedLookup.entireOrder _ h.2.2.2.2.1,NativeFinalizedLookup.entireOrder _ h.2.2.2.2.2.1,
    NativeFinalizedLookup.entireOrder _ h.2.2.2.2.2.2]

theorem exactCurrentLineage : NativeFailureSection.LineageSource loaded.original.policy checked.image.ids := by
  rw [exactSevenLists loaded abort checked]
  exact NativeFailureSource.allSevenAbortLists loaded abort

theorem acceptedApplyAbsence : abort.original.row.body.applies = [] := by
  rcases (NativeFailureSource.abortOriginalRow loaded abort).2 with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,same⟩
  exact same.trans (NativeFailureSource.noFinalizedApply abort)

theorem resolvedApplyAbsence : checked.image.applies = [] := by
  have h := (computed loaded abort checked).2.2.2.2.2.2
  rw [acceptedApplyAbsence loaded abort] at h
  exact (Option.some.inj h).symm

theorem originalConfigIds : ∀ id ∈ checked.image.configs, id = loaded.original.policy.config := by
  have list := (NativeFailureSource.allSevenAbortLists loaded abort).1
  have base := (NativeSnapshotBase.checkedSnapshot (originalSnapshot loaded)).2
  have same := Option.some.inj (list.symm.trans (NativeSnapshotBase.checkedBase base).finalized)
  dsimp only at same
  rw [(computed loaded abort checked).1,same]
  exact (NativeSnapshotBase.configurationsExact base).2

theorem inputAt {index : Nat} {row : NativeIscCertificate.Checked} (position : checked.image.inputs[index]? = some row) :
    abort.original.row.body.inputs[index]? = some row.qcId ∧
    NativeFinalizedLookup.one (·.qcId) (iscSection loaded.original).certificates row.qcId = some row := by
  have h := computed loaded abort checked
  exact NativeFinalizedLookup.atPosition _ h.2.1 position

theorem inputOriginal {row : NativeIscCertificate.Checked} (member : row ∈ checked.image.inputs) :
    row ∈ (iscSection loaded.original).certificates := by
  have h := computed loaded abort checked
  exact (NativeFinalizedLookup.each _ h.2.1 row member).1

theorem eligibilityAt {index : Nat} {row : NativeEligibilityLineage.Edge} (position : checked.image.eligibility[index]? = some row) :
    abort.original.row.body.eligibility[index]? = some row.id ∧
    NativeFinalizedLookup.one (·.id) (ecSection (snapshot loaded.original)).certificates row.id = some row := by
  have h := computed loaded abort checked
  exact NativeFinalizedLookup.atPosition _ h.2.2.1 position

theorem eligibilityOriginal {row : NativeEligibilityLineage.Edge} (member : row ∈ checked.image.eligibility) :
    row ∈ (ecSection (snapshot loaded.original)).certificates := by
  have h := computed loaded abort checked
  exact (NativeFinalizedLookup.each _ h.2.2.1 row member).1

theorem planAt {index : Nat} {row : NativePlanLineage.Edge} (position : checked.image.plans[index]? = some row) :
    abort.original.row.body.plans[index]? = some row.id ∧
    NativeFinalizedLookup.one (·.id) (planSection (snapshot loaded.original)).certificates row.id = some row := by
  have h := computed loaded abort checked
  exact NativeFinalizedLookup.atPosition _ h.2.2.2.1 position

theorem planOriginal {row : NativePlanLineage.Edge} (member : row ∈ checked.image.plans) :
    row ∈ (planSection (snapshot loaded.original)).certificates := by
  have h := computed loaded abort checked
  exact (NativeFinalizedLookup.each _ h.2.2.2.1 row member).1

theorem parameterAt {index : Nat} {row : NativeParameterLineage.Edge} (position : checked.image.parameters[index]? = some row) :
    abort.original.row.body.parameters[index]? = some row.id ∧
    NativeFinalizedLookup.one (·.id) (parameterSection (snapshot loaded.original)).certificates row.id = some row := by
  have h := computed loaded abort checked
  exact NativeFinalizedLookup.atPosition _ h.2.2.2.2.1 position

theorem parameterOriginal {row : NativeParameterLineage.Edge} (member : row ∈ checked.image.parameters) :
    row ∈ (parameterSection (snapshot loaded.original)).certificates := by
  have h := computed loaded abort checked
  exact (NativeFinalizedLookup.each _ h.2.2.2.2.1 row member).1

theorem rootAt {index : Nat} {row : NativeAggregateLineage.Edge} (position : checked.image.roots[index]? = some row) :
    abort.original.row.body.roots[index]? = some row.id ∧
    NativeFinalizedLookup.one (·.id) (rootSection (snapshot loaded.original)).certificates row.id = some row := by
  have h := computed loaded abort checked
  exact NativeFinalizedLookup.atPosition _ h.2.2.2.2.2.1 position

theorem rootOriginal {row : NativeAggregateLineage.Edge} (member : row ∈ checked.image.roots) :
    row ∈ (rootSection (snapshot loaded.original)).certificates := by
  have h := computed loaded abort checked
  exact (NativeFinalizedLookup.each _ h.2.2.2.2.2.1 row member).1

theorem inputCertificate {row} (member : row ∈ checked.image.inputs) :
    NativeIscCertificate.Source sha
      (NativeIscAdmission.expected loaded.original.policy loaded.original.state
        (iscSection loaded.original).schema (iscSection loaded.original).arithmetic)
      loaded.original.policy.validators row.source row :=
  NativeIscCertificate.allChecked
    (NativeFinalizedIscSection.checkedSource (originalIscSection loaded)).2.2.2.2.2.2.2.1 row
    (inputOriginal loaded abort checked member)

theorem eligibilityCertificate {row} (member : row ∈ checked.image.eligibility) :
    let b := ecSection (snapshot loaded.original)
    NativeEligibilityLineage.check sha .finalized (NativeEligibilitySection.expected loaded.original.policy loaded.original.state b.norms) loaded.original.policy.validators
      b.norms.isc.certificates b.norms.isc.finalized b.norms.norms b.seeds row.source = some row :=
  NativeEligibilitySection.certificateChecked (originalSections loaded).2.2.2.2
    (eligibilityOriginal loaded abort checked member)

theorem planCertificate {row} (member : row ∈ checked.image.plans) :
    let b := planSection (snapshot loaded.original)
    NativePlanLineage.check sha .finalized (NativePlanSection.expected loaded.original.policy loaded.original.state b.eligibility) loaded.original.policy.validators
      b.eligibility.norms.isc.certificates b.eligibility.norms.isc.finalized b.eligibility.finalized
      b.required b.eligibility.certificates b.eligibility.seeds row.source = some row :=
  NativePlanSection.certificateChecked (originalSections loaded).2.2.2.1
    (planOriginal loaded abort checked member)

theorem parameterCertificate {row} (member : row ∈ checked.image.parameters) :
    let b := parameterSection (snapshot loaded.original)
    NativeParameterLineage.check sha .finalized (NativeParameterSection.expected loaded.original.policy loaded.original.state b.plans) loaded.original.policy.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.finalized
      b.plans.finalized b.keys b.plans.eligibility.certificates b.plans.certificates row.source = some row :=
  NativeParameterSection.certificateChecked (originalSections loaded).2.2.1
    (parameterOriginal loaded abort checked member)

theorem rootCertificate {row} (member : row ∈ checked.image.roots) :
    let b := rootSection (snapshot loaded.original)
    NativeAggregateLineage.check sha .finalized (NativeParameterSection.expected loaded.original.policy loaded.original.state b.parameters.prior.plans) loaded.original.policy.validators
      b.parameters.prior.plans.eligibility.norms.isc.certificates b.parameters.prior.plans.eligibility.norms.isc.finalized
      b.parameters.prior.plans.eligibility.finalized b.parameters.prior.plans.finalized b.parameters.prior.finalized
      b.parameters.prior.keys b.parameters.prior.plans.eligibility.certificates b.parameters.prior.plans.certificates
      b.parameters.prior.certificates row.source = some row :=
  NativeAggregateSection.certificateChecked (originalSections loaded).2.1
    (rootOriginal loaded abort checked member)

end DeltaReduce.NativeAbortLineage
