import DeltaReduce.NativeConfigReplay

/-! Complete original policy admission in the existing computed mixed WAL fold.
The whole mode binds the actual decoded initial policy/state and every candidate.
The CURRENT native arithmetic refusal is retained; this is not PO-AB1 or a
physical durability/authentication theorem. Historical retry is a separate cache
lookup and never re-runs current admission. -/
namespace DeltaReduce.NativeWholeReplay
open NativeReceiptBytes NativeVoteBytes NativeConfigReplay

/-- Inverse of runSound: histories contain actual executed steps. -/
theorem historyRun {mode sha policy snap m log n}
    (h : History mode sha policy snap m log n) : run mode sha policy snap m log = some n := by
  induction h with
  | nil => rfl
  | cons step _ ih => simp only [run,step,ih,bind,Option.bind]

/-- Every new cache record has an actual executable pre and suffix; the
preceding machine is not a caller-chosen state with a matching vote count. -/
theorem historyVotePosition {mode sha policy snap m log n}
    (h : History mode sha policy snap m log n) (stored : Stored) (mem : stored ∈ n.votes) :
    stored ∈ m.votes ∨ ∃ pre e suffix prior b v id,
      log = pre ++ e::suffix ∧ run mode sha policy snap m pre = some prior ∧
      VoteEntry mode sha policy snap prior e b v id ∧
      run mode sha policy snap (added mode snap prior e b v id) suffix = some n ∧
      stored = ⟨v,voteReceipt mode b e v id,NativeReplayAdmission.parents mode b⟩ := by
  induction h with
  | nil => exact Or.inl mem
  | @cons m e next rest final hs ht ih =>
    rcases ih mem with old | found
    · rcases stepSound hs with ⟨_,_,same⟩ | ⟨b,v,id,checks,rfl⟩
      · exact Or.inl (same ▸ old)
      · simp only [added,List.mem_append,List.mem_singleton] at old
        rcases old with old | eq
        · exact Or.inl old
        · exact Or.inr ⟨[],e,rest,m,b,v,id,rfl,rfl,checks,historyRun ht,eq⟩
    · obtain ⟨pre,entry,suffix,prior,b,v,id,eq,before,checks,after,record⟩ := found
      refine Or.inr ⟨e::pre,entry,suffix,prior,b,v,id,?_,?_,checks,after,record⟩
      · simp only [eq,List.cons_append]
      · simp only [run,hs,before,bind,Option.bind]

theorem recoveredPosition {sha policy initial snap log final stored}
    (h : recover .whole sha policy initial snap log = some final) (mem : stored ∈ final.votes) :
    ∃ startup core pre e suffix prior x v id,
      NativeReplayAdmission.prepareWhole sha policy initial = some startup ∧
      NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial = some core ∧
      log = pre ++ e::suffix ∧ run .whole sha policy snap ⟨core,[]⟩ pre = some prior ∧
      VoteEntry .whole sha policy snap prior e x v id ∧
      run .whole sha policy snap (added .whole snap prior e x v id) suffix = some final ∧
      stored = ⟨v,voteReceipt .whole x e v id,x.admitted.selected.original.parents⟩ := by
  obtain ⟨startup,core,hp,hc,hist,_,_⟩ := recoveryComputed h
  rcases historyVotePosition hist stored mem with old | found
  · exact False.elim (List.not_mem_nil old)
  · obtain ⟨pre,e,suffix,prior,x,v,id,eq,before,checked,after,record⟩ := found
    exact ⟨startup,core,pre,e,suffix,prior,x,v,id,hp,hc,eq,before,checked,after,record⟩

/-- All runtime admission facts are derived from the fold, including the global
WAL position shared with commands. Neither readiness nor recovery is an input. -/
theorem actualFacts (m : Machine) (e : NativeWalBytes.Entry) :
    (facts m e).tick = m.core.tick ∧ (facts m e).expectedSequence = e.sequence ∧
    (facts m e).invalidated = m.core.invalidated ∧
    (facts m e).ready = false ∧ (facts m e).recovery = true := ⟨rfl,rfl,rfl,rfl,rfl⟩

theorem entryWholeSource {sha policy snap m e x v id}
    (h : VoteEntry .whole sha policy snap m e x v id) :
    NativeSelectedVote.Source sha policy m.core.state e.command (facts m e) x ∧
    v = x.vote ∧ encodeFrame v.wire = e.command ∧
    e.sequence = m.core.sequence + 1 ∧ v.sequence = e.sequence ∧
    NativeWalBytes.policyId sha policy = some e.record ∧
    NativeSelectedVote.GuardedAction x.admitted.selected.original.action := by
  have original := voteOriginalSource h
  obtain ⟨source,eq⟩ := NativeReplayAdmission.wholeExact original.1
  exact ⟨NativeSelectedVote.fromBytesSource source,eq,original.2.1,h.2.1,
    NativeReplayAdmission.originalSequence original.1,original.2.2.2,
    (NativeReplayAdmission.guardedActionMatches original.1).1⟩

theorem entryWholeAuthority {sha policy snap m e x v id}
    (h : VoteEntry .whole sha policy snap m e x v id) :
    NativePolicyBytes.Canonical x.policy ∧
    NativeSnapshotBase.bindSnapshot sha x.policy x.state = some x.admitted.checked.snapshot ∧
    x.admitted.checked.entries.map NativeCandidateAuthority.Entry.original = x.policy.candidates ∧
    x.policy.candidates.find? (NativeSelectedVote.matching x.state x.vote) =
      some x.admitted.selected.original ∧
    NativeSelectedVote.Checks x.policy x.state x.admitted.checked.snapshot.prior.tail
      x.admitted.selected (facts m e) x.vote :=
  NativeSelectedVote.originalByteAuthority
    (NativeReplayAdmission.wholeExact (voteOriginalSource h).1).1

theorem globalPosition {sha policy snap core pre prior e x v id}
    (start : core.sequence = 0)
    (before : run .whole sha policy snap ⟨core,[]⟩ pre = some prior)
    (h : VoteEntry .whole sha policy snap prior e x v id) :
    e.sequence = pre.length + 1 ∧ v.sequence = pre.length + 1 := by
  have counted := historySequence (runSound before)
  have source := entryWholeSource h
  simp only [start,Nat.zero_add] at counted
  exact ⟨by omega,by omega⟩

theorem duplicateScanRejected {mode sha policy snap m e}
    (kind : e.kind = 2)
    (conflict : ∀ b v, NativeReplayAdmission.fromBytes mode sha policy m.core.state e.command
      (facts m e) = some (b,v) → ¬ fresh m v) : step mode sha policy snap m e = none := by
  cases hs : step mode sha policy snap m e with
  | none => rfl
  | some n =>
    rcases stepSound hs with ⟨command,_,_⟩ | ⟨b,v,id,checks,_⟩
    · omega
    · exact False.elim (conflict b v (voteOriginalSource checks).1 checks.2.2.2.2.2.2.2.2.2.1)

theorem invalidatedScanRejected {sha policy snap m e}
    (kind : e.kind = 2) (bad : m.core.invalidated = true) :
    step .whole sha policy snap m e = none := by
  simp only [step,if_neg (by omega : e.kind ≠ 1)]
  split <;> try rfl
  rw [NativeReplayAdmission.wholeInvalidated (show (facts m e).invalidated = true from bad)]
  rfl

theorem commandInvalidates {sha policy snap m e n}
    (h : step .whole sha policy snap m e = some n) (kind : e.kind = 1) :
    n.core.invalidated = true := by
  rcases stepSound h with ⟨_,cmd,_⟩ | ⟨b,v,id,checks,_⟩
  · exact (NativeCommandReplay.stepClock cmd (by rfl)).2
  · have vote := checks.1; omega

theorem arithmeticScanRejected {sha policy snap m e v}
    (kind : e.kind = 2) (parsed : decodeFrame e.command = some v)
    (arith : v.wire.kind = actionName 5 ∨ v.wire.kind = actionName 7) :
    step .whole sha policy snap m e = none := by
  cases hs : step .whole sha policy snap m e with
  | none => rfl
  | some n =>
    rcases stepSound hs with ⟨command,_,_⟩ | ⟨x,w,id,checks,_⟩
    · omega
    · obtain ⟨source,rfl⟩ := NativeReplayAdmission.wholeExact (voteOriginalSource checks).1
      have frame := (NativeSelectedVote.fromBytesSource source).vote
      rw [parsed] at frame
      have eq := Option.some.inj frame
      have hc := NativeReplayAdmission.wholeChecks (voteOriginalSource checks).1
      rw [NativeSelectedVote.arithmeticKindRejected (eq ▸ arith)] at hc
      contradiction

/-- The actual byte scan, policy preparation and computed history all survive
composition; torn/unknown physical observations do not become successful recovery. -/
theorem observedWhole {sha policy initial raw snap final}
    (h : recoverObserved .whole sha policy initial raw snap = some final) :
    ∃ scan startup core, NativeWalScan.check sha raw = some scan ∧
      scan.torn = false ∧ scan.tail = [] ∧
      NativeReplayAdmission.prepareWhole sha policy initial = some startup ∧
      NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial = some core ∧
      History .whole sha policy snap ⟨core,[]⟩ (NativeWalScan.entries scan) final ∧
      final.core.sequence = (NativeWalScan.entries scan).length ∧ Unique final := by
  obtain ⟨scan,checked,torn,tail,recovered⟩ := observedComputed h
  obtain ⟨startup,core,prepared,seed,hist,_,_⟩ := recoveryComputed recovered
  exact ⟨scan,startup,core,checked,torn,tail,prepared,seed,hist,
    (recoveryCounts recovered).1,recoveryUnique recovered⟩

theorem incompleteRejected {mode sha policy initial raw snap scan}
    (parsed : NativeWalScan.check sha raw = some scan)
    (incomplete : scan.torn = true ∨ scan.tail ≠ []) :
    recoverObserved mode sha policy initial raw snap = none := by
  simp only [recoverObserved,parsed,bind,Option.bind]
  have bad : ¬ (scan.torn = false ∧ scan.tail = []) := by
    intro h; rcases incomplete with t | tail
    · rw [t] at h; cases h.1
    · exact tail h.2
  exact if_neg bad

/-- Successful exact retry returns a stored record whose complete original
policy/state was checked at its actual historical position, never today's state. -/
theorem retryWholeOrigin {sha policy initial snap log final raw stored}
    (recovered : recover .whole sha policy initial snap log = some final)
    (retried : retryVote sha final raw = some stored) :
    ∃ e ∈ log, ∃ prior x v id,
      VoteEntry .whole sha policy snap prior e x v id ∧
      NativeSelectedVote.Source sha policy prior.core.state e.command (facts prior e) x ∧
      encodeFrame stored.vote.wire = raw ∧
      stored = ⟨v,voteReceipt .whole x e v id,x.admitted.selected.original.parents⟩ := by
  have retry := retryOrigin retried
  obtain ⟨e,mem,prior,x,v,id,checks,record⟩ := recoveryVoteOrigin recovered retry.1
  exact ⟨e,mem,prior,x,v,id,checks,(entryWholeSource checks).1,retry.2.1,record⟩

end DeltaReduce.NativeWholeReplay
