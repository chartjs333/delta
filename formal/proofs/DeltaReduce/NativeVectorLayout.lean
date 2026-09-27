import DeltaReduce.NativeVectorArithmetic

/-! Explicit original-to-draft coordinate profile. No value sorting or native
admission changes. Original schema/plan metadata stays in the retained source. -/
namespace DeltaReduce.NativeVectorLayout
open NativeReceiptBytes (Bytes)
open NativeBinding (asciiBytes validIdentifier Shard)

def text (bs : Bytes) : String := String.ofList (bs.map (fun b => Char.ofNat b.toNat))
def digits (n : Nat) : String :=
  String.ofList (List.replicate (10 - (toString n).length) '0') ++ toString n
def coordinate (name : Bytes) (i : Nat) : String := text name ++ ":" ++ digits i
def shardName (i : Nat) : String := "s" ++ digits i

structure Location where
  parameter : Bytes
  flat : Nat
  global : Nat
  label : String
  deriving DecidableEq, Repr

def rowLocations (r : NativeSchemaBinding.Row) : List Location :=
  (List.range r.count).map (fun i => ⟨r.name,i,r.start+i,coordinate r.name i⟩)
def locations (s : NativeSchemaBinding.Schema) : List Location := s.rows.flatMap rowLocations
def shard (e : NativeShardPartition.Entry) : Shard := ⟨shardName e.ordinal,e.start,e.count⟩

theorem rowCoordinate {r : NativeSchemaBinding.Row} {i : Nat} (h : i < r.count) :
    (rowLocations r)[i]? = some ⟨r.name,i,r.start+i,coordinate r.name i⟩ := by
  simp [rowLocations,h]

theorem completeLocation {s l} (h : l ∈ locations s) :
    ∃ r ∈ s.rows, ∃ i < r.count, l = ⟨r.name,i,r.start+i,coordinate r.name i⟩ := by
  obtain ⟨r,hr,hl⟩ := List.mem_flatMap.mp h
  obtain ⟨i,hi,eq⟩ := List.mem_map.mp hl
  exact ⟨r,hr,i,List.mem_range.mp hi,eq.symm⟩

def Small (p : NativeShardPlanBinding.Bound) : Prop :=
  0 < p.inputs.schema.total ∧ p.inputs.schema.total ≤ 4096 ∧
  (p.inputs.schema.rows.map (·.count)).sum ≤ 4096 ∧
  0 < p.plan.entries.length ∧ p.plan.entries.length ≤ 4096 ∧
  (∀ e ∈ p.plan.entries, 0 < e.count ∧ e.count ≤ 4096) ∧
  (∀ r ∈ p.inputs.schema.rows, NativeSchemaBinding.NameValid r.name ∧
    asciiBytes (text r.name) = r.name)
instance (p) : Decidable (Small p) := by unfold Small; infer_instance

def LayoutChecks (p : NativeShardPlanBinding.Bound) (ls : List Location) : Prop :=
  ls.map Location.global = List.range p.inputs.schema.total ∧
  (ls.map Location.label).Pairwise (· < ·) ∧
  (∀ l ∈ ls, validIdentifier l.label = true) ∧
  p.plan.entries.map (·.ordinal) = List.range p.plan.entries.length ∧
  p.plan.entries.flatMap (fun e => (List.range e.count).map (e.start + ·)) =
    List.range p.inputs.schema.total ∧
  (∀ e ∈ p.plan.entries, ∀ i ∈ List.range e.count,
    ls[e.start+i]? = some ⟨e.name,e.offset+i,e.start+i,coordinate e.name (e.offset+i)⟩)
instance (p ls) : Decidable (LayoutChecks p ls) := by unfold LayoutChecks; infer_instance

structure Layout where
  source : NativeShardPlanBinding.Bound
  positions : List Location
  deriving DecidableEq, Repr
def Layout.coordinates (l : Layout) := l.positions.map Location.label
def Layout.shards (l : Layout) := l.source.plan.entries.map shard

def construct (p : NativeShardPlanBinding.Bound) : Option Layout :=
  if Small p then
    let ls := locations p.inputs.schema
    if LayoutChecks p ls then some ⟨p,ls⟩ else none
  else none

theorem constructed {p l} (h : construct p = some l) :
    l.source = p ∧ l.positions = locations p.inputs.schema ∧ Small p ∧ LayoutChecks p l.positions := by
  unfold construct at h
  split at h <;> try contradiction
  dsimp only at h
  split at h <;> try contradiction
  cases Option.some.inj h
  exact ⟨rfl,rfl,by assumption,by assumption⟩

theorem constructFromChecks {p} (small : Small p) (checks : LayoutChecks p (locations p.inputs.schema)) :
    construct p = some ⟨p,locations p.inputs.schema⟩ := by simp [construct,small,checks]

theorem exactCoordinate {p l} (h : construct p = some l) {e}
    (member : e ∈ p.plan.entries) {i : Nat} (within : i < e.count) :
    l.positions[e.start+i]? = some ⟨e.name,e.offset+i,e.start+i,coordinate e.name (e.offset+i)⟩ :=
  (constructed h).2.2.2.2.2.2.2.2 e member i (List.mem_range.mpr within)

theorem originalLocation {p l} (h : construct p = some l) {v} (member : v ∈ l.positions) :
    ∃ r ∈ p.inputs.schema.rows, ∃ i < r.count,
      v = ⟨r.name,i,r.start+i,coordinate r.name i⟩ := by
  rw [(constructed h).2.1] at member
  exact completeLocation member

theorem exactPartition {p l} (h : construct p = some l) :
    l.shards = p.plan.entries.map shard ∧
    l.shards.flatMap (fun s => (List.range s.length).map (s.offset + ·)) =
      List.range p.inputs.schema.total := by
  have src := constructed h
  refine ⟨by simp [Layout.shards,src.1],?_⟩
  simpa [Layout.shards,src.1,List.flatMap_map,shard] using src.2.2.2.2.2.2.2.1

theorem metadataRetained {p l} (h : construct p = some l) :
    l.source.inputs.schema = p.inputs.schema ∧ l.source.plan = p.plan := by
  rw [(constructed h).1]; exact ⟨rfl,rfl⟩

theorem bytesNotRenamed {p l} (h : construct p = some l) {r} (member : r ∈ p.inputs.schema.rows) :
    asciiBytes (text r.name) = r.name := (constructed h).2.2.1.2.2.2.2.2.2 r member |>.2

end DeltaReduce.NativeVectorLayout
