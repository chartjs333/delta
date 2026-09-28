import DeltaReduce.NativeRootCorpus
import DeltaReduce.NativeIscProjection

/-! Original ROOT and computed leaf corpus share complete source parents, not
just their identifiers. The full ISC input corpus is checked separately from
the eligible arithmetic inputs; finalized leaves need no proposed vote. -/
namespace DeltaReduce.NativeRootParents
open NativeBinding NativeEarlySource NativeRootSource

section Original
variable {codec store trust anchor} (binding : Binding codec trust anchor store)
    {adapter : HashAdapter codec} {policy state vote facts}
    (loaded : Loaded adapter.sha256 policy state vote facts) (root : Root loaded.original)
    {config proof profile permission inputs}
    (checked : NativeRootCorpus.Checked binding loaded root config proof profile permission inputs)

theorem samePlanSection : checked.image.vector.source.plan.members.plans =
    NativePlanningSource.planSection loaded.original := by
  have v := (NativeRootCorpus.computed binding loaded root checked.executed).vector
  have q := NativePlanQCorpus.boundSource (NativeVectorContext.boundSource v).1
  have c := NativePlanCoefficients.boundSource q.1
  have m := NativePlanMembers.preparedSource c.members
  obtain ⟨tree,p,s,hp,hs,src⟩ := NativePlanSection.preparedSource m.plans
  obtain ⟨ot,op⟩ := (loadedOriginal loaded).policy
  have peq := congrArg Prod.snd (Option.some.inj (hp.symm.trans op))
  have seq := Option.some.inj (hs.symm.trans (loadedOriginal loaded).state)
  dsimp only at peq
  subst p; subst s
  exact Option.some.inj ((NativePlanSection.fromComponents src).symm.trans
    (NativePlanningSource.sections loaded).1)

theorem samePlan : NativeVectorAuthority.plan checked.image.vector = root.original.plan := by
  have v := (NativeRootCorpus.computed binding loaded root checked.executed).vector
  have q := NativePlanQCorpus.boundSource (NativeVectorContext.boundSource v).1
  have c := NativePlanCoefficients.boundSource q.1
  have m := NativePlanMembers.preparedSource c.members
  have found := m.edge
  rw [samePlanSection binding loaded root checked] at found
  have original := (NativeAggregateLineage.checkedSource (NativeRootSource.checked loaded root)).plan
  exact Option.some.inj (found.symm.trans original)

theorem planChecked :
    NativePlanLineage.check adapter.sha256 .finalized
      (NativePlanSection.expected loaded.original.policy loaded.original.state
        (NativePlanningSource.planSection loaded.original).eligibility)
      loaded.original.policy.validators
      (NativePlanningSource.ecSection loaded.original).norms.isc.certificates
      (NativePlanningSource.ecSection loaded.original).norms.isc.finalized
      (NativePlanningSource.ecSection loaded.original).finalized
      (NativePlanningSource.planSection loaded.original).required
      (NativePlanningSource.ecSection loaded.original).certificates
      (NativePlanningSource.ecSection loaded.original).seeds root.original.plan.source = some root.original.plan := by
  have found := (NativeAggregateLineage.checkedSource (NativeRootSource.checked loaded root)).plan
  exact NativePlanSection.certificateChecked (NativePlanningSource.sections loaded).1
    (List.mem_of_find?_eq_some found)

include checked in
theorem sameIsc : root.original.parent = root.original.plan.parent := by
  have original := NativeAggregateLineage.checkedSource (NativeRootSource.checked loaded root)
  have plan := NativePlanLineage.checkedSource (planChecked loaded root)
  have checks := (NativeRootCorpus.computed binding loaded root checked.executed).parents
  have key := checks.2.1
  rw [samePlan binding loaded root checked] at key
  have nativeKey := plan.2.2.2.2.2.2.1.2.2.2.1
  have found := original.parent
  rw [key,← nativeKey] at found
  exact Option.some.inj (found.symm.trans plan.2.2.1)

include checked in
theorem sameEc : root.original.ec = root.original.plan.ec := by
  have original := NativeAggregateLineage.checkedSource (NativeRootSource.checked loaded root)
  have plan := NativePlanLineage.checkedSource (planChecked loaded root)
  have key := (NativeRootCorpus.computed binding loaded root checked.executed).parents.2.2.1
  rw [samePlan binding loaded root checked] at key
  have nativeKey := plan.2.2.2.2.2.2.1.2.2.2.2.1
  have found := original.ec
  rw [key,← nativeKey] at found
  exact Option.some.inj (found.symm.trans plan.2.2.2.1)

include checked in
theorem crossParents : NativePlanMembers.CrossParents root.original.plan := by
  have v := (NativeRootCorpus.computed binding loaded root checked.executed).vector
  have q := NativePlanQCorpus.boundSource (NativeVectorContext.boundSource v).1
  have c := NativePlanCoefficients.boundSource q.1
  have m := NativePlanMembers.preparedSource c.members
  have parents := (NativePlanMembers.derivedSource m.rows).parents
  change NativePlanMembers.CrossParents (NativeVectorAuthority.plan checked.image.vector) at parents
  rw [samePlan binding loaded root checked] at parents
  exact parents

include checked in
theorem sameEcIsc : root.original.plan.parent = root.original.plan.ec.parent := by
  have plan := NativePlanLineage.checkedSource (planChecked loaded root)
  have ec := NativeEligibilityLineage.checkedSource
    (NativePlanSection.checkedParents (NativePlanningSource.sections loaded).1 (planChecked loaded root)).2.1
  have fields := crossParents binding loaded root checked
  have fp := plan.2.2.1
  have fe := ec.2.2.1
  rw [fields.2.2.2.2.1] at fp
  rw [fields.2.2.2.2.2.1] at fe
  exact Option.some.inj (fp.symm.trans fe)

include checked in
theorem sameEcSeed : root.original.plan.seed = root.original.plan.ec.seed := by
  have plan := NativePlanLineage.checkedSource (planChecked loaded root)
  have ec := NativeEligibilityLineage.checkedSource
    (NativePlanSection.checkedParents (NativePlanningSource.sections loaded).1 (planChecked loaded root)).2.1
  have fields := crossParents binding loaded root checked
  have fp := plan.2.2.2.2.1
  have fe := ec.2.2.2.2.1
  rw [fields.2.2.2.2.2.2.2.2.2.1] at fp
  rw [fields.2.2.2.2.2.2.2.2.2.2.1] at fe
  exact Option.some.inj (fp.symm.trans fe)

structure Complete (allInputs : List NativeAvailableQ.Input) where
  image : NativeIscProjection.Image
  executed : NativeIscProjection.check adapter.sha256 codec store checked.image.vector
    permission allInputs = some image
  frame : NativeIscProjection.FrameChecks binding checked.image.corpus.frame image

def complete (allInputs : List NativeAvailableQ.Input) :
    Option (Complete binding loaded root checked allInputs) := do
  match ran : NativeIscProjection.check adapter.sha256 codec store checked.image.vector permission allInputs with
  | none => none
  | some image =>
    if frame : NativeIscProjection.FrameChecks binding checked.image.corpus.frame image then
      some ⟨image,ran,frame⟩ else none

variable {allInputs} (full : Complete binding loaded root checked allInputs)

theorem everyOriginalTuple : full.image.rows.map (fun r => r.source.member.input) =
    root.original.parent.certificate.body.tuples := by
  have src := NativeIscProjection.constructed (NativeIscProjection.checked full.executed).1
  have originals := (NativeIscCorpus.everyOriginalMember src.corpus).1
  rw [samePlan binding loaded root checked,← sameIsc binding loaded root checked] at originals
  rw [← originals,← NativeIscProjection.everyRow src.rows,List.map_map]
  rfl

theorem everyOriginalEligibility : full.image.rows.map (fun r => r.source.member.eligibility) =
    root.original.ec.certificate.common.entries := by
  have src := NativeIscProjection.constructed (NativeIscProjection.checked full.executed).1
  have originals := (NativeIscCorpus.everyOriginalMember src.corpus).2
  rw [samePlan binding loaded root checked,← sameEc binding loaded root checked] at originals
  rw [← originals,← NativeIscProjection.everyRow src.rows,List.map_map]
  rfl

theorem originalTupleAt {index : Nat} {row}
    (atIndex : full.image.rows[index]? = some row) :
    root.original.parent.certificate.body.tuples[index]? = some row.source.member.input := by
  rw [← everyOriginalTuple binding loaded root checked full,List.getElem?_map,atIndex]; rfl

theorem exactCommitments : checked.image.corpus.frame.commitments =
    full.image.rows.map NativeIscProjection.commitment := full.frame.2.2.2.2.1

theorem originalCommitmentAt {index : Nat} {row}
    (atIndex : full.image.rows[index]? = some row) :
    checked.image.corpus.frame.commitments[index]? = some (NativeIscProjection.commitment row) := by
  rw [exactCommitments binding loaded root checked full,List.getElem?_map,atIndex]; rfl

theorem iscSource : Resolves codec store binding.authority.isc full.image.isc.raw
    (.isc checked.image.corpus.frame.members checked.image.corpus.frame.commitments) := by
  rw [full.frame.2.1,full.frame.2.2.2.1,full.frame.2.2.2.2.1]
  exact NativeIscProjection.iscResolved full.executed

theorem ecSource : Resolves codec store binding.authority.ec full.image.ec.raw
    (.ec checked.image.corpus.frame.ecIsc checked.image.corpus.frame.eligible) := by
  rw [full.frame.2.2.1,full.frame.2.2.2.2.2.1,full.frame.2.2.2.2.2.2]
  exact NativeIscProjection.ecResolved full.executed

theorem missingArtifactRejects {out a}
    (built : NativeIscProjection.construct adapter.sha256 codec.hash checked.image.vector permission allInputs = some out)
    (member : a ∈ NativeIscProjection.artifacts out) (absent : store a.ref.id = none) :
    complete binding loaded root checked allInputs = none := by
  have rejected := NativeIscProjection.unavailableRejected built member absent
  unfold complete
  split
  · rfl
  · rename_i image ran
    rw [rejected] at ran
    contradiction

end Original
end DeltaReduce.NativeRootParents
