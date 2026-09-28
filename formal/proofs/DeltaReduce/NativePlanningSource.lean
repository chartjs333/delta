import DeltaReduce.PublicEarlyHistory

/-! Selected EC/APC source edges at the original historical snapshot. Executed
whole admission supplies the lineage proofs; raw edge constructors do not. -/
namespace DeltaReduce.NativePlanningSource
open NativeBinding NativeEarlySource

def ecSection (x : NativeSelectedVote.Checked) := NativeCandidateAuthority.ecSection x.admitted.checked.snapshot
def planSection (x : NativeSelectedVote.Checked) := NativeCandidateAuthority.planSection x.admitted.checked.snapshot
def ecMatches (x : NativeSelectedVote.Checked) :=
  (ecSection x).bodies.filter (fun e => e.id == x.admitted.selected.original.body)
def planMatches (x : NativeSelectedVote.Checked) :=
  (planSection x).bodies.filter (fun e => e.id == x.admitted.selected.original.body)

structure Ec (x : NativeSelectedVote.Checked) where
  original : NativeEligibilityLineage.Edge
  selected : ecMatches x = [original]
  kind : x.admitted.selected.original.action = 3
structure Plan (x : NativeSelectedVote.Checked) where
  original : NativePlanLineage.Edge
  selected : planMatches x = [original]
  kind : x.admitted.selected.original.action = 4

def loadEc (x : NativeSelectedVote.Checked) : Option (Ec x) :=
  if kind : x.admitted.selected.original.action = 3 then
    match selected : ecMatches x with
    | [e] => some ⟨e,selected,kind⟩
    | _ => none
  else none
def loadPlan (x : NativeSelectedVote.Checked) : Option (Plan x) :=
  if kind : x.admitted.selected.original.action = 4 then
    match selected : planMatches x with
    | [e] => some ⟨e,selected,kind⟩
    | _ => none
  else none

theorem singletonFind {α} {xs : List α} {p : α → Bool} {x}
    (h : xs.filter p = [x]) : xs.find? p = some x := by
  induction xs with
  | nil => simp at h
  | cons y ys ih =>
    cases hp : p y with
    | false => simp only [List.filter_cons,hp,Bool.false_eq_true,↓reduceIte] at h
               simpa only [List.find?,hp,Bool.false_eq_true,↓reduceIte] using ih h
    | true => simp only [List.filter_cons,hp,↓reduceIte] at h
              have same := (List.cons.inj h).1
              subst y
              simp only [List.find?,hp]

theorem ecOriginal {x} (e : Ec x) :
    e.original ∈ (ecSection x).bodies ∧ e.original.id = x.admitted.selected.original.body := by
  have mem : e.original ∈ ecMatches x := by rw [e.selected]; simp
  have pair := List.mem_filter.mp mem
  exact ⟨pair.1,by simpa using pair.2⟩
theorem planOriginal {x} (e : Plan x) :
    e.original ∈ (planSection x).bodies ∧ e.original.id = x.admitted.selected.original.body := by
  have mem : e.original ∈ planMatches x := by rw [e.selected]; simp
  have pair := List.mem_filter.mp mem
  exact ⟨pair.1,by simpa using pair.2⟩

theorem sections {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) :
    NativePlanSection.bindSection sha loaded.original.policy loaded.original.state = some (planSection loaded.original) ∧
    NativeEligibilitySection.bindSection sha loaded.original.policy loaded.original.state = some (ecSection loaded.original) := by
  have h := NativeCandidateAuthority.sourceSections (NativeSelectedVote.originalByteAuthority loaded.computed).2.1
  exact h.2.2.2

theorem ecChecked {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (e : Ec loaded.original) :
    NativeEligibilityLineage.check sha .proposed
      (NativeEligibilitySection.expected loaded.original.policy loaded.original.state (ecSection loaded.original).norms)
      loaded.original.policy.validators (ecSection loaded.original).norms.isc.certificates
      (ecSection loaded.original).norms.isc.finalized (ecSection loaded.original).norms.norms
      (ecSection loaded.original).seeds e.original.source = some e.original :=
  NativeEligibilitySection.proposedChecked (sections loaded).2 (ecOriginal e).1

theorem planChecked {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (e : Plan loaded.original) :
    NativePlanLineage.check sha .proposed
      (NativePlanSection.expected loaded.original.policy loaded.original.state (planSection loaded.original).eligibility)
      loaded.original.policy.validators (ecSection loaded.original).norms.isc.certificates
      (ecSection loaded.original).norms.isc.finalized (ecSection loaded.original).finalized
      (planSection loaded.original).required (ecSection loaded.original).certificates
      (ecSection loaded.original).seeds e.original.source = some e.original :=
  NativePlanSection.proposedChecked (sections loaded).1 (planOriginal e).1

theorem ecParentSources {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (e : Ec loaded.original) :
    NativeIscCertificate.Source sha
      (NativeEligibilitySection.expected loaded.original.policy loaded.original.state (ecSection loaded.original).norms)
      loaded.original.policy.validators e.original.parent.source e.original.parent ∧
    NativeNormEvidence.Source sha
      (NativeEligibilitySection.expected loaded.original.policy loaded.original.state (ecSection loaded.original).norms)
      (ecSection loaded.original).norms.isc.finalized e.original.norm.source e.original.norm ∧
    NativeSeedTranscript.Source sha
      (NativeEligibilitySection.expected loaded.original.policy loaded.original.state (ecSection loaded.original).norms)
      (ecSection loaded.original).norms.isc.finalized e.original.seed.source e.original.seed :=
  NativeEligibilitySection.checkedParents (sections loaded).2 (ecChecked loaded e)

theorem planEcChecked {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (e : Plan loaded.original) :
    NativeEligibilityLineage.check sha .finalized
      (NativePlanSection.expected loaded.original.policy loaded.original.state (planSection loaded.original).eligibility)
      loaded.original.policy.validators (ecSection loaded.original).norms.isc.certificates
      (ecSection loaded.original).norms.isc.finalized (ecSection loaded.original).norms.norms
      (ecSection loaded.original).seeds e.original.ec.source = some e.original.ec :=
  (NativePlanSection.checkedParents (sections loaded).1 (planChecked loaded e)).2.1

theorem planIscAndSeedSources {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (e : Plan loaded.original) :
    NativeIscCertificate.Source sha
      (NativePlanSection.expected loaded.original.policy loaded.original.state (planSection loaded.original).eligibility)
      loaded.original.policy.validators e.original.parent.source e.original.parent ∧
    NativeSeedTranscript.Source sha
      (NativePlanSection.expected loaded.original.policy loaded.original.state (planSection loaded.original).eligibility)
      (ecSection loaded.original).norms.isc.finalized e.original.seed.source e.original.seed := by
  have h := NativePlanSection.checkedParents (sections loaded).1 (planChecked loaded e)
  exact ⟨h.1,h.2.2⟩

theorem ecOriginalAuthority {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (e : Ec loaded.original) :
    NativeCandidateAuthority.Ec sha loaded.original.admitted.checked.snapshot
      loaded.original.admitted.selected.original loaded.original.admitted.selected.parents e.original := by
  have h := (NativeCandidateAuthority.checked (loadedAuthority loaded)).2.2.2.2
  simp only [NativeCandidateAuthority.Authority,e.kind] at h
  have found := singletonFind e.selected
  simp only [ecSection] at found
  rw [found] at h
  exact h

theorem planOriginalAuthority {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (e : Plan loaded.original) :
    NativeCandidateAuthority.Plan sha loaded.original.admitted.checked.snapshot
      loaded.original.admitted.selected.original loaded.original.admitted.selected.parents e.original e.original.ec := by
  have h := (NativeCandidateAuthority.checked (loadedAuthority loaded)).2.2.2.2
  simp only [NativeCandidateAuthority.Authority,e.kind] at h
  have found := singletonFind e.selected
  simp only [planSection] at found
  rw [found] at h
  have parent := (NativePlanLineage.checkedSource (planChecked loaded e)).2.2.2.1
  simp only [ecSection] at parent
  dsimp only at h
  rw [parent] at h
  exact h

theorem planOriginalCoverage {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) (e : Plan loaded.original) :
    NativePlan.acceptedTickets e.original.ec.certificate = e.original.certificate.common.buckets.map NativePlan.Bucket.ticket ∧
    NativePlan.acceptedTickets e.original.ec.certificate = e.original.certificate.common.weights.map NativePlan.Weight.ticket := by
  have src := NativePlanLineage.checkedSource (planChecked loaded e)
  exact NativePlan.originalCoverage src.2.2.2.2.2.1.1 src.2.2.2.2.2.2.1.2.2.2.2.2.2.2

theorem ecFromComponents {x e} (selected : ecMatches x = [e]) (kind : x.admitted.selected.original.action = 3) :
    loadEc x = some ⟨e,selected,kind⟩ := by
  unfold loadEc; simp only [dif_pos kind]
  split
  · rename_i found hf
    have same : found = e := by simpa only [selected,List.cons.injEq,and_true] using hf.symm
    subst found; rfl
  · rename_i hother; simp_all
theorem planFromComponents {x e} (selected : planMatches x = [e]) (kind : x.admitted.selected.original.action = 4) :
    loadPlan x = some ⟨e,selected,kind⟩ := by
  unfold loadPlan; simp only [dif_pos kind]
  split
  · rename_i found hf
    have same : found = e := by simpa only [selected,List.cons.injEq,and_true] using hf.symm
    subst found; rfl
  · rename_i hother; simp_all

theorem ecAmbiguousRejects {x} (h : 1 < (ecMatches x).length) : loadEc x = none := by
  unfold loadEc; split <;> try rfl
  split <;> try rfl
  rename_i e he; rw [he] at h; simp at h
theorem planAmbiguousRejects {x} (h : 1 < (planMatches x).length) : loadPlan x = none := by
  unfold loadPlan; split <;> try rfl
  split <;> try rfl
  rename_i e he; rw [he] at h; simp at h

end DeltaReduce.NativePlanningSource
