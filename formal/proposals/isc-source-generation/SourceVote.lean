import DeltaReduce.NativeVoteBytes
import ProfileSource

/-! T047/T053: exact approved successor V bytes. This reuses primitive framing
and decimal proofs, never the legacy thirteen-field Vote decoder or its sigma.
The twelve-field 2.0.0 grammar keeps the original physical durable sequence.
Canonical decoding alone grants neither signature authority nor producer origin.
No concrete successor semantics identifier is assigned. -/
namespace DeltaReduce.ProfileSource.Vote
open NativeReceiptBytes
open NativeVoteBytes (ascii maxValue maxEnvelope textBytes TextValid readText readTextEncoded
  encodeFields readFields readFieldsEncoded DecimalValid parseDecimal decimalValue ContentId)

structure WireVote where
  bodyHash : Bytes
  context : Bytes
  sequence : Bytes
  height : Bytes
  kind : Bytes
  round : Bytes
  semantics : Bytes
  epoch : Bytes
  validator : Bytes
  view : Bytes
  deriving DecidableEq, Repr

def fields (v : WireVote) : List (Bytes × Bytes) :=
  [(ascii "body_hash",v.bodyHash), (ascii "context_id",v.context),
   (ascii "durable_sequence",v.sequence), (ascii "formal_semantics_id",v.semantics),
   (ascii "height",v.height), (ascii "kind",v.kind), (ascii "round_id",v.round),
   (ascii "schema_version",ascii "2.0.0"),
   (ascii "type_name",ascii "VOTE"), (ascii "validator_epoch_id",v.epoch),
   (ascii "validator_id",v.validator), (ascii "view",v.view)]

def keys : List Bytes := (fields ⟨[],[],[],[],[],[],[],[],[],[]⟩).map Prod.fst

theorem exactKeys (v : WireVote) : (fields v).map Prod.fst = keys := rfl

def fromValues : List Bytes → Option WireVote
  | [body,context,sequence,semantics,height,kind,round,schema,name,epoch,validator,view] =>
    if schema = ascii "2.0.0" ∧ name = ascii "VOTE" then
      some ⟨body,context,sequence,height,kind,round,semantics,epoch,validator,view⟩
    else none
  | _ => none

theorem valuesRetainAllFields (v : WireVote) : fromValues ((fields v).map Prod.snd) = some v := by
  simp [fields, fromValues]

def drcHeader : Bytes := [68,82,67,49,1,0,0,3]
def mapHeader : Bytes := [49,0,0,0,12]
def payload (v : WireVote) : Bytes := mapHeader ++ encodeFields (fields v)
def encodeFrame (v : WireVote) : Bytes := drcHeader ++ sizedBytes (payload v)

def FrameValid (v : WireVote) : Prop :=
  (∀ p ∈ fields v, TextValid p.2) ∧ (encodeFrame v).length ≤ maxEnvelope
instance (v : WireVote) : Decidable (FrameValid v) := by unfold FrameValid; infer_instance

def readFrame (raw : Bytes) : Option WireVote := do
  if raw.length ≤ maxEnvelope then
    let rest ← consume drcHeader raw
    let (body, rest) ← readSection maxEnvelope rest
    if rest = [] then
      let body ← consume mapHeader body
      let (values, rest) ← readFields keys body
      if rest = [] then fromValues values else none
    else none
  else none

theorem frameLength (v : WireVote) : (encodeFrame v).length = 12 + (payload v).length := by
  simp [encodeFrame, sizedBytes, drcHeader, beLength]; omega

theorem readFrameEncoded (v : WireVote) (valid : FrameValid v) :
    readFrame (encodeFrame v) = some v := by
  have small : (payload v).length ≤ maxEnvelope := by have := valid.2; rw [frameLength] at this; omega
  have bound : (payload v).length < 256^4 := by unfold maxEnvelope at small; omega
  unfold readFrame
  rw [if_pos valid.2]
  simp only [encodeFrame, consumeAppend, bind, Option.bind]
  rw [← List.append_nil (sizedBytes (payload v)), readSectionEncoded _ _ _ bound small]
  simp only [↓reduceIte, payload, consumeAppend]
  rw [← exactKeys v, ← List.append_nil (encodeFields (fields v)), readFieldsEncoded _ _ valid.1]
  simpa using valuesRetainAllFields v

def labelByte (b : UInt8) : Prop :=
  (48 ≤ b.toNat ∧ b.toNat ≤ 57) ∨ (65 ≤ b.toNat ∧ b.toNat ≤ 90) ∨
  (97 ≤ b.toNat ∧ b.toNat ≤ 122) ∨ b ∈ [46,95,58,45]
instance (b) : Decidable (labelByte b) := by unfold labelByte; infer_instance

def Label (b : Bytes) : Prop := b ≠ [] ∧ b.length ≤ 128 ∧ ∀ c ∈ b, labelByte c
instance (b) : Decidable (Label b) := by unfold Label; infer_instance

def kinds : List Bytes := [ascii "ROUND_CONFIG",ascii "ISC",ascii "EC",ascii "APC",
  ascii "PARAMETER",ascii "AGGREGATE_ROOT",ascii "APPLY",ascii "VIEW_CHANGE",ascii "ABORT"]
def maxVote (kind : Bytes) : Nat := if kind = ascii "ISC" then 4096 else 946

def IdentitiesValid (v : WireVote) : Prop :=
  ContentId v.bodyHash ∧ ContentId v.semantics ∧ ContentId v.epoch ∧
  Label v.context ∧ v.kind ∈ kinds ∧ Label v.round ∧ Label v.validator ∧
  v.sequence.length ≤ 20 ∧ v.height.length ≤ 20 ∧ v.view.length ≤ 20 ∧
  (encodeFrame v).length ≤ maxVote v.kind
instance (v : WireVote) : Decidable (IdentitiesValid v) := by unfold IdentitiesValid; infer_instance

structure Vote where
  wire : WireVote
  sequence : Nat
  height : Nat
  view : Nat
  deriving DecidableEq, Repr

def VoteValid (v : Vote) : Prop :=
  FrameValid v.wire ∧ IdentitiesValid v.wire ∧ 0 < v.sequence ∧
  parseDecimal v.wire.sequence = some v.sequence ∧
  parseDecimal v.wire.height = some v.height ∧ parseDecimal v.wire.view = some v.view
instance (v : Vote) : Decidable (VoteValid v) := by unfold VoteValid; infer_instance

def interpret (w : WireVote) : Option Vote := do
  let sequence ← parseDecimal w.sequence
  let height ← parseDecimal w.height
  let view ← parseDecimal w.view
  let v := Vote.mk w sequence height view
  if VoteValid v then some v else none

theorem interpretValid (v : Vote) (valid : VoteValid v) : interpret v.wire = some v := by
  rcases valid with ⟨f,i,s,a,b,c⟩
  simp only [interpret, a, b, c, bind, Option.bind]
  cases v
  exact if_pos ⟨f,i,s,a,b,c⟩

theorem interpretedSound {w v} (ok : interpret w = some v) : v.wire = w ∧ VoteValid v := by
  unfold interpret at ok
  cases a : parseDecimal w.sequence with
  | none => simp [a] at ok
  | some sequence =>
    simp only [a, bind, Option.bind] at ok
    cases b : parseDecimal w.height with
    | none => simp [b] at ok
    | some height =>
      simp only [b] at ok
      cases c : parseDecimal w.view with
      | none => simp [c] at ok
      | some view =>
        simp only [c] at ok
        split at ok
        · cases Option.some.inj ok
          exact ⟨rfl, ‹VoteValid _›⟩
        · contradiction

def decodeFrame (raw : Bytes) : Option Vote := do
  let w ← readFrame raw
  let v ← interpret w
  if encodeFrame w = raw then some v else none

theorem decodeFrameEncoded (v : Vote) (valid : VoteValid v) :
    decodeFrame (encodeFrame v.wire) = some v := by
  simp [decodeFrame, readFrameEncoded _ valid.1, interpretValid _ valid]

theorem decodeFrameFromEncoding (v : Vote) (raw : Bytes) (valid : VoteValid v)
    (bytes : encodeFrame v.wire = raw) : decodeFrame raw = some v := by
  rw [← bytes]
  exact decodeFrameEncoded v valid

theorem decodedVoteSound {raw v} (ok : decodeFrame raw = some v) :
    VoteValid v ∧ encodeFrame v.wire = raw := by
  unfold decodeFrame at ok
  cases a : readFrame raw with
  | none => simp [a] at ok
  | some w =>
    simp only [a, bind, Option.bind] at ok
    cases b : interpret w with
    | none => simp [b] at ok
    | some value =>
      simp only [b] at ok
      split at ok
      · cases Option.some.inj ok
        have h := interpretedSound b
        exact ⟨h.2, h.1 ▸ ‹encodeFrame w = raw›⟩
      · contradiction

theorem wireEncodingInjective {a b : WireVote} (va : FrameValid a) (vb : FrameValid b)
    (same : encodeFrame a = encodeFrame b) : a = b := by
  have h := congrArg readFrame same
  rw [readFrameEncoded _ va, readFrameEncoded _ vb] at h
  exact Option.some.inj h

/-- The whole original object, not a relabeled legacy vote. -/
theorem sourceFields {raw v} (ok : decodeFrame raw = some v) :
    encodeFrame v.wire = raw ∧ ContentId v.wire.semantics ∧
    v.wire.kind ∈ kinds ∧ parseDecimal v.wire.sequence = some v.sequence ∧
    0 < v.sequence := by
  have h := decodedVoteSound ok
  exact ⟨h.2,h.1.2.1.2.1,h.1.2.1.2.2.2.2.1,h.1.2.2.2.1,h.1.2.2.1⟩

def domain (kind : Bytes) : Bytes :=
  ascii (if kind = ascii "ISC" then "deltareduce.isc-vote.ed25519.v1"
    else "deltareduce.non-isc-vote.ed25519.v1") ++ [0]

def preimageBytes (kind registry key raw : Bytes) : Bytes :=
  domain kind ++ sizedBytes registry ++ sizedBytes key ++ sizedBytes raw

def signaturePreimage (registry key raw : Bytes) : Option Bytes := do
  let v ← decodeFrame raw
  if ContentId registry ∧ ContentId key then
    some (preimageBytes v.wire.kind registry key raw)
  else none

theorem signableSource {registry key raw message}
    (ok : signaturePreimage registry key raw = some message) :
    ContentId registry ∧ ContentId key ∧ ∃ v, decodeFrame raw = some v ∧
      encodeFrame v.wire = raw ∧ message = preimageBytes v.wire.kind registry key raw := by
  unfold signaturePreimage at ok
  cases h : decodeFrame raw with
  | none => simp [h] at ok
  | some v =>
    simp only [h,bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i ids
    exact ⟨ids.1,ids.2,v,rfl,(decodedVoteSound h).2,(Option.some.inj ok).symm⟩

def voteId (sha : Bytes → Bytes) (raw : Bytes) : Option Bytes :=
  let digest := sha (ascii "deltareduce:003:vote:v2" ++ [0] ++ raw)
  if digest.length = 32 then some (ascii "sha256:" ++ NativeVoteBytes.hexBytes digest) else none

structure Artifact where
  registry : Bytes
  key : Bytes
  vote : Bytes
  signature : Bytes
  deriving DecidableEq, Repr

def artifactHeader (kind : Bytes) : Bytes :=
  (if kind = ascii "ISC" then [73,83,71,49] else [78,83,71,49]) ++ [0,1,0,0]

def artifactBytes (kind : Bytes) (g : Artifact) : Bytes :=
  artifactHeader kind ++ sizedBytes g.registry ++ sizedBytes g.key ++
    sizedBytes g.vote ++ g.signature

/-- A descriptor is not trusted: every field must reconstruct the full original
G, including all signature bytes. Actual Ed25519 verification and independent
key enrollment remain the existing separate source-authentication boundary. -/
def bindArtifact (original : Bytes) (g : Artifact) : Option Vote := do
  let v ← decodeFrame g.vote
  if ContentId g.registry ∧ ContentId g.key ∧ g.signature.length = 64 ∧
      artifactBytes v.wire.kind g = original then some v else none

theorem artifactSource {original g v} (ok : bindArtifact original g = some v) :
    decodeFrame g.vote = some v ∧ encodeFrame v.wire = g.vote ∧
    ContentId g.registry ∧ ContentId g.key ∧ g.signature.length = 64 ∧
    artifactBytes v.wire.kind g = original ∧
    signaturePreimage g.registry g.key g.vote =
      some (preimageBytes v.wire.kind g.registry g.key g.vote) := by
  unfold bindArtifact at ok
  cases h : decodeFrame g.vote with
  | none => simp [h] at ok
  | some out =>
    simp only [h,bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i valid
    cases Option.some.inj ok
    refine ⟨rfl,(decodedVoteSound h).2,valid.1,valid.2.1,valid.2.2.1,valid.2.2.2,?_⟩
    simp [signaturePreimage,h,valid.1,valid.2.1]

theorem artifactComplete {g v}
    (vote : decodeFrame g.vote = some v)
    (ids : ContentId g.registry ∧ ContentId g.key) (signature : g.signature.length = 64) :
    bindArtifact (artifactBytes v.wire.kind g) g = some v := by
  simp [bindArtifact,vote,ids.1,ids.2,signature]

theorem artifactSubstitutionRejected {original g v}
    (vote : decodeFrame g.vote = some v) (different : artifactBytes v.wire.kind g ≠ original) :
    bindArtifact original g = none := by simp [bindArtifact,vote,different]

theorem artifactBound {original g v} (ok : bindArtifact original g = some v) :
    original.length ≤ 226 + maxVote v.wire.kind := by
  obtain ⟨raw,_,registry,key,sig,bytes,_⟩ := artifactSource ok
  rcases (decodedVoteSound raw).1.2.1 with ⟨_,_,_,_,_,_,_,_,_,_,bound⟩
  rw [(decodedVoteSound raw).2] at bound
  have size : (artifactHeader v.wire.kind).length = 8 := by
    unfold artifactHeader
    split <;> rfl
  rw [← bytes]
  simp only [artifactBytes,List.length_append,sizedBytes,beLength,
    size,registry.1,key.1,sig]
  omega

/-- This is an exact byte/context join, not permission to cast a vote. Producer
admission and durable source authority remain separate enclosing obligations. -/
def OwnFields (semantics epoch actor : Bytes) (entry : NativeWalBytes.Entry) (v : Vote) : Prop :=
  entry.kind = 2 ∧ entry.state = [] ∧ entry.effects = [] ∧
  v.wire.semantics = semantics ∧ v.wire.epoch = epoch ∧ v.wire.validator = actor ∧
  v.sequence = entry.sequence
instance (semantics epoch actor entry v) : Decidable (OwnFields semantics epoch actor entry v) := by
  unfold OwnFields; infer_instance

def bindOwn (semantics epoch actor : Bytes) (entry : NativeWalBytes.Entry) : Option Vote := do
  let v ← decodeFrame entry.command
  if OwnFields semantics epoch actor entry v then some v else none

theorem ownSource {semantics epoch actor entry v}
    (ok : bindOwn semantics epoch actor entry = some v) :
    decodeFrame entry.command = some v ∧ encodeFrame v.wire = entry.command ∧
    OwnFields semantics epoch actor entry v := by
  unfold bindOwn at ok
  cases h : decodeFrame entry.command with
  | none => simp [h] at ok
  | some out =>
    simp only [h,bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i fields
    cases Option.some.inj ok
    exact ⟨rfl,(decodedVoteSound h).2,fields⟩

theorem ownComplete {semantics epoch actor entry v}
    (raw : decodeFrame entry.command = some v) (fields : OwnFields semantics epoch actor entry v) :
    bindOwn semantics epoch actor entry = some v := by simp [bindOwn,raw,fields]

theorem physicalSlotRetained {semantics epoch actor entry v}
    (ok : bindOwn semantics epoch actor entry = some v) :
    v.sequence = entry.sequence := (ownSource ok).2.2.2.2.2.2.2.2

/-- Rank is a separate annotation of the unchanged original signed object. -/
theorem originalPosition {first xs before n entry ordinal semantics epoch actor v}
    (continuous : Wal.Continuous first xs)
    (position : (Wal.annotate before xs)[n]? = some (entry,ordinal))
    (ok : bindOwn semantics epoch actor entry = some v) :
    v.sequence = first + n ∧ encodeFrame v.wire = entry.command :=
  ⟨(physicalSlotRetained ok).trans (Wal.physicalPosition continuous before position),
    (ownSource ok).2.1⟩

theorem differentOriginalVotes {first xs before} {n m : Nat} {left right ln rn semantics epoch actor a b}
    (continuous : Wal.Continuous first xs)
    (lp : (Wal.annotate before xs)[n]? = some (left,ln))
    (rp : (Wal.annotate before xs)[m]? = some (right,rn)) (different : n ≠ m)
    (la : bindOwn semantics epoch actor left = some a)
    (rb : bindOwn semantics epoch actor right = some b) :
    a.sequence ≠ b.sequence ∧ a.wire ≠ b.wire := by
  have seq : a.sequence ≠ b.sequence := by
    rw [physicalSlotRetained la,physicalSlotRetained rb]
    exact Wal.distinctPhysicalPositions continuous before lp rp different
  refine ⟨seq,?_⟩
  intro same
  have av := (decodedVoteSound (ownSource la).1).1.2.2.2.1
  have bv := (decodedVoteSound (ownSource rb).1).1.2.2.2.1
  rw [same,bv] at av
  exact seq (Option.some.inj av).symm

end DeltaReduce.ProfileSource.Vote
