import DeltaReduce.NativeTransition

/-! Checked command replay, original receipt caches and snapshot comparison.
Votes reject: this is not a replacement for the mixed native runtime history.
Optional clock input denotes the primitive initial tick of an independently
validated startup vote policy; it does not authenticate or decode that policy.
No successful function here grants physical durability, readiness or exposure. -/
namespace DeltaReduce.NativeCommandReplay
open NativeReceiptBytes NativeVoteBytes NativeStateBytes NativeTransition

structure Receipt where
  state : Bytes
  effects : Bytes
  record : Bytes
  nextId : Bytes
  effectsId : Bytes
  recordId : Bytes
  sequence : Nat
  replay : Bool
  deriving DecidableEq, Repr

structure Cached where
  request : Bytes
  commandId : Bytes
  receipt : Receipt
  deriving DecidableEq, Repr

structure Snapshot where
  sequence : Nat
  state : Bytes
  deriving DecidableEq, Repr

structure Machine where
  state : Bytes
  sequence : Nat
  tick : Nat
  invalidated : Bool
  requests : List Cached
  matched : Bool
  deriving DecidableEq, Repr

def cached (e : NativeWalBytes.Entry) (c : Command) (out : Output) : Cached :=
  ⟨c.wire.request,out.commandId,
    ⟨e.state,e.effects,e.record,out.nextId,out.effectsId,out.recordId,e.sequence,false⟩⟩

def initialMatch : Option Snapshot → Bool
  | none => true | some s => s.sequence == 0

def snapshotGuard (snap : Option Snapshot) (e : NativeWalBytes.Entry) : Prop :=
  ∀ s ∈ snap, e.sequence = s.sequence → e.state = s.state
instance (snap e) : Decidable (snapshotGuard snap e) := by
  cases snap <;> simp only [snapshotGuard,Option.mem_def] <;> infer_instance

def mark (snap : Option Snapshot) (e : NativeWalBytes.Entry) : Bool :=
  match snap with | none => false | some s => e.sequence == s.sequence

def clockGuard (clock : Option Nat) (m : Machine) (c : Command) : Prop :=
  clock.isSome = true → m.tick ≤ c.tick
instance (clock m c) : Decidable (clockGuard clock m c) := by unfold clockGuard; infer_instance

def fresh (m : Machine) (c : Command) : Prop :=
  ∀ r ∈ m.requests, r.request ≠ c.wire.request
instance (m c) : Decidable (fresh m c) := by unfold fresh; infer_instance

def updated (clock : Option Nat) (snap : Option Snapshot) (m : Machine)
    (e : NativeWalBytes.Entry) (c : Command) (out : Output) : Machine :=
  ⟨e.state,e.sequence,if clock.isSome then c.tick else m.tick,
    if clock.isSome then true else m.invalidated,
    m.requests ++ [cached e c out],m.matched || mark snap e⟩

def initialMachine (clock : Option Nat) (snap : Option Snapshot) (raw : Bytes) : Option Machine := do
  let _ ← decodeState raw
  if (∀ t ∈ clock, t < 256^8) ∧ (∀ s ∈ snap, s.sequence < 256^8) then
    match snap with
    | some s => do
      let _ ← decodeState s.state
      some ⟨raw,0,clock.getD 0,false,[],initialMatch snap⟩
    | none => some ⟨raw,0,clock.getD 0,false,[],true⟩
  else none

def step (sha : Bytes → Bytes) (clock : Option Nat) (snap : Option Snapshot)
    (m : Machine) (e : NativeWalBytes.Entry) : Option Machine := do
  if e.kind = 1 ∧ e.sequence = m.sequence+1 ∧ e.sequence < 256^8 then
    let c ← decodeCommand e.command
    if clockGuard clock m c then
      let out ← replayEntry sha m.state e
      if fresh m c ∧ snapshotGuard snap e then some (updated clock snap m e c out) else none
    else none
  else none

theorem initialShape {clock snap raw m} (h : initialMachine clock snap raw = some m) :
    (∃ s, decodeState raw = some s) ∧ m.state = raw ∧ m.sequence = 0 ∧
    m.tick = clock.getD 0 ∧ m.invalidated = false ∧ m.requests = [] ∧
    m.matched = initialMatch snap := by
  unfold initialMachine at h
  cases hs : decodeState raw with
  | none => simp [hs] at h
  | some s =>
    simp only [hs,bind,Option.bind] at h
    split at h <;> try contradiction
    cases snap with
    | none => cases Option.some.inj h; exact ⟨⟨s,rfl⟩,rfl,rfl,rfl,rfl,rfl,rfl⟩
    | some snap =>
      cases hd : decodeState snap.state with
      | none => simp [hd] at h
      | some state =>
        simp only [hd] at h
        cases Option.some.inj h
        exact ⟨⟨s,rfl⟩,rfl,rfl,rfl,rfl,rfl,rfl⟩

def Admitted (sha : Bytes → Bytes) (clock : Option Nat) (snap : Option Snapshot)
    (m : Machine) (e : NativeWalBytes.Entry) (c : Command) (out : Output) : Prop :=
  e.kind = 1 ∧ e.sequence = m.sequence+1 ∧ e.sequence < 256^8 ∧
  decodeCommand e.command = some c ∧ clockGuard clock m c ∧
  replayEntry sha m.state e = some out ∧ fresh m c ∧ snapshotGuard snap e

theorem stepSound {sha clock snap m e n} (ok : step sha clock snap m e = some n) :
    ∃ c out, Admitted sha clock snap m e c out ∧ n = updated clock snap m e c out := by
  unfold step at ok
  split at ok <;> try contradiction
  rename_i position
  cases hc : decodeCommand e.command with
  | none => simp [hc] at ok
  | some c =>
    simp only [hc,bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i time
    cases ho : replayEntry sha m.state e with
    | none => simp [ho] at ok
    | some out =>
      simp only [ho] at ok
      split at ok <;> try contradiction
      rename_i guards
      exact ⟨c,out,⟨position.1,position.2.1,position.2.2,hc,time,ho,guards⟩,Option.some.inj ok.symm⟩

theorem stepFromComponents (sha clock snap m e c out)
    (h : Admitted sha clock snap m e c out) :
    step sha clock snap m e = some (updated clock snap m e c out) := by
  obtain ⟨kind,seq,bound,decoded,time,computed,unique,snapshot⟩ := h
  simp only [step,if_pos (And.intro kind (And.intro seq bound)),decoded,bind,Option.bind,if_pos time,computed,if_pos (And.intro unique snapshot)]

theorem voteRejected (sha clock snap m e) (vote : e.kind ≠ 1) : step sha clock snap m e = none := by
  simp [step,vote]

theorem wrongPositionRejected (sha clock snap m e) (bad : e.sequence ≠ m.sequence+1) :
    step sha clock snap m e = none := by simp [step,bad]

theorem oldClockRejected (sha clock snap m e c)
    (parsed : decodeCommand e.command = some c) (bad : ¬ clockGuard clock m c) :
    step sha clock snap m e = none := by simp [step,parsed,bad]

theorem duplicateRejected (sha clock snap m e c)
    (parsed : decodeCommand e.command = some c) (bad : ¬ fresh m c) :
    step sha clock snap m e = none := by
  simp only [step,parsed,bind,Option.bind]
  split <;> try rfl
  split <;> try rfl
  cases replayEntry sha m.state e <;> simp [bad]

theorem wrongSnapshotRejected (sha clock snap m e) (bad : ¬ snapshotGuard snap e) :
    step sha clock snap m e = none := by
  unfold step
  split <;> try rfl
  cases decodeCommand e.command with
  | none => rfl
  | some c =>
    simp only [bind,Option.bind]
    split <;> try rfl
    cases replayEntry sha m.state e <;> simp [bad]

theorem stepSequence {sha clock snap m e n} (h : step sha clock snap m e = some n) :
    n.sequence = m.sequence+1 ∧ e.sequence = n.sequence := by
  obtain ⟨c,out,a,rfl⟩ := stepSound h
  exact ⟨a.2.1,rfl⟩

theorem stepCache {sha clock snap m e n} (h : step sha clock snap m e = some n) :
    ∃ c out, decodeCommand e.command = some c ∧ replayEntry sha m.state e = some out ∧
      fresh m c ∧ n.requests = m.requests ++ [cached e c out] ∧ n.state = e.state := by
  obtain ⟨c,out,a,rfl⟩ := stepSound h
  exact ⟨c,out,a.2.2.2.1,a.2.2.2.2.2.1,a.2.2.2.2.2.2.1,rfl,rfl⟩

theorem stepClock {sha clock snap m e n} (h : step sha clock snap m e = some n)
    (active : clock.isSome = true) : m.tick ≤ n.tick ∧ n.invalidated = true := by
  obtain ⟨c,out,a,rfl⟩ := stepSound h
  simpa [updated,active] using a.2.2.2.2.1 active

theorem stepSnapshot {sha clock snap m e n} (h : step sha clock snap m e = some n) :
    snapshotGuard snap e ∧ n.matched = (m.matched || mark snap e) := by
  obtain ⟨c,out,a,rfl⟩ := stepSound h
  exact ⟨a.2.2.2.2.2.2.2,rfl⟩

theorem originalReceipt (e c out) :
    (cached e c out).receipt.state = e.state ∧
    (cached e c out).receipt.effects = e.effects ∧
    (cached e c out).receipt.record = e.record ∧
    (cached e c out).receipt.sequence = e.sequence ∧
    (cached e c out).receipt.replay = false := ⟨rfl,rfl,rfl,rfl,rfl⟩

def run (sha : Bytes → Bytes) (clock : Option Nat) (snap : Option Snapshot) :
    Machine → List NativeWalBytes.Entry → Option Machine
  | m, [] => some m
  | m, e::rest => do
    let n ← step sha clock snap m e
    run sha clock snap n rest

inductive History (sha : Bytes → Bytes) (clock : Option Nat) (snap : Option Snapshot) :
    Machine → List NativeWalBytes.Entry → Machine → Prop where
  | nil (m) : History sha clock snap m [] m
  | cons {m e n rest final} : step sha clock snap m e = some n →
      History sha clock snap n rest final → History sha clock snap m (e::rest) final

theorem runSound {sha clock snap m log final} (h : run sha clock snap m log = some final) :
    History sha clock snap m log final := by
  induction log generalizing m with
  | nil => cases Option.some.inj h; exact .nil _
  | cons e rest ih =>
    simp only [run] at h
    cases hs : step sha clock snap m e with
    | none => simp [hs] at h
    | some n =>
      simp only [hs,bind,Option.bind] at h
      exact .cons hs (ih h)

theorem historySequence {sha clock snap m log final} (h : History sha clock snap m log final) :
    final.sequence = m.sequence + log.length := by
  induction h with
  | nil => simp
  | cons hs _ ih => have seq := (stepSequence hs).1; simp only [List.length_cons]; omega

theorem historyCacheExtension {sha clock snap m log final} (h : History sha clock snap m log final) :
    ∃ suffix, final.requests = m.requests ++ suffix ∧ suffix.length = log.length := by
  induction h with
  | nil => exact ⟨[],by simp, rfl⟩
  | cons hs _ ih =>
    obtain ⟨c,out,_,_,_,cache,_⟩ := stepCache hs
    obtain ⟨suffix,eq,len⟩ := ih
    exact ⟨cached _ c out :: suffix,by simpa [cache,List.append_assoc] using eq,by simp [len]⟩

theorem historyRecordOrigin {sha clock snap m log final} (h : History sha clock snap m log final)
    (r : Cached) (member : r ∈ final.requests) :
    r ∈ m.requests ∨ ∃ e ∈ log, ∃ prior c out,
      decodeCommand e.command = some c ∧ replayEntry sha prior e = some out ∧ r = cached e c out := by
  induction h with
  | nil => exact Or.inl member
  | cons hs _ ih =>
    rcases ih member with old | ⟨e,em,prior,c,out,decoded,computed,same⟩
    · obtain ⟨c,out,decoded,computed,_,cache,_⟩ := stepCache hs
      rw [cache,List.mem_append] at old
      rcases old with old | added
      · exact Or.inl old
      · exact Or.inr ⟨_,by simp,_,c,out,decoded,computed,by simpa using added⟩
    · exact Or.inr ⟨e,List.mem_cons_of_mem _ em,prior,c,out,decoded,computed,same⟩

theorem historyClock {sha clock snap m log final} (h : History sha clock snap m log final)
    (active : clock.isSome = true) : m.tick ≤ final.tick := by
  induction h with
  | nil => exact Nat.le_refl _
  | cons hs _ ih => exact Nat.le_trans (stepClock hs active).1 ih

def UniqueRequests (m : Machine) : Prop :=
  m.requests.Pairwise (fun a b => a.request ≠ b.request)

theorem stepUnique {sha clock snap m e n} (h : step sha clock snap m e = some n)
    (unique : UniqueRequests m) : UniqueRequests n := by
  obtain ⟨c,out,_,_,fresh,cache,_⟩ := stepCache h
  unfold UniqueRequests
  rw [cache,List.pairwise_append]
  refine ⟨unique,by simp,?_⟩
  intro a am b bm
  have same : b = cached e c out := by simpa using bm
  subst b
  exact fresh a am

theorem historyUnique {sha clock snap m log final} (h : History sha clock snap m log final)
    (unique : UniqueRequests m) : UniqueRequests final := by
  induction h with
  | nil => exact unique
  | cons hs _ ih => exact ih (stepUnique hs unique)

theorem historySnapshot {sha clock s m log final} (h : History sha clock (some s) m log final)
    (matched : final.matched = true) :
    m.matched = true ∨ ∃ e ∈ log, e.sequence = s.sequence ∧ e.state = s.state := by
  induction h with
  | nil => exact Or.inl matched
  | @cons m e n rest final hs hist ih =>
    rcases ih matched with old | found
    · have guard := stepSnapshot hs
      rw [guard.2,Bool.or_eq_true] at old
      rcases old with old | marked
      · exact Or.inl old
      · have seq : e.sequence = s.sequence := by simpa [mark] using marked
        exact Or.inr ⟨_,by simp,seq,guard.1 s (by simp) seq⟩
    · obtain ⟨e,em,seq,state⟩ := found
      exact Or.inr ⟨e,List.mem_cons_of_mem _ em,seq,state⟩

def recover (sha : Bytes → Bytes) (clock : Option Nat) (snap : Option Snapshot)
    (initial : Bytes) (log : List NativeWalBytes.Entry) : Option Machine := do
  let m ← initialMachine clock snap initial
  let final ← run sha clock snap m log
  if final.matched = true ∧ (∀ s ∈ snap, s.sequence ≤ log.length) then some final else none

theorem recoveryComputed {sha clock snap initial log final}
    (h : recover sha clock snap initial log = some final) :
    ∃ m, initialMachine clock snap initial = some m ∧ History sha clock snap m log final ∧
      final.matched = true ∧ (∀ s ∈ snap, s.sequence ≤ log.length) := by
  unfold recover at h
  cases hi : initialMachine clock snap initial with
  | none => simp [hi] at h
  | some m =>
    simp only [hi,bind,Option.bind] at h
    cases hr : run sha clock snap m log with
    | none => simp [hr] at h
    | some n =>
      simp only [hr] at h
      split at h <;> try contradiction
      rename_i checks
      cases Option.some.inj h
      exact ⟨m,rfl,runSound hr,checks⟩

theorem recoverySequence {sha clock snap initial log final}
    (h : recover sha clock snap initial log = some final) :
    final.sequence = log.length ∧ final.requests.length = log.length := by
  obtain ⟨m,seed,hist,_,_⟩ := recoveryComputed h
  have shape := initialShape seed
  have seq := historySequence hist
  obtain ⟨suffix,cache,len⟩ := historyCacheExtension hist
  constructor
  · simpa [shape.2.2.1] using seq
  · simpa [cache,shape.2.2.2.2.2.1] using len

theorem recoveryRecordOrigin {sha clock snap initial log final}
    (h : recover sha clock snap initial log = some final) (r : Cached) (member : r ∈ final.requests) :
    ∃ e ∈ log, ∃ prior c out, decodeCommand e.command = some c ∧
      replayEntry sha prior e = some out ∧ r = cached e c out := by
  obtain ⟨m,seed,hist,_,_⟩ := recoveryComputed h
  rcases historyRecordOrigin hist r member with old | found
  · simp [(initialShape seed).2.2.2.2.2.1] at old
  · exact found

theorem recoveryUnique {sha clock snap initial log final}
    (h : recover sha clock snap initial log = some final) : UniqueRequests final := by
  obtain ⟨m,seed,hist,_,_⟩ := recoveryComputed h
  apply historyUnique hist
  simp [UniqueRequests,(initialShape seed).2.2.2.2.2.1]

theorem positiveSnapshotOrigin {sha clock s initial log final}
    (h : recover sha clock (some s) initial log = some final) (positive : s.sequence ≠ 0) :
    ∃ e ∈ log, e.sequence = s.sequence ∧ e.state = s.state := by
  obtain ⟨m,seed,hist,matched,_⟩ := recoveryComputed h
  rcases historySnapshot hist matched with old | found
  · rw [(initialShape seed).2.2.2.2.2.2] at old
    simp [initialMatch,positive] at old
  · exact found

def recoverObserved (sha : Bytes → Bytes) (clock : Option Nat) (snap : Option Snapshot)
    (initial raw : Bytes) : Option Machine := do
  let scan ← NativeWalScan.check sha raw
  if scan.torn = false ∧ scan.tail = [] then
    recover sha clock snap initial (NativeWalScan.entries scan)
  else none

theorem observedRecovery {sha clock snap initial raw final}
    (ok : recoverObserved sha clock snap initial raw = some final) :
    ∃ scan, NativeWalScan.check sha raw = some scan ∧ scan.torn = false ∧ scan.tail = [] ∧
      recover sha clock snap initial (NativeWalScan.entries scan) = some final := by
  unfold recoverObserved at ok
  cases hs : NativeWalScan.check sha raw with
  | none => simp [hs] at ok
  | some scan =>
    simp only [hs,bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i complete
    exact ⟨scan,rfl,complete.1,complete.2,ok⟩

def retry (sha : Bytes → Bytes) (m : Machine) (raw : Bytes) : Option Receipt := do
  let c ← decodeCommand raw
  let id ← contentId sha commandDomain raw
  let old ← m.requests.find? (fun r => r.request == c.wire.request)
  if old.commandId = id then some {old.receipt with replay := true} else none

theorem retryFromCache (sha m raw c id old)
    (parsed : decodeCommand raw = some c) (hashed : contentId sha commandDomain raw = some id)
    (found : m.requests.find? (fun r => r.request == c.wire.request) = some old)
    (same : old.commandId = id) : retry sha m raw = some {old.receipt with replay := true} := by
  simp [retry,parsed,hashed,found,same]

theorem retryConflict (sha m raw c id old)
    (parsed : decodeCommand raw = some c) (hashed : contentId sha commandDomain raw = some id)
    (found : m.requests.find? (fun r => r.request == c.wire.request) = some old)
    (different : old.commandId ≠ id) : retry sha m raw = none := by
  simp [retry,parsed,hashed,found,different]

theorem retryOrigin {sha m raw receipt} (ok : retry sha m raw = some receipt) :
    ∃ c id old, decodeCommand raw = some c ∧ contentId sha commandDomain raw = some id ∧
      old ∈ m.requests ∧ old.request = c.wire.request ∧ old.commandId = id ∧
      receipt = {old.receipt with replay := true} := by
  unfold retry at ok
  cases hc : decodeCommand raw with
  | none => simp [hc] at ok
  | some c =>
    simp only [hc,bind,Option.bind] at ok
    cases hh : contentId sha commandDomain raw with
    | none => simp [hh] at ok
    | some id =>
      simp only [hh] at ok
      cases hf : m.requests.find? (fun r => r.request == c.wire.request) with
      | none => simp [hf] at ok
      | some old =>
        simp only [hf] at ok
        split at ok <;> try contradiction
        rename_i same
        exact ⟨c,id,old,rfl,rfl,List.mem_of_find?_eq_some hf,
          by simpa using List.find?_some hf,same,Option.some.inj ok.symm⟩

theorem retryHistorical (sha m n raw) (cache : m.requests = n.requests) :
    retry sha m raw = retry sha n raw := by simp only [retry,cache]

end DeltaReduce.NativeCommandReplay
