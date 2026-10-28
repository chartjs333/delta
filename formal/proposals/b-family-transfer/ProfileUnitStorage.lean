import ProfileUnitFinalization
import ProfileEcDurability

/-! T047/T053. Join the complete unit-bearing EC successor to the existing
original event, companion bytes and exact companion prefix. The companion
codec, original WAL identities and T barrier machine are reused unchanged.
The enclosing producing fold must derive the prior state, rows, clock and
decoded index. This component does not turn an index or byte hash into origin
authority, and does not infer physical durability from an imported flag. -/
namespace DeltaReduce.ProfileSource.UnitStorage
open NativeReceiptBytes (Bytes)
open Control (Node)

def checkStep (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (parent : ConfigurationUnits.Parent) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue : NativePolicyCodec.Value) (originals : Collections.Originals)
    (cut tick : Nat) (bodyId : Bytes) (rows : List ConfigurationQC.Received)
    (event : Index.Event) (origins : List Nat) (index : Index.Bound)
    (boot previous : Bytes) (ordinal : Nat) (cuts : List Node)
    (originalFrame : Bytes) : Option UnitFinalization.Ec := do
  let whole ← UnitFinalization.ec sha enrolled parent actor configRaw stateRaw policyRaw
    stateValue originals cut tick bodyId rows
  let checked ← EcFinalization.bindEvent event (UnitFinalization.ecFields whole)
    policyRaw stateRaw actor cut origins
  let pre ← EcDurability.atEvent index event
  let _ ← EcDurability.bindOriginal sha
    (EcDurability.material boot previous ordinal pre cuts event checked policyRaw stateRaw)
    originalFrame
  some whole

theorem checkedStep {sha enrolled parent actor configRaw stateRaw policyRaw stateValue
    originals cut tick bodyId rows event origins index boot previous ordinal cuts originalFrame whole}
    (ok : checkStep sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows event origins index boot previous ordinal cuts originalFrame = some whole) :
    UnitFinalization.ec sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows = some whole ∧
    EcFinalization.EventChecks event (UnitFinalization.ecFields whole).source
      policyRaw stateRaw actor cut origins ∧
    ∃ pre, EcDurability.atEvent index event = some pre ∧
      EcDurability.encode sha (EcDurability.material boot previous ordinal pre cuts event
        (UnitFinalization.ecFields whole) policyRaw stateRaw) = some originalFrame := by
  simp only [checkStep,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨w,hw,checked,hc,pre,hp,bytes,hb,last⟩ := ok
  obtain ⟨same,events⟩ := EcFinalization.originalEventChecked hc
  subst checked
  cases Option.some.inj last
  exact ⟨hw,events,pre,hp,(EcDurability.wholeOriginalBinding hb).2⟩

theorem originalFrameUnique {sha enrolled parent actor configRaw stateRaw policyRaw stateValue
    originals cut tick bodyId rows event origins index boot previous ordinal cuts left right a b}
    (ha : checkStep sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows event origins index boot previous ordinal cuts left = some a)
    (hb : checkStep sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows event origins index boot previous ordinal cuts right = some b) :
    a = b ∧ left = right := by
  obtain ⟨ea,_,pa,ipa,fa⟩ := checkedStep ha
  obtain ⟨eb,_,pb,ipb,fb⟩ := checkedStep hb
  have same : a = b := Option.some.inj (ea.symm.trans eb)
  subst b
  have samePrefix : pa = pb := Option.some.inj (ipa.symm.trans ipb)
  subst pb
  exact ⟨rfl,Option.some.inj (fa.symm.trans fb)⟩

theorem noPrefixErasure {sha enrolled parent actor configRaw stateRaw policyRaw stateValue
    originals cut tick bodyId rows event origins index boot previous ordinal cuts originalFrame whole}
    (ok : checkStep sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows event origins index boot previous ordinal cuts originalFrame = some whole) :
    ∃ pre, EcDurability.atEvent index event = some pre ∧
      (∀ n < event.position, pre[n]? = (index.eventDescriptors[n]?).map Control.encode) ∧
      EcDurability.encode sha (EcDurability.material boot previous ordinal pre cuts event
        (UnitFinalization.ecFields whole) policyRaw stateRaw) = some originalFrame := by
  obtain ⟨_,_,pre,hp,hm⟩ := checkedStep ok
  exact ⟨pre,hp,fun _ hn => EcDurability.prefixPosition hp hn,hm⟩

/-- Derive the companion ordinal/predecessor from all original prior records;
neither is chosen by the caller. Original event positions are not renumbered. -/
def checkStorage (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (parent : ConfigurationUnits.Parent) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue : NativePolicyCodec.Value) (originals : Collections.Originals)
    (cut tick : Nat) (bodyId : Bytes) (rows : List ConfigurationQC.Received)
    (event : Index.Event) (origins : List Nat) (index : Index.Bound) (boot : Bytes)
    (ms : List EcDurability.Material) (prior : Bytes) (cutNodes : List Node)
    (originalFrame : Bytes) : Option UnitFinalization.Ec := do
  let frames ← EcDurability.bindJournal sha boot actor ms prior
  let cuts ← Import.cuts sha cutNodes
  let previous ← EcDurability.lastIdentity sha ms
  if EcDurability.companionCut sha actor prior frames.length cuts = true ∧
      (∀ m ∈ ms, m.eventIndex < event.position) then
    checkStep sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals cut tick
      bodyId rows event origins index boot previous (ms.length+1) cutNodes originalFrame
  else none

theorem storageAndSourceJoined {sha enrolled parent actor configRaw stateRaw policyRaw stateValue
    originals cut tick bodyId rows event origins index boot ms prior cutNodes originalFrame whole}
    (ok : checkStorage sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows event origins index boot ms prior cutNodes originalFrame = some whole) :
    ∃ frames cuts previous,
      EcDurability.ChainSource sha boot actor (NativeVoteBytes.ascii "GENESIS") 1 0 ms frames ∧
      frames.flatten = prior ∧ ms.length = frames.length ∧
      Import.cuts sha cutNodes = some cuts ∧
      EcDurability.companionCut sha actor prior frames.length cuts = true ∧
      (∀ m ∈ ms, m.eventIndex < event.position) ∧
      EcDurability.lastIdentity sha ms = some previous ∧
      checkStep sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals cut tick
        bodyId rows event origins index boot previous (ms.length+1) cutNodes originalFrame = some whole := by
  simp only [checkStorage,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨frames,hf,cuts,hc,previous,hp,last⟩ := ok
  split at last <;> try contradiction
  rename_i guards
  obtain ⟨history,raws,length⟩ := EcDurability.wholeJournalChecked hf
  exact ⟨frames,cuts,previous,history,raws,length,hc,guards.1,guards.2,hp,last⟩

theorem completeUnitsRetained {sha enrolled parent actor configRaw stateRaw policyRaw stateValue
    originals cut tick bodyId rows event origins index boot ms prior cutNodes originalFrame whole}
    (ok : checkStorage sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows event origins index boot ms prior cutNodes originalFrame = some whole) :
    UnitState.bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
        = some whole.before ∧
    UnitState.bind sha enrolled parent actor configRaw stateRaw whole.candidate.update.raw
        stateValue whole.nextOriginals = some whole.following ∧
    ConfigurationUnits.ParentMatches parent whole.before.header.config ∧
    ConfigurationUnits.ParentMatches parent whole.following.header.config := by
  obtain ⟨_,_,_,_,_,_,_,_,_,_,step⟩ := storageAndSourceJoined ok
  have ec := (checkedStep step).1
  have source := UnitFinalization.ecSource ec
  exact ⟨source.before,source.following,UnitFinalization.ecParentUnits ec⟩

/-- Only exact original bytes and the already computed whole source candidate
feed the EXISTING T transaction. No new storage format or durability rule. -/
def transaction (prior originalFrame priorPolicy : Bytes) (whole : UnitFinalization.Ec) :
    EcDurability.Transaction :=
  EcDurability.transaction prior originalFrame priorPolicy (UnitFinalization.ecFields whole)

theorem transactionNoRelabel (prior originalFrame priorPolicy : Bytes)
    (whole : UnitFinalization.Ec) :
    (transaction prior originalFrame priorPolicy whole).prior = prior ∧
    (transaction prior originalFrame priorPolicy whole).frame = originalFrame ∧
    (transaction prior originalFrame priorPolicy whole).priorPolicy = priorPolicy ∧
    (transaction prior originalFrame priorPolicy whole).nextPolicy = whole.candidate.update.raw ∧
    (transaction prior originalFrame priorPolicy whole).certificate = whole.candidate.certificate.raw :=
  ⟨rfl,rfl,rfl,rfl,rfl⟩

theorem originalWalPreserved {prior originalFrame priorPolicy whole nativeWal trace out}
    (run : EcDurability.Run (transaction prior originalFrame priorPolicy whole) nativeWal trace out) :
    out.nativeWal = nativeWal := (EcDurability.runInvariants run).1

end DeltaReduce.ProfileSource.UnitStorage
