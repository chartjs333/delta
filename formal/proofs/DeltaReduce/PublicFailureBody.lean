import DeltaReduce.NativeFailureSource

/-! Complete VIEW_CHANGE and explicitly empty-downstream ABORT public bodies.
Nonempty certificate lineage rejects; it is never replaced by empty sets. -/
namespace DeltaReduce.PublicFailureBody
open NativeBinding PublicState
open PublicAuthority (record setValue)

structure Limits where
  maxView : Nat
  maxTime : Nat
  softDeadline : Nat
  hardDeadline : Nat
  deriving DecidableEq, Repr
def ViewFits (c : Limits) (b : NativeFailurePayload.ViewBody) : Prop :=
  b.fromView ≤ c.maxView ∧ b.toView ≤ c.maxView ∧ b.deadline = c.softDeadline ∧
  c.softDeadline ≤ c.hardDeadline ∧ c.hardDeadline ≤ c.maxTime
instance (c b) : Decidable (ViewFits c b) := by unfold ViewFits; infer_instance
def AbortFits (c : Limits) (b : NativeFailurePayload.AbortBody) : Prop :=
  b.view ≤ c.maxView ∧ b.deadline = c.hardDeadline ∧ c.softDeadline ≤ c.hardDeadline ∧ c.hardDeadline ≤ c.maxTime
instance (c b) : Decidable (AbortFits c b) := by unfold AbortFits; infer_instance
def EmptyLineage (b : NativeFailurePayload.AbortBody) : Prop :=
  b.inputs = [] ∧ b.eligibility = [] ∧ b.plans = [] ∧ b.parameters = [] ∧ b.roots = [] ∧ b.applies = []
instance (b) : Decidable (EmptyLineage b) := by unfold EmptyLineage; infer_instance

def reason (bytes : Bytes) : Option String :=
  if bytes = NativeVoteBytes.ascii "HARD_DEADLINE" then some "HARD_DEADLINE"
  else if bytes = NativeVoteBytes.ascii "INCOMPLETE_INPUT" then some "INCOMPLETE_INPUT"
  else if bytes = NativeVoteBytes.ascii "UNSAFE_COEFFICIENTS" then some "UNSAFE_COEFFICIENTS"
  else if bytes = NativeVoteBytes.ascii "IRRECOVERABLE_AVAILABILITY" then some "IRRECOVERABLE_AVAILABILITY"
  else if bytes = NativeVoteBytes.ascii "PARAMETER_FAILURE" then some "PARAMETER_FAILURE"
  else if bytes = NativeVoteBytes.ascii "APPLY_FAILURE" then some "APPLY_FAILURE" else none

structure Trust where
  checkpoint : NativeFailurePayload.AbortBody → String → Prop
structure Metadata (earlyTrust : PublicEarlyBody.Trust) (trust : Trust) where
  early : PublicEarlyBody.Metadata earlyTrust
  checkpoint : NativeFailurePayload.AbortBody → Option String
  authentic : ∀ b n, checkpoint b = some n → trust.checkpoint b n

structure Config {trust} (source : PublicEarlyBody.Metadata trust) where
  original : Bytes
  name : PublicEarlyBody.Name source (.config original)
def loadConfigs {trust} (source : PublicEarlyBody.Metadata trust) : List Bytes → Option (List (Config source))
  | [] => some []
  | id::ids => do
    let name ← PublicEarlyBody.loadName source (.config id)
    let rest ← loadConfigs source ids
    some (⟨id,name⟩::rest)
def Config.value {trust source} (c : Config (trust := trust) source) := c.name.value
theorem configsOriginal {trust source ids configs}
    (h : loadConfigs (trust := trust) source ids = some configs) : configs.map Config.original = ids := by
  induction ids generalizing configs with
  | nil => cases Option.some.inj h; rfl
  | cons id ids ih =>
    simp only [loadConfigs,bind,Option.bind_eq_some_iff] at h
    obtain ⟨name,_,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,ih hr]

structure ViewImage {earlyTrust trust} (source : Metadata earlyTrust trust) (limits : Limits)
    (x : NativeSelectedVote.Checked) (native : NativeFailurePayload.ViewBody) where
  header : PublicEarlyBody.Header source.early x
  fits : ViewFits limits native
def loadViewBody {earlyTrust trust} (source : Metadata earlyTrust trust) (limits : Limits)
    (x : NativeSelectedVote.Checked) (native : NativeFailurePayload.ViewBody) : Option (ViewImage source limits x native) := do
  let header ← PublicEarlyBody.loadHeader source.early x
  if fits : ViewFits limits native then some ⟨header,fits⟩ else none
def ViewImage.value {earlyTrust trust source limits x native}
    (p : ViewImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) :=
  record [("fromView",.integer native.fromView),("round",p.header.round),
    ("softDeadline",.integer native.deadline),("toView",.integer native.toView)]
def ViewImage.context {earlyTrust trust source limits x native}
    (p : ViewImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) :=
  record [("fromView",.integer native.fromView),("round",p.header.round)]
def ViewImage.vote {earlyTrust trust source limits x native}
    (p : ViewImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) : Vote :=
  ⟨p.header.actor.value,.text "VIEW_CHANGE",p.context,p.value⟩
def ViewImage.observation {earlyTrust trust source limits x native}
    (p : ViewImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) :=
  record [("round",p.header.round),("view",.integer native.fromView)]

structure AbortImage {earlyTrust trust} (source : Metadata earlyTrust trust) (limits : Limits)
    (x : NativeSelectedVote.Checked) (native : NativeFailurePayload.AbortBody) where
  header : PublicEarlyBody.Header source.early x
  fits : AbortFits limits native
  empty : EmptyLineage native
  checkpoint : String
  checkpointSelected : source.checkpoint native = some checkpoint
  reason : String
  reasonComputed : PublicFailureBody.reason native.reason = some reason
  configs : List (Config source.early)
  configsComputed : loadConfigs source.early native.configs = some configs
def loadAbortBody {earlyTrust trust} (source : Metadata earlyTrust trust) (limits : Limits)
    (x : NativeSelectedVote.Checked) (native : NativeFailurePayload.AbortBody) : Option (AbortImage source limits x native) := do
  if valid : AbortFits limits native ∧ EmptyLineage native then
    let header ← PublicEarlyBody.loadHeader source.early x
    match checkpointSelected : source.checkpoint native with
    | none => none
    | some checkpoint =>
      match reasonComputed : reason native.reason with
      | none => none
      | some why =>
        match configsComputed : loadConfigs source.early native.configs with
        | none => none
        | some configs => some ⟨header,valid.1,valid.2,checkpoint,checkpointSelected,why,reasonComputed,configs,configsComputed⟩
  else none
def emptyLineageValue : Value := record
  [("aggregate",setValue []),("apc",setValue []),("apply",setValue []),
   ("ec",setValue []),("isc",setValue []),("parameter",setValue [])]
def AbortImage.value {earlyTrust trust source limits x native}
    (p : AbortImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) :=
  record [("configs",setValue (p.configs.map Config.value)),("hardDeadline",.integer native.deadline),
    ("lineage",emptyLineageValue),("parentCheckpoint",.model p.checkpoint),("reason",.text p.reason),
    ("round",p.header.round),("validatorEpoch",p.header.epoch.value),("view",.integer native.view)]
def AbortImage.vote {earlyTrust trust source limits x native}
    (p : AbortImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) : Vote :=
  ⟨p.header.actor.value,.text "ABORT",p.header.round,p.value⟩

inductive Image (sha : Bytes → Bytes) (x : NativeSelectedVote.Checked) {earlyTrust trust}
    (source : Metadata earlyTrust trust) (limits : Limits) where
  | view (native : NativeFailureSource.View sha x) (body : ViewImage source limits x native.original.row.body)
  | abort (native : NativeFailureSource.Abort sha x) (body : AbortImage source limits x native.original.row.body)
def Image.vote {sha x earlyTrust trust source limits} : Image sha x (earlyTrust := earlyTrust) (trust := trust) source limits → Vote
  | .view _ b => b.vote | .abort _ b => b.vote
def Image.Separated {sha x earlyTrust trust source limits} : Image sha x (earlyTrust := earlyTrust) (trust := trust) source limits → Prop
  | .view _ _ => True | .abort _ b => (b.configs.map Config.value).Nodup
instance {sha x earlyTrust trust source limits} (p : Image sha x (earlyTrust := earlyTrust) (trust := trust) source limits) : Decidable p.Separated := by
  cases p <;> unfold Image.Separated <;> infer_instance
def project (sha : Bytes → Bytes) (x : NativeSelectedVote.Checked) {earlyTrust trust}
    (source : Metadata earlyTrust trust) (limits : Limits) : Option (Image sha x source limits) := do
  if x.admitted.selected.original.action = 8 then
    let v ← NativeFailureSource.loadView sha x
    let b ← loadViewBody source limits x v.original.row.body
    some (.view v b)
  else
    let a ← NativeFailureSource.loadAbort sha x
    let b ← loadAbortBody source limits x a.original.row.body
    some (.abort a b)

def ConfigurationFits (limits : Limits) (x : NativeSelectedVote.Checked) : Prop :=
  limits.softDeadline = x.policy.softDeadline ∧ limits.hardDeadline = x.policy.hardDeadline
instance (limits x) : Decidable (ConfigurationFits limits x) := by unfold ConfigurationFits; infer_instance
structure Checked {sha policy state vote facts} (loaded : NativeEarlySource.Loaded sha policy state vote facts)
    {earlyTrust trust} (source : Metadata earlyTrust trust) (limits : Limits) (models : List String) (candidate : Vote) where
  image : Image sha loaded.original source limits
  computed : project sha loaded.original source limits = some image
  entire : candidate = image.vote
  separated : image.Separated
  canonical : PublicState.canonical models (.function (voteEntries candidate)) = true
  configured : ConfigurationFits limits loaded.original
def check {sha policy state vote facts} (loaded : NativeEarlySource.Loaded sha policy state vote facts)
    {earlyTrust trust} (source : Metadata earlyTrust trust) (limits : Limits) (models : List String) (candidate : Vote) :
    Option (Checked loaded source limits models candidate) :=
  match computed : project sha loaded.original source limits with
  | none => none
  | some image =>
    if valid : candidate = image.vote ∧ image.Separated ∧ PublicState.canonical models (.function (voteEntries candidate)) = true ∧ ConfigurationFits limits loaded.original then
      some ⟨image,computed,valid.1,valid.2.1,valid.2.2.1,valid.2.2.2⟩ else none

theorem viewExactNumbers {earlyTrust trust source limits x native}
    (p : ViewImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) :
    readField p.value "fromView" = some (.integer native.fromView) ∧
    readField p.value "toView" = some (.integer native.toView) ∧
    readField p.value "softDeadline" = some (.integer native.deadline) := ⟨rfl,rfl,rfl⟩
theorem abortAllConfigs {earlyTrust trust source limits x native}
    (p : AbortImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) :
    p.configs.map Config.original = native.configs := configsOriginal p.configsComputed
theorem abortExactAbsence {earlyTrust trust source limits x native}
    (p : AbortImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) :
    native.inputs = [] ∧ native.eligibility = [] ∧ native.plans = [] ∧ native.parameters = [] ∧ native.roots = [] ∧ native.applies = [] := p.empty
theorem abortCheckpointAuthority {earlyTrust trust source limits x native}
    (p : AbortImage (earlyTrust := earlyTrust) (trust := trust) source limits x native) : trust.checkpoint native p.checkpoint :=
  source.authentic _ _ p.checkpointSelected
theorem nonemptyLineageRejects {earlyTrust trust source limits x native} (nonempty : ¬ EmptyLineage native) :
    loadAbortBody (earlyTrust := earlyTrust) (trust := trust) source limits x native = none := by
  have bad : ¬ (AbortFits limits native ∧ EmptyLineage native) := fun h => nonempty h.2
  simp only [loadAbortBody,dif_neg bad]
theorem outsideViewLimitsRejects {earlyTrust trust source limits x native} (bad : ¬ ViewFits limits native) :
    loadViewBody (earlyTrust := earlyTrust) (trust := trust) source limits x native = none := by
  unfold loadViewBody; cases PublicEarlyBody.loadHeader source.early x <;> simp only [bind,Option.bind,dif_neg bad]
theorem checkedWholeVote {sha policy state vote facts loaded earlyTrust trust source limits models candidate}
    (p : Checked (sha := sha) (policy := policy) (state := state) (vote := vote) (facts := facts)
      loaded (earlyTrust := earlyTrust) (trust := trust) source limits models candidate) :
    candidate = p.image.vote ∧ PublicState.canonical models (.function (voteEntries candidate)) = true := ⟨p.entire,p.canonical⟩
theorem checkedDeadlines {sha policy state vote facts loaded earlyTrust trust source limits models candidate}
    (p : Checked (sha := sha) (policy := policy) (state := state) (vote := vote) (facts := facts)
      loaded (earlyTrust := earlyTrust) (trust := trust) source limits models candidate) :
    limits.softDeadline = loaded.original.policy.softDeadline ∧ limits.hardDeadline = loaded.original.policy.hardDeadline := p.configured
theorem viewObservationFromSource {sha x earlyTrust trust source limits}
    (v : NativeFailureSource.View sha x)
    (p : ViewImage (earlyTrust := earlyTrust) (trust := trust) source limits x v.original.row.body) :
    p.observation = record [("round",p.header.round),("view",.integer v.original.observation.view)] := by
  have h := (NativeFailureSource.exactTimeout v).2.2.2.1
  have same := (NativeFailureSource.viewNumbers v).2.2.1
  simp only [ViewImage.observation,same,h]
theorem configSetCoverage {trust source} (cs : List (Config (trust := trust) source)) :
    ∃ values, setValue (cs.map Config.value) = .set values ∧
      (PublicAuthority.valuesList values).Perm (cs.map Config.value) := PublicAuthority.setRetainsAllValues _
theorem checkFromComponents {sha policy state vote facts loaded earlyTrust trust source limits models candidate}
    (image : Image sha loaded.original (earlyTrust := earlyTrust) (trust := trust) source limits)
    (computed : project sha loaded.original source limits = some image) (entire : candidate = image.vote)
    (separated : image.Separated) (canonical : PublicState.canonical models (.function (voteEntries candidate)) = true)
    (configured : ConfigurationFits limits loaded.original) :
    check (sha := sha) (policy := policy) (state := state) (vote := vote) (facts := facts) loaded source limits models candidate =
      some ⟨image,computed,entire,separated,canonical,configured⟩ := by
  unfold check; split
  · rename_i missing; rw [computed] at missing; contradiction
  · rename_i found hf
    have same := Option.some.inj (computed.symm.trans hf); subst found
    simp only [dif_pos (And.intro entire (And.intro separated (And.intro canonical configured)))]
theorem wrongConfigurationRejects {sha policy state vote facts loaded earlyTrust trust source limits models candidate}
    (wrong : ¬ ConfigurationFits limits loaded.original) :
    check (sha := sha) (policy := policy) (state := state) (vote := vote) (facts := facts)
      loaded (earlyTrust := earlyTrust) (trust := trust) source limits models candidate = none := by
  unfold check; split
  · rfl
  · split
    · rename_i valid; exact False.elim (wrong valid.2.2.2)
    · rfl
theorem changedVoteRejects {sha policy state vote facts loaded earlyTrust trust source limits models candidate image}
    (computed : project sha loaded.original (earlyTrust := earlyTrust) (trust := trust) source limits = some image)
    (changed : candidate ≠ image.vote) :
    check (sha := sha) (policy := policy) (state := state) (vote := vote) (facts := facts) loaded source limits models candidate = none := by
  unfold check; split
  · rfl
  · rename_i found hf
    have same := Option.some.inj (computed.symm.trans hf); subst found
    split
    · rename_i valid; exact False.elim (changed valid.1)
    · rfl

end DeltaReduce.PublicFailureBody
