import ProfileCandidates
import ProfileConfigurationQC
import ProfileSourceIndex

/-! T047/T053. Original typed non-ISC certificate-to-delivered-V binding.
This composes with the existing typed collection decoders and exact G/V source
binding. It does not infer signature validity, physical delivery or lawful
first-finalization from a quorum; the enclosing original history supplies them.
No certificate, signer, vote, sequence or source occurrence is replaced. -/
namespace DeltaReduce.ProfileSource.CertificateVotes
open NativeReceiptBytes NativeVoteBytes
open NativeInputSetBody (Context)
open InputSection (Located)
open ConfigurationQC (Received)

structure Target where
  kind : Bytes
  semantics : Bytes
  context : Context
  voteContext : Bytes
  body : Bytes
  certificateId : Bytes
  originalCertificate : Bytes
  signers : List Bytes
  threshold : Nat
  deriving DecidableEq

def ec (sha : Bytes → Bytes) (sigma : Bytes) (original : Located Eligibility.Edge) : Option Target := do
  let e := original.value
  let body ← NativeEligibility.bodyId sha ⟨e.certificate.common,e.seedId⟩
  let context ← Candidates.parentContext sha "deltareduce.vote-context.ec.v1" e.certificate.common.isc
  if original.raw = Eligibility.bytes sigma .finalized e.certificate e.seedId then
    some ⟨ascii "EC",sigma,e.certificate.common.context,context,body,e.id,original.raw,
      e.certificate.signers,e.certificate.threshold⟩
  else none

def apc (sha : Bytes → Bytes) (sigma : Bytes) (original : Located Plan.Edge) : Option Target := do
  let e := original.value
  let body ← NativePlan.bodyId sha e.certificate.common
  let context ← Candidates.parentContext sha "deltareduce.vote-context.apc.v1" e.certificate.common.ec
  if original.raw = Plan.bytes sigma .finalized e.certificate then
    some ⟨ascii "APC",sigma,e.certificate.common.context,context,body,e.id,original.raw,
      e.certificate.signers,e.certificate.threshold⟩
  else none

/-- PARAMETER's vote context comes from its original proposed assignment row.
It cannot be derived from the body hash, which intentionally omits that field.
The enclosing source prefix binds this row at its original producing cut. -/
def parameter (sha : Bytes → Bytes) (sigma : Bytes)
    (assignment original : Located Parameter.Edge) : Option Target := do
  let a := assignment.value
  let e := original.value
  if a.certificate.common = e.certificate.common ∧ a.voteContext ≠ [] ∧
      assignment.raw = Parameter.bytes sigma .proposed a.certificate a.voteContext ∧
      original.raw = Parameter.bytes sigma .finalized e.certificate e.voteContext then
    let body ← NativeParameter.bodyId sha ⟨a.certificate.common,a.voteContext⟩
    some ⟨ascii "PARAMETER",sigma,e.certificate.common.context,a.voteContext,body,e.id,original.raw,
      e.certificate.signers,e.certificate.threshold⟩
  else none

def root (sha : Bytes → Bytes) (sigma : Bytes) (original : Located Aggregate.Edge) : Option Target := do
  let e := original.value
  let body ← NativeAggregateRoot.bodyId sha e.certificate.common
  let context ← Candidates.parentContext sha "deltareduce.vote-context.root.v1" e.certificate.common.plan
  if original.raw = Aggregate.bytes sigma .finalized e.certificate then
    some ⟨ascii "AGGREGATE_ROOT",sigma,e.certificate.common.context,context,body,e.id,original.raw,
      e.certificate.signers,e.certificate.threshold⟩
  else none

def applyTarget (sha : Bytes → Bytes) (sigma : Bytes) (original : Located Apply.Edge) : Option Target := do
  let e := original.value
  let c := e.decoded.certificate
  let body ← Apply.candidateId sha sigma e.decoded.candidate
  let context ← Candidates.parentContext sha "deltareduce.vote-context.apply.v1" c.root
  if original.raw = Apply.certificateJSON sigma c ∧ body = c.candidate then
    some ⟨ascii "APPLY",sigma,c.context,context,body,e.id,original.raw,c.signers,c.threshold⟩
  else none

def fullMatch (t : Target) (v : Vote.Vote) : Prop :=
  v.wire.kind = t.kind ∧ v.wire.semantics = t.semantics ∧
  v.wire.context = t.voteContext ∧ v.wire.bodyHash = t.body ∧
  v.wire.epoch = t.context.epoch ∧ v.wire.round = t.context.round ∧
  v.height = t.context.height ∧ v.view = t.context.view
instance (t v) : Decidable (fullMatch t v) := by unfold fullMatch; infer_instance

def matching (actor : Bytes) (cut : Nat) (t : Target) (rows : List Received) : List Received :=
  rows.filter (fun r => decide (r.receiver = actor ∧ r.position ≤ cut ∧ fullMatch t r.vote))

/-- A conflicting full context in the same original body/context group is not
silently erased by the filter. Invalid attempt classification belongs to the
original producer, before it supplies the admitted-delivery inventory here. -/
def GroupCompatible (actor : Bytes) (cut : Nat) (t : Target) (rows : List Received) : Prop :=
  ∀ r ∈ rows, r.receiver = actor → r.position ≤ cut →
    r.vote.wire.kind = t.kind → r.vote.wire.bodyHash = t.body →
    r.vote.wire.context = t.voteContext → fullMatch t r.vote
instance (actor cut t rows) : Decidable (GroupCompatible actor cut t rows) := by
  unfold GroupCompatible; infer_instance

def Quorum (committee : List Bytes) (t : Target) (rows : List Received) : Prop :=
  committee.length = 4 ∧ committee.Nodup ∧ t.threshold = 3 ∧
  Configuration.ordered t.signers = true ∧ t.signers.Nodup ∧ 3 ≤ t.signers.length ∧
  (∀ signer ∈ t.signers, signer ∈ committee ∧ ∃ r ∈ rows, r.vote.wire.validator = signer) ∧
  ∀ r ∈ rows, r.vote.wire.validator ∈ t.signers
instance (committee t rows) : Decidable (Quorum committee t rows) := by
  unfold Quorum; infer_instance

structure Bound where
  target : Target
  originalRows : List Received
  matchingRows : List Received

def bind (committee : List Bytes) (actor : Bytes) (cut : Nat)
    (t : Target) (rows : List Received) : Option Bound :=
  let chosen := matching actor cut t rows
  if GroupCompatible actor cut t rows ∧ Quorum committee t chosen then
    some ⟨t,rows,chosen⟩ else none

theorem boundSource {committee actor cut t rows out}
    (ok : bind committee actor cut t rows = some out) :
    out.target = t ∧ out.originalRows = rows ∧ out.matchingRows = matching actor cut t rows ∧
    GroupCompatible actor cut t rows ∧ Quorum committee t out.matchingRows := by
  unfold bind at ok
  dsimp only at ok
  split at ok <;> try contradiction
  rename_i checks
  cases Option.some.inj ok
  exact ⟨rfl,rfl,rfl,checks⟩

theorem boundComplete {committee actor cut t rows}
    (group : GroupCompatible actor cut t rows)
    (quorum : Quorum committee t (matching actor cut t rows)) :
    bind committee actor cut t rows = some ⟨t,rows,matching actor cut t rows⟩ := by
  simp only [bind]
  exact if_pos ⟨group,quorum⟩

theorem matchingOriginal {actor cut t rows r} (found : r ∈ matching actor cut t rows) :
    r ∈ rows ∧ r.receiver = actor ∧ r.position ≤ cut ∧ fullMatch t r.vote := by
  simpa only [matching,List.mem_filter,decide_eq_true_eq] using found

theorem eachSignerHasOriginal {committee actor cut t rows out signer}
    (ok : bind committee actor cut t rows = some out) (member : signer ∈ t.signers) :
    signer ∈ committee ∧ ∃ r ∈ rows, r.vote.wire.validator = signer ∧
      r.receiver = actor ∧ r.position ≤ cut ∧ fullMatch t r.vote ∧
      Vote.bindArtifact r.originalG r.artifact = some r.vote := by
  have source := boundSource ok
  obtain ⟨enrolled,r,inside,same⟩ := source.2.2.2.2.2.2.2.2.2.2.1 signer member
  rw [source.2.2.1] at inside
  have original := matchingOriginal inside
  exact ⟨enrolled,r,original.1,same,original.2.1,original.2.2.1,original.2.2.2,r.bound⟩

theorem preservesWitness {committee actor cut t rows out}
    (ok : bind committee actor cut t rows = some out) :
    out.target.originalCertificate = t.originalCertificate ∧
    out.target.certificateId = t.certificateId ∧ out.target.signers = t.signers ∧
    out.originalRows = rows := by
  have src := boundSource ok
  rw [src.1]
  exact ⟨rfl,rfl,rfl,src.2.1⟩

/-- The same body does not authorize replacing a signer-dependent witness. -/
theorem distinctWitnessesStayDistinct {committee actorA actorB cutA cutB a b rowsA rowsB left right}
    (ha : bind committee actorA cutA a rowsA = some left)
    (hb : bind committee actorB cutB b rowsB = some right)
    (different : a.certificateId ≠ b.certificateId) :
    left.target.certificateId ≠ right.target.certificateId := by
  rw [(boundSource ha).1,(boundSource hb).1]
  exact different

inductive Original where
  | ec (certificate : Located Eligibility.Edge)
  | apc (certificate : Located Plan.Edge)
  | parameter (assignment certificate : Located Parameter.Edge)
  | root (certificate : Located Aggregate.Edge)
  | apply (certificate : Located Apply.Edge)

def derive (sha : Bytes → Bytes) (sigma : Bytes) : Original → Option Target
  | .ec c => ec sha sigma c
  | .apc c => apc sha sigma c
  | .parameter a c => parameter sha sigma a c
  | .root c => root sha sigma c
  | .apply c => applyTarget sha sigma c

def bindOriginal (sha : Bytes → Bytes) (sigma : Bytes) (committee : List Bytes)
    (actor : Bytes) (cut : Nat) (original : Original) (rows : List Received) : Option Bound := do
  let target ← derive sha sigma original
  bind committee actor cut target rows

theorem originalSource {sha sigma committee actor cut original rows out}
    (ok : bindOriginal sha sigma committee actor cut original rows = some out) :
    derive sha sigma original = some out.target ∧ out.originalRows = rows ∧
    out.matchingRows = matching actor cut out.target rows ∧
    GroupCompatible actor cut out.target rows ∧
    Quorum committee out.target out.matchingRows := by
  unfold bindOriginal at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨target,source,accepted⟩ := ok
  have bound := boundSource accepted
  rw [bound.1]
  exact ⟨source,bound.2⟩

/-- These are existing original finalization positions/receivers, not new
protocol IDs. SourceIndex binds them to each original event before this join. -/
structure OriginalCut where
  receiver : Bytes
  cut : Nat
  certificate : Original

/-- Preserve each certificate's OWN original cut. Applying one later snapshot
cut to every historical QC could incorrectly replace its original signer set. -/
def bindAll (sha : Bytes → Bytes) (sigma : Bytes) (committee : List Bytes)
    (rows : List Received) : List OriginalCut → Option (List Bound)
  | [] => some []
  | c::cs => do
    let b ← bindOriginal sha sigma committee c.receiver c.cut c.certificate rows
    let bs ← bindAll sha sigma committee rows cs
    some (b::bs)

theorem wholeCount {sha sigma committee rows originals bound}
    (ok : bindAll sha sigma committee rows originals = some bound) :
    bound.length = originals.length := by
  induction originals generalizing bound with
  | nil => cases Option.some.inj ok; rfl
  | cons c cs ih =>
    simp only [bindAll,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨b,hb,bs,hbs,last⟩ := ok
    cases Option.some.inj last
    exact congrArg Nat.succ (ih hbs)

theorem everyOriginalAt {sha sigma committee rows originals bound original} {index : Nat}
    (ok : bindAll sha sigma committee rows originals = some bound)
    (found : originals[index]? = some original) :
    ∃ result, bound[index]? = some result ∧
      bindOriginal sha sigma committee original.receiver original.cut original.certificate rows = some result := by
  induction originals generalizing bound index with
  | nil => simp at found
  | cons c cs ih =>
    simp only [bindAll,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨b,hb,bs,hbs,last⟩ := ok
    cases Option.some.inj last
    cases index with
    | zero =>
      have eq : c = original := by simpa using found
      subst original
      exact ⟨b,rfl,hb⟩
    | succ n =>
      obtain ⟨b,hb,source⟩ := ih hbs (by simpa using found)
      exact ⟨b,by simpa using hb,source⟩

theorem futureDeliveryDoesNotChangeCut (actor cut t rows later)
    (future : ∀ r ∈ later, cut < r.position) :
    matching actor cut t (rows ++ later) = matching actor cut t rows := by
  unfold matching
  rw [List.filter_append]
  have empty : List.filter (fun r => decide (r.receiver = actor ∧ r.position ≤ cut ∧ fullMatch t r.vote)) later = [] := by
    apply List.filter_eq_nil_iff.mpr
    intro r hr
    have no : ¬ (r.receiver = actor ∧ r.position ≤ cut ∧ fullMatch t r.vote) := by
      intro accepted
      have tooLate := future r hr
      omega
    simpa using no
  rw [empty,List.append_nil]

def finalizationAction : Original → Bytes
  | .ec _ => ascii "ACT-EC-FINALIZE"
  | .apc _ => ascii "ACT-APC-FINALIZE"
  | .parameter _ _ => ascii "ACT-PARAM-FINALIZE"
  | .root _ => ascii "ACT-ROOT-FINALIZE"
  | .apply _ => ascii "ACT-APPLY-FINALIZE"

structure AtEvent where
  original : Index.Event
  votes : Bound

/-- Bind the cutoff to the actual original source occurrence. The event's
position is an inventory index, not a new vote or WAL sequence. No event at
position zero may pretend to have a preceding delivered quorum. -/
def bindEvent (sha : Bytes → Bytes) (sigma : Bytes) (committee : List Bytes)
    (original : Original) (rows : List Received) (event : Index.Event) : Option AtEvent := do
  let target ← derive sha sigma original
  if event.action = finalizationAction original ∧ 0 < event.position ∧
      event.original = target.originalCertificate then
    let result ← bind committee event.actor (event.position-1) target rows
    some ⟨event,result⟩
  else none

theorem eventBound {sha sigma committee original rows event result}
    (ok : bindEvent sha sigma committee original rows event = some result) :
    result.original = event ∧ derive sha sigma original = some result.votes.target ∧
    event.action = finalizationAction original ∧ 0 < event.position ∧
    event.original = result.votes.target.originalCertificate ∧
    bind committee event.actor (event.position-1) result.votes.target rows = some result.votes := by
  unfold bindEvent at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨target,typed,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i checks
  obtain ⟨bound,accepted,last⟩ := Option.bind_eq_some_iff.mp ok
  cases Option.some.inj last
  rw [(boundSource accepted).1]
  exact ⟨rfl,typed,checks.1,checks.2.1,checks.2.2,accepted⟩

theorem eventComplete {sha sigma committee original rows event target bound}
    (typed : derive sha sigma original = some target)
    (action : event.action = finalizationAction original)
    (positive : 0 < event.position)
    (bytes : event.original = target.originalCertificate)
    (votes : bind committee event.actor (event.position-1) target rows = some bound) :
    bindEvent sha sigma committee original rows event = some ⟨event,bound⟩ := by
  have checks : event.action = finalizationAction original ∧ 0 < event.position ∧
      event.original = target.originalCertificate := ⟨action,positive,bytes⟩
  simp only [bindEvent,typed,Bind.bind,Option.bind,if_pos checks,votes]

theorem originalFinalizationCut {sha declared store position descriptor event
    sigma committee original rows result}
    (indexed : Index.EventSource sha declared store position descriptor event)
    (ok : bindEvent sha sigma committee original rows event = some result) :
    result.original.descriptor = descriptor ∧ result.original.position = position ∧
    result.original.original = result.votes.target.originalCertificate ∧
    ∀ signer ∈ result.votes.target.signers, ∃ r ∈ rows,
      r.vote.wire.validator = signer ∧ r.receiver = event.actor ∧
      r.position < position ∧ fullMatch result.votes.target r.vote ∧
      Vote.bindArtifact r.originalG r.artifact = some r.vote := by
  have bound := eventBound ok
  rw [bound.1]
  refine ⟨indexed.originalDescriptor,indexed.index,bound.2.2.2.2.1,?_⟩
  intro signer member
  have source := eachSignerHasOriginal bound.2.2.2.2.2 member
  obtain ⟨_,r,originalRow,same,receiver,before,matched,bytes⟩ := source
  refine ⟨r,originalRow,same,receiver,?_,matched,bytes⟩
  have positive := bound.2.2.2.1
  have indexedPosition := indexed.index
  omega

end DeltaReduce.ProfileSource.CertificateVotes
