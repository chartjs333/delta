import DeltaReduce.NativeVectorAuthority

/-! Finalized certificates carry no proposed-vote context. Preserve their
original empty context while checking the arithmetic projection's parent and
denominator fields. These are projection checks, not native admission rules. -/
namespace DeltaReduce.NativeFinalizedAssignment
open NativeBinding

def Fields (context : NativeInputSetBody.Context) (isc ec plan : Bytes)
    (denominator : Int) (e : NativeParameterLineage.Edge) : Prop :=
  e.voteContext = [] ∧ e.certificate.common.context = context ∧
  e.certificate.common.plan = plan ∧ e.certificate.common.isc = isc ∧
  e.certificate.common.ec = ec ∧ (e.certificate.common.denominator : Int) = denominator
instance (context isc ec plan denominator e) : Decidable (Fields context isc ec plan denominator e) := by
  unfold Fields; infer_instance

def Checks (b : NativeVectorContext.Bound) (a : Assignment) (e : NativeParameterLineage.Edge) : Prop :=
  Fields (NativeVectorAuthority.plan b).certificate.common.context
    (NativeVectorAuthority.plan b).parent.qcId (NativeVectorAuthority.plan b).ec.id
    (NativeVectorAuthority.plan b).id a.denominator e
instance (b a e) : Decidable (Checks b a e) := by unfold Checks; infer_instance

theorem decodedContext {committee source certificate context}
    (h : NativeParameterLineage.decode .finalized committee source = some (certificate,context)) :
    context = [] := by
  simp only [NativeParameterLineage.decode,bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,_,last⟩ := h
  exact (Prod.mk.inj (Option.some.inj last)).2.symm

theorem originalContext {sha expected committee parents fi fe fp keys ecs plans source e}
    (h : NativeParameterLineage.check sha .finalized expected committee parents fi fe fp keys ecs plans source = some e) :
    e.voteContext = [] := decodedContext (NativeParameterLineage.checkedSource h).decoded

/-- Regression: the former corpus predicate cannot hold for ANY genuinely
decoded finalized certificate, regardless of the projected assignment. -/
theorem proposedPredicateImpossible {sha expected committee parents fi fe fp keys ecs plans source e}
    (h : NativeParameterLineage.check sha .finalized expected committee parents fi fe fp keys ecs plans source = some e)
    (b : NativeVectorContext.Bound) (a : Assignment) :
    ¬ NativeVectorAuthority.AssignmentChecks b a e := by
  intro bad
  exact bad.2.1 (originalContext h)

theorem fieldsFromComponents {context isc ec plan denominator e}
    (empty : e.voteContext = []) (ctx : e.certificate.common.context = context)
    (hp : e.certificate.common.plan = plan) (hi : e.certificate.common.isc = isc)
    (he : e.certificate.common.ec = ec) (hd : (e.certificate.common.denominator : Int) = denominator) :
    Fields context isc ec plan denominator e := ⟨empty,ctx,hp,hi,he,hd⟩

theorem noInventedVoteContext {b a e} (h : Checks b a e) : e.voteContext = [] := h.1

theorem commonFields {b a e} (h : Checks b a e) :
    e.certificate.common.context = (NativeVectorAuthority.plan b).certificate.common.context ∧
    e.certificate.common.plan = (NativeVectorAuthority.plan b).id ∧
    e.certificate.common.isc = (NativeVectorAuthority.plan b).parent.qcId ∧
    e.certificate.common.ec = (NativeVectorAuthority.plan b).ec.id ∧
    (e.certificate.common.denominator : Int) = a.denominator := h.2

theorem proposedContextIrrelevant (b : NativeVectorContext.Bound) (a : Assignment)
    (e : NativeParameterLineage.Edge) (context : String) :
    Checks b {a with context := context} e ↔ Checks b a e := Iff.rfl

theorem nonemptyRejected {context isc ec plan denominator e} (h : e.voteContext ≠ []) :
    ¬ Fields context isc ec plan denominator e := fun good => h good.1

theorem changedDenominatorRejected {context isc ec plan denominator e}
    (h : (e.certificate.common.denominator : Int) ≠ denominator) :
    ¬ Fields context isc ec plan denominator e := fun good => h good.2.2.2.2.2

end DeltaReduce.NativeFinalizedAssignment
