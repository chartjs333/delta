import DeltaReduce.NativePolicyBytes
import DeltaReduce.NativeStateBytes

/-! Computed CONFIG admission for the explicitly empty certificate-graph
subdomain. This is not admission for the other eight actions or full recovery.
SHA is a named byte function; initialization and caller runtime facts are not
authenticated by this module. No Boolean certificate approval is accepted. -/
namespace DeltaReduce.NativeConfigAdmission
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativePolicyBytes (Policy Candidate)
open NativeStateBytes (State)
open NativeVoteBytes (Vote ContentId)

theorem encodedField {name a b x y left right}
    (head : encode a x = some left) (tail : encode b y = some right) :
    encode (.field name a b) (.pair x y) = some (left ++ right) := by
  simp only [NativePolicyCodec.encode,head,tail,bind,Option.bind]

theorem encodedCons {fmt x xs left right}
    (head : encode fmt x = some left) (tail : writeMany (encode fmt) xs = some right) :
    writeMany (encode fmt) (x::xs) = some (left ++ right) := by
  simp only [writeMany,head,tail,bind,Option.bind]

theorem encodedVector {bound fmt vs body}
    (size : vs.length ≤ bound ∧ vs.length < 256^4)
    (encoded : writeMany (encode fmt) vs = some body) :
    encode (.vector bound fmt) (.items vs) = some (be 4 vs.length ++ body) := by
  simp only [NativePolicyCodec.encode,if_pos size,encoded,bind,Option.bind]

def ascii := NativeVoteBytes.ascii
def getText (fmt : Format) (v : Value) (key : String) : Option Bytes :=
  lookup fmt v key >>= NativePolicyBytes.text
def getTexts (fmt : Format) (v : Value) (key : String) : Option (List Bytes) := do
  let vs ← lookup fmt v key >>= NativePolicyBytes.items
  vs.mapM NativePolicyBytes.text
def isEmpty (v : Value) : Bool := match v with | .items [] => true | _ => false
def emptyFields : Format → Value → Bool
  | .end, .end => true
  | .field _ _ rest, .pair value tail => isEmpty value && emptyFields rest tail
  | _, _ => false
def graphEmpty : Value → Bool
  | .pair _ (.pair _ (.pair _ (.pair _ (.pair _ (.pair _ rest))))) =>
    -- All 27 vectors after the four scalar/two config fields must be empty.
    match fmtSnapshot with
    | .field _ _ (.field _ _ (.field _ _ (.field _ _ (.field _ _ (.field _ _ fmt))))) =>
      emptyFields fmt rest
    | _ => false
  | _ => false

def labelByte (b : UInt8) : Prop :=
  (48 ≤ b.toNat ∧ b.toNat ≤ 57) ∨ (65 ≤ b.toNat ∧ b.toNat ≤ 90) ∨
  (97 ≤ b.toNat ∧ b.toNat ≤ 122) ∨ b.toNat ∈ [46,95,58,45]
instance (b : UInt8) : Decidable (labelByte b) := by unfold labelByte; infer_instance
def Label (b : Bytes) : Prop := b ≠ [] ∧ b.length ≤ 128 ∧ ∀ x ∈ b, labelByte x
instance (b : Bytes) : Decidable (Label b) := by unfold Label; infer_instance

def HeaderChecks (p : Policy) (s : State) : Prop :=
  NativePolicyBytes.Canonical p ∧ p.localValidator ≠ [] ∧ ContentId p.epoch ∧
  (∀ v ∈ p.validators, v ≠ []) ∧ p.validators.length % 3 = 1 ∧
  p.localValidator ∈ p.validators ∧ Label p.round ∧ ContentId p.config ∧
  p.softDeadline < p.hardDeadline ∧ s.wire.round = p.round ∧
  s.wire.config = p.config ∧ 0 < s.height
instance (p : Policy) (s : State) : Decidable (HeaderChecks p s) := by
  unfold HeaderChecks; infer_instance

def configPreimage (height : Nat) (epoch : Bytes) : Bytes :=
  ascii "deltareduce.vote-context.config.v1" ++ [0] ++
  be 8 height ++ be 8 epoch.length ++ epoch
def configContext (sha : Bytes → Bytes) (height : Nat) (epoch : Bytes) : Option Bytes :=
  let digest := sha (configPreimage height epoch)
  if digest.length = 32 then some (ascii "sha256:" ++ NativeVoteBytes.hexBytes digest) else none

def ConfigIds (p : Policy) (ids : List Bytes) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT ids = true ∧
  ∀ id ∈ ids, id = p.config
instance (p : Policy) (ids : List Bytes) : Decidable (ConfigIds p ids) := by
  unfold ConfigIds; infer_instance

def parentTailEmpty : Format → Value → Bool
  | .end, .end => true
  | .field _ _ rest, .pair (.text []) tail => parentTailEmpty rest tail
  | _, _ => false
def configParents (v : Value) : Option (Bytes × Bytes) :=
  match v, fmtParents with
  | .pair (.text config) (.pair (.text checkpoint) rest),
      .field _ _ (.field _ _ fmt) =>
    if parentTailEmpty fmt rest then some (config,checkpoint) else none
  | _, _ => none

structure Bound where
  policy : Policy
  state : State
  candidate : Candidate
  checkpoint : Bytes
  schema : Bytes
  arithmetic : Bytes
  accumulator : Bytes
  proposed : List Bytes
  finalized : List Bytes
  snapshotId : Bytes
  context : Bytes

def Checks (b : Bound) : Prop :=
  HeaderChecks b.policy b.state ∧ graphEmpty b.policy.snapshot = true ∧
  ContentId b.schema ∧ ContentId b.arithmetic ∧
  (b.accumulator = [] ∨ ContentId b.accumulator) ∧
  ConfigIds b.policy b.proposed ∧ ConfigIds b.policy b.finalized ∧
  b.candidate.action = 1 ∧ b.candidate.body = b.policy.config ∧
  b.candidate.body ∈ b.proposed ∧ b.candidate.height = b.state.height ∧
  b.candidate.view = b.state.view ∧ b.candidate.context = b.context ∧
  ContentId b.checkpoint
instance (b : Bound) : Decidable (Checks b) := by unfold Checks; infer_instance

def singleCandidate (cs : List Candidate) : Option Candidate :=
  match cs with | [c] => some c | _ => none

def bindConfig (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let c ← singleCandidate p.candidates
  let id ← getText fmtSnapshot p.snapshot "state_id"
  let computed ← NativeStateBytes.contentId sha NativeStateBytes.stateDomain
    (NativeStateBytes.encodeState s.wire)
  let schema ← getText fmtSnapshot p.snapshot "parameter_schema_id"
  let arithmetic ← getText fmtSnapshot p.snapshot "arithmetic_profile_id"
  let accumulator ← getText fmtSnapshot p.snapshot "required_accumulator_proof_id"
  let proposed ← getTexts fmtSnapshot p.snapshot "proposed_round_config_ids"
  let finalized ← getTexts fmtSnapshot p.snapshot "finalized_round_config_ids"
  let (config,checkpoint) ← configParents c.parents
  let context ← configContext sha s.height p.epoch
  let b := Bound.mk p s c checkpoint schema arithmetic accumulator proposed finalized id context
  if id = computed ∧ ContentId id ∧ config = p.config ∧ Checks b then some b else none

def SourceChecks (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop :=
  b.policy = p ∧ b.state = s ∧ p.candidates = [b.candidate] ∧
  getText fmtSnapshot p.snapshot "state_id" = some b.snapshotId ∧
  NativeStateBytes.contentId sha NativeStateBytes.stateDomain
    (NativeStateBytes.encodeState s.wire) = some b.snapshotId ∧ ContentId b.snapshotId ∧
  getText fmtSnapshot p.snapshot "parameter_schema_id" = some b.schema ∧
  getText fmtSnapshot p.snapshot "arithmetic_profile_id" = some b.arithmetic ∧
  getText fmtSnapshot p.snapshot "required_accumulator_proof_id" = some b.accumulator ∧
  getTexts fmtSnapshot p.snapshot "proposed_round_config_ids" = some b.proposed ∧
  getTexts fmtSnapshot p.snapshot "finalized_round_config_ids" = some b.finalized ∧
  configParents b.candidate.parents = some (p.config,b.checkpoint) ∧
  configContext sha s.height p.epoch = some b.context ∧ Checks b

theorem bindConfigSound {sha p s b} (ok : bindConfig sha p s = some b) :
    SourceChecks sha p s b := by
  unfold bindConfig at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨c,hc,id,hi,computed,hh,schema,hs,arithmetic,ha,accumulator,hu,
    proposed,hp,finalized,hf,parents,hr,ht⟩ := ok
  rcases parents with ⟨config,checkpoint⟩
  obtain ⟨context,hx,last⟩ := ht
  dsimp only at last
  split at last
  · rename_i checks
    cases Option.some.inj last
    have singleton : p.candidates = [c] := by
      unfold singleCandidate at hc
      split at hc <;> simp_all
    rcases checks with ⟨same,valid,parent,checks⟩
    subst computed; subst config
    exact ⟨rfl,rfl,singleton,hi,hh,valid,hs,ha,hu,hp,hf,hr,hx,checks⟩
  · contradiction

theorem bindConfigComplete {sha p s b} (h : SourceChecks sha p s b) :
    bindConfig sha p s = some b := by
  rcases h with ⟨policy,state,cs,id,hashed,valid,schema,arithmetic,accumulator,
    proposed,finalized,parents,context,checks⟩
  unfold bindConfig
  rw [cs]
  simp only [singleCandidate,bind,Option.bind]
  rw [id,hashed,schema,arithmetic,accumulator,proposed,finalized,parents,context]
  simp only [bind,Option.bind]
  have rebuilt : Bound.mk p s b.candidate b.checkpoint b.schema b.arithmetic b.accumulator
      b.proposed b.finalized b.snapshotId b.context = b := by
    rw [← policy,← state]
  rw [rebuilt]
  simp only [true_and,ite_true,valid,checks]

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindConfig sha p s

theorem prepareSound {sha policyRaw stateRaw b}
    (ok : prepare sha policyRaw stateRaw = some b) :
    ∃ tree, NativePolicyBytes.decodePolicy policyRaw = some (tree,b.policy) ∧
    NativeStateBytes.decodeState stateRaw = some b.state ∧
    SourceChecks sha b.policy b.state b := by
  unfold prepare at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := ok
  have h := bindConfigSound hb
  exact ⟨tree,h.1 ▸ hp,h.2.1 ▸ hs,by simpa only [h.1,h.2.1] using h⟩

structure RuntimeFacts where
  tick : Nat
  ready : Bool
  invalidated : Bool
  recovery : Bool
  expectedSequence : Nat
  deriving DecidableEq, Repr

def VoteChecks (b : Bound) (r : RuntimeFacts) (v : Vote) : Prop :=
  NativeVoteBytes.VoteValid v ∧ v.wire.kind = ascii "ROUND_CONFIG" ∧
  v.wire.validator = b.policy.localValidator ∧ v.wire.epoch = b.policy.epoch ∧
  v.wire.round = b.state.wire.round ∧ v.height = b.state.height ∧ v.view = b.state.view ∧
  v.wire.context = b.candidate.context ∧ v.wire.bodyHash = b.candidate.body ∧
  b.checkpoint = b.state.wire.parent ∧ v.sequence = r.expectedSequence ∧
  (r.recovery = true ∨ r.ready = true) ∧ r.invalidated = false ∧
  b.state.wire.phase = ascii "TICKETING_OPEN" ∧ r.tick < b.policy.hardDeadline ∧
  r.tick < 256^8 ∧ r.expectedSequence < 256^8
instance (b : Bound) (r : RuntimeFacts) (v : Vote) : Decidable (VoteChecks b r v) := by
  unfold VoteChecks; infer_instance

def checkVote (b : Bound) (r : RuntimeFacts) (v : Vote) : Option Vote :=
  if VoteChecks b r v then some v else none

def fromBytes (sha : Bytes → Bytes) (policyRaw stateRaw voteRaw : Bytes)
    (r : RuntimeFacts) : Option (Bound × Vote) := do
  let b ← prepare sha policyRaw stateRaw
  let v ← NativeVoteBytes.decodeFrame voteRaw
  let v ← checkVote b r v
  some (b,v)

theorem checkSound {b r v out} (ok : checkVote b r v = some out) :
    out = v ∧ VoteChecks b r v := by
  unfold checkVote at ok; split at ok
  · exact ⟨(Option.some.inj ok).symm,‹VoteChecks _ _ _›⟩
  · contradiction

theorem checkComplete {b r v} (ok : VoteChecks b r v) : checkVote b r v = some v := by
  simp [checkVote,ok]

theorem fromBytesSound {sha policyRaw stateRaw voteRaw r b v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v)) :
    prepare sha policyRaw stateRaw = some b ∧ NativeVoteBytes.decodeFrame voteRaw = some v ∧
    VoteChecks b r v := by
  unfold fromBytes at ok
  cases a : prepare sha policyRaw stateRaw with
  | none => simp [a] at ok
  | some bound =>
    cases q : NativeVoteBytes.decodeFrame voteRaw with
    | none => simp [a,q] at ok
    | some vote =>
      cases t : checkVote bound r vote with
      | none => simp [a,q,t] at ok
      | some out =>
        simp only [a,q,t,bind,Option.bind,Option.some.injEq] at ok
        cases ok
        obtain ⟨eq,checks⟩ := checkSound t
        cases eq
        exact ⟨rfl,rfl,checks⟩

theorem byteIdentity {sha policyRaw stateRaw voteRaw r b v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v)) :
    NativeVoteBytes.encodeFrame v.wire = voteRaw :=
  (NativeVoteBytes.decodedVoteSound (fromBytesSound ok).2.1).2

theorem noArithmetic {b r v out} (ok : checkVote b r v = some out) :
    v.wire.kind = ascii "ROUND_CONFIG" := (checkSound ok).2.2.1

theorem mustBeRecoveredLive {b r v out} (ok : checkVote b r v = some out)
    (live : r.recovery = false) : r.ready = true := by
  have h := (checkSound ok).2
  unfold VoteChecks at h
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,ready,_⟩
  rcases ready with ready | ready
  · simp [live] at ready
  · exact ready

theorem invalidatedRejects {b r v} (h : r.invalidated = true) : checkVote b r v = none := by
  unfold checkVote
  split
  · rename_i checks
    have g := checks.2.2.2.2.2.2.2.2.2.2.2.2.1
    simp [h] at g
  · rfl

theorem originalSequence {b r v out} (ok : checkVote b r v = some out) :
    out.sequence = r.expectedSequence := by
  have h := checkSound ok
  rw [h.1]
  exact h.2.2.2.2.2.2.2.2.2.2.2.1

theorem deadlineRetained {b r v out} (ok : checkVote b r v = some out) :
    r.tick < b.policy.hardDeadline := (checkSound ok).2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1

theorem contextPreimage {sha height epoch id} (ok : configContext sha height epoch = some id) :
    (sha (configPreimage height epoch)).length = 32 ∧
    id = ascii "sha256:" ++ NativeVoteBytes.hexBytes (sha (configPreimage height epoch)) := by
  unfold configContext at ok
  dsimp only at ok
  split at ok
  · exact ⟨‹_›,(Option.some.inj ok).symm⟩
  · contradiction

theorem admittedSource {sha policyRaw stateRaw voteRaw r b v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v)) :
    SourceChecks sha b.policy b.state b ∧ VoteChecks b r v := by
  have h := fromBytesSound ok
  exact ⟨(prepareSound h.1).choose_spec.2.2,h.2.2⟩

theorem admittedOriginalBytes {sha policyRaw stateRaw voteRaw r b v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v)) :
    NativeStateBytes.StateValid b.state ∧
    NativeStateBytes.encodeState b.state.wire = stateRaw ∧
    NativeVoteBytes.encodeFrame v.wire = voteRaw ∧
    ∃ tree body, NativePolicyBytes.extract tree = some b.policy ∧
      NativePolicyCodec.encode fmtPolicy tree = some body ∧
      policyRaw = NativePolicyBytes.header ++ body := by
  have h := fromBytesSound ok
  obtain ⟨tree,decoded,state,_⟩ := prepareSound h.1
  obtain ⟨body,encoded,bytes⟩ := (NativePolicyBytes.decoded decoded).2
  exact ⟨(NativeStateBytes.stateSound state).1,(NativeStateBytes.stateSound state).2,
    byteIdentity ok,tree,body,NativePolicyBytes.acceptedExtraction decoded,encoded,bytes.symm⟩

theorem fromComponents {sha policyRaw stateRaw voteRaw r b v}
    (policy : prepare sha policyRaw stateRaw = some b)
    (vote : NativeVoteBytes.decodeFrame voteRaw = some v)
    (checks : VoteChecks b r v) : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v) := by
  simp only [fromBytes,policy,vote,checkComplete checks,bind,Option.bind]

theorem nonemptyGraphRejects {sha p s b}
    (graph : graphEmpty p.snapshot = false) : bindConfig sha p s ≠ some b := by
  intro ok
  have h := bindConfigSound ok
  -- Recover the named Checks conjunct without accepting a separate approval.
  have checked : Checks b := by
    rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,hc⟩
    exact hc
  have policy := (bindConfigSound ok).1
  have eq := checked.2.1
  simp only [policy,graph,Bool.false_eq_true] at eq

end DeltaReduce.NativeConfigAdmission
