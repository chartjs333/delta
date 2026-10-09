# Arithmetic unit source selection — R2.3 boundary

T047/T053, 9 October 2026. **R2.3 OPEN / Formal NO_GO.**
Assignment `13069d7e-a148-475a-bd49-9885bf2f283d`, effective scope 13.
This records a missing source-selection contract, not a new proof obligation,
an impossibility theorem, or a complete production-reachable counterexample.
No unit rule, default, field, schema or runtime change is implemented here.

## What has been established

Commit `0246277a29fb8477112d4b6f5e900417d46fe167` qualifies the independent
bootstrap/full trusted-floor/manifest source join. Its general Lean results
retain the original initial-configuration bytes, complete inventory, all trusted
records and original journal prefixes. They do not interpret an unspecified
initial-configuration field as arithmetic authority.

The remaining unit-source obligation predates this work. Feature 008 §3 and
FR-026 require the configured ApplyArithmeticProfile to define exact arithmetic
representations; amendment 0001 requires an independently authenticated root
binding apply/model/optimizer quantum. R2.1/R2.2 already prove their arithmetic
and constructor results for the original stated premises. Those results remain
CLOSED; this audit neither changes their premises nor invalidates them.

## Exact existing paths and their limits

The immutable source index and lexical census are in
[`evidence/unit-source-selection/audit.json`](evidence/unit-source-selection/audit.json).
Each source has a full commit, repository path, byte length and SHA-256.

| Existing source | What it actually supplies |
|---|---|
| `60c692f6:delta-core-cpp/include/delta/certificates/contracts.hpp`, `ApplyArithmeticProfile`; matching `src/certificates/contracts.cpp` canonical JSON | Accumulator proof, domain weights, learning rate, momentum, decay, Nesterov and rounding; no apply/model/optimizer quantum |
| Same commit, `delta-core-cpp/include/delta/apply/engine.hpp` and `src/apply/engine.cpp` | Original model/momentum and DomainAggregate integer vectors and value hashes. Their bytes do not select physical units |
| Same commit, `specs/004-compressed-delta-protocol/spec.md`, FR-002/003 | Original per-segment **Q input** scale. This is the conversion numerator scale, not a rule choosing the common apply/model/optimizer scale |
| Same commit, `specs/008-certificates-and-consensus/spec.md`, §3, FR-026/032 | Existing requirement for configured representation and profile/hash binding. It is not an exact missing-field decoder |
| `26eb02d0:docs/adr/0013-snapshot-provenance-profile-v1.md`, §§2–4 | Independent `initial_config_ref`, genesis/schema/producer pins and original byte custody; no concrete unit-selector field or derivation rule |
| `1438fa3d:docs/adr/0016-storage-availability-source-binding-v1.md` and `90561a97:docs/adr/0018-authenticated-availability-contract-v1.md` | Storage authority/observed availability, not a selector for optimizer units |
| `12326b89:formal/proposals/retention-policy-source-binding-v1.md`, §§2–6 | Exact R/E retention declaration binding only. Its approval does not select an arithmetic unit field |
| `0246277a:formal/proofs/DeltaReduce/NativeStateProjection.lean`, `UnitKey`, `UnitSource`, `construct` | A deliberately unresolved primitive source, keyed by full context/APC/apply-profile/accumulator/current tuple; missing units reject |
| Same commit, `NativeAuthorityProjection.lean` and `NativeBindingConstruction.lean` | Constructed graph closure plus separate `nativeAnchor`/`nativeRecovery` authentication premises. Hashing a newly constructed PROFILE does not authenticate its unit selection |
| Same commit, `ArithmeticBinding.lean`, `Profile.applyQuantum`, `StateVector.quantum`, `Binding.modelQuantum/optimizerQuantum` | Existing candidate graph grammar and equality obligations. It provides a place to represent units after selection, not proof that an original native authority selected those bytes |

The current closed RoundConfig decoder (`ProfileConfiguration.configuration`)
preserves its existing fields and the specifically approved storage binding.
The initial authority resolver preserves the entire independently pinned initial
configuration, and reads the explicitly specified `storage_authority` field.
Its synthetic test explicitly labels surrounding initial fields
`retained-not-qualified-as-genesis`. That test cannot supply a missing original
unit field by example.

## Why this is a choice of source semantics, not merely a decoder lemma

Existing kernel results `NativeStateArtifacts.sourceCannotDetermineQuantum`
and `noUniqueQuantumProjection`, with
`NativeStateProjectionVectors.numericProfile` and `sourceAllowsAnotherQuantum`,
show that the same original numeric profile admits candidate quantum `1/4`
and `1/2`, yielding different complete projected profiles. These results prove
insufficiency of that profile alone, **not** impossibility for every full source.

The existing amendment-0001 conversion is
`R((N*u)*y, (L*v)*x)`, where `u/v` is Q scale and `x/y` is apply scale.
For fixed `N=1`, `L=1`, Q scale `1/2`, the two apply scales above produce `2`
and `1`. The existing proposal oracle reproduces these values in the audit.
This small illustration is not a valid snapshot, native capture or TLC trace.

Consequently, choosing a constant, copying units from projected output, or
accepting an arbitrary resolver changes or assumes the required correspondence.
Writing a new original config/profile field would specify new canonical source
semantics and potentially new signed hashes. Generic source custody and content
hashes do not decide which such field/rule the deployment originally used.

The exact unresolved selection is:

`independently authenticated initial/config authority + original UnitKey`
`→ selected configured ApplyArithmeticProfile + apply/model/optimizer quantum`.

No applicable exact selector was identified in the recorded immutable contracts.
This is a scoped finding about available applicable sources; an additional
already-authoritative original contract could resolve it. It is not evidence
that no such external artifact can exist or that the full Profile-v1 relation
is mathematically impossible.

## Decision requested, without implementation

Authorize one **specification-only** pass to resolve this exact missing binding.
It must first reuse any provided immutable original selector and its authority
path. If none exists, document one minimal concrete future-generation binding
using the existing initial/configuration/validator authority and existing
PROFILE/MODEL/OPTIMIZER representation. Do not invent a production quantum value,
new trust root, success callback or rule inferred from desired outputs.

The deliverable must identify exact selected fields/bytes/context, configured
profile selection, parent/current unit continuity, initial applicability,
canonical bounds and compatibility effects on hashes/signatures/QC claims. Any
new field or derivation rule remains PROPOSED until a separate exact decision.
Stop after that document; this request does not approve its eventual design or
implementation and does not reopen R2.1/R2.2.

All existing restrictions remain: fixed enrolled Profile-v1, O not F, no new
trust, no source restriction/caps/lineage erasure, no production/guard removal,
no concrete sigma, no full R3, no weakened assumptions/invariants, and no false
GO. The existing sprint/assignment/history remain. Reviewed substantive R2.3
closure still precedes the named recovery theorem. This audit has no graph
review or independent Formal GO attestation.
