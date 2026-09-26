import DeltaReduce.NativeFailureSection

/-! Actual native VIEW/ABORT candidate fields and body/timeout authority.
This is a selected-candidate subrelation, not complete shared policy admission. -/
namespace DeltaReduce.NativeFailureAuthority
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeFailurePayload
open NativePolicyBytes (Policy Candidate)
open NativeStateBytes (State)
open NativeVoteBytes (ContentId ascii)
open NativeFailureSection (Tail)

structure Parents where
  config : Bytes
  checkpoint : Bytes
  reason : Bytes
  deriving DecidableEq, Repr

def parentsValue (p : Parents) : Value := .pair (.text p.config) (.pair (.text p.checkpoint) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text p.reason) .end))))))))))))))
def readParents : Value → Option Parents
  | .pair (.text config) (.pair (.text checkpoint) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text []) (.pair (.text reason) .end)))))))))))))) => some ⟨config,checkpoint,reason⟩
  | _ => none

theorem parentsRead (p) : readParents (parentsValue p) = some p := by cases p; rfl
theorem parentsOriginal {v p} (h : readParents v = some p) : v = parentsValue p := by
  unfold readParents at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl

def viewContext (sha : Bytes → Bytes) (round : Bytes) (view : Nat) : Option Bytes :=
  if WireId round ∧ view < 256^8 then
    NativeStateBytes.contentId sha (ascii "deltareduce.vote-context.view.v1")
      (NativeInputSetBody.text64 round ++ be 8 view)
  else none
def abortContext (sha : Bytes → Bytes) (round : Bytes) : Option Bytes :=
  if WireId round then
    NativeStateBytes.contentId sha (ascii "deltareduce.vote-context.abort.v1")
      (NativeInputSetBody.text64 round)
  else none

theorem viewContextBounds {sha round view id} (h : viewContext sha round view = some id) :
    WireId round ∧ view < 256^8 := by
  unfold viewContext at h; split at h
  · assumption
  · contradiction
theorem abortContextBounds {sha round id} (h : abortContext sha round = some id) :
    WireId round := by
  unfold abortContext at h; split at h
  · assumption
  · contradiction

def Common (p : Policy) (s : State) (c : Candidate) (parent : Parents) (ctx : Bytes) : Prop :=
  ContentId c.body ∧ WireId c.context ∧ ContentId parent.config ∧
  ContentId parent.checkpoint ∧ parent.config = p.config ∧ c.context = ctx ∧
  c.height = s.height ∧ c.view = s.view ∧ c.height < 256^8 ∧ c.view < 256^8
instance (p s c parent ctx) : Decidable (Common p s c parent ctx) := by unfold Common; infer_instance

def ViewChecks (p : Policy) (s : State) (v : ViewBody) (o : Timeout) : Prop :=
  v.round = p.round ∧ v.height = s.height ∧ v.fromView = s.view ∧
  s.view < 256^8-1 ∧ v.toView = s.view+1 ∧ v.deadline = p.softDeadline ∧
  o.round = v.round ∧ o.height = v.height ∧ o.view = v.fromView
instance (p s v o) : Decidable (ViewChecks p s v o) := by unfold ViewChecks; infer_instance

def matchingTimeout (v : ViewBody) (o : Timeout) : Bool :=
  o.round == v.round && o.height == v.height && o.view == v.fromView

structure ViewEntry where
  parents : Parents
  context : Bytes
  row : Row ViewBody
  observation : Timeout

def checkView (sha : Bytes → Bytes) (p : Policy) (s : State) (t : Tail) (c : Candidate) :
    Option ViewEntry := do
  let parent ← readParents c.parents
  let ctx ← viewContext sha p.round s.view
  let row ← t.views.find? (fun r => r.id == c.body)
  let observation ← t.timeouts.find? (matchingTimeout row.body)
  let e := ViewEntry.mk parent ctx row observation
  if c.action = 8 ∧ parent.reason = [] ∧ Common p s c parent ctx ∧
      ViewChecks p s row.body observation then some e else none

structure ViewSource (sha : Bytes → Bytes) (p : Policy) (s : State) (t : Tail)
    (c : Candidate) (e : ViewEntry) : Prop where
  parents : readParents c.parents = some e.parents
  context : viewContext sha p.round s.view = some e.context
  row : t.views.find? (fun r => r.id == c.body) = some e.row
  observation : t.timeouts.find? (matchingTimeout e.row.body) = some e.observation
  action : c.action = 8
  reason : e.parents.reason = []
  common : Common p s c e.parents e.context
  checked : ViewChecks p s e.row.body e.observation

theorem viewSource {sha p s t c e} (h : checkView sha p s t c = some e) :
    ViewSource sha p s t c e := by
  unfold checkView at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨parent,hp,ctx,hc,row,hr,obs,ho,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨hp,hc,hr,ho,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2⟩

theorem viewFromComponents {sha p s t c e} (h : ViewSource sha p s t c e) :
    checkView sha p s t c = some e := by
  unfold checkView
  rw [h.parents,h.context]
  dsimp only [bind,Option.bind]
  rw [h.row]
  dsimp only [bind,Option.bind]
  rw [h.observation]
  exact if_pos ⟨h.action,h.reason,h.common,h.checked⟩

theorem viewMembership {sha p s t c e} (h : checkView sha p s t c = some e) :
    e.row ∈ t.views ∧ e.row.id = c.body ∧ e.observation ∈ t.timeouts := by
  have hs := viewSource h
  exact ⟨List.mem_of_find?_eq_some hs.row,by simpa using List.find?_some hs.row,
    List.mem_of_find?_eq_some hs.observation⟩

theorem exactTimeout {sha p s t c e} (h : checkView sha p s t c = some e) :
    e.observation.round = e.row.body.round ∧ e.observation.height = s.height ∧
    e.observation.view = s.view ∧ e.row.body.toView = s.view+1 ∧ s.view < 256^8-1 := by
  rcases (viewSource h).checked with ⟨_,hh,hv,hn,ht,_,ho,he,hf⟩
  exact ⟨ho,he.trans hh,hf.trans hv,ht,hn⟩

def AbortChecks (p : Policy) (s : State) (t : Tail) (parent : Parents) (a : AbortBody) : Prop :=
  a.reason = parent.reason ∧ a.parent = s.wire.parent ∧ t.lineage.applies = [] ∧
  NativeFailureSection.AbortExact p s t.lineage a
instance (p s t parent a) : Decidable (AbortChecks p s t parent a) := by unfold AbortChecks; infer_instance

structure AbortEntry where
  parents : Parents
  context : Bytes
  row : Row AbortBody

def checkAbort (sha : Bytes → Bytes) (p : Policy) (s : State) (t : Tail) (c : Candidate) :
    Option AbortEntry := do
  let parent ← readParents c.parents
  let ctx ← abortContext sha p.round
  let row ← t.aborts.find? (fun r => r.id == c.body)
  let e := AbortEntry.mk parent ctx row
  if c.action = 9 ∧ WireId parent.reason ∧ Common p s c parent ctx ∧
      AbortChecks p s t parent row.body then some e else none

structure AbortSource (sha : Bytes → Bytes) (p : Policy) (s : State) (t : Tail)
    (c : Candidate) (e : AbortEntry) : Prop where
  parents : readParents c.parents = some e.parents
  context : abortContext sha p.round = some e.context
  row : t.aborts.find? (fun r => r.id == c.body) = some e.row
  action : c.action = 9
  reason : WireId e.parents.reason
  common : Common p s c e.parents e.context
  checked : AbortChecks p s t e.parents e.row.body

theorem abortSource {sha p s t c e} (h : checkAbort sha p s t c = some e) :
    AbortSource sha p s t c e := by
  unfold checkAbort at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨parent,hp,ctx,hc,row,hr,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨hp,hc,hr,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2⟩

theorem abortFromComponents {sha p s t c e} (h : AbortSource sha p s t c e) :
    checkAbort sha p s t c = some e := by
  unfold checkAbort
  rw [h.parents,h.context]
  dsimp only [bind,Option.bind]
  rw [h.row]
  exact if_pos ⟨h.action,h.reason,h.common,h.checked⟩

theorem abortMembership {sha p s t c e} (h : checkAbort sha p s t c = some e) :
    e.row ∈ t.aborts ∧ e.row.id = c.body := by
  have hs := abortSource h
  exact ⟨List.mem_of_find?_eq_some hs.row,by simpa using List.find?_some hs.row⟩

theorem noFinalizedApply {sha p s t c e} (h : checkAbort sha p s t c = some e) :
    t.lineage.applies = [] := (abortSource h).checked.2.2.1

theorem viewOriginalRow {sha p s t c e}
    (tail : NativeFailureSection.checkTail sha p s = some t)
    (h : checkView sha p s t c = some e) :
    checkRow fmtViewChange readView (viewId sha) e.row.source = some e.row :=
  NativeFailureSection.everyView tail (viewMembership h).1

theorem abortOriginalRow {sha p s t c e}
    (tail : NativeFailureSection.checkTail sha p s = some t)
    (h : checkAbort sha p s t c = some e) :
    checkRow fmtAbortBody readAbort (abortId sha) e.row.source = some e.row ∧
    NativeFailureSection.AbortExact p s t.lineage e.row.body :=
  NativeFailureSection.everyAbort tail (abortMembership h).1

inductive Entry where
  | view (checked : ViewEntry)
  | abort (checked : AbortEntry)

def checkpoint : Entry → Bytes
  | .view e => e.parents.checkpoint
  | .abort e => e.parents.checkpoint

def checkCandidate (sha : Bytes → Bytes) (p : Policy) (s : State) (t : Tail) (c : Candidate) :
    Option Entry :=
  if c.action = 8 then Entry.view <$> checkView sha p s t c
  else if c.action = 9 then Entry.abort <$> checkAbort sha p s t c else none

def EntrySource (sha : Bytes → Bytes) (p : Policy) (s : State) (t : Tail) (c : Candidate) : Entry → Prop
  | .view e => checkView sha p s t c = some e
  | .abort e => checkAbort sha p s t c = some e

theorem candidateSource {sha p s t c e} (h : checkCandidate sha p s t c = some e) :
    EntrySource sha p s t c e := by
  unfold checkCandidate at h
  split at h
  · cases hv : checkView sha p s t c with
    | none => simp [hv] at h
    | some v => simp only [hv,Functor.map,Option.map] at h; cases Option.some.inj h; exact hv
  · split at h
    · cases ha : checkAbort sha p s t c with
      | none => simp [ha] at h
      | some a => simp only [ha,Functor.map,Option.map] at h; cases Option.some.inj h; exact ha
    · contradiction

theorem onlyFailure {sha p s t c e} (h : checkCandidate sha p s t c = some e) :
    c.action = 8 ∨ c.action = 9 := by
  cases e with
  | view v => exact Or.inl (viewSource (candidateSource h)).action
  | abort a => exact Or.inr (abortSource (candidateSource h)).action

structure Bound where
  prior : NativeFailureSection.Bound
  entry : Entry

def bindCandidate (sha : Bytes → Bytes) (p : Policy) (s : State) (c : Candidate) : Option Bound := do
  let prior ← NativeFailureSection.bindSection sha p s
  let entry ← checkCandidate sha p s prior.tail c
  some ⟨prior,entry⟩

theorem boundSource {sha p s c b} (h : bindCandidate sha p s c = some b) :
    NativeFailureSection.bindSection sha p s = some b.prior ∧
    checkCandidate sha p s b.prior.tail c = some b.entry := by
  unfold bindCandidate at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨prior,hs,entry,he,last⟩ := h
  cases Option.some.inj last
  exact ⟨hs,he⟩

theorem boundFromComponents {sha p s c b}
    (hs : NativeFailureSection.bindSection sha p s = some b.prior)
    (he : checkCandidate sha p s b.prior.tail c = some b.entry) :
    bindCandidate sha p s c = some b := by simp only [bindCandidate,hs,he,bind,Option.bind]
end DeltaReduce.NativeFailureAuthority
