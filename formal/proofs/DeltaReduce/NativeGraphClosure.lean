import DeltaReduce.ArithmeticBinding

/-! Executable finite-depth completeness over the actual decoded store.
Fuel bounds path depth, not total graph work or concrete decoder resources.
No supplied graph-completeness proposition or approved-body table is consumed. -/
namespace DeltaReduce.NativeGraphClosure
open NativeBinding

def refBound (r : Ref) : Bool :=
  r.id.length == 32 && 0 < r.length && r.length ≤ 4194304

def check (codec : Codec) (store : Store) : Nat → Ref → Bool
  | 0, _ => false
  | fuel + 1, ref =>
    if refBound ref then
      match loadPayload codec store ref with
      | none => false
      | some p => p.payload.refs.all (check codec store fuel)
    else false

theorem checkedNode {codec store fuel ref}
    (h : check codec store (fuel + 1) ref = true) :
    refBound ref = true ∧ ∃ p, loadPayload codec store ref = some p ∧
      ∀ child ∈ p.payload.refs, check codec store fuel child = true := by
  unfold check at h
  split at h
  next valid =>
    split at h
    next => contradiction
    next p loaded => exact ⟨valid,p,loaded,by simpa only [List.all_eq_true] using h⟩
  next => contradiction

theorem complete {codec store fuel ref} (h : check codec store fuel ref = true) :
    Complete codec store ref := by
  induction fuel generalizing ref with
  | zero => cases h
  | succ fuel ih =>
    obtain ⟨_,p,_,children⟩ := checkedNode h
    exact .node p.resolved (fun _ child atPosition =>
      ih (children child (List.mem_of_getElem? atPosition)))

theorem bounded {codec store fuel ref} (h : check codec store fuel ref = true) :
    ref.id.length = 32 ∧ 0 < ref.length ∧ ref.length ≤ 4194304 := by
  cases fuel with
  | zero => cases h
  | succ fuel => simpa [refBound,and_assoc] using (checkedNode h).1

theorem zeroRejected (codec store ref) : check codec store 0 ref = false := rfl

theorem missingRejected {codec store ref} (missing : store ref.id = none) (fuel : Nat) :
    check codec store fuel ref = false := by
  have bad : loadPayload codec store ref = none := by
    unfold loadPayload
    split
    · rfl
    · rename_i bytes found
      rw [missing] at found
      contradiction
  cases fuel <;> simp [check,bad]

theorem badRefRejected {codec store ref} (bad : refBound ref = false) (fuel : Nat) :
    check codec store fuel ref = false := by
  cases fuel <;> simp [check,bad]

theorem invalidPayloadRejected {codec store ref} (bad : loadPayload codec store ref = none) (fuel : Nat) :
    check codec store fuel ref = false := by
  cases fuel <;> simp [check,bad]

theorem childChecked {codec store fuel ref p child}
    (loaded : loadPayload codec store ref = some p) (member : child ∈ p.payload.refs)
    (h : check codec store (fuel + 1) ref = true) : check codec store fuel child = true := by
  obtain ⟨_,other,found,children⟩ := checkedNode h
  cases Option.some.inj (loaded.symm.trans found)
  exact children child member

theorem missingChildRejected {codec store fuel ref p child}
    (loaded : loadPayload codec store ref = some p) (member : child ∈ p.payload.refs)
    (missing : store child.id = none) : check codec store (fuel + 1) ref = false := by
  apply Bool.eq_false_iff.mpr
  intro accepted
  have childOk := childChecked loaded member accepted
  rw [missingRejected missing] at childOk
  contradiction

theorem orderedWalk {codec store fuel ref p index child}
    (loaded : loadPayload codec store ref = some p)
    (atPosition : p.payload.refs[index]? = some child)
    (h : check codec store (fuel + 1) ref = true) :
    ∃ bytes payload, Walk codec store ref [index] bytes payload := by
  have closed := complete (childChecked loaded (List.mem_of_getElem? atPosition) h)
  cases closed with
  | node resolved _ => exact ⟨_,_,.step p.resolved atPosition (.here resolved)⟩

end DeltaReduce.NativeGraphClosure
