import Std
import DeltaReduce.ParameterKernel

/-!
PO-AB1 graph layer. Two independently supplied stores may not resolve different
typed arithmetic graphs from one authenticated authority reference. This is an
ordered, recursively complete graph relation, not equality of a pure function's
two calls. It makes no assumption of graph/result uniqueness.

The codec is an explicit parameter: instantiating it with the bounded canonical
ASCII decoder, and authenticating the native anchor/certificates/recovery, remain
separate refinement obligations. Collision freedom on accepted canonical bytes
is a named cryptographic premise, not a proved property of SHA-256. Content IDs
are byte lists; the native sha256:hex spelling needs its concrete adapter proof.
The payloads mirror native_binding.py. The later checked extraction layer proves
PARAMETER body soundness; certified conversion/Apply/recovery remain open.
-/
namespace DeltaReduce.NativeBinding

abbrev Bytes := List UInt8
abbrev ContentId := Bytes

inductive Kind where
  | authority | schema | profile | plan | model | optimizer
  | isc | ec | apc | qShard | aggregate
  deriving DecidableEq, Repr

structure Ref where
  id : ContentId
  kind : Kind
  length : Nat
  deriving DecidableEq, Repr

structure Rational where
  numerator : Int
  denominator : Int
  deriving DecidableEq, Repr

structure Context where
  round : String
  height : Nat
  view : Nat
  epoch : String
  hardDeadline : Nat
  parentCheckpoint : String
  deriving DecidableEq, Repr

structure Authority where
  context : Context
  schema : Ref
  profile : Ref
  plan : Ref
  model : Ref
  optimizer : Ref
  isc : Ref
  ec : Ref
  apc : Ref
  deriving DecidableEq, Repr

structure Shard where
  id : String
  offset : Nat
  length : Nat
  deriving DecidableEq, Repr

structure DomainWeight where
  domain : String
  weight : Rational
  deriving DecidableEq, Repr

structure Profile where
  accumulatorBits : Nat
  applyQuantum : Rational
  domainWeights : List DomainWeight
  learningRate : Rational
  momentum : Rational
  weightDecay : Rational
  rounding : String
  nesterov : Bool
  outputRange : String
  deriving DecidableEq, Repr

structure StateVector where
  schema : Ref
  quantum : Rational
  values : List Int
  deriving DecidableEq, Repr

structure Ticket where
  id : String
  domain : String
  deriving DecidableEq, Repr

structure Contribution where
  ticket : String
  weight : Rational
  q : Ref
  deriving DecidableEq, Repr

structure Assignment where
  domain : String
  shard : String
  context : String
  denominator : Int
  quantum : Rational
  contributions : List Contribution
  deriving DecidableEq, Repr

structure Plan where
  schema : Ref
  profile : Ref
  tickets : List Ticket
  assignments : List Assignment
  deriving DecidableEq, Repr

structure Leaf where
  shard : String
  q : Ref
  deriving DecidableEq, Repr

structure Commitment where
  ticket : String
  domain : String
  leaves : List Leaf
  deriving DecidableEq, Repr

structure QShard where
  ticket : String
  domain : String
  shard : String
  schema : Ref
  quantum : Rational
  values : List Int
  deriving DecidableEq, Repr

structure ParameterBody where
  kind : String
  authorityId : ContentId
  context : String
  domain : String
  shard : String
  denominator : Int
  numerators : List Int
  inputLeafIds : List ContentId
  deriving DecidableEq, Repr

inductive Payload where
  | authority (value : Authority)
  | schema (coordinates : List String) (shards : List Shard)
  | profile (value : Profile)
  | plan (value : Plan)
  | model (value : StateVector)
  | optimizer (value : StateVector)
  | isc (members : List String) (commitments : List Commitment)
  | ec (isc : Ref) (eligible : List String)
  | apc (ec : Ref) (plan : Ref)
  | qShard (value : QShard)
  | aggregate (authorityId : ContentId) (parameters : List ParameterBody)
  deriving DecidableEq, Repr

def Payload.kind : Payload → Kind
  | .authority _ => .authority
  | .schema _ _ => .schema
  | .profile _ => .profile
  | .plan _ => .plan
  | .model _ => .model
  | .optimizer _ => .optimizer
  | .isc _ _ => .isc
  | .ec _ _ => .ec
  | .apc _ _ => .apc
  | .qShard _ => .qShard
  | .aggregate _ _ => .aggregate

/-- Named field order, then original list order. No store iteration or sorting
of observed values defines the edges. Aggregate parameters are inline bodies;
their IDs are checked against the authority graph by the arithmetic layer. -/
def Payload.edges : Payload → List (Kind × Ref)
  | .authority a => [(.schema, a.schema), (.profile, a.profile), (.plan, a.plan),
      (.model, a.model), (.optimizer, a.optimizer), (.isc, a.isc), (.ec, a.ec), (.apc, a.apc)]
  | .plan p => [(.schema, p.schema), (.profile, p.profile)] ++
      p.assignments.flatMap (fun a => a.contributions.map (fun c => (.qShard, c.q)))
  | .model s | .optimizer s => [(.schema, s.schema)]
  | .isc _ commitments => commitments.flatMap
      (fun c => c.leaves.map (fun leaf => (.qShard, leaf.q)))
  | .ec iscRef _ => [(.isc, iscRef)]
  | .apc ecRef planRef => [(.ec, ecRef), (.plan, planRef)]
  | .qShard q => [(.schema, q.schema)]
  | .schema _ _ | .profile _ | .aggregate _ _ => []

def Payload.refs (payload : Payload) : List Ref := payload.edges.map Prod.snd

def Payload.wellTypedEdges (payload : Payload) : Prop :=
  ∀ edge ∈ payload.edges, edge.2.kind = edge.1

instance (payload : Payload) : Decidable payload.wellTypedEdges :=
  inferInstanceAs (Decidable (∀ edge ∈ payload.edges, edge.2.kind = edge.1))

structure Codec where
  hash : Bytes → ContentId
  canonical : Bytes → Bool
  decode : Bytes → Option Payload
  valueHash : Kind → List Int → ContentId

abbrev Store := ContentId → Option Bytes

/-- Explicit external collision-resistance premise, scoped to canonical inputs. -/
def CollisionFree (codec : Codec) : Prop :=
  ∀ a b, codec.canonical a = true → codec.canonical b = true →
    codec.hash a = codec.hash b → a = b

structure Resolves (codec : Codec) (store : Store) (ref : Ref)
    (bytes : Bytes) (payload : Payload) : Prop where
  present : store ref.id = some bytes
  content : codec.hash bytes = ref.id
  length : bytes.length = ref.length
  canonical : codec.canonical bytes = true
  decoded : codec.decode bytes = some payload
  kind : payload.kind = ref.kind
  typed : payload.wellTypedEdges

/-- Within one observed store, lookup and decoding fix the witness without a
cryptographic assumption. Useful for concrete rejected/missing-node examples. -/
theorem resolvedAtPresentBytes {codec : Codec} {store : Store} {ref : Ref}
    {knownBytes bytes : Bytes} {knownPayload payload : Payload}
    (present : store ref.id = some knownBytes)
    (decoded : codec.decode knownBytes = some knownPayload)
    (resolved : Resolves codec store ref bytes payload) :
    bytes = knownBytes ∧ payload = knownPayload := by
  have sameBytes := Option.some.inj (resolved.present.symm.trans present)
  subst sameBytes
  exact ⟨rfl, Option.some.inj (resolved.decoded.symm.trans decoded)⟩

theorem resolvedBytesAndPayloadUnique {codec : Codec} (collisionFree : CollisionFree codec)
    {leftStore rightStore : Store} {ref : Ref} {leftBytes rightBytes : Bytes}
    {leftPayload rightPayload : Payload}
    (left : Resolves codec leftStore ref leftBytes leftPayload)
    (right : Resolves codec rightStore ref rightBytes rightPayload) :
    leftBytes = rightBytes ∧ leftPayload = rightPayload := by
  have sameBytes := collisionFree leftBytes rightBytes left.canonical right.canonical
    (left.content.trans right.content.symm)
  have sameDecoded := left.decoded.symm.trans (sameBytes ▸ right.decoded)
  exact ⟨sameBytes, Option.some.inj sameDecoded⟩

/-- Finite complete unfolding allows DAG sharing. No omitted referenced child;
unrelated cached artifacts are unconstrained. Cycles have no finite witness. -/
inductive Complete (codec : Codec) (store : Store) : Ref → Prop where
  | node {ref : Ref} {bytes : Bytes} {payload : Payload}
      (resolved : Resolves codec store ref bytes payload)
      (children : ∀ (index : Nat) (child : Ref),
        payload.refs[index]? = some child → Complete codec store child) :
      Complete codec store ref

inductive Walk (codec : Codec) (store : Store) : Ref → List Nat → Bytes → Payload → Prop where
  | here {ref bytes payload} (resolved : Resolves codec store ref bytes payload) :
      Walk codec store ref [] bytes payload
  | step {ref bytes payload index child path endBytes endPayload}
      (resolved : Resolves codec store ref bytes payload)
      (edge : payload.refs[index]? = some child)
      (rest : Walk codec store child path endBytes endPayload) :
      Walk codec store ref (index :: path) endBytes endPayload

theorem walkUnique {codec : Codec} (collisionFree : CollisionFree codec)
    {leftStore rightStore : Store} {ref : Ref} {path : List Nat}
    {leftBytes rightBytes : Bytes} {leftPayload rightPayload : Payload}
    (left : Walk codec leftStore ref path leftBytes leftPayload)
    (right : Walk codec rightStore ref path rightBytes rightPayload) :
    leftBytes = rightBytes ∧ leftPayload = rightPayload := by
  induction left with
  | here left =>
      cases right with
      | here right => exact resolvedBytesAndPayloadUnique collisionFree left right
  | step left edge rest ih =>
      cases right with
      | step right rightEdge rightRest =>
          obtain ⟨_, samePayload⟩ := resolvedBytesAndPayloadUnique collisionFree left right
          subst samePayload
          have sameChild := Option.some.inj (edge.symm.trans rightEdge)
          subst sameChild
          exact ih rightRest

/-- Completeness transfers every existing ordered path to the other store,
so uniqueness does not silently accept a subset of contributions. -/
theorem walkTransport {codec : Codec} (collisionFree : CollisionFree codec)
    {leftStore rightStore : Store} {ref : Ref} {path : List Nat}
    {bytes : Bytes} {payload : Payload}
    (walk : Walk codec leftStore ref path bytes payload)
    (complete : Complete codec rightStore ref) :
    Walk codec rightStore ref path bytes payload := by
  induction walk with
  | here left =>
      cases complete with
      | node right children =>
          obtain ⟨sameBytes, samePayload⟩ := resolvedBytesAndPayloadUnique collisionFree left right
          subst sameBytes
          subst samePayload
          exact .here right
  | step left edge rest ih =>
      cases complete with
      | node right children =>
          obtain ⟨_, samePayload⟩ := resolvedBytesAndPayloadUnique collisionFree left right
          subst samePayload
          exact .step right edge (ih (children _ _ edge))

structure Anchor where
  authority : Ref
  context : Context
  currentModelHash : ContentId
  currentOptimizerHash : ContentId
  aggregate : Option Ref
  deriving DecidableEq, Repr

def Anchor.roots (anchor : Anchor) : List Ref :=
  anchor.authority :: anchor.aggregate.toList

/-- These predicates must be supplied by the separately verified native and
certificate boundary, not by an untrusted command or a hash-equality check. -/
structure Trust where
  anchorAuthenticated : Anchor → Prop
  recoveryAuthenticated : Anchor → Prop
  certificateAuthenticated : Ref → Prop

structure Binding (codec : Codec) (trust : Trust) (anchor : Anchor) (store : Store) where
  authenticatedAnchor : trust.anchorAuthenticated anchor
  authenticatedRecovery : trust.recoveryAuthenticated anchor
  complete : ∀ ref ∈ anchor.roots, Complete codec store ref
  authorityBytes : Bytes
  authority : Authority
  authorityResolved : Resolves codec store anchor.authority authorityBytes (.authority authority)
  contextMatches : authority.context = anchor.context
  iscAuthenticated : trust.certificateAuthenticated authority.isc
  ecAuthenticated : trust.certificateAuthenticated authority.ec
  apcAuthenticated : trust.certificateAuthenticated authority.apc
  modelBytes : Bytes
  model : StateVector
  modelWalk : Walk codec store anchor.authority [3] modelBytes (.model model)
  modelSchema : model.schema = authority.schema
  modelCurrent : codec.valueHash .model model.values = anchor.currentModelHash
  optimizerBytes : Bytes
  optimizer : StateVector
  optimizerWalk : Walk codec store anchor.authority [4] optimizerBytes (.optimizer optimizer)
  optimizerSchema : optimizer.schema = authority.schema
  optimizerCurrent : codec.valueHash .optimizer optimizer.values = anchor.currentOptimizerHash
  profileBytes : Bytes
  profile : Profile
  profileWalk : Walk codec store anchor.authority [1] profileBytes (.profile profile)
  modelQuantum : model.quantum = profile.applyQuantum
  optimizerQuantum : optimizer.quantum = profile.applyQuantum
  aggregateBound : ∀ ref, anchor.aggregate = some ref →
    trust.certificateAuthenticated ref ∧
    ∃ bytes parameters, Resolves codec store ref bytes (.aggregate anchor.authority.id parameters)

end DeltaReduce.NativeBinding

namespace DeltaReduce
open NativeBinding

/-- The graph conjunct of PO-AB1, conditional on an instantiated canonical codec
and named trust/hash premises. Ordered path domains AND exact bytes/payloads agree
across independently supplied complete stores, including all recursively required
Q shards. The current model, optimizer, profile and authority fields agree too.
Arithmetic soundness, decoder implementation and persistence are separate gates. -/
theorem nativeArithmeticGraphUnique {codec : Codec} (collisionFree : CollisionFree codec)
    {trust : Trust} {anchor : Anchor} {leftStore rightStore : Store}
    (left : Binding codec trust anchor leftStore) (right : Binding codec trust anchor rightStore) :
    (∀ ref ∈ anchor.roots, ∀ path bytes payload,
      Walk codec leftStore ref path bytes payload ↔ Walk codec rightStore ref path bytes payload) ∧
    left.authority = right.authority ∧ left.model = right.model ∧
    left.optimizer = right.optimizer ∧ left.profile = right.profile := by
  have authority := resolvedBytesAndPayloadUnique collisionFree
    left.authorityResolved right.authorityResolved
  have model := walkUnique collisionFree left.modelWalk right.modelWalk
  have optimizer := walkUnique collisionFree left.optimizerWalk right.optimizerWalk
  have profile := walkUnique collisionFree left.profileWalk right.profileWalk
  refine ⟨?_, Payload.authority.inj authority.2, Payload.model.inj model.2,
    Payload.optimizer.inj optimizer.2, Payload.profile.inj profile.2⟩
  intro ref member path bytes payload
  constructor
  · intro walk
    exact walkTransport collisionFree walk (right.complete ref member)
  · intro walk
    exact walkTransport collisionFree walk (left.complete ref member)

end DeltaReduce

namespace DeltaReduce.NativeBinding
open DeltaReduce

/- Checked extraction layer. The codec/trust instantiation remains a separate
native refinement gate. These functions take an independently bound store, not
caller-supplied mathematical rows or an assumed expected PARAMETER result. -/
structure LoadedPayload (codec : Codec) (store : Store) (ref : Ref) where
  bytes : Bytes
  payload : Payload
  resolved : Resolves codec store ref bytes payload

def loadPayload (codec : Codec) (store : Store) (ref : Ref) :
    Option (LoadedPayload codec store ref) :=
  match present : store ref.id with
  | none => none
  | some bytes =>
      match decoded : codec.decode bytes with
      | none => none
      | some payload =>
          if valid : codec.hash bytes = ref.id ∧ bytes.length = ref.length ∧
              codec.canonical bytes = true ∧ payload.kind = ref.kind ∧ payload.wellTypedEdges then
            some ⟨bytes, payload, ⟨present, valid.1, valid.2.1, valid.2.2.1,
              decoded, valid.2.2.2.1, valid.2.2.2.2⟩⟩
          else none

structure ParameterFrame where
  coordinates : List String
  shards : List Shard
  plan : Plan
  members : List String
  commitments : List Commitment
  ecIsc : Ref
  eligible : List String
  apcEc : Ref
  apcPlan : Ref
  deriving DecidableEq, Repr

structure FrameOrigin (codec : Codec) (store : Store) (authority : Authority)
    (frame : ParameterFrame) : Prop where
  schema : ∃ bytes, Resolves codec store authority.schema bytes
    (.schema frame.coordinates frame.shards)
  plan : ∃ bytes, Resolves codec store authority.plan bytes (.plan frame.plan)
  isc : ∃ bytes, Resolves codec store authority.isc bytes (.isc frame.members frame.commitments)
  ec : ∃ bytes, Resolves codec store authority.ec bytes (.ec frame.ecIsc frame.eligible)
  apc : ∃ bytes, Resolves codec store authority.apc bytes (.apc frame.apcEc frame.apcPlan)

def loadParameterFrame (codec : Codec) (store : Store) (authority : Authority) :
    Option {frame : ParameterFrame // FrameOrigin codec store authority frame} := do
  let schema ← loadPayload codec store authority.schema
  let plan ← loadPayload codec store authority.plan
  let isc ← loadPayload codec store authority.isc
  let ec ← loadPayload codec store authority.ec
  let apc ← loadPayload codec store authority.apc
  match hs : schema.payload, hp : plan.payload, hi : isc.payload,
      he : ec.payload, ha : apc.payload with
  | .schema coordinates shards, .plan planValue, .isc members commitments,
      .ec iscRef eligible, .apc ecRef planRef =>
      some ⟨⟨coordinates, shards, planValue, members, commitments, iscRef, eligible, ecRef, planRef⟩,
        ⟨⟨schema.bytes, by simpa only [hs] using schema.resolved⟩,
         ⟨plan.bytes, by simpa only [hp] using plan.resolved⟩,
         ⟨isc.bytes, by simpa only [hi] using isc.resolved⟩,
         ⟨ec.bytes, by simpa only [he] using ec.resolved⟩,
         ⟨apc.bytes, by simpa only [ha] using apc.resolved⟩⟩⟩
  | _, _, _, _, _ => none

def minInput : Int := -9223372036854775808
def maxInput : Int := 9223372036854775807

def positiveQuantum (quantum : Rational) : Prop :=
  ParameterKernel.ReducedNonnegative minInput maxInput quantum.numerator quantum.denominator ∧
    0 < quantum.numerator

instance (quantum : Rational) : Decidable (positiveQuantum quantum) :=
  inferInstanceAs (Decidable
    (ParameterKernel.ReducedNonnegative minInput maxInput quantum.numerator quantum.denominator ∧
      0 < quantum.numerator))

def domains (profile : Profile) : List String := profile.domainWeights.map (·.domain)
def shardIds (frame : ParameterFrame) : List String := frame.shards.map (·.id)
def coveredCoordinates (frame : ParameterFrame) : List Nat :=
  frame.shards.flatMap (fun s => (List.range s.length).map (s.offset + ·))
def assignmentKeys (frame : ParameterFrame) : List (String × String) :=
  frame.plan.assignments.map (fun a => (a.domain, a.shard))
def expectedKeys (frame : ParameterFrame) (profile : Profile) : List (String × String) :=
  (domains profile).flatMap (fun domain => (shardIds frame).map (domain, ·))

def validIdentifier (value : String) : Bool :=
  let chars := value.toList
  decide (0 < chars.length ∧ chars.length ≤ 128) && chars.all (fun ch =>
    let n := ch.toNat
    decide ((65 ≤ n ∧ n ≤ 90) ∨ (97 ≤ n ∧ n ≤ 122) ∨ (48 ≤ n ∧ n ≤ 57) ∨
      n = 46 ∨ n = 95 ∨ n = 58 ∨ n = 45))

/-- A decidable validation predicate, checked by the loader below; never a
premise that untrusted rows are already valid. All ordered lists come from the
resolved frame or the independently bound profile/current vectors. -/
def ParameterFrameValid (authority : Authority) (profile : Profile)
    (model optimizer : StateVector) (frame : ParameterFrame) : Prop :=
  frame.coordinates ≠ [] ∧ frame.coordinates.Pairwise (· < ·) ∧
  frame.shards ≠ [] ∧ (shardIds frame).Pairwise (· < ·) ∧
  (∀ s ∈ frame.shards, 0 < s.length ∧ s.offset + s.length ≤ frame.coordinates.length) ∧
  (∀ index ∈ List.range frame.coordinates.length, (coveredCoordinates frame).count index = 1) ∧
  (profile.accumulatorBits = 64 ∨ profile.accumulatorBits = 128) ∧
  profile.rounding = "HALF_TOWARD_POSITIVE" ∧ profile.nesterov = true ∧
  profile.outputRange = "FULL_SIGNED_INT64" ∧ positiveQuantum profile.applyQuantum ∧
  domains profile ≠ [] ∧ (domains profile).Pairwise (· < ·) ∧
  (∀ d ∈ profile.domainWeights,
    ParameterKernel.ReducedNonnegative minInput maxInput d.weight.numerator d.weight.denominator) ∧
  (∀ r ∈ [profile.learningRate, profile.momentum, profile.weightDecay],
    ParameterKernel.ReducedNonnegative minInput maxInput r.numerator r.denominator) ∧
  model.values.length = frame.coordinates.length ∧ optimizer.values.length = frame.coordinates.length ∧
  frame.ecIsc = authority.isc ∧ frame.apcEc = authority.ec ∧ frame.apcPlan = authority.plan ∧
  frame.plan.schema = authority.schema ∧ frame.plan.profile = authority.profile ∧
  frame.members ≠ [] ∧ frame.members.Pairwise (· < ·) ∧
  frame.eligible ≠ [] ∧ frame.eligible.Pairwise (· < ·) ∧
  (∀ ticket ∈ frame.eligible, ticket ∈ frame.members) ∧
  frame.plan.tickets.map (·.id) = frame.eligible ∧
  (∀ t ∈ frame.plan.tickets, t.domain ∈ domains profile) ∧
  frame.commitments.map (·.ticket) = frame.members ∧
  (∀ c ∈ frame.commitments, c.domain ∈ domains profile ∧
    c.leaves.map (·.shard) = shardIds frame ∧
    ∀ t ∈ frame.plan.tickets, t.id = c.ticket → t.domain = c.domain) ∧
  assignmentKeys frame = expectedKeys frame profile ∧
  (frame.plan.assignments.map (·.context)).Nodup ∧
  (∀ a ∈ frame.plan.assignments, 0 < a.denominator ∧ a.denominator ≤ maxInput ∧
    positiveQuantum a.quantum) ∧
  (∀ value ∈ model.values ++ optimizer.values, Fits minInput maxInput value) ∧
  (∀ name ∈ frame.coordinates ++ shardIds frame ++ domains profile ++ frame.members ++
    frame.plan.assignments.map (·.context), validIdentifier name = true)

instance (authority : Authority) (profile : Profile) (model optimizer : StateVector)
    (frame : ParameterFrame) : Decidable (ParameterFrameValid authority profile model optimizer frame) :=
  by unfold ParameterFrameValid; infer_instance

def committedQ (frame : ParameterFrame) (ticket shard : String) : Option Ref := do
  let commitment ← frame.commitments.find? (fun c => c.ticket == ticket)
  let leaf ← commitment.leaves.find? (fun leaf => leaf.shard == shard)
  some leaf.q

def eligibleDomainTickets (frame : ParameterFrame) (domain : String) : List String :=
  (frame.plan.tickets.filter (fun t => t.domain == domain)).map (·.id)

structure LoadedRow (codec : Codec) (store : Store) (schema : Ref) (frame : ParameterFrame)
    (assignment : Assignment) (width : Nat) (contribution : Contribution) where
  bytes : Bytes
  q : QShard
  resolved : Resolves codec store contribution.q bytes (.qShard q)
  committed : committedQ frame contribution.ticket assignment.shard = some contribution.q
  ticket : q.ticket = contribution.ticket
  domain : q.domain = assignment.domain
  shard : q.shard = assignment.shard
  parameterSchema : q.schema = schema
  quantum : q.quantum = assignment.quantum
  shape : q.values.length = width

def LoadedRow.row {codec store schema frame assignment width contribution}
    (loaded : LoadedRow codec store schema frame assignment width contribution) : ParameterKernel.Row :=
  ⟨contribution.weight.numerator, contribution.weight.denominator, loaded.q.values⟩

def loadRow (codec : Codec) (store : Store) (schema : Ref) (frame : ParameterFrame)
    (assignment : Assignment) (width : Nat) (contribution : Contribution) :
    Option (LoadedRow codec store schema frame assignment width contribution) := do
  let loaded ← loadPayload codec store contribution.q
  match hq : loaded.payload with
  | .qShard q =>
      if checked : committedQ frame contribution.ticket assignment.shard = some contribution.q ∧
          q.ticket = contribution.ticket ∧ q.domain = assignment.domain ∧
          q.shard = assignment.shard ∧ q.schema = schema ∧
          q.quantum = assignment.quantum ∧ q.values.length = width then
        some ⟨loaded.bytes, q, by simpa only [hq] using loaded.resolved,
          checked.1, checked.2.1, checked.2.2.1, checked.2.2.2.1,
          checked.2.2.2.2.1, checked.2.2.2.2.2.1, checked.2.2.2.2.2.2⟩
      else none
  | _ => none

inductive RowsBound (codec : Codec) (store : Store) (schema : Ref) (frame : ParameterFrame)
    (assignment : Assignment) (width : Nat) : List Contribution → List ParameterKernel.Row → Prop where
  | nil : RowsBound codec store schema frame assignment width [] []
  | cons {contribution contributions rows}
      (loaded : LoadedRow codec store schema frame assignment width contribution)
      (tail : RowsBound codec store schema frame assignment width contributions rows) :
      RowsBound codec store schema frame assignment width
        (contribution :: contributions) (loaded.row :: rows)

def loadRows (codec : Codec) (store : Store) (schema : Ref) (frame : ParameterFrame)
    (assignment : Assignment) (width : Nat) (contributions : List Contribution) :
    Option {rows : List ParameterKernel.Row //
      RowsBound codec store schema frame assignment width contributions rows} :=
  match contributions with
  | [] => some ⟨[], .nil⟩
  | contribution :: rest => do
      let loaded ← loadRow codec store schema frame assignment width contribution
      let tail ← loadRows codec store schema frame assignment width rest
      some ⟨loaded.row :: tail.val, .cons loaded tail.property⟩

theorem rowsBoundLength {codec store schema frame assignment width contributions rows}
    (bound : RowsBound codec store schema frame assignment width contributions rows) :
    contributions.length = rows.length ∧ ∀ row ∈ rows, row.values.length = width := by
  induction bound with
  | nil => exact ⟨rfl, by simp⟩
  | cons loaded tail ih =>
      refine ⟨by simp [ih.1], ?_⟩
      intro row member
      rcases List.mem_cons.mp member with equal | member
      · subst row; exact loaded.shape
      · exact ih.2 row member

def accumulatorLo (profile : Profile) : Int := -(2 ^ (profile.accumulatorBits - 1))
def accumulatorHi (profile : Profile) : Int := 2 ^ (profile.accumulatorBits - 1) - 1

structure DerivedParameter {codec : Codec} {store : Store} {trust : Trust} {anchor : Anchor}
    (binding : Binding codec trust anchor store) (domain shard : String) where
  frame : ParameterFrame
  origin : FrameOrigin codec store binding.authority frame
  validated : ParameterFrameValid binding.authority binding.profile binding.model binding.optimizer frame
  assignment : Assignment
  planned : assignment ∈ frame.plan.assignments
  key : assignment.domain = domain ∧ assignment.shard = shard
  partition : Shard
  partitionMember : partition ∈ frame.shards
  partitionKey : partition.id = shard
  orderedCoverage : assignment.contributions.map (·.ticket) = eligibleDomainTickets frame domain
  rows : List ParameterKernel.Row
  boundRows : RowsBound codec store binding.authority.schema frame assignment partition.length
    assignment.contributions rows
  numerators : List Int
  computed : ParameterKernel.checkedParameter (accumulatorLo binding.profile)
    (accumulatorHi binding.profile) minInput maxInput assignment.denominator partition.length rows =
      some numerators

def DerivedParameter.body {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (result : DerivedParameter binding domain shard) : ParameterBody :=
  { kind := "PARAMETER_EXPECTED", authorityId := anchor.authority.id,
    context := result.assignment.context, domain := domain, shard := shard,
    denominator := result.assignment.denominator, numerators := result.numerators,
    inputLeafIds := result.assignment.contributions.map (fun c => c.q.id) }

/-- A mathematical checked extractor, not a C ABI operation or new failure
terminal. It derives the full typed PARAMETER body before any conversion/Apply.
Quantum conversion cannot become an extra PARAMETER admission precondition. -/
def deriveParameter {codec : Codec} {store : Store} {trust : Trust} {anchor : Anchor}
    (binding : Binding codec trust anchor store) (domain shard : String) :
    Option (DerivedParameter binding domain shard) := do
  let source ← loadParameterFrame codec store binding.authority
  let frame := source.val
  if valid : ParameterFrameValid binding.authority binding.profile
      binding.model binding.optimizer frame then
    match planned : frame.plan.assignments.find?
        (fun a => a.domain == domain && a.shard == shard) with
    | none => none
    | some assignment =>
        match partitioned : frame.shards.find? (fun s => s.id == shard) with
        | none => none
        | some partition =>
            if ordered : assignment.contributions.map (·.ticket) = eligibleDomainTickets frame domain then
              let loaded ← loadRows codec store binding.authority.schema frame assignment
                partition.length assignment.contributions
              match computed : ParameterKernel.checkedParameter (accumulatorLo binding.profile)
                  (accumulatorHi binding.profile) minInput maxInput assignment.denominator
                  partition.length loaded.val with
              | none => none
              | some numerators =>
                  some ⟨frame, source.property, valid, assignment,
                    List.mem_of_find?_eq_some planned,
                    by simpa using List.find?_some planned,
                    partition, List.mem_of_find?_eq_some partitioned,
                    by simpa using List.find?_some partitioned,
                    ordered, loaded.val, loaded.property, numerators, computed⟩
            else none
  else none

/-- Every checked extracted row has one real Q artifact at the exact contribution
reference and the exact weight pair; no missing row is padded or silently omitted. -/
theorem rowsBoundAt {codec store schema frame assignment width contributions rows}
    (bound : RowsBound codec store schema frame assignment width contributions rows)
    (index : Nat) (row : ParameterKernel.Row) (atIndex : rows[index]? = some row) :
    ∃ contribution, contributions[index]? = some contribution ∧
      ∃ loaded : LoadedRow codec store schema frame assignment width contribution,
        row = loaded.row := by
  induction bound generalizing index row with
  | nil => simp at atIndex
  | @cons contribution contributions rows loaded tail ih =>
      cases index with
      | zero =>
          simp only [List.getElem?_cons_zero] at atIndex
          exact ⟨contribution, rfl, loaded, (Option.some.inj atIndex).symm⟩
      | succ index => exact ih index row atIndex

/-- This body-level result is deliberately not the complete PO-AB1 conversion
conjunct: certified aggregate conversion and schema placement remain separate. -/
theorem derivedParameterBodySound {codec store trust anchor}
    {binding : Binding codec trust anchor store} {domain shard}
    (result : DerivedParameter binding domain shard) :
    result.body.kind = "PARAMETER_EXPECTED" ∧ result.body.authorityId = anchor.authority.id ∧
    result.body.context = result.assignment.context ∧
    result.body.domain = domain ∧ result.body.shard = shard ∧
    result.body.denominator = result.assignment.denominator ∧
    result.body.inputLeafIds = result.assignment.contributions.map (fun c => c.q.id) ∧
    result.rows.length = (eligibleDomainTickets result.frame domain).length ∧
    result.body.numerators.length = result.partition.length ∧
    result.body.numerators = ParameterKernel.exactParameterRows result.assignment.denominator
      (List.replicate result.partition.length 0) result.rows ∧
    ParameterKernel.PrefixesSafe (accumulatorLo binding.profile) (accumulatorHi binding.profile)
      minInput maxInput result.assignment.denominator 0
      (List.replicate result.partition.length 0) result.rows := by
  obtain ⟨_, _, shape, exactRows, _, prefixes⟩ := ParameterKernel.checkedParameterSound
    (accumulatorLo binding.profile) (accumulatorHi binding.profile) minInput maxInput
    result.assignment.denominator result.partition.length result.rows result.numerators result.computed
  have count := (rowsBoundLength result.boundRows).1
  have coverage := congrArg List.length result.orderedCoverage
  simp only [List.length_map] at coverage
  exact ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, count.symm.trans coverage, shape, exactRows, prefixes⟩

theorem derivedParameterCoordinateRefines {codec store trust anchor}
    {binding : Binding codec trust anchor store} {domain shard}
    (result : DerivedParameter binding domain shard) (index : Nat)
    (within : index < result.partition.length) :
    ∃ value, result.body.numerators[index]? = some value ∧
      checkedAccumulate (accumulatorLo binding.profile) (accumulatorHi binding.profile)
        (accumulatorLo binding.profile) (accumulatorHi binding.profile) 0
        (ParameterKernel.coordinateTerms result.assignment.denominator index result.rows) =
          some value :=
  ParameterKernel.checkedParameterCoordinateRefines
    (accumulatorLo binding.profile) (accumulatorHi binding.profile) minInput maxInput
    result.assignment.denominator result.partition.length result.rows result.numerators
    result.computed index within

end DeltaReduce.NativeBinding
