import ProfilePolicy
import ProfileCandidates

/-! T047/T053. One installed source state: the independently selected original
configuration, full S0/P0 bytes, all collections and all candidates share the
same decoded context. This composes existing checks, without taking a successful
public projection as a premise. It is not initial/producer authority; absence
of an installed policy is handled by the enclosing history, not by an invented
empty policy or by erasing candidate/certificate collections. -/
namespace DeltaReduce.ProfileSource.InstalledState
open NativeReceiptBytes (Bytes)
open NativePolicyCodec (Value)

structure Bound where
  installed : Policy.Bound
  collections : Collections.Bound
  candidates : List Candidates.Entry

def bind (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) : Option Bound := do
  let installed ← Policy.bind sha enrolled actor configRaw stateRaw policyRaw stateValue
  let collections ← Collections.bind sha installed.header.state installed.policy originals
  let candidates ← Candidates.checkAll sha installed.policy installed.header.state collections
    installed.policy.candidates
  some ⟨installed,collections,candidates⟩

structure Source (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) (out : Bound) : Prop where
  installed : Policy.bind sha enrolled actor configRaw stateRaw policyRaw stateValue = some out.installed
  collections : Collections.bind sha out.installed.header.state out.installed.policy originals = some out.collections
  candidates : Candidates.checkAll sha out.installed.policy out.installed.header.state out.collections
    out.installed.policy.candidates = some out.candidates

theorem boundSource {sha enrolled actor configRaw stateRaw policyRaw stateValue originals out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out) :
    Source sha enrolled actor configRaw stateRaw policyRaw stateValue originals out := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨installed,hi,collections,hc,candidates,hcs,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hi,hc,hcs⟩

theorem complete {sha enrolled actor configRaw stateRaw policyRaw stateValue originals out}
    (h : Source sha enrolled actor configRaw stateRaw policyRaw stateValue originals out) :
    bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out := by
  simp only [bind,h.installed,h.collections,h.candidates,Bind.bind,Option.bind]

theorem allOriginalBytes {sha enrolled actor configRaw stateRaw policyRaw stateValue originals out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out) :
    NativeHeader.policyBytes out.installed.policy.source = some policyRaw ∧
    NativeHeader.stateBytes stateValue = some stateRaw ∧
    Configuration.encodeFrame out.installed.header.config.originalValue = some configRaw ∧
    out.candidates.map Candidates.Entry.original = out.installed.policy.candidates := by
  have h := boundSource ok
  have p := Policy.boundOriginals h.installed
  have c := Configuration.wholeSource (Configuration.enrolledSource p.2.2.2.1).1
  exact ⟨p.1,p.2.2.1,c.2.1,Candidates.originals h.candidates⟩

theorem originalSnapshotFields {sha enrolled actor configRaw stateRaw policyRaw stateValue originals out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out) :
    ∃ value, Policy.decode policyRaw = some (value,out.installed.policy) ∧
      ∀ name, NativePolicyCodec.lookup NativeHeader.snapshotFormat out.installed.policy.snapshot name =
        ((NativePolicyCodec.lookup NativeHeader.policyFormat value "snapshot").bind
          (fun s => NativePolicyCodec.lookup NativeHeader.snapshotFormat s name)) := by
  obtain ⟨value,hp,_⟩ := Policy.boundSource (boundSource ok).installed
  refine ⟨value,hp,?_⟩
  intro name
  rw [Policy.snapshotRetained hp]
  rfl

theorem allCandidateSource {sha enrolled actor configRaw stateRaw policyRaw stateValue originals out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out) :
    ∀ e ∈ out.candidates,
      Candidates.check sha out.installed.policy out.installed.header.state
        out.collections e.original = some e :=
  Candidates.everyEntry (boundSource ok).candidates

theorem abortPreservesDownstream {sha enrolled actor configRaw stateRaw policyRaw stateValue originals out row}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out)
    (member : row ∈ out.collections.tail.aborts) :
    NativeFailureSection.LineageSource out.installed.policy
      ⟨row.body.configs,row.body.inputs,row.body.eligibility,row.body.plans,
       row.body.parameters,row.body.roots,row.body.applies⟩ :=
  Collections.abortLineageNotErased (boundSource ok).collections member

end DeltaReduce.ProfileSource.InstalledState
