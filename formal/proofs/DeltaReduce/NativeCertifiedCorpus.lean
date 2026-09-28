import DeltaReduce.NativeBindingConstruction
import DeltaReduce.NativeAggregateSection

/-! Check the actual finalized PARAMETER corpus against source computations.
Original QC identifiers and projected artifact identifiers remain distinct. -/
namespace DeltaReduce.NativeCertifiedCorpus
open NativeBinding
open NativeVectorContext (Bound)
open NativeVectorAuthority (policy state plan)

def ordinal (b : Bound) (name : String) : Option Nat :=
  ((b.first.corpus.manifest.plan.plan.entries).find?
    (fun e => NativeVectorLayout.shardName e.ordinal == name)).map (·.ordinal)

theorem ordinalSource {b name i} (h : ordinal b name = some i) :
    ∃ e ∈ b.first.corpus.manifest.plan.plan.entries,
      e.ordinal = i ∧ NativeVectorLayout.shardName i = name := by
  unfold ordinal at h
  cases found : b.first.corpus.manifest.plan.plan.entries.find?
      (fun e => NativeVectorLayout.shardName e.ordinal == name) with
  | none => simp [found] at h
  | some e =>
    simp only [found,Option.map_some,Option.some.injEq] at h
    exact ⟨e,List.mem_of_find?_eq_some found,h,by simpa [h] using List.find?_some found⟩

def ExactBody (body : NativeParameter.Common) (leaves : List Bytes) (values : List Int) : Bool :=
  NativeVectorAuthority.bodyMatches body leaves values &&
    body.numerators == values.map (asciiBytes ∘ toString)

theorem exactBody {body leaves values} (h : ExactBody body leaves values = true) :
    body.leaves.Perm leaves ∧ body.numerators.map NativeCertificateDecimal.number = values ∧
    body.numerators = values.map (asciiBytes ∘ toString) := by
  have parts : NativeVectorAuthority.bodyMatches body leaves values = true ∧
      body.numerators = values.map (asciiBytes ∘ toString) := by simpa [ExactBody] using h
  exact ⟨(NativeVectorAuthority.matchedBody parts.1).1,
    (NativeVectorAuthority.matchedBody parts.1).2,parts.2⟩

section Corpus
variable {codec store trust anchor} (binding : Binding codec trust anchor store)

structure Leaf (b : Bound) (p : BoundParameter binding) where
  index : Nat
  computation : NativeVectorJoin.Joined binding b (asciiBytes p.domain) index
  leaves : List Bytes

def LeafChecks (b : Bound) (p : BoundParameter binding) (e : NativeParameterLineage.Edge)
    (i : Nat) (j : NativeVectorJoin.Joined binding b (asciiBytes p.domain) i) : Prop :=
  NativeVectorLayout.text (asciiBytes p.domain) = p.domain ∧
  NativeVectorLayout.shardName i = p.shard ∧ j.native.body = p.body ∧
  NativeVectorAuthority.FrameChecks binding.authority b j.native.frame ∧
  e.certificate.common.domain = asciiBytes p.domain ∧
  e.certificate.common.shard = asciiBytes p.shard ∧
  NativeVectorAuthority.AssignmentChecks b j.native.assignment e
instance (b p e i j) : Decidable (LeafChecks binding b p e i j) := by
  unfold LeafChecks; infer_instance

def checkLeaf (b : Bound) (p : BoundParameter binding) (e : NativeParameterLineage.Edge) :
    Option (Leaf binding b p) := do
  let i ← ordinal b p.shard
  let j ← NativeVectorJoin.join binding b (asciiBytes p.domain) i
  let leaves ← NativeVectorAuthority.sourceLeaves i j.out.slices
  if LeafChecks binding b p e i j ∧ ExactBody e.certificate.common leaves j.native.numerators = true then
    some ⟨i,j,leaves⟩ else none

attribute [local irreducible] LeafChecks ExactBody

theorem leafChecked {b p e out} (h : checkLeaf binding b p e = some out) :
    ordinal b p.shard = some out.index ∧
    NativeVectorJoin.join binding b (asciiBytes p.domain) out.index = some out.computation ∧
    NativeVectorAuthority.sourceLeaves out.index out.computation.out.slices = some out.leaves ∧
    LeafChecks binding b p e out.index out.computation ∧
    ExactBody e.certificate.common out.leaves out.computation.native.numerators = true := by
  simp only [checkLeaf,bind,Option.bind_eq_some_iff] at h
  obtain ⟨i,hi,j,hj,leaves,hl,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hi,hj,hl,by assumption⟩

theorem leafNumbers {b p e out} (h : checkLeaf binding b p e = some out) :
    e.certificate.common.numerators.map NativeCertificateDecimal.number = out.computation.out.values ∧
    e.certificate.common.leaves.Perm out.leaves ∧
    out.leaves.length = out.computation.out.slices.length := by
  have src := leafChecked binding h
  have body := exactBody src.2.2.2.2
  exact ⟨body.2.1.trans (NativeVectorJoin.numeratorsDerived out.computation),body.1,
    NativeVectorAuthority.sourceLeafCount src.2.2.1⟩

theorem leafBody {b p e out} (h : checkLeaf binding b p e = some out) :
    out.computation.native.body = p.body ∧
    NativeVectorAuthority.AssignmentChecks b out.computation.native.assignment e := by
  have checks := (leafChecked binding h).2.2.2.1
  unfold LeafChecks at checks
  exact ⟨checks.2.2.1,checks.2.2.2.2.2.2⟩

theorem wrongDomainRejected {b p e} (bad : e.certificate.common.domain ≠ asciiBytes p.domain) :
    checkLeaf binding b p e = none := by
  cases h : checkLeaf binding b p e with
  | none => rfl
  | some out =>
    have checks := (leafChecked binding h).2.2.2.1
    unfold LeafChecks at checks
    exact False.elim (bad checks.2.2.2.2.1)

theorem wrongParentRejected {b p e} (bad : e.certificate.common.plan ≠ (plan b).id) :
    checkLeaf binding b p e = none := by
  cases h : checkLeaf binding b p e with
  | none => rfl
  | some out =>
    have checks := (leafBody binding h).2
    unfold NativeVectorAuthority.AssignmentChecks at checks
    exact False.elim (bad checks.2.2.2.1)

/-- Strict ordered zipper: no omitted, extra or reordered shard is repaired. -/
def checkLeaves (b : Bound) : List (BoundParameter binding) → List NativeParameterLineage.Edge → Bool
  | [],[] => true
  | p::ps,e::es => (checkLeaf binding b p e).isSome && checkLeaves b ps es
  | _,_ => false

theorem leafCounts {b ps es} (h : checkLeaves binding b ps es = true) : ps.length = es.length := by
  induction ps generalizing es with
  | nil => cases es <;> simp_all [checkLeaves]
  | cons p ps ih =>
    cases es with
    | nil => simp [checkLeaves] at h
    | cons e es =>
      have parts := Bool.and_eq_true_iff.mp h
      simp only [List.length_cons,ih parts.2]

theorem unequalCountsRejected {b ps es} (different : ps.length ≠ es.length) :
    checkLeaves binding b ps es = false := by
  cases h : checkLeaves binding b ps es with
  | false => rfl
  | true => exact False.elim (different (leafCounts binding h))

theorem leafAt {b ps es} (h : checkLeaves binding b ps es = true) {i : Nat} {p}
    (position : ps[i]? = some p) :
    ∃ e out, es[i]? = some e ∧ checkLeaf binding b p e = some out := by
  induction ps generalizing es i with
  | nil => simp at position
  | cons first ps ih =>
    cases es with
    | nil => simp [checkLeaves] at h
    | cons e es =>
      have parts := Bool.and_eq_true_iff.mp h
      cases i with
      | zero =>
        simp only [List.getElem?_cons_zero,Option.some.injEq] at position
        subst p
        obtain ⟨out,hout⟩ := Option.isSome_iff_exists.mp parts.1
        exact ⟨e,out,rfl,hout⟩
      | succ i => simpa using ih parts.2 (by simpa using position)

def key (p : BoundParameter binding) : NativeParameter.Key := ⟨asciiBytes p.domain,asciiBytes p.shard⟩

def RootChecks (b : Bound) (c : ParameterCorpus binding) (e : NativeAggregateLineage.Edge) : Prop :=
  e.certificate.common.context = (plan b).certificate.common.context ∧
  e.certificate.common.isc = (plan b).parent.qcId ∧
  e.certificate.common.ec = (plan b).ec.id ∧ e.certificate.common.plan = (plan b).id ∧
  c.entries.map (key binding) = e.certificate.common.keys ∧
  NativeVectorAuthority.FrameChecks binding.authority b c.frame
instance (b c e) : Decidable (RootChecks binding b c e) := by unfold RootChecks; infer_instance

structure Image where
  loaded : NativeAggregateSection.Bound
  root : NativeAggregateLineage.Edge
  corpus : ParameterCorpus binding

def check (sha : Bytes → Bytes) (b : Bound) (id : Bytes) : Option (Image binding) := do
  let loaded ← NativeAggregateSection.bindSection sha (policy b) (state b)
  let root ← loaded.certificates.find? (fun e => e.id == id)
  if root.id ∈ loaded.finalized then
    let corpus ← deriveParameterCorpus binding
    if RootChecks binding b corpus root ∧ checkLeaves binding b corpus.entries root.shards = true then
      some ⟨loaded,root,corpus⟩ else none
  else none

attribute [local irreducible] RootChecks

structure Source (sha : Bytes → Bytes) (b : Bound) (id : Bytes) (out : Image binding) : Prop where
  loaded : NativeAggregateSection.bindSection sha (policy b) (state b) = some out.loaded
  root : out.loaded.certificates.find? (fun e => e.id == id) = some out.root
  finalized : out.root.id ∈ out.loaded.finalized
  corpus : deriveParameterCorpus binding = some out.corpus
  parents : RootChecks binding b out.corpus out.root
  leaves : checkLeaves binding b out.corpus.entries out.root.shards = true

theorem checked {sha b id out} (h : check binding sha b id = some out) : Source binding sha b id out := by
  simp only [check,bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,r,hr,last⟩ := h
  split at last <;> try contradiction
  rename_i finalized
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨c,hc,last⟩ := last
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hs,hr,finalized,hc,(by assumption : RootChecks binding b c r ∧ checkLeaves binding b c.entries r.shards = true).1,(by assumption : RootChecks binding b c r ∧ checkLeaves binding b c.entries r.shards = true).2⟩

theorem rootIdentity {sha b id out} (h : check binding sha b id = some out) :
    out.root.id = id ∧ out.root.id ∈ out.loaded.finalized :=
  ⟨by simpa using List.find?_some (checked binding h).root,(checked binding h).finalized⟩

theorem originalRoot {sha b id out} (h : check binding sha b id = some out) :
    NativeAggregateLineage.check sha .finalized
      (NativeParameterSection.expected (policy b) (state b) out.loaded.parameters.prior.plans) (policy b).validators
      out.loaded.parameters.prior.plans.eligibility.norms.isc.certificates out.loaded.parameters.prior.plans.eligibility.norms.isc.finalized
      out.loaded.parameters.prior.plans.eligibility.finalized out.loaded.parameters.prior.plans.finalized out.loaded.parameters.prior.finalized
      out.loaded.parameters.prior.keys out.loaded.parameters.prior.plans.eligibility.certificates out.loaded.parameters.prior.plans.certificates
      out.loaded.parameters.prior.certificates out.root.source = some out.root :=
  NativeAggregateSection.certificateChecked (checked binding h).loaded
    (List.mem_of_find?_eq_some (checked binding h).root)

theorem originalShard {sha b id out} (h : check binding sha b id = some out)
    {e} (mem : e ∈ out.root.shards) :
    NativeParameterLineage.check sha .finalized
      (NativeParameterSection.expected (policy b) (state b) out.loaded.parameters.prior.plans) (policy b).validators
      out.loaded.parameters.prior.plans.eligibility.norms.isc.certificates out.loaded.parameters.prior.plans.eligibility.norms.isc.finalized
      out.loaded.parameters.prior.plans.eligibility.finalized out.loaded.parameters.prior.plans.finalized
      out.loaded.parameters.prior.keys out.loaded.parameters.prior.plans.eligibility.certificates out.loaded.parameters.prior.plans.certificates
      e.source = some e :=
  NativeAggregateSection.checkedShard (checked binding h).loaded (originalRoot binding h) mem

theorem entireCorpus {sha b id out} (h : check binding sha b id = some out) :
    out.corpus.entries.length = out.root.shards.length ∧
    out.root.shards.map NativeAggregateLineage.shardLeaf = out.root.certificate.common.leaves :=
  ⟨leafCounts binding (checked binding h).leaves,
    NativeAggregateLineage.resolvedLeaves (NativeAggregateLineage.checkedSource (originalRoot binding h)).selected⟩

theorem computedPosition {sha b id out} (h : check binding sha b id = some out) {i : Nat} {p}
    (position : out.corpus.entries[i]? = some p) :
    ∃ e leaf, out.root.shards[i]? = some e ∧ checkLeaf binding b p e = some leaf :=
  leafAt binding (checked binding h).leaves position

end Corpus
end DeltaReduce.NativeCertifiedCorpus
