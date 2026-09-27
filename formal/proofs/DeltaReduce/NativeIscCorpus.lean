import DeltaReduce.NativeVectorAuthority

/-! Complete ISC member manifests, including EC-rejected members. Primitive
availability observations remain unauthenticated component inputs. Loading them
does not prove a commitment preimage, signer custody or native recovery. -/
namespace DeltaReduce.NativeIscCorpus
open NativeBinding (Bytes)
open NativePlanMembers (Member)
open NativeAvailableQ (Input Permission Primitive Coverage)
open NativeVectorContext (Bound)

def manifest (sha : Bytes → Bytes) (i : Input) :=
  NativeManifestBinding.bind (NativePlanCoefficients.contentHash sha)
    i.schemaRaw i.scaleRaw i.planRaw i.manifestRaw i.manifestId i.raws

def Links (b : Bound) (m : Member) (i : Input) (q : NativeManifestBinding.Bound) : Prop :=
  i.observation.commitmentTicket = m.input.ticket ∧
  i.observation.commitment = m.input.commitment ∧
  i.observation.certificate = m.input.availability ∧
  q.manifest.wire.ticket = m.input.ticket ∧ q.manifest.wire.domain = m.input.domain ∧
  q.manifest.wire.schema = (NativeVectorAuthority.plan b).certificate.common.context.schema ∧
  q.manifest.wire.parent = (NativeVectorAuthority.state b).wire.parent ∧
  NativeVectorContext.Compatible b.first.corpus.manifest q
instance (b m i q) : Decidable (Links b m i q) := by unfold Links; infer_instance

structure Row where
  member : Member
  input : Input
  corpus : NativeManifestBinding.Bound
  deriving DecidableEq, Repr

def loadRow (sha : Bytes → Bytes) (b : Bound) (permission : Permission)
    (m : Member) (i : Input) : Option Row := do
  let q ← manifest sha i
  if Primitive permission i.observation ∧ Coverage i.observation q ∧ Links b m i q then
    some ⟨m,i,q⟩ else none

theorem rowSource {sha b p m i r} (h : loadRow sha b p m i = some r) :
    r.member = m ∧ r.input = i ∧ manifest sha i = some r.corpus ∧
    Primitive p i.observation ∧ Coverage i.observation r.corpus ∧ Links b m i r.corpus := by
  simp only [loadRow,bind,Option.bind_eq_some_iff] at h
  obtain ⟨q,hq,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨rfl,rfl,hq,by assumption⟩

theorem rowFromSources {sha b p m i q} (loaded : manifest sha i = some q)
    (primitive : Primitive p i.observation) (coverage : Coverage i.observation q)
    (links : Links b m i q) : loadRow sha b p m i = some ⟨m,i,q⟩ := by
  simp only [loadRow,loaded,bind,Option.bind]
  exact if_pos ⟨primitive,coverage,links⟩

theorem wrongMemberRejected {sha b p m i q} (loaded : manifest sha i = some q)
    (wrong : ¬ Links b m i q) : loadRow sha b p m i = none := by
  simp [loadRow,loaded,wrong]

theorem missingManifestRejected {sha b p m i} (missing : manifest sha i = none) :
    loadRow sha b p m i = none := by simp [loadRow,missing]

def loadRows (sha : Bytes → Bytes) (b : Bound) (p : Permission) :
    List Member → List Input → Option (List Row)
  | [],[] => some []
  | m::ms,i::ins => do
    let r ← loadRow sha b p m i
    let rest ← loadRows sha b p ms ins
    some (r::rest)
  | _,_ => none

inductive Rows (sha : Bytes → Bytes) (b : Bound) (p : Permission) :
    List Member → List Input → List Row → Prop
  | nil : Rows sha b p [] [] []
  | cons {m i r ms ins rs} (head : loadRow sha b p m i = some r)
      (tail : Rows sha b p ms ins rs) : Rows sha b p (m::ms) (i::ins) (r::rs)

theorem rowsSource {sha b p ms ins rs} (h : loadRows sha b p ms ins = some rs) :
    Rows sha b p ms ins rs := by
  induction ms generalizing ins rs with
  | nil => cases ins <;> simp [loadRows] at h; subst rs; exact .nil
  | cons m ms ih =>
    cases ins with
    | nil => simp [loadRows] at h
    | cons i ins =>
      simp only [loadRows,bind,Option.bind_eq_some_iff] at h
      obtain ⟨r,hr,rest,ht,last⟩ := h
      cases Option.some.inj last
      exact .cons hr (ih ht)

theorem rowsFromSources {sha b p ms ins rs} (h : Rows sha b p ms ins rs) :
    loadRows sha b p ms ins = some rs := by
  induction h with
  | nil => rfl
  | cons head tail ih => simp [loadRows,head,ih]

theorem completeRows {sha b p ms ins rs} (h : Rows sha b p ms ins rs) :
    rs.map Row.member = ms ∧ rs.map Row.input = ins := by
  induction h with
  | nil => exact ⟨rfl,rfl⟩
  | cons head tail ih => simp [(rowSource head).1,(rowSource head).2.1,ih.1,ih.2]

theorem rowAt {sha b p ms ins rs} (h : Rows sha b p ms ins rs) {n : Nat} {r : Row}
    (position : rs[n]? = some r) : ∃ m i, ms[n]? = some m ∧ ins[n]? = some i ∧
      loadRow sha b p m i = some r := by
  induction h generalizing n with
  | nil => simp at position
  | @cons m i out ms ins rs head tail ih =>
    cases n with
    | zero => simp at position; subst r; exact ⟨m,i,rfl,rfl,head⟩
    | succ n => simpa using ih (by simpa using position)

def arithmeticRows (rs : List Row) :=
  (rs.filter (fun r => r.member.eligibility.accepted != 0)).map (fun r => (r.member,r.corpus))
def ArithmeticCoverage (b : Bound) (rs : List Row) : Prop :=
  arithmeticRows rs = b.source.rows.map (fun r => (r.term.source.member,r.corpus.manifest))
instance (b rs) : Decidable (ArithmeticCoverage b rs) := by unfold ArithmeticCoverage; infer_instance

structure Complete where
  members : List Member
  rows : List Row

def collect (sha : Bytes → Bytes) (b : Bound) (p : Permission) (inputs : List Input) : Option Complete := do
  let ms ← NativePlanMembers.align (NativeVectorAuthority.plan b).parent.certificate.body.tuples
    (NativeVectorAuthority.plan b).ec.certificate.common.entries
  let rs ← loadRows sha b p ms inputs
  if ArithmeticCoverage b rs then some ⟨ms,rs⟩ else none

structure Source (sha : Bytes → Bytes) (b : Bound) (p : Permission) (inputs : List Input)
    (c : Complete) : Prop where
  alignment : NativePlanMembers.align (NativeVectorAuthority.plan b).parent.certificate.body.tuples
    (NativeVectorAuthority.plan b).ec.certificate.common.entries = some c.members
  rows : Rows sha b p c.members inputs c.rows
  arithmetic : ArithmeticCoverage b c.rows

theorem collected {sha b p inputs c} (h : collect sha b p inputs = some c) : Source sha b p inputs c := by
  simp only [collect,bind,Option.bind_eq_some_iff] at h
  obtain ⟨ms,hm,rs,hr,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hm,rowsSource hr,by assumption⟩

theorem collectFromSources {sha b p inputs c} (h : Source sha b p inputs c) :
    collect sha b p inputs = some c := by
  simp only [collect,h.alignment,rowsFromSources h.rows,bind,Option.bind,if_pos h.arithmetic]

theorem everyOriginalMember {sha b p inputs c} (h : collect sha b p inputs = some c) :
    c.rows.map (fun r => r.member.input) = (NativeVectorAuthority.plan b).parent.certificate.body.tuples ∧
    c.rows.map (fun r => r.member.eligibility) = (NativeVectorAuthority.plan b).ec.certificate.common.entries := by
  have src := collected h
  have all := NativePlanMembers.alignedSource src.alignment
  have same := (completeRows src.rows).1
  exact ⟨by rw [← all.1,← same,List.map_map]; rfl,
    by rw [← all.2.1,← same,List.map_map]; rfl⟩

theorem rejectedMemberRetained {sha b p inputs c} (h : collect sha b p inputs = some c)
    (m : Member) (mem : m ∈ c.members) (rejected : m.eligibility.accepted = 0) :
    ∃ r ∈ c.rows, r.member = m ∧ r.member.eligibility.accepted = 0 := by
  rw [← (completeRows (collected h).rows).1] at mem
  obtain ⟨r,hr,eq⟩ := List.mem_map.mp mem
  exact ⟨r,hr,eq,eq ▸ rejected⟩

theorem originalManifestBytes {sha b p m i r} (h : loadRow sha b p m i = some r) :
    NativeManifestBytes.encode r.corpus.manifest.wire = i.manifestRaw ∧
    r.corpus.plan.plan.entries.length = i.raws.length ∧ i.raws.length = r.corpus.blocks.length :=
  ⟨NativeManifestBinding.exactPreimage (rowSource h).2.2.1,
    NativeManifestBinding.noMissingOrExtraBlocks (rowSource h).2.2.1⟩

theorem exactAvailableLeaves {sha b p m i r} (h : loadRow sha b p m i = some r) :
    i.observation.covered.Perm (r.corpus.manifest.refs.map (fun ref => ref.wire.leaf)) :=
  NativeAvailableQ.exactCoveredLeaves (rowSource h).2.2.2.1 (rowSource h).2.2.2.2.1

theorem inputsRequired {sha b p ms inputs rs} (h : loadRows sha b p ms inputs = some rs) :
    inputs.length = ms.length := by
  have src := completeRows (rowsSource h)
  have left := congrArg List.length src.1
  have right := congrArg List.length src.2
  simp only [List.length_map] at left right
  exact right.symm.trans left

theorem missingOrExtraRejected {sha b p ms inputs} (different : inputs.length ≠ ms.length) :
    loadRows sha b p ms inputs = none := by
  cases loaded : loadRows sha b p ms inputs with
  | none => rfl
  | some rs => exact False.elim (different (inputsRequired loaded))

def run (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (p : Permission) (eligibleInputs allInputs : List Input) : Option (Bound × Complete) := do
  let b ← NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw p eligibleInputs
  let c ← collect sha b p allInputs
  some (b,c)

theorem runSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw p eligibleInputs allInputs b c}
    (h : run sha policyRaw stateRaw apcId configRaw proofRaw profileRaw p eligibleInputs allInputs = some (b,c)) :
    NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw p eligibleInputs = some b ∧
    collect sha b p allInputs = some c := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨b',hb,c',hc,last⟩ := h
  cases Option.some.inj last
  exact ⟨hb,hc⟩
end DeltaReduce.NativeIscCorpus
