import DeltaReduce.PublicRecovery

/-! Reachable live machines use the same checked all-vote log as recovery.
This layer does not authenticate public snapshots or implement phase/QC rules. -/
namespace DeltaReduce.PublicReachability
open NativeBinding PublicJournal PublicRecovery

theorem replayAppend {codec trust voteTrust}
    (env : PublicJournal.Environment codec trust voteTrust) (start : Journal)
    (left right : List PublicJournal.Event) :
    PublicJournal.replay env start (left ++ right) =
      (PublicJournal.replay env start left >>= fun mid => PublicJournal.replay env mid right) := by
  induction left generalizing start with
  | nil => rfl
  | cons event rest ih =>
      cases h : PublicJournal.step env start event <;> simp [PublicJournal.replay, h, ih]

theorem replayExtend {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {start log mid event final}
    (prior : PublicJournal.replay env start log = some mid)
    (next : PublicJournal.step env mid event = some final) :
    PublicJournal.replay env start (log ++ [event]) = some final := by
  simp [replayAppend, prior, PublicJournal.replay, next]

structure Invariant {codec trust voteTrust}
    (env : PublicRecovery.Environment codec trust voteTrust) (m : Machine) : Prop where
  replayed : PublicJournal.replay env.journal m.initial m.log = some m.journal
  emptyInitial : m.initial.slots = []
  pendingChecked : ∀ slot, m.pending = some slot →
    Nonempty (CheckedSlot env.journal m.journal slot) ∧ m.mode ≠ .ready
  sentStored : ∀ slot ∈ m.sent, slot ∈ m.journal.slots ∧ slot.native.isSome = true

theorem initialInvariant {codec trust voteTrust}
    (env : PublicRecovery.Environment codec trust voteTrust) (actor current) :
    Invariant env (PublicRecovery.initial actor current) := by
  constructor
  · rfl
  · rfl
  · intro slot h; contradiction
  · intro slot h; contradiction

theorem rememberMember {sent : List Slot} {added slot : Slot} :
    slot ∈ remember sent added ↔ slot ∈ sent ∨ slot = added := by
  unfold remember
  split
  · rename_i h
    constructor
    · exact Or.inl
    · rintro (old | rfl) <;> assumption
  · simp

theorem lookupMember {slots : List Slot} {key slot}
    (found : lookup slots key = some slot) : slot ∈ slots := by
  induction slots with
  | nil => contradiction
  | cons head rest ih =>
      simp only [lookup] at found
      split at found
      · cases Option.some.inj found; exact List.mem_cons_self
      · exact List.mem_cons_of_mem _ (ih found)

theorem arithmeticRecordPresent {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {journal slot}
    (checked : CheckedSlot env journal slot) (kind : slot.envelope.action.arithmetic = true) :
    slot.native.isSome = true := by
  cases checked.kind with
  | arithmetic _ native => simp [native.projected]
  | other otherKind _ _ => simp [kind] at otherKind

theorem observedAppendStep {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {journal slot o final}
    (accepted : observedAppend env journal slot o = some final) :
    PublicJournal.step env journal (.vote slot) = some final := by
  cases h : appendSlot env journal slot with
  | none => simp [observedAppend, h] at accepted
  | some next =>
      simp only [observedAppend, h] at accepted
      change (if observationMatches env journal next slot o then some next else none) = some final at accepted
      split at accepted
      · cases Option.some.inj accepted; exact h
      · contradiction

theorem extendedInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m : Machine}
    (prior : Invariant env m) (ready : enabled m)
    {event next mode sent}
    (accepted : PublicJournal.step env.journal m.journal event = some next)
    (stored : ∀ slot ∈ sent, slot ∈ next.slots ∧ slot.native.isSome = true) :
    Invariant env { m with journal := next, log := m.log ++ [event], mode := mode, sent := sent } := by
  constructor
  · exact replayExtend prior.replayed accepted
  · exact prior.emptyInitial
  · intro slot h; simp [ready.2] at h
  · exact stored

theorem stepPreservesSlots {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {journal event final}
    (accepted : PublicJournal.step env journal event = some final) :
    ∀ slot ∈ journal.slots, slot ∈ final.slots := by
  have history := stepSound accepted
  cases history with
  | vote _ => intro slot member; exact List.mem_append_left _ member
  | advance _ => exact fun _ h => h

theorem persistPreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m slot stages o final}
    (prior : Invariant env m)
    (accepted : persist env.journal m slot stages o = some final) : Invariant env final := by
  simp only [persist] at accepted
  split at accepted
  · rename_i gate
    cases checked : checkSlot env.journal m.journal slot with
    | none => simp [checked] at accepted
    | some evidence =>
      cases cut : classify stages with
      | none => simp [checked, cut] at accepted
      | some choice =>
        cases choice with
        | unknown =>
          simp only [checked, cut] at accepted
          split at accepted
          · cases Option.some.inj accepted
            exact ⟨prior.replayed, prior.emptyInitial,
              fun s h => by cases Option.some.inj h; exact ⟨⟨evidence⟩, by intro impossible; cases impossible⟩,
              prior.sentStored⟩
          · contradiction
        | exposed =>
          cases appended : observedAppend env.journal m.journal slot
              ⟨o.before, o.after, true, o.receipt, o.effect⟩ with
          | none => simp only [checked, cut] at accepted
                    simp [appended] at accepted
          | some next =>
            simp only [checked, cut] at accepted
            have same : some { m with
                journal := next, log := m.log ++ [.vote slot],
                mode := .ready, sent := remember m.sent slot } = some final := by
              simpa only [show (Cut.unexposed == Cut.exposed) = false from rfl, show (Cut.exposed == Cut.exposed) = true from rfl, appended, bind, Option.bind, Bool.false_eq_true, ↓reduceIte] using accepted
            cases Option.some.inj same
            have step := observedAppendStep appended
            apply extendedInvariant prior gate.1 step
            intro s member
            rcases rememberMember.mp member with old | rfl
            · exact ⟨stepPreservesSlots step s (prior.sentStored s old).1, (prior.sentStored s old).2⟩
            · have shape := (observedAppendExact appended).1.choose_spec
              rw [shape]
              exact ⟨List.mem_append_right _ (List.mem_singleton_self _), arithmeticRecordPresent evidence gate.2⟩
        | unexposed =>
          cases appended : observedAppend env.journal m.journal slot
              ⟨o.before, o.after, false, o.receipt, o.effect⟩ with
          | none => simp only [checked, cut] at accepted
                    simp [show (Cut.unexposed == Cut.exposed) = false from rfl, appended] at accepted
          | some next =>
            simp only [checked, cut] at accepted
            have same : some { m with
                journal := next, log := m.log ++ [.vote slot],
                mode := .mustCrash } = some final := by simpa only [show (Cut.unexposed == Cut.exposed) = false from rfl, show (Cut.exposed == Cut.exposed) = true from rfl, appended, bind, Option.bind, Bool.false_eq_true, ↓reduceIte] using accepted
            cases Option.some.inj same
            have step := observedAppendStep appended
            apply extendedInvariant prior gate.1 step
            intro s member
            exact ⟨stepPreservesSlots step s (prior.sentStored s member).1, (prior.sentStored s member).2⟩
  · contradiction

theorem otherVotePreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m slot final}
    (prior : Invariant env m) (accepted : otherVote env.journal m slot = some final) :
    Invariant env final := by
  simp only [otherVote] at accepted
  split at accepted
  · rename_i gate
    cases h : appendSlot env.journal m.journal slot with
    | none => simp [h] at accepted
    | some next =>
      simp only [h] at accepted
      cases Option.some.inj accepted
      apply extendedInvariant prior gate.1 (event := .vote slot) h
      intro s member
      exact ⟨stepPreservesSlots (event := .vote slot) h s (prior.sentStored s member).1,
        (prior.sentStored s member).2⟩
  · contradiction

theorem advancePreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m certificate final}
    (prior : Invariant env m) (accepted : advance env.journal m certificate = some final) :
    Invariant env final := by
  simp only [advance] at accepted
  split at accepted
  · rename_i gate
    cases h : PublicJournal.step env.journal m.journal (.advance certificate) with
    | none => simp [h] at accepted
    | some next =>
      simp only [h] at accepted
      cases Option.some.inj accepted
      apply extendedInvariant prior gate h
      intro s member
      exact ⟨stepPreservesSlots h s (prior.sentStored s member).1, (prior.sentStored s member).2⟩
  · contradiction

theorem modeChangePreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m : Machine} {mode : Mode}
    (prior : Invariant env m) (notReady : mode ≠ .ready) :
    Invariant env { m with mode := mode } := by
  exact ⟨prior.replayed, prior.emptyInitial,
    fun slot h => ⟨(prior.pendingChecked slot h).1, notReady⟩, prior.sentStored⟩

theorem crashPreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m final}
    (prior : Invariant env m) (accepted : crash m = some final) : Invariant env final := by
  unfold crash at accepted
  split at accepted
  · cases Option.some.inj accepted; exact modeChangePreservesInvariant prior (by decide)
  · contradiction

theorem restartPreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m final}
    (prior : Invariant env m) (accepted : restart m = some final) : Invariant env final := by
  unfold restart at accepted
  split at accepted
  · cases Option.some.inj accepted; exact modeChangePreservesInvariant prior (by decide)
  · contradiction

theorem retryOriginalSlot {m key command slot}
    (accepted : retry m key command = .retry slot) :
    slot ∈ m.journal.slots ∧ slot.native.isSome = true := by
  unfold retry at accepted
  split at accepted
  · cases found : lookup m.journal.slots key with
    | none => simp [found] at accepted
    | some saved =>
      cases rec : saved.native with
      | none => simp [found, rec] at accepted
      | some record =>
        simp only [found, rec] at accepted
        split at accepted
        · cases RetryResult.retry.inj accepted; exact ⟨lookupMember found, by simp [rec]⟩
        · contradiction
  · contradiction

theorem exposeRetryPreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m key command final record}
    (prior : Invariant env m) (accepted : exposeRetry m key command = some (final, record)) :
    Invariant env final := by
  cases h : retry m key command with
  | conflict | missing | unavailable => simp [exposeRetry, h] at accepted
  | retry slot =>
    cases rec : slot.native with
    | none => simp [exposeRetry, h, rec] at accepted
    | some saved =>
      simp only [exposeRetry, h, rec] at accepted
      change some ({ m with sent := remember m.sent slot }, saved) = some (final, record) at accepted
      have same := Option.some.inj accepted
      cases same
      refine ⟨prior.replayed, prior.emptyInitial, prior.pendingChecked, ?_⟩
      intro s member
      rcases rememberMember.mp member with old | rfl
      · exact prior.sentStored s old
      · exact retryOriginalSlot h

theorem recoveryLogExtends {m : Machine} {scan events}
    (accepted : recoveryLog m scan = some events) :
    ∃ suffix, events = m.log ++ suffix := by
  cases scan with
  | complete saved =>
    cases p : m.pending with
    | none =>
      simp only [recoveryLog, p] at accepted
      split at accepted
      · cases Option.some.inj accepted; exact ⟨[], by simpa using ‹events = m.log›⟩
      · contradiction
    | some slot =>
      simp only [recoveryLog, p] at accepted
      split at accepted
      · cases Option.some.inj accepted; exact ⟨[.vote slot], ‹_›⟩
      · contradiction
  | verifiedAbsent saved =>
    simp only [recoveryLog] at accepted
    split at accepted
    · cases Option.some.inj accepted; exact ⟨[], by simpa using ‹_ ∧ _›.2⟩
    · contradiction
  | incomplete | corrupt | ambiguous => contradiction

theorem restorePreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m scan events o final}
    (prior : Invariant env m) (selected : recoveryLog m scan = some events)
    (accepted : restore env m events o = some final) : Invariant env final := by
  cases replayed : PublicJournal.replay env.journal m.initial events with
  | none => simp [restore, replayed] at accepted
  | some recovered =>
    simp only [restore, replayed] at accepted
    change (if _ then some _ else none) = some final at accepted
    split at accepted
    · cases Option.some.inj accepted
      refine ⟨replayed, prior.emptyInitial, ?_, ?_⟩
      · intro slot h; contradiction
      · obtain ⟨suffix, eqn⟩ := recoveryLogExtends selected
        have tail : PublicJournal.replay env.journal m.journal suffix = some recovered := by
          simpa [eqn, replayAppend, prior.replayed] using replayed
        intro slot member
        exact ⟨replayPreservesProjectedRecord tail (prior.sentStored slot member).1,
          (prior.sentStored slot member).2⟩
    · contradiction

theorem recoverPreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m scan o final}
    (prior : Invariant env m) (accepted : recover env m scan o = some final) : Invariant env final := by
  simp only [recover] at accepted
  split at accepted
  · split at accepted
    · cases scan with
      | complete events =>
        cases selected : recoveryLog m (.complete events) with
        | none => simp [selected] at accepted
        | some log =>
          apply restorePreservesInvariant prior selected
          simpa [selected] using accepted
      | verifiedAbsent events =>
        cases selected : recoveryLog m (.verifiedAbsent events) with
        | none => simp [selected] at accepted
        | some log =>
          apply restorePreservesInvariant prior selected
          simpa [selected] using accepted
      | incomplete | corrupt | ambiguous =>
        dsimp only at accepted
        split at accepted
        · cases Option.some.inj accepted
          apply modeChangePreservesInvariant prior
          simp
        · contradiction
    · contradiction
  · contradiction

/-- Reachability is generated only by successful executable operations; no
replay equation, prefix equality or invariant is a constructor premise. -/
inductive Transition {codec trust voteTrust}
    (env : PublicRecovery.Environment codec trust voteTrust) : Machine → Machine → Prop where
  | persist {m slot stages o final} (result : PublicRecovery.persist env.journal m slot stages o = some final) : Transition env m final
  | otherVote {m slot final} (result : PublicRecovery.otherVote env.journal m slot = some final) : Transition env m final
  | advance {m certificate final} (result : PublicRecovery.advance env.journal m certificate = some final) : Transition env m final
  | crash {m final} (result : PublicRecovery.crash m = some final) : Transition env m final
  | restart {m final} (result : PublicRecovery.restart m = some final) : Transition env m final
  | recover {m scan o final} (result : PublicRecovery.recover env m scan o = some final) : Transition env m final
  | retry {m key command final record} (result : exposeRetry m key command = some (final, record)) : Transition env m final

inductive Reachable {codec trust voteTrust}
    (env : PublicRecovery.Environment codec trust voteTrust) (actor : String) (current : RecoveryKernel.Current) : Machine → Prop where
  | initial : Reachable env actor current (PublicRecovery.initial actor current)
  | next {m final} (prior : Reachable env actor current m) (step : Transition env m final) : Reachable env actor current final

theorem transitionPreservesInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m final}
    (prior : Invariant env m) (step : Transition env m final) : Invariant env final := by
  cases step with
  | persist result => exact persistPreservesInvariant prior result
  | otherVote result => exact otherVotePreservesInvariant prior result
  | advance result => exact advancePreservesInvariant prior result
  | crash result => exact crashPreservesInvariant prior result
  | restart result => exact restartPreservesInvariant prior result
  | recover result => exact recoverPreservesInvariant prior result
  | retry result => exact exposeRetryPreservesInvariant prior result

theorem reachableInvariant {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {actor current m}
    (reachable : Reachable env actor current m) : Invariant env m := by
  induction reachable with
  | initial => exact initialInvariant env actor current
  | next _ step ih => exact transitionPreservesInvariant ih step

theorem reachableJournalHistory {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {actor current m}
    (reachable : Reachable env actor current m) :
    PublicJournal.History env.journal m.initial m.log m.journal ∧
    m.journal.slots = voteSlots m.log := by
  have inv := reachableInvariant reachable
  exact ⟨replaySound inv.replayed, by simpa [inv.emptyInitial] using replayExactSlots inv.replayed⟩

theorem reachablePendingCannotBeReady {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {actor current m slot}
    (reachable : Reachable env actor current m) (pending : m.pending = some slot) :
    Nonempty (CheckedSlot env.journal m.journal slot) ∧ m.mode ≠ .ready :=
  (reachableInvariant reachable).pendingChecked slot pending

theorem reachableSentIsStored {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {actor current m slot}
    (reachable : Reachable env actor current m) (sent : slot ∈ m.sent) :
    slot ∈ voteSlots m.log ∧ slot.native.isSome = true := by
  have bound := (reachableInvariant reachable).sentStored slot sent
  rw [(reachableJournalHistory reachable).2] at bound
  exact bound

theorem transitionInitialUnchanged {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {m final}
    (transition : Transition env m final) : final.initial = m.initial := by
  cases transition <;> rename_i result
  all_goals
    simp only [persist, otherVote, advance, crash, restart, recover, restore, exposeRetry,
      bind, Option.bind] at result
    repeat' first | dsimp only at result | split at result | contradiction
  all_goals
    first
    | cases Option.some.inj result; rfl
    | exact (congrArg (fun pair : Machine × RecoveryKernel.Record => pair.1.initial)
        (Option.some.inj result)).symm

theorem reachableInitialUnchanged {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {actor current m}
    (reachable : Reachable env actor current m) :
    m.initial = (PublicRecovery.initial actor current).initial := by
  induction reachable with
  | initial => rfl
  | next _ step ih => exact (transitionInitialUnchanged step).trans ih

theorem historySlotProvenance {codec trust voteTrust}
    {env : PublicJournal.Environment codec trust voteTrust} {start events final slot}
    (history : PublicJournal.History env start events final) (member : slot ∈ final.slots) :
    slot ∈ start.slots ∨ ∃ before, Nonempty (CheckedSlot env before slot) := by
  induction history with
  | nil => exact Or.inl member
  | cons transition tail ih =>
    rcases ih member with old | new
    · cases transition with
      | vote checked =>
        rcases List.mem_append.mp old with old | added
        · exact Or.inl old
        · cases List.mem_singleton.mp added; exact Or.inr ⟨_, ⟨checked⟩⟩
      | advance _ => exact Or.inl old
    · exact Or.inr new

theorem reachableSlotProvenance {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {actor current m slot}
    (reachable : Reachable env actor current m) (member : slot ∈ m.journal.slots) :
    ∃ before, Nonempty (CheckedSlot env.journal before slot) := by
  rcases historySlotProvenance (reachableJournalHistory reachable).1 member with old | derived
  · simp [(reachableInvariant reachable).emptyInitial] at old
  · exact derived

theorem reachableArithmeticPreparation {codec trust voteTrust}
    {env : PublicRecovery.Environment codec trust voteTrust} {actor current m slot}
    (reachable : Reachable env actor current m) (member : slot ∈ m.journal.slots)
    (kind : slot.envelope.action.arithmetic = true) :
    ∃ before, ∃ _checked : CheckedSlot env.journal before slot,
      ∃ native : NativeSlot env.journal before slot,
      ∃ resolved : NativeReplay.Resolved env.journal.native native.record.data,
      ∃ prepared : NativePrepared resolved.binding voteTrust resolved.input.metadata .ready
        before.admissionState native.record.data.command,
        native.record = prepared.record ∧ slot.native = some prepared.record ∧
        prepared.record.sequence = before.slots.length + 1 ∧
        prepared.record.receipt = native.record.receipt ∧
        prepared.record.effect = native.record.effect ∧ SlotCommon before slot := by
  obtain ⟨before, ⟨checked⟩⟩ := reachableSlotProvenance reachable member
  obtain ⟨native, resolved, prepared, same⟩ := checkedNativeHasPreparation checked kind
  refine ⟨before, checked, native, resolved, prepared, same, ?_, ?_, ?_, ?_, checked.common⟩
  · rw [← same]; exact native.projected
  · rw [← same]; exact nativeSequenceCountsAllSlots checked native
  · exact (congrArg RecoveryKernel.Record.receipt same).symm
  · exact (congrArg RecoveryKernel.Record.effect same).symm

end DeltaReduce.PublicReachability
