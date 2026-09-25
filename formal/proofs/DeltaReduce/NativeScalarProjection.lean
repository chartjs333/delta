import DeltaReduce.ArithmeticBinding

/-! Explicit scalar-shard abstraction for the existing TLA arithmetic model.
This is a checked, lossless numeric projection, not a native admission rule.
Multi-coordinate shards have no scalar projection; native vector admission is
unchanged. Symbol/parent/QC authentication and the complete action bridge remain
separate obligations. No caller supplies an expected scalar result. -/
namespace DeltaReduce.NativeScalarProjection
open NativeBinding

structure Layout where
  width : Nat
  shards : List Shard
  positive : 0 < width
  scalar : ∀ s ∈ shards, s.length = 1 ∧ s.offset < width
  names : (shards.map Shard.id).Nodup
  coverage : ∀ i ∈ List.range width, (shards.map Shard.offset).count i = 1

def layout (frame : ParameterFrame) : Option Layout :=
  if h : 0 < frame.coordinates.length ∧
      (∀ s ∈ frame.shards, s.length = 1 ∧ s.offset < frame.coordinates.length) ∧
      (frame.shards.map Shard.id).Nodup ∧
      (∀ i ∈ List.range frame.coordinates.length, (frame.shards.map Shard.offset).count i = 1) then
    some ⟨frame.coordinates.length, frame.shards, h.1, h.2.1, h.2.2.1, h.2.2.2⟩
  else none

inductive Cells (values : List Int) : List Shard → List (String × Int) → Prop where
  | nil : Cells values [] []
  | cons {s shards value rest} (atOffset : values[s.offset]? = some value)
      (tail : Cells values shards rest) : Cells values (s :: shards) ((s.id,value) :: rest)

def readCells (values : List Int) : (shards : List Shard) →
    Option {cells : List (String × Int) // Cells values shards cells}
  | [] => some ⟨[], .nil⟩
  | s :: rest =>
      match atOffset : values[s.offset]? with
      | none => none
      | some value => do
          let tail ← readCells values rest
          some ⟨(s.id,value) :: tail.val, .cons atOffset tail.property⟩

structure Projected (l : Layout) (values : List Int) where
  shape : values.length = l.width
  cells : List (String × Int)
  source : Cells values l.shards cells

def project (l : Layout) (values : List Int) : Option (Projected l values) := do
  if shape : values.length = l.width then
    let cells ← readCells values l.shards
    some ⟨shape, cells.val, cells.property⟩
  else none

theorem cellsNames {values shards cells} (h : Cells values shards cells) :
    cells.map Prod.fst = shards.map Shard.id := by
  induction h with
  | nil => rfl
  | cons _ _ ih => simp only [List.map_cons, ih]

theorem cellsAt {values shards cells} (h : Cells values shards cells)
    (index : Nat) (s : Shard) (found : shards[index]? = some s) :
    ∃ value, values[s.offset]? = some value ∧ cells[index]? = some (s.id,value) := by
  induction h generalizing index s with
  | nil => simp at found
  | cons atOffset tail ih =>
      cases index with
      | zero => simp only [List.getElem?_cons_zero] at found; cases found; exact ⟨_,atOffset,rfl⟩
      | succ index => exact ih index s found

theorem cellOrigin {values shards cells} (h : Cells values shards cells) {name value}
    (member : (name,value) ∈ cells) :
    ∃ s ∈ shards, s.id = name ∧ values[s.offset]? = some value := by
  induction h with
  | nil => simp at member
  | @cons s shards v rest atOffset tail ih =>
      rcases List.mem_cons.mp member with same | member
      · cases same; exact ⟨s,List.mem_cons_self,rfl,atOffset⟩
      · obtain ⟨source, hs, hn, hv⟩ := ih member
        exact ⟨source,List.mem_cons_of_mem _ hs,hn,hv⟩

theorem cellsUnique {values shards left right} (a : Cells values shards left)
    (b : Cells values shards right) : left = right := by
  induction a generalizing right with
  | nil => cases b; rfl
  | cons atOffset tail ih =>
      cases b with
      | cons other rest =>
          have same := Option.some.inj (atOffset.symm.trans other)
          simp only [same, ih rest]

theorem layoutSource {frame l} (accepted : layout frame = some l) :
    l.width = frame.coordinates.length ∧ l.shards = frame.shards := by
  unfold layout at accepted
  split at accepted
  · cases accepted; exact ⟨rfl,rfl⟩
  · contradiction

theorem nonScalarLayoutRejected {frame s} (member : s ∈ frame.shards)
    (wrong : s.length ≠ 1) : layout frame = none := by
  unfold layout
  split
  · rename_i h; exact False.elim (wrong (h.2.1 s member).1)
  · rfl

theorem coveredOffset (l : Layout) (i : Nat) (within : i < l.width) :
    ∃ s ∈ l.shards, s.offset = i := by
  have count := l.coverage i (List.mem_range.mpr within)
  have member : i ∈ l.shards.map Shard.offset := by
    apply List.count_pos_iff.mp
    omega
  exact List.mem_map.mp member

theorem projectionRetainsEveryCoordinate {l values} (p : Projected l values)
    (i : Nat) (within : i < l.width) :
    ∃ s ∈ l.shards, s.offset = i ∧
      ∃ value, values[i]? = some value ∧ (s.id,value) ∈ p.cells := by
  obtain ⟨s, member, offset⟩ := coveredOffset l i within
  obtain ⟨index, found⟩ := List.mem_iff_getElem?.mp member
  obtain ⟨value, atOffset, atIndex⟩ := cellsAt p.source index s found
  exact ⟨s,member,offset,value,by simpa only [offset] using atOffset,
    List.mem_of_getElem? atIndex⟩

theorem projectionNamesExact {l values} (p : Projected l values) :
    p.cells.map Prod.fst = l.shards.map Shard.id ∧ (p.cells.map Prod.fst).Nodup :=
  ⟨cellsNames p.source, by rw [cellsNames p.source]; exact l.names⟩

theorem projectionInjective {l left right} (a : Projected l left) (b : Projected l right)
    (same : a.cells = b.cells) : left = right := by
  apply List.ext_getElem?
  intro i
  by_cases within : i < l.width
  · obtain ⟨s, member, offset⟩ := coveredOffset l i within
    obtain ⟨index, found⟩ := List.mem_iff_getElem?.mp member
    obtain ⟨x, hx, cx⟩ := cellsAt a.source index s found
    obtain ⟨y, hy, cy⟩ := cellsAt b.source index s found
    rw [same, cy] at cx
    have value : y = x := congrArg Prod.snd (Option.some.inj cx)
    subst y
    simpa only [offset] using hx.trans hy.symm
  · have leftEnd : left[i]? = none := List.getElem?_eq_none (by rw [a.shape]; omega)
    have rightEnd : right[i]? = none := List.getElem?_eq_none (by rw [b.shape]; omega)
    exact leftEnd.trans rightEnd.symm

theorem projectWrongShape {l values} (wrong : values.length ≠ l.width) :
    project l values = none := by simp [project, wrong]

theorem cellsPreserveAllValues {l values} (p : Projected l values) {name value}
    (member : (name,value) ∈ p.cells) : ∃ i, i < l.width ∧ values[i]? = some value := by
  obtain ⟨s, hs, _, hv⟩ := cellOrigin p.source member
  exact ⟨s.offset,(l.scalar s hs).2,hv⟩

structure Parameter {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) where
  value : Int
  scalar : native.partition.length = 1
  exactNumerator : native.numerators = [value]

def parameter {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) : Option (Parameter native) :=
  match shape : native.numerators with
  | [value] => if scalar : native.partition.length = 1 then some ⟨value,scalar,shape⟩ else none
  | _ => none

theorem parameterRetainsCanonicalFraction {codec store trust anchor}
    {binding : Binding codec trust anchor store} {domain shard}
    {native : DerivedParameter binding domain shard} (p : Parameter native) :
    native.body.numerators = [p.value] ∧
    native.body.denominator = native.assignment.denominator ∧
    native.body.inputLeafIds = native.assignment.contributions.map (fun c => c.q.id) :=
  ⟨p.exactNumerator,rfl,rfl⟩

theorem parameterScalarComputedFromNativeRows {codec store trust anchor}
    {binding : Binding codec trust anchor store} {domain shard}
    {native : DerivedParameter binding domain shard} (p : Parameter native) :
    checkedAccumulate (accumulatorLo binding.profile) (accumulatorHi binding.profile)
      (accumulatorLo binding.profile) (accumulatorHi binding.profile) 0
      (ParameterKernel.coordinateTerms native.assignment.denominator 0 native.rows) = some p.value := by
  obtain ⟨value, atIndex, computed⟩ := derivedParameterCoordinateRefines native 0 (by rw [p.scalar]; omega)
  have same : value = p.value := by simpa only [DerivedParameter.body, p.exactNumerator,
    List.getElem?_cons_zero, Option.some.injEq] using atIndex.symm
  simpa only [same] using computed

theorem vectorParameterHasNoScalarProjection {codec store trust anchor}
    {binding : Binding codec trust anchor store} {domain shard}
    (native : DerivedParameter binding domain shard) (notScalar : native.partition.length ≠ 1) :
    parameter native = none := by
  unfold parameter
  split <;> simp_all

structure Apply {codec store trust anchor} {binding : Binding codec trust anchor store}
    (native : NativeApply binding) where
  scalarLayout : Layout
  layoutSelected : layout native.core.conversion.certified.corpus.frame = some scalarLayout
  model : Projected scalarLayout native.body.nextModel
  optimizer : Projected scalarLayout native.body.nextOptimizer

def applyResult {codec store trust anchor} {binding : Binding codec trust anchor store}
    (native : NativeApply binding) : Option (Apply native) := do
  match selected : layout native.core.conversion.certified.corpus.frame with
  | none => none
  | some l =>
      let model ← project l native.body.nextModel
      let optimizer ← project l native.body.nextOptimizer
      some ⟨l,selected,model,optimizer⟩

theorem applyRetainsNativeHashPreimages {codec store trust anchor}
    {binding : Binding codec trust anchor store} {native : NativeApply binding}
    (_p : Apply native) :
    native.body.nextModelHash = codec.valueHash .model native.body.nextModel ∧
    native.body.nextOptimizerHash = codec.valueHash .optimizer native.body.nextOptimizer := ⟨rfl,rfl⟩

theorem applyCoordinatePairFromSameSchema {codec store trust anchor}
    {binding : Binding codec trust anchor store} {native : NativeApply binding}
    (p : Apply native) (index : Nat) (s : Shard)
    (found : p.scalarLayout.shards[index]? = some s) :
    ∃ model optimizer, native.body.nextModel[s.offset]? = some model ∧
      native.body.nextOptimizer[s.offset]? = some optimizer ∧
      p.model.cells[index]? = some (s.id,model) ∧
      p.optimizer.cells[index]? = some (s.id,optimizer) := by
  obtain ⟨model, hm, cm⟩ := cellsAt p.model.source index s found
  obtain ⟨optimizer, ho, co⟩ := cellsAt p.optimizer.source index s found
  exact ⟨model,optimizer,hm,ho,cm,co⟩

theorem applyLayoutComesFromBoundSchema {codec store trust anchor}
    {binding : Binding codec trust anchor store} {native : NativeApply binding}
    (p : Apply native) :
    p.scalarLayout.width = native.core.conversion.certified.corpus.frame.coordinates.length ∧
    p.scalarLayout.shards = native.core.conversion.certified.corpus.frame.shards :=
  layoutSource p.layoutSelected

theorem applyNoScalarLayoutRejects {codec store trust anchor}
    {binding : Binding codec trust anchor store} (native : NativeApply binding)
    (unrepresentable : layout native.core.conversion.certified.corpus.frame = none) :
    applyResult native = none := by
  unfold applyResult
  split
  · rfl
  · rename_i l selected
    rw [unrepresentable] at selected
    contradiction

end DeltaReduce.NativeScalarProjection
