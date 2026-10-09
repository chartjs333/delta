import ProfileIscFinalization

/-! T047/T053. EC-SOURCE-STEP-v1's computed first-finalization conjunct.
This is isolated feature000 source interpretation, not a deployed EC producer.
The enclosing history must derive the complete prior state, original admitted
rows, phase/clock and prerequisites. Neither byte binding nor this computation
asserts that origin, authentication or a concrete EC durability contract.
No public action/result, supplied successor policy or durable flag is an input. -/
namespace DeltaReduce.ProfileSource.EcFinalization
open NativeReceiptBytes (Bytes)
open NativePolicyCodec (Value lookup)
open NativeVoteBytes (ascii)
open InputSection (Located)
open IscFinalization (replace otherFields insertBody signers)

/-- Resolve every finalized ID, then test the ORIGINAL ISC b of every resolved
witness. Unknown IDs and a second body/seed/view/witness for b fail closed. -/
def FirstFor (ecs : Eligibility.Bound) (b : Bytes) : Prop :=
  (∀ id ∈ ecs.finalized, ∃ row ∈ ecs.certificates, row.value.id = id) ∧
  ∀ row ∈ ecs.certificates, row.value.id ∈ ecs.finalized →
    row.value.certificate.common.isc ≠ b
instance (ecs b) : Decidable (FirstFor ecs b) := by unfold FirstFor; infer_instance

theorem existingFinalizedExcludesFirst {ecs b row}
    (member : row ∈ ecs.certificates) (finalized : row.value.id ∈ ecs.finalized)
    (same : row.value.certificate.common.isc = b) : ¬ FirstFor ecs b := by
  intro first
  exact first.2 row member finalized same

def sameWitnessTree (a b : Value) : Bool :=
  match NativeEligibilityLineage.decode .finalized [] a,
        NativeEligibilityLineage.decode .finalized [] b with
  | some left,some right => decide (left = right)
  | _,_ => false

theorem witnessTreeExact {a b} (same : sameWitnessTree a b = true) : a = b := by
  unfold sameWitnessTree at same
  split at same <;> try contradiction
  rename_i left right ha hb
  have eq : left = right := of_decide_eq_true same
  rcases left with ⟨c,seed⟩
  cases eq
  exact (NativeEligibilityLineage.decodedOriginal ha).trans
    (NativeEligibilityLineage.decodedOriginal hb).symm

/-- Existing equal e must contain the exact same EC AND seed sidecar. -/
def insertWitness (id : Bytes) (tree : Value) : List (Bytes × Value) → Option (List (Bytes × Value))
  | [] => some [(id,tree)]
  | (old,value)::rest =>
    if id = old then
      if sameWitnessTree tree value then some ((old,value)::rest) else none
    else if NativePolicyBytes.bytesLT id old then some ((id,tree)::(old,value)::rest)
    else do
      let tail ← insertWitness id tree rest
      some ((old,value)::tail)

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
      · cases Option.some.inj ok; simp
      · obtain ⟨tail,ht,last⟩ := Option.bind_eq_some_iff.mp ok
        cases Option.some.inj last
        exact List.mem_cons_of_mem _ (ih ht)

theorem differentWitnessCollision (id : Bytes) (old new : Value) (rest : List (Bytes × Value))
    (different : old ≠ new) : insertWitness id new ((id,old)::rest) = none := by
  rw [insertWitness,if_pos rfl]
  split
  · rename_i same
    exact False.elim (different (witnessTreeExact same).symm)
  · rfl

structure Update where
  snapshot : Value
  policy : Value
  raw : Bytes
  witnesses : List (Bytes × Value)
  finalized : List Bytes

def update (prior : NativePolicyBytes.Policy) (ecs : Eligibility.Bound)
    (certificate : Located Eligibility.Edge) : Option Update := do
  let old := ecs.certificates.map (fun x => (x.value.id,x.tree))
  let witnesses ← insertWitness certificate.value.id certificate.tree old
  let finalized := insertBody certificate.value.id ecs.finalized
  let first ← replace NativeHeader.snapshotFormat prior.snapshot "eligibility_certificates"
    (.items (witnesses.map Prod.snd))
  let snapshot ← replace NativeHeader.snapshotFormat first "finalized_eligibility_ids"
    (.items (finalized.map Value.text))
  let policy ← replace NativeHeader.policyFormat prior.source "snapshot" snapshot
  let raw ← NativeHeader.policyBytes policy
  some ⟨snapshot,policy,raw,witnesses,finalized⟩

theorem updateSource {prior ecs certificate out}
    (ok : update prior ecs certificate = some out) :
    ∃ first,
      insertWitness certificate.value.id certificate.tree
        (ecs.certificates.map (fun x => (x.value.id,x.tree))) = some out.witnesses ∧
      out.finalized = insertBody certificate.value.id ecs.finalized ∧
      replace NativeHeader.snapshotFormat prior.snapshot "eligibility_certificates"
        (.items (out.witnesses.map Prod.snd)) = some first ∧
      replace NativeHeader.snapshotFormat first "finalized_eligibility_ids"
        (.items (out.finalized.map Value.text)) = some out.snapshot ∧
      replace NativeHeader.policyFormat prior.source "snapshot" out.snapshot = some out.policy ∧
      NativeHeader.policyBytes out.policy = some out.raw := by
  simp only [update,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨w,hw,first,hf,snapshot,hs,policy,hp,raw,hr,last⟩ := ok
  cases Option.some.inj last
  exact ⟨first,hw,rfl,hf,hs,hp,hr⟩

theorem preservesOtherSnapshotFields {prior ecs certificate out}
    (ok : update prior ecs certificate = some out) (key : String)
    (notWitness : key ≠ "eligibility_certificates") (notFinal : key ≠ "finalized_eligibility_ids") :
    lookup NativeHeader.snapshotFormat out.snapshot key =
      lookup NativeHeader.snapshotFormat prior.snapshot key := by
  obtain ⟨first,_,_,hf,hs,_,_⟩ := updateSource ok
  exact (otherFields hs key notFinal).trans (otherFields hf key notWitness)

theorem preservesOuterFields {prior ecs certificate out}
    (ok : update prior ecs certificate = some out) (key : String) (notSnapshot : key ≠ "snapshot") :
    lookup NativeHeader.policyFormat out.policy key = lookup NativeHeader.policyFormat prior.source key := by
  obtain ⟨first,_,_,_,_,hp,_⟩ := updateSource ok
  exact otherFields hp key notSnapshot

theorem allOriginalLineageRetained {prior ecs certificate out}
    (ok : update prior ecs certificate = some out) :
    (ecs.certificates.map (fun x => (x.value.id,x.tree))).Sublist out.witnesses ∧
    ecs.finalized.Sublist out.finalized ∧
    (certificate.value.id,certificate.tree) ∈ out.witnesses ∧
    certificate.value.id ∈ out.finalized := by
  obtain ⟨first,hw,hb,_,_,_,_⟩ := updateSource ok
  exact ⟨originalWitnessesRetained hw,by rw [hb]; exact IscFinalization.originalFinalizedRetained _ _,
    selectedWitnessRetained hw,by rw [hb]; exact IscFinalization.selectedBodyRetained _ _⟩

def Guards (prior : InstalledState.Bound) (actor : Bytes) (tick : Nat)
    (body : Located Eligibility.Edge) : Prop :=
  let p := prior.installed.policy
  let s := prior.installed.header.state
  p.localValidator = actor ∧ p.config ∈ prior.collections.finalizedConfigs ∧
  p.initialTick ≤ tick ∧ tick < p.hardDeadline ∧
  s.phase ≠ ascii "AGGREGATED" ∧ s.phase ≠ ascii "ABORTED" ∧
  prior.collections.tail.aborts.isEmpty = true ∧
  FirstFor prior.collections.eligibility body.value.certificate.common.isc
instance (prior actor tick body) : Decidable (Guards prior actor tick body) := by
  unfold Guards; infer_instance

structure Candidate where
  selected : Located Eligibility.Edge
  certificate : Located Eligibility.Edge
  quorum : CertificateVotes.Bound
  update : Update

/-- Compute S from ALL original matching admitted rows at this cut; never
select first-q or reconstruct a witness from a later snapshot cut. -/
def bodyTarget (sha : Bytes → Bytes) (sigma : Bytes)
    (body : Located Eligibility.Edge) : Option CertificateVotes.Target := do
  let b := body.value
  let id ← NativeEligibility.bodyId sha ⟨b.certificate.common,b.seedId⟩
  let context ← Candidates.parentContext sha "deltareduce.vote-context.ec.v1" b.certificate.common.isc
  if id = b.id ∧ body.raw = NativeEligibility.bodyBytes ⟨b.certificate.common,b.seedId⟩ then
    some ⟨ascii "EC",sigma,b.certificate.common.context,context,id,[],[],[],3⟩
  else none

def assemble (sha : Bytes → Bytes) (prior : InstalledState.Bound) (actor : Bytes)
    (cut tick : Nat) (bodyId : Bytes) (rows : List ConfigurationQC.Received) : Option Candidate := do
  let p := prior.installed.policy
  let s := prior.installed.header.state
  let ecs := prior.collections.eligibility
  let selected ← ecs.bodies.find? (fun row => row.value.id == bodyId)
  if Guards prior actor tick selected then
    let target ← bodyTarget sha s.semantics selected
    let names := signers p.validators (CertificateVotes.matching actor cut target rows)
    let c : NativeEligibility.Certificate := ⟨selected.value.certificate.common,3,names⟩
    let tree := NativeEligibilityLineage.original .finalized c selected.value.seedId
    let raw := Eligibility.bytes s.semantics .finalized c selected.value.seedId
    let edge ← Eligibility.bind sha s.semantics .finalized prior.collections.context p.validators
      ecs.lineage tree raw
    let certificate : Located Eligibility.Edge := ⟨tree,raw,edge⟩
    let full ← CertificateVotes.ec sha s.semantics certificate
    let quorum ← CertificateVotes.bind p.validators actor cut full rows
    let following ← update p ecs certificate
    some ⟨selected,certificate,quorum,following⟩
  else none

structure Source (sha : Bytes → Bytes) (prior : InstalledState.Bound) (actor : Bytes)
    (cut tick : Nat) (bodyId : Bytes) (rows : List ConfigurationQC.Received) (out : Candidate) where
  target : CertificateVotes.Target
  full : CertificateVotes.Target
  selected : prior.collections.eligibility.bodies.find? (fun row => row.value.id == bodyId) = some out.selected
  guards : Guards prior actor tick out.selected
  targetComputed : bodyTarget sha prior.installed.header.state.semantics out.selected = some target
  certificateComputed :
    let names := signers prior.installed.policy.validators (CertificateVotes.matching actor cut target rows)
    let c : NativeEligibility.Certificate := ⟨out.selected.value.certificate.common,3,names⟩
    out.certificate.tree = NativeEligibilityLineage.original .finalized c out.selected.value.seedId ∧
    out.certificate.raw = Eligibility.bytes prior.installed.header.state.semantics .finalized c out.selected.value.seedId ∧
    Eligibility.bind sha prior.installed.header.state.semantics .finalized prior.collections.context
      prior.installed.policy.validators prior.collections.eligibility.lineage
      out.certificate.tree out.certificate.raw = some out.certificate.value
  fullTarget : CertificateVotes.ec sha prior.installed.header.state.semantics out.certificate = some full
  quorum : CertificateVotes.bind prior.installed.policy.validators actor cut full rows = some out.quorum
  updated : update prior.installed.policy prior.collections.eligibility out.certificate = some out.update

theorem assembled {sha prior actor cut tick bodyId rows out}
    (ok : assemble sha prior actor cut tick bodyId rows = some out) :
    Nonempty (Source sha prior actor cut tick bodyId rows out) := by
  unfold assemble at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨selected,hs,last⟩ := ok
  split at last <;> try contradiction
  rename_i guards
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨target,ht,edge,he,full,hf,quorum,hq,next,hn,last⟩ := last
  cases Option.some.inj last
  exact ⟨⟨target,full,hs,guards,ht,⟨rfl,rfl,he⟩,hf,hq,hn⟩⟩

theorem assembleComplete {sha prior actor cut tick bodyId rows out}
    (h : Source sha prior actor cut tick bodyId rows out) :
    assemble sha prior actor cut tick bodyId rows = some out := by
  unfold assemble
  dsimp only
  rw [h.selected]
  dsimp only [Bind.bind,Option.bind]
  rw [if_pos h.guards,h.targetComputed]
  dsimp only
  have hc := h.certificateComputed.2.2
  rw [h.certificateComputed.1,h.certificateComputed.2.1] at hc
  rw [hc]
  dsimp only
  rw [← h.certificateComputed.1,← h.certificateComputed.2.1]
  rw [h.fullTarget]
  dsimp only
  rw [h.quorum]
  dsimp only
  rw [h.updated]

theorem exactComputedWitness {sha prior actor cut tick bodyId rows out}
    (ok : assemble sha prior actor cut tick bodyId rows = some out) :
    ∃ target, bodyTarget sha prior.installed.header.state.semantics out.selected = some target ∧
      out.certificate.value.certificate.common = out.selected.value.certificate.common ∧
      out.certificate.value.certificate.threshold = 3 ∧
      out.certificate.value.certificate.signers = signers prior.installed.policy.validators
        (CertificateVotes.matching actor cut target rows) ∧
      out.certificate.value.seedId = out.selected.value.seedId := by
  obtain ⟨h⟩ := assembled ok
  have parsed := (Eligibility.boundSource h.certificateComputed.2.2).decoded
  rw [h.certificateComputed.1] at parsed
  simp only [NativeEligibilityLineage.original,NativeEligibilityLineage.decode,
    NativeEligibility.valueRead,Bind.bind,Option.bind] at parsed
  have same := Option.some.inj parsed
  have cert := congrArg Prod.fst same
  have seed := congrArg Prod.snd same
  dsimp only at cert seed
  refine ⟨h.target,h.targetComputed,?_,?_,?_,seed.symm⟩
  · rw [← cert]
  · rw [← cert]
  · rw [← cert]

theorem firstAtOriginalKey {sha prior actor cut tick bodyId rows out}
    (ok : assemble sha prior actor cut tick bodyId rows = some out) :
    FirstFor prior.collections.eligibility out.selected.value.certificate.common.isc := by
  obtain ⟨h⟩ := assembled ok
  exact h.guards.2.2.2.2.2.2.2

theorem allDeliveredOriginalsRetained {sha prior actor cut tick bodyId rows out}
    (ok : assemble sha prior actor cut tick bodyId rows = some out) : out.quorum.originalRows = rows := by
  obtain ⟨h⟩ := assembled ok
  exact (CertificateVotes.boundSource h.quorum).2.1

theorem unchangedLineage {sha prior actor cut tick bodyId rows out}
    (ok : assemble sha prior actor cut tick bodyId rows = some out) (key : String)
    (notWitness : key ≠ "eligibility_certificates") (notFinal : key ≠ "finalized_eligibility_ids") :
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
    (rows : List ConfigurationQC.Received) : Option Original := do
  let prior ← InstalledState.bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals
  let candidate ← assemble sha prior actor cut tick bodyId rows
  some ⟨prior,candidate⟩

theorem originalBefore {sha enrolled actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId rows out}
    (ok : fromBytes sha enrolled actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows = some out) :
    InstalledState.bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out.before ∧
    assemble sha out.before actor cut tick bodyId rows = some out.candidate := by
  simp only [fromBytes,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨prior,hp,candidate,hc,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hp,hc⟩

/-- The whole successor is checked using COMPUTED original EC bytes, not a
supplied post-policy or a successful public representation. -/
def successorOriginals (sigma : Bytes) (originals : Collections.Originals)
    (candidate : Candidate) : Option Collections.Originals := do
  let raws ← Index.collect (fun pair => do
    let (certificate,seed) ← NativeEligibilityLineage.decode .finalized [] pair.2
    some (Eligibility.bytes sigma .finalized certificate seed)) candidate.update.witnesses
  some { originals with eligibilityCertificates := raws }

structure Whole where
  source : Original
  successorOriginals : Collections.Originals
  following : InstalledState.Bound

def checkWhole (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) (cut tick : Nat) (bodyId : Bytes)
    (rows : List ConfigurationQC.Received) : Option Whole := do
  let source ← fromBytes sha enrolled actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId rows
  let nextRaws ← successorOriginals source.before.installed.header.state.semantics originals source.candidate
  let following ← InstalledState.bind sha enrolled actor configRaw stateRaw
    source.candidate.update.raw stateValue nextRaws
  some ⟨source,nextRaws,following⟩

theorem wholeNativeStateChecked {sha enrolled actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId rows out}
    (ok : checkWhole sha enrolled actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows = some out) :
    fromBytes sha enrolled actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows = some out.source ∧
    successorOriginals out.source.before.installed.header.state.semantics originals
      out.source.candidate = some out.successorOriginals ∧
    InstalledState.bind sha enrolled actor configRaw stateRaw out.source.candidate.update.raw
      stateValue out.successorOriginals = some out.following := by
  simp only [checkWhole,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨source,hs,nextRaws,hr,following,hf,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hs,hr,hf⟩

/- Origins of these positions belong to the independent full history fold.
The union is recomputed from all matching admitted rows; an event cannot omit
a duplicate occurrence or fourth signer by shortening its own dependency list. -/
/-- Structural ordered-set insertion keeps the kernel computation transparent;
the original event inventory itself is never converted to a set. -/
def insertPosition (position : Nat) : List Nat → List Nat
  | [] => [position]
  | head::rest =>
    if position = head then head::rest
    else if position < head then position::head::rest
    else head::insertPosition position rest

theorem insertedPositionMembership (position n : Nat) (old : List Nat) :
    n ∈ insertPosition position old ↔ n = position ∨ n ∈ old := by
  induction old with
  | nil => simp [insertPosition]
  | cons head rest ih =>
    simp only [insertPosition]
    split
    · rename_i same
      subst position
      simp
    · split <;> simp_all [List.mem_cons,or_left_comm]

theorem insertedPositionSorted (position : Nat) (old : List Nat) :
    old.Pairwise (· < ·) → (insertPosition position old).Pairwise (· < ·) := by
  induction old with
  | nil => simp [insertPosition]
  | cons head rest ih =>
    intro sorted
    obtain ⟨before,tail⟩ := List.pairwise_cons.mp sorted
    simp only [insertPosition]
    split
    · exact sorted
    · rename_i different
      split
      · rename_i earlier
        apply List.pairwise_cons.mpr
        refine ⟨?_,sorted⟩
        intro n member
        rcases List.mem_cons.mp member with same | member
        · simpa [same] using earlier
        · exact Nat.lt_trans earlier (before n member)
      · rename_i later
        apply List.pairwise_cons.mpr
        refine ⟨?_,ih tail⟩
        intro n member
        rcases (insertedPositionMembership position n rest).mp member with same | member
        · omega
        · exact before n member

def orderedUnion (positions : List Nat) : List Nat := positions.foldr insertPosition []

theorem orderedUnionSorted (positions : List Nat) :
    (orderedUnion positions).Pairwise (· < ·) := by
  induction positions with
  | nil => simp [orderedUnion]
  | cons head rest ih => exact insertedPositionSorted head _ ih

theorem orderedUnionMembership (n : Nat) (positions : List Nat) :
    n ∈ orderedUnion positions ↔ n ∈ positions := by
  induction positions with
  | nil => simp [orderedUnion]
  | cons head rest ih =>
    simp only [orderedUnion,List.foldr_cons,insertedPositionMembership]
    simpa only [orderedUnion,List.mem_cons] using (or_congr Iff.rfl ih)

def dependencyUnion (origins : List Nat) (rows : List ConfigurationQC.Received) : List Nat :=
  orderedUnion (origins ++ rows.map ConfigurationQC.Received.position)

theorem dependenciesAreExactlyOriginalPositions (n : Nat) (origins : List Nat)
    (rows : List ConfigurationQC.Received) :
    n ∈ dependencyUnion origins rows ↔
      n ∈ origins ∨ ∃ row ∈ rows, row.position = n := by
  simp only [dependencyUnion,orderedUnionMembership,List.mem_append,List.mem_map]

def EventChecks (event : Index.Event) (source : Original) (policyRaw stateRaw : Bytes)
    (actor : Bytes) (cut : Nat) (origins : List Nat) : Prop :=
  let c := source.candidate
  event.action = ascii "ACT-EC-FINALIZE" ∧ event.actor = actor ∧
  event.position = cut + 1 ∧ event.original = c.certificate.raw ∧
  (∃ originalParent ∈ source.before.collections.eligibility.lineage.inputs.certificates,
    originalParent.value.consensusId = c.selected.value.certificate.common.isc ∧
    event.inputs = [policyRaw,stateRaw,c.selected.raw,originalParent.raw,
      c.selected.value.seed.raw,c.selected.value.norm.raw]) ∧
  (∀ i ∈ origins, i < event.position) ∧
  event.dependencies = dependencyUnion origins c.quorum.matchingRows
instance (e s p st a c o) : Decidable (EventChecks e s p st a c o) := by
  unfold EventChecks; infer_instance

def bindEvent (event : Index.Event) (source : Whole) (policyRaw stateRaw : Bytes)
    (actor : Bytes) (cut : Nat) (origins : List Nat) : Option Whole :=
  if EventChecks event source.source policyRaw stateRaw actor cut origins then some source else none

theorem originalEventChecked {event source policyRaw stateRaw actor cut origins out}
    (ok : bindEvent event source policyRaw stateRaw actor cut origins = some out) :
    out = source ∧ EventChecks event source.source policyRaw stateRaw actor cut origins := by
  unfold bindEvent at ok
  split at ok <;> try contradiction
  rename_i checks
  cases Option.some.inj ok
  exact ⟨rfl,checks⟩

/-- Re-observation checks the exact witness AND seed derived at the original
cut. Its only result is the current state, including later ABORT/lineage. The
enclosing fold still establishes that this is the original producing event. -/
def Retained (original : Whole) (current : InstalledState.Bound) : Prop :=
  let old := original.source.candidate.certificate
  old.value.id ∈ current.collections.eligibility.finalized ∧
  ∃ row ∈ current.collections.eligibility.certificates,
    row.value.id = old.value.id ∧ row.raw = old.raw ∧ sameWitnessTree row.tree old.tree = true
instance (o c) : Decidable (Retained o c) := by unfold Retained; infer_instance

def replay (original : Whole) (current : InstalledState.Bound) : Option InstalledState.Bound :=
  if Retained original current then some current else none

theorem replayStutters {original current out} (ok : replay original current = some out) :
    out = current ∧ Retained original current := by
  unfold replay at ok
  split at ok <;> try contradiction
  rename_i retained
  cases Option.some.inj ok
  exact ⟨rfl,retained⟩

theorem replayExactSeedAndWitness {original current out}
    (ok : replay original current = some out) :
    ∃ row ∈ out.collections.eligibility.certificates,
      row.tree = original.source.candidate.certificate.tree ∧
      row.raw = original.source.candidate.certificate.raw := by
  obtain ⟨same,retained⟩ := replayStutters ok
  subst out
  obtain ⟨row,hm,_,hr,ht⟩ := retained.2
  exact ⟨row,hm,witnessTreeExact ht,hr⟩

/-- Recompute the old cut, not a new arrival cut. Both full native states are
decoded independently. No supplied success flag/P1/public representation. -/
def checkReplay (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw oldStateRaw oldPolicyRaw : Bytes) (oldState : Value)
    (oldOriginals : Collections.Originals) (cut tick : Nat) (bodyId : Bytes)
    (oldRows : List ConfigurationQC.Received) (event : Index.Event) (origins : List Nat)
    (currentStateRaw currentPolicyRaw : Bytes) (currentState : Value)
    (currentOriginals : Collections.Originals) : Option InstalledState.Bound := do
  let original ← checkWhole sha enrolled actor configRaw oldStateRaw oldPolicyRaw oldState
    oldOriginals cut tick bodyId oldRows
  let bound ← bindEvent event original oldPolicyRaw oldStateRaw actor cut origins
  let current ← InstalledState.bind sha enrolled actor configRaw currentStateRaw currentPolicyRaw
    currentState currentOriginals
  replay bound current

theorem replayOriginalCut {sha enrolled actor configRaw oldStateRaw oldPolicyRaw oldState oldOriginals
    cut tick bodyId oldRows event origins currentStateRaw currentPolicyRaw currentState currentOriginals out}
    (ok : checkReplay sha enrolled actor configRaw oldStateRaw oldPolicyRaw oldState oldOriginals
      cut tick bodyId oldRows event origins currentStateRaw currentPolicyRaw currentState
      currentOriginals = some out) :
    ∃ original,
      checkWhole sha enrolled actor configRaw oldStateRaw oldPolicyRaw oldState oldOriginals
        cut tick bodyId oldRows = some original ∧
      EventChecks event original.source oldPolicyRaw oldStateRaw actor cut origins ∧
      InstalledState.bind sha enrolled actor configRaw currentStateRaw currentPolicyRaw
        currentState currentOriginals = some out ∧ Retained original out := by
  simp only [checkReplay,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨original,ho,bound,hb,current,hc,last⟩ := ok
  obtain ⟨same,he⟩ := originalEventChecked hb
  subst bound
  obtain ⟨same,retained⟩ := replayStutters last
  subst out
  exact ⟨original,ho,he,hc,retained⟩

end DeltaReduce.ProfileSource.EcFinalization
