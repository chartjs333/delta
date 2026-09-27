import DeltaReduce.NativeVectorLayout

/-! Complete computed draft SCHEMA/Q_SHARD artifacts. Hash/decoder/source
authentication remain separate boundaries; exact store bytes are checked. -/
namespace DeltaReduce.NativeVectorArtifacts
open NativeBinding
open NativeVectorLayout (Layout text shardName)
open NativeVectorContext (Slice)

def encodeShard (s : Shard) : Bytes :=
  asciiBytes "{\"id\":" ++ quotedBytes (asciiBytes s.id) ++
  asciiBytes ",\"length\":" ++ asciiBytes (toString s.length) ++
  asciiBytes ",\"offset\":" ++ asciiBytes (toString s.offset) ++ [125]
def encodeSchema (l : Layout) : Bytes :=
  asciiBytes "{\"kind\":\"SCHEMA\",\"payload\":{\"coordinates\":" ++
  arrayBytes (l.coordinates.map (quotedBytes ∘ asciiBytes)) ++
  asciiBytes ",\"shards\":" ++ arrayBytes (l.shards.map encodeShard) ++ [125,125]
def encodeSchemaRef (r : Ref) : Bytes :=
  asciiBytes "{\"id\":" ++ quotedBytes (idBytes r.id) ++
  asciiBytes ",\"kind\":\"SCHEMA\",\"length\":" ++ asciiBytes (toString r.length) ++ [125]
def encodeQ (q : QShard) : Bytes :=
  asciiBytes "{\"kind\":\"Q_SHARD\",\"payload\":{\"domain\":" ++ quotedBytes (asciiBytes q.domain) ++
  asciiBytes ",\"quantum\":" ++ arrayBytes ([q.quantum.numerator,q.quantum.denominator].map (asciiBytes ∘ toString)) ++
  asciiBytes ",\"schema\":" ++ encodeSchemaRef q.schema ++
  asciiBytes ",\"shard\":" ++ quotedBytes (asciiBytes q.shard) ++
  asciiBytes ",\"ticket\":" ++ quotedBytes (asciiBytes q.ticket) ++
  asciiBytes ",\"values\":" ++ arrayBytes (q.values.map (asciiBytes ∘ toString)) ++ [125,125]

structure Artifact where
  raw : Bytes
  payload : Payload
  ref : Ref
  deriving DecidableEq, Repr

def pack (hash : Bytes → ContentId) (raw : Bytes) (payload : Payload) : Option Artifact :=
  if 0 < raw.length ∧ raw.length ≤ 4194304 ∧ (hash raw).length = 32 then
    some ⟨raw,payload,⟨hash raw,payload.kind,raw.length⟩⟩ else none
theorem packed {hash raw payload a} (h : pack hash raw payload = some a) :
    a.raw = raw ∧ a.payload = payload ∧ a.ref = ⟨hash raw,payload.kind,raw.length⟩ ∧
    0 < raw.length ∧ raw.length ≤ 4194304 ∧ (hash raw).length = 32 := by
  unfold pack at h; split at h <;> try contradiction
  cases Option.some.inj h; exact ⟨rfl,rfl,rfl,by assumption⟩

def schema (hash : Bytes → ContentId) (l : Layout) : Option Artifact :=
  pack hash (encodeSchema l) (.schema l.coordinates l.shards)
theorem schemaEncoded {hash l a} (h : schema hash l = some a) :
    a.raw = encodeSchema l ∧ a.payload = .schema l.coordinates l.shards ∧
    a.ref = ⟨hash (encodeSchema l),.schema,(encodeSchema l).length⟩ := by
  have src := packed h; exact ⟨src.1,src.2.1,src.2.2.1⟩
theorem schemaHashPreimage {codec l a} (adapter : HashAdapter codec) (h : schema codec.hash l = some a) :
    a.ref.id = adapter.sha256 (artifactHashInput (encodeSchema l)) := by
  rw [(schemaEncoded h).2.2]; exact adapter.artifact _

def qValue (schemaRef : Ref) (s : Slice) : QShard :=
  { ticket := text s.source.term.source.member.input.ticket
    domain := text s.source.term.source.member.input.domain
    shard := shardName s.block.block.header.ordinal
    schema := schemaRef, quantum := s.block.quantum, values := s.block.block.frame.values }
def QChecks (r : Ref) (s : Slice) : Prop :=
  r.kind = .schema ∧ r.id.length = 32 ∧ 0 < r.length ∧ r.length ≤ 4194304 ∧
  (∀ id ∈ [s.source.term.source.member.input.ticket,s.source.term.source.member.input.domain],
    asciiBytes (text id) = id ∧ validIdentifier (text id) = true) ∧
  s.block.block.header.ordinal < 4096 ∧
  0 < s.block.block.frame.values.length ∧ s.block.block.frame.values.length ≤ 4096 ∧
  positiveQuantum s.block.quantum ∧
  (∀ v ∈ s.block.block.frame.values, Fits minInput maxInput v)
instance (r s) : Decidable (QChecks r s) := by unfold QChecks; infer_instance
def qArtifact (hash : Bytes → ContentId) (r : Ref) (s : Slice) : Option Artifact :=
  if QChecks r s then pack hash (encodeQ (qValue r s)) (.qShard (qValue r s)) else none
theorem qEncoded {hash r s a} (h : qArtifact hash r s = some a) :
    QChecks r s ∧ a.raw = encodeQ (qValue r s) ∧ a.payload = .qShard (qValue r s) ∧
    a.ref = ⟨hash (encodeQ (qValue r s)),.qShard,(encodeQ (qValue r s)).length⟩ := by
  by_cases check : QChecks r s
  · rw [qArtifact,if_pos check] at h
    have p := @packed hash (encodeQ (qValue r s)) (.qShard (qValue r s)) a h
    exact ⟨check,p.1,p.2.1,p.2.2.1⟩
  · simp only [qArtifact,if_neg check] at h; contradiction
theorem fullValues (r : Ref) (s : Slice) : (qValue r s).values = s.block.block.frame.values := rfl
theorem originalQuantum (r : Ref) (s : Slice) : (qValue r s).quantum = s.block.quantum := rfl
theorem qHashPreimage {codec r s a} (adapter : HashAdapter codec) (h : qArtifact codec.hash r s = some a) :
    a.ref.id = adapter.sha256 (artifactHashInput (encodeQ (qValue r s))) := by
  rw [(qEncoded h).2.2.2]; exact adapter.artifact _

def contribution (s : Slice) (r : Ref) : Contribution :=
  ⟨text s.source.term.source.member.input.ticket,
    ⟨s.source.term.source.weight.numerator,s.source.term.source.weight.denominator⟩,r⟩

structure RowImage (codec : Codec) (store : Store) (schemaRef : Ref) (frame : ParameterFrame)
    (assignment : Assignment) (width : Nat) (s : Slice) where
  artifact : Artifact
  generated : qArtifact codec.hash schemaRef s = some artifact
  loaded : LoadedRow codec store schemaRef frame assignment width (contribution s artifact.ref)
  bytes : loaded.bytes = artifact.raw
  value : loaded.q = qValue schemaRef s

def loadImage (codec : Codec) (store : Store) (schemaRef : Ref) (frame : ParameterFrame)
    (assignment : Assignment) (width : Nat) (s : Slice) :
    Option (RowImage codec store schemaRef frame assignment width s) := do
  match gen : qArtifact codec.hash schemaRef s with
  | none => none
  | some a =>
    let row ← loadRow codec store schemaRef frame assignment width (contribution s a.ref)
    if checks : row.bytes = a.raw ∧ row.q = qValue schemaRef s then
      some ⟨a,gen,row,checks.1,checks.2⟩ else none

theorem missingImageRejected {codec store schemaRef frame assignment width s a}
    (generated : qArtifact codec.hash schemaRef s = some a) (missing : store a.ref.id = none) :
    loadImage codec store schemaRef frame assignment width s = none := by
  unfold loadImage
  split
  · rfl
  · rename_i a' gen
    cases Option.some.inj (gen.symm.trans generated)
    have absent : loadPayload codec store (contribution s a.ref).q = none := by
      unfold loadPayload
      split
      · rfl
      · rename_i bytes present
        change store a.ref.id = some bytes at present
        rw [missing] at present
        contradiction
    simp [loadRow,absent]

theorem substitutedBytesRejected {codec store schemaRef frame assignment width s a}
    (generated : qArtifact codec.hash schemaRef s = some a)
    (row : LoadedRow codec store schemaRef frame assignment width (contribution s a.ref))
    (loaded : loadRow codec store schemaRef frame assignment width (contribution s a.ref) = some row)
    (different : row.bytes ≠ a.raw) : loadImage codec store schemaRef frame assignment width s = none := by
  unfold loadImage
  split
  · rfl
  · rename_i a' gen
    cases Option.some.inj (gen.symm.trans generated)
    simp [loaded,different]

theorem rowNumbers {codec store schemaRef frame assignment width s}
    (r : RowImage codec store schemaRef frame assignment width s) :
    r.loaded.row = NativeVectorArithmetic.kernelRow s := by
  simp [LoadedRow.row,r.value,qValue,contribution,NativeVectorArithmetic.kernelRow]
theorem rowOriginalBytes {codec store schemaRef frame assignment width s}
    (r : RowImage codec store schemaRef frame assignment width s) :
    r.loaded.bytes = encodeQ (qValue schemaRef s) ∧
    store r.artifact.ref.id = some (encodeQ (qValue schemaRef s)) := by
  have bytes := r.bytes.trans (qEncoded r.generated).2.1
  exact ⟨bytes,by simpa [contribution,bytes] using r.loaded.resolved.present⟩

structure RowsImage (codec : Codec) (store : Store) (schemaRef : Ref) (frame : ParameterFrame)
    (assignment : Assignment) (width : Nat) (slices : List Slice) where
  contributions : List Contribution
  bound : RowsBound codec store schemaRef frame assignment width contributions
    (slices.map NativeVectorArithmetic.kernelRow)
  sources : List Artifact
  count : sources.length = slices.length
  original : ∀ (i : Nat) (s : Slice), slices[i]? = some s → ∃ a,
    sources[i]? = some a ∧ qArtifact codec.hash schemaRef s = some a ∧
    contributions[i]? = some (contribution s a.ref) ∧ store a.ref.id = some a.raw

def loadImages (codec : Codec) (store : Store) (schemaRef : Ref) (frame : ParameterFrame)
    (assignment : Assignment) (width : Nat) : (slices : List Slice) →
    Option (RowsImage codec store schemaRef frame assignment width slices)
  | [] => some ⟨[],.nil,[],rfl,by simp⟩
  | s::ss => do
    let r ← loadImage codec store schemaRef frame assignment width s
    let rest ← loadImages codec store schemaRef frame assignment width ss
    some ⟨contribution s r.artifact.ref :: rest.contributions,
      by simpa only [List.map_cons,← rowNumbers r] using RowsBound.cons r.loaded rest.bound,
      r.artifact :: rest.sources,by simp [rest.count],by
        intro i t ht
        cases i with
        | zero =>
          simp at ht; subst t
          exact ⟨r.artifact,rfl,r.generated,rfl,by
            simpa only [contribution,r.bytes] using r.loaded.resolved.present⟩
        | succ i => simpa using rest.original i t (by simpa using ht)⟩

theorem allRowsBound {codec store schemaRef frame assignment width slices}
    (r : RowsImage codec store schemaRef frame assignment width slices) :
    RowsBound codec store schemaRef frame assignment width r.contributions
      (slices.map NativeVectorArithmetic.kernelRow) ∧ r.contributions.length = slices.length :=
  ⟨r.bound,by simpa using (rowsBoundLength r.bound).1⟩

theorem parameterComputation {b domain index out codec store schemaRef frame assignment profile}
    (reduced : NativeVectorArithmetic.reduce b domain index = some out)
    (rows : RowsImage codec store schemaRef frame assignment (NativeVectorContext.shape out.first).entry.count out.slices)
    (denominator : assignment.denominator = b.source.plan.accumulator.numbers.denominator)
    (width : profile.accumulatorBits = b.source.plan.accumulator.numbers.accumulatorBits) :
    RowsBound codec store schemaRef frame assignment (NativeVectorContext.shape out.first).entry.count
      rows.contributions (out.slices.map NativeVectorArithmetic.kernelRow) ∧
    ParameterKernel.checkedParameter (accumulatorLo profile) (accumulatorHi profile) minInput maxInput
      assignment.denominator (NativeVectorContext.shape out.first).entry.count
      (out.slices.map NativeVectorArithmetic.kernelRow) = some out.values := by
  refine ⟨rows.bound,?_⟩
  simpa [NativeVectorArithmetic.compute,accumulatorLo,accumulatorHi,NativeVectorArithmetic.lo,
    NativeVectorArithmetic.hi,denominator,width] using (NativeVectorArithmetic.reduced reduced).2.2.2.2

end DeltaReduce.NativeVectorArtifacts
