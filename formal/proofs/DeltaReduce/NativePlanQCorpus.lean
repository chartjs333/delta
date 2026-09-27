import DeltaReduce.NativeAvailableQ

/-! All eligible APC coefficients joined to complete original Q byte corpora.
No caller-supplied decoded corpus or approval flag. Primitive observations,
hash/configuration source authority and full recovery remain unproved. -/
namespace DeltaReduce.NativePlanQCorpus
open NativeReceiptBytes (Bytes)
open NativePlanCoefficients (Term)
open NativeAvailableQ (Input Permission Primitive Coverage)

def Links (p : NativePlanCoefficients.Bound) (t : Term) (i : Input)
    (q : NativeAccumulatorBinding.BoundCorpus) : Prop :=
  i.observation.commitmentTicket = t.source.member.input.ticket ∧
  i.observation.commitment = t.source.member.input.commitment ∧
  i.observation.certificate = t.source.member.input.availability ∧
  q.manifest.manifest.wire.domain = t.source.member.input.domain ∧
  q.manifest.manifest.wire.schema = p.members.edge.certificate.common.context.schema ∧
  q.manifest.manifest.wire.proof = p.members.edge.certificate.common.accumulator ∧
  q.manifest.manifest.wire.config = p.accumulator.proof.config
instance (p t i q) : Decidable (Links p t i q) := by unfold Links; infer_instance

structure Row where
  term : Term
  corpus : NativeAccumulatorBinding.BoundCorpus
  deriving DecidableEq, Repr

def loadRow (sha : Bytes → Bytes) (configRaw proofRaw profileRaw : Bytes)
    (p : NativePlanCoefficients.Bound) (permission : Permission) (t : Term) (i : Input) : Option Row := do
  let q ← NativeAvailableQ.load (NativePlanCoefficients.contentHash sha) configRaw proofRaw profileRaw i
  if Primitive permission i.observation ∧ Coverage i.observation q.manifest ∧ Links p t i q then
    some ⟨t,q⟩ else none

theorem rowSource {sha configRaw proofRaw profileRaw p permission t i row}
    (h : loadRow sha configRaw proofRaw profileRaw p permission t i = some row) :
    row.term = t ∧
    NativeAvailableQ.load (NativePlanCoefficients.contentHash sha) configRaw proofRaw profileRaw i = some row.corpus ∧
    Primitive permission i.observation ∧ Coverage i.observation row.corpus.manifest ∧ Links p t i row.corpus := by
  simp only [loadRow,bind,Option.bind_eq_some_iff] at h
  obtain ⟨q,hq,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨rfl,hq,by assumption⟩

theorem rowFromSources {sha configRaw proofRaw profileRaw p permission t i q}
    (loaded : NativeAvailableQ.load (NativePlanCoefficients.contentHash sha)
      configRaw proofRaw profileRaw i = some q)
    (primitive : Primitive permission i.observation) (coverage : Coverage i.observation q.manifest)
    (links : Links p t i q) :
    loadRow sha configRaw proofRaw profileRaw p permission t i = some ⟨t,q⟩ := by
  simp only [loadRow,loaded,bind,Option.bind]
  exact if_pos ⟨primitive,coverage,links⟩

theorem rowMismatchRejected {sha configRaw proofRaw profileRaw p permission t i q}
    (loaded : NativeAvailableQ.load (NativePlanCoefficients.contentHash sha)
      configRaw proofRaw profileRaw i = some q) (mismatch : ¬ Links p t i q) :
    loadRow sha configRaw proofRaw profileRaw p permission t i = none := by
  simp [loadRow,loaded,mismatch]

def loadRows (sha : Bytes → Bytes) (configRaw proofRaw profileRaw : Bytes)
    (p : NativePlanCoefficients.Bound) (permission : Permission) : List Term → List Input → Option (List Row)
  | [],[] => some []
  | t::ts,i::ins => do
    let row ← loadRow sha configRaw proofRaw profileRaw p permission t i
    let rest ← loadRows sha configRaw proofRaw profileRaw p permission ts ins
    some (row::rest)
  | _,_ => none

inductive Rows (sha : Bytes → Bytes) (configRaw proofRaw profileRaw : Bytes)
    (p : NativePlanCoefficients.Bound) (permission : Permission) : List Term → List Input → List Row → Prop
  | nil : Rows sha configRaw proofRaw profileRaw p permission [] [] []
  | cons {t i r ts ins rs}
      (head : loadRow sha configRaw proofRaw profileRaw p permission t i = some r)
      (tail : Rows sha configRaw proofRaw profileRaw p permission ts ins rs) :
      Rows sha configRaw proofRaw profileRaw p permission (t::ts) (i::ins) (r::rs)

theorem rowsSource {sha configRaw proofRaw profileRaw p permission ts ins rs}
    (h : loadRows sha configRaw proofRaw profileRaw p permission ts ins = some rs) :
    Rows sha configRaw proofRaw profileRaw p permission ts ins rs := by
  induction ts generalizing ins rs with
  | nil => cases ins <;> simp [loadRows] at h; subst rs; exact .nil
  | cons t ts ih =>
    cases ins with
    | nil => simp [loadRows] at h
    | cons i ins =>
      simp only [loadRows,bind,Option.bind_eq_some_iff] at h
      obtain ⟨r,hr,rest,hs,last⟩ := h
      cases Option.some.inj last
      exact .cons hr (ih hs)

theorem rowsFromSources {sha configRaw proofRaw profileRaw p permission ts ins rs}
    (h : Rows sha configRaw proofRaw profileRaw p permission ts ins rs) :
    loadRows sha configRaw proofRaw profileRaw p permission ts ins = some rs := by
  induction h with
  | nil => rfl
  | cons head tail ih => simp [loadRows,head,ih]

theorem completeRows {sha configRaw proofRaw profileRaw p permission ts ins rs}
    (h : Rows sha configRaw proofRaw profileRaw p permission ts ins rs) :
    rs.map Row.term = ts ∧ rs.length = ins.length := by
  induction h with
  | nil => exact ⟨rfl,rfl⟩
  | cons head tail ih => simp [(rowSource head).1,ih.1,ih.2]

theorem rowAt {sha configRaw proofRaw profileRaw p permission ts ins rs}
    (h : Rows sha configRaw proofRaw profileRaw p permission ts ins rs) (n : Nat) (r : Row)
    (position : rs[n]? = some r) :
    ∃ t i, ts[n]? = some t ∧ ins[n]? = some i ∧
      loadRow sha configRaw proofRaw profileRaw p permission t i = some r := by
  induction h generalizing n with
  | nil => simp at position
  | @cons t i out ts ins rs head tail ih =>
    cases n with
    | zero => simp at position; subst r; exact ⟨t,i,rfl,rfl,head⟩
    | succ n => simpa using ih n (by simpa using position)

theorem rowMember {sha configRaw proofRaw profileRaw p permission ts ins rs}
    (h : Rows sha configRaw proofRaw profileRaw p permission ts ins rs) (r : Row) (mem : r ∈ rs) :
    ∃ t ∈ ts, ∃ i ∈ ins, loadRow sha configRaw proofRaw profileRaw p permission t i = some r := by
  induction h with
  | nil => simp at mem
  | @cons t i out ts ins rs head tail ih =>
    rcases List.mem_cons.mp mem with same | inside
    · subst r; exact ⟨t,by simp,i,by simp,head⟩
    · obtain ⟨t,ht,i,hi,hr⟩ := ih inside
      exact ⟨t,List.mem_cons_of_mem _ ht,i,List.mem_cons_of_mem _ hi,hr⟩

structure Bound where
  plan : NativePlanCoefficients.Bound
  rows : List Row

def bind (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : Permission) (inputs : List Input) : Option Bound := do
  let p ← NativePlanCoefficients.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
  let rows ← loadRows sha configRaw proofRaw profileRaw p permission p.coefficients inputs
  some ⟨p,rows⟩

theorem boundSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b) :
    NativePlanCoefficients.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b.plan ∧
    Rows sha configRaw proofRaw profileRaw b.plan permission b.plan.coefficients inputs b.rows := by
  simp only [bind,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,rs,hr,last⟩ := h
  cases Option.some.inj last
  exact ⟨hp,rowsSource hr⟩

theorem sharedDecodedProof {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b)
    (r : Row) (mem : r ∈ b.rows) : r.corpus.bounds = b.plan.accumulator := by
  have src := boundSource h
  obtain ⟨t,_,i,_,hr⟩ := rowMember src.2 r mem
  have rr := rowSource hr
  have load := (NativeAccumulatorBinding.corpusSource rr.2.1).2.1
  have proofEq := rr.2.2.2.2.2.2.2.2.2.1
  rw [proofEq,(NativePlanCoefficients.boundSource src.1).accumulator] at load
  exact (Option.some.inj load).symm

theorem boundCoordinateRange {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b)
    (r : Row) (mem : r ∈ b.rows) {blockIndex coordinateIndex v}
    (value : NativeAvailableQ.coordinate r.corpus.manifest blockIndex coordinateIndex = some v) :
    |v| ≤ 32767 := by
  obtain ⟨_,_,_,_,hr⟩ := rowMember (boundSource h).2 r mem
  exact NativeAvailableQ.coordinateRange (rowSource hr).2.1 value

def inDomain (domain : Bytes) (rows : List Row) :=
  rows.filter (fun r => r.term.source.member.input.domain == domain)

open scoped BigOperators
/-- Arbitrary selected domain prefixes/subsets use only actual byte-decoded
coordinate lookups; there is no assumed Q range in this statement. The selector
can choose different coordinates, so this is a bound, not vector sum equality. -/
theorem boundDomainPrefixFits {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b)
    (domain : Bytes) (blockIndex coordinateIndex : Fin (inDomain domain b.rows).length → Nat)
    (values : Fin (inDomain domain b.rows).length → Int)
    (lookups : ∀ i, NativeAvailableQ.coordinate ((inDomain domain b.rows).get i).corpus.manifest
      (blockIndex i) (coordinateIndex i) = some (values i))
    (positions : Finset (Fin (inDomain domain b.rows).length)) :
    |∑ i ∈ positions, ((((inDomain domain b.rows).get i).term.coefficient : Nat) : Int)*values i| ≤
      (NativeAccumulatorBinding.limit b.plan.accumulator.numbers.accumulatorBits : Int) := by
  have src := boundSource h
  have pc := NativePlanCoefficients.checked (NativePlanCoefficients.boundSource src.1).coefficients
  have rows := completeRows src.2
  have count : b.rows.length ≤ b.plan.accumulator.numbers.count := by
    have lens := congrArg List.length rows.1
    simp only [List.length_map] at lens
    rw [lens,pc.2,NativePlanCoefficients.exactCount]
    exact pc.1.2.1
  have member (i : Fin (inDomain domain b.rows).length) : (inDomain domain b.rows).get i ∈ b.rows :=
    List.mem_of_mem_filter (List.get_mem _ i)
  have size : (inDomain domain b.rows).length ≤ b.plan.accumulator.numbers.count :=
    (List.length_filter_le _ _).trans count
  apply NativeAccumulatorBinding.everyBoundedPrefix pc.1.1 Finset.univ
    (fun i => (((inDomain domain b.rows).get i).term.coefficient : Int)) values
    (by simpa using size) _ _ positions (Finset.subset_univ _)
  · intro i _
    have termMem : ((inDomain domain b.rows).get i).term ∈ b.plan.coefficients := by
      rw [← rows.1]; exact List.mem_map.mpr ⟨_,member i,rfl⟩
    rw [pc.2] at termMem
    have cb := NativePlanCoefficients.coefficientBound pc.1 termMem
    simpa using (show ((((inDomain domain b.rows).get i).term.coefficient : Nat) : Int) ≤
      (b.plan.accumulator.numbers.coefficient : Int) by exact_mod_cast cb)
  · intro i _; exact boundCoordinateRange h _ (member i) (lookups i)

theorem boundProductFits {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b)
    (r : Row) (mem : r ∈ b.rows) {blockIndex coordinateIndex v}
    (value : NativeAvailableQ.coordinate r.corpus.manifest blockIndex coordinateIndex = some v) :
    |(r.term.coefficient : Int)*v| ≤
      (NativeAccumulatorBinding.limit b.plan.accumulator.numbers.productBits : Int) := by
  have src := boundSource h
  have pc := NativePlanCoefficients.checked (NativePlanCoefficients.boundSource src.1).coefficients
  have termMem : r.term ∈ b.plan.coefficients := by
    rw [← (completeRows src.2).1]; exact List.mem_map.mpr ⟨r,mem,rfl⟩
  rw [pc.2] at termMem
  exact NativePlanCoefficients.productFits pc.1 termMem v (boundCoordinateRange h r mem value)

theorem completeEligibleOrder {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b) :
    b.rows.map (fun r => r.term.source) = b.plan.members.rows ∧ b.rows.length = inputs.length := by
  have src := boundSource h
  have rows := completeRows src.2
  have originals := NativePlanCoefficients.completeSourceRows src.1
  refine ⟨?_,rows.2⟩
  rw [← originals.1,← rows.1,List.map_map]
  rfl

theorem rejectedMembersRetained {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some b) :
    ∃ all, all.map NativePlanMembers.Member.input = b.plan.members.edge.parent.certificate.body.tuples ∧
      all.map NativePlanMembers.Member.eligibility = b.plan.members.edge.ec.certificate.common.entries ∧
      b.plan.members.rows.map NativePlanMembers.Row.member = NativePlanMembers.eligible all := by
  have src := NativePlanCoefficients.boundSource (boundSource h).1
  exact NativePlanMembers.completeEligibility (NativePlanMembers.preparedSource src.members).rows
end DeltaReduce.NativePlanQCorpus
