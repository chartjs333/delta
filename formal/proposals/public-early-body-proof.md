# Original CONFIG/ISC to complete public vote construction

Tasks T044/T048/T053/T054/T056/T057; Feature000 amendment 0001. This is
conditional early-vote body construction at the original historical state,
not complete public/native recovery, local acceptance or Formal GO.

`NativeEarlySource` executes `NativeSelectedVote.fromBytes` on the original
policy, preceding state and VOTE bytes with the actual replay facts. Existing
whole snapshot/candidate admission, exact original frame/state encoding,
validator/epoch/height/view/round/context/body/parents and sequence identity are
retained. CONFIG checks its selected kind, configured native ID and proposed
membership. ISC scans the entire original checked snapshot input list and
requires exactly one matching native body ID. It rechecks the original body
decoder, computed body ID, complete expected context and tuple validity. Missing
or ambiguous matches reject. Original tuple order/count and each complete
availability/commitment/domain/ticket tuple are retained. No later aggregate,
arithmetic Binding or successful PARAMETER/APPLY is required.

`PublicEarlyBody` loads independently keyed primitive names and close policy.
CONFIG builds the entire public envelope and ConfigContext; ConfigBodies in the
TLA model are configured model values, so the native configuration ID maps to a
primitive public name, not an invented decoded configuration. ISC builds all
five InputBody fields and the complete public envelope. Public canonicalRoot is
the complete entry set, not the native input-root hash. Each content-name key
includes native body ID, the whole native body/context/root/ordered tuple list,
and the entire selected tuple. Ticket names also retain the full native context.
Every source tuple becomes one entry; no filter, truncating zip or deduplication
can remove it. Sorting retains all values. Pairwise distinct projected entries
and complete canonicality are checked before comparing the entire candidate
vote, including validator, kind, context and body.

The metadata boundary is substantive: `Trust` must independently authenticate
the primitive names and close policy. The native ISC does not contain the
public content symbol or configured close policy. Fixture trust is deliberately
synthetic. Rejecting collapsed entries is a projection representability
restriction, not a change to native admission. Global alias injectivity,
configuration/policy agreement across every module, cryptographic/exporter
authentication and public availability/committee/QC semantics remain open.
Raw constructors and a caller-selected Checked value do not establish original
source authority; use Loaded and the historical source relation.

`PublicEarlyHistory` combines the source/body check with the original row's
preceding state and runtime facts. An ordinary captured row loads the same
original selected candidate by executable determinism. Successful candidate
recovery supplies an actual executed prefix, prior machine and capture step
for every ordinary row, with its original position. It does not re-admit a retry
against the later final state. This helper does not yet project the entire
cache or equate it with all public actor durable sets. NativeCacheProjection
still rejects every ordinary row; no resolver, NativeVoteTrust, NativePrepared,
ready event or recovered flag is manufactured.

Kernel cases reuse the actual pinned original ISC admission and native body hash
component proofs, then compose a complete ISC public vote with synthetic names.
CONFIG examples check shape/canonicality only, not new native CONFIG admission.
Small negatives cover actor, context, kind, body, omitted entries, close policy,
missing names/policy, duplicate public entries and complete source-key retention.
Python cross-source checks compare retained original native body/context hashes
and public TLA field inventories; a counterexample shows why a ticket/commitment
alias alone loses availability/domain/root distinctions. No new native run,
full-state trace, production mutant or independent attestation is claimed.

Remaining ordinary EC/APC/ROOT/VIEW/ABORT projections, shared alias/configuration
identity, all-actor sequence abstraction and complete public durable equality
are still required. Full phase/send/delivery/QC/current/crash/unknown/torn/repair
refinement, production snapshot equivalence, physical WAL/exposure authority,
bounded concrete codec/hash/exporter resources, native compatibility, contract
freeze, clean offline reproduction and independent review remain open. The
mandatory nativeArithmeticRecoveryRefines theorem remains missing; guard and
runtime are unchanged. UNKNOWN/incomplete cannot become complete through this
construction.

Reproduce with `lake --no-cache build DeltaReduce` in `formal/proofs`, fresh
individual compilation of the four named modules and AxiomAudit, tooling/oracle
tests, refinement fixtures and semantic regeneration. Evidence records the
precise final sources; source constructors alone are not formal authority.
