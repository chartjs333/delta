# Complete-state/native first-vote correspondence, v2 candidate

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060; amendment 0001.
Status: conditional finite projection tooling, **not native authority**.
No TLA/Lean transition, public trace v1 schema, runtime or WAL format changes.

## A separate version and trust boundary

The old native v1 snapshot binds an opaque producer root. The complete-state
profile binds the canonical values of all 64 protocol variables. These roots
are incompatible. Neither replacing the v1 root nor hashing a new wrapper proves
that the native runtime produced the complete state.

`deltareduce.full-public-native.v2-candidate` therefore retains the exact old
snapshot ASCII bytes/ID and original operation ID as **source observations**.
It separately records complete prior/next roots, exact model/config identity,
the selected modeled envelope and the original canonical command/envelope/
receipt/effect bytes. It does not emit a modified v1 snapshot or substitute its
root. The ID is SHA-256 of this version string, NUL and sorted canonical JSON.
A v1 snapshot supplied to the v2 verifier is rejected by version, and a legacy
root supplied for a complete state fails the complete-state preimage check.

The current `PinnedFixtureSources` registry pins exact public/native source
digests independently of any submitted claim and runs the entire existing
public/native refinement and diagnostic durability checker before use. It is a
synthetic fixture registry, **not authenticated production metadata**. The output
always says `SYNTHETIC_PINNED_FIXTURE_NOT_NATIVE_AUTHENTICATION`, and the generated
container says `native_export_authenticated=false`. Rehashing a claim with another
provenance label cannot upgrade it. There is no accepted production-authenticated
mode or permissive authentication Boolean in this checker.

The unresolved production premise is named
`AuthenticProjection(producer, source/environment, run, position, nativeSnapshotBytes,
completeStatePreimage, configuration)`. A future independently resolved registry
must bind that exact tuple and the native acquisition/journal boundary. A caller's
root, self-signed wrapper or matching output hash cannot establish the premise.
How the native exporter acquires all variables, preserves atomicity and proves
that provenance remains a mandatory refinement task under the formal-first STOP.

## Executable correspondence

For each of the nine first arithmetic votes in the pinned complete arithmetic
path, the checker independently performs these steps:

1. Validate both complete preimages, every variable, canonical tagged value,
   resource bound, model/config identity and root.
2. Resolve the original actor, action, role, height/epoch/round, view/time,
   current checkpoint and recovered readiness from the pinned source registry
   and complete state. Require ACTIVE, no abort request, alive/READY and the
   unchanged parent at first admission. This profile's source anchor supplies
   the fixed native deadline; the separately pinned TLC configuration binds the
   same deadline and finite identity vocabulary.
3. Derive the single new durable envelope from the before/after sets. Check actor,
   kind, context and previously proposed candidate. Count the prior actor's entire
   durable vote set, require its exact counter and derive sequence +1. Require no
   prior identical formal context. No arithmetic-only renumbering is permitted.
4. Check the exact vote projection changes: durable/volatile sets, typed vote set
   and sequence. All other complete state fields must be unchanged. This is a
   structural vote projection check, **not an alternative production Next**.
5. Resolve actual modeled config/ISC/EC/APC certificates and their nested parent
   chain, seed, eligible membership, ticket/commitment/availability identities.
   Check complete ISC/EC/APC and ticket bodies against this fixed identity profile,
   including canonical root, norm evidence and coefficient-profile metadata.
   For every used QC, require at least three distinct configured signers, with
   matching envelopes in both delivered and durable vote sets. These are the
   model's abstract signatures; cryptographic authentication is not proved.
6. Reconstruct the expected native authority and PARAMETER body using the checked
   artifact graph, exact Q/schema/shard inputs, weights/quanta, parent model and
   optimizer. Compare the **whole** modeled arithmetic body and metadata with
   this reconstruction. For APPLY, require complete two-shard coverage, each
   certified PARAMETER body and aggregate QC; recompute conversions, optimizer,
   full native APPLY body and structured next model/optimizer values.
7. Re-encode the full native command and body hash and compare them with the
   original bytes. Bind the original diagnostic receipt/effect and sequence from
   the separately checked completed operation. No new receipt is created in the
   native journal. A receipt here is source output evidence, not network delivery;
   the full-state TLC path retains separate send/delivery actions and quorum power.

`verify_projection` repeats this derivation and compares every claim field with
the computed result. No supplied expected-result equality or arithmetic approval
flag substitutes for it. The independently pinned source constructor and strict
v2 version stay mandatory even for a rehashed otherwise well-formed claim.

## Finite identity boundary and non-claims

The registry supports only the existing one-ticket/one-domain/two-scalar-shard
example with three honest actors. Its explicitly pinned symbol mapping relates
TLA identifiers/structured values to native schema/profile/authority/parent IDs.
It is not a general native parser or a cryptographic proof that abstract config,
seed, content and certificate records hash to those native IDs. Original native
IDs/bytes are retained and mathematical values are rederived; production
certificate/exporter provenance and general identity abstraction remain open.

The complete source fixture contains the later aggregate and completed public
trace. Requiring that fixture in this diagnostic registry is not an availability
precondition for runtime PARAMETER admission. The existing native PARAMETER
mathematics still needs no later conversion/aggregate. Admission completeness,
unknown/failed/incomplete observations, historical retry, arbitrary snapshots,
WAL cuts and repair are not newly covered by this first-vote checker. Incomplete
durability cannot be represented by filling in a complete state. Actual complete
state replay remains checked separately by production TLA Init/TypeOK/Next; the
new output is not a Lean composition or `nativeArithmeticRecoveryRefines`.

The underlying TLA path and old native source bytes are unchanged. Arithmetic
scope is still finite limit 127 for TLC and native INT64 for the fixture oracle,
with no all-width or production conformance claim. Formal semantics ID therefore
stays unchanged; a new source-bound NO_GO report identifies this tool revision.

## Reproduction and closure

```text
python formal/scripts/generate_public_native_projection.py
python -m unittest discover -s formal/tests -p test_public_native_projection.py -v
```

The emitted nine wrappers preserve arithmetic sequences 5/6/8 for each actor.
Tests rehash changed complete states and claims, exercise wrong arithmetic,
missing/undelivered QCs, sequence, current, readiness, time/view, action, hidden
side effects, old roots/versions and forged provenance labels. Full generation is
byte reproducible. Native files and the original complete arithmetic path remain
unchanged and independently checked.

Next, express the complete-state/native identity relation in the mandatory proof
layer, with an audited general representation/decoder boundary rather than a
finite table. Compose it with actual reachable native journal operations and
global TLA vote/QC/current behavior, including arithmetic crash/unknown recovery.
General adapters/admission, initial snapshots, contract freeze, clean reproduction
and independent reviews still block authority. Mandatory coverage remains 44/45.
