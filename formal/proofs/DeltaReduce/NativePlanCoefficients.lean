import DeltaReduce.NativePlanMembers
import DeltaReduce.NativeAccumulatorBinding

/-! Final original APC alpha scaled by the specific decoded proof denominator.
No extra EC gamma multiplication, minimum-LCM substitution, native admission
equivalence, signature authority, or Q availability follows from this layer. -/
namespace DeltaReduce.NativePlanCoefficients
open NativeReceiptBytes (Bytes)
open NativePlanMembers (Row)
open NativeAccumulatorBinding (Numbers NumericValid)

def coefficient (n : Numbers) (r : Row) : Nat :=
  r.weight.numerator * (n.denominator / r.weight.denominator)
def WeightFits (n : Numbers) (r : Row) : Prop :=
  NativePlan.WeightValid r.weight ∧ r.weight.denominator ∣ n.denominator ∧
  coefficient n r ≤ n.coefficient
instance (n r) : Decidable (WeightFits n r) := by unfold WeightFits; infer_instance
def PlanFits (n : Numbers) (rows : List Row) : Prop :=
  NumericValid n ∧ rows.length ≤ n.count ∧ ∀ r ∈ rows, WeightFits n r
instance (n rows) : Decidable (PlanFits n rows) := by unfold PlanFits; infer_instance

structure Term where
  source : Row
  coefficient : Nat
  deriving DecidableEq, Repr
def terms (n : Numbers) (rows : List Row) : List Term :=
  rows.map (fun r => ⟨r,coefficient n r⟩)
def check (n : Numbers) (rows : List Row) : Option (List Term) :=
  if PlanFits n rows then some (terms n rows) else none
theorem checked {n rows ts} (h : check n rows = some ts) :
    PlanFits n rows ∧ ts = terms n rows := by
  unfold check at h; split at h <;> try contradiction
  exact ⟨by assumption,(Option.some.inj h).symm⟩
theorem sourceRows (n rows) : (terms n rows).map Term.source = rows := by
  simp [terms,List.map_map,Function.comp_def]
theorem exactCount (n rows) : (terms n rows).length = rows.length := by simp [terms]
theorem termSource {n rows t} (h : t ∈ terms n rows) :
    t.source ∈ rows ∧ t.coefficient = coefficient n t.source := by
  obtain ⟨r,hr,eq⟩ := List.mem_map.mp h
  cases eq
  exact ⟨hr,rfl⟩
theorem scaledExactly {n r} (h : WeightFits n r) :
    coefficient n r * r.weight.denominator = r.weight.numerator*n.denominator := by
  rw [coefficient,Nat.mul_assoc,Nat.div_mul_cancel h.2.1]
theorem coefficientBound {n rows t} (h : PlanFits n rows) (mem : t ∈ terms n rows) :
    t.coefficient ≤ n.coefficient := by
  have src := termSource mem
  rw [src.2]
  exact (h.2.2 _ src.1).2.2

def inDomain (domain : Bytes) (ts : List Term) : List Term :=
  ts.filter (fun t => t.source.member.input.domain == domain)
theorem domainMembership {domain ts t} : t ∈ inDomain domain ts ↔
    t ∈ ts ∧ t.source.member.input.domain = domain := by simp [inDomain]
theorem domainCount {n rows domain} (h : PlanFits n rows) :
    (inDomain domain (terms n rows)).length ≤ n.count := by
  exact (List.length_filter_le _ _).trans (by simpa [terms] using h.2.1)

theorem productFits {n rows t} (h : PlanFits n rows) (mem : t ∈ terms n rows)
    (q : Int) (hq : |q| ≤ 32767) :
    |(t.coefficient : Int)*q| ≤ (NativeAccumulatorBinding.limit n.productBits : Int) := by
  apply NativeAccumulatorBinding.everyBoundedProduct h.1 _ q _ hq
  simpa using (show (t.coefficient : Int) ≤ (n.coefficient : Int) by
    exact_mod_cast coefficientBound h mem)

open scoped BigOperators
/-- Every prefix (indeed every subset of positions) of a selected domain.
Positions preserve zero terms and repeated numeric values without collapsing. -/
theorem domainPrefixFits {n rows domain} (h : PlanFits n rows)
    (q : Fin (inDomain domain (terms n rows)).length → Int)
    (hq : ∀ i, |q i| ≤ 32767)
    (positions : Finset (Fin (inDomain domain (terms n rows)).length)) :
    |∑ i ∈ positions, (((inDomain domain (terms n rows)).get i).coefficient : Int)*q i| ≤
      (NativeAccumulatorBinding.limit n.accumulatorBits : Int) := by
  apply NativeAccumulatorBinding.everyBoundedPrefix h.1 Finset.univ
    (fun i => (((inDomain domain (terms n rows)).get i).coefficient : Int)) q
    (by simpa using domainCount (domain := domain) h) _ _ positions (Finset.subset_univ _)
  · intro i _
    have mem := (domainMembership.mp (List.get_mem _ i)).1
    have bound := coefficientBound h mem
    simpa using (show (((inDomain domain (terms n rows)).get i).coefficient : Int) ≤
      (n.coefficient : Int) by exact_mod_cast bound)
  · intro i _; exact hq i

/-- Same raw digest adapter as the native certificate parser. Its implementation
and provenance are UNVERIFIED; malformed digest widths cannot form an ID. -/
def contentHash (sha : Bytes → Bytes) (raw : Bytes) : Bytes :=
  let digest := sha raw
  if digest.length = 32 then NativeVoteBytes.ascii "sha256:" ++ NativeVoteBytes.hexBytes digest else []

def ConfigLinks (m : NativePlanMembers.Bound) (a : NativeAccumulatorBinding.Bound) : Prop :=
  a.config.schema = m.edge.certificate.common.context.schema ∧
  a.config.base = m.edge.certificate.common.context.config
instance (m a) : Decidable (ConfigLinks m a) := by unfold ConfigLinks; infer_instance
structure Bound where
  members : NativePlanMembers.Bound
  accumulator : NativeAccumulatorBinding.Bound
  coefficients : List Term

def bind (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes) :
    Option Bound := do
  let members ← NativePlanMembers.prepare sha policyRaw stateRaw apcId
  let a ← NativeAccumulatorBinding.load (contentHash sha) configRaw proofRaw profileRaw
    members.edge.certificate.common.accumulator
  if ConfigLinks members a then
    let ts ← check a.numbers members.rows
    some ⟨members,a,ts⟩
  else none

structure Source (sha : Bytes → Bytes)
    (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes) (b : Bound) : Prop where
  members : NativePlanMembers.prepare sha policyRaw stateRaw apcId = some b.members
  accumulator : NativeAccumulatorBinding.load (contentHash sha) configRaw proofRaw profileRaw
    b.members.edge.certificate.common.accumulator = some b.accumulator
  links : ConfigLinks b.members b.accumulator
  coefficients : check b.accumulator.numbers b.members.rows = some b.coefficients

theorem boundSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b) :
    Source sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b := by
  simp only [bind,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨m,hm,a,ha,last⟩ := h
  split at last <;> try contradiction
  rename_i links
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨ts,ht,last⟩ := last
  cases Option.some.inj last
  exact ⟨hm,ha,links,ht⟩

theorem bindFromSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b}
    (h : Source sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b) :
    bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b := by
  simp only [bind,h.members,h.accumulator,Bind.bind,Option.bind,if_pos h.links,h.coefficients]

theorem completeSourceRows {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b) :
    b.coefficients.map Term.source = b.members.rows ∧
    b.coefficients.length = b.members.rows.length ∧
    b.members.rows.map Row.weight = b.members.edge.certificate.common.weights ∧
    b.members.rows.map Row.bucket = b.members.edge.certificate.common.buckets := by
  have src := boundSource h
  have numeric := checked src.coefficients
  have members := NativePlanMembers.fullOriginalCoverage (NativePlanMembers.preparedSource src.members).rows
  exact ⟨numeric.2 ▸ sourceRows _ _,numeric.2 ▸ exactCount _ _,members.1,members.2.1⟩

theorem actualBounds {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b) :
    NativeAccumulatorBinding.NumericSource b.accumulator.proof b.accumulator.numbers ∧
    PlanFits b.accumulator.numbers b.members.rows := by
  have src := boundSource h
  exact ⟨NativeAccumulatorBinding.numbersSource (NativeAccumulatorBinding.loadedSource src.accumulator).numbers,
    (checked src.coefficients).1⟩

theorem boundDomainPrefixFits {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b)
    (domain : Bytes) (q : Fin (inDomain domain b.coefficients).length → Int)
    (hq : ∀ i, |q i| ≤ 32767)
    (positions : Finset (Fin (inDomain domain b.coefficients).length)) :
    |∑ i ∈ positions, (((inDomain domain b.coefficients).get i).coefficient : Int)*q i| ≤
      (NativeAccumulatorBinding.limit b.accumulator.numbers.accumulatorBits : Int) := by
  have hc := checked (boundSource h).coefficients
  revert q hq positions
  rw [hc.2]
  exact fun q hq positions => domainPrefixFits hc.1 q hq positions

theorem orderedPosition (n : Numbers) (rows : List Row) (i : Nat) :
    ((terms n rows).map Term.source)[i]? = rows[i]? := congrArg (fun xs => xs[i]?) (sourceRows n rows)

theorem boundCoefficientIdentity {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b t}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b)
    (mem : t ∈ b.coefficients) :
    t.source ∈ b.members.rows ∧
    t.coefficient = t.source.weight.numerator *
      (b.accumulator.numbers.denominator / t.source.weight.denominator) ∧
    t.coefficient * t.source.weight.denominator =
      t.source.weight.numerator * b.accumulator.numbers.denominator := by
  have hc := checked (boundSource h).coefficients
  rw [hc.2] at mem
  have src := termSource mem
  exact ⟨src.1,src.2,src.2 ▸ scaledExactly (hc.1.2.2 _ src.1)⟩
end DeltaReduce.NativePlanCoefficients
