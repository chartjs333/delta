import ProfileCertificateVotes
import ProfileInstalledState

/-! T047/T053. Pure candidate construction for the approved first-ISC producer.
The complete prior policy and the original admitted delivery cut are inputs to
this conjunct, not authority inferred from its output. The enclosing source
fold still derives their origin, ordinary-active phase, clock and barriers.
Only the two specified snapshot collections change; no lineage is cleared. -/
namespace DeltaReduce.ProfileSource.IscFinalization
open NativeReceiptBytes (Bytes)
open NativePolicyCodec (Value Format lookup)
open NativeVoteBytes (ascii)
open ISCSourceV2

def replace : Format → Value → String → Value → Option Value
  | .field name _ tail,.pair head rest,key,new =>
      if key = name then some (.pair new rest) else do
        let next ← replace tail rest key new
        some (.pair head next)
  | _,_,_,_ => none

theorem replacementField {fmt original key new next}
    (ok : replace fmt original key new = some next) : lookup fmt next key = some new := by
  induction fmt generalizing original next with
  | field name head tail ihHead ih =>
    cases original <;> simp only [replace] at ok <;> try contradiction
    rename_i value rest
    split at ok
    · rename_i same
      cases Option.some.inj ok
      simp [lookup,same]
    · rename_i different
      obtain ⟨later,hl,last⟩ := Option.bind_eq_some_iff.mp ok
      cases Option.some.inj last
      simp only [lookup,if_neg different]
      exact ih hl
  | _ => cases original <;> simp [replace] at ok

theorem otherFields {fmt original key new next}
    (ok : replace fmt original key new = some next) (other : String) (different : other ≠ key) :
    lookup fmt next other = lookup fmt original other := by
  induction fmt generalizing original next with
  | field name head tail ihHead ih =>
    cases original <;> simp only [replace] at ok <;> try contradiction
    rename_i value rest
    split at ok
    · rename_i same
      cases Option.some.inj ok
      have ne : other ≠ name := by simpa only [← same] using different
      simp only [lookup,if_neg ne]
    · obtain ⟨later,hl,last⟩ := Option.bind_eq_some_iff.mp ok
      cases Option.some.inj last
      simp only [lookup]
      split <;> first | rfl | exact ih hl
  | _ => cases original <;> simp [replace] at ok

def sameWitnessTree (a b : Value) : Bool :=
  match readCertificate a,readCertificate b with
  | some left,some right => decide (left = right)
  | _,_ => false

theorem witnessTreeExact {a b} (same : sameWitnessTree a b = true) : a = b := by
  unfold sameWitnessTree at same
  split at same <;> try contradiction
  rename_i left right ha hb
  have eq : left = right := of_decide_eq_true same
  exact (certificateOriginal ha).trans ((congrArg certificateValue eq).trans
    (certificateOriginal hb).symm)

/-- Preserve a previously retained exact witness, or insert one new witness at
its original c ordering position. Equal c with different bytes fails closed. -/
def insertWitness (id : Bytes) (tree : Value) : List (Bytes × Value) → Option (List (Bytes × Value))
  | [] => some [(id,tree)]
  | (old,value)::rest =>
    if id = old then
      if sameWitnessTree tree value then some ((old,value)::rest) else none
    else if NativePolicyBytes.bytesLT id old then some ((id,tree)::(old,value)::rest)
    else do
      let tail ← insertWitness id tree rest
      some ((old,value)::tail)

def insertBody (id : Bytes) : List Bytes → List Bytes
  | [] => [id]
  | old::rest => if id = old then old::rest else
      if NativePolicyBytes.bytesLT id old then id::old::rest else old::insertBody id rest

theorem originalWitnessesRetained {id tree old next}
    (ok : insertWitness id tree old = some next) : old.Sublist next := by
  induction old generalizing next with
  | nil => exact List.nil_sublist _
  | cons head rest ih =>
    rcases head with ⟨key,value⟩
    simp only [insertWitness] at ok
    split at ok
    · split at ok <;> try contradiction
      cases Option.some.inj ok
      exact List.Sublist.refl _
    · split at ok
      · cases Option.some.inj ok
        exact List.sublist_cons_self _ _
      · obtain ⟨tail,ht,last⟩ := Option.bind_eq_some_iff.mp ok
        cases Option.some.inj last
        exact (ih ht).cons_cons _

theorem selectedWitnessRetained {id tree old next}
    (ok : insertWitness id tree old = some next) : (id,tree) ∈ next := by
  induction old generalizing next with
  | nil => cases Option.some.inj ok; simp
  | cons head rest ih =>
    rcases head with ⟨key,value⟩
    simp only [insertWitness] at ok
    split at ok
    · rename_i sameId
      split at ok <;> try contradiction
      rename_i sameTree
      cases Option.some.inj ok
      have eq := witnessTreeExact sameTree
      simp [sameId,eq]
    · split at ok
      · cases Option.some.inj ok
        simp
      · obtain ⟨tail,ht,last⟩ := Option.bind_eq_some_iff.mp ok
        cases Option.some.inj last
        exact List.mem_cons_of_mem _ (ih ht)

theorem originalFinalizedRetained (id : Bytes) (old : List Bytes) :
    old.Sublist (insertBody id old) := by
  induction old with
  | nil => exact List.nil_sublist _
  | cons head rest ih =>
    simp only [insertBody]
    split
    · exact List.Sublist.refl _
    · split
      · exact List.sublist_cons_self _ _
      · exact ih.cons_cons _

theorem selectedBodyRetained (id : Bytes) (old : List Bytes) :
    id ∈ insertBody id old := by
  induction old with
  | nil => simp [insertBody]
  | cons head rest ih =>
    simp only [insertBody]
    split
    · rename_i same
      simp [same]
    · split
      · simp
      · exact List.mem_cons_of_mem _ ih

structure Update where
  snapshot : Value
  policy : Value
  raw : Bytes
  witnesses : List (Bytes × Value)
  finalized : List Bytes

def update (prior : NativePolicyBytes.Policy) (inputs : InputSection.Bound)
    (certificate : BoundCertificate) : Option Update := do
  let old := inputs.certificates.map (fun x => (x.value.witnessId,x.tree))
  let witnesses ← insertWitness certificate.witnessId certificate.originalTree old
  let finalized := insertBody certificate.consensusId inputs.finalized
  let first ← replace NativeHeader.snapshotFormat prior.snapshot "input_set_certificates"
    (.items (witnesses.map Prod.snd))
  let snapshot ← replace NativeHeader.snapshotFormat first "finalized_input_set_ids"
    (.items (finalized.map Value.text))
  let policy ← replace NativeHeader.policyFormat prior.source "snapshot" snapshot
  let raw ← NativeHeader.policyBytes policy
  some ⟨snapshot,policy,raw,witnesses,finalized⟩

theorem updateSource {prior inputs certificate out}
    (ok : update prior inputs certificate = some out) :
    ∃ first,
      insertWitness certificate.witnessId certificate.originalTree
        (inputs.certificates.map (fun x => (x.value.witnessId,x.tree))) = some out.witnesses ∧
      out.finalized = insertBody certificate.consensusId inputs.finalized ∧
      replace NativeHeader.snapshotFormat prior.snapshot "input_set_certificates"
        (.items (out.witnesses.map Prod.snd)) = some first ∧
      replace NativeHeader.snapshotFormat first "finalized_input_set_ids"
        (.items (out.finalized.map Value.text)) = some out.snapshot ∧
      replace NativeHeader.policyFormat prior.source "snapshot" out.snapshot = some out.policy ∧
      NativeHeader.policyBytes out.policy = some out.raw := by
  simp only [update,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨w,hw,first,hf,snapshot,hs,policy,hp,raw,hr,last⟩ := ok
  cases Option.some.inj last
  exact ⟨first,hw,rfl,hf,hs,hp,hr⟩

theorem preservesOtherSnapshotFields {prior inputs certificate out}
    (ok : update prior inputs certificate = some out) (key : String)
    (notWitness : key ≠ "input_set_certificates") (notFinal : key ≠ "finalized_input_set_ids") :
    lookup NativeHeader.snapshotFormat out.snapshot key =
      lookup NativeHeader.snapshotFormat prior.snapshot key := by
  obtain ⟨first,_,_,hf,hs,_,_⟩ := updateSource ok
  exact (otherFields hs key notFinal).trans (otherFields hf key notWitness)

theorem preservesOuterFields {prior inputs certificate out}
    (ok : update prior inputs certificate = some out) (key : String) (notSnapshot : key ≠ "snapshot") :
    lookup NativeHeader.policyFormat out.policy key = lookup NativeHeader.policyFormat prior.source key := by
  obtain ⟨first,_,_,_,_,hp,_⟩ := updateSource ok
  exact otherFields hp key notSnapshot

theorem allOldWitnessesAndBodies {prior inputs certificate out}
    (ok : update prior inputs certificate = some out) :
    (inputs.certificates.map (fun x => (x.value.witnessId,x.tree))).Sublist out.witnesses ∧
    inputs.finalized.Sublist out.finalized ∧
    (certificate.witnessId,certificate.originalTree) ∈ out.witnesses ∧
    certificate.consensusId ∈ out.finalized := by
  obtain ⟨first,hw,hb,_,_,_,_⟩ := updateSource ok
  exact ⟨originalWitnessesRetained hw,by rw [hb]; exact originalFinalizedRetained _ _,
    selectedWitnessRetained hw,by rw [hb]; exact selectedBodyRetained _ _⟩

theorem differentWitnessCollision (id : Bytes) (old new : Value) (rest : List (Bytes × Value))
    (different : old ≠ new) : insertWitness id new ((id,old)::rest) = none := by
  rw [insertWitness,if_pos rfl]
  split
  · rename_i same
    exact False.elim (different (witnessTreeExact same).symm)
  · rfl

def target (sigma context : Bytes) (body : InputSection.BodyRow) : CertificateVotes.Target :=
  ⟨ascii "ISC",sigma,body.body.context,context,body.consensusId,[],[],[],3⟩

def signers (committee : List Bytes) (rows : List ConfigurationQC.Received) : List Bytes :=
  committee.filter (fun id => rows.any (fun row => row.vote.wire.validator == id))

structure Candidate where
  selected : InputSection.Located InputSection.BodyRow
  certificate : BoundCertificate
  quorum : CertificateVotes.Bound
  update : Update

def Inputs (prior : InstalledState.Bound) : InputSection.Bound :=
  prior.collections.eligibility.lineage.inputs

def Guards (prior : InstalledState.Bound) (actor : Bytes) (tick : Nat)
    (bodyId : Bytes) (frozen : List NativeInputSetBody.Tuple)
    (selected : InputSection.Located InputSection.BodyRow) : Prop :=
  let p := prior.installed.policy
  let inputs := Inputs prior
  p.localValidator = actor ∧ p.config ∈ prior.collections.finalizedConfigs ∧
  bodyId ∈ inputs.closed ∧ selected.value.body.tuples = frozen ∧
  p.initialTick ≤ tick ∧ tick < p.hardDeadline ∧ prior.collections.tail.aborts.isEmpty = true ∧
  bodyId ∉ inputs.finalized ∧
  ∀ old ∈ inputs.certificates,
    old.value.certificate.body.context.round = prior.installed.header.state.round →
    old.value.consensusId ∉ inputs.finalized
instance (p a t b f s) : Decidable (Guards p a t b f s) := by unfold Guards; infer_instance

def computedCertificate (prior : InstalledState.Bound) (actor : Bytes) (cut : Nat)
    (context : Bytes) (body : InputSection.BodyRow) (rows : List ConfigurationQC.Received) :
    Certificate :=
  let t := target prior.installed.header.state.semantics context body
  ⟨body.body,3,signers prior.installed.policy.validators
    (CertificateVotes.matching actor cut t rows)⟩

def completeTarget (sigma context : Bytes) (body : InputSection.BodyRow)
    (certificate : BoundCertificate) (computed : Certificate) : CertificateVotes.Target :=
  ⟨ascii "ISC",sigma,body.body.context,context,body.consensusId,certificate.witnessId,
    certificateJSON sigma computed,computed.signers,3⟩

/-- The input inventory must be the source-derived received inventory at this
actor/cut. Authentication and physical occurrence are not granted by Received's
structural V/G binding. No first-q selection or replacement of b by c occurs. -/
def assemble (sha : Bytes → Bytes) (prior : InstalledState.Bound) (actor : Bytes)
    (cut tick : Nat) (bodyId : Bytes) (frozen : List NativeInputSetBody.Tuple)
    (rows : List ConfigurationQC.Received) : Option Candidate := do
  let p := prior.installed.policy
  let s := prior.installed.header.state
  let inputs := Inputs prior
  let selected ← inputs.bodies.find? (fun row => row.value.consensusId == bodyId)
  if Guards prior actor tick bodyId frozen selected then
    let context ← NativeIscAdmission.iscContext sha s.round
    let c := computedCertificate prior actor cut context selected.value rows
    let raw := certificateJSON s.semantics c
    let certificate ← bindCertificate sha s.semantics prior.collections.context s.parent
      p.validators (certificateValue c) raw
    let full := completeTarget s.semantics context selected.value certificate c
    let quorum ← CertificateVotes.bind p.validators actor cut full rows
    let following ← update p inputs certificate
    some ⟨selected,certificate,quorum,following⟩
  else none

structure Source (sha : Bytes → Bytes) (prior : InstalledState.Bound) (actor : Bytes)
    (cut tick : Nat) (bodyId : Bytes) (frozen : List NativeInputSetBody.Tuple)
    (rows : List ConfigurationQC.Received) (out : Candidate) where
  context : Bytes
  selected : (Inputs prior).bodies.find? (fun row => row.value.consensusId == bodyId) = some out.selected
  guards : Guards prior actor tick bodyId frozen out.selected
  voteContext : NativeIscAdmission.iscContext sha prior.installed.header.state.round = some context
  certificate :
    let c := computedCertificate prior actor cut context out.selected.value rows
    bindCertificate sha prior.installed.header.state.semantics prior.collections.context
      prior.installed.header.state.parent prior.installed.policy.validators
      (certificateValue c) (certificateJSON prior.installed.header.state.semantics c) = some out.certificate
  quorum : CertificateVotes.bind prior.installed.policy.validators actor cut
    (completeTarget prior.installed.header.state.semantics context out.selected.value out.certificate
      (computedCertificate prior actor cut context out.selected.value rows)) rows = some out.quorum
  updated : update prior.installed.policy (Inputs prior) out.certificate = some out.update

theorem assembled {sha prior actor cut tick bodyId frozen rows out}
    (ok : assemble sha prior actor cut tick bodyId frozen rows = some out) :
    Nonempty (Source sha prior actor cut tick bodyId frozen rows out) := by
  unfold assemble at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨selected,hs,last⟩ := ok
  split at last <;> try contradiction
  rename_i guards
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨context,hctx,certificate,hc,quorum,hq,next,hn,last⟩ := last
  cases Option.some.inj last
  exact ⟨⟨context,hs,guards,hctx,hc,hq,hn⟩⟩

theorem assembleComplete {sha prior actor cut tick bodyId frozen rows out}
    (h : Source sha prior actor cut tick bodyId frozen rows out) :
    assemble sha prior actor cut tick bodyId frozen rows = some out := by
  unfold assemble
  dsimp only
  rw [h.selected]
  dsimp only [Bind.bind,Option.bind]
  rw [if_pos h.guards,h.voteContext]
  dsimp only
  rw [h.certificate]
  dsimp only
  rw [h.quorum]
  dsimp only
  rw [h.updated]

theorem exactComputedSigners {sha prior actor cut tick bodyId frozen rows out}
    (ok : assemble sha prior actor cut tick bodyId frozen rows = some out) :
    out.quorum.originalRows = rows ∧ out.certificate.certificate.body = out.selected.value.body ∧
    out.certificate.certificate.signers = out.quorum.target.signers := by
  obtain ⟨h⟩ := assembled ok
  have q := CertificateVotes.boundSource h.quorum
  have c := boundCertificateSource h.certificate
  have same := Option.some.inj ((certificateRead _).symm.trans c.parsed)
  exact ⟨q.2.1,by rw [← same]; rfl,by rw [← same,q.1]; rfl⟩

theorem unchangedLineage {sha prior actor cut tick bodyId frozen rows out}
    (ok : assemble sha prior actor cut tick bodyId frozen rows = some out) (key : String)
    (notWitness : key ≠ "input_set_certificates") (notFinal : key ≠ "finalized_input_set_ids") :
    lookup NativeHeader.snapshotFormat out.update.snapshot key =
      lookup NativeHeader.snapshotFormat prior.installed.policy.snapshot key := by
  obtain ⟨h⟩ := assembled ok
  exact preservesOtherSnapshotFields h.updated key notWitness notFinal

structure Original where
  before : InstalledState.Bound
  candidate : Candidate

def fromBytes (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) (cut tick : Nat) (bodyId : Bytes)
    (frozen : List NativeInputSetBody.Tuple) (rows : List ConfigurationQC.Received) : Option Original := do
  let prior ← InstalledState.bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals
  let candidate ← assemble sha prior actor cut tick bodyId frozen rows
  some ⟨prior,candidate⟩

theorem originalBefore {sha enrolled actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId frozen rows out}
    (ok : fromBytes sha enrolled actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId frozen rows = some out) :
    InstalledState.bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out.before ∧
    assemble sha out.before actor cut tick bodyId frozen rows = some out.candidate := by
  simp only [fromBytes,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨prior,hp,candidate,hc,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hp,hc⟩

end DeltaReduce.ProfileSource.IscFinalization
