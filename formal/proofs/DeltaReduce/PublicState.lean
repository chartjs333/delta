import DeltaReduce.PublicSnapshot
/-! Complete tagged public states. This is a representation/extraction layer,
not a proof of TLA Next, native producer authentication or full recovery. -/
namespace DeltaReduce.PublicState
mutual
inductive Value where
  | boolean (value : Bool)
  | integer (value : Int)
  | text (value : String)
  | model (value : String)
  | set (values : Values)
  | function (entries : Entries)
  deriving DecidableEq, Repr
inductive Values where
  | nil
  | cons (head : Value) (tail : Values)
  deriving DecidableEq, Repr
inductive Entries where
  | nil
  | cons (key value : Value) (tail : Entries)
  deriving DecidableEq, Repr
end
open DeltaReduce.NativeBinding
theorem congrPair {α β γ : Sort _} (f : α → β → γ) {a a' : α} {b b' : β}
    (left : a = a') (right : b = b') : f a b = f a' b' := by
  cases left
  cases right
  rfl

theorem byteAppendLength {a b : Bytes} {n m : Nat}
    (first : a.length = n) (second : b.length = m) :
    (a ++ b).length = n + m := by
  rw [List.length_append, first, second]

theorem commaSingletonLength {a : Bytes} {n : Nat} (one : a.length = n) :
    (List.intercalate [44] [a]).length = n := by
  simpa only [List.intercalate_singleton] using one

theorem commaConsLength {a b : Bytes} {tail : List Bytes} {n m : Nat}
    (first : a.length = n) (rest : (List.intercalate [44] (b :: tail)).length = m) :
    (List.intercalate [44] (a :: b :: tail)).length = n + 1 + m := by
  simp only [List.intercalate_cons_cons, List.length_append, List.length_cons,
    List.length_nil, first, rest]

def quoted (s : String) : Bytes := quotedBytes (s.toList.flatMap (fun c => escapedASCII c.toNat))
def array (xs : List Bytes) : Bytes := [91] ++ List.intercalate [44] xs ++ [93]
mutual
def encode : Value → Bytes
  | .boolean b => array [quoted "bool", asciiBytes (if b then "true" else "false")]
  | .integer n => array [quoted "int", quoted (toString n)]
  | .text s => array [quoted "str", quoted s]
  | .model s => array [quoted "model", quoted s]
  | .set xs => asciiBytes "[\"set\",[" ++ List.intercalate [44] (encodeValues xs) ++ [93,93]
  | .function xs => asciiBytes "[\"fun\",[" ++ List.intercalate [44] (encodeEntries xs) ++ [93,93]
def encodeValues : Values → List Bytes
  | .nil => []
  | .cons x xs => encode x :: encodeValues xs
def encodeEntries : Entries → List Bytes
  | .nil => []
  | .cons k v xs => ([91] ++ encode k ++ [44] ++ encode v ++ [93]) :: encodeEntries xs
end
def byteLess (left right : Bytes) : Bool :=
  left.lex right (fun a b => decide (a < b))

theorem byteLessCorrect (left right : Bytes) : byteLess left right = true ↔ left < right := by
  change left.lex right (fun a b => decide (a < b)) = true ↔ List.Lex (· < ·) left right
  simp only [List.lex_eq_true_iff_lex, decide_eq_true_eq]

theorem byteLessCommonPrefix (shared left right : Bytes) :
    byteLess (shared ++ left) (shared ++ right) = byteLess left right := by
  induction shared with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.cons_append, byteLess, List.cons_lex_cons, UInt8.lt_irrefl,
      decide_false, beq_self_eq_true, Bool.false_or, Bool.true_and] at *
    exact ih

def ordered : List Bytes → Bool
  | [] => true
  | first :: rest => rest.all (byteLess first) && ordered rest

theorem orderedCorrect (xs : List Bytes) :
    ordered xs = true ↔ xs.Pairwise (fun a b => a < b) := by
  induction xs with
  | nil => simp [ordered]
  | cons first rest ih =>
    simp [ordered, List.pairwise_cons, List.all_eq_true, byteLessCorrect, ih]
def keys : Entries → List Bytes
  | .nil => []
  | .cons k _ xs => encode k :: keys xs
mutual
def canonical (models : List String) : Value → Bool
  | .boolean _ | .integer _ => true
  | .text s => s.toList.all (fun c => decide (32 ≤ c.toNat ∧ c.toNat ≤ 126))
  | .model s => models.contains s && s.toList.all (fun c => decide (32 ≤ c.toNat ∧ c.toNat ≤ 126))
  | .set xs => canonicalValues models xs && ordered (encodeValues xs)
  | .function xs => canonicalEntries models xs && ordered (keys xs)
def canonicalValues (models : List String) : Values → Bool
  | .nil => true
  | .cons x xs => canonical models x && canonicalValues models xs
def canonicalEntries (models : List String) : Entries → Bool
  | .nil => true
  | .cons k v xs => canonical models k && canonical models v && canonicalEntries models xs
end


def fieldNames : List String := [
  "abortQCs",
  "abortReason",
  "abortRequests",
  "abortVotes",
  "aggregateCandidates",
  "aggregateRootQCs",
  "aggregateVotes",
  "aggregationPlanCertificates",
  "alive",
  "apcVotes",
  "applyCandidates",
  "applyQCs",
  "applyVotes",
  "availabilityAttestations",
  "availabilityCertificates",
  "availabilityShortfalls",
  "availableArtifacts",
  "availableTickets",
  "byzantine",
  "certificateRejections",
  "certificateReplayReceipts",
  "closedInputBodies",
  "commitments",
  "corruptArtifacts",
  "crashCoverage",
  "currentAdvanceReceipts",
  "currentCheckpoint",
  "currentReplayReceipts",
  "durableSequence",
  "durableVotes",
  "ecVotes",
  "eligibilityCertificates",
  "finalizedCertificates",
  "inputSetCertificates",
  "iscVotes",
  "lateAvailabilityEvidence",
  "leaseActive",
  "leaseEpoch",
  "leaseOwner",
  "logicalTime",
  "materializedArtifacts",
  "messageMultiplicity",
  "messages",
  "parameterQCs",
  "parameterResults",
  "parameterVotes",
  "partition",
  "pendingPointerRecoveries",
  "phase",
  "proposals",
  "publishedObjects",
  "receivedVotes",
  "recoveryState",
  "reduceApplyRejections",
  "rejectedCommitments",
  "rejectedPublications",
  "repairAttempts",
  "seedTranscripts",
  "ticketPlan",
  "timeoutObservations",
  "timeoutVotes",
  "view",
  "viewChangeQCs",
  "volatileVotes"]

theorem fieldCount : fieldNames.length = 64 := by decide
theorem fieldNamesUnique : fieldNames.Nodup := by decide

def lookup (name : String) : List (String × Value) → Option Value
  | [] => none
  | (key,value) :: rest => if key = name then some value else lookup name rest

structure State where
  rows : List (String × Value)
  complete : rows.map Prod.fst = fieldNames

def loadRows (rows : List (String × Value)) : Option State :=
  if complete : rows.map Prod.fst = fieldNames then some ⟨rows, complete⟩ else none

def State.read (state : State) (name : String) : Option Value := lookup name state.rows

theorem lookupPresent {rows : List (String × Value)} {name value}
    (h : lookup name rows = some value) : (name,value) ∈ rows := by
  induction rows with
  | nil => simp [lookup] at h
  | cons head tail ih =>
    rcases head with ⟨key,entry⟩
    simp only [lookup] at h
    split at h
    · rename_i same
      simp_all
    · exact List.mem_cons_of_mem _ (ih h)

theorem lookupExists {rows : List (String × Value)} {name}
    (h : name ∈ rows.map Prod.fst) : ∃ value, lookup name rows = some value := by
  induction rows with
  | nil => simp at h
  | cons head tail ih =>
    rcases head with ⟨key,entry⟩
    by_cases same : key = name
    · exact ⟨entry, by simp [lookup, same]⟩
    · have member : name ∈ tail.map Prod.fst := by
        simp only [List.map_cons, List.mem_cons] at h
        rcases h with first | rest
        · exact False.elim (same first.symm)
        · exact rest
      obtain ⟨value, found⟩ := ih member
      exact ⟨value, by simp [lookup, same, found]⟩

theorem rowsFieldUnique {rows : List (String × Value)} {name left right}
    (unique : (rows.map Prod.fst).Nodup)
    (a : (name,left) ∈ rows) (b : (name,right) ∈ rows) : left = right := by
  induction rows with
  | nil => simp at a
  | cons head tail ih =>
    rcases head with ⟨key,entry⟩
    have unique' : key ∉ tail.map Prod.fst ∧ (tail.map Prod.fst).Nodup := by simpa using unique
    rcases List.mem_cons.mp a with firstA | restA
    · rcases List.mem_cons.mp b with firstB | restB
      · cases firstA; cases firstB; rfl
      · cases firstA
        exact False.elim (unique'.1 (List.mem_map.mpr ⟨(name,right), restB, rfl⟩))
    · rcases List.mem_cons.mp b with firstB | restB
      · cases firstB
        exact False.elim (unique'.1 (List.mem_map.mpr ⟨(name,left), restA, rfl⟩))
      · exact ih unique'.2 restA restB

theorem everyFieldRetained (state : State) {name} (known : name ∈ fieldNames) :
    ∃ value, state.read name = some value ∧ (name,value) ∈ state.rows := by
  have present : name ∈ state.rows.map Prod.fst := by rw [state.complete]; exact known
  obtain ⟨value, found⟩ := lookupExists present
  exact ⟨value, found, lookupPresent found⟩

theorem retainedFieldUnique (state : State) {name left right}
    (a : (name,left) ∈ state.rows) (b : (name,right) ∈ state.rows) : left = right :=
  rowsFieldUnique (by rw [state.complete]; exact fieldNamesUnique) a b

theorem loadedRowsExact {rows state} (loaded : loadRows rows = some state) :
    state.rows = rows ∧ rows.map Prod.fst = fieldNames := by
  unfold loadRows at loaded
  split at loaded
  · rename_i complete
    cases Option.some.inj loaded
    exact ⟨rfl, complete⟩
  · contradiction

theorem missingFieldRejected {rows name} (known : name ∈ fieldNames)
    (missing : name ∉ rows.map Prod.fst) : loadRows rows = none := by
  unfold loadRows
  split
  · rename_i complete
    exact False.elim (missing (complete.symm ▸ known))
  · rfl

theorem wrongInventoryRejected {rows} (wrong : rows.map Prod.fst ≠ fieldNames) :
    loadRows rows = none := by simp [loadRows, wrong]

theorem changedFieldChangesRows (left right : State) {name}
    (changed : left.read name ≠ right.read name) : left.rows ≠ right.rows := by
  intro equal
  exact changed (congrArg (lookup name) equal)

mutual
def nodes : Value → Nat
  | .set xs => 1 + valueNodes xs
  | .function xs => 1 + entryNodes xs
  | _ => 1
def valueNodes : Values → Nat
  | .nil => 0
  | .cons x xs => nodes x + valueNodes xs
def entryNodes : Entries → Nat
  | .nil => 0
  | .cons k v xs => nodes k + nodes v + entryNodes xs
end

mutual
def depth : Value → Nat
  | .set xs => valueDepth xs
  | .function xs => entryDepth xs
  | _ => 0
def valueDepth : Values → Nat
  | .nil => 0
  | .cons x xs => max (1 + depth x) (valueDepth xs)
def entryDepth : Entries → Nat
  | .nil => 0
  | .cons k v xs => max (max (1 + depth k) (1 + depth v)) (entryDepth xs)
end

def object (rows : List (String × Bytes)) : Bytes :=
  [123] ++ List.intercalate [44] (rows.map (fun (k,v) => quoted k ++ [58] ++ v)) ++ [125]
def variableBytes (state : State) : Bytes := object (state.rows.map (fun (k,v) => (k,encode v)))

structure Identity where
  semantics : ContentId
  configuration : ContentId
  modules : List (String × ContentId)
  deriving DecidableEq, Repr

def profile : String := "deltareduce.full-public-state.v1-candidate"
def identityBytes (identity : Identity) : Bytes := object [
  ("configuration_sha256", quotedBytes ((idBytes identity.configuration).drop 7)),
  ("formal_semantics_id", quotedBytes (idBytes identity.semantics)),
  ("modules", object (identity.modules.map (fun (name,hash) => (name,quotedBytes ((idBytes hash).drop 7)))))]
def documentHeader (identity : Identity) : Bytes :=
  asciiBytes "{\"model\":" ++ identityBytes identity ++ asciiBytes ",\"profile\":" ++
  quoted profile ++ asciiBytes ",\"variables\":"
def documentBytes (identity : Identity) (state : State) : Bytes :=
  documentHeader identity ++ variableBytes state ++ [125]
def preimage (identity : Identity) (state : State) : Bytes :=
  asciiBytes profile ++ [0] ++ documentBytes identity state

def identityCanonical (identity : Identity) : Bool :=
  decide (identity.semantics.length = 32 ∧ identity.configuration.length = 32) &&
  ordered (identity.modules.map (fun (name,_) => asciiBytes name)) &&
  identity.modules.all (fun (name,hash) => decide (hash.length = 32) &&
    name.toList.all (fun c => decide (32 ≤ c.toNat ∧ c.toNat ≤ 126)))

/-- Typed input, not a native byte parser. Unknown/null values have no constructor.
Allocation/stack behavior of a concrete decoder remains a separate obligation. -/
structure Observation where
  version : String
  identity : Identity
  rows : List (String × Value)
  bytes : Bytes
  root : ContentId

def admissible (models : List String) (expected : Identity)
    (sha256 : Bytes → ContentId) (input : Observation) (state : State) : Prop :=
  input.version = profile ∧ input.identity = expected ∧ identityCanonical expected = true ∧
  (state.rows.all (fun (_,v) => canonical models v && decide (depth v ≤ 64))) = true ∧
  (state.rows.map (fun (_,v) => nodes v)).sum ≤ 250000 ∧
  input.bytes = documentBytes expected state ∧ input.bytes.length ≤ 4194304 ∧
  input.root.length = 32 ∧ sha256 (preimage expected state) = input.root

instance (models expected sha256 input state) : Decidable (admissible models expected sha256 input state) := by
  unfold admissible; infer_instance

structure Loaded (models : List String) (expected : Identity)
    (sha256 : Bytes → ContentId) (input : Observation) where
  state : State
  original : state.rows = input.rows
  checked : admissible models expected sha256 input state

def load (models : List String) (expected : Identity) (sha256 : Bytes → ContentId)
    (input : Observation) : Option (Loaded models expected sha256 input) :=
  if complete : input.rows.map Prod.fst = fieldNames then
    let state : State := ⟨input.rows, complete⟩
    if checked : admissible models expected sha256 input state then
      some ⟨state, rfl, checked⟩ else none
  else none

/-- A supplied proof object is accepted by the same executable checks. Concrete
examples construct every conjunct from encoding/canonicality proofs; this is
not authentication of a producer or a public transition. -/
theorem loadProvided {models expected sha256 input}
    (loaded : Loaded models expected sha256 input) :
    load models expected sha256 input = some loaded := by
  rcases loaded with ⟨⟨rows, complete⟩, original, checked⟩
  dsimp at original
  subst rows
  simp only [load, dif_pos complete, dif_pos checked]

theorem loadedIdentity {models expected sha256 input} (loaded : Loaded models expected sha256 input) :
    input.version = profile ∧ input.identity = expected ∧ loaded.state.rows = input.rows :=
  ⟨loaded.checked.1, loaded.checked.2.1, loaded.original⟩
theorem loadedCompletePreimage {models expected sha256 input} (loaded : Loaded models expected sha256 input) :
    input.bytes = documentBytes expected loaded.state ∧
    sha256 (preimage expected loaded.state) = input.root :=
  ⟨loaded.checked.2.2.2.2.2.1, loaded.checked.2.2.2.2.2.2.2.2⟩
theorem loadedBounded {models expected sha256 input} (loaded : Loaded models expected sha256 input) :
    (loaded.state.rows.map (fun (_,v) => nodes v)).sum ≤ 250000 ∧ input.bytes.length ≤ 4194304 :=
  ⟨loaded.checked.2.2.2.2.1, loaded.checked.2.2.2.2.2.2.1⟩
theorem loadedEveryField {models expected sha256 input name}
    (loaded : Loaded models expected sha256 input) (known : name ∈ fieldNames) :
    ∃ value, loaded.state.read name = some value ∧ (name,value) ∈ input.rows := by
  obtain ⟨value, found, member⟩ := everyFieldRetained loaded.state known
  exact ⟨value, found, loaded.original ▸ member⟩

def valuesList : Values → List Value
  | .nil => []
  | .cons x xs => x :: valuesList xs
def functionLookup (key : Value) : Entries → Option Value
  | .nil => none
  | .cons k v xs => if k = key then some v else functionLookup key xs
def readFunction (value key : Value) : Option Value := match value with
  | .function xs => functionLookup key xs
  | _ => none
def readSet : Value → Option (List Value)
  | .set xs => some (valuesList xs)
  | _ => none
def readNat : Value → Option Nat
  | .integer z => if 0 ≤ z then some z.toNat else none
  | _ => none

structure Vote where
  actor : Value
  kind : Value
  context : Value
  body : Value
  deriving DecidableEq, Repr
def voteEntries (v : Vote) : Entries :=
  .cons (.text "body") v.body (.cons (.text "context") v.context
    (.cons (.text "kind") v.kind (.cons (.text "validator") v.actor .nil)))
def readVote : Value → Option Vote
  | .function (.cons (.text "body") body (.cons (.text "context") context
      (.cons (.text "kind") kind (.cons (.text "validator") actor .nil)))) => some ⟨actor,kind,context,body⟩
  | _ => none
theorem readVoteExact {value vote} (h : readVote value = some vote) :
    value = .function (voteEntries vote) := by
  unfold readVote at h
  split at h
  · cases h; rfl
  · contradiction

structure Frame where
  current : Value
  view : Nat
  logicalTime : Nat
  sequence : Nat
  votes : List Vote
  deriving DecidableEq, Repr

def readVotes (state : State) : Option (List Vote) := do
  let value ← state.read "durableVotes"
  let values ← readSet value
  values.mapM readVote
def actorVotes (actor : Value) (frame : Frame) : List Vote :=
  frame.votes.filter (fun vote => decide (vote.actor = actor))

def frameMatches (state : State) (actor : Value) (frame : Frame) : Prop :=
  state.read "currentCheckpoint" = some frame.current ∧
  state.read "view" = some (.integer frame.view) ∧
  state.read "logicalTime" = some (.integer frame.logicalTime) ∧
  (state.read "durableSequence" >>= fun f => readFunction f actor) = some (.integer frame.sequence) ∧
  readVotes state = some frame.votes ∧ (actorVotes actor frame).length = frame.sequence ∧
  state.read "phase" = some (.text "ACTIVE") ∧ state.read "abortRequests" = some (.set .nil) ∧
  (state.read "alive" >>= readSet).any (fun alive => alive.contains actor) = true ∧
  (state.read "recoveryState" >>= fun f => readFunction f actor) = some (.text "READY")
instance (state actor frame) : Decidable (frameMatches state actor frame) := by
  unfold frameMatches; infer_instance
structure CheckedFrame (state : State) (actor : Value) where
  data : Frame
  bound : frameMatches state actor data

/-- Extracts fields from the complete state; no expected frame or approval flag.
The actor-to-native identity relation is not supplied by this representation layer. -/
def extract (state : State) (actor : Value) : Option (CheckedFrame state actor) := do
  let current ← state.read "currentCheckpoint"
  let view ← state.read "view" >>= readNat
  let time ← state.read "logicalTime" >>= readNat
  let sequence ← state.read "durableSequence" >>= (fun f => readFunction f actor) >>= readNat
  let votes ← readVotes state
  let data : Frame := ⟨current,view,time,sequence,votes⟩
  if bound : frameMatches state actor data then some ⟨data,bound⟩ else none

theorem frameCurrentTime {state actor} (frame : CheckedFrame state actor) :
    state.read "currentCheckpoint" = some frame.data.current ∧
    state.read "view" = some (.integer frame.data.view) ∧
    state.read "logicalTime" = some (.integer frame.data.logicalTime) :=
  ⟨frame.bound.1, frame.bound.2.1, frame.bound.2.2.1⟩
theorem frameSequenceFromAllVotes {state actor} (frame : CheckedFrame state actor) :
    readVotes state = some frame.data.votes ∧
    frame.data.sequence = (actorVotes actor frame.data).length :=
  ⟨frame.bound.2.2.2.2.1, frame.bound.2.2.2.2.2.1.symm⟩
theorem frameRequiresReady {state actor} (frame : CheckedFrame state actor) :
    state.read "phase" = some (.text "ACTIVE") ∧
    (state.read "recoveryState" >>= fun f => readFunction f actor) = some (.text "READY") :=
  ⟨frame.bound.2.2.2.2.2.2.1, frame.bound.2.2.2.2.2.2.2.2.2⟩
theorem frameCompleteSource {state actor} (_frame : CheckedFrame state actor) {name}
    (known : name ∈ fieldNames) : ∃ value, (name,value) ∈ state.rows := by
  obtain ⟨value, _, member⟩ := everyFieldRetained state known
  exact ⟨value,member⟩

/-- The complete parent/body is retained. This is an extraction check, not
certificate validity, arithmetic validity or a production Next proof. -/
def readField (body : Value) (name : String) : Option Value := readFunction body (.text name)

def candidateCollection (vote : Vote) : Option String :=
  if vote.kind = .text "PARAMETER" then some "parameterResults"
  else if vote.kind = .text "APPLY" then some "applyCandidates" else none

def expectedContext (vote : Vote) : Option Value := do
  if vote.kind = .text "PARAMETER" then
    let domain ← readField vote.body "domain"
    let shard ← readField vote.body "shard"
    some (.function (.cons (.text "domain") domain (.cons (.text "shard") shard .nil)))
  else if vote.kind = .text "APPLY" then readField vote.body "aggregate" else none

def firstMatches (state : State) (actor : Value) (frame : Frame) (vote : Vote) : Prop :=
  vote.actor = actor ∧
  readField vote.body "parent" = some frame.current ∧
  expectedContext vote = some vote.context ∧
  ((candidateCollection vote >>= state.read) >>= readSet).any (fun xs => xs.contains vote.body) = true ∧
  (actorVotes actor frame).all (fun old => !(decide (old.kind = vote.kind ∧ old.context = vote.context))) = true

instance (state actor frame vote) : Decidable (firstMatches state actor frame vote) := by
  unfold firstMatches; infer_instance

structure First (before after : State) (actor : Value) where
  prior : CheckedFrame before actor
  next : CheckedFrame after actor
  vote : Vote
  added : next.data.votes.filter (fun v => !prior.data.votes.contains v) = [vote]
  retained : ∀ v ∈ prior.data.votes, v ∈ next.data.votes
  sequence : next.data.sequence = prior.data.sequence + 1
  checked : firstMatches before actor prior.data vote

/-- Derive the single new envelope; no caller-supplied expected body or sequence.
This does not check all other after-state effects or global QC eligibility. -/
def extractFirst (before after : State) (actor : Value) : Option (First before after actor) := do
  let prior ← extract before actor
  let next ← extract after actor
  match added : next.data.votes.filter (fun v => !prior.data.votes.contains v) with
  | [vote] =>
    if checks : (∀ v ∈ prior.data.votes, v ∈ next.data.votes) ∧
        next.data.sequence = prior.data.sequence + 1 ∧ firstMatches before actor prior.data vote then
      some ⟨prior,next,vote,added,checks.1,checks.2.1,checks.2.2⟩ else none
  | _ => none

structure Projected (models : List String) (expected : Identity) (sha256 : Bytes → ContentId)
    (before after : Observation) (actor : Value) where
  prior : Loaded models expected sha256 before
  next : Loaded models expected sha256 after
  first : First prior.state next.state actor

/-- Both complete preimages share the separately supplied identity/configuration.
Unknown observations have no total-state fallback. This does not authenticate
the source producer or justify a TLA transition. -/
def projectFirst (models : List String) (expected : Identity) (sha256 : Bytes → ContentId)
    (before after : Observation) (actor : Value) : Option (Projected models expected sha256 before after actor) := do
  let prior ← load models expected sha256 before
  let next ← load models expected sha256 after
  let first ← extractFirst prior.state next.state actor
  some ⟨prior,next,first⟩

theorem projectionSameIdentity {models expected sha256 before after actor}
    (p : Projected models expected sha256 before after actor) :
    before.identity = expected ∧ after.identity = expected :=
  ⟨p.prior.checked.2.1,p.next.checked.2.1⟩

theorem projectionCompletePreimages {models expected sha256 before after actor}
    (p : Projected models expected sha256 before after actor) :
    before.bytes = documentBytes expected p.prior.state ∧
    after.bytes = documentBytes expected p.next.state ∧
    sha256 (preimage expected p.prior.state) = before.root ∧
    sha256 (preimage expected p.next.state) = after.root :=
  ⟨(loadedCompletePreimage p.prior).1,(loadedCompletePreimage p.next).1,
    (loadedCompletePreimage p.prior).2,(loadedCompletePreimage p.next).2⟩

theorem firstOriginalParent {before after actor} (first : First before after actor) :
    readField first.vote.body "parent" = before.read "currentCheckpoint" :=
  first.checked.2.1.trans first.prior.bound.1.symm

theorem firstActorAndContext {before after actor} (first : First before after actor) :
    first.vote.actor = actor ∧ expectedContext first.vote = some first.vote.context :=
  ⟨first.checked.1, first.checked.2.2.1⟩

theorem firstAllVoteSequence {before after actor} (first : First before after actor) :
    first.next.data.sequence = (actorVotes actor first.prior.data).length + 1 :=
  first.sequence.trans (congrArg (· + 1) (frameSequenceFromAllVotes first.prior).2)

theorem firstNoOldVoteLost {before after actor} (first : First before after actor) :
    ∀ v ∈ first.prior.data.votes, v ∈ first.next.data.votes := first.retained

theorem firstContextFresh {before after actor} (first : First before after actor)
    {old} (member : old ∈ actorVotes actor first.prior.data) :
    ¬ (old.kind = first.vote.kind ∧ old.context = first.vote.context) := by
  have all := first.checked.2.2.2.2
  have one := (List.all_eq_true.mp all) old member
  intro both
  simp [both.1, both.2] at one

theorem firstEnvelopeFromAfter {before after actor} (first : First before after actor) :
    first.vote ∈ first.next.data.votes := by
  have member : first.vote ∈ first.next.data.votes.filter (fun v => !first.prior.data.votes.contains v) := by
    rw [first.added]; exact List.mem_cons_self
  exact (List.mem_filter.mp member).1

theorem firstEnvelopeNotPreviouslyStored {before after actor} (first : First before after actor) :
    first.vote ∉ first.prior.data.votes := by
  have member : first.vote ∈ first.next.data.votes.filter (fun v => !first.prior.data.votes.contains v) := by
    rw [first.added]; exact List.mem_cons_self
  simpa using (List.mem_filter.mp member).2

theorem firstBodyProposed {before after actor} (first : First before after actor) :
    ((candidateCollection first.vote >>= before.read) >>= readSet).any
      (fun xs => xs.contains first.vote.body) = true := first.checked.2.2.2.1

/-- Independent identity adapter, explicitly not a proof of native hashes or
exporter provenance. Height/epoch/model IDs cannot be invented by the vote. -/
structure IdentityMap where
  actor : Value → Option String
  checkpoint : Value → Option String
  height : Value → Option Nat
  epoch : Value → Option String

def nativeMatches (mapping : IdentityMap) {before after actor}
    (first : First before after actor) (anchor : Anchor) (metadata : VoteMetadata) : Prop :=
  mapping.actor actor = some metadata.actor ∧
  mapping.checkpoint first.prior.data.current = some anchor.context.parentCheckpoint ∧
  ((readField first.vote.body "round" >>= fun r => readField r "height") >>= mapping.height) = some anchor.context.height ∧
  ((readField first.vote.body "round" >>= fun r => readField r "epoch") >>= mapping.epoch) = some anchor.context.epoch ∧
  first.prior.data.view = anchor.context.view ∧ first.prior.data.logicalTime = metadata.logicalTime ∧
  metadata.logicalTime < anchor.context.hardDeadline ∧ metadata.recovered = true

instance (mapping) {before after actor} (first : First before after actor) (anchor metadata) :
    Decidable (nativeMatches mapping first anchor metadata) := by unfold nativeMatches; infer_instance

structure NativeFrame (mapping : IdentityMap) {before after actor}
    (first : First before after actor) (anchor : Anchor) (metadata : VoteMetadata) : Type where
  bound : nativeMatches mapping first anchor metadata

def bindNativeFrame (mapping : IdentityMap) {before after actor}
    (first : First before after actor) (anchor : Anchor) (metadata : VoteMetadata) :
    Option (NativeFrame mapping first anchor metadata) :=
  if bound : nativeMatches mapping first anchor metadata then some ⟨bound⟩ else none

theorem nativeFrameIdentity {mapping before after actor} {first : First before after actor} {anchor metadata}
    (bound : NativeFrame mapping first anchor metadata) :
    mapping.actor actor = some metadata.actor ∧
    mapping.checkpoint first.prior.data.current = some anchor.context.parentCheckpoint :=
  ⟨bound.bound.1,bound.bound.2.1⟩

theorem nativeFrameClock {mapping before after actor} {first : First before after actor} {anchor metadata}
    (bound : NativeFrame mapping first anchor metadata) :
    first.prior.data.view = anchor.context.view ∧
    first.prior.data.logicalTime = metadata.logicalTime ∧ metadata.logicalTime < anchor.context.hardDeadline :=
  ⟨bound.bound.2.2.2.2.1, bound.bound.2.2.2.2.2.1, bound.bound.2.2.2.2.2.2.1⟩

end DeltaReduce.PublicState
