import DeltaReduce.NativeRootSource

/-! Recompute every finalized leaf of a selected ROOT proposal. Original raw
policy/state are reused by the vector loader; there is no future ROOT QC input. -/
namespace DeltaReduce.NativeRootCorpus
open NativeBinding NativeEarlySource NativeRootSource

section Computation
variable {codec store trust anchor} (binding : Binding codec trust anchor store)
    {adapter : HashAdapter codec} {policy state vote facts} (loaded : Loaded adapter.sha256 policy state vote facts)
    (root : Root loaded.original)

def SameSnapshot (b : NativeVectorContext.Bound) : Prop :=
  NativeVectorAuthority.policy b = loaded.original.policy ∧
  NativeVectorAuthority.state b = loaded.original.state ∧
  (NativeVectorAuthority.plan b).id = root.original.certificate.common.plan
structure Image where
  vector : NativeVectorContext.Bound
  corpus : ParameterCorpus binding

def compute (config proof profile : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) : Option (Image binding) := do
  let b ← NativeVectorContext.bind adapter.sha256 policy state root.original.certificate.common.plan
    config proof profile permission inputs
  let c ← deriveParameterCorpus binding
  if NativeCertifiedCorpus.RootChecks binding b c root.original ∧
      NativeCertifiedCorpus.checkLeaves binding b c.entries root.original.shards = true then
    some ⟨b,c⟩ else none

structure Source (config proof profile : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) (out : Image binding) : Prop where
  vector : NativeVectorContext.bind adapter.sha256 policy state root.original.certificate.common.plan
    config proof profile permission inputs = some out.vector
  corpus : deriveParameterCorpus binding = some out.corpus
  parents : NativeCertifiedCorpus.RootChecks binding out.vector out.corpus root.original
  leaves : NativeCertifiedCorpus.checkLeaves binding out.vector out.corpus.entries root.original.shards = true

theorem computed {config proof profile permission inputs out}
    (h : compute binding loaded root config proof profile permission inputs = some out) :
    Source binding loaded root config proof profile permission inputs out := by
  simp only [compute,bind,Option.bind_eq_some_iff] at h
  obtain ⟨b,hb,c,hc,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hb,hc,(by assumption : NativeCertifiedCorpus.RootChecks binding b c root.original ∧
    NativeCertifiedCorpus.checkLeaves binding b c.entries root.original.shards = true).1,
    (by assumption : NativeCertifiedCorpus.RootChecks binding b c root.original ∧
    NativeCertifiedCorpus.checkLeaves binding b c.entries root.original.shards = true).2⟩

theorem fromComponents {config proof profile permission inputs out}
    (h : Source binding loaded root config proof profile permission inputs out) :
    compute binding loaded root config proof profile permission inputs = some out := by
  simp only [compute,h.vector,bind,Option.bind,h.corpus,
    if_pos (And.intro h.parents h.leaves)]

structure Checked (config proof profile : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) where
  image : Image binding
  executed : compute binding loaded root config proof profile permission inputs = some image

def check (config proof profile : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) :
    Option (Checked binding loaded root config proof profile permission inputs) :=
  match h : compute binding loaded root config proof profile permission inputs with
  | none => none
  | some image => some ⟨image,h⟩

variable {config proof profile permission inputs}
    (checked : Checked binding loaded root config proof profile permission inputs)

theorem sameOriginalSnapshot : SameSnapshot loaded root checked.image.vector := by
  have src := computed binding loaded root checked.executed
  obtain ⟨vt,vp,vs⟩ := NativeVectorAuthority.rawSource src.vector
  obtain ⟨ot,op⟩ := (loadedOriginal loaded).policy
  exact ⟨congrArg Prod.snd (Option.some.inj (vp.symm.trans op)),
    Option.some.inj (vs.symm.trans (loadedOriginal loaded).state),src.parents.2.2.2.1.symm⟩

theorem completeOrder :
    checked.image.corpus.entries.length = root.original.shards.length ∧
    root.original.shards.map NativeAggregateLineage.shardLeaf = root.original.certificate.common.leaves :=
  ⟨NativeCertifiedCorpus.leafCounts binding (computed binding loaded root checked.executed).leaves,
    NativeRootSource.completeLeaves loaded root⟩

theorem originalPosition {index : Nat} {entry}
    (position : checked.image.corpus.entries[index]? = some entry) :
    ∃ e leaf, root.original.shards[index]? = some e ∧
      NativeCertifiedCorpus.checkLeaf binding checked.image.vector entry e = some leaf :=
  NativeCertifiedCorpus.leafAt binding (computed binding loaded root checked.executed).leaves position

theorem originalRows : checked.image.vector.source.rows.map (fun r => r.term.source) =
      checked.image.vector.source.plan.members.rows ∧
    checked.image.vector.source.rows.length = inputs.length :=
  NativeVectorContext.completeOriginalRows (computed binding loaded root checked.executed).vector

theorem exactKeys : checked.image.corpus.entries.map (NativeCertifiedCorpus.key binding) =
    root.original.certificate.common.keys :=
  (computed binding loaded root checked.executed).parents.2.2.2.2.1

end Computation
end DeltaReduce.NativeRootCorpus
