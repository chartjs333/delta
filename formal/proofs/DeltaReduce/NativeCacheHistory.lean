import DeltaReduce.NativeVoteCache

/-! Complete ordered source cache, extensionally the same candidate replay.
Original mixed-WAL positions are retained beside separate all-vote ordinals. -/
namespace DeltaReduce.NativeCacheHistory
open NativeBinding NativeVoteCache
open NativeConfigReplay (Machine)
open NativeArithmeticJournal (Input)
variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

def run (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) :
    Machine → List (Input (store := store) (trust := trust) adapter) → Option (Result (store := store) (trust := trust) adapter)
  | m,[] => some ⟨m,[]⟩
  | m,i::rest => do
    let one ← capture adapter policy snap m i
    let tail ← run policy snap one.after rest
    some ⟨tail.after,one.rows ++ tail.rows⟩

variable {log : List (Input (store := store) (trust := trust) adapter)}

theorem consParts {policy snap m i rest result}
    (h : run (store := store) (trust := trust) adapter policy snap m (i::rest) = some result) :
    ∃ one tail, capture adapter policy snap m i = some one ∧ run adapter policy snap one.after rest = some tail ∧
      result = ⟨tail.after,one.rows ++ tail.rows⟩ := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨one,ho,tail,ht,last⟩ := h
  exact ⟨one,tail,ho,ht,(Option.some.inj last).symm⟩

theorem runOriginal {policy snap m result} (h : run adapter policy snap m log = some result) :
    NativeArithmeticHistory.run adapter policy snap m log = some result.after := by
  induction log generalizing m result with
  | nil => cases Option.some.inj h; rfl
  | cons i rest ih =>
    obtain ⟨one,tail,ho,ht,rfl⟩ := consParts adapter h
    obtain ⟨out,step,eq,_,_,_⟩ := captured adapter ho
    simp only [NativeArithmeticHistory.run,step,← eq,bind,Option.bind]
    exact ih ht

theorem complete {policy snap m final}
    (h : NativeArithmeticHistory.run adapter policy snap m log = some final) :
    ∃ result, run adapter policy snap m log = some result ∧ result.after = final := by
  have history := NativeArithmeticHistory.runSound adapter h
  clear h
  induction history with
  | nil => exact ⟨⟨_,[]⟩,rfl,rfl⟩
  | @cons m i out rest final hs ht ih =>
    obtain ⟨one,ho,eq,_,_,_⟩ := stepCapture adapter hs
    obtain ⟨tail,ht,done⟩ := ih
    refine ⟨⟨tail.after,one.rows ++ tail.rows⟩,?_,done⟩
    simp only [run,ho,bind,Option.bind,eq,ht]

theorem exactCache {policy snap m result} (h : run adapter policy snap m log = some result) :
    result.after.votes = m.votes ++ result.rows.map (native adapter) := by
  induction log generalizing m result with
  | nil => cases Option.some.inj h; simp
  | cons i rest ih =>
    obtain ⟨one,tail,ho,ht,rfl⟩ := consParts adapter h
    obtain ⟨_,_,_,cache,_,_⟩ := captured adapter ho
    change tail.after.votes = _
    rw [ih ht,cache]
    simp only [List.map_append,List.append_assoc]

theorem captureOrdinals {policy snap m i result}
    (h : capture (store := store) (trust := trust) adapter policy snap m i = some result) :
    result.rows.map Row.ordinal = List.range' (m.votes.length+1) result.rows.length := by
  obtain ⟨_,_,_,_,source,len⟩ := captured adapter h
  cases eq : result.rows with
  | nil => rfl
  | cons row rest =>
    have ordinal := (source row (by rw [eq]; simp)).1
    cases rest with
    | nil => simp [ordinal]
    | cons other tail => simp [eq] at len

theorem ordinals {policy snap m result} (h : run adapter policy snap m log = some result) :
    result.rows.map Row.ordinal = List.range' (m.votes.length+1) result.rows.length := by
  induction log generalizing m result with
  | nil => cases Option.some.inj h; rfl
  | cons i rest ih =>
    obtain ⟨one,tail,ho,ht,rfl⟩ := consParts adapter h
    have cache := (captured adapter ho).choose_spec.2.2.1
    have first := captureOrdinals adapter ho
    have next := ih ht
    have count : one.after.votes.length+1 = m.votes.length+1+one.rows.length := by
      rw [cache,List.length_append,List.length_map]; omega
    simp only [List.map_append,first,next,count,List.range'_append_1,List.length_append]

theorem rowPosition {policy snap m result} (h : run adapter policy snap m log = some result)
    {row} (member : row ∈ result.rows) :
    ∃ pre i suffix prior one,
      log = pre ++ i::suffix ∧ NativeArithmeticHistory.run adapter policy snap m pre = some prior ∧
      capture adapter policy snap prior i = some one ∧ row ∈ one.rows ∧ RowSource adapter policy snap prior i row ∧
      NativeArithmeticHistory.run adapter policy snap one.after suffix = some result.after := by
  induction log generalizing m result with
  | nil => cases Option.some.inj h; simp at member
  | cons i rest ih =>
    obtain ⟨one,tail,ho,ht,rfl⟩ := consParts adapter h
    obtain ⟨out,step,eq,_,source,_⟩ := captured adapter ho
    rcases List.mem_append.mp member with first | later
    · exact ⟨[],i,rest,m,one,rfl,rfl,ho,first,source row first,runOriginal adapter (result := tail) ht⟩
    · obtain ⟨pre,e,suffix,prior,next,logeq,before,hn,mem,hs,after⟩ := ih ht later
      refine ⟨i::pre,e,suffix,prior,next,?_,?_,hn,mem,hs,after⟩
      · simp only [logeq,List.cons_append]
      · simp only [NativeArithmeticHistory.run,step,← eq,before,bind,Option.bind]

def recover (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (log : List (Input (store := store) (trust := trust) adapter)) : Option (Result (store := store) (trust := trust) adapter) := do
  if NativeArithmeticHistory.zeroSnapshot initial snap then
    let startup ← NativeReplayAdmission.prepareWhole adapter.sha256 policy initial
    let core ← NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial
    let result ← run adapter policy snap ⟨core,[]⟩ log
    if result.after.core.matched = true ∧ (∀ s ∈ snap, s.sequence ≤ log.length) then some result else none
  else none

theorem recoveryComputed {policy initial snap result} (h : recover adapter policy initial snap log = some result) :
    NativeArithmeticHistory.zeroSnapshot initial snap ∧ ∃ startup core,
      NativeReplayAdmission.prepareWhole adapter.sha256 policy initial = some startup ∧
      NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial = some core ∧
      run adapter policy snap ⟨core,[]⟩ log = some result ∧ result.after.core.matched = true ∧
      (∀ s ∈ snap, s.sequence ≤ log.length) := by
  unfold recover at h
  split at h <;> try contradiction
  rename_i zero
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨startup,hp,core,hc,result,hr,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨zero,startup,core,hp,hc,hr,by assumption⟩

theorem recoveredOriginal {policy initial snap result} (h : recover adapter policy initial snap log = some result) :
    NativeArithmeticHistory.recover adapter policy initial snap log = some result.after := by
  obtain ⟨zero,startup,core,hp,hc,hr,checks⟩ := recoveryComputed adapter h
  exact NativeArithmeticHistory.recoveryFromComponents adapter zero hp hc (runOriginal adapter hr) checks

theorem recoveryComplete {policy initial snap final}
    (h : NativeArithmeticHistory.recover adapter policy initial snap log = some final) :
    ∃ result, recover adapter policy initial snap log = some result ∧ result.after = final := by
  obtain ⟨zero,startup,core,hp,hc,hist,checks⟩ := NativeArithmeticHistory.recoveryComputed adapter h
  obtain ⟨result,hr,eq⟩ := complete adapter (NativeArithmeticHistory.historyRun adapter hist)
  refine ⟨result,?_,eq⟩
  simp only [recover,if_pos zero,hp,hc,hr,bind,Option.bind,eq,if_pos checks]

theorem recoveredCache {policy initial snap result} (h : recover adapter policy initial snap log = some result) :
    result.after.votes = result.rows.map (native adapter) ∧
    result.rows.map Row.ordinal = List.range' 1 result.rows.length ∧
    result.after.core.requests.length + result.rows.length = log.length := by
  obtain ⟨_,_,core,_,_,hr,_,_⟩ := recoveryComputed adapter h
  have cache := exactCache adapter hr
  have numbered := ordinals adapter hr
  have counts := (NativeArithmeticHistory.recoveryCounts adapter (recoveredOriginal adapter h)).2
  simp only [List.nil_append] at cache
  rw [cache,List.length_map] at counts
  exact ⟨cache,numbered,counts⟩

/-- Neither number is rewritten. Their difference is exactly the number of
commands already executed at this actual historical position. -/
theorem positionMapping {policy initial snap result} (h : recover adapter policy initial snap log = some result)
    {row} (member : row ∈ result.rows) :
    ∃ core pre i suffix prior one,
      log = pre ++ i::suffix ∧ NativeArithmeticHistory.run adapter policy snap ⟨core,[]⟩ pre = some prior ∧
      capture adapter policy snap prior i = some one ∧ RowSource adapter policy snap prior i row ∧
      row.entry.sequence = pre.length+1 ∧ row.ordinal = prior.votes.length+1 ∧
      row.entry.sequence = row.ordinal + prior.core.requests.length := by
  obtain ⟨_,_,core,_,seed,hr,_,_⟩ := recoveryComputed adapter h
  obtain ⟨pre,i,suffix,prior,one,eq,before,ho,_,source,_⟩ := rowPosition adapter hr member
  obtain ⟨out,step,_,_,_,_⟩ := captured adapter ho
  have seq := (NativeArithmeticJournal.stepSequence adapter step).1.symm.trans
    (NativeArithmeticJournal.stepSequence adapter step).2
  have history := NativeArithmeticHistory.runSound adapter before
  have prefixSeq := NativeArithmeticHistory.historySequence adapter history
  have prefixCounts := NativeArithmeticHistory.historyCounts adapter history
  have shape := NativeCommandReplay.initialShape seed
  simp only [shape.2.2.1,shape.2.2.2.2.2.1,List.length_nil,Nat.zero_add] at prefixSeq prefixCounts
  refine ⟨core,pre,i,suffix,prior,one,eq,before,ho,source,?_,source.1,?_⟩
  · rw [source.2.1]; omega
  · rw [source.2.1,source.1]; omega

def recoverObserved (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (observation : Option Bytes) (sources : List (Option (NativeArithmeticJournal.Source codec store trust adapter.sha256))) :
    Option (Result (store := store) (trust := trust) adapter) := do
  let raw ← observation
  let scan ← NativeWalScan.check adapter.sha256 raw
  if scan.torn = false ∧ scan.tail = [] then
    let log ← NativeArithmeticHistory.align adapter (NativeWalScan.entries scan) sources
    recover adapter policy initial snap log
  else none

theorem observed {policy initial snap observation sources result}
    (h : recoverObserved (store := store) (trust := trust) adapter policy initial snap observation sources = some result) :
    ∃ raw scan log, observation = some raw ∧ NativeWalScan.check adapter.sha256 raw = some scan ∧
      scan.torn = false ∧ scan.tail = [] ∧ NativeArithmeticHistory.align adapter (NativeWalScan.entries scan) sources = some log ∧
      recover adapter policy initial snap log = some result := by
  unfold recoverObserved at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨raw,ho,scan,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i complete
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨log,ha,hr⟩ := last
  exact ⟨raw,scan,log,ho,hs,complete.1,complete.2,ha,hr⟩

theorem observedOriginal {policy initial snap observation sources result}
    (h : recoverObserved (store := store) (trust := trust) adapter policy initial snap observation sources = some result) :
    NativeArithmeticHistory.recoverObserved adapter policy initial snap observation sources = some result.after := by
  obtain ⟨raw,scan,log,ho,hs,torn,tail,ha,hr⟩ := observed adapter h
  have whole : scan.torn = false ∧ scan.tail = [] := ⟨torn,tail⟩
  simp only [NativeArithmeticHistory.recoverObserved,ho,hs,bind,Option.bind,if_pos whole,ha]
  exact recoveredOriginal adapter hr

theorem unknownRejects (policy initial snap sources) :
    recoverObserved (store := store) (trust := trust) adapter policy initial snap none sources = none := rfl

theorem observedComplete {policy initial snap observation sources final}
    (h : NativeArithmeticHistory.recoverObserved (store := store) (trust := trust) adapter policy initial snap observation sources = some final) :
    ∃ result, recoverObserved adapter policy initial snap observation sources = some result ∧ result.after = final := by
  obtain ⟨raw,scan,log,ho,hs,torn,tail,ha,hr⟩ := NativeArithmeticHistory.observed adapter h
  obtain ⟨result,hc,eq⟩ := recoveryComplete adapter hr
  have whole : scan.torn = false ∧ scan.tail = [] := ⟨torn,tail⟩
  exact ⟨result,by simp only [recoverObserved,ho,hs,bind,Option.bind,if_pos whole,ha,hc],eq⟩

end DeltaReduce.NativeCacheHistory
