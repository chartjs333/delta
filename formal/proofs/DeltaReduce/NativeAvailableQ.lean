import DeltaReduce.NativePlanCoefficients

/-! Original Q bytes plus native InputLedger primitive fields. These typed
primitive observations are UNAUTHENTICATED_COMPONENT_INPUT, not a native wire
decoder, attestation verifier, ledger history, or commitment preimage. -/
namespace DeltaReduce.NativeAvailableQ
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ContentId)

def Ids (xs : List Bytes) : Prop :=
  0 < xs.length ∧ xs.length ≤ 4096 ∧ xs.Nodup ∧ NativeSchemaBinding.Ordered xs ∧
  ∀ x ∈ xs, 0 < x.length ∧ x.length ≤ 255 ∧ x.all (fun b => b.toNat < 128) = true
instance (xs) : Decidable (Ids xs) := by unfold Ids; infer_instance

structure Permission where
  tickets : List Bytes
  attesters : List Bytes
  threshold : Nat
  deriving DecidableEq, Repr
structure Observation where
  commitmentTicket : Bytes
  commitment : Bytes
  proofTicket : Bytes
  proofCommitment : Bytes
  certificate : Bytes
  required : List Bytes
  covered : List Bytes
  attesters : List Bytes
  threshold : Nat
  deriving DecidableEq, Repr

def Primitive (p : Permission) (o : Observation) : Prop :=
  Ids p.tickets ∧ Ids p.attesters ∧ Ids [o.commitmentTicket] ∧
  ContentId o.commitment ∧ ContentId o.certificate ∧ o.commitmentTicket ∈ p.tickets ∧
  o.proofTicket = o.commitmentTicket ∧ o.proofCommitment = o.commitment ∧
  Ids o.required ∧ (∀ id ∈ o.required, ContentId id) ∧ o.covered = o.required ∧
  Ids o.attesters ∧ (∀ id ∈ o.attesters, id ∈ p.attesters) ∧
  0 < p.threshold ∧ p.threshold < 2^32 ∧ o.threshold = p.threshold ∧ p.threshold ≤ o.attesters.length
instance (p o) : Decidable (Primitive p o) := by unfold Primitive; infer_instance

def Coverage (o : Observation) (m : NativeManifestBinding.Bound) : Prop :=
  o.required.Perm (m.manifest.refs.map (fun r => r.wire.leaf)) ∧
  o.commitmentTicket = m.manifest.wire.ticket
instance (o m) : Decidable (Coverage o m) := by unfold Coverage; infer_instance

theorem exactCoveredLeaves {p o m} (primitive : Primitive p o) (coverage : Coverage o m) :
    o.covered.Perm (m.manifest.refs.map (fun r => r.wire.leaf)) := by
  rw [primitive.2.2.2.2.2.2.2.2.2.2.1]
  exact coverage.1

theorem noMissingLeaf {p o m} (primitive : Primitive p o) (coverage : Coverage o m)
    (id : Bytes) : id ∈ o.covered ↔ id ∈ m.manifest.refs.map (fun r => r.wire.leaf) :=
  (exactCoveredLeaves primitive coverage).mem_iff

theorem exactLeafCount {p o m} (primitive : Primitive p o) (coverage : Coverage o m) :
    o.covered.length = m.manifest.refs.length := by
  simpa using (exactCoveredLeaves primitive coverage).length_eq

structure Input where
  schemaRaw : Bytes
  scaleRaw : Bytes
  planRaw : Bytes
  manifestRaw : Bytes
  manifestId : Bytes
  raws : List Bytes
  observation : Observation
  deriving DecidableEq, Repr

def load (hash : Bytes → Bytes) (configRaw proofRaw profileRaw : Bytes) (i : Input) :=
  NativeAccumulatorBinding.bindCorpus hash i.schemaRaw i.scaleRaw i.planRaw
    i.manifestRaw i.manifestId configRaw proofRaw profileRaw i.raws

theorem manifestSource {hash configRaw proofRaw profileRaw i q}
    (h : load hash configRaw proofRaw profileRaw i = some q) :
    NativeManifestBinding.bind hash i.schemaRaw i.scaleRaw i.planRaw i.manifestRaw i.manifestId
      i.raws = some q.manifest := (NativeAccumulatorBinding.corpusSource h).1

theorem blockSource {hash scaleRaw p w rs raws qs}
    (h : NativeManifestBinding.Corpus hash scaleRaw p w rs raws qs)
    (q : NativeScaleBinding.Bound) (mem : q ∈ qs) :
    ∃ raw ∈ raws, NativeScaleBinding.bind hash scaleRaw raw = some q := by
  induction h with
  | nil => simp at mem
  | @cons r raw out rs raws qs source links remaining ih =>
    rcases List.mem_cons.mp mem with same | inside
    · subst q; exact ⟨raw,by simp,source⟩
    · obtain ⟨r,hr,hs⟩ := ih inside
      exact ⟨r,List.mem_cons_of_mem _ hr,hs⟩

theorem originalBlock {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws m}
    (h : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some m)
    (q : NativeScaleBinding.Bound) (mem : q ∈ m.blocks) :
    ∃ raw ∈ raws, NativeQBytes.decode raw = some q.block.frame ∧
      NativeQBytes.encodeFrame q.block.frame.header q.block.frame.payload = raw := by
  obtain ⟨raw,hr,hs⟩ := blockSource (NativeManifestBinding.fullOrderedCorpus h) q mem
  have decoded := (NativeQHeader.joined (NativeScaleBinding.boundSource hs).block).1
  exact ⟨raw,hr,decoded,(NativeQBytes.decodedFields decoded).2⟩

theorem originalRange {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws m}
    (h : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some m)
    (q : NativeScaleBinding.Bound) (mem : q ∈ m.blocks) (v : Int) (hv : v ∈ q.block.frame.values) :
    |v| ≤ 32767 := by
  obtain ⟨_,_,decoded,_⟩ := originalBlock h q mem
  exact abs_le.mpr (NativeQBytes.decodedRange decoded v hv)

def coordinate (m : NativeManifestBinding.Bound) (blockIndex coordinateIndex : Nat) : Option Int := do
  let q ← m.blocks[blockIndex]?
  q.block.frame.values[coordinateIndex]?

theorem coordinateRange {hash configRaw proofRaw profileRaw i q}
    (h : load hash configRaw proofRaw profileRaw i = some q) {blockIndex coordinateIndex v}
    (value : coordinate q.manifest blockIndex coordinateIndex = some v) : |v| ≤ 32767 := by
  simp only [coordinate,bind,Option.bind_eq_some_iff] at value
  obtain ⟨b,hb,hv⟩ := value
  exact originalRange (manifestSource h) b (List.mem_of_getElem? hb) v (List.mem_of_getElem? hv)

theorem fullOriginalCorpus {hash configRaw proofRaw profileRaw i q}
    (h : load hash configRaw proofRaw profileRaw i = some q) :
    NativeManifestBytes.encode q.manifest.manifest.wire = i.manifestRaw ∧
    q.manifest.plan.plan.entries.length = i.raws.length ∧ i.raws.length = q.manifest.blocks.length :=
  ⟨NativeManifestBinding.exactPreimage (manifestSource h),
    NativeManifestBinding.noMissingOrExtraBlocks (manifestSource h)⟩
end DeltaReduce.NativeAvailableQ
