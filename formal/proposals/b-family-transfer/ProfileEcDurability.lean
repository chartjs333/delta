import ProfileEcFinalization
import ProfileImport

/-! T047/T053, scope18. Isolated PROFILE-EC-COMMIT-V1 byte association and
persist-before-expose machine. These are source conjuncts, not a replacement
for the complete producing fold. No public acceptance or imported durable bit
is a premise. The successful barrier is the existing Profile T primitive.
Original native WAL bytes are separate from the companion ordinal namespace. -/
namespace DeltaReduce.ProfileSource.EcDurability
open NativeReceiptBytes (Bytes be)
open NativeVoteBytes (ascii ContentId)
open Control (Node Nodes Fields)

def recordDomain := ascii "deltareduce.profile.ec-commit.record.v1"
def sourceDomain := ascii "deltareduce.profile.ec-commit.source.v1"
def journalDomain := ascii "deltareduce.profile.ec-commit.journals.v1"

def texts : List (String × Bytes) → Fields
  | [] => .nil
  | (name,value)::rest => .cons (ascii name) (.text value) (texts rest)

def nodeList : List Node → Nodes
  | [] => .nil
  | x::xs => .cons x (nodeList xs)

def sourceFrames (start : Nat) : List Bytes → Bytes
  | [] => []
  | raw::rest => be 8 start ++ be 4 raw.length ++ raw ++ sourceFrames (start+1) rest

def sourcePreimage (boot : Bytes) (originals : List Bytes) : Bytes :=
  sourceDomain ++ [0] ++ boot ++ be 8 originals.length ++ sourceFrames 0 originals

def sourceId (sha : Bytes → Bytes) (boot : Bytes) (originals : List Bytes) : Bytes :=
  Index.rawId sha (sourcePreimage boot originals)

def journalId (sha : Bytes → Bytes) (cuts : List Node) : Bytes :=
  Index.rawId sha (journalDomain ++ [0] ++ Control.encode (.array (nodeList cuts)))

/-- Exact material is provided by original-source decoding and native EC
computation. This structure itself is NOT an authority or legality predicate. -/
structure Material where
  bootstrap : Bytes
  actor : Bytes
  previous : Bytes
  ordinal : Nat
  eventIndex : Nat
  originals : List Bytes
  event : Bytes
  priorPolicy : Bytes
  nextPolicy : Bytes
  roundState : Bytes
  certificate : Bytes
  seed : Bytes
  cuts : List Node

def fields (sha : Bytes → Bytes) (m : Material) : Fields := texts [
  ("actor_id",m.actor),
  ("bootstrap_id",m.bootstrap),
  ("certificate_raw_id",Index.rawId sha m.certificate),
  ("event_index",ascii (toString m.eventIndex)),
  ("event_raw_id",Index.rawId sha m.event),
  ("journal_prefix_id",journalId sha m.cuts),
  ("next_policy_raw_id",Index.rawId sha m.nextPolicy),
  ("ordinal",ascii (toString m.ordinal)),
  ("previous_record_id",m.previous),
  ("prior_policy_raw_id",Index.rawId sha m.priorPolicy),
  ("profile_id",ascii "snapshot-provenance-linux-single-epoch-v1"),
  ("round_state_raw_id",Index.rawId sha m.roundState),
  ("schema_version",ascii "1"),
  ("seed_raw_id",Index.rawId sha m.seed),
  ("source_prefix_id",sourceId sha m.bootstrap m.originals),
  ("type_name",ascii "EC_COMMIT")]

def raw (sha : Bytes → Bytes) (m : Material) : Bytes := Control.encode (.object (fields sha m))

def frame (sha : Bytes → Bytes) (original : Bytes) : Option Bytes :=
  let digest := sha (recordDomain ++ [0] ++ original)
  if original.length ≤ 4*1024*1024 ∧ digest.length = 32 then
    some (be 4 original.length ++ original ++ digest) else none

def Material.Valid (sha : Bytes → Bytes) (m : Material) : Prop :=
  ContentId m.bootstrap ∧ m.actor ≠ [] ∧ Control.safe m.actor = true ∧
  0 < m.ordinal ∧ m.ordinal ≤ 1000000 ∧ 0 < m.eventIndex ∧ m.eventIndex < 1000000 ∧
  m.originals.length = m.eventIndex ∧
  (if m.ordinal = 1 then m.previous = ascii "GENESIS" else ContentId m.previous) ∧
  (m.originals.all (fun p => decide (p.length ≤ 4*1024*1024))) = true ∧
  (∀ id ∈ [Index.rawId sha m.certificate,Index.rawId sha m.event,journalId sha m.cuts,
    Index.rawId sha m.nextPolicy,Index.rawId sha m.priorPolicy,Index.rawId sha m.roundState,
    Index.rawId sha m.seed,sourceId sha m.bootstrap m.originals], ContentId id) ∧
  (Control.encode (.array (nodeList m.cuts))).length ≤ 4*1024*1024 ∧
  Control.canonicalFields (fields sha m) = true
instance (sha m) : Decidable (Material.Valid sha m) := by unfold Material.Valid; infer_instance

def encode (sha : Bytes → Bytes) (m : Material) : Option Bytes := do
  let _ ← Import.cuts sha m.cuts
  if m.Valid sha then frame sha (raw sha m) else none

def bindOriginal (sha : Bytes → Bytes) (m : Material) (original : Bytes) : Option Bytes := do
  let expected ← encode sha m
  if original = expected then some original else none

theorem wholeOriginalBinding {sha m original out}
    (ok : bindOriginal sha m original = some out) :
    out = original ∧ encode sha m = some original := by
  simp only [bindOriginal,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨expected,he,last⟩ := ok
  split at last <;> try contradiction
  rename_i same
  cases Option.some.inj last
  exact ⟨rfl,same ▸ he⟩

theorem changedOriginalRejected {sha m original other}
    (good : bindOriginal sha m original = some original) (different : other ≠ original) :
    bindOriginal sha m other = none := by
  have expected := (wholeOriginalBinding good).2
  simp [bindOriginal,expected,different]

/-- Companion ordinals/links are disjoint from the native physical WAL. Each
typed material must encode the complete original frame; no unknown tail can
be hidden by proposing a shorter typed list. -/
def chain (sha : Bytes → Bytes) (boot actor previous : Bytes) (ordinal lastEvent : Nat) :
    List Material → Option (List Bytes)
  | [] => some []
  | m::rest => do
    if m.bootstrap = boot ∧ m.actor = actor ∧ m.previous = previous ∧
        m.ordinal = ordinal ∧ lastEvent < m.eventIndex then
      let whole ← encode sha m
      let id ← NativeStateBytes.contentId sha recordDomain (raw sha m)
      let tail ← chain sha boot actor id (ordinal+1) m.eventIndex rest
      some (whole::tail)
    else none

inductive ChainSource (sha : Bytes → Bytes) (boot actor : Bytes) :
    Bytes → Nat → Nat → List Material → List Bytes → Prop where
  | nil (previous ordinal lastEvent) : ChainSource sha boot actor previous ordinal lastEvent [] []
  | cons {previous ordinal lastEvent m rest whole id tail}
      (owner : m.bootstrap = boot ∧ m.actor = actor ∧ m.previous = previous ∧
        m.ordinal = ordinal ∧ lastEvent < m.eventIndex)
      (encoded : encode sha m = some whole)
      (identity : NativeStateBytes.contentId sha recordDomain (raw sha m) = some id)
      (next : ChainSource sha boot actor id (ordinal+1) m.eventIndex rest tail) :
      ChainSource sha boot actor previous ordinal lastEvent (m::rest) (whole::tail)

theorem chainSound {sha boot actor previous ordinal lastEvent ms frames}
    (ok : chain sha boot actor previous ordinal lastEvent ms = some frames) :
    ChainSource sha boot actor previous ordinal lastEvent ms frames := by
  induction ms generalizing previous ordinal lastEvent frames with
  | nil => cases Option.some.inj ok; exact .nil _ _ _
  | cons m rest ih =>
    simp only [chain] at ok
    split at ok <;> try contradiction
    rename_i owner
    simp only [Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨whole,he,id,hi,tail,ht,last⟩ := ok
    cases Option.some.inj last
    exact .cons owner he hi (ih ht)

theorem chainComplete {sha boot actor previous ordinal lastEvent ms frames}
    (source : ChainSource sha boot actor previous ordinal lastEvent ms frames) :
    chain sha boot actor previous ordinal lastEvent ms = some frames := by
  induction source with
  | nil => rfl
  | cons owner encoded identity next ih =>
    simp only [chain,if_pos owner,encoded,identity,Bind.bind,Option.bind,ih]

theorem chainOriginalPosition {sha boot actor previous ordinal lastEvent ms frames}
    (source : ChainSource sha boot actor previous ordinal lastEvent ms frames) {n m}
    (atOriginal : ms[n]? = some m) :
    m.bootstrap = boot ∧ m.actor = actor ∧ m.ordinal = ordinal+n ∧
      ∃ bytes, frames[n]? = some bytes ∧ encode sha m = some bytes := by
  induction source generalizing n with
  | nil => simp at atOriginal
  | @cons previous ordinal lastEvent head rest whole id tail owner encoded identity next ih =>
    cases n with
    | zero =>
      have same : head = m := by simpa using atOriginal
      subst m
      exact ⟨owner.1,owner.2.1,by simpa using owner.2.2.2.1,whole,rfl,encoded⟩
    | succ n =>
      obtain ⟨hb,ha,ho,bytes,hp,he⟩ := ih (by simpa using atOriginal)
      exact ⟨hb,ha,by omega,bytes,by simpa using hp,he⟩

theorem chainNoRecordErasure {sha boot actor previous ordinal lastEvent ms frames}
    (source : ChainSource sha boot actor previous ordinal lastEvent ms frames) :
    ms.length = frames.length := by
  induction source with
  | nil => rfl
  | cons owner encoded identity next ih => simpa using congrArg Nat.succ ih

def bindJournal (sha : Bytes → Bytes) (boot actor : Bytes) (ms : List Material)
    (original : Bytes) : Option (List Bytes) := do
  let frames ← chain sha boot actor (ascii "GENESIS") 1 0 ms
  if frames.flatten = original then some frames else none

theorem wholeJournalChecked {sha boot actor ms original frames}
    (ok : bindJournal sha boot actor ms original = some frames) :
    ChainSource sha boot actor (ascii "GENESIS") 1 0 ms frames ∧
    frames.flatten = original ∧ ms.length = frames.length := by
  simp only [bindJournal,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨fs,hc,last⟩ := ok
  split at last <;> try contradiction
  rename_i exactBytes
  cases Option.some.inj last
  exact ⟨chainSound hc,exactBytes,chainNoRecordErasure (chainSound hc)⟩

/-- Exact previous-companion inventory association. These are the already
decoded complete cut rows; the enclosing importer still resolves every other
journal. A missing nonempty companion is never equated with empty. -/
def companionCut (sha : Bytes → Bytes) (actor original : Bytes) (count : Nat)
    (cuts : List Import.JournalCut) : Bool :=
  let selected := cuts.filter (fun row => row.actor == actor && row.journal == ascii "PROFILE-EC-COMMIT-V1")
  match selected with
  | [] => decide (original = [] ∧ count = 0)
  | [row] => decide (row.span.reference.id = Index.rawId sha original ∧
      row.span.reference.length = original.length ∧ row.span.count = count ∧
      row.span.first = (if count = 0 then 0 else 1) ∧ row.span.last = count)
  | _ => false

theorem nonemptyCompanionHasOriginalCut {sha actor original count cuts}
    (checked : companionCut sha actor original count cuts = true) (nonempty : original ≠ []) :
    ∃ row ∈ cuts, row.actor = actor ∧ row.journal = ascii "PROFILE-EC-COMMIT-V1" ∧
      row.span.reference.id = Index.rawId sha original ∧ row.span.reference.length = original.length ∧
      row.span.count = count ∧ row.span.first = (if count = 0 then 0 else 1) ∧ row.span.last = count := by
  unfold companionCut at checked
  cases eq : cuts.filter (fun r => r.actor == actor && r.journal == ascii "PROFILE-EC-COMMIT-V1") with
  | nil => simp [eq,nonempty] at checked
  | cons row rest =>
    cases rest with
    | nil =>
      have member : row ∈ cuts.filter (fun r => r.actor == actor && r.journal == ascii "PROFILE-EC-COMMIT-V1") := by
        rw [eq]; simp
      simp only [List.mem_filter,Bool.and_eq_true,beq_iff_eq] at member
      exact ⟨row,member.1,member.2.1,member.2.2,of_decide_eq_true (by simpa only [eq] using checked)⟩
    | cons head tail => simp [eq] at checked

/-- All preceding occurrences are retained at their original positions.
The outer Index checker still binds the descriptors to original source bytes. -/
def atEvent (index : Index.Bound) (event : Index.Event) : Option (List Bytes) :=
  if index.events[event.position]? = some event ∧
      index.eventDescriptors = index.events.map Index.Event.descriptor then
    some ((index.eventDescriptors.take event.position).map Control.encode) else none

theorem prefixPosition {index event result}
    (ok : atEvent index event = some result) {n : Nat} (early : n < event.position) :
    result[n]? = (index.eventDescriptors[n]?).map Control.encode := by
  unfold atEvent at ok
  split at ok <;> try contradiction
  cases Option.some.inj ok
  simp [List.getElem?_map,early]

/-- Material is constructed from the COMPUTED Whole and original event/cut;
neither a supplied successor policy nor a supplied E is trusted. -/
def material (boot previous : Bytes) (ordinal : Nat) (originals : List Bytes)
    (cuts : List Node) (event : Index.Event) (whole : EcFinalization.Whole)
    (policyRaw stateRaw : Bytes) : Material :=
  ⟨boot,event.actor,previous,ordinal,event.position,originals,Control.encode event.descriptor,
   policyRaw,whole.source.candidate.update.raw,stateRaw,
   whole.source.candidate.certificate.raw,whole.source.candidate.selected.value.seed.raw,cuts⟩

def checkStep (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : NativePolicyCodec.Value)
    (originals : Collections.Originals) (cut tick : Nat) (bodyId : Bytes)
    (rows : List ConfigurationQC.Received) (event : Index.Event) (origins : List Nat)
    (index : Index.Bound) (boot previous : Bytes) (ordinal : Nat) (cuts : List Node)
    (originalFrame : Bytes) : Option EcFinalization.Whole := do
  let whole ← EcFinalization.checkWhole sha enrolled actor configRaw stateRaw policyRaw
    stateValue originals cut tick bodyId rows
  let checked ← EcFinalization.bindEvent event whole policyRaw stateRaw actor cut origins
  let pre ← atEvent index event
  let _ ← bindOriginal sha (material boot previous ordinal pre cuts event checked policyRaw stateRaw)
    originalFrame
  some checked

theorem checkedStep {sha enrolled actor configRaw stateRaw policyRaw stateValue originals cut tick
    bodyId rows event origins index boot previous ordinal cuts originalFrame whole}
    (ok : checkStep sha enrolled actor configRaw stateRaw policyRaw stateValue originals cut tick
      bodyId rows event origins index boot previous ordinal cuts originalFrame = some whole) :
    EcFinalization.checkWhole sha enrolled actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows = some whole ∧
    EcFinalization.EventChecks event whole.source policyRaw stateRaw actor cut origins ∧
    ∃ pre, atEvent index event = some pre ∧
      encode sha (material boot previous ordinal pre cuts event whole policyRaw stateRaw) =
        some originalFrame := by
  simp only [checkStep,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨w,hw,checked,hc,pre,hp,bytes,hb,last⟩ := ok
  obtain ⟨same,events⟩ := EcFinalization.originalEventChecked hc
  subst checked
  cases Option.some.inj last
  exact ⟨hw,events,pre,hp,(wholeOriginalBinding hb).2⟩

def lastIdentity (sha : Bytes → Bytes) (ms : List Material) : Option Bytes :=
  match ms.getLast? with
  | none => some (ascii "GENESIS")
  | some m => NativeStateBytes.contentId sha recordDomain (raw sha m)

/-- Compose the exact original companion, cut inventory and computed EC step.
No caller-supplied ordinal/predecessor is used for the new record. A lawful
full source fold still supplies the independently decoded index and prior state. -/
def checkStorage (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : NativePolicyCodec.Value)
    (originals : Collections.Originals) (cut tick : Nat) (bodyId : Bytes)
    (rows : List ConfigurationQC.Received) (event : Index.Event) (origins : List Nat)
    (index : Index.Bound) (boot : Bytes) (ms : List Material) (prior : Bytes)
    (cutNodes : List Node) (originalFrame : Bytes) : Option EcFinalization.Whole := do
  let frames ← bindJournal sha boot actor ms prior
  let cuts ← Import.cuts sha cutNodes
  let previous ← lastIdentity sha ms
  if companionCut sha actor prior frames.length cuts = true ∧
      (∀ m ∈ ms, m.eventIndex < event.position) then
    checkStep sha enrolled actor configRaw stateRaw policyRaw stateValue originals cut tick
      bodyId rows event origins index boot previous (ms.length+1) cutNodes originalFrame
  else none

theorem storageAndNativeJoined {sha enrolled actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId rows event origins index boot ms prior cutNodes originalFrame whole}
    (ok : checkStorage sha enrolled actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows event origins index boot ms prior cutNodes originalFrame = some whole) :
    ∃ frames cuts previous,
      ChainSource sha boot actor (ascii "GENESIS") 1 0 ms frames ∧
      frames.flatten = prior ∧ ms.length = frames.length ∧
      Import.cuts sha cutNodes = some cuts ∧
      companionCut sha actor prior frames.length cuts = true ∧
      (∀ m ∈ ms, m.eventIndex < event.position) ∧
      lastIdentity sha ms = some previous ∧
      checkStep sha enrolled actor configRaw stateRaw policyRaw stateValue originals cut tick
        bodyId rows event origins index boot previous (ms.length+1) cutNodes originalFrame = some whole := by
  simp only [checkStorage,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨frames,hf,cuts,hc,previous,hp,last⟩ := ok
  split at last <;> try contradiction
  rename_i guards
  obtain ⟨history,raws,length⟩ := wholeJournalChecked hf
  exact ⟨frames,cuts,previous,history,raws,length,hc,guards.1,guards.2,hp,last⟩

/- One-transaction machine. `current` and `exposed` below are logical history,
not a restart cache. Crash does not erase committed EC/observations. A full
recovered current (including later ABORT) is handled by replayStutters above
and the enclosing producing fold, never replaced by this transaction's P1. -/
structure Transaction where
  prior : Bytes
  frame : Bytes
  priorPolicy : Bytes
  nextPolicy : Bytes
  certificate : Bytes
  deriving DecidableEq, Repr

def transaction (prior originalFrame priorPolicy : Bytes) (whole : EcFinalization.Whole) : Transaction :=
  ⟨prior,originalFrame,priorPolicy,whole.source.candidate.update.raw,whole.source.candidate.certificate.raw⟩

def target (t : Transaction) : Bytes := t.prior ++ t.frame

inductive Phase where
  | prepared | appended | recoveryVerified | durable | committed | crashed | blocked
  deriving DecidableEq, Repr

structure Machine where
  nativeWal : Bytes
  volatile : Bytes
  stable : Bytes
  phase : Phase
  current : Bytes
  exposed : List Bytes
  deriving DecidableEq, Repr

def initial (t : Transaction) (nativeWal : Bytes) : Machine :=
  ⟨nativeWal,t.prior,t.prior,.prepared,t.priorPolicy,[]⟩

inductive Action where
  | append | barrier | commit | expose | recover
  | crash (surviving : Bytes)
  deriving DecidableEq, Repr

def step (t : Transaction) (s : Machine) : Action → Option Machine
  | .append => if s.phase = .prepared then
      some {s with volatile := s.volatile ++ t.frame, phase := .appended} else none
  | .barrier => if (s.phase = .appended ∨ s.phase = .recoveryVerified) ∧ s.volatile = target t then
      some {s with stable := s.volatile, phase := .durable} else none
  | .commit => if s.phase = .durable ∧ s.stable = s.volatile ∧ s.volatile = target t then
      some {s with current := t.nextPolicy, phase := .committed} else none
  | .expose => if s.phase = .committed ∧ s.stable = target t ∧ s.current = t.nextPolicy then
      some {s with exposed := s.exposed ++ [t.certificate]} else none
  | .crash surviving => if s.stable.IsPrefix surviving ∧ surviving.length ≤ s.volatile.length then
      some {s with volatile := surviving, stable := surviving, phase := .crashed} else none
  | .recover => if s.phase = .crashed then
      some {s with phase := if s.volatile = target t then .recoveryVerified
        else if s.volatile = t.prior then .prepared else .blocked} else none

/-- A run starts at the computed transaction, not at a caller-supplied phase.
Trace order is newest first. Each step is a successfully evaluated primitive. -/
inductive Run (t : Transaction) (nativeWal : Bytes) : List Action → Machine → Prop where
  | start : Run t nativeWal [] (initial t nativeWal)
  | next {trace before after action} : Run t nativeWal trace before →
      step t before action = some after → Run t nativeWal (action::trace) after

def barrierSinceCrash : List Action → Bool
  | [] => false
  | .barrier::_ => true
  | .crash _::_ => false
  | _::rest => barrierSinceCrash rest

def Armed (s : Machine) : Prop := s.phase = .durable ∨ s.phase = .committed

theorem stepWal {t s a out} (ok : step t s a = some out) : out.nativeWal = s.nativeWal := by
  cases a <;> simp only [step] at ok <;>
    split at ok <;> try contradiction
  all_goals cases Option.some.inj ok; rfl

theorem stepHistory {t s a out} (ok : step t s a = some out) : s.exposed.IsPrefix out.exposed := by
  cases a <;> simp only [step] at ok <;> split at ok <;> try contradiction
  all_goals cases Option.some.inj ok; simp

theorem stepEffects {t s a out} (ok : step t s a = some out)
    (old : ∀ x ∈ s.exposed, x = t.certificate) :
    ∀ x ∈ out.exposed, x = t.certificate := by
  cases a <;> simp only [step] at ok <;> split at ok <;> try contradiction
  all_goals
    cases Option.some.inj ok
    simp only [List.mem_append,List.mem_singleton]
    intro x hx
    first | exact old x hx | exact hx.elim (old x) id

theorem stepArmed {t s a out trace} (ok : step t s a = some out)
    (old : Armed s → barrierSinceCrash trace = true) :
    Armed out → barrierSinceCrash (a::trace) = true := by
  cases a <;> simp only [step] at ok <;> split at ok <;> try contradiction
  all_goals cases Option.some.inj ok; simp_all [Armed,barrierSinceCrash]
  split <;> try simp_all
  split <;> simp_all

theorem runInvariants {t nativeWal trace out} (run : Run t nativeWal trace out) :
    out.nativeWal = nativeWal ∧
    (∀ x ∈ out.exposed, x = t.certificate) ∧
    (Armed out → barrierSinceCrash trace = true) := by
  induction run with
  | start => simp [initial,Armed]
  | next before ok ih => exact ⟨(stepWal ok).trans ih.1,stepEffects ok ih.2.1,stepArmed ok ih.2.2⟩

theorem computedOriginalEffect {prior originalFrame priorPolicy whole nativeWal trace out}
    (run : Run (transaction prior originalFrame priorPolicy whole) nativeWal trace out) :
    out.nativeWal = nativeWal ∧
    ∀ x ∈ out.exposed, x = whole.source.candidate.certificate.raw :=
  ⟨(runInvariants run).1,(runInvariants run).2.1⟩

theorem exposeRequiresNewBarrier {t nativeWal trace before after}
    (run : Run t nativeWal trace before) (ok : step t before .expose = some after) :
    barrierSinceCrash trace = true ∧ before.stable = target t ∧ before.current = t.nextPolicy := by
  simp only [step] at ok
  split at ok <;> try contradiction
  rename_i h
  exact ⟨(runInvariants run).2.2 (Or.inr h.1),h.2⟩

theorem commitRequiresNewBarrier {t nativeWal trace before after}
    (run : Run t nativeWal trace before) (ok : step t before .commit = some after) :
    barrierSinceCrash trace = true ∧ before.stable = target t := by
  simp only [step] at ok
  split at ok <;> try contradiction
  rename_i h
  exact ⟨(runInvariants run).2.2 (Or.inl h.1),h.2.1.trans h.2.2⟩

theorem crashKeepsLogicalHistory {t s raw out} (ok : step t s (.crash raw) = some out) :
    out.exposed = s.exposed ∧ out.current = s.current ∧ out.volatile = raw ∧ out.stable = raw := by
  simp only [step] at ok
  split at ok <;> try contradiction
  cases Option.some.inj ok
  simp

theorem recoveryDoesNotExposeOrCommit {t s out} (ok : step t s .recover = some out) :
    out.exposed = s.exposed ∧ out.current = s.current ∧ out.volatile = s.volatile ∧
    out.stable = s.stable ∧ step t out .expose = none ∧ step t out .commit = none := by
  simp only [step] at ok
  split at ok <;> try contradiction
  cases Option.some.inj ok
  split <;> try simp_all [step]
  split <;> simp_all

theorem unknownRecoveryPreservesBytes {t s out} (ok : step t s .recover = some out)
    (notTarget : s.volatile ≠ target t) (notPrior : s.volatile ≠ t.prior) :
    out.phase = .blocked ∧ out.volatile = s.volatile ∧ out.stable = s.stable := by
  simp only [step] at ok
  split at ok <;> try contradiction
  cases Option.some.inj ok
  simp

theorem repeatedExposureIdentity {t s out} (ok : step t s .expose = some out) :
    out.nativeWal = s.nativeWal ∧ out.volatile = s.volatile ∧ out.stable = s.stable ∧
    out.current = s.current ∧ out.exposed = s.exposed ++ [t.certificate] := by
  simp only [step] at ok
  split at ok <;> try contradiction
  cases Option.some.inj ok
  simp

end DeltaReduce.ProfileSource.EcDurability
