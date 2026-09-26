import DeltaReduce.NativeStateBytes
import DeltaReduce.NativePolicyCodec

/-! The certificate content_id macro bounds canonical JSON, separately from
policy wire size. The lower-level domain hash remains unbounded. -/
namespace DeltaReduce.NativeContractSize
open NativeReceiptBytes

def maxBytes : Nat := 4 * 1024 * 1024

def contentId (sha : Bytes → Bytes) (domain raw : Bytes) : Option Bytes :=
  if raw.length ≤ maxBytes then NativeStateBytes.contentId sha domain raw else none

theorem accepted {sha domain raw id} (h : contentId sha domain raw = some id) :
    raw.length ≤ maxBytes ∧ NativeStateBytes.contentId sha domain raw = some id := by
  unfold contentId at h
  split at h <;> try contradiction
  exact ⟨by assumption,h⟩

theorem fromComponents {sha domain raw id} (bound : raw.length ≤ maxBytes)
    (hashed : NativeStateBytes.contentId sha domain raw = some id) :
    contentId sha domain raw = some id := by simp only [contentId,if_pos bound,hashed]

theorem oversized {sha domain raw} (h : maxBytes < raw.length) :
    contentId sha domain raw = none := by simp [contentId,Nat.not_le.mpr h]

theorem emptyDigest (domain raw) : contentId (fun _ => []) domain raw = none := by
  unfold contentId
  split <;> simp [NativeStateBytes.contentId]

-- Original policy source and scope tag travel with each computed payload.
-- Expected is absent for synthetic proposed-certificate views, whose section
-- identity is the separate vote-body hash. Finalized rows retain their QC ID.
structure Row where
  scope : String
  source : NativePolicyCodec.Value
  domain : Bytes
  payload : Bytes
  expected : Option Bytes
  deriving Repr

structure Checked where
  row : Row
  id : Bytes
  deriving Repr

def check (sha : Bytes → Bytes) (row : Row) : Option Checked := do
  let id ← contentId sha row.domain row.payload
  if row.expected = none ∨ row.expected = some id then some ⟨row,id⟩ else none

theorem checkedSource {sha row out} (h : check sha row = some out) :
    out.row = row ∧ row.payload.length ≤ maxBytes ∧
    NativeStateBytes.contentId sha row.domain row.payload = some out.id ∧
    (row.expected = none ∨ row.expected = some out.id) := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨id,hi,last⟩ := h
  split at last <;> try contradiction
  rename_i identity
  cases Option.some.inj last
  exact ⟨rfl,(accepted hi).1,(accepted hi).2,identity⟩

theorem checkFromComponents {sha row id}
    (bound : row.payload.length ≤ maxBytes)
    (hashed : NativeStateBytes.contentId sha row.domain row.payload = some id)
    (identity : row.expected = none ∨ row.expected = some id) :
    check sha row = some ⟨row,id⟩ := by
  simp only [check,fromComponents bound hashed,bind,Option.bind,if_pos identity]

theorem checkOversized {sha row} (h : maxBytes < row.payload.length) :
    check sha row = none := by simp only [check,oversized h,bind,Option.bind]

theorem wrongIdentity {sha row id} (hashed : contentId sha row.domain row.payload = some id)
    (wrong : row.expected ≠ none ∧ row.expected ≠ some id) : check sha row = none := by
  simp [check,hashed,wrong.1,wrong.2]

def checkAll (sha : Bytes → Bytes) : List Row → Option (List Checked)
  | [] => some []
  | row::rows => do
    let out ← check sha row
    let rest ← checkAll sha rows
    some (out::rest)

theorem allSources {sha rows outs} (h : checkAll sha rows = some outs) :
    outs.map Checked.row = rows := by
  induction rows generalizing outs with
  | nil => simp [checkAll] at h; subst outs; rfl
  | cons row rows ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨out,ho,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource ho).1,ih hr]

theorem allChecked {sha rows outs} (h : checkAll sha rows = some outs)
    (out : Checked) (mem : out ∈ outs) : check sha out.row = some out := by
  induction rows generalizing outs with
  | nil => simp [checkAll] at h; subst outs; contradiction
  | cons row rows ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨first,hf,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with eq | tail
    · subst out; simpa only [(checkedSource hf).1] using hf
    · exact ih hr tail

theorem allBounds {sha rows outs} (h : checkAll sha rows = some outs)
    (row : Row) (mem : row ∈ rows) : row.payload.length ≤ maxBytes := by
  rw [← allSources h] at mem
  obtain ⟨out,ho,eq⟩ := List.mem_map.mp mem
  subst row
  exact (checkedSource (allChecked h out ho)).2.1

theorem exactCount {sha rows outs} (h : checkAll sha rows = some outs) :
    outs.length = rows.length := by simpa using congrArg List.length (allSources h)

theorem exactPosition {sha rows outs} {i : Nat} {out : Checked} (h : checkAll sha rows = some outs)
    (atIndex : outs[i]? = some out) : rows[i]? = some out.row := by
  rw [← allSources h]
  simp only [List.getElem?_map,atIndex,Option.map_some]

theorem oversizedListRejected {sha rows row} (mem : row ∈ rows)
    (over : maxBytes < row.payload.length) : checkAll sha rows = none := by
  cases h : checkAll sha rows with
  | none => rfl
  | some outs => exact False.elim (Nat.not_le.mpr over (allBounds h row mem))

theorem appendFromComponents {sha a b x y}
    (ha : checkAll sha a = some x) (hb : checkAll sha b = some y) :
    checkAll sha (a ++ b) = some (x ++ y) := by
  induction a generalizing x with
  | nil => simp [checkAll] at ha; subst x; exact hb
  | cons row rows ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at ha
    obtain ⟨out,ho,rest,hr,last⟩ := ha
    cases Option.some.inj last
    simp only [List.cons_append,checkAll,ho,ih hr,bind,Option.bind]

end DeltaReduce.NativeContractSize
