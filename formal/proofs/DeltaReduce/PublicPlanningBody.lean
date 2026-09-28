import DeltaReduce.NativePlanningSource

/-! Complete EC/APC public values from original selected native edges. Names
are primitive independent metadata; full public bodies are computed here. -/
namespace DeltaReduce.PublicPlanningBody
open NativeBinding PublicState
open PublicAuthority (record setValue iscValue seedValue ecValue apcValue ClosePolicy)

inductive Key where
  | seed (id : Bytes) (transcript : NativeSeedTranscript.Transcript)
  | norm (id : Bytes) (evidence : NativeNormEvidence.Evidence) (ec : NativeEligibility.Common)
  | coefficient (id : Bytes) (plan : NativePlan.Common) (ec : NativeEligibility.Common)
  deriving DecidableEq, Repr
structure Trust where
  atom : Key → String → Prop
structure Metadata (earlyTrust : PublicEarlyBody.Trust) (trust : Trust) where
  early : PublicEarlyBody.Metadata earlyTrust
  atom : Key → Option String
  authentic : ∀ k n, atom k = some n → trust.atom k n
structure Name {earlyTrust trust} (source : Metadata earlyTrust trust) (key : Key) where
  text : String
  selected : source.atom key = some text
def loadName {earlyTrust trust} (source : Metadata earlyTrust trust) (key : Key) : Option (Name source key) :=
  match h : source.atom key with | none => none | some n => some ⟨n,h⟩
def Name.value {earlyTrust trust source key} (n : Name (earlyTrust := earlyTrust) (trust := trust) source key) : Value := .model n.text
theorem primitiveAuthority {earlyTrust trust source key} (n : Name (earlyTrust := earlyTrust) (trust := trust) source key) :
    trust.atom key n.text := source.authentic _ _ n.selected

structure IscBody {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativeIscCertificate.Checked) where
  header : PublicEarlyBody.Header source.early x
  policy : ClosePolicy
  policySelected : source.early.policy native.bodyId native.certificate.body = some policy
  entries : List (PublicEarlyBody.Entry source.early native.bodyId native.certificate.body)
  computed : PublicEarlyBody.loadEntries source.early native.bodyId native.certificate.body native.certificate.body.tuples = some entries
def loadIscBody {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativeIscCertificate.Checked) : Option (IscBody source x native) := do
  let header ← PublicEarlyBody.loadHeader source.early x
  match selected : source.early.policy native.bodyId native.certificate.body with
  | none => none
  | some policy =>
    match computed : PublicEarlyBody.loadEntries source.early native.bodyId native.certificate.body native.certificate.body.tuples with
    | none => none
    | some entries => some ⟨header,policy,selected,entries,computed⟩
def IscBody.value {earlyTrust trust source x native} (p : IscBody (earlyTrust := earlyTrust) (trust := trust) source x native) : Value :=
  iscValue p.header.round p.header.config.value p.policy (setValue (p.entries.map PublicEarlyBody.Entry.value))

structure Member {trust} (source : PublicEarlyBody.Metadata trust) (context : NativeInputSetBody.Context) where
  original : Bytes
  name : PublicEarlyBody.Name source (.ticket context original)
def loadMembers {trust} (source : PublicEarlyBody.Metadata trust) (context : NativeInputSetBody.Context) :
    List Bytes → Option (List (Member source context))
  | [] => some []
  | t::ts => do
    let name ← PublicEarlyBody.loadName source (.ticket context t)
    let rest ← loadMembers source context ts
    some (⟨t,name⟩::rest)
def Member.value {trust source context} (m : Member (trust := trust) source context) := m.name.value
theorem membersOriginal {trust source context ts ms}
    (h : loadMembers (trust := trust) source context ts = some ms) : ms.map Member.original = ts := by
  induction ts generalizing ms with
  | nil => cases Option.some.inj h; rfl
  | cons t ts ih =>
    simp only [loadMembers,bind,Option.bind_eq_some_iff] at h
    obtain ⟨name,_,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,ih hr]
theorem membersCount {trust source context ts ms}
    (h : loadMembers (trust := trust) source context ts = some ms) : ms.length = ts.length := by
  simpa only [List.length_map] using congrArg List.length (membersOriginal h)

structure EcBody {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativeEligibilityLineage.Edge) where
  parent : IscBody source x native.parent
  seed : Name source (.seed native.seed.id native.seed.transcript)
  norm : Name source (.norm native.norm.id native.norm.evidence native.certificate.common)
  members : List (Member source.early native.parent.certificate.body.context)
  computed : loadMembers source.early native.parent.certificate.body.context
    (NativePlan.acceptedTickets native.certificate) = some members
def loadEcBody {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativeEligibilityLineage.Edge) : Option (EcBody source x native) := do
  let parent ← loadIscBody source x native.parent
  let seed ← loadName source (.seed native.seed.id native.seed.transcript)
  let norm ← loadName source (.norm native.norm.id native.norm.evidence native.certificate.common)
  match computed : loadMembers source.early native.parent.certificate.body.context (NativePlan.acceptedTickets native.certificate) with
  | none => none
  | some members => some ⟨parent,seed,norm,members,computed⟩
def EcBody.seedValue {earlyTrust trust source x native} (p : EcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :=
  PublicAuthority.seedValue p.parent.value p.parent.header.epoch.value p.seed.value
def EcBody.value {earlyTrust trust source x native} (p : EcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :=
  ecValue p.parent.value p.seedValue (setValue (p.members.map Member.value)) p.norm.value
def EcBody.vote {earlyTrust trust source x native} (p : EcBody (earlyTrust := earlyTrust) (trust := trust) source x native) : Vote :=
  ⟨p.parent.header.actor.value,.text "EC",p.parent.value,p.value⟩
def EcBody.Separated {earlyTrust trust source x native} (p : EcBody (earlyTrust := earlyTrust) (trust := trust) source x native) : Prop :=
  (p.parent.entries.map PublicEarlyBody.Entry.value).Nodup ∧ (p.members.map Member.value).Nodup
instance {earlyTrust trust source x native} (p : EcBody (earlyTrust := earlyTrust) (trust := trust) source x native) : Decidable p.Separated := by
  unfold EcBody.Separated; infer_instance

-- Explicit stronger projection restriction, not a native admission theorem.
def SamePlanParents (p : NativePlanLineage.Edge) : Prop :=
  p.parent.qcId = p.ec.parent.qcId ∧ p.parent.certificate = p.ec.parent.certificate ∧
  p.seed.id = p.ec.seed.id ∧ p.seed.transcript = p.ec.seed.transcript
instance (p) : Decidable (SamePlanParents p) := by unfold SamePlanParents; infer_instance

structure ApcBody {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativePlanLineage.Edge) where
  parents : SamePlanParents native
  ec : EcBody source x native.ec
  coefficient : Name source (.coefficient native.id native.certificate.common native.ec.certificate.common)
  members : List (Member source.early native.ec.parent.certificate.body.context)
  computed : loadMembers source.early native.ec.parent.certificate.body.context
    (native.certificate.common.weights.map NativePlan.Weight.ticket) = some members
  sameMembers : members.map Member.value = ec.members.map Member.value
def loadApcBody {earlyTrust trust} (source : Metadata earlyTrust trust) (x : NativeSelectedVote.Checked)
    (native : NativePlanLineage.Edge) : Option (ApcBody source x native) := do
  if parents : SamePlanParents native then
    let ec ← loadEcBody source x native.ec
    let coefficient ← loadName source (.coefficient native.id native.certificate.common native.ec.certificate.common)
    match computed : loadMembers source.early native.ec.parent.certificate.body.context
        (native.certificate.common.weights.map NativePlan.Weight.ticket) with
    | none => none
    | some members =>
      if sameMembers : members.map Member.value = ec.members.map Member.value then
        some ⟨parents,ec,coefficient,members,computed,sameMembers⟩ else none
  else none
def ApcBody.value {earlyTrust trust source x native} (p : ApcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :=
  apcValue p.ec.parent.value p.ec.seedValue p.ec.value (setValue (p.members.map Member.value)) p.coefficient.value
theorem loadApcFromComponents {earlyTrust trust source x native}
    (p : ApcBody (earlyTrust := earlyTrust) (trust := trust) source x native)
    (ec : loadEcBody source x native.ec = some p.ec)
    (coefficient : loadName source (.coefficient native.id native.certificate.common native.ec.certificate.common) = some p.coefficient) :
    loadApcBody source x native = some p := by
  unfold loadApcBody
  simp only [dif_pos p.parents,ec,bind,Option.bind,coefficient]
  split
  · rename_i missing; rw [p.computed] at missing; contradiction
  · rename_i members hm
    have same := Option.some.inj (p.computed.symm.trans hm); subst members
    simp only [dif_pos p.sameMembers]
def ApcBody.vote {earlyTrust trust source x native} (p : ApcBody (earlyTrust := earlyTrust) (trust := trust) source x native) : Vote :=
  ⟨p.ec.parent.header.actor.value,.text "APC",p.ec.value,p.value⟩

inductive Image (x : NativeSelectedVote.Checked) {earlyTrust trust} (source : Metadata earlyTrust trust) where
  | ec (native : NativePlanningSource.Ec x) (body : EcBody source x native.original)
  | apc (native : NativePlanningSource.Plan x) (body : ApcBody source x native.original)
def Image.vote {x earlyTrust trust source} : Image x (earlyTrust := earlyTrust) (trust := trust) source → Vote
  | .ec _ body => body.vote | .apc _ body => body.vote
def Image.Separated {x earlyTrust trust source} : Image x (earlyTrust := earlyTrust) (trust := trust) source → Prop
  | .ec _ body => body.Separated
  | .apc _ body => body.ec.Separated ∧ (body.members.map Member.value).Nodup
instance {x earlyTrust trust source} (p : Image x (earlyTrust := earlyTrust) (trust := trust) source) : Decidable p.Separated := by
  cases p <;> unfold Image.Separated <;> infer_instance

def project (x : NativeSelectedVote.Checked) {earlyTrust trust} (source : Metadata earlyTrust trust) : Option (Image x source) := do
  if x.admitted.selected.original.action = 3 then
    let e ← NativePlanningSource.loadEc x
    let body ← loadEcBody source x e.original
    some (.ec e body)
  else
    let p ← NativePlanningSource.loadPlan x
    let body ← loadApcBody source x p.original
    some (.apc p body)

structure Checked {sha policy state vote facts} (loaded : NativeEarlySource.Loaded sha policy state vote facts)
    {earlyTrust trust} (source : Metadata earlyTrust trust) (models : List String) (candidate : Vote) where
  image : Image loaded.original source
  computed : project loaded.original source = some image
  entire : candidate = image.vote
  separated : image.Separated
  canonical : PublicState.canonical models (.function (voteEntries candidate)) = true
def check {sha policy state vote facts} (loaded : NativeEarlySource.Loaded sha policy state vote facts)
    {earlyTrust trust} (source : Metadata earlyTrust trust) (models : List String) (candidate : Vote) :
    Option (Checked loaded source models candidate) :=
  match computed : project loaded.original source with
  | none => none
  | some image =>
    if valid : candidate = image.vote ∧ image.Separated ∧ PublicState.canonical models (.function (voteEntries candidate)) = true then
      some ⟨image,computed,valid.1,valid.2.1,valid.2.2⟩ else none

theorem completeOriginalIsc {earlyTrust trust source x native}
    (p : IscBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    p.entries.map PublicEarlyBody.Entry.original = native.certificate.body.tuples := PublicEarlyBody.entriesOriginal p.computed
theorem ecOriginalMembers {earlyTrust trust source x native}
    (p : EcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    p.members.map Member.original = NativePlan.acceptedTickets native.certificate := membersOriginal p.computed
theorem apcOriginalMembers {earlyTrust trust source x native}
    (p : ApcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    p.members.map Member.original = native.certificate.common.weights.map NativePlan.Weight.ticket := membersOriginal p.computed
theorem ecParentShape {earlyTrust trust source x native}
    (p : EcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    readField p.value "isc" = some p.parent.value ∧ readField p.seedValue "isc" = some p.parent.value ∧
    readField p.value "seed" = some p.seedValue ∧ readField p.value "normEvidence" = some p.norm.value := ⟨rfl,rfl,rfl,rfl⟩
theorem apcParentShape {earlyTrust trust source x native}
    (p : ApcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    readField p.value "isc" = readField p.ec.value "isc" ∧
    readField p.value "seed" = readField p.ec.value "seed" ∧
    readField p.value "ec" = some p.ec.value ∧
    readField p.value "members" = readField p.ec.value "members" := by
  refine ⟨rfl,rfl,rfl,?_⟩
  change some (setValue (p.members.map Member.value)) = some (setValue (p.ec.members.map Member.value))
  rw [p.sameMembers]
theorem nativeParentsRetained {earlyTrust trust source x native}
    (p : ApcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    native.parent.certificate = native.ec.parent.certificate ∧ native.seed.transcript = native.ec.seed.transcript :=
  ⟨p.parents.2.1,p.parents.2.2.2⟩
theorem differentPlanParentsReject {earlyTrust trust source x native} (h : ¬ SamePlanParents native) :
    loadApcBody (earlyTrust := earlyTrust) (trust := trust) source x native = none := by
  simp only [loadApcBody,dif_neg h]
theorem checkedWholeVote {sha policy state vote facts loaded earlyTrust trust source models candidate}
    (p : Checked (sha := sha) (policy := policy) (state := state) (vote := vote) (facts := facts)
      loaded (earlyTrust := earlyTrust) (trust := trust) source models candidate) :
    candidate = p.image.vote ∧ PublicState.canonical models (.function (voteEntries candidate)) = true := ⟨p.entire,p.canonical⟩

theorem memberSetCoverage {trust source context} (ms : List (Member (trust := trust) source context)) :
    ∃ values, setValue (ms.map Member.value) = .set values ∧
      (PublicAuthority.valuesList values).Perm (ms.map Member.value) := PublicAuthority.setRetainsAllValues _
theorem seedKeyRetainsShares {id a b} (different : a.shares ≠ b.shares) : Key.seed id a ≠ .seed id b := by
  intro h; cases h; exact different rfl
theorem normKeyRetainsEntries {id a b ec} (different : a.entries ≠ b.entries) : Key.norm id a ec ≠ .norm id b ec := by
  intro h; cases h; exact different rfl
theorem coefficientKeyRetainsWeights {id a b ec} (different : a.weights ≠ b.weights) : Key.coefficient id a ec ≠ .coefficient id b ec := by
  intro h; cases h; exact different rfl
theorem ecProjectFromComponents {x earlyTrust trust source native body}
    (kind : x.admitted.selected.original.action = 3) (selected : NativePlanningSource.loadEc x = some native)
    (computed : loadEcBody (earlyTrust := earlyTrust) (trust := trust) source x native.original = some body) :
    project x source = some (.ec native body) := by simp only [project,if_pos kind,selected,bind,Option.bind,computed]
theorem apcProjectFromComponents {x earlyTrust trust source native body}
    (kind : x.admitted.selected.original.action ≠ 3) (selected : NativePlanningSource.loadPlan x = some native)
    (computed : loadApcBody (earlyTrust := earlyTrust) (trust := trust) source x native.original = some body) :
    project x source = some (.apc native body) := by simp only [project,if_neg kind,selected,bind,Option.bind,computed]
theorem checkFromComponents {sha policy state vote facts loaded earlyTrust trust source models candidate}
    (image : Image loaded.original (earlyTrust := earlyTrust) (trust := trust) source)
    (computed : project loaded.original source = some image) (entire : candidate = image.vote)
    (separated : image.Separated) (canonical : PublicState.canonical models (.function (voteEntries candidate)) = true) :
    check (sha := sha) (policy := policy) (state := state) (vote := vote) (facts := facts) loaded source models candidate =
      some ⟨image,computed,entire,separated,canonical⟩ := by
  unfold check
  split
  · rename_i missing; rw [computed] at missing; contradiction
  · rename_i found hf
    have same := Option.some.inj (computed.symm.trans hf); subst found
    simp only [dif_pos (And.intro entire (And.intro separated canonical))]
theorem changedVoteRejects {sha policy state vote facts loaded earlyTrust trust source models candidate image}
    (computed : project loaded.original (earlyTrust := earlyTrust) (trust := trust) source = some image)
    (changed : candidate ≠ image.vote) :
    check (sha := sha) (policy := policy) (state := state) (vote := vote) (facts := facts) loaded source models candidate = none := by
  unfold check
  split
  · rfl
  · rename_i found hf
    have same := Option.some.inj (computed.symm.trans hf); subst found
    split
    · rename_i valid; exact False.elim (changed valid.1)
    · rfl

end DeltaReduce.PublicPlanningBody
