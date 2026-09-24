import Std

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
The payloads mirror native_binding.py; no arithmetic correctness is claimed here.
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
