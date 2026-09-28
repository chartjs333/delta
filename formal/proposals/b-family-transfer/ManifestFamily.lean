import ShardFamily

/-! General source-bound transfer of the B relation to the original004 manifest
and its complete ordered corpus. No vote/QC/WAL capture is synthesized. -/
namespace DeltaReduce.ManifestFamily
open NativeManifestBinding

theorem corpusShapes {hash scaleRaw p w refs raws qs}
    (h : Corpus hash scaleRaw p w refs raws qs) :
    ∀ q ∈ qs, q.block.frame.values.length = (NativeVectorContext.shape q).entry.count := by
  induction h with
  | nil => simp
  | cons source links tail ih =>
    intro q hq
    rcases List.mem_cons.mp hq with rfl | member
    · exact (NativeQHeader.joined (NativeScaleBinding.boundSource source).block).2.2.symm
    · exact ih q member

section General
variable {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws m}
variable (loaded : bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some m)
include loaded

theorem positiveAndBounded (q : NativeScaleBinding.Bound) (member : q ∈ m.blocks) :
    0 < (NativeVectorContext.shape q).entry.count ∧
    (NativeVectorContext.shape q).entry.count ≤ 524288 := by
  have entry : (NativeVectorContext.shape q).entry ∈ m.plan.plan.entries := by
    rw [← NativeVectorContext.originalPlanSlots loaded]
    exact List.mem_map.mpr ⟨q,member,rfl⟩
  have bounds := NativeShardPlanBinding.exactPayloadBounds (boundSource loaded).plan _ entry
  exact ⟨bounds.1,bounds.2.1⟩

def layout : ShardFamily.Layout :=
  ⟨m.blocks.length,fun s => (NativeVectorContext.shape m.blocks[s.val]).entry.count,
    fun s => (positiveAndBounded loaded _ (List.getElem_mem s.isLt)).1⟩

/-- The source manifest and all original raw leaves remain in the single common
carrier. Optional protocol context is passed through, not authenticated here. -/
def whole (control : Control) : ShardFamily.Whole (layout loaded)
    (Bound × List NativeReceiptBytes.Bytes × Control) Int :=
  ⟨(m,raws,control),fun s => m.blocks[s.val].block.frame.values,
    fun s => corpusShapes (fullOrderedCorpus loaded) _ (List.getElem_mem s.isLt)⟩

def family (control : Control) := ShardFamily.project (whole loaded control)

theorem full_reconstruction (control : Control) :
    ShardFamily.reconstruct (family loaded control) = whole loaded control :=
  ShardFamily.reconstruct_project _

theorem bounded_layout : (layout loaded).count ≤ 4096 ∧
    ∀ s, 0 < (layout loaded).width s ∧ (layout loaded).width s ≤ 524288 := by
  have same := (noMissingOrExtraBlocks loaded).1.trans (noMissingOrExtraBlocks loaded).2
  exact ⟨by simpa only [layout,← same] using
    (NativeShardPlanBinding.completePartition (boundSource loaded).plan).2.1,
    fun s => positiveAndBounded loaded _ (List.getElem_mem s.isLt)⟩

theorem ordered_source (control : Control) :
    ShardFamily.ordered (ShardFamily.reconstruct (family loaded control)) =
      m.blocks.map (fun q => q.block.frame.values) := by
  rw [full_reconstruction]
  simp only [ShardFamily.ordered,whole,layout]
  apply List.ext_getElem?
  intro k
  by_cases hk : k < m.blocks.length <;> simp [hk]

theorem raw_identity (control : Control) (a : ShardFamily.Selector (layout loaded)) :
    (ShardFamily.scalarView (family loaded control) a).1 = (m,raws,control) ∧
    NativeManifestBytes.encode (ShardFamily.scalarView (family loaded control) a).1.1.manifest.wire = manifestRaw ∧
    hash (manifestInput manifestRaw) = manifestId :=
  ⟨rfl,exactPreimage loaded,(boundSource loaded).identity.2⟩

theorem coordinate_source (control : Control) (a : ShardFamily.Selector (layout loaded))
    (s : Fin (layout loaded).count) :
    (family loaded control).view a s =
      (m.blocks[s.val]'s.isLt).block.frame.values[(a s).val]'(by
        have shape := corpusShapes (fullOrderedCorpus loaded) (m.blocks[s.val]'s.isLt) (List.getElem_mem s.isLt)
        rw [shape]
        exact (a s).isLt) := rfl

end General

/- Concrete instance uses the existing kernel-checked source, not rebuilt bytes
or a new synthetic certificate. The raw fixture hash boundary is unchanged. -/
def original := family NativeManifestVectors.wholeManifest ()

theorem originalWidths : List.ofFn (layout NativeManifestVectors.wholeManifest).width = [4,8,8,8,8] := by decide
theorem originalCount : (layout NativeManifestVectors.wholeManifest).count = 5 := by decide
theorem originalStarts : NativeManifestVectors.bound.blocks.map
    (fun q => (NativeVectorContext.shape q).entry.start) = [0,4,12,20,28] :=
  NativeVectorArithmeticVectors.actualLocations

theorem originalRoundtrip : ShardFamily.reconstruct original = whole NativeManifestVectors.wholeManifest () :=
  full_reconstruction _ _

theorem originalFullValues : ShardFamily.ordered (ShardFamily.reconstruct original) =
    NativeManifestVectors.bound.blocks.map (fun q => q.block.frame.values) :=
  ordered_source _ _

theorem originalNoNewObjects (a : ShardFamily.Selector (layout NativeManifestVectors.wholeManifest)) :
    (ShardFamily.scalarView original a).1.1 = NativeManifestVectors.bound := rfl

end DeltaReduce.ManifestFamily
