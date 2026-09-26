import DeltaReduce.NativeCommandReplay
import DeltaReduce.NativeConfigAdmission

/-! Computed mixed CONFIG/command replay. CONFIG supports only the explicitly
checked singleton/empty-graph policy subdomain. The ordered cache represents
journal order, not the native sorted VoteJournal storage layout. Byte scans and
typed snapshots are observations, not authenticated physical durability. -/
namespace DeltaReduce.NativeConfigReplay
open NativeReceiptBytes NativeVoteBytes NativeStateBytes

structure Stored where
  vote : Vote
  receipt : NativeReceiptBytes.Receipt
  parents : NativePolicyCodec.Value

structure Machine where
  core : NativeCommandReplay.Machine
  votes : List Stored

def key (v : Vote) : Bytes × Bytes × Bytes :=
  (v.wire.validator,v.wire.epoch,v.wire.context)

def fresh (m : Machine) (v : Vote) : Prop := ∀ old ∈ m.votes, key old.vote ≠ key v
instance (m v) : Decidable (fresh m v) := by unfold fresh; infer_instance

def facts (m : Machine) (e : NativeWalBytes.Entry) : NativeConfigAdmission.RuntimeFacts :=
  ⟨m.core.tick,false,m.core.invalidated,true,e.sequence⟩

def voteReceipt (e : NativeWalBytes.Entry) (v : Vote) (id : Bytes) : NativeReceiptBytes.Receipt :=
  ⟨1,e.sequence,e.command,id,v.wire.context⟩

def atVote (m : Machine) (e : NativeWalBytes.Entry) : NativeWalBytes.Entry :=
  {e with state := m.core.state}

def added (snap : Option NativeCommandReplay.Snapshot) (m : Machine) (e : NativeWalBytes.Entry)
    (b : NativeConfigAdmission.Bound) (v : Vote) (id : Bytes) : Machine :=
  ⟨{m.core with sequence := e.sequence, matched := m.core.matched || NativeCommandReplay.mark snap e},
    m.votes ++ [⟨v,voteReceipt e v id,b.candidate.parents⟩]⟩

def VoteEntry (sha : Bytes → Bytes) (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (m : Machine) (e : NativeWalBytes.Entry) (b : NativeConfigAdmission.Bound) (v : Vote) (id : Bytes) : Prop :=
  e.kind = 2 ∧ e.sequence = m.core.sequence+1 ∧ e.sequence < 256^8 ∧
  e.state = [] ∧ e.effects = [] ∧ NativeWalBytes.policyId sha policy = some e.record ∧
  NativeConfigAdmission.fromBytes sha policy m.core.state e.command (facts m e) = some (b,v) ∧
  NativeVoteBytes.voteId sha e.command = some id ∧ Valid (voteReceipt e v id) ∧
  fresh m v ∧ NativeCommandReplay.snapshotGuard snap (atVote m e)

def step (sha : Bytes → Bytes) (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (m : Machine) (e : NativeWalBytes.Entry) : Option Machine := do
  if e.kind = 1 then
    let core ← NativeCommandReplay.step sha (some 0) snap m.core e
    some ⟨core,m.votes⟩
  else if e.kind = 2 ∧ e.sequence = m.core.sequence+1 ∧ e.sequence < 256^8 ∧
      e.state = [] ∧ e.effects = [] ∧ NativeWalBytes.policyId sha policy = some e.record then
    let (b,v) ← NativeConfigAdmission.fromBytes sha policy m.core.state e.command (facts m e)
    let id ← NativeVoteBytes.voteId sha e.command
    if Valid (voteReceipt e v id) ∧ fresh m v ∧ NativeCommandReplay.snapshotGuard snap (atVote m e) then
      some (added snap m e b v id)
    else none
  else none

theorem stepSound {sha policy snap m e n} (h : step sha policy snap m e = some n) :
    (e.kind = 1 ∧ NativeCommandReplay.step sha (some 0) snap m.core e = some n.core ∧ n.votes = m.votes) ∨
    (∃ b v id, VoteEntry sha policy snap m e b v id ∧ n = added snap m e b v id) := by
  unfold step at h
  split at h
  · rename_i kind
    cases hc : NativeCommandReplay.step sha (some 0) snap m.core e with
    | none => simp [hc] at h
    | some core =>
      simp only [hc,bind,Option.bind] at h
      cases Option.some.inj h
      exact Or.inl ⟨kind,rfl,rfl⟩
  · split at h <;> try contradiction
    rename_i checks
    cases ha : NativeConfigAdmission.fromBytes sha policy m.core.state e.command (facts m e) with
    | none => simp [ha] at h
    | some pair =>
      rcases pair with ⟨b,v⟩
      simp only [ha,bind,Option.bind] at h
      cases hi : NativeVoteBytes.voteId sha e.command with
      | none => simp [hi] at h
      | some id =>
        simp only [hi] at h
        split at h <;> try contradiction
        rename_i rest
        exact Or.inr ⟨b,v,id,⟨checks.1,checks.2.1,checks.2.2.1,checks.2.2.2.1,
          checks.2.2.2.2.1,checks.2.2.2.2.2,ha,hi,rest⟩,(Option.some.inj h).symm⟩

theorem commandFromComponents {sha policy snap m e core} (kind : e.kind = 1)
    (h : NativeCommandReplay.step sha (some 0) snap m.core e = some core) :
    step sha policy snap m e = some ⟨core,m.votes⟩ := by simp [step,kind,h]

theorem voteFromComponents {sha policy snap m e b v id}
    (h : VoteEntry sha policy snap m e b v id) :
    step sha policy snap m e = some (added snap m e b v id) := by
  rcases h with ⟨kind,seq,bound,st,ef,pol,source,hash,valid,unique,snapshot⟩
  have guard : e.kind = 2 ∧ e.sequence = m.core.sequence+1 ∧ e.sequence < 256^8 ∧ e.state = [] ∧ e.effects = [] ∧ NativeWalBytes.policyId sha policy = some e.record := ⟨kind,seq,bound,st,ef,pol⟩
  simp only [step,if_neg (by omega : e.kind ≠ 1),if_pos guard,source,hash,bind,Option.bind]
  exact if_pos ⟨valid,unique,snapshot⟩

theorem voteOriginalSource {sha policy snap m e b v id}
    (h : VoteEntry sha policy snap m e b v id) :
    NativeConfigAdmission.SourceChecks sha b.policy b.state b ∧ NativeConfigAdmission.VoteChecks b (facts m e) v ∧
    encodeFrame v.wire = e.command ∧ (voteReceipt e v id).sequence = v.sequence ∧
    NativeWalBytes.policyId sha policy = some e.record := by
  rcases h with ⟨_,_,_,_,_,pol,source,_,_,_,_⟩
  have admitted := NativeConfigAdmission.admittedSource source
  have seq := admitted.2.2.2.2.2.2.2.2.2.2.2.1
  exact ⟨admitted.1,admitted.2,NativeConfigAdmission.byteIdentity source,seq.symm,pol⟩

theorem stepSequence {sha policy snap m e n} (h : step sha policy snap m e = some n) :
    n.core.sequence = m.core.sequence+1 ∧ n.core.sequence = e.sequence := by
  rcases stepSound h with ⟨_,cmd,_⟩ | ⟨b,v,id,checks,rfl⟩
  · exact ⟨(NativeCommandReplay.stepSequence cmd).1,(NativeCommandReplay.stepSequence cmd).2.symm⟩
  · exact ⟨checks.2.1,rfl⟩

theorem stepCounts {sha policy snap m e n} (h : step sha policy snap m e = some n) :
    n.core.requests.length + n.votes.length = m.core.requests.length + m.votes.length + 1 := by
  rcases stepSound h with ⟨_,cmd,votes⟩ | ⟨b,v,id,checks,rfl⟩
  · obtain ⟨c,out,_,eq⟩ := NativeCommandReplay.stepSound cmd
    simp only [eq,NativeCommandReplay.updated,votes,List.length_append,List.length_singleton]
    omega
  · simp [added]
    omega

theorem stepClock {sha policy snap m e n} (h : step sha policy snap m e = some n) :
    m.core.tick ≤ n.core.tick ∧ (m.core.invalidated = true → n.core.invalidated = true) := by
  rcases stepSound h with ⟨_,cmd,_⟩ | ⟨b,v,id,checks,rfl⟩
  · have hc := NativeCommandReplay.stepClock cmd (by rfl)
    exact ⟨hc.1,fun _ => hc.2⟩
  · exact ⟨Nat.le_refl _,fun h => h⟩

theorem voteCannotRewriteState (snap m e b v hash) :
    (added snap m e b v hash).core.state = m.core.state ∧
    (added snap m e b v hash).core.requests = m.core.requests ∧
    (added snap m e b v hash).core.tick = m.core.tick := ⟨rfl,rfl,rfl⟩

def run (sha : Bytes → Bytes) (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) :
    Machine → List NativeWalBytes.Entry → Option Machine
  | m,[] => some m
  | m,e::rest => do let n ← step sha policy snap m e; run sha policy snap n rest

inductive History (sha : Bytes → Bytes) (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) :
    Machine → List NativeWalBytes.Entry → Machine → Prop
  | nil (m) : History sha policy snap m [] m
  | cons {m e n rest final} : step sha policy snap m e = some n →
      History sha policy snap n rest final → History sha policy snap m (e::rest) final

theorem runSound {sha policy snap m log final} (h : run sha policy snap m log = some final) :
    History sha policy snap m log final := by
  induction log generalizing m with
  | nil => simp only [run,Option.some.injEq] at h; subst final; exact .nil _
  | cons e rest ih =>
    cases hs : step sha policy snap m e with
    | none => simp [run,hs] at h
    | some n => simp only [run,hs,bind,Option.bind] at h; exact .cons hs (ih h)

theorem historySequence {sha policy snap m log n} (h : History sha policy snap m log n) :
    n.core.sequence = m.core.sequence + log.length := by
  induction h with
  | nil => simp
  | cons hs _ ih => have seq := (stepSequence hs).1; simp only [List.length_cons]; omega

theorem historyCounts {sha policy snap m log n} (h : History sha policy snap m log n) :
    n.core.requests.length + n.votes.length =
      m.core.requests.length + m.votes.length + log.length := by
  induction h with
  | nil => simp
  | cons hs _ ih => have counts := stepCounts hs; simp only [List.length_cons]; omega

theorem historyVoteOrigin {sha policy snap m log n} (h : History sha policy snap m log n)
    (stored : Stored) (member : stored ∈ n.votes) :
    stored ∈ m.votes ∨ ∃ e ∈ log, ∃ prior b v id,
      VoteEntry sha policy snap prior e b v id ∧
      stored = ⟨v,voteReceipt e v id,b.candidate.parents⟩ := by
  induction h with
  | nil => exact Or.inl member
  | @cons m e next rest final hs ht ih =>
    rcases ih member with old | found
    · rcases stepSound hs with ⟨_,_,same⟩ | ⟨b,v,id,checks,rfl⟩
      · exact Or.inl (same ▸ old)
      · simp only [added,List.mem_append,List.mem_singleton] at old
        rcases old with old | eq
        · exact Or.inl old
        · exact Or.inr ⟨e,List.mem_cons_self,m,b,v,id,checks,eq⟩
    · rcases found with ⟨entry,mem,prior,b,v,id,checks,eq⟩
      exact Or.inr ⟨entry,List.mem_cons_of_mem _ mem,prior,b,v,id,checks,eq⟩

theorem historyCommandOrigin {sha policy snap m log n} (h : History sha policy snap m log n)
    (stored : NativeCommandReplay.Cached) (member : stored ∈ n.core.requests) :
    stored ∈ m.core.requests ∨ ∃ e ∈ log, ∃ prior c out,
      NativeCommandReplay.Admitted sha (some 0) snap prior e c out ∧ stored = NativeCommandReplay.cached e c out := by
  induction h with
  | nil => exact Or.inl member
  | @cons m e next rest final hs ht ih =>
    rcases ih member with old | found
    · rcases stepSound hs with ⟨_,cmd,_⟩ | ⟨b,v,id,checks,rfl⟩
      · obtain ⟨c,out,admitted,eq⟩ := NativeCommandReplay.stepSound cmd
        rw [eq] at old
        simp only [NativeCommandReplay.updated,List.mem_append,List.mem_singleton] at old
        rcases old with old | eq
        · exact Or.inl old
        · exact Or.inr ⟨e,List.mem_cons_self,m.core,c,out,admitted,eq⟩
      · exact Or.inl old
    · rcases found with ⟨entry,mem,prior,c,out,checks,eq⟩
      exact Or.inr ⟨entry,List.mem_cons_of_mem _ mem,prior,c,out,checks,eq⟩

def Unique (m : Machine) : Prop :=
  NativeCommandReplay.UniqueRequests m.core ∧
    m.votes.Pairwise (fun a b => key a.vote ≠ key b.vote)

theorem stepUnique {sha policy snap m e n} (h : step sha policy snap m e = some n)
    (unique : Unique m) : Unique n := by
  rcases stepSound h with ⟨_,cmd,same⟩ | ⟨b,v,id,checks,rfl⟩
  · exact ⟨NativeCommandReplay.stepUnique cmd unique.1,same ▸ unique.2⟩
  · refine ⟨unique.1,?_⟩
    change (m.votes ++ [_]).Pairwise _
    rw [List.pairwise_append]
    refine ⟨unique.2,by simp,?_⟩
    intro a am c cm
    have eq : c = Stored.mk v (voteReceipt e v id) b.candidate.parents := by simpa using cm
    subst c
    exact checks.2.2.2.2.2.2.2.2.2.1 a am

theorem historyUnique {sha policy snap m log n} (h : History sha policy snap m log n)
    (unique : Unique m) : Unique n := by
  induction h with
  | nil => exact unique
  | cons hs _ ih => exact ih (stepUnique hs unique)

theorem stepSnapshot {sha policy snap m e n} (h : step sha policy snap m e = some n) :
    (∀ s ∈ snap, e.sequence = s.sequence → n.core.state = s.state) ∧
    n.core.matched = (m.core.matched || NativeCommandReplay.mark snap e) := by
  rcases stepSound h with ⟨_,cmd,_⟩ | ⟨b,v,id,checks,rfl⟩
  · obtain ⟨c,out,admitted,eq⟩ := NativeCommandReplay.stepSound cmd
    rw [eq]
    exact ⟨admitted.2.2.2.2.2.2.2,rfl⟩
  · exact ⟨checks.2.2.2.2.2.2.2.2.2.2,rfl⟩

theorem historySnapshot {sha policy s m log n} (h : History sha policy (some s) m log n)
    (matched : n.core.matched = true) :
    m.core.matched = true ∨ ∃ e ∈ log, ∃ before after,
      step sha policy (some s) before e = some after ∧ e.sequence = s.sequence ∧
      after.core.state = s.state := by
  induction h with
  | nil => exact Or.inl matched
  | @cons m e next rest final hs ht ih =>
    rcases ih matched with old | found
    · have guard := stepSnapshot hs
      rw [guard.2,Bool.or_eq_true] at old
      rcases old with old | marked
      · exact Or.inl old
      · have seq : e.sequence = s.sequence := by simpa [NativeCommandReplay.mark] using marked
        exact Or.inr ⟨e,List.mem_cons_self,m,next,hs,seq,guard.1 s (by simp) seq⟩
    · obtain ⟨e,em,before,after,hs,seq,state⟩ := found
      exact Or.inr ⟨e,List.mem_cons_of_mem _ em,before,after,hs,seq,state⟩

def recover (sha : Bytes → Bytes) (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (log : List NativeWalBytes.Entry) : Option Machine := do
  let b ← NativeConfigAdmission.prepare sha policy initial
  let core ← NativeCommandReplay.initialMachine (some b.policy.initialTick) snap initial
  let final ← run sha policy snap ⟨core,[]⟩ log
  if final.core.matched = true ∧ (∀ s ∈ snap, s.sequence ≤ log.length) then some final else none

theorem recoveryComputed {sha policy initial snap log final}
    (h : recover sha policy initial snap log = some final) :
    ∃ b core, NativeConfigAdmission.prepare sha policy initial = some b ∧
      NativeCommandReplay.initialMachine (some b.policy.initialTick) snap initial = some core ∧
      History sha policy snap ⟨core,[]⟩ log final ∧ final.core.matched = true ∧
      (∀ s ∈ snap, s.sequence ≤ log.length) := by
  unfold recover at h
  cases hp : NativeConfigAdmission.prepare sha policy initial with
  | none => simp [hp] at h
  | some b =>
    cases hc : NativeCommandReplay.initialMachine (some b.policy.initialTick) snap initial with
    | none => simp [hp,hc] at h
    | some core =>
      cases hr : run sha policy snap ⟨core,[]⟩ log with
      | none => simp [hp,hc,hr] at h
      | some out =>
        simp only [hp,hc,hr,bind,Option.bind] at h
        split at h <;> try contradiction
        rename_i checks
        cases Option.some.inj h
        exact ⟨b,core,rfl,hc,runSound hr,checks⟩

theorem recoveryCounts {sha policy initial snap log final}
    (h : recover sha policy initial snap log = some final) :
    final.core.sequence = log.length ∧
    final.core.requests.length + final.votes.length = log.length := by
  obtain ⟨b,core,_,seed,hist,_,_⟩ := recoveryComputed h
  have shape := NativeCommandReplay.initialShape seed
  have seq := historySequence hist
  have counts := historyCounts hist
  simpa [shape.2.2.1,shape.2.2.2.2.2.1] using And.intro seq counts

theorem recoveryUnique {sha policy initial snap log final}
    (h : recover sha policy initial snap log = some final) : Unique final := by
  obtain ⟨b,core,_,seed,hist,_,_⟩ := recoveryComputed h
  apply historyUnique hist
  simp [Unique,NativeCommandReplay.UniqueRequests,(NativeCommandReplay.initialShape seed).2.2.2.2.2.1]

theorem positiveSnapshotOrigin {sha policy initial s log final}
    (h : recover sha policy initial (some s) log = some final) (positive : s.sequence ≠ 0) :
    ∃ e ∈ log, ∃ before after, step sha policy (some s) before e = some after ∧
      e.sequence = s.sequence ∧ after.core.state = s.state := by
  obtain ⟨b,core,_,seed,hist,matched,_⟩ := recoveryComputed h
  rcases historySnapshot hist matched with old | found
  · rw [(NativeCommandReplay.initialShape seed).2.2.2.2.2.2] at old
    simp [NativeCommandReplay.initialMatch,positive] at old
  · exact found

def recoverObserved (sha : Bytes → Bytes) (policy initial raw : Bytes)
    (snap : Option NativeCommandReplay.Snapshot) : Option Machine := do
  let scan ← NativeWalScan.check sha raw
  if scan.torn = false ∧ scan.tail = [] then
    recover sha policy initial snap (NativeWalScan.entries scan)
  else none

theorem observedComputed {sha policy initial raw snap final}
    (h : recoverObserved sha policy initial raw snap = some final) :
    ∃ scan, NativeWalScan.check sha raw = some scan ∧ scan.torn = false ∧ scan.tail = [] ∧
      recover sha policy initial snap (NativeWalScan.entries scan) = some final := by
  unfold recoverObserved at h
  cases hs : NativeWalScan.check sha raw with
  | none => simp [hs] at h
  | some scan =>
    simp only [hs,bind,Option.bind] at h
    split at h <;> try contradiction
    rename_i checks
    exact ⟨scan,rfl,checks.1,checks.2,h⟩

def retryVote (sha : Bytes → Bytes) (m : Machine) (raw : Bytes) : Option Stored := do
  let v ← decodeFrame raw
  let id ← NativeVoteBytes.voteId sha raw
  let old ← m.votes.find? (fun r => key r.vote == key v)
  if encodeFrame old.vote.wire = raw ∧ old.receipt.voteId = id then some old else none

theorem retryHistorical (sha m n raw) (same : m.votes = n.votes) :
    retryVote sha m raw = retryVote sha n raw := by simp only [retryVote,same]

theorem retryFromCache {sha m raw v id old} (parsed : decodeFrame raw = some v)
    (hashed : NativeVoteBytes.voteId sha raw = some id)
    (found : m.votes.find? (fun r => key r.vote == key v) = some old)
    (same : encodeFrame old.vote.wire = raw ∧ old.receipt.voteId = id) :
    retryVote sha m raw = some old := by simp [retryVote,parsed,hashed,found,same]

theorem retryConflict {sha m raw v id old} (parsed : decodeFrame raw = some v)
    (hashed : NativeVoteBytes.voteId sha raw = some id)
    (found : m.votes.find? (fun r => key r.vote == key v) = some old)
    (different : encodeFrame old.vote.wire ≠ raw) : retryVote sha m raw = none := by
  simp [retryVote,parsed,hashed,found,different]

theorem retryOrigin {sha m raw stored} (h : retryVote sha m raw = some stored) :
    stored ∈ m.votes ∧ encodeFrame stored.vote.wire = raw ∧
      NativeVoteBytes.voteId sha raw = some stored.receipt.voteId := by
  unfold retryVote at h
  cases hp : decodeFrame raw with
  | none => simp [hp] at h
  | some v =>
    cases hh : NativeVoteBytes.voteId sha raw with
    | none => simp [hp,hh] at h
    | some id =>
      cases hf : m.votes.find? (fun r => key r.vote == key v) with
      | none => simp [hp,hh,hf] at h
      | some old =>
        simp only [hp,hh,hf,bind,Option.bind] at h
        split at h <;> try contradiction
        rename_i checks
        cases Option.some.inj h
        exact ⟨List.mem_of_find?_eq_some hf,checks.1,by rw [checks.2]⟩

end DeltaReduce.NativeConfigReplay
