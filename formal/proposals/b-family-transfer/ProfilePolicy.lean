import ProfileNativeHeader

/-! T047/T053. Decode the entire successor policy into the existing native
typed carrier, retaining the changed ISC subtrees verbatim. Extraction of
unchanged outer fields is distinct from encoding them with a legacy codec.
No legacy payload is accepted, rewritten, or used as an origin witness. -/
namespace DeltaReduce.ProfileSource.Policy
open NativeReceiptBytes
open NativePolicyCodec (Format Value)
open NativePolicyBytes (Policy)

def byNames : List String → Value → String → Option Value
  | name::tail,.pair x y,key => if key = name then some x else byNames tail y key
  | _,_,_ => none

theorem lookupByNames (fmt : Format) (value : Value) (key : String) :
    NativePolicyCodec.lookup fmt value key = byNames (ISCSourceV2.fields fmt) value key := by
  induction fmt generalizing value with
  | field name head tail ihHead ihTail =>
    cases value <;> simp only [NativePolicyCodec.lookup,ISCSourceV2.fields,byNames]
    rename_i x y
    split <;> simp_all
  | _ => cases value <;> rfl

theorem sameOuterFields (value : Value) (key : String) :
    NativePolicyCodec.lookup NativeHeader.policyFormat value key =
      NativePolicyCodec.lookup NativePolicySchema.fmtPolicy value key := by
  rw [lookupByNames,lookupByNames]
  exact congrArg (fun names => byNames names value key) ISCSourceV2.completePolicyInventory

theorem sameSnapshotFields (value : Value) (key : String) :
    NativePolicyCodec.lookup NativeHeader.snapshotFormat value key =
      NativePolicyCodec.lookup NativePolicySchema.fmtSnapshot value key := by
  rw [lookupByNames,lookupByNames]
  exact congrArg (fun names => byNames names value key) ISCSourceV2.completeSnapshotInventory.1

def decode (raw : Bytes) : Option (Value × Policy) := do
  if raw.length ≤ 4194304 then
    let payload ← consume ISCSourceV2.header raw
    let value ← NativePolicyCodec.decode NativeHeader.policyFormat payload
    let p ← NativePolicyBytes.extract value
    if NativePolicyBytes.Canonical p then some (value,p) else none
  else none

theorem extractionOriginal {value p} (ok : NativePolicyBytes.extract value = some p) :
    p.source = value := by
  unfold NativePolicyBytes.extract at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  repeat (obtain ⟨_,_,ok⟩ := ok)
  rfl

structure Source (raw : Bytes) (value : Value) (p : Policy) : Prop where
  bound : raw.length ≤ 4194304
  bytes : NativeHeader.policyBytes value = some raw
  extraction : NativePolicyBytes.extract value = some p
  canonical : NativePolicyBytes.Canonical p

theorem consumed {magic raw payload : Bytes} (ok : consume magic raw = some payload) :
    magic ++ payload = raw := by
  unfold consume at ok
  split at ok <;> try contradiction
  rename_i hpref
  cases Option.some.inj ok
  calc
    magic ++ raw.drop magic.length = raw.take magic.length ++ raw.drop magic.length :=
      congrArg (fun xs => xs ++ raw.drop magic.length) hpref.1.symm
    _ = raw := List.take_append_drop magic.length raw

theorem sound {raw value p} (ok : decode raw = some (value,p)) : Source raw value p := by
  unfold decode at ok
  split at ok <;> try contradiction
  rename_i bounded
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨payload,hp,v,hv,policy,he,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i canonical
  cases Option.some.inj ok
  have encoded := (NativePolicyCodec.decoded hv).2
  have original := consumed hp
  refine ⟨bounded,?_,he,canonical⟩
  simp only [NativeHeader.policyBytes,encoded,bind,Option.bind]
  rw [original]
  exact if_pos bounded

theorem complete {raw value p} (source : Source raw value p) :
    decode raw = some (value,p) := by
  have encoded := source.bytes
  unfold NativeHeader.policyBytes at encoded
  cases hb : NativePolicyCodec.encode NativeHeader.policyFormat value with
  | none => simp [hb] at encoded
  | some payload =>
    simp only [hb,bind,Option.bind] at encoded
    split at encoded <;> try contradiction
    cases Option.some.inj encoded
    simp only [decode,if_pos source.bound,consumeAppend,NativePolicyCodec.encoded hb,
      bind,Option.bind,source.extraction,if_pos source.canonical]

theorem completeSourcePreserved {raw value p} (ok : decode raw = some (value,p)) :
    NativeHeader.policyBytes p.source = some raw ∧
    NativePolicyBytes.Canonical p ∧
    ∀ name, NativePolicyCodec.lookup NativeHeader.policyFormat p.source name =
      NativePolicyCodec.lookup NativePolicySchema.fmtPolicy value name := by
  have src := sound ok
  have original := extractionOriginal src.extraction
  exact ⟨by simpa only [original] using src.bytes,src.canonical,
    fun name => by simpa only [original] using sameOuterFields value name⟩

theorem snapshotRetained {raw value p} (ok : decode raw = some (value,p)) :
    NativePolicyCodec.lookup NativeHeader.policyFormat value "snapshot" = some p.snapshot := by
  have source := (sound ok).extraction
  rw [sameOuterFields]
  unfold NativePolicyBytes.extract at source
  simp only [NativePolicyBytes.field,bind,Option.bind_eq_some_iff] at source
  obtain ⟨localId,hl,epoch,he,ids,hi,validators,hv,role,hr,round,hd,config,hc,
    reason,hn,initial,ht,soft,hs,hard,hh,snapshot,hp,cs,hcs,candidates,hca,last⟩ := source
  cases Option.some.inj last
  exact hp

theorem everySnapshotFieldRetained {raw value p} (ok : decode raw = some (value,p)) (key : String) :
    ∃ original, NativePolicyCodec.lookup NativeHeader.policyFormat value "snapshot" = some original ∧
      NativePolicyCodec.lookup NativeHeader.snapshotFormat p.snapshot key =
        NativePolicyCodec.lookup NativeHeader.snapshotFormat original key :=
  ⟨p.snapshot,snapshotRetained ok,rfl⟩

/-- An original policy may be absent before installation. This decoder handles
only an actually present original DVPOL002 artifact; its candidate requirement
is the existing install-policy requirement, not an initial-state restriction. -/
structure Bound where
  header : NativeHeader.Bound
  policy : Policy

def bind (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value) : Option Bound := do
  let (value,p) ← decode policyRaw
  let h ← NativeHeader.check sha enrolled actor configRaw stateRaw policyRaw stateValue value
  some ⟨h,p⟩

theorem boundSource {sha enrolled actor configRaw stateRaw policyRaw stateValue out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue = some out) :
    ∃ value, decode policyRaw = some (value,out.policy) ∧
      NativeHeader.check sha enrolled actor configRaw stateRaw policyRaw stateValue value =
        some out.header := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨value,p⟩,hp,h,hh,last⟩ := ok
  cases Option.some.inj last
  exact ⟨value,hp,hh⟩

theorem boundComplete {sha enrolled actor configRaw stateRaw policyRaw stateValue value p h}
    (policy : decode policyRaw = some (value,p))
    (header : NativeHeader.check sha enrolled actor configRaw stateRaw policyRaw stateValue value = some h) :
    bind sha enrolled actor configRaw stateRaw policyRaw stateValue = some ⟨h,p⟩ := by
  simp only [bind,policy,header,Bind.bind,Option.bind]

theorem boundOriginals {sha enrolled actor configRaw stateRaw policyRaw stateValue out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue = some out) :
    NativeHeader.policyBytes out.policy.source = some policyRaw ∧
    out.header.policy = out.policy.source ∧
    NativeHeader.stateBytes stateValue = some stateRaw ∧
    Configuration.checkEnrolled enrolled configRaw = some out.header.config ∧
    NativeHeader.Matches sha configRaw stateRaw actor out.header.config
      out.header.state out.policy.source := by
  obtain ⟨value,hp,hh⟩ := boundSource ok
  have p := completeSourcePreserved hp
  have h := NativeHeader.checked hh
  have src := extractionOriginal (sound hp).extraction
  exact ⟨p.1,h.2.2.2.2.1.trans src.symm,h.2.1,h.1,
    by simpa only [h.2.2.2.2.1,← src] using h.2.2.2.2.2⟩

end DeltaReduce.ProfileSource.Policy
