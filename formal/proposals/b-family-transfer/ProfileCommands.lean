import ProfileNativeHeader
import DeltaReduce.NativeTransition

/-! T047/T053. The original seven coarse command rules in the parameterized
successor byte generation. Pure transition fields are reused; no legacy state
or command is decoded, serialized or relabeled. This is one producer conjunct,
not certificate admission, initial origin, persistence or public refinement. -/
namespace DeltaReduce.ProfileSource.Commands
open NativeReceiptBytes NativeVoteBytes NativePolicyCodec

/-- Field-only reuse of the native transition; never a legacy serialization. -/
def nativeState (s : NativeHeader.Coarse) : NativeStateBytes.State :=
  ⟨⟨s.available,s.committed,s.config,NativeIscCertificate.number s.sequence,
    NativeIscCertificate.number s.height,s.parent,s.phase,s.round,s.root,s.total,
    NativeIscCertificate.number s.view⟩,s.sequence,s.height,s.view⟩
def commandFormat : Configuration.Format := Configuration.object [
  ("actor_id",.text),("body_hash",.text),("command_kind",.text),
  ("formal_semantics_id",.text),("height",.text),("logical_tick",.text),
  ("request_id",.text),("round_id",.text),("schema_version",.text),
  ("type_name",.text),("view",.text)]

def commandBytes (tree : Value) : Option Bytes := do
  let payload ← Configuration.encode commandFormat tree
  let raw := [68,82,67,49,1,0,0,6] ++ sizedBytes payload
  if raw.length ≤ maxEnvelope then some raw else none

structure Command where
  original : Value
  semantics : Bytes
  native : NativeStateBytes.Command

def readCommand (v : Value) : Option Command := do
  let actor ← Configuration.textField commandFormat v "actor_id"
  let body ← Configuration.textField commandFormat v "body_hash"
  let name ← Configuration.textField commandFormat v "command_kind"
  let sigma ← Configuration.textField commandFormat v "formal_semantics_id"
  let heightRaw ← Configuration.textField commandFormat v "height"
  let tickRaw ← Configuration.textField commandFormat v "logical_tick"
  let request ← Configuration.textField commandFormat v "request_id"
  let round ← Configuration.textField commandFormat v "round_id"
  let viewRaw ← Configuration.textField commandFormat v "view"
  let height ← parseDecimal heightRaw
  let tick ← parseDecimal tickRaw
  let view ← parseDecimal viewRaw
  if ContentId sigma ∧ ContentId body ∧ actor ≠ [] ∧ name ≠ [] ∧ request ≠ [] ∧ round ≠ [] ∧
      Configuration.textField commandFormat v "schema_version" = some (ascii "1.0.0") ∧
      Configuration.textField commandFormat v "type_name" = some (ascii "COMMAND") then
    some ⟨v,sigma,⟨⟨actor,body,name,heightRaw,tickRaw,request,round,viewRaw⟩,height,tick,view⟩⟩
  else none

def record (values : List Value) : Value := values.foldr Value.pair .end

def stateTree (sigma : Bytes) (s : NativeStateBytes.State) : Value := record [
  .number s.wire.available,.number s.wire.committed,.text s.wire.config,
  .text s.wire.sequence,.text sigma,.text s.wire.height,.text s.wire.parent,
  .text s.wire.phase,.text s.wire.round,.text (ascii "1.0.0"),.text s.wire.root,
  .number s.wire.total,.text (ascii "ROUND_STATE"),.text s.wire.view]

structure Edge where
  before : NativeHeader.Coarse
  command : Command
  action : NativeTransition.Action
  following : NativeHeader.Coarse
  nextBytes : Bytes

def derive (stateValue commandValue : Value) (stateRaw commandRaw : Bytes) : Option Edge := do
  let before ← NativeHeader.readCoarse stateValue
  let command ← readCommand commandValue
  let action ← NativeTransition.parseAction command.native.wire.commandKind
  if NativeHeader.stateBytes stateValue = some stateRaw ∧
      commandBytes commandValue = some commandRaw ∧
      command.semantics = before.semantics ∧
      NativeTransition.Enabled action (nativeState before) command.native then
    let tree := stateTree before.semantics
      (NativeTransition.candidate action (nativeState before) command.native)
    let following ← NativeHeader.readCoarse tree
    let raw ← NativeHeader.stateBytes tree
    some ⟨before,command,action,following,raw⟩
  else none

structure Source (sv cv : Value) (sr cr : Bytes) (e : Edge) : Prop where
  before : NativeHeader.readCoarse sv = some e.before
  command : readCommand cv = some e.command
  action : NativeTransition.parseAction e.command.native.wire.commandKind = some e.action
  stateRaw : NativeHeader.stateBytes sv = some sr
  commandRaw : commandBytes cv = some cr
  semantics : e.command.semantics = e.before.semantics
  enabled : NativeTransition.Enabled e.action (nativeState e.before) e.command.native
  following : NativeHeader.readCoarse
    (stateTree e.before.semantics (NativeTransition.candidate e.action
      (nativeState e.before) e.command.native)) = some e.following
  raw : NativeHeader.stateBytes
    (stateTree e.before.semantics (NativeTransition.candidate e.action
      (nativeState e.before) e.command.native)) = some e.nextBytes

theorem derivedSource {sv cv sr cr e} (ok : derive sv cv sr cr = some e) : Source sv cv sr cr e := by
  unfold derive at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨s,hs,c,hc,a,ha,last⟩ := ok
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨n,hn,raw,hr,last⟩ := last
  cases Option.some.inj last
  exact ⟨hs,hc,ha,valid.1,valid.2.1,valid.2.2.1,valid.2.2.2,hn,hr⟩

theorem derivedComplete {sv cv sr cr e} (h : Source sv cv sr cr e) :
    derive sv cv sr cr = some e := by
  unfold derive
  rw [h.before,h.command]
  dsimp only [Bind.bind,Option.bind]
  rw [h.action]
  dsimp only
  rw [if_pos ⟨h.stateRaw,h.commandRaw,h.semantics,h.enabled⟩]
  rw [h.following]
  dsimp only
  rw [h.raw]

theorem originalState {sv cv sr cr e} (ok : derive sv cv sr cr = some e) :
    e.before.original = sv := (NativeHeader.coarseSource (derivedSource ok).before).1

theorem computedState {sv cv sr cr e} (ok : derive sv cv sr cr = some e) :
    e.following.original = stateTree e.before.semantics
      (NativeTransition.candidate e.action (nativeState e.before) e.command.native) :=
  (NativeHeader.coarseSource (derivedSource ok).following).1

theorem noSuppliedNextState {sv cv sr cr left right}
    (a : derive sv cv sr cr = some left) (b : derive sv cv sr cr = some right) : left = right :=
  Option.some.inj (a.symm.trans b)

theorem originalPhaseGuard {sv cv sr cr e} (ok : derive sv cv sr cr = some e) :
    NativeTransition.PhaseGuard e.action (nativeState e.before) e.command.native :=
  (derivedSource ok).enabled.2.2.2.1

theorem actualCommandContext {sv cv sr cr e} (ok : derive sv cv sr cr = some e) :
    e.command.native.wire.round = e.before.round ∧ e.command.native.height = e.before.height :=
  ⟨(derivedSource ok).enabled.1,(derivedSource ok).enabled.2.1⟩

theorem sameGeneration {sv cv sr cr e} (ok : derive sv cv sr cr = some e) :
    e.command.semantics = e.before.semantics := (derivedSource ok).semantics

theorem nativeCandidateSequence {sv cv sr cr e} (ok : derive sv cv sr cr = some e) :
    (NativeTransition.candidate e.action (nativeState e.before) e.command.native).sequence =
      if e.action = .config then e.before.sequence else e.before.sequence+1 :=
  NativeTransition.candidateSequence _ _ _

def effectFormat : Configuration.Format := Configuration.object [
  ("body_hash",.text),("effect_id",.text),("kind",.text),("target_id",.text)]
def effectsFormat : Configuration.Format := Configuration.object [
  ("effects",.vector effectFormat),("formal_semantics_id",.text),("next_state_root",.text),
  ("prior_state_root",.text),("request_id",.text),("round_id",.text),
  ("schema_version",.text),("type_name",.text)]
def walFormat : Configuration.Format := Configuration.object [
  ("command_id",.text),("effect_batch_id",.text),("formal_semantics_id",.text),
  ("next_state_root",.text),("prior_state_root",.text),("record_kind",.text),
  ("round_id",.text),("schema_version",.text),("sequence",.text),("type_name",.text)]

def envelope (code : Nat) (fmt : Configuration.Format) (tree : Value) : Option Bytes := do
  let payload ← Configuration.encode fmt tree
  let raw := NativeStateBytes.header code ++ sizedBytes payload
  if raw.length ≤ maxEnvelope then some raw else none

def effectsTree (e : Edge) (prior next : Bytes) : Value :=
  let c := e.command.native
  record [.items [
    record [.text next,.text (NativeTransition.effectId c ":01:persist"),
      .text (ascii "PERSIST_STATE"),.text c.wire.actor],
    record [.text c.wire.body,.text (NativeTransition.effectId c ":02:publish"),
      .text (ascii "PUBLISH_CERTIFICATE"),.text (ascii "validators")]],
    .text e.before.semantics,.text next,.text prior,.text c.wire.request,.text c.wire.round,
    .text (ascii "1.0.0"),.text (ascii "EFFECT_BATCH")]

def walTree (e : Edge) (prior cmd next effects : Bytes) : Value :=
  record [.text cmd,.text effects,.text e.before.semantics,.text next,.text prior,
    .text (ascii "TRANSITION"),.text e.command.native.wire.round,.text (ascii "1.0.0"),
    .text (NativeTransition.decimal e.following.sequence),.text (ascii "WAL_RECORD")]

structure Output where
  edge : Edge
  effects : Bytes
  record : Bytes
  priorId : Bytes
  commandId : Bytes
  nextId : Bytes
  effectsId : Bytes
  recordId : Bytes

def execute (sha : Bytes → Bytes) (sv cv : Value) (sr cr : Bytes) : Option Output := do
  let e ← derive sv cv sr cr
  let prior ← NativeStateBytes.contentId sha NativeStateBytes.stateDomain sr
  let command ← NativeStateBytes.contentId sha NativeStateBytes.commandDomain cr
  let next ← NativeStateBytes.contentId sha NativeStateBytes.stateDomain e.nextBytes
  let effects ← envelope 7 effectsFormat (effectsTree e prior next)
  let effectsId ← NativeStateBytes.contentId sha NativeTransition.effectDomain effects
  let wal ← envelope 8 walFormat (walTree e prior command next effectsId)
  let walId ← NativeStateBytes.contentId sha NativeTransition.walDomain wal
  some ⟨e,effects,wal,prior,command,next,effectsId,walId⟩

structure OutputSource (sha : Bytes → Bytes) (sv cv : Value) (sr cr : Bytes) (out : Output) : Prop where
  edge : derive sv cv sr cr = some out.edge
  prior : NativeStateBytes.contentId sha NativeStateBytes.stateDomain sr = some out.priorId
  command : NativeStateBytes.contentId sha NativeStateBytes.commandDomain cr = some out.commandId
  next : NativeStateBytes.contentId sha NativeStateBytes.stateDomain out.edge.nextBytes = some out.nextId
  effects : envelope 7 effectsFormat (effectsTree out.edge out.priorId out.nextId) = some out.effects
  effectsId : NativeStateBytes.contentId sha NativeTransition.effectDomain out.effects = some out.effectsId
  wal : envelope 8 walFormat (walTree out.edge out.priorId out.commandId out.nextId out.effectsId) = some out.record
  walId : NativeStateBytes.contentId sha NativeTransition.walDomain out.record = some out.recordId

theorem executedSource {sha sv cv sr cr out} (ok : execute sha sv cv sr cr = some out) :
    OutputSource sha sv cv sr cr out := by
  unfold execute at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨e,he,p,hp,c,hc,n,hn,f,hf,fi,hfi,w,hw,wi,hwi,last⟩ := ok
  cases Option.some.inj last
  exact ⟨he,hp,hc,hn,hf,hfi,hw,hwi⟩

theorem executedComplete {sha sv cv sr cr out} (h : OutputSource sha sv cv sr cr out) :
    execute sha sv cv sr cr = some out := by
  unfold execute
  rw [h.edge]
  dsimp only [Bind.bind,Option.bind]
  rw [h.prior,h.command,h.next]
  dsimp only
  rw [h.effects]
  dsimp only
  rw [h.effectsId]
  dsimp only
  rw [h.wal]
  dsimp only
  rw [h.walId]

def checkStored (sha : Bytes → Bytes) (sv cv : Value) (sr : Bytes)
    (entry : NativeWalBytes.Entry) : Option Output := do
  if entry.kind = 1 then
    let out ← execute sha sv cv sr entry.command
    if entry.state = out.edge.nextBytes ∧ entry.effects = out.effects ∧ entry.record = out.record
      then some out else none
  else none

theorem storedComputed {sha sv cv sr entry out}
    (ok : checkStored sha sv cv sr entry = some out) :
    entry.kind = 1 ∧ execute sha sv cv sr entry.command = some out ∧
    entry.state = out.edge.nextBytes ∧ entry.effects = out.effects ∧ entry.record = out.record := by
  unfold checkStored at ok
  split at ok <;> try contradiction
  rename_i kind
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨computed,hc,last⟩ := ok
  split at last <;> try contradiction
  rename_i same
  cases Option.some.inj last
  exact ⟨kind,hc,same⟩

/-- The outer scan establishes physical-slot continuity. The inner coarse
counter is never substituted for it by this computation check. -/
theorem physicalSlotIndependent (sha sv cv sr entry slot) :
    checkStored sha sv cv sr {entry with sequence := slot} = checkStored sha sv cv sr entry := rfl

end DeltaReduce.ProfileSource.Commands

