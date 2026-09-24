import Std

/-!
Checked sequential journal replay for the pending arithmetic-binding amendment.
This is a mathematical sublayer, not nativeArithmeticRecoveryRefines. Admission,
diagnostic encoders and certificate authentication are explicit adapter inputs;
their connection to NativeBinding and the public exporter is still required.
No physical byte scan, fsync, arbitrary initial snapshot or repair is modeled.
-/
namespace DeltaReduce.RecoveryKernel

abbrev Bytes := List UInt8

structure Current where
  checkpoint : Bytes
  model : Bytes
  optimizer : Bytes
  deriving DecidableEq, Repr

/-- Context includes the actor and the entire formal uniqueness context. The
adapter must bind action, parents, authority and canonical command/body bytes. -/
structure VoteData where
  context : Bytes
  command : Bytes
  authority : Bytes
  body : Bytes
  deriving DecidableEq, Repr

structure Record where
  data : VoteData
  sequence : Nat
  receipt : Bytes
  effect : Bytes
  deriving DecidableEq, Repr

structure Certificate where
  parent : Current
  next : Current
  bytes : Bytes
  deriving DecidableEq, Repr

inductive Entry where
  | vote (record : Record)
  | advance (certificate : Certificate)
  deriving DecidableEq, Repr

structure State where
  votes : List Record
  current : Current
  deriving DecidableEq, Repr

/-- Decoded diagnostic claims. Their authentication/complete physical coverage
is a separate adapter premise, not a property established by these constructors. -/
inductive Scan where
  | complete (journal : List Entry)
  | verifiedAbsent (journal : List Entry)
  | incomplete | corrupt | ambiguous
  deriving DecidableEq, Repr

structure Adapter where
  admitted : Current → VoteData → Bool
  effect : VoteData → Option Bytes
  receipt : VoteData → Nat → Bytes → Option Bytes
  authenticated : Certificate → Bool
  scanAuthenticated : State → List Entry → Record → Scan → Bool

def lookup (records : List Record) (context : Bytes) : Option Record :=
  match records with
  | [] => none
  | r :: rest => if r.data.context = context then some r else lookup rest context

def initial (current : Current) : State := ⟨[], current⟩

def validVote (adapter : Adapter) (state : State) (record : Record) : Prop :=
  adapter.admitted state.current record.data = true ∧
  record.sequence = state.votes.length + 1 ∧
  lookup state.votes record.data.context = none ∧
  adapter.effect record.data = some record.effect ∧
  adapter.receipt record.data record.sequence record.effect = some record.receipt

instance (a : Adapter) (s : State) (r : Record) : Decidable (validVote a s r) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ _ ∧ _))

/-- A vote cannot advance any current pointer. Only an authenticated ApplyQC
entry can perform the parent-to-next compare-and-set, or exact idempotent replay. -/
def step (adapter : Adapter) (state : State) : Entry → Option State
  | .vote record =>
      if validVote adapter state record then
        some ⟨state.votes ++ [record], state.current⟩ else none
  | .advance certificate =>
      if adapter.authenticated certificate then
        if state.current = certificate.next then some state
        else if state.current = certificate.parent then
          some ⟨state.votes, certificate.next⟩ else none
      else none

def replay (adapter : Adapter) (state : State) : List Entry → Option State
  | [] => some state
  | entry :: rest => do
      let next ← step adapter state entry
      replay adapter next rest

def voteRecords : List Entry → List Record
  | [] => []
  | .vote record :: rest => record :: voteRecords rest
  | .advance _ :: rest => voteRecords rest

/-- Independent relational specification of each accepted operation. -/
inductive Transition (adapter : Adapter) : State → Entry → State → Prop where
  | vote {s r} (accepted : validVote adapter s r) :
      Transition adapter s (.vote r) ⟨s.votes ++ [r], s.current⟩
  | advance {s c} (authenticated : adapter.authenticated c = true)
      (fresh : s.current ≠ c.next) (parent : s.current = c.parent) :
      Transition adapter s (.advance c) ⟨s.votes, c.next⟩
  | already {s c} (authenticated : adapter.authenticated c = true)
      (same : s.current = c.next) : Transition adapter s (.advance c) s

inductive History (adapter : Adapter) : State → List Entry → State → Prop where
  | nil (s) : History adapter s [] s
  | cons {s e mid rest final} (transition : Transition adapter s e mid)
      (tail : History adapter mid rest final) : History adapter s (e :: rest) final

theorem stepSound {a s e final} (accepted : step a s e = some final) :
    Transition a s e final := by
  cases e with
  | vote r =>
      simp only [step] at accepted
      split at accepted
      · cases Option.some.inj accepted
        exact .vote ‹_›
      · contradiction
  | advance c =>
      simp only [step] at accepted
      split at accepted
      · split at accepted
        · cases Option.some.inj accepted
          exact .already ‹_› ‹_›
        · split at accepted
          · cases Option.some.inj accepted
            exact .advance ‹_› ‹_› ‹_›
          · contradiction
      · contradiction

theorem stepComplete {a s e final} (transition : Transition a s e final) :
    step a s e = some final := by
  cases transition with
  | vote accepted => simp [step, accepted]
  | advance authenticated fresh parent =>
      simp only [step, authenticated, ↓reduceIte]
      rw [if_neg fresh, if_pos parent]
  | already authenticated same => simp [step, authenticated, same]

theorem replaySound {a s entries final} (accepted : replay a s entries = some final) :
    History a s entries final := by
  induction entries generalizing s with
  | nil => cases Option.some.inj accepted; exact .nil _
  | cons e rest ih =>
      simp only [replay] at accepted
      cases next : step a s e with
      | none => simp [next] at accepted
      | some mid =>
          simp only [next] at accepted
          exact .cons (stepSound next) (ih accepted)

theorem replayComplete {a s entries final} (history : History a s entries final) :
    replay a s entries = some final := by
  induction history with
  | nil => rfl
  | cons transition _ ih => simp [replay, stepComplete transition, ih]

theorem replayAppend (a : Adapter) (s : State) (prior suffix : List Entry) :
    replay a s (prior ++ suffix) = (replay a s prior).bind (fun mid => replay a mid suffix) := by
  induction prior generalizing s with
  | nil => rfl
  | cons e rest ih =>
      simp only [List.cons_append, replay]
      cases next : step a s e <;> simp [ih]

theorem historyExactRecords {a s entries final} (history : History a s entries final) :
    final.votes = s.votes ++ voteRecords entries := by
  induction history with
  | nil => simp [voteRecords]
  | cons transition _ ih =>
      cases transition <;> simpa [voteRecords, List.append_assoc] using ih

theorem replayExactRecords {a s entries final} (accepted : replay a s entries = some final) :
    final.votes = s.votes ++ voteRecords entries := historyExactRecords (replaySound accepted)

theorem lookupAppendPreserves {records context record} (found : lookup records context = some record)
    (suffix : List Record) : lookup (records ++ suffix) context = some record := by
  induction records with
  | nil => contradiction
  | cons first rest ih =>
      simp only [lookup] at found
      simp only [List.cons_append, lookup]
      split at found
      · simp_all
      · simp_all

theorem lookupFreshAppend {records context} (absent : lookup records context = none)
    (record : Record) (same : record.data.context = context) :
    lookup (records ++ [record]) context = some record := by
  induction records with
  | nil => simp [lookup, same]
  | cons first rest ih =>
      simp only [lookup] at absent
      split at absent
      · contradiction
      · simp_all [lookup]

theorem replayPreservesRecord {a s entries final context record}
    (accepted : replay a s entries = some final) (found : lookup s.votes context = some record) :
    lookup final.votes context = some record := by
  rw [replayExactRecords accepted]
  exact lookupAppendPreserves found _

theorem replayDuplicateRejected {a s record} (existing : lookup s.votes record.data.context ≠ none) :
    step a s (.vote record) = none := by
  simp [step, validVote, existing]

theorem voteDoesNotAdvance {a s r final} (accepted : step a s (.vote r) = some final) :
    final.current = s.current := by
  have transition := stepSound accepted
  cases transition
  rfl

theorem advanceRequiresCertificate {a s certificate final}
    (accepted : step a s (.advance certificate) = some final) :
    a.authenticated certificate = true ∧ final.votes = s.votes ∧
    (final = s ∨ (s.current = certificate.parent ∧ final.current = certificate.next)) := by
  have transition := stepSound accepted
  cases transition with
  | advance authenticated _ parent => exact ⟨authenticated, rfl, .inr ⟨parent, rfl⟩⟩
  | already authenticated _ => exact ⟨authenticated, rfl, .inl rfl⟩

inductive Mode where
  | ready | crashed | recovering | unknown | blocked
  deriving DecidableEq, Repr

inductive LookupResult where
  | missing | retry (original : Record) | conflict | unavailable
  deriving DecidableEq, Repr

/-- This path never revalidates an old parent against the newer current state. -/
def retry (mode : Mode) (state : State) (context command : Bytes) : LookupResult :=
  if mode = .ready then
    match lookup state.votes context with
    | none => .missing
    | some original => if command = original.data.command then .retry original else .conflict
  else .unavailable

theorem identicalRetry {state context original}
    (found : lookup state.votes context = some original) :
    retry .ready state context original.data.command = .retry original := by
  simp [retry, found]

theorem canonicalConflict {state context original command}
    (found : lookup state.votes context = some original) (different : command ≠ original.data.command) :
    retry .ready state context command = .conflict := by simp [retry, found, different]

theorem unverifiedCannotRetry {mode state context command} (notReady : mode ≠ .ready) :
    retry mode state context command = .unavailable := by simp [retry, notReady]

/-- Actual replay over prior, first admission and any legal suffix derives the
saved record. Neither recovered-state equality nor record uniqueness is assumed. -/
theorem originalRecordRecovered {a start prior before record suffix final}
    (prefixAccepted : replay a start prior = some before)
    (admitted : validVote a before record)
    (suffixAccepted : replay a ⟨before.votes ++ [record], before.current⟩ suffix = some final) :
    replay a start (prior ++ .vote record :: suffix) = some final ∧
    lookup final.votes record.data.context = some record ∧
    retry .ready final record.data.context record.data.command = .retry record := by
  have inserted := lookupFreshAppend admitted.2.2.1 record rfl
  have found := replayPreservesRecord suffixAccepted inserted
  refine ⟨?_, found, identicalRetry found⟩
  rw [replayAppend, prefixAccepted]
  simpa [replay, step, admitted] using suffixAccepted

inductive Preparation where
  | pending (record : Record) | retry (record : Record) | conflict | rejected | unavailable
  deriving DecidableEq, Repr

/-- Pure pre-WAL preparation returns no externally sendable effect. A pending
record is internal data. Callers must perform durable commit before exposing it. -/
def prepare (adapter : Adapter) (mode : Mode) (state : State) (data : VoteData) : Preparation :=
  if mode = .ready then
    match lookup state.votes data.context with
    | some original => if data.command = original.data.command then .retry original else .conflict
    | none =>
        if adapter.admitted state.current data then
          let sequence := state.votes.length + 1
          match adapter.effect data with
          | none => .rejected
          | some effect =>
              match adapter.receipt data sequence effect with
              | none => .rejected
              | some receipt => .pending ⟨data, sequence, receipt, effect⟩
        else .rejected
  else .unavailable

theorem firstRejection {a s data} (absent : lookup s.votes data.context = none)
    (invalid : a.admitted s.current data = false) :
    prepare a .ready s data = .rejected := by simp [prepare, absent, invalid]

theorem preparationSound {a s data record} (prepared : prepare a .ready s data = .pending record) :
    validVote a s record ∧ record.data = data := by
  simp only [prepare, ↓reduceIte] at prepared
  cases found : lookup s.votes data.context with
  | some original =>
      simp only [found] at prepared
      split at prepared <;> contradiction
  | none =>
      simp only [found] at prepared
      split at prepared
      · cases effect : a.effect data with
        | none => simp [effect] at prepared
        | some bytes =>
            simp only [effect] at prepared
            cases receipt : a.receipt data (s.votes.length + 1) bytes with
            | none => simp [receipt] at prepared
            | some encoded =>
                simp only [receipt] at prepared
                cases Preparation.pending.inj prepared
                exact ⟨⟨‹_›, rfl, found, effect, receipt⟩, rfl⟩
      · contradiction

inductive Stage where
  | validated | appended | durable | committed
  deriving DecidableEq, Repr

def exposePending (mode : Mode) (stage : Stage) (state : State) (record : Record) : Option Record :=
  if mode = .ready ∧ stage = .committed ∧ lookup state.votes record.data.context = some record
    then some record else none

theorem exposureRequiresCommittedRecord {mode stage state record output}
    (exposed : exposePending mode stage state record = some output) :
    mode = .ready ∧ stage = .committed ∧ lookup state.votes record.data.context = some record ∧
    output = record := by
  simp only [exposePending] at exposed
  split at exposed
  · exact ⟨‹_ ∧ _ ∧ _›.1, ‹_ ∧ _ ∧ _›.2.1, ‹_ ∧ _ ∧ _›.2.2, (Option.some.inj exposed).symm⟩
  · contradiction

inductive Recovery where
  | ready (state : State) | unresolved | blocked
  deriving DecidableEq, Repr

def checkedReplay (a : Adapter) (start : State) (journal : List Entry) : Recovery :=
  match replay a start journal with
  | some state => .ready state
  | none => .blocked

/-- Single interrupted append. The authenticator binds this exact initial state,
last known prefix, pending record and scan; authenticating that claim is not
proved here. Even an authenticated claim must pass exact prefix and replay checks. -/
def resolveUnknown (a : Adapter) (start : State) (prior : List Entry) (pending : Record)
    (scan : Scan) : Recovery :=
  if a.scanAuthenticated start prior pending scan then
    match scan with
    | .complete journal =>
      if journal = prior ++ [.vote pending] then checkedReplay a start journal else .blocked
    | .verifiedAbsent journal =>
      if journal = prior then checkedReplay a start journal else .blocked
    | .incomplete => .unresolved
    | .corrupt | .ambiguous => .blocked
  else .blocked

/-- No later scan can silently turn an already blocked recovery into permission
to vote; repair is outside this model and requires separate formal authority. -/
def continueRecovery (a : Adapter) (start : State) (prior : List Entry) (pending : Record)
    (previous : Recovery) (scan : Scan) : Recovery :=
  match previous with
  | .blocked => .blocked
  | .ready state => .ready state
  | .unresolved => resolveUnknown a start prior pending scan

def observedSequence : Recovery → Option Nat
  | .ready state => some state.votes.length
  | .unresolved | .blocked => none

theorem verifiedPresenceReplays {a start prior record final}
    (authenticated : a.scanAuthenticated start prior record (.complete (prior ++ [.vote record])) = true)
    (accepted : replay a start (prior ++ [.vote record]) = some final) :
    resolveUnknown a start prior record (.complete (prior ++ [.vote record])) = .ready final := by
  simp [resolveUnknown, authenticated, checkedReplay, accepted]

theorem verifiedAbsenceReplays {a start prior record before}
    (authenticated : a.scanAuthenticated start prior record (.verifiedAbsent prior) = true)
    (accepted : replay a start prior = some before) :
    resolveUnknown a start prior record (.verifiedAbsent prior) = .ready before := by
  simp [resolveUnknown, authenticated, checkedReplay, accepted]

theorem ordinaryPrefixCannotResolveUnknown (a start prior record) :
    resolveUnknown a start prior record (.complete prior) = .blocked := by
  have different : prior ≠ prior ++ [Entry.vote record] := by
    intro eq
    have lengths := congrArg List.length eq
    simp at lengths
  simp [resolveUnknown, different]

theorem incompleteRetainsUnknownSequence (a start prior record)
    (authenticated : a.scanAuthenticated start prior record .incomplete = true) :
    resolveUnknown a start prior record .incomplete = .unresolved ∧
    observedSequence (resolveUnknown a start prior record .incomplete) = none := by
  simp [resolveUnknown, authenticated, observedSequence]

theorem corruptAndAmbiguousStayBlocked (a start prior record scan) :
    resolveUnknown a start prior record .corrupt = .blocked ∧
    resolveUnknown a start prior record .ambiguous = .blocked ∧
    continueRecovery a start prior record .blocked scan = .blocked := by
  simp [resolveUnknown, continueRecovery]

theorem unauthenticatedScanBlocked {a start prior record scan}
    (invalid : a.scanAuthenticated start prior record scan = false) :
    resolveUnknown a start prior record scan = .blocked := by simp [resolveUnknown, invalid]

end DeltaReduce.RecoveryKernel
