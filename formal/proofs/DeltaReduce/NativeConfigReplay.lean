import DeltaReduce.NativeCommandReplay
import DeltaReduce.NativeReplayAdmission

/-! One computed journal fold with closed CONFIG-only or CONFIG/ISC proposal modes.
The former retains its singleton/empty-graph scope; the latter checks the whole original policy. The ordered cache represents
journal order, not the native sorted VoteJournal storage layout. Byte scans and
typed snapshots are observations, not authenticated physical durability. -/
namespace DeltaReduce.NativeConfigReplay
open NativeReceiptBytes NativeVoteBytes NativeStateBytes
open NativeReplayAdmission (Mode Selected)

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

def voteReceipt (mode : Mode) (b : Selected mode) (e : NativeWalBytes.Entry) (v : Vote) (id : Bytes) : NativeReceiptBytes.Receipt :=
  ⟨NativeReplayAdmission.action mode b,e.sequence,e.command,id,v.wire.context⟩

def atVote (m : Machine) (e : NativeWalBytes.Entry) : NativeWalBytes.Entry :=
  {e with state := m.core.state}

def added (mode : Mode) (snap : Option NativeCommandReplay.Snapshot) (m : Machine) (e : NativeWalBytes.Entry)
    (b : Selected mode) (v : Vote) (id : Bytes) : Machine :=
  ⟨{m.core with sequence := e.sequence, matched := m.core.matched || NativeCommandReplay.mark snap e},
    m.votes ++ [⟨v,voteReceipt mode b e v id,NativeReplayAdmission.parents mode b⟩]⟩

def VoteEntry (mode : Mode) (sha : Bytes → Bytes) (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (m : Machine) (e : NativeWalBytes.Entry) (b : Selected mode) (v : Vote) (id : Bytes) : Prop :=
  e.kind = 2 ∧ e.sequence = m.core.sequence+1 ∧ e.sequence < 256^8 ∧
  e.state = [] ∧ e.effects = [] ∧ NativeWalBytes.policyId sha policy = some e.record ∧
  NativeReplayAdmission.fromBytes mode sha policy m.core.state e.command (facts m e) = some (b,v) ∧
  NativeVoteBytes.voteId sha e.command = some id ∧ Valid (voteReceipt mode b e v id) ∧
  fresh m v ∧ NativeCommandReplay.snapshotGuard snap (atVote m e)

def step (mode : Mode) (sha : Bytes → Bytes) (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (m : Machine) (e : NativeWalBytes.Entry) : Option Machine := do
  if e.kind = 1 then
    let core ← NativeCommandReplay.step sha (some 0) snap m.core e
    some ⟨core,m.votes⟩
  else if e.kind = 2 ∧ e.sequence = m.core.sequence+1 ∧ e.sequence < 256^8 ∧
      e.state = [] ∧ e.effects = [] ∧ NativeWalBytes.policyId sha policy = some e.record then
    let (b,v) ← NativeReplayAdmission.fromBytes mode sha policy m.core.state e.command (facts m e)
    let id ← NativeVoteBytes.voteId sha e.command
    if Valid (voteReceipt mode b e v id) ∧ fresh m v ∧ NativeCommandReplay.snapshotGuard snap (atVote m e) then
      some (added mode snap m e b v id)
    else none
  else none

theorem stepSound {mode sha policy snap m e n} (h : step mode sha policy snap m e = some n) :
    (e.kind = 1 ∧ NativeCommandReplay.step sha (some 0) snap m.core e = some n.core ∧ n.votes = m.votes) ∨
    (∃ b v id, VoteEntry mode sha policy snap m e b v id ∧ n = added mode snap m e b v id) := by
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
    cases ha : NativeReplayAdmission.fromBytes mode sha policy m.core.state e.command (facts m e) with
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

theorem commandFromComponents {mode sha policy snap m e core} (kind : e.kind = 1)
    (h : NativeCommandReplay.step sha (some 0) snap m.core e = some core) :
    step mode sha policy snap m e = some ⟨core,m.votes⟩ := by simp [step,kind,h]

theorem wrongPositionRejected {mode sha policy snap m e}
    (bad : e.sequence ≠ m.core.sequence + 1) : step mode sha policy snap m e = none := by
  unfold step
  split
  · rw [NativeCommandReplay.wrongPositionRejected sha (some 0) snap m.core e bad]
    rfl
  · simp [bad]

theorem wrongPolicyRejected {mode sha policy snap m e} (kind : e.kind = 2)
    (bad : NativeWalBytes.policyId sha policy ≠ some e.record) :
    step mode sha policy snap m e = none := by simp [step,kind,bad]

theorem voteFromComponents {mode sha policy snap m e b v id}
    (h : VoteEntry mode sha policy snap m e b v id) :
    step mode sha policy snap m e = some (added mode snap m e b v id) := by
  rcases h with ⟨kind,seq,bound,st,ef,pol,source,hash,valid,unique,snapshot⟩
  have guard : e.kind = 2 ∧ e.sequence = m.core.sequence+1 ∧ e.sequence < 256^8 ∧ e.state = [] ∧ e.effects = [] ∧ NativeWalBytes.policyId sha policy = some e.record := ⟨kind,seq,bound,st,ef,pol⟩
  simp only [step,if_neg (by omega : e.kind ≠ 1),if_pos guard,source,hash,bind,Option.bind]
  exact if_pos ⟨valid,unique,snapshot⟩

theorem voteOriginalSource {mode sha policy snap m e b v id}
    (h : VoteEntry mode sha policy snap m e b v id) :
    NativeReplayAdmission.fromBytes mode sha policy m.core.state e.command (facts m e) = some (b,v) ∧
    encodeFrame v.wire = e.command ∧ (voteReceipt mode b e v id).sequence = v.sequence ∧
    NativeWalBytes.policyId sha policy = some e.record := by
  rcases h with ⟨_,_,_,_,_,pol,source,_,_,_,_⟩
  exact ⟨source,NativeReplayAdmission.byteIdentity source,
    (NativeReplayAdmission.originalSequence source).symm,pol⟩

theorem stepSequence {mode sha policy snap m e n} (h : step mode sha policy snap m e = some n) :
    n.core.sequence = m.core.sequence+1 ∧ n.core.sequence = e.sequence := by
  rcases stepSound h with ⟨_,cmd,_⟩ | ⟨b,v,id,checks,rfl⟩
  · exact ⟨(NativeCommandReplay.stepSequence cmd).1,(NativeCommandReplay.stepSequence cmd).2.symm⟩
  · exact ⟨checks.2.1,rfl⟩

theorem stepCounts {mode sha policy snap m e n} (h : step mode sha policy snap m e = some n) :
    n.core.requests.length + n.votes.length = m.core.requests.length + m.votes.length + 1 := by
  rcases stepSound h with ⟨_,cmd,votes⟩ | ⟨b,v,id,checks,rfl⟩
  · obtain ⟨c,out,_,eq⟩ := NativeCommandReplay.stepSound cmd
    simp only [eq,NativeCommandReplay.updated,votes,List.length_append,List.length_singleton]
    omega
  · simp [added]
    omega

theorem stepClock {mode sha policy snap m e n} (h : step mode sha policy snap m e = some n) :
    m.core.tick ≤ n.core.tick ∧ (m.core.invalidated = true → n.core.invalidated = true) := by
  rcases stepSound h with ⟨_,cmd,_⟩ | ⟨b,v,id,checks,rfl⟩
  · have hc := NativeCommandReplay.stepClock cmd (by rfl)
    exact ⟨hc.1,fun _ => hc.2⟩
  · exact ⟨Nat.le_refl _,fun h => h⟩

theorem voteCannotRewriteState (mode : Mode) (snap m e b v hash) :
    (added mode snap m e b v hash).core.state = m.core.state ∧
    (added mode snap m e b v hash).core.requests = m.core.requests ∧
    (added mode snap m e b v hash).core.tick = m.core.tick := ⟨rfl,rfl,rfl⟩

def run (mode : Mode) (sha : Bytes → Bytes) (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) :
    Machine → List NativeWalBytes.Entry → Option Machine
  | m,[] => some m
  | m,e::rest => do let n ← step mode sha policy snap m e; run mode sha policy snap n rest

inductive History (mode : Mode) (sha : Bytes → Bytes) (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) :
    Machine → List NativeWalBytes.Entry → Machine → Prop
  | nil (m) : History mode sha policy snap m [] m
  | cons {m e n rest final} : step mode sha policy snap m e = some n →
      History mode sha policy snap n rest final → History mode sha policy snap m (e::rest) final

theorem runSound {mode sha policy snap m log final} (h : run mode sha policy snap m log = some final) :
    History mode sha policy snap m log final := by
  induction log generalizing m with
  | nil => simp only [run,Option.some.injEq] at h; subst final; exact .nil _
  | cons e rest ih =>
    cases hs : step mode sha policy snap m e with
    | none => simp [run,hs] at h
    | some n => simp only [run,hs,bind,Option.bind] at h; exact .cons hs (ih h)

theorem historySequence {mode sha policy snap m log n} (h : History mode sha policy snap m log n) :
    n.core.sequence = m.core.sequence + log.length := by
  induction h with
  | nil => simp
  | cons hs _ ih => have seq := (stepSequence hs).1; simp only [List.length_cons]; omega

theorem historyCounts {mode sha policy snap m log n} (h : History mode sha policy snap m log n) :
    n.core.requests.length + n.votes.length =
      m.core.requests.length + m.votes.length + log.length := by
  induction h with
  | nil => simp
  | cons hs _ ih => have counts := stepCounts hs; simp only [List.length_cons]; omega

theorem historyVoteOrigin {mode sha policy snap m log n} (h : History mode sha policy snap m log n)
    (stored : Stored) (member : stored ∈ n.votes) :
    stored ∈ m.votes ∨ ∃ e ∈ log, ∃ prior b v id,
      VoteEntry mode sha policy snap prior e b v id ∧
      stored = ⟨v,voteReceipt mode b e v id,NativeReplayAdmission.parents mode b⟩ := by
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

theorem historyCommandOrigin {mode sha policy snap m log n} (h : History mode sha policy snap m log n)
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

theorem stepUnique {mode sha policy snap m e n} (h : step mode sha policy snap m e = some n)
    (unique : Unique m) : Unique n := by
  rcases stepSound h with ⟨_,cmd,same⟩ | ⟨b,v,id,checks,rfl⟩
  · exact ⟨NativeCommandReplay.stepUnique cmd unique.1,same ▸ unique.2⟩
  · refine ⟨unique.1,?_⟩
    change (m.votes ++ [_]).Pairwise _
    rw [List.pairwise_append]
    refine ⟨unique.2,by simp,?_⟩
    intro a am c cm
    have eq : c = Stored.mk v (voteReceipt mode b e v id) (NativeReplayAdmission.parents mode b) := by simpa using cm
    subst c
    exact checks.2.2.2.2.2.2.2.2.2.1 a am

theorem historyUnique {mode sha policy snap m log n} (h : History mode sha policy snap m log n)
    (unique : Unique m) : Unique n := by
  induction h with
  | nil => exact unique
  | cons hs _ ih => exact ih (stepUnique hs unique)

theorem stepSnapshot {mode sha policy snap m e n} (h : step mode sha policy snap m e = some n) :
    (∀ s ∈ snap, e.sequence = s.sequence → n.core.state = s.state) ∧
    n.core.matched = (m.core.matched || NativeCommandReplay.mark snap e) := by
  rcases stepSound h with ⟨_,cmd,_⟩ | ⟨b,v,id,checks,rfl⟩
  · obtain ⟨c,out,admitted,eq⟩ := NativeCommandReplay.stepSound cmd
    rw [eq]
    exact ⟨admitted.2.2.2.2.2.2.2,rfl⟩
  · exact ⟨checks.2.2.2.2.2.2.2.2.2.2,rfl⟩

theorem historySnapshot {mode sha policy s m log n} (h : History mode sha policy (some s) m log n)
    (matched : n.core.matched = true) :
    m.core.matched = true ∨ ∃ e ∈ log, ∃ before after,
      step mode sha policy (some s) before e = some after ∧ e.sequence = s.sequence ∧
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

def recover (mode : Mode) (sha : Bytes → Bytes) (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (log : List NativeWalBytes.Entry) : Option Machine := do
  let b ← NativeReplayAdmission.prepare mode sha policy initial
  let core ← NativeCommandReplay.initialMachine (some (NativeReplayAdmission.initialTick mode b)) snap initial
  let final ← run mode sha policy snap ⟨core,[]⟩ log
  if final.core.matched = true ∧ (∀ s ∈ snap, s.sequence ≤ log.length) then some final else none

theorem startupRejected {mode sha policy initial snap log}
    (bad : NativeReplayAdmission.prepare mode sha policy initial = none) :
    recover mode sha policy initial snap log = none := by simp [recover,bad]

theorem recoveryFromComponents {mode sha policy initial snap log b core final}
    (policyOk : NativeReplayAdmission.prepare mode sha policy initial = some b)
    (seed : NativeCommandReplay.initialMachine (some (NativeReplayAdmission.initialTick mode b)) snap initial = some core)
    (history : run mode sha policy snap ⟨core,[]⟩ log = some final)
    (checks : final.core.matched = true ∧ (∀ s ∈ snap, s.sequence ≤ log.length)) :
    recover mode sha policy initial snap log = some final := by
  simp only [recover,policyOk,seed,history,bind,Option.bind]
  exact if_pos checks

theorem recoveryComputed {mode sha policy initial snap log final}
    (h : recover mode sha policy initial snap log = some final) :
    ∃ b core, NativeReplayAdmission.prepare mode sha policy initial = some b ∧
      NativeCommandReplay.initialMachine (some (NativeReplayAdmission.initialTick mode b)) snap initial = some core ∧
      History mode sha policy snap ⟨core,[]⟩ log final ∧ final.core.matched = true ∧
      (∀ s ∈ snap, s.sequence ≤ log.length) := by
  unfold recover at h
  cases hp : NativeReplayAdmission.prepare mode sha policy initial with
  | none => simp [hp] at h
  | some b =>
    cases hc : NativeCommandReplay.initialMachine (some (NativeReplayAdmission.initialTick mode b)) snap initial with
    | none => simp [hp,hc] at h
    | some core =>
      cases hr : run mode sha policy snap ⟨core,[]⟩ log with
      | none => simp [hp,hc,hr] at h
      | some out =>
        simp only [hp,hc,hr,bind,Option.bind] at h
        split at h <;> try contradiction
        rename_i checks
        cases Option.some.inj h
        exact ⟨b,core,rfl,hc,runSound hr,checks⟩

theorem recoveryCounts {mode sha policy initial snap log final}
    (h : recover mode sha policy initial snap log = some final) :
    final.core.sequence = log.length ∧
    final.core.requests.length + final.votes.length = log.length := by
  obtain ⟨b,core,_,seed,hist,_,_⟩ := recoveryComputed h
  have shape := NativeCommandReplay.initialShape seed
  have seq := historySequence hist
  have counts := historyCounts hist
  simpa [shape.2.2.1,shape.2.2.2.2.2.1] using And.intro seq counts

theorem recoveryUnique {mode sha policy initial snap log final}
    (h : recover mode sha policy initial snap log = some final) : Unique final := by
  obtain ⟨b,core,_,seed,hist,_,_⟩ := recoveryComputed h
  apply historyUnique hist
  simp [Unique,NativeCommandReplay.UniqueRequests,(NativeCommandReplay.initialShape seed).2.2.2.2.2.1]

theorem recoveryVoteOrigin {mode sha policy initial snap log final stored}
    (h : recover mode sha policy initial snap log = some final) (member : stored ∈ final.votes) :
    ∃ e ∈ log, ∃ prior b v id, VoteEntry mode sha policy snap prior e b v id ∧
      stored = ⟨v,voteReceipt mode b e v id,NativeReplayAdmission.parents mode b⟩ := by
  obtain ⟨b,core,_,_,hist,_,_⟩ := recoveryComputed h
  rcases historyVoteOrigin hist stored member with old | found
  · exact False.elim (List.not_mem_nil old)
  · exact found

theorem recoveryCommandOrigin {mode sha policy initial snap log final stored}
    (h : recover mode sha policy initial snap log = some final)
    (member : stored ∈ final.core.requests) :
    ∃ e ∈ log, ∃ prior c out, NativeCommandReplay.Admitted sha (some 0) snap prior e c out ∧
      stored = NativeCommandReplay.cached e c out := by
  obtain ⟨b,core,_,seed,hist,_,_⟩ := recoveryComputed h
  rcases historyCommandOrigin hist stored member with old | found
  · rw [(NativeCommandReplay.initialShape seed).2.2.2.2.2.1] at old
    exact False.elim (List.not_mem_nil old)
  · exact found

theorem recoveryProposalOrigin {sha policy initial snap log final stored}
    (h : recover .proposals sha policy initial snap log = some final) (member : stored ∈ final.votes) :
    ∃ e ∈ log, ∃ prior b c v id,
      VoteEntry .proposals sha policy snap prior e (b,c) v id ∧
      c.candidate ∈ b.graph.policy.candidates ∧
      NativeProposalAdmission.CandidateSource sha b.graph c.candidate c ∧
      NativeProposalAdmission.VoteChecks b.graph c (facts prior e) v ∧
      encodeFrame v.wire = e.command ∧
      stored = ⟨v,voteReceipt .proposals (b,c) e v id,c.candidate.parents⟩ := by
  obtain ⟨e,mem,prior,⟨b,c⟩,v,id,checked,eq⟩ := recoveryVoteOrigin h member
  have original := voteOriginalSource checked
  have admitted := NativeReplayAdmission.proposalOriginalSource original.1
  exact ⟨e,mem,prior,b,c,v,id,checked,admitted.1,admitted.2.1,admitted.2.2,original.2.1,eq⟩

theorem positiveSnapshotOrigin {mode sha policy initial s log final}
    (h : recover mode sha policy initial (some s) log = some final) (positive : s.sequence ≠ 0) :
    ∃ e ∈ log, ∃ before after, step mode sha policy (some s) before e = some after ∧
      e.sequence = s.sequence ∧ after.core.state = s.state := by
  obtain ⟨b,core,_,seed,hist,matched,_⟩ := recoveryComputed h
  rcases historySnapshot hist matched with old | found
  · rw [(NativeCommandReplay.initialShape seed).2.2.2.2.2.2] at old
    simp [NativeCommandReplay.initialMatch,positive] at old
  · exact found

def recoverObserved (mode : Mode) (sha : Bytes → Bytes) (policy initial raw : Bytes)
    (snap : Option NativeCommandReplay.Snapshot) : Option Machine := do
  let scan ← NativeWalScan.check sha raw
  if scan.torn = false ∧ scan.tail = [] then
    recover mode sha policy initial snap (NativeWalScan.entries scan)
  else none

theorem observedComputed {mode sha policy initial raw snap final}
    (h : recoverObserved mode sha policy initial raw snap = some final) :
    ∃ scan, NativeWalScan.check sha raw = some scan ∧ scan.torn = false ∧ scan.tail = [] ∧
      recover mode sha policy initial snap (NativeWalScan.entries scan) = some final := by
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
