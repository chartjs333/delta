import DeltaReduce.NativeVectorContext

/-! Ordered full-vector PARAMETER arithmetic from the original loaded corpus.
The draft signed fraction/denominator/coefficient-sum guards are explicitly
rechecked; original wide proof success is not assumed to imply them. -/
namespace DeltaReduce.NativeVectorArithmetic
open NativeReceiptBytes (Bytes)
open NativeVectorContext (Bound Slice shape sliceRows)

def kernelRow (s : Slice) : ParameterKernel.Row :=
  ⟨s.source.term.source.weight.numerator,s.source.term.source.weight.denominator,
    s.block.block.frame.values⟩

def lo (n : NativeAccumulatorBinding.Numbers) : Int := -(2^(n.accumulatorBits-1))
def hi (n : NativeAccumulatorBinding.Numbers) : Int := 2^(n.accumulatorBits-1)-1

def compute (n : NativeAccumulatorBinding.Numbers) (width : Nat) (slices : List Slice) : Option (List Int) :=
  ParameterKernel.checkedParameter (lo n) (hi n) NativeBinding.minInput NativeBinding.maxInput
    n.denominator width (slices.map kernelRow)

theorem computed {n width slices values} (h : compute n width slices = some values) :
    0 < width ∧ slices.map kernelRow ≠ [] ∧ values.length = width ∧
    values = ParameterKernel.exactParameterRows n.denominator (List.replicate width 0)
      (slices.map kernelRow) ∧
    (∀ s ∈ slices, s.block.block.frame.values.length = width) ∧
    ParameterKernel.PrefixesSafe (lo n) (hi n) NativeBinding.minInput NativeBinding.maxInput
      n.denominator 0 (List.replicate width 0) (slices.map kernelRow) := by
  have result := ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ h
  exact ⟨result.1,result.2.1,result.2.2.1,result.2.2.2.1,
    fun s hs => result.2.2.2.2.1 (kernelRow s) (List.mem_map.mpr ⟨s,hs,rfl⟩),result.2.2.2.2.2⟩

structure Result where
  domain : Bytes
  index : Nat
  first : NativeScaleBinding.Bound
  slices : List Slice
  values : List Int
  deriving DecidableEq, Repr

def reduce (b : Bound) (domain : Bytes) (index : Nat) : Option Result := do
  let first ← b.first.corpus.manifest.blocks[index]?
  let slices ← sliceRows index (NativePlanQCorpus.inDomain domain b.source.rows)
  let values ← compute b.source.plan.accumulator.numbers (shape first).entry.count slices
  some ⟨domain,index,first,slices,values⟩

theorem reduced {b domain index out} (h : reduce b domain index = some out) :
    out.domain = domain ∧ out.index = index ∧
    b.first.corpus.manifest.blocks[index]? = some out.first ∧
    sliceRows index (NativePlanQCorpus.inDomain domain b.source.rows) = some out.slices ∧
    compute b.source.plan.accumulator.numbers (shape out.first).entry.count out.slices = some out.values := by
  simp only [reduce,bind,Option.bind_eq_some_iff] at h
  obtain ⟨first,hf,slices,hs,values,hv,last⟩ := h
  cases Option.some.inj last
  exact ⟨rfl,rfl,hf,hs,hv⟩

theorem reducedFromSources {b domain index first slices values}
    (slot : b.first.corpus.manifest.blocks[index]? = some first)
    (rows : sliceRows index (NativePlanQCorpus.inDomain domain b.source.rows) = some slices)
    (value : compute b.source.plan.accumulator.numbers (shape first).entry.count slices = some values) :
    reduce b domain index = some ⟨domain,index,first,slices,values⟩ := by simp [reduce,slot,rows,value]

theorem allEligibleRows {b domain index out} (h : reduce b domain index = some out) :
    out.slices.map Slice.source = NativePlanQCorpus.inDomain domain b.source.rows :=
  (NativeVectorContext.slicedSources (reduced h).2.2.2.1).1

theorem exactOutput {b domain index out} (h : reduce b domain index = some out) :
    out.values = ParameterKernel.exactParameterRows b.source.plan.accumulator.numbers.denominator
      (List.replicate (shape out.first).entry.count 0) (out.slices.map kernelRow) ∧
    out.values.length = (shape out.first).entry.count := by
  have result := computed (reduced h).2.2.2.2
  exact ⟨result.2.2.2.1,result.2.2.1⟩

theorem coordinateRefines {b domain index out} (h : reduce b domain index = some out)
    (coordinate : Nat) (within : coordinate < (shape out.first).entry.count) :
    ∃ v, out.values[coordinate]? = some v ∧
      checkedAccumulate (lo b.source.plan.accumulator.numbers) (hi b.source.plan.accumulator.numbers)
        (lo b.source.plan.accumulator.numbers) (hi b.source.plan.accumulator.numbers) 0
        (ParameterKernel.coordinateTerms b.source.plan.accumulator.numbers.denominator
          coordinate (out.slices.map kernelRow)) = some v :=
  ParameterKernel.checkedParameterCoordinateRefines _ _ _ _ _ _ _ _
    (reduced h).2.2.2.2 coordinate within

theorem sourceAligned {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b
    domain index out}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) (calculated : reduce b domain index = some out) :
    ∀ s ∈ out.slices, shape s.block = shape out.first := by
  have src := NativeVectorContext.boundSource loaded
  have align := NativeVectorContext.alignFromSources src.2.1 src.2.2
  have same : NativeVectorContext.Bound.mk b.source b.first = b := by cases b; rfl
  rw [same] at align
  have r := reduced calculated
  exact NativeVectorContext.slicedShape align (fun _ h => List.mem_of_mem_filter h) r.2.2.1 r.2.2.2.1

theorem sourceProductBounds {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b
    domain index out}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) (calculated : reduce b domain index = some out)
    (s : Slice) (member : s ∈ out.slices) (coordinate : Nat) (v : Int)
    (value : s.block.block.frame.values[coordinate]? = some v) :
    |(s.source.term.coefficient : Int)*v| ≤
      (NativeAccumulatorBinding.limit b.source.plan.accumulator.numbers.productBits : Int) := by
  have src := NativeVectorContext.slicedSources (reduced calculated).2.2.2.1
  have mem : s.source ∈ b.source.rows := by
    have dm : s.source ∈ NativePlanQCorpus.inDomain domain b.source.rows := by
      rw [← src.1]; exact List.mem_map.mpr ⟨s,member,rfl⟩
    exact List.mem_of_mem_filter dm
  apply NativePlanQCorpus.boundProductFits (NativeVectorContext.boundSource loaded).1 s.source mem
    (blockIndex := index) (coordinateIndex := coordinate)
  simp [NativeAvailableQ.coordinate,src.2 s member,value]

theorem sourceCoefficient {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b
    domain index out}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) (calculated : reduce b domain index = some out)
    (s : Slice) (member : s ∈ out.slices) :
    (s.source.term.coefficient : Int) = (kernelRow s).numerator *
      ((b.source.plan.accumulator.numbers.denominator : Int) / (kernelRow s).denominator) := by
  have src := NativePlanQCorpus.boundSource (NativeVectorContext.boundSource loaded).1
  have mem : s.source ∈ b.source.rows := by
    have dm : s.source ∈ NativePlanQCorpus.inDomain domain b.source.rows := by
      rw [← allEligibleRows calculated]; exact List.mem_map.mpr ⟨s,member,rfl⟩
    exact List.mem_of_mem_filter dm
  have tm : s.source.term ∈ b.source.plan.coefficients := by
    rw [← (NativePlanQCorpus.completeRows src.2).1]; exact List.mem_map.mpr ⟨_,mem,rfl⟩
  have coefficient := (NativePlanCoefficients.boundCoefficientIdentity src.1 tm).2.1
  simpa [kernelRow,Int.natCast_ediv] using congrArg (fun n : Nat => (n : Int)) coefficient

theorem originalCoordinateTerms {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b
    domain index out}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) (calculated : reduce b domain index = some out) (coordinate : Nat) :
    ParameterKernel.coordinateTerms b.source.plan.accumulator.numbers.denominator
      coordinate (out.slices.map kernelRow) =
    out.slices.map (fun s => ((s.source.term.coefficient : Int),
      (s.block.block.frame.values[coordinate]?).getD 0)) := by
  simp only [ParameterKernel.coordinateTerms,List.map_map,Function.comp_def]
  apply List.map_congr_left
  intro s hs
  exact congrArg (fun c => (c,(s.block.block.frame.values[coordinate]?).getD 0))
    (sourceCoefficient loaded calculated s hs).symm

theorem originalCoordinateRefines {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b
    domain index out}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) (calculated : reduce b domain index = some out)
    (coordinate : Nat) (within : coordinate < (shape out.first).entry.count) :
    ∃ v, out.values[coordinate]? = some v ∧
      checkedAccumulate (lo b.source.plan.accumulator.numbers) (hi b.source.plan.accumulator.numbers)
        (lo b.source.plan.accumulator.numbers) (hi b.source.plan.accumulator.numbers) 0
        (out.slices.map (fun s => ((s.source.term.coefficient : Int),
          (s.block.block.frame.values[coordinate]?).getD 0))) = some v := by
  have result := coordinateRefines calculated coordinate within
  rw [originalCoordinateTerms loaded calculated coordinate] at result
  exact result

theorem noCoordinateFallback {b domain index out} (calculated : reduce b domain index = some out)
    (coordinate : Nat) (within : coordinate < (shape out.first).entry.count)
    (s : Slice) (member : s ∈ out.slices) :
    ∃ v, s.block.block.frame.values[coordinate]? = some v := by
  have length := (computed (reduced calculated).2.2.2.2).2.2.2.2.1 s member
  have lt : coordinate < s.block.block.frame.values.length := by omega
  exact ⟨s.block.block.frame.values[coordinate],List.getElem?_eq_getElem lt⟩

def domains (b : Bound) : List Bytes :=
  (b.source.rows.map (fun r => r.term.source.member.input.domain)).eraseDups.mergeSort
    NativeSchemaBinding.less

def keys (b : Bound) : List (Bytes × Nat) :=
  (domains b).flatMap (fun d => (List.range b.first.corpus.manifest.blocks.length).map (d,·))

theorem keysComplete (b : Bound) (domain : Bytes) (index : Nat) :
    (domain,index) ∈ keys b ↔
    (∃ r ∈ b.source.rows, r.term.source.member.input.domain = domain) ∧
      index < b.first.corpus.manifest.blocks.length := by
  simp [keys,domains,List.mem_flatMap,List.mem_map,eq_comm]

def reduceKeys (b : Bound) : List (Bytes × Nat) → Option (List Result)
  | [] => some []
  | k::ks => do
    let out ← reduce b k.1 k.2
    let rest ← reduceKeys b ks
    some (out::rest)

theorem reducedKeys {b ks outs} (h : reduceKeys b ks = some outs) :
    outs.map (fun r => (r.domain,r.index)) = ks ∧
    ∀ out ∈ outs, reduce b out.domain out.index = some out := by
  induction ks generalizing outs with
  | nil => simp [reduceKeys] at h; subst outs; exact ⟨rfl,by simp⟩
  | cons k ks ih =>
    simp only [reduceKeys,bind,Option.bind_eq_some_iff] at h
    obtain ⟨out,ho,rest,hr,last⟩ := h
    cases Option.some.inj last
    have result := reduced ho
    have tail := ih hr
    refine ⟨by simp [result.1,result.2.1,tail.1],?_⟩
    intro x hx
    rcases List.mem_cons.mp hx with same | inside
    · subst x; simpa only [result.1,result.2.1] using ho
    · exact tail.2 x inside

def run (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) :
    Option (Bound × List Result) := do
  let b ← NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs
  let results ← reduceKeys b (keys b)
  some (b,results)

theorem runSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b results}
    (h : run sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some (b,results)) :
    NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b ∧
    results.map (fun r => (r.domain,r.index)) = keys b ∧
    ∀ out ∈ results, reduce b out.domain out.index = some out := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨b',hb,results',hr,last⟩ := h
  cases Option.some.inj last
  exact ⟨hb,reducedKeys hr⟩
end DeltaReduce.NativeVectorArithmetic
