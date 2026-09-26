import DeltaReduce.NativeParameter

/-! Actual original PARAMETER parent lookup. Proposed assignment/domain guards
are intentionally not silently imposed on finalized certificates. -/
namespace DeltaReduce.NativeParameterLineage
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeParameter
open NativeInputSetBody (Context)
inductive Mode where | proposed | finalized deriving DecidableEq, Repr
def decode (mode : Mode) (committee : List Bytes) (source : Value) : Option (Certificate × Bytes) :=
  match mode with
  | .proposed => do let b ← readBody source; some (proposedCertificate committee b,b.voteContext)
  | .finalized => do let c ← read source; some (c,[])
def original (mode : Mode) (c : Certificate) (ctx : Bytes) : Value :=
  match mode with
  | .proposed => bodyValue ⟨c.common,ctx⟩
  | .finalized => value c
theorem decodedOriginal {mode committee source c ctx}
    (h : decode mode committee source = some (c,ctx)) : source = original mode c ctx := by
  cases mode with
  | proposed =>
    simp only [decode,bind,Option.bind_eq_some_iff] at h
    obtain ⟨b,hb,last⟩ := h
    cases Option.some.inj last
    exact bodyOriginal hb
  | finalized =>
    simp only [decode,bind,Option.bind_eq_some_iff] at h
    obtain ⟨b,hb,last⟩ := h
    cases Option.some.inj last
    exact readOriginal hb
def ProposedChecks (keys : List Key) (c : Common) (ctx : Bytes)
    (parent : NativeIscCertificate.Checked) (ec : NativeEligibilityLineage.Edge)
    (plan : NativePlanLineage.Edge) : Prop :=
  ctx ≠ [] ∧ plan.certificate.common.isc = parent.qcId ∧
  plan.certificate.common.ec = ec.id ∧ ⟨c.domain,c.shard⟩ ∈ keys ∧
  ∃ e ∈ ec.certificate.common.entries, e.accepted ≠ 0 ∧ e.domain = c.domain
instance (keys c ctx parent ec plan) : Decidable (ProposedChecks keys c ctx parent ec plan) := by
  unfold ProposedChecks; infer_instance
def NativeParentChecks (mode : Mode) (finalizedIsc finalizedEc finalizedPlan : List Bytes)
    (keys : List Key) (c : Certificate) (ctx : Bytes) (parent : NativeIscCertificate.Checked)
    (ec : NativeEligibilityLineage.Edge) (plan : NativePlanLineage.Edge) : Prop :=
  parent.qcId ∈ finalizedIsc ∧ ec.id ∈ finalizedEc ∧ plan.id ∈ finalizedPlan ∧
  c.common.isc = parent.qcId ∧ c.common.ec = ec.id ∧ c.common.plan = plan.id ∧
  (mode = .proposed → ProposedChecks keys c.common ctx parent ec plan)
instance (mode finalizedIsc finalizedEc finalizedPlan keys c ctx parent ec plan) :
    Decidable (NativeParentChecks mode finalizedIsc finalizedEc finalizedPlan keys c ctx parent ec plan) := by
  unfold NativeParentChecks; infer_instance
def resultId (sha : Bytes → Bytes) (mode : Mode) (c : Certificate) (ctx : Bytes) : Option Bytes :=
  match mode with
  | .proposed => bodyId sha ⟨c.common,ctx⟩
  | .finalized => id sha c
structure Edge where
  certificate : Certificate
  voteContext : Bytes
  source : Value
  id : Bytes
  parent : NativeIscCertificate.Checked
  ec : NativeEligibilityLineage.Edge
  plan : NativePlanLineage.Edge
def asBody (e : Edge) : Body := ⟨e.certificate.common,e.voteContext⟩

def check (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalizedIsc finalizedEc finalizedPlan : List Bytes)
    (keys : List Key) (ecs : List NativeEligibilityLineage.Edge) (plans : List NativePlanLineage.Edge) (source : Value) : Option Edge := do
  let (c,ctx) ← decode mode committee source
  let parent ← parents.find? (fun p => p.qcId == c.common.isc)
  let ec ← ecs.find? (fun n => n.id == c.common.ec)
  let plan ← plans.find? (fun p => p.id == c.common.plan)
  if Valid expected committee c ∧ NativeParentChecks mode finalizedIsc finalizedEc finalizedPlan keys c ctx parent ec plan then
    let hash ← resultId sha mode c ctx
    some ⟨c,ctx,source,hash,parent,ec,plan⟩
  else none
structure Source (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalizedIsc finalizedEc finalizedPlan : List Bytes)
    (keys : List Key) (ecs : List NativeEligibilityLineage.Edge) (plans : List NativePlanLineage.Edge) (source : Value) (e : Edge) : Prop where
  originalSource : e.source = source
  decoded : decode mode committee source = some (e.certificate,e.voteContext)
  parent : parents.find? (fun p => p.qcId == e.certificate.common.isc) = some e.parent
  ec : ecs.find? (fun p => p.id == e.certificate.common.ec) = some e.ec
  plan : plans.find? (fun p => p.id == e.certificate.common.plan) = some e.plan
  valid : Valid expected committee e.certificate
  parents : NativeParentChecks mode finalizedIsc finalizedEc finalizedPlan keys e.certificate e.voteContext e.parent e.ec e.plan
  identity : resultId sha mode e.certificate e.voteContext = some e.id
theorem checkedSource {sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source e}
    (h : check sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source = some e) : Source sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source e := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨c,ctx⟩,hd,parent,hp,ec,he,plan,ha,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨hash,hh,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,hd,hp,he,ha,valid.1,valid.2,hh⟩
theorem fromComponents {sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source e}
    (h : Source sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source e) : check sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source = some e := by
  unfold check
  rw [h.decoded]
  dsimp only [bind,Option.bind]
  rw [h.parent,h.ec,h.plan]
  dsimp only [bind,Option.bind]
  rw [if_pos ⟨h.valid,h.parents⟩,h.identity]
  rw [← h.originalSource]
theorem originalRetained {sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source e}
    (h : check sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source = some e) :
    source = original mode e.certificate e.voteContext := decodedOriginal (checkedSource h).decoded
theorem parentWitnesses {sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source e}
    (h : check sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source = some e) :
    e.parent ∈ parents ∧ e.parent.qcId = e.certificate.common.isc ∧
    e.ec ∈ ecs ∧ e.ec.id = e.certificate.common.ec ∧
    e.plan ∈ plans ∧ e.plan.id = e.certificate.common.plan := by
  have src := checkedSource h
  exact ⟨List.mem_of_find?_eq_some src.parent,by simpa using List.find?_some src.parent,
    List.mem_of_find?_eq_some src.ec,by simpa using List.find?_some src.ec,
    List.mem_of_find?_eq_some src.plan,by simpa using List.find?_some src.plan⟩
theorem proposalAssignment {sha expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source e}
    (h : check sha .proposed expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source = some e) :
    ProposedChecks keys e.certificate.common e.voteContext e.parent e.ec e.plan :=
  (checkedSource h).parents.2.2.2.2.2.2 rfl
def checkAll (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalizedIsc finalizedEc finalizedPlan : List Bytes)
    (keys : List Key) (ecs : List NativeEligibilityLineage.Edge) (plans : List NativePlanLineage.Edge) : List Value → Option (List Edge)
  | [] => some []
  | v::vs => do
    let e ← check sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans v
    let rest ← checkAll sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans vs
    some (e::rest)
theorem allSources {sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans vs es}
    (h : checkAll sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans vs = some es) : es.map Edge.source = vs := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource he).originalSource,ih hr]
theorem allChecked {sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans vs es}
    (h : checkAll sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans vs = some es) (e : Edge) (mem : e ∈ es) :
    check sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans e.source = some e := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(checkedSource hx).originalSource] using hx
    · exact ih hr mem
def format (mode : Mode) : Format := match mode with
  | .proposed => fmtParameterBody
  | .finalized => fmtParameter
def fromBytes (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalizedIsc finalizedEc finalizedPlan : List Bytes)
    (keys : List Key) (ecs : List NativeEligibilityLineage.Edge) (plans : List NativePlanLineage.Edge) (raw : Bytes) : Option Edge := do
  if raw.length ≤ 4*1024*1024 then
    let source ← NativePolicyCodec.decode (format mode) raw
    check sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans source
  else none
theorem bytesSource {sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans raw e}
    (h : fromBytes sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans raw = some e) :
    raw.length ≤ 4*1024*1024 ∧ encode (format mode) e.source = some raw ∧
    Source sha mode expected committee parents finalizedIsc finalizedEc finalizedPlan keys ecs plans e.source e := by
  unfold fromBytes at h; split at h <;> try contradiction
  rename_i size
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨source,parsed,checked⟩ := h
  have src := checkedSource checked
  exact ⟨size,src.originalSource ▸ (NativePolicyCodec.decoded parsed).2,by simpa only [src.originalSource] using src⟩
end DeltaReduce.NativeParameterLineage
