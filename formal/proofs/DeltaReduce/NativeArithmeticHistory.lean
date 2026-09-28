import DeltaReduce.NativeArithmeticJournal

/-! Executed mixed candidate histories, with a checked source at every arithmetic
position. This remains a separate conditional replay candidate, not the guarded
runtime, authenticated physical observation, public refinement or exposure. -/
namespace DeltaReduce.NativeArithmeticHistory
open NativeBinding
open NativeArithmeticJournal
open NativeConfigReplay (Machine Stored)

variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

def run (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) :
    Machine → List (Input (store := store) (trust := trust) adapter) → Option Machine
  | m,[] => some m
  | m,i::rest => do
    let out ← step adapter policy snap m i
    run policy snap out.after rest

inductive History (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) :
    Machine → List (Input (store := store) (trust := trust) adapter) → Machine → Prop
  | nil (m) : History policy snap m [] m
  | cons {m i out rest final} : step adapter policy snap m i = some out →
      History policy snap out.after rest final → History policy snap m (i::rest) final

variable {log : List (Input (store := store) (trust := trust) adapter)}

theorem runSound {policy snap m final} (h : run adapter policy snap m log = some final) :
    History adapter policy snap m log final := by
  induction log generalizing m with
  | nil => cases Option.some.inj h; exact .nil _
  | cons i rest ih =>
    cases hs : step adapter policy snap m i with
    | none => simp [run,hs] at h
    | some out =>
      simp only [run,hs,bind,Option.bind] at h
      exact .cons hs (ih h)

theorem historyRun {policy snap m final} (h : History adapter policy snap m log final) :
    run adapter policy snap m log = some final := by
  induction h with
  | nil => rfl
  | cons hs _ ih => simp only [run,hs,ih,bind,Option.bind]

theorem historySequence {policy snap m final} (h : History adapter policy snap m log final) :
    final.core.sequence = m.core.sequence + log.length := by
  induction h with
  | nil => simp
  | cons hs _ ih => have seq := (stepSequence adapter hs).1; simp only [List.length_cons]; omega

theorem historyCounts {policy snap m final} (h : History adapter policy snap m log final) :
    final.core.requests.length + final.votes.length = m.core.requests.length + m.votes.length + log.length := by
  induction h with
  | nil => simp
  | cons hs _ ih => have counts := stepCounts adapter hs; simp only [List.length_cons]; omega

theorem historyUnique {policy snap m final} (h : History adapter policy snap m log final)
    (unique : NativeConfigReplay.Unique m) : NativeConfigReplay.Unique final := by
  induction h with
  | nil => exact unique
  | cons hs _ ih => exact ih (stepUnique adapter hs unique)

theorem historyClock {policy snap m final} (h : History adapter policy snap m log final) :
    m.core.tick ≤ final.core.tick ∧ (m.core.invalidated = true → final.core.invalidated = true) := by
  induction h with
  | nil => exact ⟨Nat.le_refl _,id⟩
  | cons hs _ ih =>
    have one := stepClock adapter hs
    exact ⟨Nat.le_trans one.1 ih.1,fun bad => ih.2 (one.2 bad)⟩

/-- Every stored vote is tied to its executed prefix and suffix, not just a
record of equal cardinality or a caller-chosen preceding machine. -/
theorem historyVotePosition {policy snap m final} (h : History adapter policy snap m log final)
    (vote : Stored) (mem : vote ∈ final.votes) :
    vote ∈ m.votes ∨ ∃ pre i suffix prior out,
      log = pre ++ i::suffix ∧ run adapter policy snap m pre = some prior ∧
      step adapter policy snap prior i = some out ∧ VoteCause adapter policy snap prior i vote ∧
      run adapter policy snap out.after suffix = some final := by
  induction h with
  | nil => exact Or.inl mem
  | @cons m i out rest final hs ht ih =>
    rcases ih mem with old | found
    · rcases stepVoteOrigin adapter hs vote old with old | cause
      · exact Or.inl old
      · exact Or.inr ⟨[],i,rest,m,out,rfl,rfl,hs,cause,historyRun adapter ht⟩
    · obtain ⟨pre,e,suffix,prior,next,eq,before,checks,cause,after⟩ := found
      refine Or.inr ⟨i::pre,e,suffix,prior,next,?_,?_,checks,cause,after⟩
      · simp only [eq,List.cons_append]
      · simp only [run,hs,before,bind,Option.bind]

/-- Exact positional decomposition for any input, including each repeated
arithmetic source. No first-arithmetic-only or finite-table premise occurs. -/
theorem historyPosition {policy snap m final} (h : History adapter policy snap m log final)
    {pre i suffix} (eq : log = pre ++ i::suffix) :
    ∃ prior out, run adapter policy snap m pre = some prior ∧
      step adapter policy snap prior i = some out ∧ run adapter policy snap out.after suffix = some final := by
  induction pre generalizing m log with
  | nil =>
    subst log
    cases h with
    | cons hs ht => exact ⟨_,_,rfl,hs,historyRun adapter ht⟩
  | cons head rest ih =>
    subst log
    cases h with
    | cons hs ht =>
      obtain ⟨prior,out,before,one,after⟩ := ih ht rfl
      exact ⟨prior,out,by simp only [run,hs,before,bind,Option.bind],one,after⟩

theorem arithmeticPosition {policy snap m final} (h : History adapter policy snap m log final)
    {pre i suffix} (eq : log = pre ++ i::suffix) {s} (source : i.source = some s) :
    ∃ prior x, run adapter policy snap m pre = some prior ∧
      Checked adapter policy snap prior i.entry s x ∧
      run adapter policy snap (added adapter snap prior i.entry x) suffix = some final ∧
      i.entry.sequence = m.core.sequence + pre.length + 1 := by
  obtain ⟨prior,out,before,one,after⟩ := historyPosition adapter h eq
  rcases stepSource adapter one with ⟨none,_,_⟩ | ⟨other,x,same,computed,rfl⟩
  · rw [source] at none; contradiction
  · rw [source] at same
    cases Option.some.inj same
    have check := checked adapter computed
    have seq := historySequence adapter (runSound adapter before)
    have pos := check.position
    exact ⟨prior,x,before,check,after,by omega⟩

/-- Extra zero-snapshot identity is a candidate restriction: the legacy initial
machine marks position zero without itself comparing the two state byte lists. -/
def zeroSnapshot (initial : Bytes) (snap : Option NativeCommandReplay.Snapshot) : Prop :=
  ∀ s ∈ snap, s.sequence = 0 → s.state = initial

instance (initial : Bytes) (snap : Option NativeCommandReplay.Snapshot) : Decidable (zeroSnapshot initial snap) :=
  inferInstanceAs (Decidable (∀ s ∈ snap, s.sequence = 0 → s.state = initial))

def recover (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (log : List (Input (store := store) (trust := trust) adapter)) : Option Machine := do
  if zeroSnapshot initial snap then
    let startup ← NativeReplayAdmission.prepareWhole adapter.sha256 policy initial
    let core ← NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial
    let final ← run adapter policy snap ⟨core,[]⟩ log
    if final.core.matched = true ∧ (∀ s ∈ snap, s.sequence ≤ log.length) then some final else none
  else none

theorem recoveryComputed {policy initial snap final} (h : recover adapter policy initial snap log = some final) :
    zeroSnapshot initial snap ∧ ∃ startup core,
      NativeReplayAdmission.prepareWhole adapter.sha256 policy initial = some startup ∧
      NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial = some core ∧
      History adapter policy snap ⟨core,[]⟩ log final ∧ final.core.matched = true ∧
      (∀ s ∈ snap, s.sequence ≤ log.length) := by
  unfold recover at h
  split at h <;> try contradiction
  rename_i zero
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨startup,hp,core,hc,out,hr,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨zero,startup,core,hp,hc,runSound adapter hr,checks⟩

theorem recoveryFromComponents {policy initial snap startup core final}
    (zero : zeroSnapshot initial snap)
    (hp : NativeReplayAdmission.prepareWhole adapter.sha256 policy initial = some startup)
    (hc : NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial = some core)
    (hr : run adapter policy snap ⟨core,[]⟩ log = some final)
    (checks : final.core.matched = true ∧ (∀ s ∈ snap, s.sequence ≤ log.length)) :
    recover adapter policy initial snap log = some final := by
  simp only [recover,if_pos zero,hp,hc,hr,bind,Option.bind]
  exact if_pos checks

theorem recoveryCounts {policy initial snap final} (h : recover adapter policy initial snap log = some final) :
    final.core.sequence = log.length ∧ final.core.requests.length + final.votes.length = log.length := by
  obtain ⟨_,_,core,_,seed,hist,_,_⟩ := recoveryComputed adapter h
  have shape := NativeCommandReplay.initialShape seed
  simpa [shape.2.2.1,shape.2.2.2.2.2.1] using
    And.intro (historySequence adapter hist) (historyCounts adapter hist)

theorem recoveryUnique {policy initial snap final} (h : recover adapter policy initial snap log = some final) :
    NativeConfigReplay.Unique final := by
  obtain ⟨_,_,core,_,seed,hist,_,_⟩ := recoveryComputed adapter h
  apply historyUnique adapter hist
  simp [NativeConfigReplay.Unique,NativeCommandReplay.UniqueRequests,(NativeCommandReplay.initialShape seed).2.2.2.2.2.1]

theorem historySnapshot {policy s m final} (h : History adapter policy (some s) m log final)
    (matched : final.core.matched = true) :
    m.core.matched = true ∨ ∃ pre i suffix prior out,
      log = pre ++ i::suffix ∧ run adapter policy (some s) m pre = some prior ∧
      step adapter policy (some s) prior i = some out ∧ i.entry.sequence = s.sequence ∧
      out.after.core.state = s.state ∧ run adapter policy (some s) out.after suffix = some final := by
  induction h with
  | nil => exact Or.inl matched
  | @cons m i out rest final hs ht ih =>
    rcases ih matched with old | found
    · have guard := stepSnapshot adapter hs
      rw [guard.2,Bool.or_eq_true] at old
      rcases old with old | mark
      · exact Or.inl old
      · have seq : i.entry.sequence = s.sequence := by simpa [NativeCommandReplay.mark] using mark
        exact Or.inr ⟨[],i,rest,m,out,rfl,rfl,hs,seq,guard.1 s (by simp) seq,historyRun adapter ht⟩
    · obtain ⟨pre,entry,suffix,prior,next,eq,before,one,seq,state,after⟩ := found
      refine Or.inr ⟨i::pre,entry,suffix,prior,next,?_,?_,one,seq,state,after⟩
      · simp only [eq,List.cons_append]
      · simp only [run,hs,before,bind,Option.bind]

theorem positiveSnapshot {policy initial s final}
    (h : recover adapter policy initial (some s) log = some final) (positive : s.sequence ≠ 0) :
    ∃ core pre i suffix prior out,
      log = pre ++ i::suffix ∧ run adapter policy (some s) ⟨core,[]⟩ pre = some prior ∧
      step adapter policy (some s) prior i = some out ∧ i.entry.sequence = s.sequence ∧
      out.after.core.state = s.state ∧ run adapter policy (some s) out.after suffix = some final := by
  obtain ⟨_,_,core,_,seed,hist,matched,_⟩ := recoveryComputed adapter h
  rcases historySnapshot adapter hist matched with old | found
  · rw [(NativeCommandReplay.initialShape seed).2.2.2.2.2.2] at old
    simp [NativeCommandReplay.initialMatch,positive] at old
  · exact ⟨core,found⟩

theorem recoveredVotePosition {policy initial snap final vote}
    (h : recover adapter policy initial snap log = some final) (mem : vote ∈ final.votes) :
    ∃ startup core pre i suffix prior out,
      NativeReplayAdmission.prepareWhole adapter.sha256 policy initial = some startup ∧
      NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial = some core ∧
      log = pre ++ i::suffix ∧ run adapter policy snap ⟨core,[]⟩ pre = some prior ∧
      step adapter policy snap prior i = some out ∧ VoteCause adapter policy snap prior i vote ∧
      run adapter policy snap out.after suffix = some final := by
  obtain ⟨_,startup,core,hp,hc,hist,_,_⟩ := recoveryComputed adapter h
  rcases historyVotePosition adapter hist vote mem with old | found
  · exact False.elim (List.not_mem_nil old)
  · obtain ⟨pre,i,suffix,prior,out,eq,before,one,cause,after⟩ := found
    exact ⟨startup,core,pre,i,suffix,prior,out,hp,hc,eq,before,one,cause,after⟩

/-- Existing exact retry remains a read-only historical cache lookup. -/
theorem retryPosition {policy initial snap final raw vote}
    (h : recover adapter policy initial snap log = some final)
    (retry : NativeConfigReplay.retryVote adapter.sha256 final raw = some vote) :
    NativeVoteBytes.encodeFrame vote.vote.wire = raw ∧ ∃ startup core pre i suffix prior out,
      NativeReplayAdmission.prepareWhole adapter.sha256 policy initial = some startup ∧
      NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial = some core ∧
      log = pre ++ i::suffix ∧ run adapter policy snap ⟨core,[]⟩ pre = some prior ∧
      step adapter policy snap prior i = some out ∧ VoteCause adapter policy snap prior i vote ∧
      run adapter policy snap out.after suffix = some final := by
  have origin := NativeConfigReplay.retryOrigin retry
  exact ⟨origin.2.1,recoveredVotePosition adapter h origin.1⟩

/-- Positional zip is total only at equal lengths; no source or WAL suffix is
dropped. The retained sources themselves are proof-bearing actual loaders. -/
def align : List NativeWalBytes.Entry → List (Option (Source codec store trust adapter.sha256)) →
    Option (List (Input (store := store) (trust := trust) adapter))
  | [],[] => some []
  | e::es,s::ss => (align es ss).map (fun rest => ⟨e,s⟩::rest)
  | _,_ => none

theorem aligned {entries sources} (h : align adapter entries sources = some log) :
    log.map Input.entry = entries ∧ log.map Input.source = sources := by
  induction entries generalizing sources log with
  | nil => cases sources <;> simp_all [align]
  | cons e es ih =>
    cases sources with
    | nil => simp [align] at h
    | cons s ss =>
      obtain ⟨rest,hr,eq⟩ := Option.map_eq_some_iff.mp h
      subst log
      have tail := ih hr
      exact ⟨by simp [tail.1],by simp [tail.2]⟩

def recoverObserved (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (observation : Option Bytes) (sources : List (Option (Source codec store trust adapter.sha256))) : Option Machine := do
  let raw ← observation
  let scan ← NativeWalScan.check adapter.sha256 raw
  if scan.torn = false ∧ scan.tail = [] then
    let log ← align adapter (NativeWalScan.entries scan) sources
    recover adapter policy initial snap log
  else none

theorem observed {policy initial snap observation sources final}
    (h : recoverObserved (store := store) (trust := trust) adapter policy initial snap observation sources = some final) :
    ∃ raw scan log, observation = some raw ∧ NativeWalScan.check adapter.sha256 raw = some scan ∧
      scan.torn = false ∧ scan.tail = [] ∧ align adapter (NativeWalScan.entries scan) sources = some log ∧
      recover adapter policy initial snap log = some final := by
  unfold recoverObserved at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨raw,ho,scan,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i complete
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨log,ha,hr⟩ := last
  exact ⟨raw,scan,log,ho,hs,complete.1,complete.2,ha,hr⟩

theorem observedOriginal {policy initial snap observation sources final}
    (h : recoverObserved (store := store) (trust := trust) adapter policy initial snap observation sources = some final) :
    ∃ raw scan log, observation = some raw ∧ NativeWalScan.check adapter.sha256 raw = some scan ∧
      raw = NativeWalScan.joined scan.pieces ∧ log.map Input.entry = NativeWalScan.entries scan ∧
      log.map Input.source = sources ∧ recover adapter policy initial snap log = some final ∧
      final.core.sequence = sources.length := by
  obtain ⟨raw,scan,log,ho,hs,_,tail,ha,hr⟩ := observed adapter h
  have aligned := aligned adapter ha
  have partition := NativeWalScan.checkedPartition adapter.sha256 raw scan hs
  rw [tail,List.append_nil] at partition
  have len : log.length = sources.length := by rw [← aligned.2,List.length_map]
  exact ⟨raw,scan,log,ho,hs,partition,aligned.1,aligned.2,hr,(recoveryCounts adapter hr).1.trans len⟩

theorem unknownRejects (policy initial snap sources) :
    recoverObserved (store := store) (trust := trust) adapter policy initial snap none sources = none := rfl

theorem incompleteRejects {policy initial snap raw sources scan}
    (parsed : NativeWalScan.check adapter.sha256 raw = some scan)
    (bad : scan.torn = true ∨ scan.tail ≠ []) :
    recoverObserved (store := store) (trust := trust) adapter policy initial snap (some raw) sources = none := by
  simp only [recoverObserved,parsed,bind,Option.bind]
  apply if_neg
  intro complete
  rcases bad with torn | tail
  · rw [torn] at complete; cases complete.1
  · exact tail complete.2

theorem zeroSnapshotRejects {policy initial snap} (bad : ¬ zeroSnapshot initial snap) :
    recover adapter policy initial snap log = none := by simp [recover,bad]

theorem wrongSourceCount {entries sources}
    (bad : entries.length ≠ sources.length) :
    align (store := store) (trust := trust) adapter entries sources = none := by
  cases h : align adapter entries sources with
  | none => rfl
  | some log =>
    have same := aligned adapter h
    have a := congrArg List.length same.1
    have b := congrArg List.length same.2
    simp only [List.length_map] at a b
    exact False.elim (bad (a.symm.trans b))

theorem corruptRejects {policy initial snap raw sources}
    (bad : NativeWalScan.check adapter.sha256 raw = none) :
    recoverObserved (store := store) (trust := trust) adapter policy initial snap (some raw) sources = none := by
  simp [recoverObserved,bad]

end DeltaReduce.NativeArithmeticHistory
