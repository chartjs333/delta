import ProfileConfiguration
import SourceVote

/-! T047/T053: whole original CONFIG QC and original delivered-V byte relation.
This is a conjunct of source FinalizeRoundConfig, not signature verification,
delivery authority, phase/time permission or a complete producing history.
The original qc_id field is preserved, not assigned a new hash equation. -/
namespace DeltaReduce.ProfileSource.ConfigurationQC
open NativeReceiptBytes
open NativeVoteBytes (ascii ContentId)
open NativePolicyCodec (Value)

def format : Configuration.Format := Configuration.object [
  ("body_hash",.text),("context_id",.text),("formal_semantics_id",.text),
  ("height",.text),("kind",.text),("qc_id",.text),("quorum_threshold",.uint 4),
  ("round_id",.text),("schema_version",.text),("signer_ids",.vector .text),
  ("type_name",.text),("validator_epoch_id",.text),("view",.text),
  ("vote_ids",.vector .text)]

def encode (value : Value) : Option Bytes := do
  let payload ← Configuration.encode format value
  let raw := [68,82,67,49,1,0,0,4] ++ sizedBytes payload
  if raw.length ≤ NativeVoteBytes.maxEnvelope then some raw else none

structure Certificate where
  original : Value
  body : Bytes
  context : Bytes
  semantics : Bytes
  epoch : Bytes
  round : Bytes
  id : Bytes
  height : Nat
  view : Nat
  threshold : Nat
  signers : List Bytes
  voteIds : List Bytes

def Valid (q : Certificate) : Prop :=
  (∀ id ∈ [q.body,q.context,q.semantics,q.epoch,q.id], ContentId id) ∧
  Vote.Label q.round ∧ (∀ signer ∈ q.signers, Vote.Label signer) ∧
  Configuration.ordered q.signers = true ∧ q.voteIds.Nodup ∧
  (∀ id ∈ q.voteIds, ContentId id) ∧
  q.signers.length = q.voteIds.length ∧ 0 < q.threshold ∧ q.threshold ≤ q.signers.length
instance (q) : Decidable (Valid q) := by unfold Valid; infer_instance

def read (value : Value) : Option Certificate := do
  let body ← Configuration.textField format value "body_hash"
  let context ← Configuration.textField format value "context_id"
  let semantics ← Configuration.textField format value "formal_semantics_id"
  let epoch ← Configuration.textField format value "validator_epoch_id"
  let round ← Configuration.textField format value "round_id"
  let id ← Configuration.textField format value "qc_id"
  let height ← Configuration.decimalField format value "height"
  let view ← Configuration.decimalField format value "view"
  let threshold ← Configuration.numberField format value "quorum_threshold"
  let signers ← Configuration.items (Configuration.lookup format value "signer_ids")
    >>= Configuration.texts
  let votes ← Configuration.items (Configuration.lookup format value "vote_ids")
    >>= Configuration.texts
  let q := Certificate.mk value body context semantics epoch round id height view threshold signers votes
  if Valid q ∧ Configuration.textField format value "kind" = some (ascii "ROUND_CONFIG") ∧
      Configuration.textField format value "type_name" = some (ascii "QUORUM_CERTIFICATE") ∧
      Configuration.textField format value "schema_version" = some (ascii "1.0.0")
  then some q else none

theorem readSource {value q} (ok : read value = some q) :
    q.original = value ∧ Valid q := by
  unfold read at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  repeat (obtain ⟨_,_,ok⟩ := ok)
  split at ok <;> try contradiction
  rename_i valid
  cases Option.some.inj ok
  exact ⟨rfl,valid.1⟩

def decode (original : Bytes) (descriptor : Value) : Option Certificate := do
  if encode descriptor = some original then read descriptor else none

theorem decoded {original descriptor q} (ok : decode original descriptor = some q) :
    encode q.original = some original ∧ read descriptor = some q ∧ Valid q := by
  unfold decode at ok
  split at ok <;> try contradiction
  rename_i exactBytes
  have source := readSource ok
  exact ⟨source.1 ▸ exactBytes,ok,source.2⟩

theorem complete {descriptor q} (parsed : read descriptor = some q)
    {original} (bytes : encode descriptor = some original) :
    decode original descriptor = some q := by simp [decode,bytes,parsed]

/-- One original received occurrence, with the whole source G and its V retained.
The enclosing source checker must authenticate that G with the independently
enrolled key and establish this receiver/cut; those are not fields of a QC. -/
structure Received where
  position : Nat
  receiver : Bytes
  originalG : Bytes
  artifact : Vote.Artifact
  vote : Vote.Vote
  bound : Vote.bindArtifact originalG artifact = some vote

def voteMatches (q : Certificate) (v : Vote.Vote) : Bool := decide (
  v.wire.kind = ascii "ROUND_CONFIG" ∧ v.wire.bodyHash = q.body ∧
  v.wire.context = q.context ∧ v.wire.semantics = q.semantics ∧
  v.wire.epoch = q.epoch ∧ v.wire.round = q.round ∧
  v.height = q.height ∧ v.view = q.view)

def selected (receiver : Bytes) (cut : Nat) (q : Certificate) (rows : List Received) : List Received :=
  rows.filter (fun row => row.receiver == receiver && decide (row.position ≤ cut) && voteMatches q row.vote)

/-- The reference checker rejects a same body/context group with inconsistent
full Vote context. Such originals cannot silently disappear from the group. -/
def GroupCompatible (receiver : Bytes) (cut : Nat) (q : Certificate) (rows : List Received) : Prop :=
  ∀ row ∈ rows, row.receiver = receiver → row.position ≤ cut →
    row.vote.wire.kind = ascii "ROUND_CONFIG" → row.vote.wire.bodyHash = q.body →
    row.vote.wire.context = q.context → voteMatches q row.vote = true
instance (receiver cut q rows) : Decidable (GroupCompatible receiver cut q rows) := by
  unfold GroupCompatible; infer_instance

/-- The exact original signer/vote pairing must occur. Multiple original votes
by one remote signer stay present; no first-q selection or vote-ID rewriting. -/
def Pairing (sha : Bytes → Bytes) (q : Certificate) (rows : List Received) : Prop :=
  q.signers.length = q.voteIds.length ∧
  (∀ signer ∈ q.signers, ∃ row ∈ rows, row.vote.wire.validator = signer) ∧
  (∀ row ∈ rows, row.vote.wire.validator ∈ q.signers) ∧
  ∀ pair ∈ q.signers.zip q.voteIds, ∃ row ∈ rows,
    row.vote.wire.validator = pair.1 ∧ Vote.voteId sha row.artifact.vote = some pair.2
instance (sha q rows) : Decidable (Pairing sha q rows) := by unfold Pairing; infer_instance

structure Joined where
  originalQC : Bytes
  certificate : Certificate
  originalRows : List Received
  matchingRows : List Received

def join (sha : Bytes → Bytes) (receiver : Bytes) (cut : Nat) (raw : Bytes)
    (descriptor : Value) (rows : List Received) : Option Joined := do
  let q ← decode raw descriptor
  let chosen := selected receiver cut q rows
  if q.threshold = 3 ∧ Pairing sha q chosen ∧ GroupCompatible receiver cut q rows then
    some ⟨raw,q,rows,chosen⟩ else none

theorem joined {sha receiver cut raw descriptor rows out}
    (ok : join sha receiver cut raw descriptor rows = some out) :
    out.originalQC = raw ∧ out.originalRows = rows ∧
    decode raw descriptor = some out.certificate ∧
    out.matchingRows = selected receiver cut out.certificate rows ∧
    out.certificate.threshold = 3 ∧ Pairing sha out.certificate out.matchingRows ∧
    GroupCompatible receiver cut out.certificate rows := by
  unfold join at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨q,hq,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i checks
  cases Option.some.inj ok
  exact ⟨rfl,rfl,hq,rfl,checks.1,checks.2.1,checks.2.2⟩

theorem originalQuorum {sha receiver cut raw descriptor rows out}
    (ok : join sha receiver cut raw descriptor rows = some out) :
    encode out.certificate.original = some raw ∧
    3 ≤ out.certificate.signers.length ∧ out.originalRows = rows := by
  have h := joined ok
  have valid := decoded h.2.2.1
  refine ⟨valid.1,?_,h.2.1⟩
  rcases valid.2.2 with ⟨_,_,_,_,_,_,_,_,enough⟩
  simpa [h.2.2.2.2.1] using enough

theorem everyPairIsOriginal {sha receiver cut raw descriptor rows out signer id}
    (ok : join sha receiver cut raw descriptor rows = some out)
    (pair : (signer,id) ∈ out.certificate.signers.zip out.certificate.voteIds) :
    ∃ row ∈ rows, row.receiver = receiver ∧ row.position ≤ cut ∧
      voteMatches out.certificate row.vote = true ∧ row.vote.wire.validator = signer ∧
      Vote.voteId sha row.artifact.vote = some id ∧
      Vote.encodeFrame row.vote.wire = row.artifact.vote := by
  have h := joined ok
  obtain ⟨row,member,who,identity⟩ := h.2.2.2.2.2.1.2.2.2 _ pair
  rw [h.2.2.2.1] at member
  have chosen := List.mem_filter.mp member
  simp only [Bool.and_eq_true,beq_iff_eq,decide_eq_true_eq] at chosen
  exact ⟨row,chosen.1,chosen.2.1.1,chosen.2.1.2,chosen.2.2,who,identity,
    (Vote.artifactSource row.bound).2.1⟩

theorem joinComplete {sha receiver cut raw descriptor rows q}
    (bytes : decode raw descriptor = some q) (threshold : q.threshold = 3)
    (pairs : Pairing sha q (selected receiver cut q rows))
    (compatible : GroupCompatible receiver cut q rows) :
    join sha receiver cut raw descriptor rows = some ⟨raw,q,rows,selected receiver cut q rows⟩ := by
  simp [join,bytes,threshold,pairs,compatible]

/-- The existing native CONFIG context domain and uint64 encoding. -/
def contextId (sha : Bytes → Bytes) (height : Nat) (epoch : Bytes) : Option Bytes :=
  let digest := sha (ascii "deltareduce.vote-context.config.v1" ++ [0] ++
    be 8 height ++ be 8 epoch.length ++ epoch)
  if digest.length = 32 then some (ascii "sha256:" ++ NativeVoteBytes.hexBytes digest) else none

def Association (sha : Bytes → Bytes) (configRaw : Bytes)
    (c : Configuration.Body) (q : Certificate) : Prop :=
  NativeStateBytes.contentId sha (ascii "deltareduce:003:round-config:v1") configRaw = some q.body ∧
  contextId sha c.height c.epoch = some q.context ∧
  q.semantics = c.semantics ∧ q.epoch = c.epoch ∧ q.round = c.round ∧
  q.height = c.height ∧ q.view = c.view ∧ q.threshold = c.quorum ∧
  ∀ signer ∈ q.signers, signer ∈ c.validators
instance (sha raw c q) : Decidable (Association sha raw c q) := by
  unfold Association; infer_instance

structure Bound where
  originalConfig : Bytes
  config : Configuration.Body
  quorum : Joined

def check (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (receiver : Bytes) (cut : Nat) (configRaw qcRaw : Bytes)
    (descriptor : Value) (rows : List Received) : Option Bound := do
  let c ← Configuration.checkEnrolled enrolled configRaw
  let q ← join sha receiver cut qcRaw descriptor rows
  if receiver ∈ c.validators ∧ Association sha configRaw c q.certificate then
    some ⟨configRaw,c,q⟩ else none

theorem checked {sha enrolled receiver cut configRaw qcRaw descriptor rows out}
    (ok : check sha enrolled receiver cut configRaw qcRaw descriptor rows = some out) :
    out.originalConfig = configRaw ∧
    Configuration.checkEnrolled enrolled configRaw = some out.config ∧
    join sha receiver cut qcRaw descriptor rows = some out.quorum ∧
    receiver ∈ out.config.validators ∧
    Association sha configRaw out.config out.quorum.certificate := by
  unfold check at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨c,hc,q,hq,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i fields
  cases Option.some.inj ok
  exact ⟨rfl,hc,hq,fields.1,fields.2⟩

theorem checkComplete {sha enrolled receiver cut configRaw qcRaw descriptor rows c q}
    (config : Configuration.checkEnrolled enrolled configRaw = some c)
    (qc : join sha receiver cut qcRaw descriptor rows = some q)
    (receiverEnrolled : receiver ∈ c.validators)
    (association : Association sha configRaw c q.certificate) :
    check sha enrolled receiver cut configRaw qcRaw descriptor rows = some ⟨configRaw,c,q⟩ := by
  simp [check,config,qc,receiverEnrolled,association]

/-- Whole signed configuration and whole original QC remain separate artifacts.
No root/body identity substitutes for an original witness; all original receipt
occurrences stay available to the enclosing complete-history checker. -/
theorem originalConfigurationAndQuorum {sha enrolled receiver cut configRaw qcRaw descriptor rows out}
    (ok : check sha enrolled receiver cut configRaw qcRaw descriptor rows = some out) :
    Configuration.encodeFrame out.config.originalValue = some configRaw ∧
    encode out.quorum.certificate.original = some qcRaw ∧
    out.quorum.originalQC = qcRaw ∧ out.quorum.originalRows = rows ∧
    3 ≤ out.quorum.certificate.signers.length ∧
    Association sha configRaw out.config out.quorum.certificate := by
  have h := checked ok
  have config := Configuration.wholeSource (Configuration.enrolledSource h.2.1).1
  have qc := joined h.2.2.1
  have quorum := originalQuorum h.2.2.1
  exact ⟨config.2.1,quorum.1,qc.1,qc.2.1,quorum.2.1,h.2.2.2.2⟩

theorem exactSignerCover {sha receiver cut raw descriptor rows out signer}
    (ok : join sha receiver cut raw descriptor rows = some out) :
    signer ∈ out.certificate.signers ↔
      ∃ row ∈ selected receiver cut out.certificate rows, row.vote.wire.validator = signer := by
  have h := joined ok
  have pairs := h.2.2.2.2.2.1
  rw [← h.2.2.2.1]
  constructor
  · exact pairs.2.1 signer
  · rintro ⟨row,member,same⟩
    rw [← same]
    exact pairs.2.2.1 row member

end DeltaReduce.ProfileSource.ConfigurationQC
