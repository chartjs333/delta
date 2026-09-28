import DeltaReduce.PublicPlanningHistory

/-! Original selected VIEW/ABORT and complete failure tail at the historical
snapshot. Runtime facts, SHA and physical timeout/absence provenance remain inputs. -/
namespace DeltaReduce.NativeFailureSource
open NativeBinding NativeEarlySource NativeFailureAuthority NativeFailurePayload

def tail (x : NativeSelectedVote.Checked) := x.admitted.checked.snapshot.prior.tail

structure View (sha : Bytes → Bytes) (x : NativeSelectedVote.Checked) where
  original : ViewEntry
  computed : checkView sha x.policy x.state (tail x) x.admitted.selected.original = some original

structure Abort (sha : Bytes → Bytes) (x : NativeSelectedVote.Checked) where
  original : AbortEntry
  computed : checkAbort sha x.policy x.state (tail x) x.admitted.selected.original = some original

def loadView (sha : Bytes → Bytes) (x : NativeSelectedVote.Checked) : Option (View sha x) :=
  match h : checkView sha x.policy x.state (tail x) x.admitted.selected.original with
  | none => none | some e => some ⟨e,h⟩
def loadAbort (sha : Bytes → Bytes) (x : NativeSelectedVote.Checked) : Option (Abort sha x) :=
  match h : checkAbort sha x.policy x.state (tail x) x.admitted.selected.original with
  | none => none | some e => some ⟨e,h⟩

theorem checkedTail {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) :
    NativeFailureSection.checkTail sha loaded.original.policy loaded.original.state = some (tail loaded.original) :=
  (NativeFailureSection.checkedSource (NativeSnapshotBase.checkedSnapshot
    (NativeSelectedVote.originalByteAuthority loaded.computed).2.1).1).2

theorem viewSource {sha x} (v : View sha x) :
    NativeFailureAuthority.ViewSource sha x.policy x.state (tail x) x.admitted.selected.original v.original :=
  NativeFailureAuthority.viewSource v.computed
theorem abortSource {sha x} (a : Abort sha x) :
    NativeFailureAuthority.AbortSource sha x.policy x.state (tail x) x.admitted.selected.original a.original :=
  NativeFailureAuthority.abortSource a.computed

theorem viewOriginalRow {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (v : View sha loaded.original) :
    checkRow NativePolicySchema.fmtViewChange readView (viewId sha) v.original.row.source = some v.original.row :=
  NativeFailureAuthority.viewOriginalRow (checkedTail loaded) v.computed
theorem abortOriginalRow {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (a : Abort sha loaded.original) :
    checkRow NativePolicySchema.fmtAbortBody readAbort (abortId sha) a.original.row.source = some a.original.row ∧
    NativeFailureSection.AbortExact loaded.original.policy loaded.original.state (tail loaded.original).lineage a.original.row.body :=
  NativeFailureAuthority.abortOriginalRow (checkedTail loaded) a.computed

theorem viewSelectedIdentity {sha x} (v : View sha x) :
    v.original.row.id = x.admitted.selected.original.body ∧
    v.original.context = x.admitted.selected.original.context ∧ x.admitted.selected.original.action = 8 :=
  ⟨(NativeFailureAuthority.viewMembership v.computed).2.1,(viewSource v).common.2.2.2.2.2.1.symm,(viewSource v).action⟩
theorem abortSelectedIdentity {sha x} (a : Abort sha x) :
    a.original.row.id = x.admitted.selected.original.body ∧
    a.original.context = x.admitted.selected.original.context ∧ x.admitted.selected.original.action = 9 :=
  ⟨(NativeFailureAuthority.abortMembership a.computed).2,(abortSource a).common.2.2.2.2.2.1.symm,(abortSource a).action⟩

theorem exactTimeout {sha x} (v : View sha x) :
    v.original.observation ∈ (tail x).timeouts ∧
    v.original.observation.round = v.original.row.body.round ∧
    v.original.observation.height = x.state.height ∧ v.original.observation.view = x.state.view ∧
    v.original.row.body.toView = x.state.view+1 ∧ x.state.view < 256^8-1 :=
  ⟨(NativeFailureAuthority.viewMembership v.computed).2.2,NativeFailureAuthority.exactTimeout v.computed⟩

theorem viewNumbers {sha x} (v : View sha x) :
    v.original.row.body.round = x.policy.round ∧ v.original.row.body.height = x.state.height ∧
    v.original.row.body.fromView = x.state.view ∧ v.original.row.body.deadline = x.policy.softDeadline := by
  have h := (viewSource v).checked
  exact ⟨h.1,h.2.1,h.2.2.1,h.2.2.2.2.2.1⟩

theorem allSevenAbortLists {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (a : Abort sha loaded.original) :
    NativeFailureSection.LineageSource loaded.original.policy
      ⟨a.original.row.body.configs,a.original.row.body.inputs,a.original.row.body.eligibility,
       a.original.row.body.plans,a.original.row.body.parameters,a.original.row.body.roots,a.original.row.body.applies⟩ :=
  NativeFailureSection.completeAbortLists (checkedTail loaded) (NativeFailureAuthority.abortMembership a.computed).1

theorem noFinalizedApply {sha x} (a : Abort sha x) : (tail x).lineage.applies = [] :=
  NativeFailureAuthority.noFinalizedApply a.computed

theorem originalEnvironment {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) :
    NativeSelectedVote.Environment loaded.original.policy loaded.original.state (tail loaded.original)
      loaded.original.admitted.selected facts :=
  (NativeSelectedVote.originalByteAuthority loaded.computed).2.2.2.2.2.2.2.2

theorem viewEnabled {sha policy state vote facts} (loaded : Loaded sha policy state vote facts)
    (v : View sha loaded.original) :
    (tail loaded.original).requests = [] ∧ loaded.original.policy.softDeadline ≤ facts.tick ∧
      facts.tick < loaded.original.policy.hardDeadline := by
  have h := (originalEnvironment loaded).2.2.2.1
  simpa only [NativeSelectedVote.enabled,(viewSource v).action,ite_true] using h

theorem loadViewFromComponents {sha x} (v : View sha x) : loadView sha x = some v := by
  unfold loadView; split
  · rename_i missing; rw [v.computed] at missing; contradiction
  · rename_i e he; have same := Option.some.inj (v.computed.symm.trans he); subst e; rfl
theorem loadAbortFromComponents {sha x} (a : Abort sha x) : loadAbort sha x = some a := by
  unfold loadAbort; split
  · rename_i missing; rw [a.computed] at missing; contradiction
  · rename_i e he; have same := Option.some.inj (a.computed.symm.trans he); subst e; rfl

theorem wrongViewKind {sha x} (h : x.admitted.selected.original.action ≠ 8) : loadView sha x = none := by
  unfold loadView; split
  · rfl
  · rename_i e he; exact False.elim (h (NativeFailureAuthority.viewSource he).action)
theorem wrongAbortKind {sha x} (h : x.admitted.selected.original.action ≠ 9) : loadAbort sha x = none := by
  unfold loadAbort; split
  · rfl
  · rename_i e he; exact False.elim (h (NativeFailureAuthority.abortSource he).action)

end DeltaReduce.NativeFailureSource
