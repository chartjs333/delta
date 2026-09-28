import DeltaReduce.NativeCacheHistory

/-! Executable lookup at an original mixed-WAL position. The preceding machine
is computed from the actual prefix; command positions do not become votes.
This is a diagnostic history view, not response exposure or public recovery. -/
namespace DeltaReduce.NativeHistoryRow
open NativeBinding NativeVoteCache
open NativeArithmeticJournal (Input)
open NativeConfigReplay (Machine)
variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

structure Located where
  prior : Machine
  input : Input (store := store) (trust := trust) adapter
  one : Result (store := store) (trust := trust) adapter
  row : Row (store := store) (trust := trust) adapter

def locate (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) :
    Machine → List (Input (store := store) (trust := trust) adapter) → Nat →
    Option (Located (store := store) (trust := trust) adapter)
  | _,[],_ => none
  | m,i::rest,n => do
    let one ← capture adapter policy snap m i
    match n with
    | 0 => match one.rows with
      | [row] => some ⟨m,i,one,row⟩
      | _ => none
    | n+1 => locate policy snap one.after rest n

theorem source {policy snap m log index out}
    (h : locate (store := store) (trust := trust) adapter policy snap m log index = some out) :
    ∃ pre suffix, log = pre ++ out.input::suffix ∧ pre.length = index ∧
      NativeArithmeticHistory.run adapter policy snap m pre = some out.prior ∧
      capture adapter policy snap out.prior out.input = some out.one ∧
      out.one.rows = [out.row] ∧ RowSource adapter policy snap out.prior out.input out.row := by
  induction log generalizing m index with
  | nil => simp [locate] at h
  | cons i rest ih =>
    simp only [locate,bind,Option.bind_eq_some_iff] at h
    obtain ⟨one,ho,last⟩ := h
    cases index with
    | zero =>
      dsimp only at last
      split at last <;> try contradiction
      rename_i row rows
      cases Option.some.inj last
      exact ⟨[],rest,rfl,rfl,rfl,ho,rows,(captured adapter ho).choose_spec.2.2.2.1 row (by rw [rows]; simp)⟩
    | succ n =>
      obtain ⟨pre,suffix,parts,len,before,step,rows,origin⟩ := ih last
      obtain ⟨next,hn,after,_,_,_⟩ := captured adapter ho
      exact ⟨i::pre,suffix,by simp only [parts,List.cons_append],by simp [len],
        by simp only [NativeArithmeticHistory.run,hn,← after,before,bind,Option.bind],step,rows,origin⟩

theorem inCompleteCache {policy snap m log result index out}
    (whole : NativeCacheHistory.run (store := store) (trust := trust) adapter policy snap m log = some result)
    (found : locate adapter policy snap m log index = some out) : out.row ∈ result.rows := by
  induction log generalizing m result index with
  | nil => simp [locate] at found
  | cons i rest ih =>
    obtain ⟨one,tail,ho,ht,rfl⟩ := NativeCacheHistory.consParts adapter whole
    simp only [locate,ho,bind,Option.bind] at found
    cases index with
    | zero =>
      dsimp only at found
      split at found <;> try contradiction
      rename_i row rows
      cases Option.some.inj found
      exact List.mem_append_left _ (by rw [rows]; simp)
    | succ n => exact List.mem_append_right _ (ih ht found)

theorem positionOriginal {policy snap m log index out}
    (h : locate (store := store) (trust := trust) adapter policy snap m log index = some out) :
    out.row.entry = out.input.entry ∧ out.row.beforeState = out.prior.core.state ∧
    out.row.ordinal = out.prior.votes.length+1 := by
  obtain ⟨_,_,_,_,_,_,_,origin⟩ := source adapter h
  exact ⟨origin.2.1,origin.2.2.1,origin.1⟩

theorem pastEnd {policy snap m log index} (past : log.length ≤ index) :
    locate (store := store) (trust := trust) adapter policy snap m log index = none := by
  cases h : locate adapter policy snap m log index with
  | none => rfl
  | some out =>
    obtain ⟨pre,suffix,parts,len,_,_,_,_⟩ := source adapter h
    rw [parts,List.length_append,List.length_cons,len] at past
    omega

structure Recovered (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (log : List (Input (store := store) (trust := trust) adapter)) (index : Nat) where
  cache : Result (store := store) (trust := trust) adapter
  complete : NativeCacheHistory.recover adapter policy initial snap log = some cache
  startup : NativeReplayAdmission.WholeStartup
  prepared : NativeReplayAdmission.prepareWhole adapter.sha256 policy initial = some startup
  core : NativeCommandReplay.Machine
  initialized : NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial = some core
  located : Located (store := store) (trust := trust) adapter
  computed : locate adapter policy snap ⟨core,[]⟩ log index = some located

def recoverAt (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (log : List (Input (store := store) (trust := trust) adapter)) (index : Nat) :
    Option (Recovered (store := store) (trust := trust) adapter policy initial snap log index) := do
  match complete : NativeCacheHistory.recover adapter policy initial snap log with
  | none => none
  | some cache =>
    match prepared : NativeReplayAdmission.prepareWhole adapter.sha256 policy initial with
    | none => none
    | some startup =>
      match initialized : NativeCommandReplay.initialMachine (some startup.policy.initialTick) snap initial with
      | none => none
      | some core =>
        match computed : locate adapter policy snap ⟨core,[]⟩ log index with
        | none => none
        | some located => some ⟨cache,complete,startup,prepared,core,initialized,located,computed⟩

theorem incompleteRejects {policy initial snap log index}
    (bad : NativeCacheHistory.recover (store := store) (trust := trust) adapter policy initial snap log = none) :
    recoverAt adapter policy initial snap log index = none := by
  unfold recoverAt
  split
  · rfl
  · rename_i cache found; rw [bad] at found; contradiction

theorem commandPositionRejects {policy snap m i rest one}
    (step : capture (store := store) (trust := trust) adapter policy snap m i = some one)
    (empty : one.rows = []) : locate adapter policy snap m (i::rest) 0 = none := by
  simp only [locate,step,bind,Option.bind,empty]

variable {policy initial snap log index}
    (recovered : Recovered (store := store) (trust := trust) adapter policy initial snap log index)

theorem sameCompleteRun : NativeCacheHistory.run adapter policy snap ⟨recovered.core,[]⟩ log = some recovered.cache := by
  obtain ⟨_,startup,core,prepared,initialized,executed,_,_⟩ := NativeCacheHistory.recoveryComputed adapter recovered.complete
  have same := Option.some.inj (prepared.symm.trans recovered.prepared)
  subst startup
  have same := Option.some.inj (initialized.symm.trans recovered.initialized)
  subst core
  exact executed

theorem locatedMember : recovered.located.row ∈ recovered.cache.rows :=
  inCompleteCache adapter (sameCompleteRun adapter recovered) recovered.computed

theorem originalSequences : recovered.located.row.entry.sequence = index+1 ∧
    recovered.located.row.ordinal = recovered.located.prior.votes.length+1 ∧
    recovered.located.row.entry.sequence = recovered.located.row.ordinal + recovered.located.prior.core.requests.length := by
  obtain ⟨pre,suffix,parts,len,before,one,_,origin⟩ := source adapter recovered.computed
  have hist := NativeArithmeticHistory.runSound adapter before
  have seq := NativeArithmeticHistory.historySequence adapter hist
  have counts := NativeArithmeticHistory.historyCounts adapter hist
  have init := NativeCommandReplay.initialShape recovered.initialized
  obtain ⟨next,step,_,_,_,_⟩ := captured adapter one
  have nextSeq := (NativeArithmeticJournal.stepSequence adapter step).1.symm.trans
    (NativeArithmeticJournal.stepSequence adapter step).2
  simp only [init.2.2.1,init.2.2.2.2.2.1,List.length_nil] at seq counts
  rw [origin.2.1] at ⊢
  exact ⟨by omega,origin.1,by rw [origin.1]; omega⟩

theorem completeNativeCache : recovered.cache.after.votes = recovered.cache.rows.map (native adapter) :=
  (NativeCacheHistory.recoveredCache adapter recovered.complete).1

end DeltaReduce.NativeHistoryRow
