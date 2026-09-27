import DeltaReduce.NativePlanQCorpus

/-! Source-derived alignment of complete original vectors. All inputs enter via
the original byte loaders. Compatibility compares their computed structures,
never a caller-supplied expected translation. Hash/source authority remains open. -/
namespace DeltaReduce.NativeVectorContext
open NativeReceiptBytes (Bytes)
open NativePlanQCorpus (Row)

structure Shape where
  entry : NativeShardPartition.Entry
  quantum : NativeBinding.Rational
  deriving DecidableEq, Repr

def shape (q : NativeScaleBinding.Bound) : Shape :=
  ⟨NativeShardPlanBinding.headerEntry q.block.header,q.quantum⟩

def context (m : NativeManifestBinding.Bound) : List Bytes :=
  let w := m.manifest.wire
  [w.schema,w.profile,w.proof,w.config,w.scale,w.plan,w.parent]

def Compatible (first other : NativeManifestBinding.Bound) : Prop :=
  context other = context first ∧ other.plan = first.plan ∧
  other.blocks.map shape = first.blocks.map shape
instance (a b) : Decidable (Compatible a b) := by unfold Compatible; infer_instance

structure Bound where
  source : NativePlanQCorpus.Bound
  first : Row

def align (source : NativePlanQCorpus.Bound) : Option Bound := do
  let first ← source.rows.head?
  if ∀ r ∈ source.rows, Compatible first.corpus.manifest r.corpus.manifest then
    some ⟨source,first⟩ else none

theorem aligned {source b} (h : align source = some b) :
    b.source = source ∧ source.rows.head? = some b.first ∧
    ∀ r ∈ source.rows, Compatible b.first.corpus.manifest r.corpus.manifest := by
  simp only [align,bind,Option.bind_eq_some_iff] at h
  obtain ⟨first,hf,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨rfl,hf,by assumption⟩

theorem alignFromSources {source first}
    (head : source.rows.head? = some first)
    (all : ∀ r ∈ source.rows, Compatible first.corpus.manifest r.corpus.manifest) :
    align source = some ⟨source,first⟩ := by
  simp only [align,head,Bind.bind,Option.bind]
  exact if_pos all

def bind (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) : Option Bound := do
  let source ← NativePlanQCorpus.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
    permission inputs
  align source

theorem boundSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b) :
    NativePlanQCorpus.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b.source ∧
    b.source.rows.head? = some b.first ∧
    ∀ r ∈ b.source.rows, Compatible b.first.corpus.manifest r.corpus.manifest := by
  simp only [bind,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,ha⟩ := h
  have a := aligned ha
  rw [← a.1] at hs a
  exact ⟨hs,a.2⟩

theorem bindFromSources {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source b}
    (loaded : NativePlanQCorpus.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some source) (alignment : align source = some b) :
    bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b := by
  simp [bind,loaded,alignment]

theorem completeOriginalRows {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b) :
    b.source.rows.map (fun r => r.term.source) = b.source.plan.members.rows ∧
    b.source.rows.length = inputs.length := NativePlanQCorpus.completeEligibleOrder (boundSource h).1

theorem sameParent {a b} (h : Compatible a b) : b.manifest.wire.parent = a.manifest.wire.parent := by
  have eq := congrArg (fun xs => xs[6]?) h.1
  simpa [context] using eq

theorem sameBlockCount {a b} (h : Compatible a b) : b.blocks.length = a.blocks.length := by
  simpa using congrArg List.length h.2.2

theorem sameSlot {a b} (h : Compatible a b) {i : Nat} {q}
    (position : a.blocks[i]? = some q) :
    ∃ r, b.blocks[i]? = some r ∧ shape r = shape q := by
  have eq := congrArg (fun xs => xs[i]?) h.2.2
  rw [List.getElem?_map,List.getElem?_map,position] at eq
  cases slot : b.blocks[i]? with
  | none => simp [slot] at eq
  | some r => exact ⟨r,rfl,by simpa [slot] using eq⟩

theorem sameCoordinateLocation {a b} (h : shape a = shape b) (i : Nat) :
    a.block.header.wire.segment = b.block.header.wire.segment ∧
    a.block.header.start+i = b.block.header.start+i ∧
    a.block.header.offset+i = b.block.header.offset+i ∧
    a.block.header.count = b.block.header.count ∧ a.quantum = b.quantum := by
  have entry := congrArg Shape.entry h
  exact ⟨congrArg NativeShardPartition.Entry.name entry,
    congrArg (fun e => e.start+i) entry,congrArg (fun e => e.offset+i) entry,
    congrArg NativeShardPartition.Entry.count entry,congrArg Shape.quantum h⟩

theorem corpusShapes {hash scaleRaw p w refs raws qs}
    (h : NativeManifestBinding.Corpus hash scaleRaw p w refs raws qs) :
    qs.map (fun q => (shape q).entry) = refs.map NativeManifestBinding.Ref.entry := by
  induction h with
  | nil => rfl
  | cons source links rest ih =>
    simp only [List.map_cons,ih]
    rw [show (shape _).entry = _ from links.2.2.1]

theorem originalPlanSlots {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws m}
    (h : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some m) :
    m.blocks.map (fun q => (shape q).entry) = m.plan.plan.entries :=
  (corpusShapes (NativeManifestBinding.fullOrderedCorpus h)).trans
    (NativeManifestBinding.fullPlan h).1

theorem sameOriginalPreimages {hash sa ta pa ma ia ra a sb tb pb mb ib rb b}
    (ha : NativeManifestBinding.bind hash sa ta pa ma ia ra = some a)
    (hb : NativeManifestBinding.bind hash sb tb pb mb ib rb = some b)
    (compatible : Compatible a b) : sa = sb ∧ ta = tb ∧ pa = pb := by
  have ap := (NativeManifestBinding.boundSource ha).plan
  have bp := (NativeManifestBinding.boundSource hb).plan
  rw [compatible.2.1] at bp
  have ai := NativeShardPlanBinding.boundSource ap
  have bi := NativeShardPlanBinding.boundSource bp
  have asrc := NativeSchemaBinding.boundSource ai.inputs
  have bsrc := NativeSchemaBinding.boundSource bi.inputs
  exact ⟨(NativeSchemaBinding.exactPreimage asrc.schema).symm.trans
      (NativeSchemaBinding.exactPreimage bsrc.schema),
    (NativeScaleBinding.exactPreimage asrc.scale).symm.trans
      (NativeScaleBinding.exactPreimage bsrc.scale),
    (NativeShardPlanBinding.exactPreimage ap).symm.trans (NativeShardPlanBinding.exactPreimage bp)⟩

structure Slice where
  source : Row
  block : NativeScaleBinding.Bound
  deriving DecidableEq, Repr

def sliceRows (index : Nat) : List Row → Option (List Slice)
  | [] => some []
  | r::rs => do
    let q ← r.corpus.manifest.blocks[index]?
    let rest ← sliceRows index rs
    some (⟨r,q⟩::rest)

theorem slicedSources {index rows slices} (h : sliceRows index rows = some slices) :
    slices.map Slice.source = rows ∧
    ∀ s ∈ slices, s.source.corpus.manifest.blocks[index]? = some s.block := by
  induction rows generalizing slices with
  | nil => simp [sliceRows] at h; subst slices; exact ⟨rfl,by simp⟩
  | cons r rs ih =>
    simp only [sliceRows,Bind.bind,Option.bind_eq_some_iff] at h
    obtain ⟨q,hq,rest,hr,last⟩ := h
    cases Option.some.inj last
    have tail := ih hr
    exact ⟨by simp [tail.1],by simpa using And.intro hq tail.2⟩

theorem slicedAt {index rows slices} (h : sliceRows index rows = some slices) (i : Nat) :
    (slices.map Slice.source)[i]? = rows[i]? := congrArg (fun xs => xs[i]?) (slicedSources h).1

theorem slicedShape {source b index first rows slices}
    (alignedSource : align source = some b)
    (subset : ∀ r ∈ rows, r ∈ source.rows)
    (slot : b.first.corpus.manifest.blocks[index]? = some first)
    (selected : sliceRows index rows = some slices) :
    ∀ s ∈ slices, shape s.block = shape first := by
  intro s hs
  have src := slicedSources selected
  have mem : s.source ∈ rows := by rw [← src.1]; exact List.mem_map.mpr ⟨s,hs,rfl⟩
  obtain ⟨q,hq,same⟩ := sameSlot ((aligned alignedSource).2.2 s.source (subset _ mem)) slot
  rw [src.2 s hs] at hq
  cases Option.some.inj hq
  exact same

theorem slicedOriginalBytes {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b
    domain index slices s}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b)
    (selected : sliceRows index (NativePlanQCorpus.inDomain domain b.source.rows) = some slices)
    (member : s ∈ slices) :
    ∃ input ∈ inputs, ∃ raw ∈ input.raws,
      NativeScaleBinding.bind (NativePlanCoefficients.contentHash sha) input.scaleRaw raw = some s.block ∧
      NativeQBytes.encodeFrame s.block.block.frame.header s.block.block.frame.payload = raw ∧
      NativeQBytes.PayloadRelation s.block.block.frame.payload s.block.block.frame.values := by
  have src := slicedSources selected
  have mem : s.source ∈ b.source.rows := by
    have dm : s.source ∈ NativePlanQCorpus.inDomain domain b.source.rows := by
      rw [← src.1]; exact List.mem_map.mpr ⟨s,member,rfl⟩
    exact List.mem_of_mem_filter dm
  obtain ⟨_,_,input,hi,hr⟩ := NativePlanQCorpus.rowMember
    (NativePlanQCorpus.boundSource (boundSource h).1).2 s.source mem
  have manifest := (NativeAccumulatorBinding.corpusSource (NativePlanQCorpus.rowSource hr).2.1).1
  have blockMem := List.mem_of_getElem? (src.2 s member)
  obtain ⟨raw,hraw,load⟩ := NativeAvailableQ.blockSource
    (NativeManifestBinding.fullOrderedCorpus manifest) s.block blockMem
  have parsed := (NativeScaleBinding.boundSource load).block
  exact ⟨input,hi,raw,hraw,load,
    (NativeQBytes.decodedFields (NativeQHeader.joined parsed).1).2,
    (NativeQHeader.joinedPayload parsed).1⟩
end DeltaReduce.NativeVectorContext
