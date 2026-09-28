# Original certified corpus and conditional aggregate/APPLY Binding

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-aggregate-binding.json`.

NativeCertifiedCorpus loads the actual original aggregate section, including
bounded original PARAMETER certificates, selects an actually finalized ROOT by
its original ID, and executes deriveParameterCorpus on the computed authority.
A strict ordered zipper checks every original finalized shard against its own
fresh NativeVectorJoin computation. The original shard ordinal is selected from
the original layout. Each leaf retains the full source Q list, domain/shard,
ISC/EC/PLAN/context, denominator, exact numerator vector and canonical decimal
spelling. The computed body also equals the corresponding computed corpus body,
including all projected Q identifiers. Previously checked proposed PARAMETER
bodies are not used as evidence for finalized QCs.

All original root keys and leaves are retained in order. Missing/extra records
reject by length; changed keys, parents, values and leaf sets reject at their
corresponding checks. Source native leaves are sorted only as required by the
original certificate encoding; source contribution order remains intact. Draft
domain/shard enumeration must equal original ROOT key order: this is a projection
restriction, not a new native admission rule. Exact decimal spelling is stronger
than the old native negative-zero/leading-zero behavior. No native repair occurs.

NativeAggregateBinding constructs the entire AGGREGATE_PROJECTION canonical JSON
from the computed authority ID and all computed PARAMETER bodies. Store bytes,
length, hash, canonical decoding and exact payload must agree. It constructs
aggregate Complete (inline bodies have no recursive payload edges) and extends
Binding to an Anchor containing both authority and aggregate. The original
authority bytes, model, optimizer, profile and paths are retained unchanged.
AUTHORITY has no aggregate edge, avoiding circular hashes. The older PARAMETER
entry point still requires no later aggregate or APPLY.

The extension requires the SAME HashAdapter and separate authentication of the
new Anchor/recovery and projected certificate. An explicit CertificateAuthority
premise relates the entire original ROOT source and QC ID to the exact projected
artifact. There is no instance of this premise and no inference of signatures or
custody from successful hashing. Original native QC IDs and projected artifact
IDs have different preimages. Earlier anchor authentication does not authenticate
the extended anchor. UnitSource and configured profile provenance remain OPEN.

The APPLY checker reloads the actual original APPLY section, selects the original
proposal, and compares its entire selected ROOT certificate plus original ID and
selected profile ID. A general theorem derives equality of the full original
ROOT source representations using their checked parsers, not hash equality.
NativeApplyResult.check executes all certified-body loading, conversions, mixture
and optimizer calculations and compares exact candidate decimal values and native
model/optimizer/parent hashes. fromSource composes the earlier raw preparation,
current-history, source graph and authority construction, corpus checking,
aggregate extension and APPLY candidate checking with the same selected original
profile. All trust and quantum premises remain explicit.

This is a conditional executable composition, not an authenticated native run or
full admission/recovery theorem. No positive full raw original/draft instance is
manufactured; original008 proof/base/current captures remain absent. Tests reuse
existing original certificate components and separately check small mathematical
body mutations and complete JSON bytes. Synthetic short encodings do not prove
native signatures, codec/hash implementations or current-state custody.

Remaining: instantiate independently authenticated original artifacts/configuration/
units/current, join arbitrary initial snapshots, full historical journal and actual
phase/QC/send/delivery/current/crash/unknown/torn/repair/physical-WAL relations,
prove concrete decoder/hash/exporter resource bounds, resolve native compatibility,
freeze the amendment, reproduce clean offline and obtain independent review.
Known computed outputs confer no phase role, send authority, quorum or current
advance. No nativeArithmeticRecoveryRefines, local PASS, guard change or GO.
