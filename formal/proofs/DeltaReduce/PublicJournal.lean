import DeltaReduce.NativeReplay

/-! Exact per-actor public vote-journal projection, including non-arithmetic
slots. Other-action admission and exporter/hash provenance remain named
premises, not arithmetic-admission bypasses or fabricated native receipts. -/
namespace DeltaReduce.PublicJournal
open NativeBinding RecoveryKernel
abbrev Bytes := NativeBinding.Bytes

inductive Action where
  | config | isc | ec | apc | parameter | root | apply | view | abort
  deriving DecidableEq, Repr

def Action.tag : Action → String
  | .config => "ACT-CONFIG-VOTE" | .isc => "ACT-ISC-VOTE" | .ec => "ACT-EC-VOTE"
  | .apc => "ACT-APC-VOTE" | .parameter => "ACT-PARAM-VOTE" | .root => "ACT-ROOT-VOTE"
  | .apply => "ACT-APPLY-VOTE" | .view => "ACT-VIEW-VOTE" | .abort => "ACT-ABORT-VOTE"

def Action.arithmetic (action : Action) : Bool := action == .parameter || action == .apply

structure Envelope where
  action : Action
  actor : String
  round : String
  height : Nat
  epoch : String
  context : String
  parents : List ContentId
  body : ContentId
  deriving DecidableEq, Repr

def Envelope.key (e : Envelope) : Option Bytes := do
  let actor ← jsonASCII e.actor
  let context ← jsonASCII e.context
  some ([91] ++ actor ++ [44] ++ context ++ [93])

def Envelope.encode (e : Envelope) : Option Bytes := do
  let actor ← jsonASCII e.actor
  let round ← jsonASCII e.round
  let epoch ← jsonASCII e.epoch
  let context ← jsonASCII e.context
  if (∀ name ∈ [e.actor, e.round, e.epoch, e.context],
        0 < name.toList.length ∧ name.toList.length ≤ 256) ∧
      e.height ≤ 9223372036854775807 ∧ (∀ hash ∈ e.body :: e.parents, hash.length = 32) then
    some (asciiBytes "{\"action_id\":" ++ quotedBytes (asciiBytes e.action.tag) ++
      asciiBytes ",\"actor_id\":" ++ actor ++ asciiBytes ",\"body_hash\":" ++ quotedBytes (idBytes e.body) ++
      asciiBytes ",\"height\":" ++ asciiBytes (toString e.height) ++
      asciiBytes ",\"parent_hashes\":" ++ arrayBytes (e.parents.map (quotedBytes ∘ idBytes)) ++
      asciiBytes ",\"round_id\":" ++ round ++ asciiBytes ",\"validator_epoch\":" ++ epoch ++
      asciiBytes ",\"vote_context_id\":" ++ context ++ [125])
  else none

/-- None means the public contract does not project a native receipt for this
non-arithmetic vote. It must never be advertised as an empty persisted receipt. -/
structure Slot where
  envelope : Envelope
  sequence : Nat
  bytes : Bytes
  key : Bytes
  native : Option Record
  deriving DecidableEq, Repr

structure Journal where
  actor : String
  slots : List Slot
  current : Current
  deriving DecidableEq, Repr

/-- An admission-only view: preceding non-arithmetic slots contribute exactly
their context and count. Their unprojected native bytes are never returned. -/
def Slot.admissionRecord (slot : Slot) : Record :=
  match slot.native with
  | some record => record
  | none => ⟨⟨slot.key, [], [], []⟩, slot.sequence, [], []⟩

def Journal.admissionState (journal : Journal) : State :=
  ⟨journal.slots.map Slot.admissionRecord, journal.current⟩

def Journal.keys (journal : Journal) : List Bytes := journal.slots.map Slot.key

structure Environment (codec : Codec) (trust : Trust) (voteTrust : NativeVoteTrust) where
  native : NativeReplay.Environment codec trust voteTrust
  /-- Existing protocol admission for non-arithmetic votes, separately linked
  to phase/QC/context/role checks. This cannot admit PARAMETER or APPLY. -/
  otherAuthorized : Journal → Envelope → Bool
  /-- Actual cryptographic/exporter adapter remains an external obligation. -/
  sha256 : Bytes → ContentId

def envelopeId {codec trust voteTrust} (env : Environment codec trust voteTrust) (slot : Slot) : ContentId :=
  env.sha256 (artifactHashInput slot.bytes)

def journalPreimage {codec trust voteTrust} (env : Environment codec trust voteTrust) (slots : List Slot) : Bytes :=
  asciiBytes "deltareduce.vote-journal-projection.draft1" ++ [0] ++
    arrayBytes (slots.map (fun slot => quotedBytes (idBytes (envelopeId env slot))))

def journalRoot {codec trust voteTrust} (env : Environment codec trust voteTrust) (slots : List Slot) : ContentId :=
  env.sha256 (journalPreimage env slots)

def SlotCommon (journal : Journal) (slot : Slot) : Prop :=
  slot.envelope.actor = journal.actor ∧ slot.envelope.encode = some slot.bytes ∧
  slot.envelope.key = some slot.key ∧ slot.sequence = journal.slots.length + 1 ∧
  slot.sequence ≤ 9223372036854775807 ∧ slot.key ∉ journal.keys

instance (journal slot) : Decidable (SlotCommon journal slot) := by unfold SlotCommon; infer_instance

structure NativeSlot {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (journal : Journal) (slot : Slot) where
  record : Record
  projected : slot.native = some record
  resolved : NativeReplay.Resolved env.native record.data
  encoded : resolved.expected.envelope = slot.bytes
  key : record.data.context = slot.key
  sequence : record.sequence = slot.sequence
  admitted : validVote (NativeReplay.adapter env.native) journal.admissionState record

def checkNativeSlot {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (journal : Journal) (slot : Slot) : Option (NativeSlot env journal slot) := do
  match projected : slot.native with
  | none => none
  | some record =>
      let resolved ← NativeReplay.resolve env.native record.data
      if checked : resolved.expected.envelope = slot.bytes ∧ record.data.context = slot.key ∧
          record.sequence = slot.sequence ∧ validVote (NativeReplay.adapter env.native) journal.admissionState record then
        some ⟨record, projected, resolved, checked.1, checked.2.1, checked.2.2.1, checked.2.2.2⟩
      else none

inductive KindChecked {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (journal : Journal) (slot : Slot) : Prop where
  | arithmetic (kind : slot.envelope.action.arithmetic = true) (native : NativeSlot env journal slot) :
      KindChecked env journal slot
  | other (kind : slot.envelope.action.arithmetic = false) (unprojected : slot.native = none)
      (authorized : env.otherAuthorized journal slot.envelope = true) : KindChecked env journal slot

structure CheckedSlot {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (journal : Journal) (slot : Slot) : Type where
  common : SlotCommon journal slot
  kind : KindChecked env journal slot

def checkSlot {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (journal : Journal) (slot : Slot) : Option (CheckedSlot env journal slot) :=
  if common : SlotCommon journal slot then
    if kind : slot.envelope.action.arithmetic = true then
      match checkNativeSlot env journal slot with
      | none => none
      | some native => some ⟨common, .arithmetic kind native⟩
    else
      if checked : slot.native = none ∧ env.otherAuthorized journal slot.envelope = true then
        some ⟨common, .other (Bool.eq_false_iff.mpr kind) checked.1 checked.2⟩
      else none
  else none

def appendSlot {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (journal : Journal) (slot : Slot) : Option Journal := do
  let _ ← checkSlot env journal slot
  some { journal with slots := journal.slots ++ [slot] }

inductive Event where
  | vote (slot : Slot) | advance (certificate : Certificate)
  deriving DecidableEq, Repr

def step {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (journal : Journal) : Event → Option Journal
  | .vote slot => appendSlot env journal slot
  | .advance c => do
      let state ← RecoveryKernel.step (NativeReplay.adapter env.native) journal.admissionState (.advance c)
      some { journal with current := state.current }

def replay {codec trust voteTrust} (env : Environment codec trust voteTrust) (journal : Journal) :
    List Event → Option Journal
  | [] => some journal
  | event :: rest => do
      let next ← step env journal event
      replay env next rest

def voteSlots : List Event → List Slot
  | [] => []
  | .vote slot :: rest => slot :: voteSlots rest
  | .advance _ :: rest => voteSlots rest

theorem checkedNativeHasPreparation {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot} (checked : CheckedSlot env journal slot) (kind : slot.envelope.action.arithmetic = true) :
    ∃ native : NativeSlot env journal slot,
      ∃ resolved : NativeReplay.Resolved env.native native.record.data,
        ∃ prepared : NativePrepared resolved.binding voteTrust resolved.input.metadata .ready
          journal.admissionState native.record.data.command,
          native.record = prepared.record := by
  cases checked.kind with
  | arithmetic _ native =>
      obtain ⟨resolved, _, prepared, same⟩ := NativeReplay.acceptedVoteHasPreparation native.admitted
      exact ⟨native, resolved, prepared, same⟩
  | other other _ _ => rw [kind] at other; contradiction

theorem otherHasNoInventedReceipt {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot} (checked : CheckedSlot env journal slot) (kind : slot.envelope.action.arithmetic = false) :
    slot.native = none := by
  cases checked.kind with
  | arithmetic other _ => rw [kind] at other; contradiction
  | other _ unprojected _ => exact unprojected

theorem checkedAdmissionKeyExact {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot} (checked : CheckedSlot env journal slot) : slot.admissionRecord.data.context = slot.key := by
  cases checked.kind with
  | arithmetic _ native => simpa [Slot.admissionRecord, native.projected] using native.key
  | other _ unprojected _ => simp [Slot.admissionRecord, unprojected]

theorem nativeSequenceCountsAllSlots {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot} (checked : CheckedSlot env journal slot) (native : NativeSlot env journal slot) :
    native.record.sequence = journal.slots.length + 1 := by
  exact native.sequence.trans checked.common.2.2.2.1

theorem appendSlotSound {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot final} (accepted : appendSlot env journal slot = some final) :
    ∃ _ : CheckedSlot env journal slot, final = { journal with slots := journal.slots ++ [slot] } := by
  cases checked : checkSlot env journal slot with
  | none => simp [appendSlot, checked] at accepted
  | some evidence => exact ⟨evidence, (Option.some.inj (by simpa [appendSlot, checked] using accepted)).symm⟩

theorem duplicateContextRejected {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot} (duplicate : slot.key ∈ journal.keys) : appendSlot env journal slot = none := by
  simp [appendSlot, checkSlot, SlotCommon, duplicate]

theorem wrongSequenceRejected {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot} (wrong : slot.sequence ≠ journal.slots.length + 1) : appendSlot env journal slot = none := by
  simp [appendSlot, checkSlot, SlotCommon, wrong]

inductive Transition {codec trust voteTrust} (env : Environment codec trust voteTrust) :
    Journal → Event → Journal → Prop where
  | vote {s slot} (checked : CheckedSlot env s slot) :
      Transition env s (.vote slot) { s with slots := s.slots ++ [slot] }
  | advance {s c final} (accepted : RecoveryKernel.step (NativeReplay.adapter env.native)
      s.admissionState (.advance c) = some final) :
      Transition env s (.advance c) { s with current := final.current }

inductive History {codec trust voteTrust} (env : Environment codec trust voteTrust) :
    Journal → List Event → Journal → Prop where
  | nil (s) : History env s [] s
  | cons {s e mid rest final} (transition : Transition env s e mid) (tail : History env mid rest final) :
      History env s (e :: rest) final

theorem stepSound {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal event final} (accepted : step env journal event = some final) : Transition env journal event final := by
  cases event with
  | vote slot =>
      obtain ⟨checked, same⟩ := appendSlotSound accepted
      subst final; exact .vote checked
  | advance c =>
      cases changed : RecoveryKernel.step (NativeReplay.adapter env.native) journal.admissionState (.advance c) with
      | none => simp [step, changed] at accepted
      | some state =>
          have same := Option.some.inj (by simpa [step, changed] using accepted)
          cases same
          exact .advance changed

theorem replaySound {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal events final} (accepted : replay env journal events = some final) : History env journal events final := by
  induction events generalizing journal with
  | nil => cases Option.some.inj accepted; exact .nil _
  | cons event rest ih =>
      cases next : step env journal event with
      | none => simp [replay, next] at accepted
      | some mid => exact .cons (stepSound next) (ih (by simpa [replay, next] using accepted))

theorem replayExactSlots {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal events final} (accepted : replay env journal events = some final) :
    final.slots = journal.slots ++ voteSlots events := by
  have history := replaySound accepted
  clear accepted
  induction history with
  | nil => simp [voteSlots]
  | cons transition _ ih => cases transition <;> simpa [voteSlots, List.append_assoc] using ih

theorem replayAdmissionKeysExact {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal events final} (accepted : replay env journal events = some final)
    (prior : ∀ slot ∈ journal.slots, slot.admissionRecord.data.context = slot.key) :
    ∀ slot ∈ final.slots, slot.admissionRecord.data.context = slot.key := by
  have history := replaySound accepted
  clear accepted
  induction history with
  | nil => exact prior
  | cons transition _ ih =>
      apply ih
      cases transition with
      | vote checked =>
          intro slot member
          rcases List.mem_append.mp member with old | new
          · exact prior slot old
          · have same : slot = _ := List.mem_singleton.mp new
            subst slot
            exact checkedAdmissionKeyExact checked
      | advance _ => exact prior

theorem replayComputedRoot {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal events final} (accepted : replay env journal events = some final) :
    journalRoot env final.slots = journalRoot env (journal.slots ++ voteSlots events) := by
  rw [replayExactSlots accepted]

theorem replayPreservesProjectedRecord {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal events final slot} (accepted : replay env journal events = some final) (saved : slot ∈ journal.slots) :
    slot ∈ final.slots := by rw [replayExactSlots accepted]; exact List.mem_append_left _ saved

structure Tip where
  sequence : Option Nat
  root : Option ContentId
  deriving DecidableEq, Repr

def knownTip {codec trust voteTrust} (env : Environment codec trust voteTrust) (slots : List Slot) : Tip :=
  ⟨some slots.length, some (journalRoot env slots)⟩

structure AppendObservation where
  before : Tip
  after : Tip
  exposed : Bool
  receipt : Option Bytes
  effect : Option Bytes
  deriving DecidableEq, Repr

/-- Roots and sequences are recomputed from the whole accepted prefix. Unknown
tips cannot be treated as a known successful append or as verified absence. -/
def observationMatches {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (before after : Journal) (slot : Slot) (observation : AppendObservation) : Prop :=
  observation.before = knownTip env before.slots ∧ observation.after = knownTip env after.slots ∧
  match slot.native with
  | none => observation.receipt = none ∧ observation.effect = none
  | some record =>
      if observation.exposed then observation.receipt = some record.receipt ∧ observation.effect = some record.effect
      else observation.receipt = none ∧ observation.effect = none

instance {codec trust voteTrust} (env : Environment codec trust voteTrust) (before after slot observation) :
    Decidable (observationMatches env before after slot observation) := by
  unfold observationMatches
  cases slot.native <;> infer_instance

def observedAppend {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (journal : Journal) (slot : Slot) (observation : AppendObservation) : Option Journal := do
  let next ← appendSlot env journal slot
  if observationMatches env journal next slot observation then some next else none

theorem observedAppendExact {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot observation final} (accepted : observedAppend env journal slot observation = some final) :
    (∃ _ : CheckedSlot env journal slot, final = { journal with slots := journal.slots ++ [slot] }) ∧
    observation.before = knownTip env journal.slots ∧ observation.after = knownTip env final.slots := by
  cases appended : appendSlot env journal slot with
  | none => simp [observedAppend, appended] at accepted
  | some next =>
      simp only [observedAppend, appended] at accepted
      change (if observationMatches env journal next slot observation then some next else none) = some final at accepted
      split at accepted
      · cases Option.some.inj accepted
        have checked := appendSlotSound appended
        exact ⟨checked, ‹observationMatches _ _ _ _ _›.1, ‹observationMatches _ _ _ _ _›.2.1⟩
      · contradiction

theorem unknownTipCannotClaimAppend {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot observation} (unknown : observation.after.sequence = none) :
    observedAppend env journal slot observation = none := by
  cases result : observedAppend env journal slot observation with
  | none => rfl
  | some final =>
      have bound := (observedAppendExact result).2.2
      have sequence := congrArg Tip.sequence bound
      simp [knownTip, unknown] at sequence

theorem changedObservationRootRejected {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {journal slot observation}
    (different : observation.before.root ≠ some (journalRoot env journal.slots)) :
    observedAppend env journal slot observation = none := by
  cases result : observedAppend env journal slot observation with
  | none => rfl
  | some final =>
      have bound := congrArg Tip.root (observedAppendExact result).2.1
      exact False.elim (different bound)

end DeltaReduce.PublicJournal
