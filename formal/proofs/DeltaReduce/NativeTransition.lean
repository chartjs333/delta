import DeltaReduce.NativeStateBytes

/-! Executable reconstruction of the pinned native summary transition. This is
not the full public protocol, vote/QC authorization, physical recovery or SHA.
Output bytes are computed here, never supplied as an admitted result. -/
namespace DeltaReduce.NativeTransition
open NativeReceiptBytes NativeVoteBytes NativeStateBytes

inductive Action where
  | config | view | commitment | availability | freeze | aggregate | abort
  deriving DecidableEq, Repr

def actionName : Action → Bytes
  | .config => ascii "FINALIZE_ROUND_CONFIG" | .view => ascii "ADVANCE_VIEW"
  | .commitment => ascii "ACCEPT_COMMITMENT" | .availability => ascii "ACCEPT_AVAILABILITY"
  | .freeze => ascii "FINALIZE_INPUT_FREEZE" | .aggregate => ascii "FINALIZE_AGGREGATE"
  | .abort => ascii "CERTIFY_ABORT"

def actions : List Action := [.config,.view,.commitment,.availability,.freeze,.aggregate,.abort]
def parseAction (name : Bytes) : Option Action := actions.find? (fun a => actionName a == name)

theorem actionParsed {name a} (ok : parseAction name = some a) : actionName a = name := by
  have h := List.find?_some (p := fun a => actionName a == name) ok
  simpa using h

def terminal (s : State) : Prop := s.wire.phase = ascii "AGGREGATED" ∨ s.wire.phase = ascii "ABORTED"
instance (s : State) : Decidable (terminal s) := by unfold terminal; infer_instance

def PhaseGuard (a : Action) (s : State) (c : Command) : Prop :=
  match a with
  | .config => s.wire.phase = ascii "TICKETING_OPEN"
  | .view => s.view + 1 < 256^8 ∧ c.view = s.view + 1
  | .commitment => (s.wire.phase = ascii "TICKETING_OPEN" ∨ s.wire.phase = ascii "COMMITTED") ∧
      s.wire.committed < s.wire.total
  | .availability => (s.wire.phase = ascii "COMMITTED" ∨ s.wire.phase = ascii "AVAILABLE") ∧
      s.wire.available < s.wire.committed
  | .freeze => s.wire.phase = ascii "AVAILABLE" ∧ 0 < s.wire.available
  | .aggregate => s.wire.phase = ascii "ELIGIBLE"
  | .abort => True
instance (a s c) : Decidable (PhaseGuard a s c) := by cases a <;> unfold PhaseGuard <;> infer_instance

def Enabled (a : Action) (s : State) (c : Command) : Prop :=
  c.wire.round = s.wire.round ∧ c.height = s.height ∧
  (a = .view ∨ c.view = s.view) ∧ PhaseGuard a s c ∧
  (a = .config ∨ (¬ terminal s ∧ s.sequence + 1 < 256^8))
instance (a s c) : Decidable (Enabled a s c) := by unfold Enabled; infer_instance

def decimal (n : Nat) : Bytes := ascii (toString n)

def changed (a : Action) (s : State) (c : Command) : WireState :=
  match a with
  | .config => s.wire
  | .view => {s.wire with view := c.wire.view}
  | .commitment => {s.wire with committed := s.wire.committed+1, phase := ascii "COMMITTED"}
  | .availability => {s.wire with available := s.wire.available+1, phase := ascii "AVAILABLE"}
  | .freeze => {s.wire with phase := ascii "ELIGIBLE"}
  | .aggregate => {s.wire with phase := ascii "AGGREGATED", root := c.wire.body}
  | .abort => {s.wire with phase := ascii "ABORTED"}

def candidate (a : Action) (s : State) (c : Command) : State :=
  if a = .config then s else
    ⟨{changed a s c with sequence := decimal (s.sequence+1)},s.sequence+1,s.height,
      if a = .view then c.view else s.view⟩

/- StateValid checks the generated decimal bytes against the exact numeric
result. No unproved general Nat printing/completeness assertion is needed. -/
def step (s : State) (c : Command) : Option State := do
  if StateValid s ∧ CommandValid c then
    let a ← parseAction c.wire.commandKind
    if Enabled a s c ∧ StateValid (candidate a s c) then some (candidate a s c) else none
  else none

theorem stepSound {s c n} (ok : step s c = some n) :
    StateValid s ∧ CommandValid c ∧ ∃ a, parseAction c.wire.commandKind = some a ∧
      Enabled a s c ∧ StateValid n ∧ n = candidate a s c := by
  unfold step at ok
  split at ok
  · rename_i valid
    cases h : parseAction c.wire.commandKind with
    | none => simp [h] at ok
    | some a =>
      simp only [h,bind,Option.bind] at ok
      split at ok
      · rename_i accepted
        cases Option.some.inj ok
        exact ⟨valid.1,valid.2,a,rfl,accepted.1,accepted.2,rfl⟩
      · contradiction
  · contradiction

theorem stepFromComponents (s c : _) (a : Action) (valid : StateValid s ∧ CommandValid c)
    (action : parseAction c.wire.commandKind = some a) (enabled : Enabled a s c)
    (next : StateValid (candidate a s c)) : step s c = some (candidate a s c) := by
  simp [step,valid,action,enabled,next]

theorem unknownReject (s c : _) (unknown : parseAction c.wire.commandKind = none) : step s c = none := by
  simp [step,unknown]

theorem disabledReject (s c : _) (a : Action) (parsed : parseAction c.wire.commandKind = some a)
    (disabled : ¬ Enabled a s c) : step s c = none := by simp [step,parsed,disabled]

theorem candidateSequence (a s c) : (candidate a s c).sequence =
    if a = .config then s.sequence else s.sequence+1 := by cases a <;> rfl

theorem candidatePreserves (a s c) :
    (candidate a s c).wire.config = s.wire.config ∧
    (candidate a s c).wire.parent = s.wire.parent ∧
    (candidate a s c).wire.round = s.wire.round ∧
    (candidate a s c).wire.total = s.wire.total ∧
    (candidate a s c).wire.height = s.wire.height ∧ (candidate a s c).height = s.height := by
  cases a <;> exact ⟨rfl,rfl,rfl,rfl,rfl,rfl⟩

theorem successfulContext {s c n} (ok : step s c = some n) :
    c.wire.round = s.wire.round ∧ c.height = s.height ∧ StateValid n := by
  obtain ⟨_,_,a,_,enabled,valid,_⟩ := stepSound ok
  exact ⟨enabled.1,enabled.2.1,valid⟩

theorem successfulSequence {s c n} (ok : step s c = some n) :
    (c.wire.commandKind = actionName .config ∧ n = s) ∨
      (¬ terminal s ∧ n.sequence = s.sequence+1 ∧ n.sequence < 256^8) := by
  obtain ⟨_,_,a,parsed,enabled,_,rfl⟩ := stepSound ok
  by_cases config : a = .config
  · subst a; exact Or.inl ⟨(actionParsed parsed).symm,by simp [candidate]⟩
  · have h := enabled.2.2.2.2.resolve_left config
    exact Or.inr ⟨h.1,by simp [candidateSequence,config],by simpa [candidateSequence,config] using h.2⟩

theorem successfulPreserves {s c n} (ok : step s c = some n) :
    n.wire.config = s.wire.config ∧ n.wire.parent = s.wire.parent ∧
    n.wire.round = s.wire.round ∧ n.wire.total = s.wire.total ∧
    n.wire.height = s.wire.height ∧ n.height = s.height := by
  obtain ⟨_,_,a,_,_,_,rfl⟩ := stepSound ok
  exact candidatePreserves a s c

theorem configUnchanged (s c) : candidate .config s c = s := rfl
theorem commitmentFields (s c) : (candidate .commitment s c).wire.committed = s.wire.committed+1 ∧
    (candidate .commitment s c).wire.available = s.wire.available ∧
    (candidate .commitment s c).wire.root = s.wire.root := ⟨rfl,rfl,rfl⟩
theorem availabilityFields (s c) : (candidate .availability s c).wire.available = s.wire.available+1 ∧
    (candidate .availability s c).wire.committed = s.wire.committed ∧
    (candidate .availability s c).wire.root = s.wire.root := ⟨rfl,rfl,rfl⟩
theorem aggregateFields (s c) : (candidate .aggregate s c).wire.root = c.wire.body ∧
    (candidate .aggregate s c).wire.phase = ascii "AGGREGATED" := ⟨rfl,rfl⟩

def effectFields (body id kind target : Bytes) : List (Bytes × Scalar) :=
  [(ascii "body_hash",.text body),(ascii "effect_id",.text id),
   (ascii "kind",.text kind),(ascii "target_id",.text target)]

def effectId (c : Command) (suffix : String) : Bytes := ascii "effect:" ++ c.wire.request ++ ascii suffix
def persistFields (c : Command) (next : Bytes) :=
  effectFields next (effectId c ":01:persist") (ascii "PERSIST_STATE") c.wire.actor
def publishFields (c : Command) :=
  effectFields c.wire.body (effectId c ":02:publish") (ascii "PUBLISH_CERTIFICATE") (ascii "validators")

def effectTail (c : Command) (prior next : Bytes) : List (Bytes × Scalar) :=
  [(ascii "formal_semantics_id",.text nativeSemantics),(ascii "next_state_root",.text next),
   (ascii "prior_state_root",.text prior),(ascii "request_id",.text c.wire.request),
   (ascii "round_id",.text c.wire.round),(ascii "schema_version",.text (ascii "1.0.0")),
   (ascii "type_name",.text (ascii "EFFECT_BATCH"))]

def effectPayload (c : Command) (prior next : Bytes) : Bytes :=
  mapHeader 8 ++ textBytes (ascii "effects") ++ [48] ++ be 4 2 ++
  payload (persistFields c next) ++ payload (publishFields c) ++ encodeFields (effectTail c prior next)
def encodeEffects (c : Command) (prior next : Bytes) : Bytes :=
  NativeStateBytes.header 7 ++ sizedBytes (effectPayload c prior next)

def EffectsValid (c : Command) (prior next : Bytes) : Prop :=
  ContentId prior ∧ ContentId next ∧ ContentId c.wire.body ∧
  c.wire.actor ≠ [] ∧ c.wire.request ≠ [] ∧ c.wire.round ≠ [] ∧
  (∀ p ∈ persistFields c next ++ publishFields c ++ effectTail c prior next, ScalarValid p.2) ∧
  (encodeEffects c prior next).length ≤ maxEnvelope
instance (c prior next) : Decidable (EffectsValid c prior next) := by unfold EffectsValid; infer_instance

def walFields (c : Command) (seq : Nat) (prior cmd next effects : Bytes) : List (Bytes × Scalar) :=
  [(ascii "command_id",.text cmd),(ascii "effect_batch_id",.text effects),
   (ascii "formal_semantics_id",.text nativeSemantics),(ascii "next_state_root",.text next),
   (ascii "prior_state_root",.text prior),(ascii "record_kind",.text (ascii "TRANSITION")),
   (ascii "round_id",.text c.wire.round),(ascii "schema_version",.text (ascii "1.0.0")),
   (ascii "sequence",.text (decimal seq)),(ascii "type_name",.text (ascii "WAL_RECORD"))]
def encodeWal (c : Command) (seq : Nat) (prior cmd next effects : Bytes) :=
  encodeEnvelope 8 (walFields c seq prior cmd next effects)
def WalValid (c : Command) (seq : Nat) (prior cmd next effects : Bytes) : Prop :=
  ContentId prior ∧ ContentId cmd ∧ ContentId next ∧ ContentId effects ∧ c.wire.round ≠ [] ∧
  parseDecimal (decimal seq) = some seq ∧ EnvelopeValid 8 (walFields c seq prior cmd next effects)
instance (c seq prior cmd next effects) : Decidable (WalValid c seq prior cmd next effects) := by
  unfold WalValid; infer_instance

def effectDomain := ascii "deltareduce:003:effect-batch:v1"
def walDomain := ascii "deltareduce:003:wal-record:v1"

structure Output where
  next : State
  stateBytes : Bytes
  effects : Bytes
  record : Bytes
  priorId : Bytes
  commandId : Bytes
  nextId : Bytes
  effectsId : Bytes
  recordId : Bytes
  deriving DecidableEq, Repr

def build (sha : Bytes → Bytes) (s : State) (c : Command) (n : State) : Option Output := do
  let priorId ← contentId sha stateDomain (encodeState s.wire)
  let commandId ← contentId sha commandDomain (encodeCommand c.wire)
  let nextId ← contentId sha stateDomain (encodeState n.wire)
  if EffectsValid c priorId nextId then
    let effects := encodeEffects c priorId nextId
    let effectsId ← contentId sha effectDomain effects
    if WalValid c n.sequence priorId commandId nextId effectsId then
      let record := encodeWal c n.sequence priorId commandId nextId effectsId
      let recordId ← contentId sha walDomain record
      some ⟨n,encodeState n.wire,effects,record,priorId,commandId,nextId,effectsId,recordId⟩
    else none
  else none

def execute (sha : Bytes → Bytes) (s : State) (c : Command) : Option Output := do
  let n ← step s c
  build sha s c n

def Built (sha : Bytes → Bytes) (s : State) (c : Command) (n : State) (out : Output) : Prop :=
  out.next = n ∧ out.stateBytes = encodeState n.wire ∧
  contentId sha stateDomain (encodeState s.wire) = some out.priorId ∧
  contentId sha commandDomain (encodeCommand c.wire) = some out.commandId ∧
  contentId sha stateDomain out.stateBytes = some out.nextId ∧
  EffectsValid c out.priorId out.nextId ∧
  out.effects = encodeEffects c out.priorId out.nextId ∧
  contentId sha effectDomain out.effects = some out.effectsId ∧
  WalValid c n.sequence out.priorId out.commandId out.nextId out.effectsId ∧
  out.record = encodeWal c n.sequence out.priorId out.commandId out.nextId out.effectsId ∧
  contentId sha walDomain out.record = some out.recordId

theorem buildSound {sha s c n out} (ok : build sha s c n = some out) : Built sha s c n out := by
  simp only [build,bind,Option.bind] at ok
  split at ok <;> try contradiction
  try dsimp only at ok
  split at ok <;> try contradiction
  try dsimp only at ok
  split at ok <;> try contradiction
  try dsimp only at ok
  split at ok <;> try contradiction
  try dsimp only at ok
  split at ok <;> try contradiction
  try dsimp only at ok
  split at ok <;> try contradiction
  try dsimp only at ok
  split at ok <;> try contradiction
  try dsimp only at ok
  cases Option.some.inj ok
  simp_all [Built]

theorem buildFromComponents (sha s c n out) (h : Built sha s c n out) :
    build sha s c n = some out := by
  obtain ⟨next,state,prior,command,nh,valid,effects,eh,wvalid,record,rh⟩ := h
  simp only [state] at nh
  simp only [effects] at eh
  simp only [record] at rh
  simp only [build,prior,command,nh,bind,Option.bind,if_pos valid,eh,if_pos wvalid,rh]
  congr 1
  cases out
  simp_all

theorem executeSound {sha s c out} (ok : execute sha s c = some out) :
    step s c = some out.next ∧ Built sha s c out.next out := by
  unfold execute at ok
  cases h : step s c with
  | none => simp [h] at ok
  | some n =>
    simp only [h,bind,Option.bind] at ok
    have b := buildSound ok
    constructor
    · simp only [b.1]
    · simpa only [b.1] using b

theorem executeFromComponents (sha s c n out) (h : step s c = some n)
    (b : Built sha s c n out) : execute sha s c = some out := by
  simp [execute,h,buildFromComponents sha s c n out b]

def fromBytes (sha : Bytes → Bytes) (prior command : Bytes) : Option Output := do
  let s ← decodeState prior
  let c ← decodeCommand command
  execute sha s c

theorem bytesSound {sha prior command out} (ok : fromBytes sha prior command = some out) :
    ∃ s c, decodeState prior = some s ∧ decodeCommand command = some c ∧
      step s c = some out.next ∧ Built sha s c out.next out ∧
      encodeState s.wire = prior ∧ encodeCommand c.wire = command := by
  unfold fromBytes at ok
  cases hs : decodeState prior with
  | none => simp [hs] at ok
  | some s =>
    simp only [hs,bind,Option.bind] at ok
    cases hc : decodeCommand command with
    | none => simp [hc] at ok
    | some c =>
      simp only [hc] at ok
      have h := executeSound ok
      exact ⟨s,c,rfl,rfl,h.1,h.2,(stateSound hs).2,(commandSound hc).2⟩

theorem bytesFromComponents (sha prior command s c out)
    (hs : decodeState prior = some s) (hc : decodeCommand command = some c)
    (computed : execute sha s c = some out) : fromBytes sha prior command = some out := by
  simp [fromBytes,hs,hc,computed]

/- This relation compares computed fields; it never accepts a caller-provided
transition predicate. No receipt/exposure or physical durability follows. -/
def replayEntry (sha : Bytes → Bytes) (prior : Bytes) (e : NativeWalBytes.Entry) : Option Output := do
  if e.kind = 1 then
    let out ← fromBytes sha prior e.command
    if e.state = out.stateBytes ∧ e.effects = out.effects ∧ e.record = out.record then some out else none
  else none

theorem replayComputed {sha prior e out} (ok : replayEntry sha prior e = some out) :
    e.kind = 1 ∧ fromBytes sha prior e.command = some out ∧
    e.state = out.stateBytes ∧ e.effects = out.effects ∧ e.record = out.record := by
  unfold replayEntry at ok
  split at ok
  · rename_i kind
    cases h : fromBytes sha prior e.command with
    | none => simp [h] at ok
    | some value =>
      simp only [h,bind,Option.bind] at ok
      split at ok
      · rename_i bytes
        cases Option.some.inj ok
        exact ⟨kind,rfl,bytes⟩
      · contradiction
  · contradiction

theorem replayFromComputed (sha prior e out) (kind : e.kind = 1)
    (computed : fromBytes sha prior e.command = some out)
    (bytes : e.state = out.stateBytes ∧ e.effects = out.effects ∧ e.record = out.record) :
    replayEntry sha prior e = some out := by simp [replayEntry,kind,computed,bytes]

theorem replayRejectChanged {sha prior e out} (computed : fromBytes sha prior e.command = some out)
    (wrong : e.state ≠ out.stateBytes ∨ e.effects ≠ out.effects ∨ e.record ≠ out.record) :
    replayEntry sha prior e = none := by
  simp only [replayEntry,computed,bind,Option.bind]
  split
  · split
    · rename_i h; rcases wrong with h₁ | h₂ | h₃ <;> simp_all
    · rfl
  · rfl

theorem scannedExecution {sha raw result prior i p out}
    (scanned : NativeWalScan.check sha raw = some result)
    (atIndex : result.pieces[i]? = some p)
    (replayed : replayEntry sha prior p.entry = some out) :
    p.entry.sequence = 1+i ∧ NativeWalBytes.encode sha p.entry = p.bytes ∧
    ∃ s c, decodeState prior = some s ∧ decodeCommand p.entry.command = some c ∧
      step s c = some out.next ∧ Built sha s c out.next out ∧
      p.entry.state = out.stateBytes ∧ p.entry.effects = out.effects ∧ p.entry.record = out.record := by
  have indexed : (NativeWalScan.entries result)[i]? = some p.entry := by
    simp only [NativeWalScan.entries,List.getElem?_map,atIndex,Option.map_some]
  have member : p ∈ result.pieces := List.mem_of_getElem? atIndex
  have canonical := NativeWalScan.scannedCanonical sha raw result
    (NativeWalScan.checkedSound sha raw result scanned).1 p member
  have r := replayComputed replayed
  obtain ⟨s,c,hs,hc,step,built,_,_⟩ := bytesSound r.2.1
  exact ⟨NativeWalScan.checkedPosition sha raw result scanned i p.entry indexed,canonical.2,
    s,c,hs,hc,step,built,r.2.2⟩

end DeltaReduce.NativeTransition
