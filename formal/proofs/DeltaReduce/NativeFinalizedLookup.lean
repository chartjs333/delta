import DeltaReduce.NativeFailureSource

/-! Ordered resolution of complete original certificate IDs. Ambiguous or
missing payloads reject; output positions and original typed objects remain. -/
namespace DeltaReduce.NativeFinalizedLookup
open NativeBinding
variable {α : Type} (key : α → Bytes)

def one (available : List α) (id : Bytes) : Option α :=
  match available.filter (fun row => key row == id) with
  | [row] => some row
  | _ => none

def all (available : List α) : List Bytes → Option (List α)
  | [] => some []
  | id::ids => do
    let row ← one key available id
    let rows ← all available ids
    some (row::rows)

theorem singleton {available id row} (h : one key available id = some row) :
    available.filter (fun r => key r == id) = [row] := by
  unfold one at h; split at h <;> try contradiction
  cases Option.some.inj h; assumption

theorem original {available id row} (h : one key available id = some row) : row ∈ available ∧ key row = id := by
  have mem : row ∈ available.filter (fun r => key r == id) := by rw [singleton key h]; simp
  have pair := List.mem_filter.mp mem
  exact ⟨pair.1,by simpa using pair.2⟩

theorem unique {available id row} (h : one key available id = some row) {other}
    (mem : other ∈ available) (same : key other = id) : other = row := by
  have hm : other ∈ available.filter (fun r => key r == id) := List.mem_filter.mpr ⟨mem,by simpa using same⟩
  simpa only [singleton key h,List.mem_singleton] using hm

theorem entireOrder {available ids rows} (h : all key available ids = some rows) : rows.map key = ids := by
  induction ids generalizing rows with
  | nil => cases Option.some.inj h; rfl
  | cons id ids ih =>
    simp only [all,bind,Option.bind_eq_some_iff] at h
    obtain ⟨row,hr,rest,ht,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(original key hr).2,ih ht]

theorem each {available ids rows} (h : all key available ids = some rows) :
    ∀ row ∈ rows, row ∈ available ∧ one key available (key row) = some row := by
  induction ids generalizing rows with
  | nil => cases Option.some.inj h; simp
  | cons id ids ih =>
    simp only [all,bind,Option.bind_eq_some_iff] at h
    obtain ⟨row,hr,rest,ht,last⟩ := h
    cases Option.some.inj last
    intro found member
    rcases List.mem_cons.mp member with rfl | member
    · exact ⟨(original key hr).1,by rw [(original key hr).2]; exact hr⟩
    · exact ih ht found member

theorem atPosition {available ids rows} (h : all key available ids = some rows) {index : Nat} {row}
    (atRow : rows[index]? = some row) : ids[index]? = some (key row) ∧ one key available (key row) = some row := by
  refine ⟨?_,(each key h row (List.mem_of_getElem? atRow)).2⟩
  rw [← entireOrder key h,List.getElem?_map,atRow]; rfl

theorem count {available ids rows} (h : all key available ids = some rows) : rows.length = ids.length := by
  simpa only [List.length_map] using congrArg List.length (entireOrder key h)

theorem missing {available id} (absent : available.filter (fun row => key row == id) = []) :
    one key available id = none := by simp only [one,absent]

theorem ambiguous {available id} (bad : 1 < (available.filter (fun row => key row == id)).length) :
    one key available id = none := by
  unfold one; split <;> try rfl
  rename_i row found; rw [found] at bad; simp at bad

theorem noInvented {available ids rows} (h : all key available ids = some rows) {row}
    (absent : row ∉ available) : row ∉ rows := fun mem => absent (each key h row mem).1

end DeltaReduce.NativeFinalizedLookup
