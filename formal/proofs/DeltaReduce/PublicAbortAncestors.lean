import DeltaReduce.NativeAbortLineage
import DeltaReduce.PublicPlanningBody
import DeltaReduce.PublicFailureBody

/-! Partial ABORT ancestor projection. Full native PARAMETER/ROOT payloads remain
in `native`; this module deliberately has no complete ABORT body/vote function.
Metadata authentication and live configuration remain independent premises. -/
namespace DeltaReduce.PublicAbortAncestors
open PublicState PublicPlanningBody

def collect {α : Type} (f : α → Option Value) : List α → Option (List Value)
  | [] => some []
  | x::xs => do
    let v ← f x
    let vs ← collect f xs
    some (v::vs)

theorem collectedPairs {α f xs vs} (h : collect (α := α) f xs = some vs) :
    List.Forall₂ (fun x v => f x = some v) xs vs := by
  induction xs generalizing vs with
  | nil => cases Option.some.inj h; exact .nil
  | cons x xs ih =>
    simp only [collect,Bind.bind,Option.bind_eq_some_iff] at h
    obtain ⟨v,hv,rest,hr,last⟩ := h
    cases Option.some.inj last
    exact .cons hv (ih hr)

theorem collectedCount {α f xs vs} (h : collect (α := α) f xs = some vs) :
    vs.length = xs.length := (List.Forall₂.length_eq (collectedPairs h)).symm

theorem collectedAt {α f xs vs} (h : collect (α := α) f xs = some vs)
    {index : Nat} {v} (position : vs[index]? = some v) :
    ∃ x, xs[index]? = some x ∧ f x = some v := by
  induction xs generalizing vs index with
  | nil => cases Option.some.inj h; simp at position
  | cons x xs ih =>
    simp only [collect,Bind.bind,Option.bind_eq_some_iff] at h
    obtain ⟨first,hf,rest,hr,last⟩ := h
    cases Option.some.inj last
    cases index with
    | zero => simp only [List.getElem?_cons_zero,Option.some.injEq] at position
              subst v; exact ⟨x,rfl,hf⟩
    | succ i => exact ih hr position

def isc {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativeIscCertificate.Checked) : Option Value := do
  let p ← loadIscBody source x native
  if (p.entries.map PublicEarlyBody.Entry.value).Nodup then some p.value else none

def ec {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativeEligibilityLineage.Edge) : Option Value := do
  let p ← loadEcBody source x native
  if p.Separated then some p.value else none

def apc {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativePlanLineage.Edge) : Option Value := do
  let p ← loadApcBody source x native
  if p.ec.Separated ∧ (p.members.map Member.value).Nodup then some p.value else none

theorem iscComputed {earlyTrust trust source x native v}
    (h : isc (earlyTrust := earlyTrust) (trust := trust) source x native = some v) :
    ∃ p, loadIscBody source x native = some p ∧ (p.entries.map PublicEarlyBody.Entry.value).Nodup ∧ v = p.value := by
  simp only [isc,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,last⟩ := h
  split at last <;> try contradiction
  exact ⟨p,hp,by assumption,(Option.some.inj last).symm⟩

theorem ecComputed {earlyTrust trust source x native v}
    (h : ec (earlyTrust := earlyTrust) (trust := trust) source x native = some v) :
    ∃ p, loadEcBody source x native = some p ∧ p.Separated ∧ v = p.value := by
  simp only [ec,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,last⟩ := h
  split at last <;> try contradiction
  exact ⟨p,hp,by assumption,(Option.some.inj last).symm⟩

theorem apcComputed {earlyTrust trust source x native v}
    (h : apc (earlyTrust := earlyTrust) (trust := trust) source x native = some v) :
    ∃ p, loadApcBody source x native = some p ∧ p.ec.Separated ∧ (p.members.map Member.value).Nodup ∧ v = p.value := by
  simp only [apc,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  exact ⟨p,hp,valid.1,valid.2,(Option.some.inj last).symm⟩

structure Image {sha x} (abort : NativeFailureSource.Abort sha x)
    {earlyTrust trust} (source : Metadata earlyTrust trust) where
  native : NativeAbortLineage.Checked x abort
  configs : List (PublicFailureBody.Config source.early)
  configsComputed : PublicFailureBody.loadConfigs source.early native.image.configs = some configs
  inputs : List Value
  inputsComputed : collect (isc source x) native.image.inputs = some inputs
  eligibility : List Value
  eligibilityComputed : collect (ec source x) native.image.eligibility = some eligibility
  plans : List Value
  plansComputed : collect (apc source x) native.image.plans = some plans

def project {sha x} (abort : NativeFailureSource.Abort sha x)
    {earlyTrust trust} (source : Metadata earlyTrust trust) : Option (Image abort source) := do
  let native ← NativeAbortLineage.load x abort
  match hc : PublicFailureBody.loadConfigs source.early native.image.configs with
  | none => none
  | some configs =>
    match hi : collect (isc source x) native.image.inputs with
    | none => none
    | some inputs =>
      match he : collect (ec source x) native.image.eligibility with
      | none => none
      | some eligibility =>
        match hp : collect (apc source x) native.image.plans with
        | none => none
        | some plans => some ⟨native,configs,hc,inputs,hi,eligibility,he,plans,hp⟩

def Image.ancestorFields {sha x abort earlyTrust trust source}
    (p : Image (sha := sha) (x := x) abort (earlyTrust := earlyTrust) (trust := trust) source) : Value :=
  PublicAuthority.record [("apc",PublicAuthority.setValue p.plans),
    ("configs",PublicAuthority.setValue (p.configs.map PublicFailureBody.Config.value)),
    ("ec",PublicAuthority.setValue p.eligibility),("isc",PublicAuthority.setValue p.inputs)]

def Image.Separated {sha x abort earlyTrust trust source}
    (p : Image (sha := sha) (x := x) abort (earlyTrust := earlyTrust) (trust := trust) source) : Prop :=
  (p.configs.map PublicFailureBody.Config.value).Nodup ∧ p.inputs.Nodup ∧ p.eligibility.Nodup ∧ p.plans.Nodup
instance {sha x abort earlyTrust trust source}
    (p : Image (sha := sha) (x := x) abort (earlyTrust := earlyTrust) (trust := trust) source) : Decidable p.Separated := by
  unfold Image.Separated; infer_instance

structure Checked {sha policy state vote facts} (loaded : NativeEarlySource.Loaded sha policy state vote facts)
    (abort : NativeFailureSource.Abort sha loaded.original) {earlyTrust trust}
    (source : Metadata earlyTrust trust) (models : List String) where
  image : Image abort source
  computed : project abort source = some image
  separated : image.Separated
  canonical : PublicState.canonical models image.ancestorFields = true

def check {sha policy state vote facts} (loaded : NativeEarlySource.Loaded sha policy state vote facts)
    (abort : NativeFailureSource.Abort sha loaded.original) {earlyTrust trust}
    (source : Metadata earlyTrust trust) (models : List String) : Option (Checked loaded abort source models) :=
  match computed : project abort source with
  | none => none
  | some image =>
    if valid : image.Separated ∧ PublicState.canonical models image.ancestorFields = true then
      some ⟨image,computed,valid.1,valid.2⟩ else none

variable {sha policy state vote facts} (loaded : NativeEarlySource.Loaded sha policy state vote facts)
  {abort : NativeFailureSource.Abort sha loaded.original} {earlyTrust trust source}
  (p : Image abort (earlyTrust := earlyTrust) (trust := trust) source)

theorem originalSevenLists : NativeFailureSection.LineageSource loaded.original.policy p.native.image.ids :=
  NativeAbortLineage.exactCurrentLineage loaded abort p.native

theorem configsOriginal : p.configs.map PublicFailureBody.Config.original = abort.original.row.body.configs :=
  (PublicFailureBody.configsOriginal p.configsComputed).trans (NativeAbortLineage.computed loaded abort p.native).1

theorem originalCounts : p.inputs.length = abort.original.row.body.inputs.length ∧
    p.eligibility.length = abort.original.row.body.eligibility.length ∧ p.plans.length = abort.original.row.body.plans.length := by
  have h := NativeAbortLineage.computed loaded abort p.native
  exact ⟨(collectedCount p.inputsComputed).trans (NativeFinalizedLookup.count _ h.2.1),
    (collectedCount p.eligibilityComputed).trans (NativeFinalizedLookup.count _ h.2.2.1),
    (collectedCount p.plansComputed).trans (NativeFinalizedLookup.count _ h.2.2.2.1)⟩

theorem inputAt {index : Nat} {v} (positionValue : p.inputs[index]? = some v) :
    ∃ n, abort.original.row.body.inputs[index]? = some n.qcId ∧
      n ∈ (NativeAbortLineage.iscSection loaded.original).certificates ∧ isc source loaded.original n = some v := by
  obtain ⟨n,position,computed⟩ := collectedAt p.inputsComputed positionValue
  exact ⟨n,(NativeAbortLineage.inputAt loaded abort p.native position).1,
    NativeAbortLineage.inputOriginal loaded abort p.native (List.mem_of_getElem? position),computed⟩

theorem eligibilityAt {index : Nat} {v} (positionValue : p.eligibility[index]? = some v) :
    ∃ n, abort.original.row.body.eligibility[index]? = some n.id ∧
      n ∈ (NativeCandidateAuthority.ecSection (NativeAbortLineage.snapshot loaded.original)).certificates ∧ ec source loaded.original n = some v := by
  obtain ⟨n,position,computed⟩ := collectedAt p.eligibilityComputed positionValue
  exact ⟨n,(NativeAbortLineage.eligibilityAt loaded abort p.native position).1,
    NativeAbortLineage.eligibilityOriginal loaded abort p.native (List.mem_of_getElem? position),computed⟩

theorem planAt {index : Nat} {v} (positionValue : p.plans[index]? = some v) :
    ∃ n, abort.original.row.body.plans[index]? = some n.id ∧
      n ∈ (NativeCandidateAuthority.planSection (NativeAbortLineage.snapshot loaded.original)).certificates ∧ apc source loaded.original n = some v := by
  obtain ⟨n,position,computed⟩ := collectedAt p.plansComputed positionValue
  exact ⟨n,(NativeAbortLineage.planAt loaded abort p.native position).1,
    NativeAbortLineage.planOriginal loaded abort p.native (List.mem_of_getElem? position),computed⟩

theorem arithmeticPayloadsRetained : p.native.image.parameters.map (·.id) = abort.original.row.body.parameters ∧
    p.native.image.roots.map (·.id) = abort.original.row.body.roots := by
  have h := NativeAbortLineage.computed loaded abort p.native
  exact ⟨NativeFinalizedLookup.entireOrder _ h.2.2.2.2.1,NativeFinalizedLookup.entireOrder _ h.2.2.2.2.2.1⟩

theorem applyAbsenceDerived : p.native.image.applies = [] := NativeAbortLineage.resolvedApplyAbsence loaded abort p.native

theorem setsRetainValues {vs : List Value} : ∃ values, PublicAuthority.setValue vs = .set values ∧
    (PublicAuthority.valuesList values).Perm vs := PublicAuthority.setRetainsAllValues _

end DeltaReduce.PublicAbortAncestors
