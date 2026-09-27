import DeltaReduce.NativeIscProjection
import DeltaReduce.NativeSizedParameterSection

/-! PLAN assignments computed from original APC weights, required keys and
prepared PARAMETER contexts. No aggregate, expected arithmetic result or APPLY
profile is synthesized here. Ordinal shard naming is an explicit restriction. -/
namespace DeltaReduce.NativePlanAssignments
open NativeBinding
open NativeVectorContext (Bound Slice)
open NativeVectorLayout (text shardName)
open NativeIscProjection (Image RowImage LeafImage)

def SameSource (s : Slice) (r : RowImage) : Prop :=
  r.source.member = s.source.term.source.member ∧ r.source.corpus = s.source.corpus.manifest
instance (s r) : Decidable (SameSource s r) := by unfold SameSource; infer_instance

structure ContributionRow where
  source : Slice
  member : RowImage
  leaf : LeafImage

def contribution (r : ContributionRow) := NativeVectorArtifacts.contribution r.source r.leaf.artifact.ref

def loadContribution (image : Image) (index : Nat) (s : Slice) : Option ContributionRow := do
  let r ← image.rows.find? (fun r => decide (SameSource s r))
  let l ← r.leaves[index]?
  if l.block = s.block ∧ s.block.block.header.ordinal = index then some ⟨s,r,l⟩ else none

theorem contributionSource {image index s r} (h : loadContribution image index s = some r) :
    r.source = s ∧ image.rows.find? (fun r => decide (SameSource s r)) = some r.member ∧
    SameSource s r.member ∧ r.member.leaves[index]? = some r.leaf ∧
    r.leaf.block = s.block ∧ s.block.block.header.ordinal = index := by
  simp only [loadContribution,bind,Option.bind_eq_some_iff] at h
  obtain ⟨m,hm,l,hl,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  have same : SameSource s m := by simpa using (List.find?_some hm)
  exact ⟨rfl,hm,same,hl,by assumption⟩

theorem contributionFields (r : ContributionRow) :
    (contribution r).ticket = text r.source.source.term.source.member.input.ticket ∧
    (contribution r).weight.numerator = r.source.source.term.source.weight.numerator ∧
    (contribution r).weight.denominator = r.source.source.term.source.weight.denominator ∧
    (contribution r).q = r.leaf.artifact.ref := ⟨rfl,rfl,rfl,rfl⟩

theorem noMemberRejected {image index s}
    (absent : image.rows.find? (fun r => decide (SameSource s r)) = none) :
    loadContribution image index s = none := by simp [loadContribution,absent]

theorem missingLeafRejected {image index s r}
    (member : image.rows.find? (fun r => decide (SameSource s r)) = some r)
    (absent : r.leaves[index]? = none) : loadContribution image index s = none := by
  simp [loadContribution,member,absent]

def loadContributions (image : Image) (index : Nat) : List Slice → Option (List ContributionRow)
  | [] => some []
  | s::ss => do
    let r ← loadContribution image index s
    let rest ← loadContributions image index ss
    some (r::rest)

theorem allSources {image index ss rs} (h : loadContributions image index ss = some rs) :
    rs.map ContributionRow.source = ss := by
  induction ss generalizing rs with
  | nil => simp [loadContributions] at h; subst rs; rfl
  | cons s ss ih =>
    simp only [loadContributions,bind,Option.bind_eq_some_iff] at h
    obtain ⟨r,hr,rest,ht,last⟩ := h
    cases Option.some.inj last
    simp [(contributionSource hr).1,ih ht]

theorem contributionAt {image index ss rs} (h : loadContributions image index ss = some rs)
    {n : Nat} {r} (position : rs[n]? = some r) :
    ∃ s, ss[n]? = some s ∧ loadContribution image index s = some r := by
  induction ss generalizing rs n with
  | nil => simp [loadContributions] at h; subst rs; simp at position
  | cons s ss ih =>
    simp only [loadContributions,bind,Option.bind_eq_some_iff] at h
    obtain ⟨r',hr,rest,ht,last⟩ := h
    cases Option.some.inj last
    cases n with
    | zero => simp at position; subst r; exact ⟨s,rfl,hr⟩
    | succ n => simpa using ih ht (by simpa using position)

def nativeKey (k : Bytes × Nat) : NativeParameter.Key := ⟨k.1,asciiBytes (shardName k.2)⟩

def findPrepared (b : Bound) (sec : NativeParameterSection.Bound) (k : Bytes × Nat) :=
  (NativeVectorAuthority.selectedBodies b sec).find? (fun e =>
    e.certificate.common.domain == k.1 && e.certificate.common.shard == asciiBytes (shardName k.2))

def PreparedChecks (b : Bound) (k : Bytes × Nat) (e : NativeParameterLineage.Edge) : Prop :=
  asciiBytes (text k.1) = k.1 ∧ validIdentifier (text k.1) = true ∧
  asciiBytes (text e.voteContext) = e.voteContext ∧ validIdentifier (text e.voteContext) = true ∧
  e.certificate.common.context = (NativeVectorAuthority.plan b).certificate.common.context ∧
  e.certificate.common.plan = (NativeVectorAuthority.plan b).id ∧
  e.certificate.common.isc = (NativeVectorAuthority.plan b).parent.qcId ∧
  e.certificate.common.ec = (NativeVectorAuthority.plan b).ec.id ∧
  e.certificate.common.denominator = b.source.plan.accumulator.numbers.denominator
instance (b k e) : Decidable (PreparedChecks b k e) := by unfold PreparedChecks; infer_instance

structure AssignmentRow where
  key : Bytes × Nat
  original : NativeParameterLineage.Edge
  first : NativeScaleBinding.Bound
  slices : List Slice
  rows : List ContributionRow

def assignment (b : Bound) (r : AssignmentRow) : Assignment :=
  ⟨text r.key.1,shardName r.key.2,text r.original.voteContext,
    b.source.plan.accumulator.numbers.denominator,r.first.quantum,r.rows.map contribution⟩

def loadAssignment (b : Bound) (image : Image) (sec : NativeParameterSection.Bound)
    (k : Bytes × Nat) : Option AssignmentRow := do
  let original ← findPrepared b sec k
  if PreparedChecks b k original then
    let first ← b.first.corpus.manifest.blocks[k.2]?
    let slices ← NativeVectorContext.sliceRows k.2 (NativePlanQCorpus.inDomain k.1 b.source.rows)
    if slices ≠ [] ∧ ∀ s ∈ slices, NativeVectorContext.shape s.block = NativeVectorContext.shape first then
      let rows ← loadContributions image k.2 slices
      some ⟨k,original,first,slices,rows⟩
    else none
  else none

structure AssignmentSource (b : Bound) (image : Image) (sec : NativeParameterSection.Bound)
    (k : Bytes × Nat) (r : AssignmentRow) : Prop where
  key : r.key = k
  original : findPrepared b sec k = some r.original
  checked : PreparedChecks b k r.original
  first : b.first.corpus.manifest.blocks[k.2]? = some r.first
  slices : NativeVectorContext.sliceRows k.2 (NativePlanQCorpus.inDomain k.1 b.source.rows) = some r.slices
  shapes : r.slices ≠ [] ∧ ∀ s ∈ r.slices, NativeVectorContext.shape s.block = NativeVectorContext.shape r.first
  rows : loadContributions image k.2 r.slices = some r.rows

theorem assignmentSource {b image sec k r} (h : loadAssignment b image sec k = some r) :
    AssignmentSource b image sec k r := by
  simp only [loadAssignment,bind,Option.bind_eq_some_iff] at h
  obtain ⟨e,he,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨first,hf,ss,hs,last⟩ := last
  split at last <;> try contradiction
  rename_i shapes
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨rows,hr,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,he,checks,hf,hs,shapes,hr⟩

theorem assignmentFromSource {b image sec k r} (h : AssignmentSource b image sec k r) :
    loadAssignment b image sec k = some r := by
  cases r
  cases h.key
  simp only [loadAssignment,h.original,bind,Option.bind,if_pos h.checked,h.first,h.slices,
    if_pos h.shapes,h.rows]

theorem noPreparedBodyRejected {b image sec k} (absent : findPrepared b sec k = none) :
    loadAssignment b image sec k = none := by simp [loadAssignment,absent]

theorem actualContext {b image sec k r} (h : loadAssignment b image sec k = some r) :
    asciiBytes (assignment b r).context = r.original.voteContext ∧
    (assignment b r).denominator = b.source.plan.accumulator.numbers.denominator :=
  ⟨(assignmentSource h).checked.2.2.1,rfl⟩

theorem completeContributions {b image sec k r} (h : loadAssignment b image sec k = some r) :
    r.rows.map (fun row => row.source.source) = NativePlanQCorpus.inDomain k.1 b.source.rows := by
  have src := assignmentSource h
  rw [← (NativeVectorContext.slicedSources src.slices).1,← allSources src.rows,List.map_map]
  rfl

theorem originalPrepared {b image sec k r} (h : loadAssignment b image sec k = some r) :
    r.original ∈ sec.bodies :=
  List.mem_of_mem_filter (List.mem_of_find?_eq_some (assignmentSource h).original)

def loadAssignments (b : Bound) (image : Image) (sec : NativeParameterSection.Bound) :
    List (Bytes × Nat) → Option (List AssignmentRow)
  | [] => some []
  | k::ks => do
    let r ← loadAssignment b image sec k
    let rest ← loadAssignments b image sec ks
    some (r::rest)

theorem allKeys {b image sec ks rs} (h : loadAssignments b image sec ks = some rs) :
    rs.map AssignmentRow.key = ks := by
  induction ks generalizing rs with
  | nil => simp [loadAssignments] at h; subst rs; rfl
  | cons k ks ih =>
    simp only [loadAssignments,bind,Option.bind_eq_some_iff] at h
    obtain ⟨r,hr,rest,ht,last⟩ := h
    cases Option.some.inj last
    simp [(assignmentSource hr).key,ih ht]

theorem assignmentAt {b image sec ks rs} (h : loadAssignments b image sec ks = some rs)
    {n : Nat} {r} (position : rs[n]? = some r) :
    ∃ k, ks[n]? = some k ∧ loadAssignment b image sec k = some r := by
  induction ks generalizing rs n with
  | nil => simp [loadAssignments] at h; subst rs; simp at position
  | cons k ks ih =>
    simp only [loadAssignments,bind,Option.bind_eq_some_iff] at h
    obtain ⟨r',hr,rest,ht,last⟩ := h
    cases Option.some.inj last
    cases n with
    | zero => simp at position; subst r; exact ⟨k,rfl,hr⟩
    | succ n => simpa using ih ht (by simpa using position)

end DeltaReduce.NativePlanAssignments
