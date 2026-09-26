import DeltaReduce.NativeIscCertificate

/-! Exact native seed transcript and checked ISC parent edge.
Seed/share/profile identities remain primitives, not authenticated randomness. -/
namespace DeltaReduce.NativeSeedTranscript
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeInputSetBody (Context contextValue readContext ContextValid)
open NativeIscCertificate (quoted array object number readTexts)

structure Transcript where
  context : Context
  isc : Bytes
  seed : Bytes
  profile : Bytes
  shares : List Bytes
  deriving DecidableEq, Repr

def value (t : Transcript) : Value := .pair (contextValue t.context)
  (.pair (.text t.isc) (.pair (.text t.seed) (.pair (.text t.profile)
    (.pair (.items (t.shares.map Value.text)) .end))))

def read : Value → Option Transcript
  | .pair ctx (.pair (.text isc) (.pair (.text seed) (.pair (.text profile)
      (.pair (.items shares) .end)))) => do
    let c ← readContext ctx
    let ss ← readTexts shares
    some ⟨c,isc,seed,profile,ss⟩
  | _ => none

theorem valueRead (t) : read (value t) = some t := by
  cases t
  simp only [value,read,NativeInputSetBody.contextRead,NativeIscCertificate.textsRead,
    bind,Option.bind]

theorem readOriginal {v t} (h : read v = some t) : v = value t := by
  unfold read at h
  split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,ss,hs,last⟩ := h
  cases Option.some.inj last
  simp only [value,← NativeInputSetBody.contextOriginal hc,← NativeIscCertificate.textsOriginal hs]

def Valid (expected : Context) (t : Transcript) : Prop :=
  ContextValid t.context ∧ t.context = expected ∧ NativeVoteBytes.ContentId t.isc ∧
  NativeVoteBytes.ContentId t.seed ∧ NativeVoteBytes.ContentId t.profile ∧
  0 < t.shares.length ∧ t.shares.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT t.shares = true ∧
  ∀ share ∈ t.shares, NativeVoteBytes.ContentId share
instance (expected t) : Decidable (Valid expected t) := by unfold Valid; infer_instance

-- Pure constructors do not authenticate the primitive seed or share IDs.
def fields (t : Transcript) : List (String × Bytes) :=
  [("arithmetic_profile_id",quoted t.context.arithmetic),
   ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),
   ("height",number t.context.height),("input_set_certificate_id",quoted t.isc),
   ("parameter_schema_id",quoted t.context.schema),("round_config_id",quoted t.context.config),
   ("round_id",quoted t.context.round),("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),
   ("seed_id",quoted t.seed),("seed_profile_id",quoted t.profile),
   ("share_ids",array (t.shares.map quoted)),
   ("type_name",quoted (NativeVoteBytes.ascii "SEED_TRANSCRIPT")),
   ("validator_epoch_id",quoted t.context.epoch),("view",number t.context.view)]
def json (t : Transcript) : Bytes := object (fields t)
def domain : Bytes := NativeVoteBytes.ascii "deltareduce.008.seed-transcript.v1"
def id (sha : Bytes → Bytes) (t : Transcript) : Option Bytes :=
  NativeStateBytes.contentId sha domain (json t)

structure Checked where
  transcript : Transcript
  source : Value
  id : Bytes

def check (sha : Bytes → Bytes) (expected : Context) (finalized : List Bytes)
    (source : Value) : Option Checked := do
  let t ← read source
  if Valid expected t ∧ t.isc ∈ finalized then
    let tid ← id sha t
    some ⟨t,source,tid⟩
  else none

def Source (sha : Bytes → Bytes) (expected : Context) (finalized : List Bytes)
    (source : Value) (out : Checked) : Prop :=
  out.source = source ∧ read source = some out.transcript ∧ source = value out.transcript ∧
  Valid expected out.transcript ∧ out.transcript.isc ∈ finalized ∧
  id sha out.transcript = some out.id

theorem checkedSource {sha expected finalized source out}
    (h : check sha expected finalized source = some out) : Source sha expected finalized source out := by
  unfold check at h
  cases hr : read source with
  | none => simp [hr] at h
  | some t =>
    simp only [hr,bind,Option.bind] at h
    split at h <;> try contradiction
    rename_i checks
    cases hi : id sha t with
    | none => simp [hi] at h
    | some tid =>
      simp only [hi] at h
      cases Option.some.inj h
      exact ⟨rfl,hr,readOriginal hr,checks.1,checks.2,hi⟩

theorem fromComponents {sha expected finalized source t tid}
    (parsed : read source = some t) (valid : Valid expected t)
    (parent : t.isc ∈ finalized) (hashed : id sha t = some tid) :
    check sha expected finalized source = some ⟨t,source,tid⟩ := by
  have checks : Valid expected t ∧ t.isc ∈ finalized := ⟨valid,parent⟩
  simp only [check,parsed,bind,Option.bind,if_pos checks,hashed]

theorem wrongParentRejected {sha expected finalized source t}
    (parsed : read source = some t) (absent : t.isc ∉ finalized) :
    check sha expected finalized source = none := by simp [check,parsed,absent]

theorem wrongShapeRejected {sha expected finalized source t}
    (parsed : read source = some t) (invalid : ¬ Valid expected t) :
    check sha expected finalized source = none := by simp [check,parsed,invalid]

theorem missingHashRejected (expected finalized source) :
    check (fun _ => []) expected finalized source = none := by
  unfold check
  cases read source with
  | none => rfl
  | some t =>
    dsimp only [bind,Option.bind]
    split <;> simp [NativeSeedTranscript.id,NativeStateBytes.contentId]

def checkAll (sha : Bytes → Bytes) (expected : Context) (finalized : List Bytes) :
    List Value → Option (List Checked)
  | [] => some []
  | v::vs => do
    let t ← check sha expected finalized v
    let ts ← checkAll sha expected finalized vs
    some (t::ts)

theorem listFromComponents {sha expected finalized v vs t ts}
    (first : check sha expected finalized v = some t)
    (rest : checkAll sha expected finalized vs = some ts) :
    checkAll sha expected finalized (v::vs) = some (t::ts) := by
  simp only [checkAll,first,rest,bind,Option.bind]

theorem allSources {sha expected finalized vs ts}
    (h : checkAll sha expected finalized vs = some ts) : ts.map Checked.source = vs := by
  induction vs generalizing ts with
  | nil => simp [checkAll] at h; subst ts; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨t,ht,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource ht).1,ih hr]

theorem allChecked {sha expected finalized vs ts}
    (h : checkAll sha expected finalized vs = some ts) (t : Checked) (mem : t ∈ ts) :
    Source sha expected finalized t.source t := by
  induction vs generalizing ts with
  | nil => simp [checkAll] at h; subst ts; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · have s := checkedSource hx; simpa only [s.1] using s
    · exact ih hr mem

def fromBytes (sha : Bytes → Bytes) (expected : Context) (finalized : List Bytes)
    (raw : Bytes) : Option Checked := do
  if raw.length ≤ 4*1024*1024 then
    let tree ← NativePolicyCodec.decode fmtSeed raw
    check sha expected finalized tree
  else none

theorem bytesSource {sha expected finalized raw out}
    (h : fromBytes sha expected finalized raw = some out) :
    raw.length ≤ 4*1024*1024 ∧ encode fmtSeed out.source = some raw ∧
    Source sha expected finalized out.source out := by
  unfold fromBytes at h
  split at h <;> try contradiction
  rename_i size
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨tree,parsed,checked⟩ := h
  have src := checkedSource checked
  exact ⟨size,src.1 ▸ (NativePolicyCodec.decoded parsed).2,by simpa only [src.1] using src⟩

theorem bytesFromComponents {sha expected finalized raw tree out}
    (size : raw.length ≤ 4*1024*1024) (parsed : NativePolicyCodec.decode fmtSeed raw = some tree)
    (checked : check sha expected finalized tree = some out) :
    fromBytes sha expected finalized raw = some out := by
  simp only [fromBytes,if_pos size,parsed,checked,bind,Option.bind]

-- This component computes both sides of the certificate edge, not finalization provenance.
def linked (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (certificate source : Value) : Option (NativeIscCertificate.Checked × Checked) := do
  let parent ← NativeIscCertificate.check sha expected committee certificate
  let seed ← check sha expected [parent.qcId] source
  some (parent,seed)

theorem linkedFromComponents {sha expected committee certificate source parent seed}
    (cert : NativeIscCertificate.check sha expected committee certificate = some parent)
    (edge : check sha expected [parent.qcId] source = some seed) :
    linked sha expected committee certificate source = some (parent,seed) := by
  simp only [linked,cert,edge,bind,Option.bind]

theorem linkedSources {sha expected committee certificate source parent seed}
    (h : linked sha expected committee certificate source = some (parent,seed)) :
    NativeIscCertificate.Source sha expected committee certificate parent ∧
    Source sha expected [parent.qcId] source seed ∧ seed.transcript.isc = parent.qcId := by
  unfold linked at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,s,hs,last⟩ := h
  cases Option.some.inj last
  have src := checkedSource hs
  exact ⟨NativeIscCertificate.checkedSource hp,src,by simpa using src.2.2.2.2.1⟩

end DeltaReduce.NativeSeedTranscript
