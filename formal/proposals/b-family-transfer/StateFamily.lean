import NativeFamily

/-! General lossless global state reconstruction through ORIGINAL shard ranges.
This uses frozen ParameterFrameValid coverage. R3 transitions are not modeled. -/
namespace DeltaReduce.StateFamily
open NativeBinding

structure Layout where
  frame : ParameterFrame
  ranges : ∀ s ∈ frame.shards, 0 < s.length ∧ s.offset + s.length ≤ frame.coordinates.length
  coverage : ∀ i ∈ List.range frame.coordinates.length, (coveredCoordinates frame).count i = 1

def ofValidated {authority profile model optimizer frame}
    (valid : ParameterFrameValid authority profile model optimizer frame) : Layout :=
  ⟨frame,valid.2.2.2.2.1,valid.2.2.2.2.2.1⟩

def shards (l : Layout) : ShardFamily.Layout :=
  ⟨l.frame.shards.length,fun s => l.frame.shards[s.val].length,
    fun s => (l.ranges _ (List.getElem_mem s.isLt)).1⟩

def globalIndex (l : Layout) (s : Fin (shards l).count) (k : Fin ((shards l).width s)) :
    Fin l.frame.coordinates.length :=
  ⟨(l.frame.shards[s.val]'s.isLt).offset + k.val,by
    have range := l.ranges (l.frame.shards[s.val]'s.isLt) (List.getElem_mem s.isLt)
    have inside := k.isLt
    change k.val < (l.frame.shards[s.val]'s.isLt).length at inside
    omega⟩

def whole (l : Layout) (common : Common) (values : List Cell)
    (shape : values.length = l.frame.coordinates.length) : ShardFamily.Whole (shards l) Common Cell :=
  ⟨common,fun s => List.ofFn (fun k => values[(globalIndex l s k).val]'(by rw [shape]; exact (globalIndex l s k).isLt)),
    fun _ => List.length_ofFn⟩

def family (l : Layout) (common : Common) (values : List Cell)
    (shape : values.length = l.frame.coordinates.length) := ShardFamily.project (whole l common values shape)

theorem globalCovered (l : Layout) (i : Fin l.frame.coordinates.length) :
    ∃ s : Fin (shards l).count,
      (l.frame.shards[s.val]'s.isLt).offset ≤ i.val ∧
      i.val < (l.frame.shards[s.val]'s.isLt).offset + (l.frame.shards[s.val]'s.isLt).length := by
  have count := l.coverage i.val (List.mem_range.mpr i.isLt)
  have member : i.val ∈ coveredCoordinates l.frame := List.count_pos_iff.mp (by omega)
  obtain ⟨s,hs,coordinate⟩ := List.mem_flatMap.mp member
  -- mem_map exposes the original local coordinate; no new shard is introduced.
  obtain ⟨k,hk,hglobal⟩ := List.mem_map.mp coordinate
  obtain ⟨index,hi⟩ := List.mem_iff_getElem?.mp hs
  obtain ⟨bound,same⟩ := List.getElem?_eq_some_iff.mp hi
  refine ⟨⟨index,bound⟩,?_,?_⟩
  · change (l.frame.shards[index]'bound).offset ≤ i.val
    rw [same]; omega
  · change i.val < (l.frame.shards[index]'bound).offset + (l.frame.shards[index]'bound).length
    rw [same]
    have := List.mem_range.mp hk; omega

def contains (l : Layout) (i : Fin l.frame.coordinates.length) (s : Fin (shards l).count) : Bool :=
  decide ((l.frame.shards[s.val]'s.isLt).offset ≤ i.val ∧
    i.val < (l.frame.shards[s.val]'s.isLt).offset + (l.frame.shards[s.val]'s.isLt).length)

/-- A representation lookup, not admission: missing ranges return none. A
validated layout already checks exact coverage, so ambiguity is not accepted. -/
def read (l : Layout) (f : ShardFamily.Family (shards l) Common Cell)
    (i : Fin l.frame.coordinates.length) : Option Cell := do
  let s ← (List.finRange (shards l).count).find? (contains l i)
  if h : (l.frame.shards[s.val]'s.isLt).offset ≤ i.val ∧
      i.val < (l.frame.shards[s.val]'s.isLt).offset + (l.frame.shards[s.val]'s.isLt).length then
    let k : Fin ((shards l).width s) := ⟨i.val - (l.frame.shards[s.val]'s.isLt).offset,by
      change i.val - (l.frame.shards[s.val]'s.isLt).offset < (l.frame.shards[s.val]'s.isLt).length
      omega⟩
    some (f.view (ShardFamily.select (shards l) s k) s)
  else none

theorem readOriginal (l : Layout) (common : Common) (values : List Cell)
    (shape : values.length = l.frame.coordinates.length) (i : Fin l.frame.coordinates.length) :
    read l (family l common values shape) i = some (values[i.val]'(by rw [shape]; exact i.isLt)) := by
  unfold read
  cases found : (List.finRange (shards l).count).find? (contains l i) with
  | none =>
    obtain ⟨s,hs⟩ := globalCovered l i
    have rejected := (List.find?_eq_none.mp found) s (List.mem_finRange s)
    simp [contains,hs] at rejected
  | some s =>
    have accepted : (l.frame.shards[s.val]'s.isLt).offset ≤ i.val ∧
        i.val < (l.frame.shards[s.val]'s.isLt).offset + (l.frame.shards[s.val]'s.isLt).length := by
      simpa [contains] using List.find?_some found
    simp only [Bind.bind,Option.bind,dif_pos accepted,family,ShardFamily.project,whole,List.getElem_ofFn,
      ShardFamily.select_self,globalIndex]
    congr 2
    omega

def rebuild (l : Layout) (f : ShardFamily.Family (shards l) Common Cell) : Option (List Cell) :=
  NativeInputProjection.collect (read l f) (List.finRange l.frame.coordinates.length)

theorem collectExact {α β} (f : α → Option β) (g : α → β) (xs : List α)
    (exactValue : ∀ x ∈ xs, f x = some (g x)) :
    NativeInputProjection.collect f xs = some (xs.map g) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    simp only [NativeInputProjection.collect,exactValue x (List.mem_cons_self),List.map_cons,
      ih (fun y hy => exactValue y (List.mem_cons_of_mem _ hy)),Bind.bind,Option.bind]

theorem fullOrderedState (l : Layout) (common : Common) (values : List Cell)
    (shape : values.length = l.frame.coordinates.length) :
    rebuild l (family l common values shape) = some values := by
  unfold rebuild
  rw [collectExact _ (fun i => values[i.val]'(by rw [shape]; exact i.isLt)) _
    (fun i _ => readOriginal l common values shape i)]
  congr 1
  apply List.ext_getElem?
  intro i
  by_cases hi : i < l.frame.coordinates.length
  · simp [hi,shape]
  · simp [hi,show values.length ≤ i by rw [shape]; omega]

theorem globalInjective (l : Layout) (common : Common) (left right : List Cell)
    (ls : left.length = l.frame.coordinates.length) (rs : right.length = l.frame.coordinates.length)
    (same : family l common left ls = family l common right rs) : left = right := by
  have equal := congrArg (rebuild l) same
  simpa only [fullOrderedState,Option.some.injEq] using equal

theorem exactlyOnce (l : Layout) (i : Fin l.frame.coordinates.length) :
    (coveredCoordinates l.frame).count i.val = 1 := l.coverage i.val (List.mem_range.mpr i.isLt)

section NativeApply
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
variable (native : NativeApply binding)

def nativeLayout := ofValidated native.core.conversion.certified.corpus.validated

theorem nativeModelShape : binding.model.values.length = (nativeLayout native).frame.coordinates.length := by
  obtain ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,shape,_⟩ := native.core.conversion.certified.corpus.validated
  exact shape

def nativeCell (k : Fin (nativeLayout native).frame.coordinates.length) : NativeFamily.ApplyCell :=
  NativeFamily.applyCell native ⟨k.val,by rw [nativeModelShape native]; exact k.isLt⟩

def nativeValues := List.ofFn (nativeCell native)

def nativeFamily (control : Control) := family (nativeLayout native) (native,control) (nativeValues native) List.length_ofFn

theorem nativeCompleteState (control : Control) :
    rebuild (nativeLayout native) (nativeFamily native control) = some (nativeValues native) :=
  fullOrderedState _ _ _ _

theorem nativeOriginalLayout (control : Control) :
    (nativeFamily native control).common.1.core.conversion.certified.corpus.frame.shards =
      native.core.conversion.certified.corpus.frame.shards ∧
    (nativeFamily native control).common.1.parameterBytes = native.parameterBytes ∧
    (nativeFamily native control).common.1.bytes = native.bytes := ⟨rfl,rfl,rfl⟩

theorem nativeNextVectors :
    (nativeValues native).map NativeFamily.ApplyCell.nextModel = native.body.nextModel ∧
    (nativeValues native).map NativeFamily.ApplyCell.nextOptimizer = native.body.nextOptimizer := by
  have shape := nativeApplyOutputBounds native
  have modelShape := nativeModelShape native
  constructor <;> simp only [nativeValues,List.map_ofFn,Function.comp_def,nativeCell,NativeFamily.applyCell]
    <;> apply List.ext_getElem? <;> intro k <;> by_cases hk : k < (nativeLayout native).frame.coordinates.length
  · have hm : k < binding.model.values.length := by omega
    have hn : k < native.core.computation.nextModel.length := by
      change k < native.body.nextModel.length; rw [shape.1]; exact hm
    simp [hk,List.getElem?_eq_getElem hn,NativeApply.body,NativeApplyCore.body]
  · simp [hk,show native.body.nextModel.length ≤ k by rw [shape.1,modelShape]; omega]
  · have hm : k < binding.model.values.length := by omega
    have hn : k < native.core.computation.nextOptimizer.length := by
      change k < native.body.nextOptimizer.length; rw [shape.2.1]; exact hm
    simp [hk,List.getElem?_eq_getElem hn,NativeApply.body,NativeApplyCore.body]
  · simp [hk,show native.body.nextOptimizer.length ≤ k by rw [shape.2.1,modelShape]; omega]

theorem nativeRebuildHashPreimages (control : Control) :
    (rebuild (nativeLayout native) (nativeFamily native control)).map
      (fun cells => (codec.valueHash .model (cells.map NativeFamily.ApplyCell.nextModel),
        codec.valueHash .optimizer (cells.map NativeFamily.ApplyCell.nextOptimizer))) =
      some (native.body.nextModelHash,native.body.nextOptimizerHash) := by
  rw [nativeCompleteState]
  simp only [Option.map_some,(nativeNextVectors native).1,(nativeNextVectors native).2]
  rfl

end NativeApply

end DeltaReduce.StateFamily
