import DeltaReduce.NativeManifestBytes
import DeltaReduce.NativeManifestMerkle
import DeltaReduce.NativeShardPlanBinding
/-! Complete original manifest/corpus binding under an explicit UNVERIFIED hash
function. No certificate, source authentication or public admission is inferred. -/
namespace DeltaReduce.NativeManifestBinding
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii parseDecimal ContentId)
open NativeManifestBytes (Wire RefWire)
open NativeShardPartition (Entry)

def refPlanWire (w : RefWire) : NativeShardPlanBytes.EntryWire :=
  ⟨w.count,w.start,w.ordinal,w.payload,w.name,w.offset⟩

structure Ref where
  wire : RefWire
  entry : Entry
  envelope : Nat
  deriving DecidableEq, Repr

def readRef (w : RefWire) : Option Ref := do
  let e ← NativeShardPlanBinding.entry (refPlanWire w)
  let n ← parseDecimal w.envelope
  if ContentId w.leaf then some ⟨w,e,n⟩ else none

structure RefSource (w : RefWire) (r : Ref) : Prop where
  original : r.wire = w
  entry : NativeShardPlanBinding.entry (refPlanWire w) = some r.entry
  envelope : parseDecimal w.envelope = some r.envelope
  leaf : ContentId w.leaf

theorem refSource {w r} (h : readRef w = some r) : RefSource w r := by
  simp only [readRef,bind,Option.bind_eq_some_iff] at h
  obtain ⟨e,he,n,hn,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨rfl,he,hn,valid⟩

def readRefs : List RefWire → Option (List Ref)
  | [] => some []
  | w::ws => do
      let r ← readRef w
      let rs ← readRefs ws
      some (r::rs)

theorem refsSource {ws rs} (h : readRefs ws = some rs) :
    rs.map Ref.wire = ws ∧ ∀ r ∈ rs, RefSource r.wire r := by
  induction ws generalizing rs with
  | nil => simp [readRefs] at h; subst rs; exact ⟨rfl,by simp⟩
  | cons w ws ih =>
    simp only [readRefs,bind,Option.bind_eq_some_iff] at h
    obtain ⟨r,hr,tail,ht,last⟩ := h
    cases Option.some.inj last
    have rest := ih ht
    have source := refSource hr
    refine ⟨by simp [source.original,rest.1],?_⟩
    intro x hx
    rcases List.mem_cons.mp hx with same | inside
    · subst x; simpa only [source.original] using source
    · exact rest.2 x inside

structure Manifest where
  wire : Wire
  refs : List Ref
  steps : Nat
  total : Nat
  envelopes : Nat
  payloads : Nat
  deriving DecidableEq, Repr

def interpret (w : Wire) : Option Manifest := do
  let rs ← readRefs w.refs
  let steps ← parseDecimal w.steps
  let total ← parseDecimal w.total
  let envelopes ← parseDecimal w.envelopes
  let payloads ← parseDecimal w.payloads
  some ⟨w,rs,steps,total,envelopes,payloads⟩

structure ManifestSource (w : Wire) (m : Manifest) : Prop where
  original : m.wire = w
  refs : readRefs w.refs = some m.refs
  steps : parseDecimal w.steps = some m.steps
  total : parseDecimal w.total = some m.total
  envelopes : parseDecimal w.envelopes = some m.envelopes
  payloads : parseDecimal w.payloads = some m.payloads

theorem interpreted {w m} (h : interpret w = some m) : ManifestSource w m := by
  simp only [interpret,bind,Option.bind_eq_some_iff] at h
  obtain ⟨rs,hr,s,hs,t,ht,e,he,p,hp,last⟩ := h
  cases Option.some.inj last
  exact ⟨rfl,hr,hs,ht,he,hp⟩

theorem interpretFromSource {w m} (h : ManifestSource w m) : interpret w = some m := by
  simp only [interpret,h.refs,h.steps,h.total,h.envelopes,h.payloads,bind,Option.bind]
  have same : Manifest.mk w m.refs m.steps m.total m.envelopes m.payloads = m := by
    rw [← h.original]
  rw [same]

def leafInput (raw : Bytes) := ascii "deltareduce.004.shard-leaf.v1" ++ [0] ++ raw
def manifestInput (raw : Bytes) := ascii "deltareduce.004.manifest.v1" ++ [0] ++ raw

/-- Every header field is derived from the manifest/ref bytes and actual payload.
Version/type are fixed by NativeQHeader.fields, not provided as approval flags. -/
def expectedHeader (hash : Bytes → Bytes) (w : Wire) (r : RefWire) (payload : Bytes) :
    NativeQHeader.Wire :=
  ⟨r.count,r.start,w.semantics,r.ordinal,w.schema,hash payload,w.profile,w.proof,
    w.config,w.scale,r.name,r.offset,w.plan,w.ticket⟩

def LeafLinks (hash : Bytes → Bytes) (p : NativeShardPlanBinding.Bound) (w : Wire)
    (r : Ref) (raw : Bytes) (q : NativeScaleBinding.Bound) : Prop :=
  q.table = p.inputs.scale ∧
  q.block.header.wire = expectedHeader hash w r.wire q.block.frame.payload ∧
  NativeShardPlanBinding.headerEntry q.block.header = r.entry ∧
  q.block.frame.payload.length = r.entry.payload ∧
  raw.length = r.envelope ∧ hash (leafInput raw) = r.wire.leaf
instance (hash p w r raw q) : Decidable (LeafLinks hash p w r raw q) := by
  unfold LeafLinks; infer_instance

def leaf (hash : Bytes → Bytes) (scaleRaw : Bytes) (p : NativeShardPlanBinding.Bound)
    (w : Wire) (r : Ref) (raw : Bytes) : Option NativeScaleBinding.Bound := do
  let q ← NativeScaleBinding.bind hash scaleRaw raw
  if LeafLinks hash p w r raw q then some q else none

theorem leafSource {hash scaleRaw p w r raw q}
    (h : leaf hash scaleRaw p w r raw = some q) :
    NativeScaleBinding.bind hash scaleRaw raw = some q ∧ LeafLinks hash p w r raw q := by
  simp only [leaf,bind,Option.bind_eq_some_iff] at h
  obtain ⟨out,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨ho,by assumption⟩

theorem leafFromSource {hash scaleRaw p w r raw q}
    (source : NativeScaleBinding.bind hash scaleRaw raw = some q)
    (links : LeafLinks hash p w r raw q) : leaf hash scaleRaw p w r raw = some q := by
  simp [leaf,source,links]

theorem leafOriginalPayload {hash scaleRaw p w r raw q}
    (h : leaf hash scaleRaw p w r raw = some q) :
    NativeQBytes.encodeFrame q.block.frame.header q.block.frame.payload = raw ∧
    NativeQBytes.PayloadRelation q.block.frame.payload q.block.frame.values ∧
    q.block.header.wire.payloadHash = hash q.block.frame.payload ∧
    hash (leafInput raw) = r.wire.leaf := by
  have src := leafSource h
  have parsed := (NativeScaleBinding.boundSource src.1).block
  exact ⟨(NativeQBytes.decodedFields (NativeQHeader.joined parsed).1).2,
    (NativeQHeader.joinedPayload parsed).1,
    congrArg NativeQHeader.Wire.payloadHash src.2.2.1,src.2.2.2.2.2.2⟩

/-- Zips the ENTIRE ordered corpus; either unmatched tail rejects. -/
def corpus (hash : Bytes → Bytes) (scaleRaw : Bytes) (p : NativeShardPlanBinding.Bound)
    (w : Wire) : List Ref → List Bytes → Option (List NativeScaleBinding.Bound)
  | [],[] => some []
  | r::rs,raw::raws => do
      let q ← leaf hash scaleRaw p w r raw
      let qs ← corpus hash scaleRaw p w rs raws
      some (q::qs)
  | _,_ => none

inductive Corpus (hash : Bytes → Bytes) (scaleRaw : Bytes)
    (p : NativeShardPlanBinding.Bound) (w : Wire) :
    List Ref → List Bytes → List NativeScaleBinding.Bound → Prop
  | nil : Corpus hash scaleRaw p w [] [] []
  | cons {r raw q rs raws qs}
      (source : NativeScaleBinding.bind hash scaleRaw raw = some q)
      (links : LeafLinks hash p w r raw q)
      (remaining : Corpus hash scaleRaw p w rs raws qs) :
      Corpus hash scaleRaw p w (r::rs) (raw::raws) (q::qs)

theorem corpusSource {hash scaleRaw p w rs raws qs}
    (h : corpus hash scaleRaw p w rs raws = some qs) : Corpus hash scaleRaw p w rs raws qs := by
  induction rs generalizing raws qs with
  | nil => cases raws <;> simp [corpus] at h; subst qs; exact .nil
  | cons r rs ih =>
    cases raws with
    | nil => simp [corpus] at h
    | cons raw raws =>
      simp only [corpus,bind,Option.bind_eq_some_iff] at h
      obtain ⟨q,hq,tail,ht,last⟩ := h
      cases Option.some.inj last
      have src := leafSource hq
      exact .cons src.1 src.2 (ih ht)

theorem corpusFromSource {hash scaleRaw p w rs raws qs}
    (h : Corpus hash scaleRaw p w rs raws qs) : corpus hash scaleRaw p w rs raws = some qs := by
  induction h with
  | nil => rfl
  | cons source links remaining ih => simp [corpus,leafFromSource source links,ih]

theorem corpusLengths {hash scaleRaw p w rs raws qs}
    (h : Corpus hash scaleRaw p w rs raws qs) : rs.length = raws.length ∧ raws.length = qs.length := by
  induction h with
  | nil => exact ⟨rfl,rfl⟩
  | cons source links remaining ih => simpa using ih

theorem corpusAt {hash scaleRaw p w rs raws qs}
    (h : Corpus hash scaleRaw p w rs raws qs) (i : Nat) (r : Ref) (position : rs[i]? = some r) :
    ∃ raw q, raws[i]? = some raw ∧ qs[i]? = some q ∧
      NativeScaleBinding.bind hash scaleRaw raw = some q ∧ LeafLinks hash p w r raw q := by
  induction h generalizing i with
  | nil => simp at position
  | @cons a raw q tail rest qs source links remaining ih =>
    cases i with
    | zero => simp at position; subst r; exact ⟨raw,q,rfl,rfl,source,links⟩
    | succ n => simpa using ih n (by simpa using position)

theorem corpusTotals {hash scaleRaw p w rs raws qs}
    (h : Corpus hash scaleRaw p w rs raws qs) :
    (raws.map List.length).sum = (rs.map Ref.envelope).sum ∧
    (qs.map (fun q => q.block.frame.payload.length)).sum = (rs.map (fun r => r.entry.payload)).sum ∧
    (qs.map (fun q => q.block.frame.values.length)).sum = (rs.map (fun r => r.entry.count)).sum := by
  induction h with
  | nil => exact ⟨rfl,rfl,rfl⟩
  | @cons r raw q rs raws qs source links remaining ih =>
    have count := (NativeQHeader.joined (NativeScaleBinding.boundSource source).block).2.2
    have same := congrArg Entry.count links.2.2.1
    change q.block.header.count = r.entry.count at same
    simp only [List.map_cons,List.sum_cons]
    exact ⟨by rw [links.2.2.2.2.1,ih.1],by rw [links.2.2.2.1,ih.2.1],
      by rw [← count,same,ih.2.2]⟩

def Links (hash : Bytes → Bytes) (planRaw : Bytes) (p : NativeShardPlanBinding.Bound)
    (m : Manifest) : Prop :=
  m.wire.version = ascii "1.0.0" ∧ m.wire.kind = ascii "ENCODED_CONTRIBUTION_MANIFEST" ∧
  m.wire.semantics = p.plan.wire.semantics ∧ m.wire.profile = p.plan.wire.profile ∧
  m.wire.schema = p.plan.wire.schema ∧ m.wire.scale = p.plan.wire.scale ∧
  m.wire.plan = hash (NativeShardPlanBinding.hashInput planRaw) ∧
  (∀ id ∈ [m.wire.root,m.wire.parent,m.wire.proof,m.wire.config,m.wire.plan], ContentId id) ∧
  NativeQHeader.Token m.wire.ticket ∧ NativeQHeader.Token m.wire.domain ∧
  0 < m.steps ∧ m.steps < 2^32 ∧
  m.refs.map Ref.entry = p.plan.entries ∧
  (m.refs.map (fun r => r.wire.leaf)).Nodup ∧
  m.total = p.inputs.schema.total ∧
  m.payloads = 2*m.total ∧ m.payloads = (m.refs.map (fun r => r.entry.payload)).sum ∧
  m.envelopes = (m.refs.map Ref.envelope).sum
instance (hash raw p m) : Decidable (Links hash raw p m) := by unfold Links; infer_instance

structure Bound where
  plan : NativeShardPlanBinding.Bound
  manifest : Manifest
  blocks : List NativeScaleBinding.Bound
  deriving DecidableEq, Repr

def bind (hash : Bytes → Bytes) (schemaRaw scaleRaw planRaw manifestRaw manifestId : Bytes)
    (raws : List Bytes) : Option Bound := do
  let p ← NativeShardPlanBinding.bind hash schemaRaw scaleRaw planRaw
  let w ← NativeManifestBytes.decode manifestRaw
  let m ← interpret w
  if Links hash planRaw p m ∧ ContentId manifestId ∧ hash (manifestInput manifestRaw) = manifestId then
    let blocks ← corpus hash scaleRaw p w m.refs raws
    let root ← NativeManifestMerkle.root hash (m.refs.map (fun r => r.wire.leaf))
    if root = w.root then some ⟨p,m,blocks⟩ else none
  else none

structure Source (hash : Bytes → Bytes) (schemaRaw scaleRaw planRaw manifestRaw manifestId : Bytes)
    (raws : List Bytes) (b : Bound) : Prop where
  plan : NativeShardPlanBinding.bind hash schemaRaw scaleRaw planRaw = some b.plan
  wire : NativeManifestBytes.decode manifestRaw = some b.manifest.wire
  interpreted : interpret b.manifest.wire = some b.manifest
  links : Links hash planRaw b.plan b.manifest
  identity : ContentId manifestId ∧ hash (manifestInput manifestRaw) = manifestId
  corpus : corpus hash scaleRaw b.plan b.manifest.wire b.manifest.refs raws = some b.blocks
  root : NativeManifestMerkle.root hash (b.manifest.refs.map (fun r => r.wire.leaf)) = some b.manifest.wire.root

theorem boundSource {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b) :
    Source hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b := by
  unfold bind at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,w,hw,m,hm,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨qs,hq,root,hr,last⟩ := last
  split at last <;> try contradiction
  rename_i rootEq
  cases Option.some.inj last
  have src := interpreted hm
  exact ⟨hp,by rw [src.original]; exact hw,by rw [src.original]; exact hm,checks.1,checks.2,
    by rw [src.original]; exact hq,by rw [src.original,← rootEq]; exact hr⟩

theorem bindFromSource {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : Source hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b) :
    bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b := by
  simp only [bind,h.plan,h.wire,h.interpreted,Bind.bind,Option.bind]
  rw [if_pos ⟨h.links,h.identity⟩,h.corpus,h.root]
  simp

/-! Results retain original byte provenance and exact full list; they do not
establish cryptographic authenticity, remote availability, or phase/QC admission. -/
theorem exactPreimage {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b) :
    NativeManifestBytes.encode b.manifest.wire = manifestRaw :=
  (NativeManifestBytes.decoded (boundSource h).wire).2.2.2

theorem originalReferences {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b) :
    b.manifest.refs.map Ref.wire = b.manifest.wire.refs ∧
    ∀ r ∈ b.manifest.refs, RefSource r.wire r :=
  refsSource (interpreted (boundSource h).interpreted).refs

theorem fullOrderedCorpus {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b) :
    Corpus hash scaleRaw b.plan b.manifest.wire b.manifest.refs raws b.blocks :=
  corpusSource (boundSource h).corpus

theorem fullPlan {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b) :
    b.manifest.refs.map Ref.entry = b.plan.plan.entries ∧
    NativeShardPartition.Span 0 0 (b.manifest.refs.map Ref.entry) b.manifest.total := by
  have src := boundSource h
  rcases src.links with ⟨_,_,_,_,_,_,_,_,_,_,_,_,entries,_,total,_⟩
  exact ⟨entries,by rw [entries,total]; exact (NativeShardPlanBinding.completePartition src.plan).2.2⟩

theorem noMissingOrExtraBlocks {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b) :
    b.plan.plan.entries.length = raws.length ∧ raws.length = b.blocks.length := by
  have lens := corpusLengths (fullOrderedCorpus h)
  have plan := congrArg List.length (fullPlan h).1
  simp only [List.length_map] at plan
  exact ⟨plan.symm.trans lens.1,lens.2⟩

theorem exactTotals {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b) :
    b.manifest.envelopes = (raws.map List.length).sum ∧
    b.manifest.payloads = (b.blocks.map (fun q => q.block.frame.payload.length)).sum ∧
    b.manifest.total = (b.blocks.map (fun q => q.block.frame.values.length)).sum := by
  have src := boundSource h
  have sums := corpusTotals (fullOrderedCorpus h)
  rcases src.links with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,payloads,envelopes⟩
  have span := NativeShardPartition.spanTotal (fullPlan h).2
  simp only [List.map_map,Function.comp_def,Nat.zero_add] at span
  exact ⟨envelopes.trans sums.1.symm,payloads.trans sums.2.1.symm,span.symm.trans sums.2.2.symm⟩

theorem exactMerkle {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (h : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b) :
    NativeManifestMerkle.Tree hash (b.manifest.refs.map (fun r => r.wire.leaf)) b.manifest.wire.root :=
  (NativeManifestMerkle.rootSource (boundSource h).root).2.2.2

end DeltaReduce.NativeManifestBinding
