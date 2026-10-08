import DeltaReduce.NativeManifestBinding

/-! R2.3 O metadata/data-use join. Reuses the original004 closed decoders,
partition/units and Merkle definitions. No public-state predicate, physical
availability oracle or new shard/certificate identity enters the relation.
Hash correctness and original configuration/producer origin remain explicit
external obligations; successful metadata resolution alone is not AC authority.
-/
namespace DeltaReduce.ProfileManifest
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ContentId)
open NativeManifestBinding

structure Metadata where
  plan : NativeShardPlanBinding.Bound
  manifest : Manifest
  deriving DecidableEq, Repr

def load (hash : Bytes → Bytes)
    (semantics schemaRaw scaleRaw planRaw manifestRaw manifestId : Bytes) :
    Option Metadata := do
  let p ← NativeShardPlanBinding.bind hash schemaRaw scaleRaw planRaw
  let w ← NativeManifestBytes.decode manifestRaw
  let m ← interpret w
  if Links hash planRaw p m ∧ ContentId manifestId ∧
      hash (manifestInput manifestRaw) = manifestId ∧ w.semantics = semantics then
    let root ← NativeManifestMerkle.root hash (m.refs.map (fun r => r.wire.leaf))
    if root = w.root then some ⟨p,m⟩ else none
  else none

structure Source (hash : Bytes → Bytes)
    (semantics schemaRaw scaleRaw planRaw manifestRaw manifestId : Bytes)
    (m : Metadata) : Prop where
  plan : NativeShardPlanBinding.bind hash schemaRaw scaleRaw planRaw = some m.plan
  wire : NativeManifestBytes.decode manifestRaw = some m.manifest.wire
  interpreted : interpret m.manifest.wire = some m.manifest
  links : Links hash planRaw m.plan m.manifest
  identity : ContentId manifestId ∧ hash (manifestInput manifestRaw) = manifestId
  semantics : m.manifest.wire.semantics = semantics
  root : NativeManifestMerkle.root hash (m.manifest.refs.map (fun r => r.wire.leaf)) =
    some m.manifest.wire.root

theorem checked {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    Source hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m := by
  unfold load at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,w,hw,parsed,hm,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨root,hr,last⟩ := last
  split at last <;> try contradiction
  rename_i eqRoot
  cases Option.some.inj last
  have origin := interpreted hm
  exact ⟨hp,by rw [origin.original]; exact hw,
    by rw [origin.original]; exact hm,checks.1,
    ⟨checks.2.1,checks.2.2.1⟩,by rw [origin.original]; exact checks.2.2.2,
    by rw [origin.original,← eqRoot]; exact hr⟩

theorem complete {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : Source hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m) :
    load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m := by
  simp only [load,h.plan,h.wire,h.interpreted,Bind.bind,Option.bind]
  rw [if_pos ⟨h.links,h.identity.1,h.identity.2,h.semantics⟩,h.root]
  simp

def originalLeaves (m : Metadata) : List (Bytes × Nat) :=
  m.manifest.refs.map (fun r => (r.wire.leaf,r.envelope))

def originalRoot (m : Metadata) : Bytes := m.manifest.wire.root

theorem originalBytes {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    NativeManifestBytes.encode m.manifest.wire = manifestRaw :=
  (NativeManifestBytes.decoded (checked h).wire).2.2.2

theorem completeOrderedReferences
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    m.manifest.refs.map Ref.wire = m.manifest.wire.refs ∧
    ∀ r ∈ m.manifest.refs, RefSource r.wire r :=
  refsSource (interpreted (checked h).interpreted).refs

theorem completeOrderedRoot
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    NativeManifestMerkle.Tree hash ((originalLeaves m).map Prod.fst) (originalRoot m) := by
  simpa only [originalLeaves,originalRoot,List.map_map,Function.comp_def] using
    (NativeManifestMerkle.rootSource (checked h).root).2.2.2

theorem originalPlan {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m}
    (h : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m) :
    m.manifest.refs.map Ref.entry = m.plan.plan.entries ∧
    NativeShardPartition.Span 0 0 (m.manifest.refs.map Ref.entry) m.manifest.total := by
  have src := checked h
  rcases src.links with ⟨_,_,_,_,_,_,_,_,_,_,_,_,entries,_,total,_⟩
  exact ⟨entries,by rw [entries,total]; exact
    (NativeShardPlanBinding.completePartition src.plan).2.2⟩

/-- The independently obtained current complete bytes are the missing premise
at data use. An AC or a previous observation cannot discharge this premise. -/
def consume (hash : Bytes → Bytes) (scaleRaw : Bytes) (m : Metadata) (raws : List Bytes) :=
  corpus hash scaleRaw m.plan m.manifest.wire m.manifest.refs raws

theorem atUseExistingBinding
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m raws blocks}
    (metadata : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m)
    (actual : consume hash scaleRaw m raws = some blocks) :
    NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws =
      some ⟨m.plan,m.manifest,blocks⟩ := by
  have s := checked metadata
  exact bindFromSource ⟨s.plan,s.wire,s.interpreted,s.links,s.identity,actual,s.root⟩

/-- Converse: no extra data-use gate beyond the original complete binding and
the independently pinned semantics. This does not filter by public success. -/
theorem existingBindingReusable
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId raws b}
    (loaded : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some b)
    (selected : b.manifest.wire.semantics = semantics) :
    load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some ⟨b.plan,b.manifest⟩ ∧
    consume hash scaleRaw ⟨b.plan,b.manifest⟩ raws = some b.blocks := by
  have s := boundSource loaded
  exact ⟨complete ⟨s.plan,s.wire,s.interpreted,s.links,s.identity,selected,s.root⟩,s.corpus⟩

theorem atUseOriginalLengths
    {hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId m raws blocks}
    (metadata : load hash semantics schemaRaw scaleRaw planRaw manifestRaw manifestId = some m)
    (actual : consume hash scaleRaw m raws = some blocks) :
    m.plan.plan.entries.length = raws.length ∧ raws.length = blocks.length :=
  noMissingOrExtraBlocks (atUseExistingBinding metadata actual)

/- Actual observations and volatile ownership are folded from empty. These
source positions are not shard/vote/certificate identifiers. The full producer
relation supplies the independently retained original event inputs and joins
this fold to its operation guards; an AC never creates a Read event here. -/
namespace Observations

structure InputSource where
  semantics : Bytes
  schema : Bytes
  scale : Bytes
  plan : Bytes
  manifest : Bytes
  manifestId : Bytes
  raws : List Bytes
  deriving DecidableEq, Repr

def decodeSource (hash : Bytes → Bytes) (s : InputSource) : Option Bound := do
  let m ← load hash s.semantics s.schema s.scale s.plan s.manifest s.manifestId
  let blocks ← consume hash s.scale m s.raws
  some ⟨m.plan,m.manifest,blocks⟩

theorem decodedOriginalBinding {hash s b} (ok : decodeSource hash s = some b) :
    NativeManifestBinding.bind hash s.schema s.scale s.plan s.manifest s.manifestId s.raws = some b := by
  simp only [decodeSource,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨m,hm,blocks,hblocks,last⟩ := ok
  cases Option.some.inj last
  exact atUseExistingBinding hm hblocks

theorem existingBindingComplete {hash s b}
    (ok : NativeManifestBinding.bind hash s.schema s.scale s.plan s.manifest s.manifestId s.raws = some b)
    (semantics : b.manifest.wire.semantics = s.semantics) : decodeSource hash s = some b := by
  obtain ⟨hm,hc⟩ := existingBindingReusable ok semantics
  simp only [decodeSource,hm,hc,Bind.bind,Option.bind]

inductive Event where
  | read (actor : Bytes) (source : InputSource)
  | failedRead (actor manifestId original : Bytes)
  | release (actor : Bytes) (readPosition : Nat)
  | processLost (actor : Bytes)
  | externalLoss (actor manifestId original : Bytes)
  | other (original : Bytes) (originalInputs : List Bytes)
  deriving DecidableEq, Repr

structure Buffer where
  actor : Bytes
  position : Nat
  source : InputSource
  deriving DecidableEq, Repr

structure Memory where
  events : List Event := []
  owned : List Buffer := []
  deriving DecidableEq, Repr

def step (hash : Bytes → Bytes) (state : Memory) (event : Event) : Memory :=
  let buffers := match event with
    | .read actor source =>
      if (decodeSource hash source).isSome then
        state.owned ++ [⟨actor,state.events.length,source⟩]
      else state.owned
    | .release actor index => state.owned.filter (fun b => !(b.actor == actor && b.position == index))
    | .processLost actor => state.owned.filter (fun b => b.actor != actor)
    | _ => state.owned
  ⟨state.events ++ [event],buffers⟩

def run (hash : Bytes → Bytes) (events : List Event) : Memory := events.foldl (step hash) {}

def OriginalRead (hash : Bytes → Bytes) (state : Memory) (buffer : Buffer) : Prop :=
  state.events[buffer.position]? = some (.read buffer.actor buffer.source) ∧
  (decodeSource hash buffer.source).isSome = true

def Provenance (hash : Bytes → Bytes) (state : Memory) : Prop :=
  ∀ buffer ∈ state.owned, OriginalRead hash state buffer

theorem eventPrefixRetained (hash state event) :
    (step hash state event).events = state.events ++ [event] := rfl

theorem originalReadAppend {hash state buffer event} (h : OriginalRead hash state buffer) :
    OriginalRead hash (step hash state event) buffer := by
  refine ⟨?_,h.2⟩
  change (state.events ++ [event])[buffer.position]? = _
  have bound : buffer.position < state.events.length := List.getElem?_eq_some_iff.mp h.1 |>.1
  rw [List.getElem?_append_left bound,h.1]

theorem stepProvenance {hash state} (h : Provenance hash state) (event : Event) :
    Provenance hash (step hash state event) := by
  intro buffer inside
  cases event with
  | read actor source =>
    simp only [step] at inside
    split at inside
    · rename_i success
      rcases List.mem_append.mp inside with old | added
      · exact originalReadAppend (h buffer old)
      · have eq : buffer = ⟨actor,state.events.length,source⟩ := by simpa using added
        subst buffer
        refine ⟨?_,success⟩
        change (state.events ++ [Event.read actor source])[state.events.length]? = _
        simp
    · exact originalReadAppend (h buffer inside)
  | failedRead actor manifest original => exact originalReadAppend (h buffer inside)
  | externalLoss actor manifest original => exact originalReadAppend (h buffer inside)
  | other original inputs => exact originalReadAppend (h buffer inside)
  | release actor index =>
    exact originalReadAppend (h buffer (List.mem_filter.mp inside).1)
  | processLost actor =>
    exact originalReadAppend (h buffer (List.mem_filter.mp inside).1)

theorem runProvenance (hash events) : Provenance hash (run hash events) := by
  have fold : ∀ (events : List Event) (state : Memory), Provenance hash state →
      Provenance hash (events.foldl (step hash) state) := by
    intro events
    induction events with
    | nil => intro state good; exact good
    | cons e rest ih => intro state good; exact ih _ (stepProvenance good e)
  exact fold events {} (by intro b impossible; simp at impossible)

def select (state : Memory) (actor : Bytes) (index : Nat) (manifestId : Bytes) : Option Buffer :=
  state.owned.find? (fun b => b.actor == actor && b.position == index && b.source.manifestId == manifestId)

theorem selectedOriginal {hash events actor index manifestId buffer}
    (found : select (run hash events) actor index manifestId = some buffer) :
    OriginalRead hash (run hash events) buffer :=
  runProvenance hash events buffer (List.mem_of_find?_eq_some found)

theorem selectedCoordinates {state actor index manifestId buffer}
    (found : select state actor index manifestId = some buffer) :
    buffer.actor = actor ∧ buffer.position = index ∧ buffer.source.manifestId = manifestId := by
  have selected := List.find?_some found
  simpa only [Bool.and_eq_true,beq_iff_eq,and_assoc] using selected

theorem runRetainsAllEvents (hash events) : (run hash events).events = events := by
  have fold : ∀ (events : List Event) (state : Memory),
      (events.foldl (step hash) state).events = state.events ++ events := by
    intro events
    induction events with
    | nil => intro state; simp
    | cons e rest ih => intro state; simp [List.foldl,ih,step,List.append_assoc]
  simpa only [run,List.nil_append] using fold events {}

theorem selectedOriginalPosition {hash events actor index manifestId buffer}
    (found : select (run hash events) actor index manifestId = some buffer) :
    events[index]? = some (.read actor buffer.source) := by
  have src := (selectedOriginal found).1
  obtain ⟨actorEq,indexEq,_⟩ := selectedCoordinates found
  simpa only [runRetainsAllEvents,actorEq,indexEq] using src

theorem selectedActualBinding {hash events actor index manifestId buffer}
    (found : select (run hash events) actor index manifestId = some buffer) :
    ∃ b, NativeManifestBinding.bind hash buffer.source.schema buffer.source.scale
      buffer.source.plan buffer.source.manifest buffer.source.manifestId buffer.source.raws = some b := by
  have actual := (selectedOriginal found).2
  cases hd : decodeSource hash buffer.source with
  | none => simp [hd] at actual
  | some b => exact ⟨b,decodedOriginalBinding hd⟩

theorem processLostCannotReuse (hash state actor index manifestId) :
    select (step hash state (.processLost actor)) actor index manifestId = none := by
  apply List.find?_eq_none.mpr
  intro buffer present
  have different := (List.mem_filter.mp present).2
  simp only [bne_iff_ne,ne_eq] at different
  simp [different]

theorem externalLossRetainsOwned (hash state actor manifestId original) :
    (step hash state (.externalLoss actor manifestId original)).owned = state.owned := rfl

theorem failedReadRetainsOwned (hash state actor manifestId original) :
    (step hash state (.failedRead actor manifestId original)).owned = state.owned := rfl

theorem releaseCannotReuse (hash state actor index manifestId) :
    select (step hash state (.release actor index)) actor index manifestId = none := by
  apply List.find?_eq_none.mpr
  intro buffer present
  have excluded := (List.mem_filter.mp present).2
  change (!(buffer.actor == actor && buffer.position == index)) = true at excluded
  simp only [Bool.not_eq_true', Bool.and_eq_false_iff] at excluded
  rcases excluded with different | different
  · simp [different]
  · simp [different]

end Observations

end DeltaReduce.ProfileManifest
