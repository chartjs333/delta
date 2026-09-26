import DeltaReduce.NativeFailurePayload

/-! Complete timeout/view/abort snapshot tail, with all seven original finalized
lists and exact current abort lineage. Candidate/live enabling is separate. -/
namespace DeltaReduce.NativeFailureSection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeFailurePayload
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeConfigAdmission (getTexts)
open NativeParameterSection (trees)
structure Lineage where
  configs : List Bytes
  inputs : List Bytes
  eligibility : List Bytes
  plans : List Bytes
  parameters : List Bytes
  roots : List Bytes
  applies : List Bytes
  deriving DecidableEq, Repr

def readLineage (p : Policy) : Option Lineage := do
  let configs ← getTexts fmtSnapshot p.snapshot "finalized_round_config_ids"
  let inputs ← getTexts fmtSnapshot p.snapshot "finalized_input_set_ids"
  let eligibility ← getTexts fmtSnapshot p.snapshot "finalized_eligibility_ids"
  let plans ← getTexts fmtSnapshot p.snapshot "finalized_aggregation_plan_ids"
  let parameters ← getTexts fmtSnapshot p.snapshot "finalized_parameter_ids"
  let roots ← getTexts fmtSnapshot p.snapshot "finalized_aggregate_root_ids"
  let applies ← getTexts fmtSnapshot p.snapshot "finalized_apply_ids"
  some ⟨configs,inputs,eligibility,plans,parameters,roots,applies⟩

def LineageSource (p : Policy) (l : Lineage) : Prop :=
  getTexts fmtSnapshot p.snapshot "finalized_round_config_ids" = some l.configs ∧
  getTexts fmtSnapshot p.snapshot "finalized_input_set_ids" = some l.inputs ∧
  getTexts fmtSnapshot p.snapshot "finalized_eligibility_ids" = some l.eligibility ∧
  getTexts fmtSnapshot p.snapshot "finalized_aggregation_plan_ids" = some l.plans ∧
  getTexts fmtSnapshot p.snapshot "finalized_parameter_ids" = some l.parameters ∧
  getTexts fmtSnapshot p.snapshot "finalized_aggregate_root_ids" = some l.roots ∧
  getTexts fmtSnapshot p.snapshot "finalized_apply_ids" = some l.applies

theorem lineageSource {p l} (h : readLineage p = some l) : LineageSource p l := by
  unfold readLineage at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,i,hi,e,he,a,ha,s,hs,r,hr,f,hf,last⟩ := h
  cases Option.some.inj last
  exact ⟨hc,hi,he,ha,hs,hr,hf⟩
theorem lineageFromComponents {p l} (h : LineageSource p l) : readLineage p = some l := by
  rcases h with ⟨hc,hi,he,ha,hs,hr,hf⟩
  simp only [readLineage,hc,hi,he,ha,hs,hr,hf,bind,Option.bind]

def AbortExact (p : Policy) (s : State) (l : Lineage) (a : AbortBody) : Prop :=
  a.round = p.round ∧ a.epoch = p.epoch ∧ a.height = s.height ∧ a.view = s.view ∧
  a.deadline = p.hardDeadline ∧ a.parent = s.wire.parent ∧ a.reason = p.reason ∧
  a.configs = l.configs ∧ a.inputs = l.inputs ∧ a.eligibility = l.eligibility ∧
  a.plans = l.plans ∧ a.parameters = l.parameters ∧ a.roots = l.roots ∧ a.applies = l.applies
instance (p s l a) : Decidable (AbortExact p s l a) := by unfold AbortExact; infer_instance

structure Tail where
  lineage : Lineage
  timeoutTrees : List Value
  timeouts : List Timeout
  viewTrees : List Value
  views : List (Row ViewBody)
  requestTrees : List Value
  requests : List Request
  abortTrees : List Value
  aborts : List (Row AbortBody)

def TailChecks (p : Policy) (s : State) (t : Tail) : Prop :=
  t.timeouts.length ≤ 100000 ∧ t.views.length ≤ 100000 ∧
  t.requests.length ≤ 100000 ∧ t.aborts.length ≤ 100000 ∧
  (∀ x ∈ t.timeouts, TimeoutValid x) ∧ NativePolicyBytes.strictly timeoutLT t.timeouts = true ∧
  (∀ x ∈ t.requests, RequestValid x) ∧ NativePolicyBytes.strictly requestLT t.requests = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (t.views.map Row.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (t.aborts.map Row.id) = true ∧
  ∀ row ∈ t.aborts, AbortExact p s t.lineage row.body
instance (p s t) : Decidable (TailChecks p s t) := by unfold TailChecks; infer_instance

def checkTail (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Tail := do
  let l ← readLineage p
  let tt ← trees p "timeout_observations"
  let ts ← readAll readTimeout tt
  let vt ← trees p "view_change_bodies"
  let vs ← checkViews sha vt
  let rt ← trees p "abort_requests"
  let rs ← readAll readRequest rt
  let ats ← trees p "abort_bodies"
  let ars ← checkAborts sha ats
  let t := Tail.mk l tt ts vt vs rt rs ats ars
  if TailChecks p s t then some t else none
structure TailSource (sha : Bytes → Bytes) (p : Policy) (s : State) (t : Tail) : Prop where
  lineage : readLineage p = some t.lineage
  timeoutTrees : trees p "timeout_observations" = some t.timeoutTrees
  timeouts : readAll readTimeout t.timeoutTrees = some t.timeouts
  viewTrees : trees p "view_change_bodies" = some t.viewTrees
  views : checkViews sha t.viewTrees = some t.views
  requestTrees : trees p "abort_requests" = some t.requestTrees
  requests : readAll readRequest t.requestTrees = some t.requests
  abortTrees : trees p "abort_bodies" = some t.abortTrees
  aborts : checkAborts sha t.abortTrees = some t.aborts
  valid : TailChecks p s t

theorem checkedTail {sha p s t} (h : checkTail sha p s = some t) : TailSource sha p s t := by
  unfold checkTail at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨l,hl,tt,htt,ts,hts,vt,hvt,vs,hvs,rt,hrt,rs,hrs,ats,hat,ars,has,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨hl,htt,hts,hvt,hvs,hrt,hrs,hat,has,valid⟩

theorem tailFromComponents {sha p s t} (h : TailSource sha p s t) : checkTail sha p s = some t := by
  unfold checkTail
  rw [h.lineage,h.timeoutTrees]
  dsimp only [bind,Option.bind]
  rw [h.timeouts,h.viewTrees]
  dsimp only [bind,Option.bind]
  rw [h.views,h.requestTrees]
  dsimp only [bind,Option.bind]
  rw [h.requests,h.abortTrees]
  dsimp only [bind,Option.bind]
  rw [h.aborts]
  exact if_pos h.valid

theorem originalLists {sha p s t} (h : checkTail sha p s = some t) :
    t.timeoutTrees = t.timeouts.map timeoutValue ∧ t.views.map Row.source = t.viewTrees ∧
    t.requestTrees = t.requests.map requestValue ∧ t.aborts.map Row.source = t.abortTrees :=
  ⟨readAllOriginal timeoutOriginal (checkedTail h).timeouts,rowsOriginal (checkedTail h).views,
   readAllOriginal requestOriginal (checkedTail h).requests,rowsOriginal (checkedTail h).aborts⟩

theorem everyView {sha p s t row} (h : checkTail sha p s = some t) (mem : row ∈ t.views) :
    checkRow fmtViewChange readView (viewId sha) row.source = some row :=
  rowsChecked (checkedTail h).views row mem

theorem everyAbort {sha p s t row} (h : checkTail sha p s = some t) (mem : row ∈ t.aborts) :
    checkRow fmtAbortBody readAbort (abortId sha) row.source = some row ∧
    AbortExact p s t.lineage row.body :=
  ⟨rowsChecked (checkedTail h).aborts row mem,(checkedTail h).valid.2.2.2.2.2.2.2.2.2.2 row mem⟩

theorem completeAbortLists {sha p s t row} (h : checkTail sha p s = some t) (mem : row ∈ t.aborts) :
    LineageSource p ⟨row.body.configs,row.body.inputs,row.body.eligibility,row.body.plans,
      row.body.parameters,row.body.roots,row.body.applies⟩ := by
  have hs := lineageSource (checkedTail h).lineage
  have ha := (everyAbort h mem).2
  rcases ha with ⟨_,_,_,_,_,_,_,hc,hi,he,hp,hs',hr,hf⟩
  simpa only [LineageSource,hc,hi,he,hp,hs',hr,hf] using hs

structure Bound where
  prior : NativeApplySection.Bound
  tail : Tail

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let prior ← NativeApplySection.bindSection sha p s
  let tail ← checkTail sha p s
  some ⟨prior,tail⟩

theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) :
    NativeApplySection.bindSection sha p s = some b.prior ∧ checkTail sha p s = some b.tail := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨prior,hp,tail,ht,last⟩ := h
  cases Option.some.inj last
  exact ⟨hp,ht⟩
theorem fromComponents {sha p s b}
    (hp : NativeApplySection.bindSection sha p s = some b.prior) (ht : checkTail sha p s = some b.tail) :
    bindSection sha p s = some b := by simp only [bindSection,hp,ht,bind,Option.bind]

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindSection sha p s
theorem preparedSource {sha policyRaw stateRaw b} (h : prepare sha policyRaw stateRaw = some b) :
    ∃ tree p s, NativePolicyBytes.decodePolicy policyRaw = some (tree,p) ∧
    NativeStateBytes.decodeState stateRaw = some s ∧
    NativeApplySection.bindSection sha p s = some b.prior ∧ checkTail sha p s = some b.tail := by
  unfold prepare at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := h
  exact ⟨tree,p,s,hp,hs,checkedSource hb⟩
theorem abortMismatch {sha p s t row} (mem : row ∈ t.aborts)
    (bad : ¬ AbortExact p s t.lineage row.body) : checkTail sha p s ≠ some t := by
  intro h
  exact bad (everyAbort h mem).2

theorem checkedOrdering {sha p s t} (h : checkTail sha p s = some t) :
    NativePolicyBytes.strictly timeoutLT t.timeouts = true ∧
    NativePolicyBytes.strictly requestLT t.requests = true ∧
    NativePolicyBytes.strictly NativePolicyBytes.bytesLT (t.views.map Row.id) = true ∧
    NativePolicyBytes.strictly NativePolicyBytes.bytesLT (t.aborts.map Row.id) = true := by
  rcases (checkedTail h).valid with ⟨_,_,_,_,_,ht,_,hr,hv,ha,_⟩
  exact ⟨ht,hr,hv,ha⟩
end DeltaReduce.NativeFailureSection
