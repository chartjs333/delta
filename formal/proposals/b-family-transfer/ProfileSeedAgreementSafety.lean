import DeltaReduce.Quorum

/-! T047/T053 cross-view certificate induction, with explicit LOCAL premises.
This reuses PO-Q1. It does not assume agreement, refinement or public acceptance.
The byte/source producer join must derive HonestPrepareUnique and
CommitStatusFloor from retained intent/knowledge histories. Until that join is
proved, this factor theorem alone is NOT full protocol qualification.
-/
namespace DeltaReduce.ProfileSeedAgreementSafety
variable {Validator Value : Type*} [DecidableEq Validator]

structure Model (Validator Value : Type*) [DecidableEq Validator] where
  validators : Finset Validator
  faulty : Finset Validator
  four : validators.card = 4
  faults : faulty.card ≤ 1
  prepare : Validator → Nat → Value → Prop
  commit : Validator → Nat → Value → Prop
  status : Validator → Nat → Option (Nat × Value) → Prop
  proposal : Nat → Value → Prop

def Model.Quorum (m : Model Validator Value) (q : Finset Validator) : Prop :=
  q ⊆ m.validators ∧ 3 ≤ q.card
def Model.Prepared (m : Model Validator Value) (v : Nat) (x : Value) : Prop :=
  ∃ q, m.Quorum q ∧ ∀ a ∈ q, m.prepare a v x
def Model.Committed (m : Model Validator Value) (v : Nat) (x : Value) : Prop :=
  ∃ q, m.Quorum q ∧ ∀ a ∈ q, m.commit a v x

/-- Direct guards of a checked new-view proposal. `chosen` is the computed
highest nonempty report, not an assertion that the proposal is globally safe. -/
structure NewView (m : Model Validator Value) (v : Nat) (x : Value) where
  q : Finset Validator
  quorum : m.Quorum q
  reports : Validator → Option (Nat × Value)
  original : ∀ a ∈ q, m.status a v (reports a)
  validReport : ∀ a ∈ q, ∀ w y, reports a = some (w,y) → m.Prepared w y ∧ w < v
  chosen : Option (Nat × Value)
  noneIff : chosen = none → ∀ a ∈ q, reports a = none
  witness : ∀ w y, chosen = some (w,y) → ∃ a ∈ q, reports a = some (w,y)
  dominates : ∀ a ∈ q, ∀ w y, reports a = some (w,y) →
    ∃ u z, chosen = some (u,z) ∧ w ≤ u
  value : ∀ w y, chosen = some (w,y) → y = x

structure LocalRules (m : Model Validator Value) where
  honestPrepareUnique : ∀ a, a ∉ m.faulty → ∀ v x y,
    m.prepare a v x → m.prepare a v y → x = y
  commitPrepared : ∀ a v x, m.commit a v x → m.Prepared v x
  prepareProposal : ∀ a v x, m.prepare a v x → m.proposal v x
  newView : ∀ v x, 0 < v → m.proposal v x → NewView m v x
  /-- Local causal fact, NOT value agreement: an honest actor cannot commit an
  older view after entering a later one; its complete later STATUS must report
  a prepared view at least as high as its earlier committed intent. -/
  commitStatusFloor : ∀ a, a ∉ m.faulty → ∀ v x u report,
    v < u → m.commit a v x → m.status a u report →
    ∃ w y, report = some (w,y) ∧ v ≤ w

theorem intersection (m : Model Validator Value) {q r}
    (hq : m.Quorum q) (hr : m.Quorum r) :
    ∃ a ∈ q ∩ r, a ∉ m.faulty := by
  exact DeltaReduce.quorumIntersectionContainsHonest m.validators q r m.faulty 1
    (by simpa using m.four) hq.1 hr.1 hq.2 hr.2 m.faults

theorem sameViewPrepared {m : Model Validator Value} (rules : LocalRules m)
    {v x y} (left : m.Prepared v x) (right : m.Prepared v y) : x = y := by
  obtain ⟨q,hq,hleft⟩ := left
  obtain ⟨r,hr,hright⟩ := right
  obtain ⟨a,ha,honest⟩ := intersection m hq hr
  obtain ⟨inLeft,inRight⟩ := Finset.mem_inter.mp ha
  exact rules.honestPrepareUnique a honest v x y (hleft a inLeft) (hright a inRight)

theorem commitPrepared {m : Model Validator Value} (rules : LocalRules m)
    {v x} (committed : m.Committed v x) : m.Prepared v x := by
  obtain ⟨q,hq,hcommit⟩ := committed
  have size := hq.2
  have positive : 0 < q.card := by omega
  obtain ⟨a,ha⟩ := Finset.card_pos.mp positive
  exact rules.commitPrepared a v x (hcommit a ha)

theorem laterPreparedPredecessor {m : Model Validator Value} (rules : LocalRules m)
    {v x u y} (committed : m.Committed v x) (later : v < u)
    (prepared : m.Prepared u y) :
    ∃ w, v ≤ w ∧ w < u ∧ m.Prepared w y := by
  obtain ⟨qc,hqc,hcommit⟩ := committed
  obtain ⟨qp,hqp,hprepare⟩ := prepared
  have size := hqp.2
  have positive : 0 < qp.card := by omega
  obtain ⟨a,ha⟩ := Finset.card_pos.mp positive
  let nv := rules.newView u y (by omega) (rules.prepareProposal a u y (hprepare a ha))
  obtain ⟨b,hb,honest⟩ := intersection m hqc nv.quorum
  obtain ⟨inCommit,inStatus⟩ := Finset.mem_inter.mp hb
  obtain ⟨w,z,reported,floor⟩ := rules.commitStatusFloor b honest v x u
    (nv.reports b) later (hcommit b inCommit) (nv.original b inStatus)
  obtain ⟨highest,value,chosen,dominates⟩ := nv.dominates b inStatus w z reported
  obtain ⟨c,hc,original⟩ := nv.witness highest value chosen
  obtain ⟨cert,bound⟩ := nv.validReport c hc highest value original
  have same := nv.value highest value chosen
  subst value
  exact ⟨highest,by omega,bound,cert⟩

theorem preparedAfterCommit {m : Model Validator Value} (rules : LocalRules m)
    {v x} (committed : m.Committed v x) :
    ∀ u y, v ≤ u → m.Prepared u y → y = x := by
  intro u
  induction u using Nat.strong_induction_on with
  | h u ih =>
    intro y bound prepared
    by_cases equal : u = v
    · subst u
      exact sameViewPrepared rules prepared (commitPrepared rules committed)
    · have later : v < u := by omega
      obtain ⟨w,above,below,previous⟩ := laterPreparedPredecessor rules committed later prepared
      exact ih w below y above previous

theorem noConflictingCommitValues {m : Model Validator Value} (rules : LocalRules m)
    {v x u y} (left : m.Committed v x) (right : m.Committed u y) : x = y := by
  by_cases order : v ≤ u
  · exact (preparedAfterCommit rules left u y order (commitPrepared rules right)).symm
  · exact preparedAfterCommit rules right v x (by omega) (commitPrepared rules left)

#print axioms sameViewPrepared
#print axioms laterPreparedPredecessor
#print axioms preparedAfterCommit
#print axioms noConflictingCommitValues
end DeltaReduce.ProfileSeedAgreementSafety
