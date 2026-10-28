import ProfileUnitState
import ProfileIscFinalization
import ProfileEcFinalization

/-! T047/T053. The selected whole unit-bearing state uses the SAME ISC/EC
candidate computations and full successor checks. `fields` is only their
numeric/collection view, never a legacy codec/admission result. Original schema-3
configuration and every complete quantum-bearing P remain in before/following.
Original source cuts, received authentication, clock and barriers still belong
to the enclosing producer; no public refinement result is an input. -/
namespace DeltaReduce.ProfileSource.UnitFinalization
open NativeReceiptBytes (Bytes)
open NativePolicyCodec (Value lookup)

def fields (b : UnitState.Bound) : InstalledState.Bound :=
  ⟨⟨⟨b.header.config.body,b.header.state,b.header.policy.source⟩,b.header.policy⟩,
    b.collections.core,b.candidates⟩

theorem fieldViewPreserves (b : UnitState.Bound) :
    (fields b).installed.header.config = b.header.config.body ∧
    (fields b).installed.header.state = b.header.state ∧
    (fields b).installed.policy = b.header.policy ∧
    (fields b).collections = b.collections.core ∧
    (fields b).candidates = b.candidates := ⟨rfl,rfl,rfl,rfl,rfl⟩

def iscOriginals (sigma : Bytes) (originals : Collections.Originals)
    (candidate : IscFinalization.Candidate) : Option Collections.Originals := do
  let raws ← Index.collect (fun pair => do
    let certificate ← ISCSourceV2.readCertificate pair.2
    some (ISCSourceV2.certificateJSON sigma certificate)) candidate.update.witnesses
  some {originals with inputCertificates := raws}

theorem iscUnrelatedOriginals {sigma originals candidate next}
    (ok : iscOriginals sigma originals candidate = some next) :
    {next with inputCertificates := originals.inputCertificates} = originals := by
  simp only [iscOriginals,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨raws,_,last⟩ := ok
  cases Option.some.inj last
  rfl

structure Isc where
  before : UnitState.Bound
  candidate : IscFinalization.Candidate
  nextOriginals : Collections.Originals
  following : UnitState.Bound

def isc (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (parent : ConfigurationUnits.Parent) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue : Value) (originals : Collections.Originals) (cut tick : Nat)
    (bodyId : Bytes) (frozen : List NativeInputSetBody.Tuple)
    (rows : List ConfigurationQC.Received) : Option Isc := do
  let before ← UnitState.bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
  let candidate ← IscFinalization.assemble sha (fields before) actor cut tick bodyId frozen rows
  let nextOriginals ← iscOriginals before.header.state.semantics originals candidate
  let following ← UnitState.bind sha enrolled parent actor configRaw stateRaw candidate.update.raw
    stateValue nextOriginals
  some ⟨before,candidate,nextOriginals,following⟩

structure IscSource (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (parent : ConfigurationUnits.Parent) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue : Value) (originals : Collections.Originals) (cut tick : Nat)
    (bodyId : Bytes) (frozen : List NativeInputSetBody.Tuple)
    (rows : List ConfigurationQC.Received) (out : Isc) : Prop where
  before : UnitState.bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals = some out.before
  computed : IscFinalization.assemble sha (fields out.before) actor cut tick bodyId frozen rows = some out.candidate
  originals : iscOriginals out.before.header.state.semantics originals out.candidate = some out.nextOriginals
  following : UnitState.bind sha enrolled parent actor configRaw stateRaw out.candidate.update.raw stateValue
    out.nextOriginals = some out.following

theorem iscSource {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId frozen rows out}
    (ok : isc sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId frozen rows = some out) :
    IscSource sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId frozen rows out := by
  simp only [isc,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨before,hb,candidate,hc,nextOriginals,ho,following,hf,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hb,hc,ho,hf⟩

theorem iscComplete {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId frozen rows out}
    (h : IscSource sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId frozen rows out) :
    isc sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId frozen rows = some out := by
  simp only [isc,h.before,h.computed,h.originals,h.following,Bind.bind,Option.bind]

theorem iscExactSignersAndBodies {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId frozen rows out}
    (ok : isc sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId frozen rows = some out) :
    out.candidate.quorum.originalRows = rows ∧
    out.candidate.certificate.certificate.body = out.candidate.selected.value.body ∧
    out.candidate.certificate.certificate.signers = out.candidate.quorum.target.signers :=
  IscFinalization.exactComputedSigners (iscSource ok).computed

theorem iscUnchangedLineage {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId frozen rows out}
    (ok : isc sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId frozen rows = some out) (key : String)
    (notWitness : key ≠ "input_set_certificates") (notFinal : key ≠ "finalized_input_set_ids") :
    lookup NativeHeader.snapshotFormat out.candidate.update.snapshot key =
      lookup NativeHeader.snapshotFormat out.before.header.policy.snapshot key :=
  IscFinalization.unchangedLineage (iscSource ok).computed key notWitness notFinal

theorem iscParentUnits {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId frozen rows out}
    (ok : isc sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId frozen rows = some out) :
    ConfigurationUnits.ParentMatches parent out.before.header.config ∧
    ConfigurationUnits.ParentMatches parent out.following.header.config :=
  ⟨UnitState.originalParentUnits (iscSource ok).before,
    UnitState.originalParentUnits (iscSource ok).following⟩

def iscFields (i : Isc) : IscFinalization.Original := ⟨fields i.before,i.candidate⟩

structure Ec where
  before : UnitState.Bound
  candidate : EcFinalization.Candidate
  nextOriginals : Collections.Originals
  following : UnitState.Bound

def ec (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (parent : ConfigurationUnits.Parent) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue : Value) (originals : Collections.Originals) (cut tick : Nat)
    (bodyId : Bytes) (rows : List ConfigurationQC.Received) : Option Ec := do
  let before ← UnitState.bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
  let candidate ← EcFinalization.assemble sha (fields before) actor cut tick bodyId rows
  let nextOriginals ← EcFinalization.successorOriginals before.header.state.semantics originals candidate
  let following ← UnitState.bind sha enrolled parent actor configRaw stateRaw candidate.update.raw
    stateValue nextOriginals
  some ⟨before,candidate,nextOriginals,following⟩

structure EcSource (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (parent : ConfigurationUnits.Parent) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue : Value) (originals : Collections.Originals) (cut tick : Nat)
    (bodyId : Bytes) (rows : List ConfigurationQC.Received) (out : Ec) : Prop where
  before : UnitState.bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals = some out.before
  computed : EcFinalization.assemble sha (fields out.before) actor cut tick bodyId rows = some out.candidate
  originals : EcFinalization.successorOriginals out.before.header.state.semantics originals out.candidate = some out.nextOriginals
  following : UnitState.bind sha enrolled parent actor configRaw stateRaw out.candidate.update.raw stateValue
    out.nextOriginals = some out.following

theorem ecSource {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId rows out}
    (ok : ec sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows = some out) :
    EcSource sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows out := by
  simp only [ec,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨before,hb,candidate,hc,nextOriginals,ho,following,hf,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hb,hc,ho,hf⟩

theorem ecComplete {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId rows out}
    (h : EcSource sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows out) :
    ec sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows = some out := by
  simp only [ec,h.before,h.computed,h.originals,h.following,Bind.bind,Option.bind]

theorem ecParentUnits {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
    cut tick bodyId rows out}
    (ok : ec sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals
      cut tick bodyId rows = some out) :
    ConfigurationUnits.ParentMatches parent out.before.header.config ∧
    ConfigurationUnits.ParentMatches parent out.following.header.config :=
  ⟨UnitState.originalParentUnits (ecSource ok).before,
    UnitState.originalParentUnits (ecSource ok).following⟩

/-- Original-event and companion material may reuse the already qualified
field-only EC computation, without claiming its legacy byte binder succeeded. -/
def ecFields (e : Ec) : EcFinalization.Whole :=
  ⟨⟨fields e.before,e.candidate⟩,e.nextOriginals,fields e.following⟩

def replayEc (old : Ec) (current : UnitState.Bound) : Option UnitState.Bound :=
  if EcFinalization.Retained (ecFields old) (fields current) then some current else none

theorem replayEcKeepsWholeCurrent {old current out}
    (ok : replayEc old current = some out) :
    out = current ∧ EcFinalization.Retained (ecFields old) (fields current) := by
  unfold replayEc at ok
  split at ok <;> try contradiction
  rename_i retained
  cases Option.some.inj ok
  exact ⟨rfl,retained⟩

theorem replayEcNoUnitOrLineageErasure {old current out}
    (ok : replayEc old current = some out) :
    out.header = current.header ∧ out.collections = current.collections ∧
    out.candidates = current.candidates := by
  rw [(replayEcKeepsWholeCurrent ok).1]
  exact ⟨rfl,rfl,rfl⟩

end DeltaReduce.ProfileSource.UnitFinalization
