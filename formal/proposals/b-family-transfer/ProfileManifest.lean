import DeltaReduce.NativeManifestBinding

/-! R2.3 O metadata/data-use join. Reuses the original004 closed decoders,
partition/units and Merkle definitions. No public-state predicate, physical
availability oracle or new shard/certificate identity enters the relation.
Hash correctness and original configuration/producer origin remain explicit
external obligations; successful metadata resolution alone is not AC authority.
-/
namespace DeltaReduce.ProfileManifest
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ContentId)
open NativeManifestBinding

structure Metadata where
  plan : NativeShardPlanBinding.Bound
  manifest : Manifest
  deriving DecidableEq, Repr

def load (hash : Bytes → Bytes)
    (semantics schemaRaw scaleRaw planRaw manifestRaw manifestId : Bytes) :
    Option Metadata := do
  let p ← NativeShardPlanBinding.bind hash schemaRaw scaleRaw planRaw
  let w ← NativeManifestBytes.decode manifestRaw
  let m ← interpret w
  if Links hash planRaw p m ∧ ContentId manifestId ∧
      hash (manifestInput manifestRaw) = manifestId ∧ w.semantics = semantics then
    let root ← NativeManifestMerkle.root hash (m.refs.map (fun r => r.wire.leaf))
    if root = w.root then some ⟨p,m⟩ else none
  else none

structure Source (hash : Bytes → Bytes)
    (semantics schemaRaw scaleRaw planRaw manifestRaw manifestId : Bytes)
    (m : Metadata) : Prop where
  plan : NativeShardPlanBinding.bind hash schemaRaw scaleRaw planRaw = some m.plan
  wire : NativeManifestBytes.decode manifestRaw = some m.manifest.wire
  interpreted : interpret m.manifest.wire = some m.manifest
  links : Links hash planRaw m.plan m.manifest
  identity : ContentId manifestId ∧ hash (manifestInput manifestRaw) = manifestId
  semantics : m.manifest.wire.semantics = semantics
  root : NativeManifestMerkle.root hash (m.manifest.refs.map (fun r => r.wire.leaf)) =
    some m.manifest.wire.root

theorem checked {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    Source hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m := by
  unfold load at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,w,hw,parsed,hm,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨root,hr,last⟩ := last
  split at last <;> try contradiction
  rename_i eqRoot
  cases Option.some.inj last
  have origin := interpreted hm
  exact ⟨hp,by rw [origin.original]; exact hw,
    by rw [origin.original]; exact hm,checks.1,
    ⟨checks.2.1,checks.2.2.1⟩,by rw [origin.original]; exact checks.2.2.2,
    by rw [origin.original,← eqRoot]; exact hr⟩

theorem complete {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : Source hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m) :
    load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m := by
  simp only [load,h.plan,h.wire,h.interpreted,Bind.bind,Option.bind]
  rw [if_pos ⟨h.links,h.identity.1,h.identity.2,h.semantics⟩,h.root]
  simp

def originalLeaves (m : Metadata) : List (Bytes × Nat) :=
  m.manifest.refs.map (fun r => (r.wire.leaf,r.envelope))

def originalRoot (m : Metadata) : Bytes := m.manifest.wire.root

theorem originalBytes {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    NativeManifestBytes.encode m.manifest.wire = manifestRaw :=
  (NativeManifestBytes.decoded (checked h).wire).2.2.2

theorem completeOrderedReferences
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    m.manifest.refs.map Ref.wire = m.manifest.wire.refs ∧
    ∀ r ∈ m.manifest.refs, RefSource r.wire r :=
  refsSource (interpreted (checked h).interpreted).refs

theorem completeOrderedRoot
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    NativeManifestMerkle.Tree hash ((originalLeaves m).map Prod.fst) (originalRoot m) := by
  simpa only [originalLeaves,originalRoot,List.map_map,Function.comp_def] using
    (NativeManifestMerkle.rootSource (checked h).root).2.2.2

theorem originalPlan {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    m.manifest.refs.map Ref.entry = m.plan.plan.entries ∧
    NativeShardPartition.Span 0 0 (m.manifest.refs.map Ref.entry) m.manifest.total := by
  have src := checked h
  rcases src.links with ⟨_,_,_,_,_,_,_,_,_,_,_,_,entries,_,total,_⟩
  exact ⟨entries,by rw [entries,total]; exact
    (NativeShardPlanBinding.completePartition src.plan).2.2⟩

/-- The independently obtained current complete bytes are the missing premise
at data use. An AC or a previous observation cannot discharge this premise. -/
def consume (hash : Bytes → Bytes) (scaleRaw : Bytes) (m : Metadata) (raws : List Bytes) :=
  corpus hash scaleRaw m.plan m.manifest.wire m.manifest.refs raws

theorem atUseExistingBinding
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m raws blocks}
    (metadata : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m)
    (actual : consume hash scaleRaw m raws = some blocks) :
    NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws =
      some ⟨m.plan,m.manifest,blocks⟩ := by
  have s := checked metadata
  exact bindFromSource ⟨s.plan,s.wire,s.interpreted,s.links,s.identity,actual,s.root⟩

/-- Converse: no extra data-use gate beyond the original complete binding and
the independently pinned semantics. This does not filter by public success. -/
theorem existingBindingReusable
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (loaded : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b)
    (selected : b.manifest.wire.semantics = semantics) :
    load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some ⟨b.plan,b.manifest⟩ ∧
    consume hash scaleRaw ⟨b.plan,b.manifest⟩ raws = some b.blocks := by
  have s := boundSource loaded
  exact ⟨complete ⟨s.plan,s.wire,s.interpreted,s.links,s.identity,selected,s.root⟩,s.corpus⟩

theorem atUseOriginalLengths
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m raws blocks}
    (metadata : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m)
    (actual : consume hash scaleRaw m raws = some blocks) :
    m.plan.plan.entries.length = raws.length ∧ raws.length = blocks.length :=
  noMissingOrExtraBlocks (atUseExistingBinding metadata actual)

end DeltaReduce.ProfileManifest
