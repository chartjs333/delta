import ProfileSelectedVote
import ProfileVoteJournal

/-! T047/T053. Join one original kind-2 entry to the exact whole policy at its
source position, native admission, original anti-equivocation cache and derived
DVREC001 receipt. Physical slot and public ordinal remain distinct. This does
not infer policy-producing origin or a successful durability barrier. -/
namespace DeltaReduce.ProfileSource.VoteRecord
open NativeReceiptBytes (Bytes Receipt)
open NativePolicyCodec (Value)
open NativeWalBytes (Entry)
open NativeConfigAdmission (RuntimeFacts)

structure Bound where
  admitted : SelectedVote.Bound
  id : Bytes
  receipt : Receipt

def receipt (e : Entry) (v : SelectedVote.Bound) (id : Bytes) : Receipt :=
  ⟨v.selected.original.action,e.sequence,e.command,id,v.vote.wire.context⟩

def bind (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) (facts : RuntimeFacts)
    (previous : Nat) (seen : List Bytes) (entry : Entry) : Option Bound := do
  if entry.kind = 2 ∧ entry.sequence = previous+1 ∧ entry.sequence < 256^8 ∧
      entry.state = [] ∧ entry.effects = [] ∧ facts.expectedSequence = entry.sequence ∧
      NativeWalBytes.policyId sha policyRaw = some entry.record then
    let admitted ← SelectedVote.bind sha enrolled actor configRaw stateRaw policyRaw
      stateValue originals facts entry.command
    let id ← Vote.voteId sha entry.command
    let result := receipt entry admitted id
    if NativeReceiptBytes.Valid result ∧ admitted.vote.wire.context ∉ seen then
      some ⟨admitted,id,result⟩
    else none
  else none

structure Source (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) (facts : RuntimeFacts)
    (previous : Nat) (seen : List Bytes) (entry : Entry) (out : Bound) : Prop where
  kind : entry.kind = 2
  position : entry.sequence = previous+1
  width : entry.sequence < 256^8
  noState : entry.state = []
  noEffects : entry.effects = []
  sequence : facts.expectedSequence = entry.sequence
  policy : NativeWalBytes.policyId sha policyRaw = some entry.record
  admitted : SelectedVote.bind sha enrolled actor configRaw stateRaw policyRaw stateValue
    originals facts entry.command = some out.admitted
  id : Vote.voteId sha entry.command = some out.id
  exactReceipt : out.receipt = receipt entry out.admitted out.id
  valid : NativeReceiptBytes.Valid out.receipt
  fresh : out.admitted.vote.wire.context ∉ seen

theorem boundSource {sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
    previous seen entry out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen entry = some out) :
    Source sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen entry out := by
  unfold bind at ok
  split at ok <;> try contradiction
  rename_i shape
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨admitted,ha,id,hi,last⟩ := ok
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨shape.1,shape.2.1,shape.2.2.1,shape.2.2.2.1,shape.2.2.2.2.1,
    shape.2.2.2.2.2.1,shape.2.2.2.2.2.2,ha,hi,rfl,valid.1,valid.2⟩

theorem complete {sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
    previous seen entry out}
    (h : Source sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen entry out) :
    bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen entry = some out := by
  unfold bind
  rw [if_pos ⟨h.kind,h.position,h.width,h.noState,h.noEffects,h.sequence,h.policy⟩]
  rw [h.admitted]
  simp only [Bind.bind,Option.bind]
  rw [h.id]
  dsimp only
  rw [← h.exactReceipt,if_pos (And.intro h.valid h.fresh)]

theorem originalReceipt {sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
    previous seen entry out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen entry = some out) :
    out.receipt.frame = entry.command ∧ out.receipt.sequence = entry.sequence ∧
    out.admitted.vote.sequence = entry.sequence ∧
    out.receipt.context = out.admitted.vote.wire.context ∧
    NativeReceiptBytes.decode (NativeReceiptBytes.encode out.receipt) = some out.receipt := by
  have h := boundSource ok
  have vote := SelectedVote.originalVoteBytes h.admitted
  refine ⟨?_,?_,vote.2.2.1.trans h.sequence,?_,?_⟩
  · rw [h.exactReceipt]; rfl
  · rw [h.exactReceipt]; rfl
  · rw [h.exactReceipt]; rfl
  · exact NativeReceiptBytes.decodeEncoded _ h.valid

theorem cannotRelabelPolicy {sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
    previous seen entry out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen entry = some out) :
    entry.record = NativeVoteBytes.hexBytes (sha policyRaw) ∧
    NativeHeader.policyBytes out.admitted.state.installed.policy.source = some policyRaw := by
  have h := boundSource ok
  exact ⟨(NativeWalBytes.policyUsesWholeBytes _ _ _ h.policy).1,
    (InstalledState.allOriginalBytes (SelectedVote.boundSource h.admitted).1).1⟩

theorem currentArithmeticGuard {sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
    previous seen entry out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen entry = some out) : out.receipt.action ≠ 5 ∧ out.receipt.action ≠ 7 := by
  have h := boundSource ok
  rw [h.exactReceipt]
  exact (SelectedVote.originalVoteBytes h.admitted).2.2.2

structure Original where
  raw : Bytes
  entry : Entry
  bound : Bound

/-- Decode the existing original kind-2 DRW1 frame, without selecting another
policy or rewriting the signed physical sequence. Kind 3 has its own W1 rule. -/
def fromBytes (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) (facts : RuntimeFacts)
    (previous : Nat) (seen : List Bytes) (raw : Bytes) : Option Original := do
  let entry ← NativeWalBytes.decode sha raw
  let bound ← bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals
    facts previous seen entry
  some ⟨raw,entry,bound⟩

theorem fromOriginal {sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
    previous seen raw out}
    (ok : fromBytes sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen raw = some out) :
    out.raw = raw ∧ NativeWalBytes.decode sha raw = some out.entry ∧
    bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen out.entry = some out.bound := by
  simp only [fromBytes,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨entry,he,bound,hb,last⟩ := ok
  cases Option.some.inj last
  exact ⟨rfl,he,hb⟩

theorem allOriginalBytes {sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
    previous seen raw out}
    (ok : fromBytes sha enrolled actor configRaw stateRaw policyRaw stateValue originals facts
      previous seen raw = some out) :
    NativeWalBytes.encode sha out.entry = raw ∧ out.bound.receipt.frame = out.entry.command ∧
    out.bound.receipt.sequence = out.entry.sequence ∧
    NativeHeader.policyBytes out.bound.admitted.state.installed.policy.source = some policyRaw := by
  have h := fromOriginal ok
  have receipt := originalReceipt h.2.2
  exact ⟨NativeWalBytes.decodedCanonical _ _ _ h.2.1,receipt.1,receipt.2.1,
    (cannotRelabelPolicy h.2.2).2⟩

end DeltaReduce.ProfileSource.VoteRecord
