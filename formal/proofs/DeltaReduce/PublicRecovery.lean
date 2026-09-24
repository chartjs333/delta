import DeltaReduce.PublicJournal

/-! Checked public persistence observations and recovery over the all-vote
journal. Scan authentication, other-action admission, full public state roots
and production byte/exporter refinement remain external obligations. -/
namespace DeltaReduce.PublicRecovery
open NativeBinding PublicJournal
abbrev Bytes := NativeBinding.Bytes

inductive Mode where
  | ready | mustCrash | crashed | recovering | blocked
  deriving DecidableEq, Repr

inductive Cut where
  | exposed | unexposed | unknown
  deriving DecidableEq, Repr

/-- Exact diagnostic stage vocabulary/order, not a caller-supplied exposure flag. -/
def classify : List String → Option Cut
  | ["VALIDATED", "APPENDED", "DURABLE", "COMMITTED", "EXPOSED"] => some .exposed
  | ["VALIDATED", "APPENDED", "DURABLE"] => some .unexposed
  | ["VALIDATED", "APPENDED", "DURABLE", "COMMITTED"] => some .unexposed
  | ["VALIDATED", "APPENDED", "SURVIVED_UNACKNOWLEDGED"] => some .unexposed
  | ["VALIDATED", "APPENDED", "BARRIER_FAILED", "SURVIVED_UNACKNOWLEDGED"] => some .unexposed
  | ["VALIDATED", "APPENDED", "UNKNOWN"] => some .unknown
  | ["VALIDATED", "APPENDED", "BARRIER_FAILED", "UNKNOWN"] => some .unknown
  | _ => none

structure Observation where
  before : Tip
  after : Tip
  receipt : Option Bytes
  effect : Option Bytes
  deriving DecidableEq, Repr

structure Machine where
  initial : Journal
  log : List PublicJournal.Event
  journal : Journal
  mode : Mode
  pending : Option Slot
  sent : List Slot
  deriving DecidableEq, Repr

def initial (actor : String) (current : RecoveryKernel.Current) : Machine :=
  let journal : Journal := ⟨actor, [], current⟩
  ⟨journal, [], journal, .ready, none, []⟩

def remember (sent : List Slot) (slot : Slot) : List Slot :=
  if slot ∈ sent then sent else sent ++ [slot]

def enabled (m : Machine) : Prop := m.mode = .ready ∧ m.pending = none
instance (m) : Decidable (enabled m) := by unfold enabled; infer_instance

def tip {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (m : Machine) : Tip :=
  if m.pending = none ∧ m.mode ≠ .blocked then knownTip env m.journal.slots else ⟨none, none⟩

def persist {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (m : Machine) (slot : Slot) (stages : List String) (o : Observation) : Option Machine := do
  if enabled m ∧ slot.envelope.action.arithmetic = true then
    let _ ← checkSlot env m.journal slot
    let cut ← classify stages
    match cut with
    | .unknown =>
        if o.before = knownTip env m.journal.slots ∧ o.after = ⟨none, none⟩ ∧
            o.receipt = none ∧ o.effect = none then
          some { m with mode := .mustCrash, pending := some slot }
        else none
    | .exposed | .unexposed => do
        let exposed := cut == .exposed
        let next ← observedAppend env m.journal slot ⟨o.before, o.after, exposed, o.receipt, o.effect⟩
        some { m with
          journal := next, log := m.log ++ [.vote slot],
          mode := (if exposed then .ready else .mustCrash),
          sent := (if exposed then remember m.sent slot else m.sent) }
  else none

def otherVote {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (m : Machine) (slot : Slot) : Option Machine := do
  if enabled m ∧ slot.envelope.action.arithmetic = false then
    let next ← appendSlot env m.journal slot
    some { m with journal := next, log := m.log ++ [.vote slot] }
  else none

def advance {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (m : Machine) (certificate : RecoveryKernel.Certificate) : Option Machine := do
  if enabled m then
    let next ← PublicJournal.step env m.journal (.advance certificate)
    some { m with journal := next, log := m.log ++ [.advance certificate] }
  else none

def crash (m : Machine) : Option Machine :=
  if m.mode ≠ .blocked then some { m with mode := .crashed } else none

def restart (m : Machine) : Option Machine :=
  if m.mode = .crashed then some { m with mode := .recovering } else none

inductive RetryResult where
  | retry (original : Slot) | conflict | missing | unavailable
  deriving DecidableEq, Repr

def lookup (slots : List Slot) (key : Bytes) : Option Slot :=
  match slots with
  | [] => none
  | slot :: rest => if slot.key = key then some slot else lookup rest key

/-- Exact historical retry does not recompute the old parent using new current. -/
def retry (m : Machine) (key command : Bytes) : RetryResult :=
  if enabled m then
    match lookup m.journal.slots key with
    | none => .missing
    | some slot =>
      match slot.native with
      | none => .unavailable
      | some record => if record.data.command = command then .retry slot else .conflict
  else .unavailable

def exposeRetry (m : Machine) (key command : Bytes) : Option (Machine × RecoveryKernel.Record) := do
  match retry m key command with
  | .retry slot =>
      let record ← slot.native
      some ({ m with sent := remember m.sent slot }, record)
  | _ => none

inductive Scan where
  | complete (events : List PublicJournal.Event)
  | verifiedAbsent (events : List PublicJournal.Event)
  | incomplete | corrupt | ambiguous
  deriving DecidableEq, Repr

structure Environment (codec : Codec) (trust : Trust) (voteTrust : NativeVoteTrust) where
  journal : PublicJournal.Environment codec trust voteTrust
  /-- Authentication binds the original initial state, exact previous log,
  pending slot and complete scan. It does not assume recovered state equality. -/
  scanAuthenticated : Journal → List PublicJournal.Event → Option Slot → Scan → Bool

def recoveryLog (m : Machine) : Scan → Option (List PublicJournal.Event)
  | .complete events =>
      let expected := match m.pending with
        | none => m.log
        | some slot => m.log ++ [.vote slot]
      if events = expected then some events else none
  | .verifiedAbsent events =>
      if m.pending.isSome ∧ events = m.log then some events else none
  | _ => none

/-- Both public roots are recomputed. No response bytes are produced by recovery. -/
def restore {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (m : Machine) (events : List PublicJournal.Event) (o : Observation) : Option Machine := do
  let recovered ← PublicJournal.replay env.journal m.initial events
  if o.before = knownTip env.journal m.journal.slots ∧
      o.after = knownTip env.journal recovered.slots ∧ o.receipt = none ∧ o.effect = none then
    some { m with journal := recovered, log := events, mode := .ready, pending := none }
  else none

def recover {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (m : Machine) (scan : Scan) (o : Observation) : Option Machine := do
  if m.mode = .recovering then
    if env.scanAuthenticated m.initial m.log m.pending scan then
      match scan with
      | .complete _ | .verifiedAbsent _ => do
          let events ← recoveryLog m scan
          restore env m events o
      | .incomplete | .corrupt | .ambiguous =>
          if o.before = knownTip env.journal m.journal.slots ∧ o.after = ⟨none, none⟩ ∧
              o.receipt = none ∧ o.effect = none then
            some { m with mode := if scan = .incomplete then .recovering else .blocked }
          else none
    else none
  else none

theorem unreadyCannotPersist {codec trust voteTrust}
    (env : PublicJournal.Environment codec trust voteTrust) (m slot stages o)
    (notReady : m.mode ≠ .ready) : persist env m slot stages o = none := by
  simp [persist, enabled, notReady]

theorem unknownPersistPreservesKnownPrefix {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {m slot stages o final}
    (cut : classify stages = some .unknown) (accepted : persist env m slot stages o = some final) :
    final.journal = m.journal ∧ final.log = m.log ∧ final.sent = m.sent ∧
    final.pending = some slot ∧ final.mode = .mustCrash ∧ o.after = ⟨none, none⟩ ∧
    o.receipt = none ∧ o.effect = none := by
  simp only [persist] at accepted
  split at accepted
  · cases checked : checkSlot env m.journal slot with
    | none => simp [checked] at accepted
    | some evidence =>
        simp only [checked, cut] at accepted
        split at accepted
        · cases Option.some.inj accepted
          exact ⟨rfl, rfl, rfl, rfl, rfl, ‹_ ∧ _ ∧ _ ∧ _›.2⟩
        · contradiction
  · contradiction

theorem unknownHasNoKnownTip {codec trust voteTrust}
    (env : PublicJournal.Environment codec trust voteTrust) (m : Machine) (slot : Slot) :
    tip env { m with pending := some slot } = ⟨none, none⟩ := by simp [tip]

theorem unreadyCannotRetry (m key command) (notReady : m.mode ≠ .ready) :
    retry m key command = .unavailable := by simp [retry, enabled, notReady]

theorem historicalRetryExact {m key slot record}
    (ready : enabled m) (found : lookup m.journal.slots key = some slot)
    (saved : slot.native = some record) :
    exposeRetry m key record.data.command = some ({ m with sent := remember m.sent slot }, record) := by
  simp [exposeRetry, retry, ready, found, saved]

theorem conflictingRetryNoOutput {m key slot record command}
    (ready : enabled m) (found : lookup m.journal.slots key = some slot)
    (saved : slot.native = some record) (different : record.data.command ≠ command) :
    retry m key command = .conflict ∧ exposeRetry m key command = none := by
  simp [exposeRetry, retry, ready, found, saved, different]

theorem retryPreservesJournal {m key command final record}
    (accepted : exposeRetry m key command = some (final, record)) :
    final.journal = m.journal ∧ final.log = m.log ∧ final.pending = m.pending := by
  cases result : retry m key command <;> simp [exposeRetry, result] at accepted
  case retry slot =>
    cases saved : slot.native with
    | none => simp [saved] at accepted
    | some original =>
        simp only [saved, Option.bind_some, Option.some.injEq, Prod.mk.injEq] at accepted
        cases accepted.1
        exact ⟨rfl, rfl, rfl⟩

theorem restartRequiresCrash {m final} (accepted : restart m = some final) :
    m.mode = .crashed ∧ final.mode = .recovering ∧ final.pending = m.pending ∧ final.log = m.log := by
  simp only [restart] at accepted
  split at accepted
  · cases Option.some.inj accepted; exact ⟨‹_›, rfl, rfl, rfl⟩
  · contradiction

theorem blockedCannotRestart (m : Machine) : restart { m with mode := .blocked } = none := by simp [restart]

theorem blockedCannotRecover {codec trust voteTrust} (env : Environment codec trust voteTrust) (m : Machine) (scan o) :
    recover env { m with mode := .blocked } scan o = none := by simp [recover]

theorem ordinaryPrefixCannotResolveUnknown (m : Machine) (slot : Slot) :
    recoveryLog { m with pending := some slot } (.complete m.log) = none := by
  have different : m.log ≠ m.log ++ [PublicJournal.Event.vote slot] := by
    intro same
    have lengths := congrArg List.length same
    simp at lengths
  simp [recoveryLog, different]

theorem absenceRequiresExactPrior {m events selected}
    (accepted : recoveryLog m (.verifiedAbsent events) = some selected) :
    m.pending.isSome = true ∧ events = m.log ∧ selected = m.log := by
  simp only [recoveryLog] at accepted
  split at accepted
  · exact ⟨‹_ ∧ _›.1, ‹_ ∧ _›.2, (Option.some.inj accepted).symm.trans ‹_ ∧ _›.2⟩
  · contradiction

theorem restoreDerivesHistory {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {m events o final} (accepted : restore env m events o = some final) :
    PublicJournal.replay env.journal m.initial events = some final.journal ∧
    PublicJournal.History env.journal m.initial events final.journal ∧
    final.journal.slots = m.initial.slots ++ voteSlots events ∧
    final.log = events ∧ final.mode = .ready ∧ final.pending = none ∧ final.sent = m.sent ∧
    o.before = knownTip env.journal m.journal.slots ∧
    o.after = knownTip env.journal final.journal.slots ∧ o.receipt = none ∧ o.effect = none := by
  cases replayed : PublicJournal.replay env.journal m.initial events with
  | none => simp [restore, replayed] at accepted
  | some recovered =>
      simp only [restore, replayed] at accepted
      change (if o.before = knownTip env.journal m.journal.slots ∧
          o.after = knownTip env.journal recovered.slots ∧ o.receipt = none ∧ o.effect = none then
        some { m with journal := recovered, log := events, mode := .ready, pending := none }
        else none) = some final at accepted
      split at accepted
      · cases Option.some.inj accepted
        exact ⟨rfl, PublicJournal.replaySound replayed, PublicJournal.replayExactSlots replayed,
          rfl, rfl, rfl, rfl, ‹_ ∧ _ ∧ _ ∧ _›⟩
      · contradiction

theorem restoreRequiresExactRoot {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {m events o} (wrong : o.before ≠ knownTip env.journal m.journal.slots) :
    restore env m events o = none := by
  cases replayed : PublicJournal.replay env.journal m.initial events <;> simp [restore, replayed, wrong]

theorem restoreCannotExpose {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {m events o final} (accepted : restore env m events o = some final) :
    final.sent = m.sent ∧ o.receipt = none ∧ o.effect = none := by
  have sound := restoreDerivesHistory accepted
  exact ⟨sound.2.2.2.2.2.2.1, sound.2.2.2.2.2.2.2.2.2⟩

theorem failedAdmissionCannotPersist {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {m slot stages o}
    (rejected : checkSlot env m.journal slot = none) : persist env m slot stages o = none := by
  simp [persist, rejected]

theorem unexposedPersistRequiresCrash {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {m slot stages o final}
    (cut : classify stages = some .unexposed) (accepted : persist env m slot stages o = some final) :
    final.mode = .mustCrash ∧ final.sent = m.sent ∧ final.log = m.log ++ [.vote slot] ∧
    final.journal.slots = m.journal.slots ++ [slot] ∧
    Nonempty (CheckedSlot env m.journal slot) ∧
    o.receipt = none ∧ o.effect = none := by
  simp only [persist] at accepted
  split at accepted
  · cases checked : checkSlot env m.journal slot with
    | none => simp [checked] at accepted
    | some evidence =>
        simp only [checked, cut] at accepted
        change (do
          let next ← observedAppend env m.journal slot ⟨o.before, o.after, false, o.receipt, o.effect⟩
          some { m with journal := next, log := m.log ++ [.vote slot], mode := .mustCrash }) = some final at accepted
        cases appended : observedAppend env m.journal slot ⟨o.before, o.after, false, o.receipt, o.effect⟩ with
        | none => simp [appended] at accepted
        | some next =>
            have same : { m with journal := next, log := m.log ++ [.vote slot], mode := .mustCrash } = final :=
              Option.some.inj (by simpa [appended] using accepted)
            subst final
            have exactNext := (observedAppendExact appended).1.choose_spec
            have noOutput : o.receipt = none ∧ o.effect = none := by
              unfold observedAppend at appended
              cases a : appendSlot env m.journal slot with
              | none => simp [a] at appended
              | some j =>
                  simp only [a] at appended
                  change (if observationMatches env m.journal j slot
                    ⟨o.before, o.after, false, o.receipt, o.effect⟩ then some j else none) = some next at appended
                  split at appended
                  · have outputs := ‹observationMatches _ _ _ _ _›.2.2
                    cases saved : slot.native <;> simpa [saved] using outputs
                  · contradiction
            exact ⟨rfl, rfl, rfl, congrArg Journal.slots exactNext, ⟨evidence⟩, noOutput⟩
  · contradiction

theorem exposedPersistHasExactObservation {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {m slot stages o final}
    (cut : classify stages = some .exposed) (accepted : persist env m slot stages o = some final) :
    final.mode = .ready ∧ final.sent = remember m.sent slot ∧
    final.log = m.log ++ [.vote slot] ∧
    observedAppend env m.journal slot ⟨o.before, o.after, true, o.receipt, o.effect⟩ = some final.journal := by
  simp only [persist] at accepted
  split at accepted
  · cases checked : checkSlot env m.journal slot with
    | none => simp [checked] at accepted
    | some evidence =>
        simp only [checked, cut] at accepted
        change (do
          let next ← observedAppend env m.journal slot ⟨o.before, o.after, true, o.receipt, o.effect⟩
          some { m with
            journal := next, log := m.log ++ [.vote slot], mode := .ready,
            sent := remember m.sent slot }) = some final at accepted
        cases appended : observedAppend env m.journal slot ⟨o.before, o.after, true, o.receipt, o.effect⟩ with
        | none => simp [appended] at accepted
        | some next =>
            have same : { m with
              journal := next, log := m.log ++ [.vote slot], mode := .ready,
              sent := remember m.sent slot } = final := Option.some.inj (by simpa [appended] using accepted)
            subst final
            exact ⟨rfl, rfl, rfl, rfl⟩
  · contradiction

theorem readyRecoveryDerivesAllVoteHistory {codec trust voteTrust}
    {env : Environment codec trust voteTrust} {m scan o final}
    (accepted : recover env m scan o = some final) (ready : final.mode = .ready) :
    m.mode = .recovering ∧ env.scanAuthenticated m.initial m.log m.pending scan = true ∧
    ∃ events, recoveryLog m scan = some events ∧
      PublicJournal.replay env.journal m.initial events = some final.journal ∧
      PublicJournal.History env.journal m.initial events final.journal ∧
      final.journal.slots = m.initial.slots ++ voteSlots events ∧
      final.log = events ∧ final.pending = none ∧ final.sent = m.sent ∧
      o.after = knownTip env.journal final.journal.slots ∧ o.receipt = none ∧ o.effect = none := by
  simp only [recover] at accepted
  split at accepted
  · rename_i recovering
    split at accepted
    · rename_i authenticated
      refine ⟨recovering, authenticated, ?_⟩
      cases scan with
      | complete events | verifiedAbsent events =>
          cases selected : recoveryLog m _ with
          | none => simp [selected] at accepted
          | some es =>
              have restored : restore env m es o = some final := by simpa [selected] using accepted
              have sound := restoreDerivesHistory restored
              exact ⟨es, rfl, sound.1, sound.2.1, sound.2.2.1, sound.2.2.2.1,
                sound.2.2.2.2.2.1, sound.2.2.2.2.2.2.1, sound.2.2.2.2.2.2.2.2⟩
      | incomplete | corrupt | ambiguous =>
          dsimp only at accepted
          split at accepted
          · cases Option.some.inj accepted
            simp at ready
          · contradiction
    · contradiction
  · contradiction

theorem exposedStagesRequireBarrierAndCommit {stages}
    (classified : classify stages = some .exposed) :
    stages = ["VALIDATED", "APPENDED", "DURABLE", "COMMITTED", "EXPOSED"] := by
  unfold classify at classified
  split at classified <;> simp_all

end DeltaReduce.PublicRecovery
