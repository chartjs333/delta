import DeltaReduce.NativeVectorArtifacts

/-! Executable join of actual original source loading and actual draft PARAMETER
derivation. Binding authentication/codec remain the existing named boundaries.
No expected output, whole translated body or arithmetic approval input. -/
namespace DeltaReduce.NativeVectorJoin
open NativeBinding
open NativeVectorLayout (Layout text shardName)
open NativeVectorArtifacts (Artifact RowsImage)

def Checks {codec store trust anchor} (binding : Binding codec trust anchor store)
    (b : NativeVectorContext.Bound) (l : Layout) (a : Artifact)
    {domain index} (d : DerivedParameter binding (text domain) (shardName index))
    (out : NativeVectorArithmetic.Result) (contributions : List Contribution) : Prop :=
  binding.authority.schema = a.ref ∧ d.frame.coordinates = l.coordinates ∧ d.frame.shards = l.shards ∧
  d.assignment.contributions = contributions ∧ d.rows = out.slices.map NativeVectorArithmetic.kernelRow ∧
  d.assignment.denominator = b.source.plan.accumulator.numbers.denominator ∧
  binding.profile.accumulatorBits = b.source.plan.accumulator.numbers.accumulatorBits ∧
  d.partition.length = (NativeVectorContext.shape out.first).entry.count ∧
  l.positions.length * b.source.rows.length ≤ 65536 ∧
  (NativeVectorArithmetic.domains b).length * l.shards.length ≤ 4096 ∧
  store a.ref.id = some a.raw
instance {codec store trust anchor} (binding : Binding codec trust anchor store) (b l a)
    {domain index} (d : DerivedParameter binding (text domain) (shardName index)) (out cs) :
    Decidable (Checks binding b l a d out cs) := by unfold Checks; infer_instance

structure Joined {codec store trust anchor} (binding : Binding codec trust anchor store)
    (b : NativeVectorContext.Bound) (domain : Bytes) (index : Nat) where
  layout : Layout
  layoutComputed : NativeVectorLayout.construct b.first.corpus.manifest.plan = some layout
  schema : Artifact
  schemaComputed : NativeVectorArtifacts.schema codec.hash layout = some schema
  native : DerivedParameter binding (text domain) (shardName index)
  derived : deriveParameter binding (text domain) (shardName index) = some native
  out : NativeVectorArithmetic.Result
  calculated : NativeVectorArithmetic.reduce b domain index = some out
  images : RowsImage codec store schema.ref native.frame native.assignment
    (NativeVectorContext.shape out.first).entry.count out.slices
  checked : Checks binding b layout schema native out images.contributions
  bounded : schema.raw.length + (images.sources.map (fun a => a.raw.length)).sum ≤ 8388608

def join {codec store trust anchor} (binding : Binding codec trust anchor store)
    (b : NativeVectorContext.Bound) (domain : Bytes) (index : Nat) : Option (Joined binding b domain index) := do
  match hl : NativeVectorLayout.construct b.first.corpus.manifest.plan with
  | none => none
  | some l =>
    match ha : NativeVectorArtifacts.schema codec.hash l with
    | none => none
    | some a =>
      match hd : deriveParameter binding (text domain) (shardName index) with
      | none => none
      | some d =>
        match ho : NativeVectorArithmetic.reduce b domain index with
        | none => none
        | some out =>
          let rows ← NativeVectorArtifacts.loadImages codec store a.ref d.frame d.assignment
            (NativeVectorContext.shape out.first).entry.count out.slices
          if checked : Checks binding b l a d out rows.contributions then
            if bounded : a.raw.length + (rows.sources.map (fun a => a.raw.length)).sum ≤ 8388608 then
              some ⟨l,hl,a,ha,d,hd,out,ho,rows,checked,bounded⟩
            else none
          else none

theorem numeratorsDerived {codec store trust anchor} {binding : Binding codec trust anchor store}
    {b domain index} (r : Joined binding b domain index) : r.native.numerators = r.out.values := by
  have computed := r.native.computed
  rw [r.checked.2.2.2.2.1,r.checked.2.2.2.2.2.1,r.checked.2.2.2.2.2.2.2.1] at computed
  have expected := (NativeVectorArithmetic.reduced r.calculated).2.2.2.2
  have width := r.checked.2.2.2.2.2.2.1
  have eq : ParameterKernel.checkedParameter (accumulatorLo binding.profile) (accumulatorHi binding.profile)
      minInput maxInput b.source.plan.accumulator.numbers.denominator
      (NativeVectorContext.shape r.out.first).entry.count (r.out.slices.map NativeVectorArithmetic.kernelRow) =
      some r.out.values := by
    simpa [accumulatorLo,accumulatorHi,NativeVectorArithmetic.compute,
      NativeVectorArithmetic.lo,NativeVectorArithmetic.hi,width] using expected
  exact Option.some.inj (computed.symm.trans eq)

theorem fullOriginalRows {codec store trust anchor} {binding : Binding codec trust anchor store}
    {b domain index} (r : Joined binding b domain index) :
    r.out.slices.map NativeVectorContext.Slice.source = NativePlanQCorpus.inDomain domain b.source.rows ∧
    r.images.sources.length = (NativePlanQCorpus.inDomain domain b.source.rows).length := by
  have all := NativeVectorArithmetic.allEligibleRows r.calculated
  exact ⟨all,r.images.count.trans (by simpa using congrArg List.length all)⟩

theorem exactSchemaBytes {codec store trust anchor} {binding : Binding codec trust anchor store}
    {b domain index} (r : Joined binding b domain index) :
    store binding.authority.schema.id = some (NativeVectorArtifacts.encodeSchema r.layout) := by
  rw [r.checked.1]
  rw [← (NativeVectorArtifacts.schemaEncoded r.schemaComputed).1]
  exact r.checked.2.2.2.2.2.2.2.2.2.2

theorem originalCoordinate {codec store trust anchor} {binding : Binding codec trust anchor store}
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b domain index}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) (r : Joined binding b domain index) (i : Nat)
    (within : i < (NativeVectorContext.shape r.out.first).entry.count) :
    ∃ v, r.native.numerators[i]? = some v ∧
      checkedAccumulate (NativeVectorArithmetic.lo b.source.plan.accumulator.numbers)
        (NativeVectorArithmetic.hi b.source.plan.accumulator.numbers)
        (NativeVectorArithmetic.lo b.source.plan.accumulator.numbers)
        (NativeVectorArithmetic.hi b.source.plan.accumulator.numbers) 0
        (r.out.slices.map (fun s => ((s.source.term.coefficient : Int),
          (s.block.block.frame.values[i]?).getD 0))) = some v := by
  rw [numeratorsDerived r]
  exact NativeVectorArithmetic.originalCoordinateRefines loaded r.calculated i within

def run {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input)
    (domain : Bytes) (index : Nat) :
    Option ((b : NativeVectorContext.Bound) × Joined binding b domain index) := do
  let b ← NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs
  let j ← join binding b domain index
  some ⟨b,j⟩

theorem runSource {codec store trust anchor} {binding : Binding codec trust anchor store}
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs domain index result}
    (h : run binding sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs domain index = some result) :
    NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some result.1 := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨b,hb,j,_,last⟩ := h
  cases Option.some.inj last
  exact hb

theorem runFromContext {codec store trust anchor} (binding : Binding codec trust anchor store)
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) (domain : Bytes) (index : Nat) :
    run binding sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs domain index =
      (join binding b domain index).map (fun j => ⟨b,j⟩) := by
  simp only [run,loaded,Bind.bind,Option.bind]
  cases join binding b domain index <;> rfl

end DeltaReduce.NativeVectorJoin
