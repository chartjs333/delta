import ProfilePolicy

/-! T047/T053. Original successor ISC collections. Consensus body b and original
certificate witness c stay separate, including multiple witnesses of one body.
This source join does not infer a historical context, signature, first-finalize
event or durability from a well-formed certificate. No public state is an input. -/
namespace DeltaReduce.ProfileSource.InputSection
open NativeReceiptBytes NativePolicyCodec
open NativePolicyBytes (Policy)
open NativeInputSetBody (Context)
open ISCSourceV2

structure Located (α : Type) where
  tree : Value
  raw : Bytes
  value : α

def collect {α : Type} (parse : Value → Bytes → Option α) :
    List Value → List Bytes → Option (List (Located α))
  | [],[] => some []
  | t::ts,r::rs => do
      let v ← parse t r
      let rest ← collect parse ts rs
      some (⟨t,r,v⟩::rest)
  | _,_ => none

theorem collectedOriginals {α} {parse : Value → Bytes → Option α} {ts rs out}
    (ok : collect parse ts rs = some out) :
    out.map Located.tree = ts ∧ out.map Located.raw = rs := by
  induction ts generalizing rs out with
  | nil => cases rs <;> simp [collect] at ok; subst out; exact ⟨rfl,rfl⟩
  | cons t ts ih =>
    cases rs with
    | nil => simp [collect] at ok
    | cons r rs =>
      simp only [collect,Bind.bind,Option.bind_eq_some_iff] at ok
      obtain ⟨v,hv,rest,hr,last⟩ := ok
      cases Option.some.inj last
      exact ⟨by simp [ih hr],by simp [ih hr]⟩

theorem collectedEach {α} {parse : Value → Bytes → Option α} {ts rs out}
    (ok : collect parse ts rs = some out) (row : Located α) (member : row ∈ out) :
    parse row.tree row.raw = some row.value := by
  induction ts generalizing rs out with
  | nil => cases rs <;> simp [collect] at ok; subst out; simp at member
  | cons t ts ih =>
    cases rs with
    | nil => simp [collect] at ok
    | cons r rs =>
      simp only [collect,Bind.bind,Option.bind_eq_some_iff] at ok
      obtain ⟨v,hv,rest,hr,last⟩ := ok
      cases Option.some.inj last
      rcases List.mem_cons.mp member with same | member
      · cases same; exact hv
      · exact ih hr member

theorem collectComplete {α} {parse : Value → Bytes → Option α} (out : List (Located α))
    (all : ∀ row ∈ out, parse row.tree row.raw = some row.value) :
    collect parse (out.map Located.tree) (out.map Located.raw) = some out := by
  induction out with
  | nil => rfl
  | cons row rest ih =>
    simp only [List.map_cons,collect,all row (by simp),Bind.bind,Option.bind]
    rw [ih (fun x hx => all x (by simp [hx]))]

structure BodyRow where
  body : Body
  consensusId : Bytes

def bindBody (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (parent : Bytes) (tree : Value) (raw : Bytes) : Option BodyRow := do
  let b ← readBody tree
  if NativeVoteBytes.ContentId sigma ∧ BodyShape expected parent b ∧
      raw = bodyBytes sigma b ∧ inputRoot sha b.tuples = some b.root then
    let id ← bodyId sha sigma b
    some ⟨b,id⟩
  else none

theorem bodySource {sha sigma expected parent tree raw out}
    (ok : bindBody sha sigma expected parent tree raw = some out) :
    tree = bodyValue out.body ∧ NativeVoteBytes.ContentId sigma ∧
    BodyShape expected parent out.body ∧ raw = bodyBytes sigma out.body ∧
    inputRoot sha out.body.tuples = some out.body.root ∧
    bodyId sha sigma out.body = some out.consensusId := by
  unfold bindBody at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨b,hb,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at ok
  obtain ⟨id,hi,last⟩ := ok
  cases Option.some.inj last
  exact ⟨bodyOriginal hb,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2,hi⟩

theorem bodyComplete {sha sigma expected parent tree raw b id}
    (parsed : readBody tree = some b) (semantic : NativeVoteBytes.ContentId sigma)
    (shape : BodyShape expected parent b) (original : raw = bodyBytes sigma b)
    (root : inputRoot sha b.tuples = some b.root) (hashed : bodyId sha sigma b = some id) :
    bindBody sha sigma expected parent tree raw = some ⟨b,id⟩ := by
  simp [bindBody,parsed,semantic,shape,original,root,hashed]

def trees (p : Policy) (key : String) : Option (List Value) :=
  lookup NativeHeader.snapshotFormat p.snapshot key >>= NativePolicyBytes.items

def ids (p : Policy) (key : String) : Option (List Bytes) := do
  let values ← trees p key
  values.mapM NativePolicyBytes.text

structure Bound where
  bodies : List (Located BodyRow)
  certificates : List (Located BoundCertificate)
  closed : List Bytes
  finalized : List Bytes

def BodyIds (b : Bound) := b.bodies.map (fun x => x.value.consensusId)
def WitnessIds (b : Bound) := b.certificates.map (fun x => x.value.witnessId)
def RepresentedBodies (b : Bound) := b.certificates.map (fun x => x.value.consensusId)

def SetChecks (b : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (BodyIds b) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (WitnessIds b) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.closed = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.finalized = true ∧
  (∀ id ∈ b.closed, id ∈ BodyIds b) ∧
  (∀ id ∈ b.finalized, id ∈ RepresentedBodies b)
instance (b) : Decidable (SetChecks b) := by unfold SetChecks; infer_instance

/-- At a specified original context, collect every original body and witness.
The enclosing producing-history join supplies the context of that source cut;
it must not silently replace old certificate views by the current view. -/
def bindAt (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (parent : Bytes) (p : Policy) (bodyRaws certificateRaws : List Bytes) : Option Bound := do
  let bodyTrees ← trees p "input_set_bodies"
  let bodies ← collect (bindBody sha sigma expected parent) bodyTrees bodyRaws
  let certificateTrees ← trees p "input_set_certificates"
  let certificates ← collect (bindCertificate sha sigma expected parent p.validators)
    certificateTrees certificateRaws
  let closed ← ids p "closed_input_set_ids"
  let finalized ← ids p "finalized_input_set_ids"
  let b := Bound.mk bodies certificates closed finalized
  if SetChecks b then some b else none

structure Source (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (parent : Bytes) (p : Policy) (bodyRaws certificateRaws : List Bytes) (b : Bound) : Prop where
  bodies : trees p "input_set_bodies" = some (b.bodies.map Located.tree)
  bodyBytes : b.bodies.map Located.raw = bodyRaws
  bodySource : ∀ row ∈ b.bodies, bindBody sha sigma expected parent row.tree row.raw = some row.value
  certificates : trees p "input_set_certificates" = some (b.certificates.map Located.tree)
  certificateBytes : b.certificates.map Located.raw = certificateRaws
  certificateSource : ∀ row ∈ b.certificates,
    bindCertificate sha sigma expected parent p.validators row.tree row.raw = some row.value
  closed : ids p "closed_input_set_ids" = some b.closed
  finalized : ids p "finalized_input_set_ids" = some b.finalized
  sets : SetChecks b

theorem boundSource {sha sigma expected parent p bodyRaws certificateRaws b}
    (ok : bindAt sha sigma expected parent p bodyRaws certificateRaws = some b) :
    Source sha sigma expected parent p bodyRaws certificateRaws b := by
  unfold bindAt at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨bt,hbt,bs,hbs,ct,hct,cs,hcs,closed,hclosed,finalized,hfinal,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  have bodies := collectedOriginals hbs
  have certs := collectedOriginals hcs
  exact ⟨by simpa only [bodies.1] using hbt,bodies.2,collectedEach hbs,
    by simpa only [certs.1] using hct,certs.2,collectedEach hcs,hclosed,hfinal,checks⟩

theorem boundComplete {sha sigma expected parent p bodyRaws certificateRaws b}
    (h : Source sha sigma expected parent p bodyRaws certificateRaws b) :
    bindAt sha sigma expected parent p bodyRaws certificateRaws = some b := by
  unfold bindAt
  rw [h.bodies,← h.bodyBytes]
  simp only [collectComplete b.bodies h.bodySource,Bind.bind,Option.bind]
  rw [h.certificates,← h.certificateBytes]
  simp only [collectComplete b.certificates h.certificateSource]
  rw [h.closed,h.finalized]
  exact if_pos h.sets

theorem finalizedBodyWitness {sha sigma expected parent p bodyRaws certificateRaws b id}
    (ok : bindAt sha sigma expected parent p bodyRaws certificateRaws = some b)
    (member : id ∈ b.finalized) :
    ∃ row ∈ b.certificates, row.value.consensusId = id ∧
      CertificateSource sha sigma expected parent p.validators row.tree row.raw row.value := by
  have src := boundSource ok
  obtain ⟨row,mem,eq⟩ := List.mem_map.mp (src.sets.2.2.2.2.2 id member)
  exact ⟨row,mem,eq,boundCertificateSource (src.certificateSource row mem)⟩

theorem closedOriginalBody {sha sigma expected parent p bodyRaws certificateRaws b id}
    (ok : bindAt sha sigma expected parent p bodyRaws certificateRaws = some b)
    (member : id ∈ b.closed) :
    ∃ row ∈ b.bodies, row.value.consensusId = id ∧
      row.tree = bodyValue row.value.body ∧ row.raw = bodyBytes sigma row.value.body := by
  have src := boundSource ok
  obtain ⟨row,mem,eq⟩ := List.mem_map.mp (src.sets.2.2.2.2.1 id member)
  have body := bodySource (src.bodySource row mem)
  exact ⟨row,mem,eq,body.1,body.2.2.2.1⟩

theorem originalCounts {sha sigma expected parent p bodyRaws certificateRaws b}
    (ok : bindAt sha sigma expected parent p bodyRaws certificateRaws = some b) :
    b.bodies.length = bodyRaws.length ∧ b.certificates.length = certificateRaws.length := by
  have src := boundSource ok
  exact ⟨by simpa using congrArg List.length src.bodyBytes,
    by simpa using congrArg List.length src.certificateBytes⟩

theorem sameBodySameConsensusId {sha sigma expected parent p bodyRaws certificateRaws b a c}
    (ok : bindAt sha sigma expected parent p bodyRaws certificateRaws = some b)
    (ha : a ∈ b.certificates) (hc : c ∈ b.certificates)
    (same : a.value.certificate.body = c.value.certificate.body) :
    a.value.consensusId = c.value.consensusId := by
  have src := boundSource ok
  have first := boundCertificateSource (src.certificateSource a ha)
  have second := boundCertificateSource (src.certificateSource c hc)
  have hb := first.body
  rw [same] at hb
  exact Option.some.inj (hb.symm.trans second.body)

theorem witnessCannotReplaceBody {sha sigma expected parent p bodyRaws certificateRaws b id}
    (ok : bindAt sha sigma expected parent p bodyRaws certificateRaws = some b)
    (missingBody : id ∉ RepresentedBodies b) : id ∉ b.finalized :=
  fun mem => missingBody ((boundSource ok).sets.2.2.2.2.2 id mem)

theorem cannotHideOriginalWitness {sha sigma expected parent p bodyRaws certificateRaws b}
    (ok : bindAt sha sigma expected parent p bodyRaws certificateRaws = some b) :
    b.certificates.map (fun row => row.value.originalBytes) = certificateRaws := by
  have src := boundSource ok
  rw [← src.certificateBytes]
  apply List.map_congr_left
  intro row mem
  exact (boundCertificateSource (src.certificateSource row mem)).bytesExact

end DeltaReduce.ProfileSource.InputSection
