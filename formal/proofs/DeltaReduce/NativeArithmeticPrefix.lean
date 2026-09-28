import DeltaReduce.NativeArithmeticVote
import DeltaReduce.NativeWholeReplay
import DeltaReduce.NativeWalScan

/-! One candidate arithmetic VOTE after an executed original guarded mixed
prefix. This does not enable original native arithmetic or validate an arbitrary
history containing prior arithmetic votes. Unknown/torn observations reject. -/
namespace DeltaReduce.NativeArithmeticPrefix
open NativeBinding
open NativeVoteBytes (Vote)

structure Prefix where
  scan : NativeWalScan.Result
  prior : NativeConfigReplay.Machine

def loadPrefix (sha : Bytes → Bytes) (policyRaw initial stateRaw : Bytes)
    (snapshot : Option NativeCommandReplay.Snapshot) (observation : Option Bytes) : Option Prefix := do
  let raw ← observation
  let scan ← NativeWalScan.check sha raw
  if scan.tail = [] ∧ scan.torn = false then
    let prior ← NativeConfigReplay.recover .whole sha policyRaw initial snapshot (NativeWalScan.entries scan)
    if prior.core.state = stateRaw then some ⟨scan,prior⟩ else none
  else none

theorem prefixSource {sha policyRaw initial stateRaw snapshot observation out}
    (h : loadPrefix sha policyRaw initial stateRaw snapshot observation = some out) :
    ∃ raw, observation = some raw ∧ NativeWalScan.check sha raw = some out.scan ∧
      out.scan.tail = [] ∧ out.scan.torn = false ∧
      NativeConfigReplay.recover .whole sha policyRaw initial snapshot (NativeWalScan.entries out.scan) = some out.prior ∧
      out.prior.core.state = stateRaw := by
  simp only [loadPrefix,bind,Option.bind_eq_some_iff] at h
  obtain ⟨raw,hr,s,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i complete
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨m,hm,last⟩ := last
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨raw,hr,hs,complete.1,complete.2,hm,by assumption⟩

theorem prefixPosition {sha policyRaw initial stateRaw snapshot observation out}
    (h : loadPrefix sha policyRaw initial stateRaw snapshot observation = some out) :
    out.prior.core.sequence = (NativeWalScan.entries out.scan).length ∧
    out.prior.core.requests.length + out.prior.votes.length = (NativeWalScan.entries out.scan).length := by
  obtain ⟨_,_,_,_,_,replayed,_⟩ := prefixSource h
  exact NativeConfigReplay.recoveryCounts replayed

theorem unknownRejected (sha policyRaw initial stateRaw snapshot) :
    loadPrefix sha policyRaw initial stateRaw snapshot none = none := rfl

theorem tornRejected {sha policyRaw initial stateRaw snapshot raw scan}
    (hs : NativeWalScan.check sha raw = some scan) (bad : scan.tail ≠ [] ∨ scan.torn ≠ false) :
    loadPrefix sha policyRaw initial stateRaw snapshot (some raw) = none := by
  simp only [loadPrefix,bind,Option.bind,hs]
  apply if_neg
  intro good
  rcases bad with tail | flag
  · exact tail good.1
  · exact flag good.2

def facts (p : Prefix) : NativeConfigAdmission.RuntimeFacts :=
  ⟨p.prior.core.tick,false,p.prior.core.invalidated,true,p.prior.core.sequence+1⟩

theorem factsDerived (p : Prefix) :
    (facts p).tick = p.prior.core.tick ∧ (facts p).invalidated = p.prior.core.invalidated ∧
    (facts p).expectedSequence = p.prior.core.sequence+1 ∧
    (facts p).recovery = true ∧ (facts p).ready = false := ⟨rfl,rfl,rfl,rfl,rfl⟩

section Arithmetic
variable {codec store trust anchor} (binding : Binding codec trust anchor store)

inductive Computation (b : NativeVectorContext.Bound) where
  | parameter (p : NativeArithmeticVote.Parameter binding b)
  | apply (p : NativeArithmeticVote.Applied binding)

def admitted {b} : Computation binding b → NativeSelectedVote.Admitted
  | .parameter p => p.admitted
  | .apply p => p.admitted

def compute (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (application : Option (NativeAggregateLineage.Edge × Bytes))
    (r : NativeConfigAdmission.RuntimeFacts) (v : Vote) : Option (Computation binding b) :=
  if v.wire.kind = NativeVoteBytes.actionName 5 then
    (NativeArithmeticVote.parameter binding adapter b r v).map Computation.parameter
  else if v.wire.kind = NativeVoteBytes.actionName 7 then do
    let (root,profileId) ← application
    (NativeArithmeticVote.applyVote binding adapter b root profileId r v).map Computation.apply
  else none

theorem computationSource {adapter b application r v out}
    (h : compute binding adapter b application r v = some out) :
    NativeArithmeticVote.select adapter.sha256 b r v = some (admitted binding out) := by
  unfold compute at h
  split at h
  · obtain ⟨p,hp,eq⟩ := Option.map_eq_some_iff.mp h
    subst out
    exact (NativeArithmeticVote.parameterSource binding hp).1
  · split at h
    · simp only [bind,Option.bind_eq_some_iff] at h
      obtain ⟨⟨root,pid⟩,_,last⟩ := h
      obtain ⟨p,hp,eq⟩ := Option.map_eq_some_iff.mp last
      subst out
      exact (NativeArithmeticVote.applySource binding hp).1
    · contradiction

structure Next (b : NativeVectorContext.Bound) where
  before : Prefix
  entry : NativeWalBytes.Entry
  vote : Vote
  computation : Computation binding b
  voteId : Bytes
  receipt : NativeReceiptBytes.Receipt

def receipt (e : NativeWalBytes.Entry) (v : Vote) (action : Nat) (id : Bytes) : NativeReceiptBytes.Receipt :=
  ⟨action,e.sequence,e.command,id,v.wire.context⟩

/-- `loaded` binds the source graph to exactly the policy and state used here.
No caller-supplied translated body, phase permission or loadPrefix count is used. -/
def check (adapter : HashAdapter codec) {b policyRaw stateRaw apc config proof profile permission inputs}
    (_loaded : NativeVectorContext.bind adapter.sha256 policyRaw stateRaw apc config proof profile permission inputs = some b)
    (initial : Bytes) (snapshot : Option NativeCommandReplay.Snapshot)
    (observation : Option Bytes) (nextRaw : Bytes)
    (application : Option (NativeAggregateLineage.Edge × Bytes)) : Option (Next binding b) := do
  let before ← loadPrefix adapter.sha256 policyRaw initial stateRaw snapshot observation
  let entry ← NativeWalBytes.decode adapter.sha256 nextRaw
  if entry.kind = 2 ∧ entry.sequence = before.prior.core.sequence+1 ∧ entry.state = [] ∧ entry.effects = [] then
    if NativeWalBytes.policyId adapter.sha256 policyRaw = some entry.record then
      let vote ← NativeVoteBytes.decodeFrame entry.command
      if NativeConfigReplay.fresh before.prior vote then
        let computation ← compute binding adapter b application (facts before) vote
        let id ← NativeVoteBytes.voteId adapter.sha256 entry.command
        let r := receipt entry vote (admitted binding computation).selected.original.action id
        if NativeReceiptBytes.Valid r then some ⟨before,entry,vote,computation,id,r⟩ else none
      else none
    else none
  else none

structure Source (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (policyRaw initial stateRaw : Bytes) (snapshot : Option NativeCommandReplay.Snapshot)
    (observation : Option Bytes) (nextRaw : Bytes)
    (application : Option (NativeAggregateLineage.Edge × Bytes)) (out : Next binding b) : Prop where
  before : loadPrefix adapter.sha256 policyRaw initial stateRaw snapshot observation = some out.before
  entry : NativeWalBytes.decode adapter.sha256 nextRaw = some out.entry
  shape : out.entry.kind = 2 ∧ out.entry.sequence = out.before.prior.core.sequence+1 ∧ out.entry.state = [] ∧ out.entry.effects = []
  policy : NativeWalBytes.policyId adapter.sha256 policyRaw = some out.entry.record
  vote : NativeVoteBytes.decodeFrame out.entry.command = some out.vote
  fresh : NativeConfigReplay.fresh out.before.prior out.vote
  arithmetic : compute binding adapter b application (facts out.before) out.vote = some out.computation
  id : NativeVoteBytes.voteId adapter.sha256 out.entry.command = some out.voteId
  receipt : out.receipt = receipt out.entry out.vote (admitted binding out.computation).selected.original.action out.voteId
  valid : NativeReceiptBytes.Valid out.receipt

theorem checked {adapter b policyRaw stateRaw apc config proof profile permission inputs loaded initial snapshot observation nextRaw application out}
    (h : @check codec store trust anchor binding adapter b policyRaw stateRaw apc config proof profile permission inputs loaded initial snapshot observation nextRaw application = some out) :
    Source binding adapter b policyRaw initial stateRaw snapshot observation nextRaw application out := by
  simp only [check,bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,e,he,last⟩ := h
  split at last <;> try contradiction
  rename_i shape
  split at last <;> try contradiction
  rename_i policyOk
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨v,hv,last⟩ := last
  split at last <;> try contradiction
  rename_i fresh
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨c,hc,id,hi,last⟩ := last
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hp,he,shape,policyOk,hv,fresh,hc,hi,rfl,by assumption⟩

theorem globalSequence {adapter b policyRaw initial stateRaw snapshot observation nextRaw application out}
    (h : Source binding adapter b policyRaw initial stateRaw snapshot observation nextRaw application out) :
    out.entry.sequence = (NativeWalScan.entries out.before.scan).length+1 ∧
    out.vote.sequence = out.entry.sequence ∧
    out.vote.sequence = out.before.prior.core.requests.length + out.before.prior.votes.length+1 := by
  have counts := prefixPosition h.before
  have seq := NativeArithmeticVote.selectedSequence (computationSource binding h.arithmetic)
  change out.vote.sequence = out.before.prior.core.sequence+1 at seq
  have entrySeq := h.shape.2.1
  exact ⟨by omega,by omega,by omega⟩

theorem originalBytes {adapter b policyRaw initial stateRaw snapshot observation nextRaw application out}
    (h : Source binding adapter b policyRaw initial stateRaw snapshot observation nextRaw application out) :
    NativeVoteBytes.encodeFrame out.vote.wire = out.entry.command ∧
    NativeWalBytes.encode adapter.sha256 out.entry = nextRaw :=
  ⟨(NativeVoteBytes.decodedVoteSound h.vote).2,NativeWalBytes.decodedCanonical _ _ _ h.entry⟩

theorem originalGuard {adapter b policyRaw initial stateRaw snapshot observation nextRaw application out}
    (h : Source binding adapter b policyRaw initial stateRaw snapshot observation nextRaw application out) :
    NativeSelectedVote.checkVote (NativeVectorAuthority.policy b) (NativeVectorAuthority.state b)
      (admitted binding out.computation).checked.snapshot.prior.tail
      (admitted binding out.computation).selected (facts out.before) out.vote = none :=
  NativeArithmeticVote.originalGuardStillRejects (computationSource binding h.arithmetic)

theorem voteHashPreimage {adapter b policyRaw initial stateRaw snapshot observation nextRaw application out}
    (h : Source binding adapter b policyRaw initial stateRaw snapshot observation nextRaw application out) :
    NativeVoteBytes.voteId adapter.sha256 (NativeVoteBytes.encodeFrame out.vote.wire) = some out.voteId := by
  rw [(originalBytes binding h).1]
  exact h.id

theorem retainedPrior {adapter b policyRaw initial stateRaw snapshot observation nextRaw application out}
    (h : Source binding adapter b policyRaw initial stateRaw snapshot observation nextRaw application out)
    (stored : NativeConfigReplay.Stored) (mem : stored ∈ out.before.prior.votes) :
    ∃ startup core pre e suffix prior x v id,
      NativeReplayAdmission.prepareWhole adapter.sha256 policyRaw initial = some startup ∧
      NativeCommandReplay.initialMachine (some startup.policy.initialTick) snapshot initial = some core ∧
      NativeWalScan.entries out.before.scan = pre ++ e::suffix ∧
      NativeConfigReplay.run .whole adapter.sha256 policyRaw snapshot ⟨core,[]⟩ pre = some prior ∧
      NativeConfigReplay.VoteEntry .whole adapter.sha256 policyRaw snapshot prior e x v id ∧
      NativeConfigReplay.run .whole adapter.sha256 policyRaw snapshot
        (NativeConfigReplay.added .whole snapshot prior e x v id) suffix = some out.before.prior ∧
      stored = ⟨v,NativeConfigReplay.voteReceipt .whole x e v id,x.admitted.selected.original.parents⟩ := by
  obtain ⟨_,_,_,_,_,replayed,_⟩ := prefixSource h.before
  exact NativeWholeReplay.recoveredPosition replayed mem

theorem noSignatureLoss {b} (out : Next binding b) :
    (NativeVoteBytes.fields out.vote.wire)[8]? = some (NativeVoteBytes.ascii "signature_id",out.vote.wire.signature) ∧
    (NativeVoteBytes.fields out.vote.wire)[12]? = some (NativeVoteBytes.ascii "view",out.vote.wire.view) ∧
    (NativeVoteBytes.fields out.vote.wire)[3]? = some (NativeVoteBytes.ascii "formal_semantics_id",NativeVoteBytes.nativeSemantics) := ⟨rfl,rfl,rfl⟩

end Arithmetic

/-- Pre-aggregate raw source construction suffices for the first PARAMETER.
The current-history tail must also be complete. Authentication stays explicit. -/
def parameterFromSource {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : NativeBindingConstruction.Premises trust codec b s root)
    (journalInitial : Bytes) (snapshot : Option NativeCommandReplay.Snapshot)
    (journalObservation : Option Bytes) (nextRaw : Bytes) :=
  if s.current.recovery.wal.tail = [] then
    check (NativeBindingConstruction.fromRun adapter ran auth) adapter
      (NativeBindingConstruction.originalPreparation ran) journalInitial snapshot journalObservation nextRaw none
  else none

/-- APPLY additionally uses the actually computed finalized corpus, full ROOT,
aggregate extension and source-selected profile. No metadata authentication is inferred. -/
def applyFromSource {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : NativeBindingConstruction.Premises trust codec b s root)
    {id image aggregate authority}
    (source : NativeCertifiedCorpus.check (NativeBindingConstruction.fromRun adapter ran auth) adapter.sha256 b id = some image)
    (made : NativeAggregateBinding.artifact (NativeBindingConstruction.fromRun adapter ran auth) image = some aggregate)
    (aggregateAuth : NativeAggregateBinding.Premises (NativeBindingConstruction.fromRun adapter ran auth) authority image aggregate)
    (journalInitial : Bytes) (snapshot : Option NativeCommandReplay.Snapshot)
    (journalObservation : Option Bytes) (nextRaw : Bytes) :=
  if s.current.recovery.wal.tail = [] then
    check (NativeAggregateBinding.extend (NativeBindingConstruction.fromRun adapter ran auth) adapter source made aggregateAuth)
      adapter (NativeBindingConstruction.originalPreparation ran) journalInitial snapshot journalObservation nextRaw
      (some (image.root,s.originalProfile.id))
  else none

end DeltaReduce.NativeArithmeticPrefix
