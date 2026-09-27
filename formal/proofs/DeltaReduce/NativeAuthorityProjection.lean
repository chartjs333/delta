import DeltaReduce.NativeStateProjection
import DeltaReduce.NativeGraphClosure

/-! Full source-computed authority root. A closed graph is not an authenticated
native root: configuration/units/certificates/recovery still need their boundary. -/
namespace DeltaReduce.NativeAuthorityProjection
open NativeBinding
open NativeVectorContext (Bound)
open NativeVectorArtifacts (Artifact pack)
open NativeIscProjection (Stored encodeRef)

def value (b : Bound) (s : NativeStateProjection.Image) : Authority :=
  ⟨NativeVectorAuthority.context b,s.graph.isc.schema.ref,s.profileArtifact.ref,
    s.graph.plan.ref,s.modelArtifact.ref,s.optimizerArtifact.ref,
    s.graph.isc.isc.ref,s.graph.isc.ec.ref,s.graph.apc.ref⟩

def encodeContext (c : Context) : Bytes :=
  asciiBytes "{\"epoch\":" ++ quotedBytes (asciiBytes c.epoch) ++
  asciiBytes ",\"hard_deadline\":" ++ asciiBytes (toString c.hardDeadline) ++
  asciiBytes ",\"height\":" ++ asciiBytes (toString c.height) ++
  asciiBytes ",\"parent_checkpoint\":" ++ quotedBytes (asciiBytes c.parentCheckpoint) ++
  asciiBytes ",\"round\":" ++ quotedBytes (asciiBytes c.round) ++
  asciiBytes ",\"view\":" ++ asciiBytes (toString c.view) ++ [125]

def encode (a : Authority) : Bytes :=
  asciiBytes "{\"kind\":\"AUTHORITY\",\"payload\":{\"context\":" ++ encodeContext a.context ++
  asciiBytes ",\"model\":" ++ encodeRef "MODEL" a.model ++
  asciiBytes ",\"optimizer\":" ++ encodeRef "OPTIMIZER" a.optimizer ++
  asciiBytes ",\"parents\":{\"apc\":" ++ encodeRef "APC_PROJECTION" a.apc ++
  asciiBytes ",\"ec\":" ++ encodeRef "EC_PROJECTION" a.ec ++
  asciiBytes ",\"isc\":" ++ encodeRef "ISC_PROJECTION" a.isc ++
  asciiBytes "},\"plan\":" ++ encodeRef "PLAN" a.plan ++
  asciiBytes ",\"profile\":" ++ encodeRef "PROFILE" a.profile ++
  asciiBytes ",\"schema\":" ++ encodeRef "SCHEMA" a.schema ++ [125,125]

def ContextChecks (b : Bound) : Prop :=
  asciiBytes (NativeVectorAuthority.context b).round = (NativeVectorAuthority.policy b).round ∧
  asciiBytes (NativeVectorAuthority.context b).epoch = (NativeVectorAuthority.policy b).epoch ∧
  asciiBytes (NativeVectorAuthority.context b).parentCheckpoint = (NativeVectorAuthority.state b).wire.parent ∧
  ∀ x ∈ [(NativeVectorAuthority.context b).round,(NativeVectorAuthority.context b).epoch,
    (NativeVectorAuthority.context b).parentCheckpoint], validIdentifier x = true
instance (b) : Decidable (ContextChecks b) := by unfold ContextChecks; infer_instance

def check (codec : Codec) (store : Store) (depth : Nat) (b : Bound) (s : NativeStateProjection.Image) :
    Option Artifact := do
  if ContextChecks b then
    let root ← pack codec.hash (encode (value b s)) (.authority (value b s))
    if Stored codec store root ∧ NativeGraphClosure.check codec store depth root.ref = true then
      some root
    else none
  else none

attribute [local irreducible] ContextChecks NativeVectorArtifacts.pack NativeIscProjection.Stored

theorem checked {codec store depth b s root} (h : check codec store depth b s = some root) :
    ContextChecks b ∧ pack codec.hash (encode (value b s)) (.authority (value b s)) = some root ∧
    Stored codec store root ∧ NativeGraphClosure.check codec store depth root.ref = true := by
  unfold check at h
  split at h
  next ctx =>
    simp only [bind,Option.bind_eq_some_iff] at h
    obtain ⟨r,hr,last⟩ := h
    split at last
    next good => cases Option.some.inj last; exact ⟨ctx,hr,good⟩
    next => cases last
  next => cases h

theorem rootResolved {codec store depth b s root} (h : check codec store depth b s = some root) :
    Resolves codec store root.ref root.raw (.authority (value b s)) := by
  have r := NativeIscProjection.storedResolves (checked h).2.2.1
  rw [(NativeVectorArtifacts.packed (checked h).2.1).2.1] at r
  exact r

theorem rootComplete {codec store depth b s root} (h : check codec store depth b s = some root) :
    Complete codec store root.ref := NativeGraphClosure.complete (checked h).2.2.2

theorem exactBytes {codec store depth b s root} (h : check codec store depth b s = some root) :
    root.raw = encode (value b s) := (NativeVectorArtifacts.packed (checked h).2.1).1

theorem rootBound {codec store depth b s root} (h : check codec store depth b s = some root) :
    root.ref.id.length = 32 ∧ 0 < root.ref.length ∧ root.ref.length ≤ 4194304 :=
  NativeGraphClosure.bounded (checked h).2.2.2

theorem allEightChildren (b s) : (.authority (value b s) : Payload).refs =
    [s.graph.isc.schema.ref,s.profileArtifact.ref,s.graph.plan.ref,s.modelArtifact.ref,
      s.optimizerArtifact.ref,s.graph.isc.isc.ref,s.graph.isc.ec.ref,s.graph.apc.ref] := rfl

theorem originalContextBytes {codec store depth b s root} (h : check codec store depth b s = some root) :
    asciiBytes (value b s).context.round = (NativeVectorAuthority.policy b).round ∧
    asciiBytes (value b s).context.epoch = (NativeVectorAuthority.policy b).epoch ∧
    asciiBytes (value b s).context.parentCheckpoint = (NativeVectorAuthority.state b).wire.parent := by
  have ctx := (checked h).1
  unfold ContextChecks at ctx
  exact ⟨ctx.1,ctx.2.1,ctx.2.2.1⟩

theorem zeroDepthRejected (codec store b s) : check codec store 0 b s = none := by
  unfold check
  split
  · cases pack codec.hash (encode (value b s)) (.authority (value b s)) <;>
      simp [bind,Option.bind,NativeGraphClosure.check]
  · rfl

def run (sha : Bytes → Bytes) (codec : Codec) (store : Store) (depth : Nat)
    (prep : NativeStateProjection.Preparation) (units : NativeStateProjection.UnitSource)
    (pid : Bytes) (initial : NativeCurrentPointer.State) (observation : NativePointerWal.Observation)
    (history : List NativeCurrentHistory.Input) (permission : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) : Option (Bound × NativeStateProjection.Image × Artifact) := do
  let (b,s) ← NativeStateProjection.run sha codec store prep units pid initial observation history permission inputs
  let root ← check codec store depth b s
  some (b,s,root)

theorem runSource {sha codec store depth prep units pid initial observation history permission inputs b s root}
    (h : run sha codec store depth prep units pid initial observation history permission inputs = some (b,s,root)) :
    NativeStateProjection.run sha codec store prep units pid initial observation history permission inputs = some (b,s) ∧
    check codec store depth b s = some root := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨b',s'⟩,hs,r,hr,last⟩ := h
  cases Option.some.inj last
  exact ⟨hs,hr⟩

end DeltaReduce.NativeAuthorityProjection
