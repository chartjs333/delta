import DeltaReduce.ArithmeticBinding

/-! Arithmetic-derived journal admission. This is still a conditional bridge:
the native input resolver and QC/scan authenticators require actual exporter
provenance. No Boolean arithmetic-admission oracle or finite record table is
accepted. Public trace projection and other vote kinds remain separate work. -/
namespace DeltaReduce.NativeReplay
open NativeBinding RecoveryKernel
abbrev Bytes := NativeBinding.Bytes

/-- Resolved independently of command bytes, by the authenticated formal context.
An unavailable graph is explicit and cannot supply empty/default inputs. -/
structure Input (codec : Codec) (trust : Trust) (voteTrust : NativeVoteTrust) where
  anchor : Anchor
  store : Store
  available : Option (Binding codec trust anchor store)
  metadata : VoteMetadata
  authenticated : voteTrust.authenticated anchor metadata

structure Graph (codec : Codec) (trust : Trust) where
  anchor : Anchor
  store : Store
  available : Option (Binding codec trust anchor store)

structure Environment (codec : Codec) (trust : Trust) (voteTrust : NativeVoteTrust) where
  input : Bytes → Option (Input codec trust voteTrust)
  graph : Bytes → Option (Graph codec trust)
  /-- Verify the exact recomputed APPLY body and parent/next checkpoint tuple,
  including real quorum/certificate lineage. Not an arithmetic-result oracle. -/
  applyAuthenticated : Anchor → Bytes → Certificate → Bool
  scanAuthenticated : State → List Entry → Record → Scan → Bool

structure Resolved {codec trust voteTrust} (env : Environment codec trust voteTrust) (data : VoteData) where
  input : Input codec trust voteTrust
  selected : env.input data.context = some input
  binding : Binding codec trust input.anchor input.store
  available : input.available = some binding
  expected : ExpectedNativeVote binding input.metadata
  exactData : expected.data = data
  bounded : data.command.length ≤ 4194304

def resolve {codec trust voteTrust} (env : Environment codec trust voteTrust) (data : VoteData) :
    Option (Resolved env data) := do
  match selected : env.input data.context with
  | none => none
  | some input =>
      match available : input.available with
      | none => none
      | some binding =>
          let expected ← deriveExpectedNativeVote binding input.metadata
          if checked : expected.data = data ∧ data.command.length ≤ 4194304 then
            some ⟨input, selected, binding, available, expected, checked.1, checked.2⟩
          else none

def admitted {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (current : Current) (data : VoteData) : Bool :=
  match resolve env data with
  | none => false
  | some resolved => decide (NativeFresh resolved.input.anchor resolved.input.metadata .ready ⟨[], current⟩)

def effect {codec trust voteTrust} (env : Environment codec trust voteTrust) (data : VoteData) : Option Bytes :=
  (resolve env data).map (fun resolved => resolved.expected.effect)

def receipt {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (data : VoteData) (sequence : Nat) (bytes : Bytes) : Option Bytes := do
  let resolved ← resolve env data
  if bytes = resolved.expected.effect then
    encodeDiagnosticReceipt codec data.command resolved.expected.envelope bytes sequence
  else none

structure CheckedApply {codec trust voteTrust} (env : Environment codec trust voteTrust) (c : Certificate) where
  graph : Graph codec trust
  selected : env.graph c.bytes = some graph
  binding : Binding codec trust graph.anchor graph.store
  available : graph.available = some binding
  result : NativeApply binding
  parent : c.parent = nativeCurrent graph.anchor
  model : c.next.model = idBytes result.body.nextModelHash
  optimizer : c.next.optimizer = idBytes result.body.nextOptimizerHash
  authenticated : env.applyAuthenticated graph.anchor result.bytes c = true

def checkApply {codec trust voteTrust} (env : Environment codec trust voteTrust) (c : Certificate) :
    Option (CheckedApply env c) := do
  match selected : env.graph c.bytes with
  | none => none
  | some graph =>
      match available : graph.available with
      | none => none
      | some binding =>
          let result ← deriveNativeApply binding
          if checked : c.parent = nativeCurrent graph.anchor ∧
              c.next.model = idBytes result.body.nextModelHash ∧
              c.next.optimizer = idBytes result.body.nextOptimizerHash ∧
              env.applyAuthenticated graph.anchor result.bytes c = true then
            some ⟨graph, selected, binding, available, result,
              checked.1, checked.2.1, checked.2.2.1, checked.2.2.2⟩
          else none

def adapter {codec trust voteTrust} (env : Environment codec trust voteTrust) : Adapter where
  admitted := admitted env
  effect := effect env
  receipt := receipt env
  authenticated c := (checkApply env c).isSome
  scanAuthenticated := env.scanAuthenticated

theorem unavailableContextRejects {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {data current} (missing : env.input data.context = none) :
    admitted env current data = false ∧ effect env data = none := by
  have rejected : resolve env data = none := by
    unfold resolve
    split
    · rfl
    · rename_i input selected
      rw [missing] at selected
      contradiction
  simp [admitted, effect, rejected]

theorem unavailableGraphRejects {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {data current input} (selected : env.input data.context = some input) (missing : input.available = none) :
    admitted env current data = false ∧ effect env data = none := by
  have rejected : resolve env data = none := by
    unfold resolve
    split
    · rfl
    · rename_i other found
      have same := Option.some.inj (selected.symm.trans found)
      subst other
      split
      · rfl
      · rename_i binding available
        rw [missing] at available
        contradiction
  simp [admitted, effect, rejected]

/-- Extract a complete native preparation from the actual replay admission
checks. No row/result equality, expected record or admission axiom is supplied. -/
theorem acceptedVoteHasPreparation {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {state : State} {record : Record} (accepted : validVote (adapter env) state record) :
    ∃ resolved : Resolved env record.data, resolve env record.data = some resolved ∧
      ∃ prepared : NativePrepared resolved.binding voteTrust resolved.input.metadata .ready state record.data.command,
        record = prepared.record := by
  obtain ⟨admission, sequence, first, effectEq, receiptEq⟩ := accepted
  change admitted env state.current record.data = true at admission
  cases resolved : resolve env record.data with
  | none => simp [admitted, resolved] at admission
  | some result =>
      have fresh : NativeFresh result.input.anchor result.input.metadata .ready state := by
        simpa [admitted, resolved, NativeFresh] using admission
      have sameEffect : result.expected.effect = record.effect := by
        simpa [adapter, effect, resolved] using effectEq
      have encoded : encodeDiagnosticReceipt codec result.expected.command result.expected.envelope
          result.expected.effect (state.votes.length + 1) = some record.receipt := by
        have command : result.expected.command = record.data.command := congrArg VoteData.command result.exactData
        simpa [adapter, receipt, resolved, sameEffect, command, sequence] using receiptEq
      let prepared : NativePrepared result.binding voteTrust result.input.metadata .ready state record.data.command :=
        ⟨result.expected, result.input.authenticated, fresh,
          by simpa only [← result.exactData, ExpectedNativeVote.data] using first,
          (congrArg VoteData.command result.exactData).symm, result.bounded, record.receipt, encoded⟩
      refine ⟨result, rfl, prepared, ?_⟩
      have sameData := result.exactData
      cases record
      simp_all [NativePrepared.record, prepared]

theorem acceptedApplyHasDerivation {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {state final : State} {c : Certificate} (accepted : step (adapter env) state (.advance c) = some final) :
    ∃ checked : CheckedApply env c, checkApply env c = some checked ∧
      final.votes = state.votes ∧
      (final = state ∨ (state.current = c.parent ∧ final.current = c.next)) := by
  obtain ⟨authenticated, votes, change⟩ := advanceRequiresCertificate accepted
  change (checkApply env c).isSome = true at authenticated
  cases checked : checkApply env c with
  | none => simp [checked] at authenticated
  | some result => exact ⟨result, rfl, votes, change⟩

/-- Native-specific independent history relation. Arithmetic votes carry actual
checked graph/metadata/encoder derivations, never a caller's accepted flag. -/
inductive NativeTransition {codec trust voteTrust} (env : Environment codec trust voteTrust) :
    State → Entry → State → Prop where
  | vote {s r} (resolved : Resolved env r.data)
      (prepared : NativePrepared resolved.binding voteTrust resolved.input.metadata .ready s r.data.command)
      (same : r = prepared.record) : NativeTransition env s (.vote r) ⟨s.votes ++ [r], s.current⟩
  | advance {s c} (checked : CheckedApply env c)
      (fresh : s.current ≠ c.next) (parent : s.current = c.parent) :
      NativeTransition env s (.advance c) ⟨s.votes, c.next⟩
  | already {s c} (checked : CheckedApply env c) (same : s.current = c.next) :
      NativeTransition env s (.advance c) s

inductive NativeHistory {codec trust voteTrust} (env : Environment codec trust voteTrust) :
    State → List Entry → State → Prop where
  | nil (s) : NativeHistory env s [] s
  | cons {s e mid rest final} (transition : NativeTransition env s e mid)
      (tail : NativeHistory env mid rest final) : NativeHistory env s (e :: rest) final

theorem replayHasNativeHistory {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {start entries final} (accepted : replay (adapter env) start entries = some final) :
    NativeHistory env start entries final := by
  have history := replaySound accepted
  clear accepted
  induction history with
  | nil s => exact .nil s
  | cons transition tail ih =>
      apply NativeHistory.cons (tail := ih)
      cases transition with
      | vote accepted =>
          obtain ⟨resolved, _, prepared, same⟩ := acceptedVoteHasPreparation accepted
          exact .vote resolved prepared same
      | advance authenticated fresh parent =>
          change (checkApply env _).isSome = true at authenticated
          obtain ⟨result, _⟩ := Option.isSome_iff_exists.mp authenticated
          exact .advance result fresh parent
      | already authenticated same =>
          change (checkApply env _).isSome = true at authenticated
          obtain ⟨result, _⟩ := Option.isSome_iff_exists.mp authenticated
          exact .already result same

/-- Genesis-prefix provenance is established by replay, not an arbitrary
recovered-state equality. This claim concerns arithmetic votes and ApplyQC only. -/
theorem genesisReplayHasNativeProvenance {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {current entries final} (accepted : replay (adapter env) (initial current) entries = some final) :
    NativeHistory env (initial current) entries final ∧ final.votes = voteRecords entries := by
  exact ⟨replayHasNativeHistory accepted, by simpa [initial] using replayExactRecords accepted⟩

theorem preparedRecordRecovered {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {start prior before record suffix final}
    (priorAccepted : replay (adapter env) start prior = some before)
    (accepted : validVote (adapter env) before record)
    (suffixAccepted : replay (adapter env) ⟨before.votes ++ [record], before.current⟩ suffix = some final) :
    NativeHistory env start (prior ++ .vote record :: suffix) final ∧
    lookup final.votes record.data.context = some record ∧
    retry .ready final record.data.context record.data.command = .retry record := by
  obtain ⟨replayed, found, retry⟩ := originalRecordRecovered priorAccepted accepted suffixAccepted
  exact ⟨replayHasNativeHistory replayed, found, retry⟩

theorem recoveredConflictKeepsOriginal {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {start entries final context original command}
    (replayed : replay (adapter env) start entries = some final)
    (found : lookup start.votes context = some original) (different : command ≠ original.data.command) :
    retry .ready final context command = .conflict ∧
    retry .ready final context original.data.command = .retry original := by
  have kept := replayPreservesRecord replayed found
  exact ⟨canonicalConflict kept different, identicalRetry kept⟩

theorem staleFirstVoteRejected {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {state data} {resolved : Resolved env data} (selected : resolve env data = some resolved)
    (stale : state.current ≠ nativeCurrent resolved.input.anchor)
    (absent : lookup state.votes data.context = none) :
    prepare (adapter env) .ready state data = .rejected := by
  apply firstRejection absent
  simp [adapter, admitted, selected, NativeFresh, stale]

theorem failedReceiptEncodingRejects {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {state data} (absent : lookup state.votes data.context = none)
    (failed : ∀ bytes, receipt env data (state.votes.length + 1) bytes = none) :
    prepare (adapter env) .ready state data = .rejected := by
  simp only [prepare, adapter, ↓reduceIte, absent]
  split
  · cases effect env data <;> simp [failed]
  · rfl

/-- Presence is established by an authenticated exact-prefix scan and real
native replay, independently of whether any receipt was previously returned. -/
theorem unknownNativePresence {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {current prior before record}
    (priorAccepted : replay (adapter env) (initial current) prior = some before)
    (accepted : validVote (adapter env) before record)
    (scan : env.scanAuthenticated (initial current) prior record
      (.complete (prior ++ [.vote record])) = true) :
    resolveUnknown (adapter env) (initial current) prior record (.complete (prior ++ [.vote record])) =
      .ready ⟨before.votes ++ [record], before.current⟩ ∧
    NativeHistory env (initial current) (prior ++ [.vote record]) ⟨before.votes ++ [record], before.current⟩ ∧
    retry .ready ⟨before.votes ++ [record], before.current⟩ record.data.context record.data.command = .retry record := by
  obtain ⟨replayed, _, retried⟩ := originalRecordRecovered priorAccepted accepted
    (show replay (adapter env) ⟨before.votes ++ [record], before.current⟩ [] =
      some ⟨before.votes ++ [record], before.current⟩ from rfl)
  exact ⟨verifiedPresenceReplays scan replayed, replayHasNativeHistory replayed, retried⟩

theorem unknownNativeAbsence {codec trust voteTrust} {env : Environment codec trust voteTrust}
    {current prior before record}
    (priorAccepted : replay (adapter env) (initial current) prior = some before)
    (scan : env.scanAuthenticated (initial current) prior record (.verifiedAbsent prior) = true) :
    resolveUnknown (adapter env) (initial current) prior record (.verifiedAbsent prior) = .ready before ∧
    NativeHistory env (initial current) prior before ∧ before.votes = voteRecords prior := by
  exact ⟨verifiedAbsenceReplays scan priorAccepted, genesisReplayHasNativeProvenance priorAccepted⟩

theorem unknownNativeCannotInferAbsence {codec trust voteTrust} (env : Environment codec trust voteTrust)
    (start prior record) :
    resolveUnknown (adapter env) start prior record (.complete prior) = .blocked ∧
    resolveUnknown (adapter env) start prior record .corrupt = .blocked ∧
    resolveUnknown (adapter env) start prior record .ambiguous = .blocked := by
  exact ⟨ordinaryPrefixCannotResolveUnknown _ _ _ _,
    (corruptAndAmbiguousStayBlocked (adapter env) start prior record .incomplete).1,
    (corruptAndAmbiguousStayBlocked (adapter env) start prior record .incomplete).2.1⟩

end DeltaReduce.NativeReplay
