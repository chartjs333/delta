import DeltaReduce.NativeAggregateRoot

/-! Original ROOT lookup and exact ordered finalized PARAMETER coverage.
All hashes are computed; no caller-supplied Merkle or body approval callback. -/
namespace DeltaReduce.NativeAggregateLineage
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeAggregateRoot
open NativeInputSetBody (Context)
open NativeAggregateMerkle (Leaf)
open NativeParameter (Key)
open NativeParameterLineage (Mode)

def shardLeaf (e : NativeParameterLineage.Edge) : Leaf :=
  ⟨e.certificate.common.domain,e.id,e.certificate.common.shard⟩

def ShardChecks (expected : Context) (committee finalized : List Bytes) (c : Common)
    (l : Leaf) (e : NativeParameterLineage.Edge) : Prop :=
  e.id ∈ finalized ∧ shardLeaf e = l ∧ NativeParameter.Valid expected committee e.certificate ∧
  e.certificate.common.isc = c.isc ∧ e.certificate.common.ec = c.ec ∧ e.certificate.common.plan = c.plan
instance (expected committee finalized c l e) : Decidable (ShardChecks expected committee finalized c l e) := by
  unfold ShardChecks; infer_instance

def resolve (sha : Bytes → Bytes) (expected : Context) (committee finalized : List Bytes)
    (c : Common) (shards : List NativeParameterLineage.Edge) (l : Leaf) : Option NativeParameterLineage.Edge := do
  let e ← shards.find? (fun e => e.id == l.qc)
  if ShardChecks expected committee finalized c l e then
    let hash ← NativeContractSize.contentId sha NativeParameter.domain (NativeParameter.json e.certificate)
    if hash = l.qc then some e else none
  else none

theorem resolvedSource {sha expected committee finalized c shards l e}
    (h : resolve sha expected committee finalized c shards l = some e) :
    shards.find? (fun e => e.id == l.qc) = some e ∧
    ShardChecks expected committee finalized c l e ∧
    NativeContractSize.contentId sha NativeParameter.domain (NativeParameter.json e.certificate) = some l.qc := by
  unfold resolve at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨e,he,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨hash,hh,last⟩ := last
  split at last <;> try contradiction
  rename_i eq
  subst hash
  cases Option.some.inj last
  exact ⟨he,valid,hh⟩

theorem resolvedFromComponents {sha expected committee finalized c shards l e}
    (hf : shards.find? (fun e => e.id == l.qc) = some e)
    (hv : ShardChecks expected committee finalized c l e)
    (hh : NativeContractSize.contentId sha NativeParameter.domain (NativeParameter.json e.certificate) = some l.qc) :
    resolve sha expected committee finalized c shards l = some e := by
  simp only [resolve,hf,bind,Option.bind,if_pos hv,hh,ite_true]

def resolveAll (sha : Bytes → Bytes) (expected : Context) (committee finalized : List Bytes)
    (c : Common) (shards : List NativeParameterLineage.Edge) : List Leaf → Option (List NativeParameterLineage.Edge)
  | [] => some []
  | l::ls => do
    let e ← resolve sha expected committee finalized c shards l
    let rest ← resolveAll sha expected committee finalized c shards ls
    some (e::rest)

theorem resolvedLeaves {sha expected committee finalized c shards ls es}
    (h : resolveAll sha expected committee finalized c shards ls = some es) : es.map shardLeaf = ls := by
  induction ls generalizing es with
  | nil => simp [resolveAll] at h; subst es; rfl
  | cons l ls ih =>
    simp only [resolveAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(resolvedSource he).2.1.2.1,ih hr]

theorem resolvedEvery {sha expected committee finalized c shards ls es}
    (h : resolveAll sha expected committee finalized c shards ls = some es) (e) (mem : e ∈ es) :
    resolve sha expected committee finalized c shards (shardLeaf e) = some e := by
  induction ls generalizing es with
  | nil => simp [resolveAll] at h; subst es; simp at mem
  | cons l ls ih =>
    simp only [resolveAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(resolvedSource hx).2.1.2.1] using hx
    · exact ih hr mem

theorem resolvedCount {sha expected committee finalized c shards ls es}
    (h : resolveAll sha expected committee finalized c shards ls = some es) : es.length = ls.length := by
  have eq := congrArg List.length (resolvedLeaves h); simpa using eq

theorem resolvedPosition {sha expected committee finalized c shards ls es} {i : Nat} {e}
    (h : resolveAll sha expected committee finalized c shards ls = some es) (atIndex : es[i]? = some e) :
    ls[i]? = some (shardLeaf e) := by
  rw [← resolvedLeaves h,List.getElem?_map,atIndex]; rfl

def decode (mode : Mode) (committee : List Bytes) (source : Value) : Option Certificate :=
  match mode with
  | .proposed => do let b ← readBody source; some (proposedCertificate committee b)
  | .finalized => read source

def original (mode : Mode) (c : Certificate) : Value :=
  match mode with
  | .proposed => bodyValue c.common
  | .finalized => value c

theorem decodedOriginal {mode committee source c}
    (h : decode mode committee source = some c) : source = original mode c := by
  cases mode with
  | proposed =>
    simp only [decode,bind,Option.bind_eq_some_iff] at h
    obtain ⟨b,hb,last⟩ := h
    cases Option.some.inj last
    exact bodyOriginal hb
  | finalized => exact certOriginal h

def ParentChecks (fi fe fp : List Bytes) (keys : List Key) (c : Common)
    (parent : NativeIscCertificate.Checked) (ec : NativeEligibilityLineage.Edge)
    (plan : NativePlanLineage.Edge) : Prop :=
  parent.qcId ∈ fi ∧ ec.id ∈ fe ∧ plan.id ∈ fp ∧
  c.isc = parent.qcId ∧ c.ec = ec.id ∧ c.plan = plan.id ∧
  c.keys = keys ∧ c.leaves.map NativeAggregateMerkle.key = keys
instance (fi fe fp keys c parent ec plan) : Decidable (ParentChecks fi fe fp keys c parent ec plan) := by
  unfold ParentChecks; infer_instance

def resultId (sha : Bytes → Bytes) (mode : Mode) (c : Certificate) (qc : Bytes) : Option Bytes :=
  match mode with
  | .proposed => bodyId sha c.common
  | .finalized => some qc

structure Edge where
  certificate : Certificate
  source : Value
  id : Bytes
  qc : Bytes
  parent : NativeIscCertificate.Checked
  ec : NativeEligibilityLineage.Edge
  plan : NativePlanLineage.Edge
  shards : List NativeParameterLineage.Edge

def check (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (fi fe fp fs : List Bytes) (keys : List Key)
    (ecs : List NativeEligibilityLineage.Edge) (plans : List NativePlanLineage.Edge)
    (shards : List NativeParameterLineage.Edge) (source : Value) : Option Edge := do
  let c ← decode mode committee source
  let parent ← parents.find? (fun p => p.qcId == c.common.isc)
  let ec ← ecs.find? (fun e => e.id == c.common.ec)
  let plan ← plans.find? (fun p => p.id == c.common.plan)
  if Valid expected committee c ∧ ParentChecks fi fe fp keys c.common parent ec plan then
    let selected ← resolveAll sha expected committee fs c.common shards c.common.leaves
    let qc ← NativeAggregateRoot.id sha c
    let hash ← resultId sha mode c qc
    some ⟨c,source,hash,qc,parent,ec,plan,selected⟩
  else none

structure Source (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (fi fe fp fs : List Bytes) (keys : List Key)
    (ecs : List NativeEligibilityLineage.Edge) (plans : List NativePlanLineage.Edge)
    (shards : List NativeParameterLineage.Edge) (source : Value) (e : Edge) : Prop where
  originalSource : e.source = source
  decoded : decode mode committee source = some e.certificate
  parent : parents.find? (fun p => p.qcId == e.certificate.common.isc) = some e.parent
  ec : ecs.find? (fun p => p.id == e.certificate.common.ec) = some e.ec
  plan : plans.find? (fun p => p.id == e.certificate.common.plan) = some e.plan
  valid : Valid expected committee e.certificate
  parents : ParentChecks fi fe fp keys e.certificate.common e.parent e.ec e.plan
  selected : resolveAll sha expected committee fs e.certificate.common shards e.certificate.common.leaves = some e.shards
  qc : NativeAggregateRoot.id sha e.certificate = some e.qc
  identity : resultId sha mode e.certificate e.qc = some e.id

theorem checkedSource {sha mode expected committee parents fi fe fp fs keys ecs plans shards source e}
    (h : check sha mode expected committee parents fi fe fp fs keys ecs plans shards source = some e) :
    Source sha mode expected committee parents fi fe fp fs keys ecs plans shards source e := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hd,parent,hp,ec,he,plan,ha,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨selected,hs,qc,hq,hash,hh,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,hd,hp,he,ha,valid.1,valid.2,hs,hq,hh⟩

theorem fromComponents {sha mode expected committee parents fi fe fp fs keys ecs plans shards source e}
    (h : Source sha mode expected committee parents fi fe fp fs keys ecs plans shards source e) :
    check sha mode expected committee parents fi fe fp fs keys ecs plans shards source = some e := by
  unfold check
  rw [h.decoded]
  dsimp only [bind,Option.bind]
  rw [h.parent,h.ec,h.plan]
  dsimp only [bind,Option.bind]
  rw [if_pos ⟨h.valid,h.parents⟩,h.selected]
  dsimp only [bind,Option.bind]
  rw [h.qc]
  dsimp only [bind,Option.bind]
  rw [h.identity]
  rw [← h.originalSource]

theorem exactCoverage {sha mode expected committee parents fi fe fp fs keys ecs plans shards source e}
    (h : check sha mode expected committee parents fi fe fp fs keys ecs plans shards source = some e) :
    e.shards.map shardLeaf = e.certificate.common.leaves ∧
    e.certificate.common.keys = keys ∧
    e.certificate.common.leaves.map NativeAggregateMerkle.key = keys :=
  ⟨resolvedLeaves (checkedSource h).selected,(checkedSource h).parents.2.2.2.2.2.2⟩

theorem everyShard {sha mode expected committee parents fi fe fp fs keys ecs plans shards source e shard}
    (h : check sha mode expected committee parents fi fe fp fs keys ecs plans shards source = some e)
    (mem : shard ∈ e.shards) :
    shard ∈ shards ∧ ShardChecks expected committee fs e.certificate.common (shardLeaf shard) shard ∧
    NativeContractSize.contentId sha NativeParameter.domain (NativeParameter.json shard.certificate) = some shard.id := by
  have hs := resolvedSource (resolvedEvery (checkedSource h).selected shard mem)
  exact ⟨List.mem_of_find?_eq_some hs.1,hs.2⟩

def checkAll (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (fi fe fp fs : List Bytes) (keys : List Key)
    (ecs : List NativeEligibilityLineage.Edge) (plans : List NativePlanLineage.Edge)
    (shards : List NativeParameterLineage.Edge) : List Value → Option (List Edge)
  | [] => some []
  | v::vs => do
    let e ← check sha mode expected committee parents fi fe fp fs keys ecs plans shards v
    let rest ← checkAll sha mode expected committee parents fi fe fp fs keys ecs plans shards vs
    some (e::rest)

theorem allSources {sha mode expected committee parents fi fe fp fs keys ecs plans shards vs es}
    (h : checkAll sha mode expected committee parents fi fe fp fs keys ecs plans shards vs = some es) : es.map Edge.source = vs := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource he).originalSource,ih hr]

theorem allChecked {sha mode expected committee parents fi fe fp fs keys ecs plans shards vs es}
    (h : checkAll sha mode expected committee parents fi fe fp fs keys ecs plans shards vs = some es) (e : Edge) (mem : e ∈ es) :
    check sha mode expected committee parents fi fe fp fs keys ecs plans shards e.source = some e := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(checkedSource hx).originalSource] using hx
    · exact ih hr mem

end DeltaReduce.NativeAggregateLineage
