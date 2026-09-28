# Arithmetic amendment candidate contract — accepted residual R1–R7

Tasks: T000–T003, T044, T047, T053–T057. Version: **1.1.0**.
Status: **SCOPE_FROZEN; CANDIDATE_NOT_FORMAL_GO**.

## Authority and fixed work boundary

On 28 September 2026 the user accepted the exact
`accepted-residual-20260928.md` as the Definition of Done for this candidate.
Its raw SHA-256 is
`51b1a92b724f6021eb4a534e6f86c92905c8fecd6f55fb5173c7eaf253d8a2e6`.
The temporary pause recorded in that historical document was subsequently lifted
for **R1–R3 only**. Its residual requirements, exclusions and acceptance criteria
are unchanged. R4–R7 remain required for GO but are deferred work.

This is scope authorization, not acceptance of an unproved mathematical claim.
The historical merged authority remains semantics
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
Amendment 0001 remains `DRAFT_NOT_AUTHORITY`. Neither a passing phase-0 check nor
this contract authorizes runtime changes or removing the native arithmetic guard.

R1 freezes the contract and binds it to the current candidate snapshot. Subsequent
proof/source changes must refresh their compatibility bindings; they cannot
silently change this contract. Final evidence/reproduction/report/review acceptance
is still R4–R7. This document does not add an R8 or a new safety obligation.

## Existing arithmetic domain, not a fixture-derived restriction

The target is amendment 0001's checked native PARAMETER/APPLY operation graph,
with the selected INT64 or INT128 accumulator and **FULL_SIGNED_INT64** output,
including `INT64_MIN`. Each product, ordered accumulator prefix, conversion,
per-domain rounding, mixture and optimizer intermediate must meet its existing
declared bound. Final-result equality cannot excuse an overflowing intermediate.
Rounding is ADR-0002's Euclidean rule with exact half ties toward positive infinity.

Vector lengths, shard partitions and input counts are those allowed by the
existing immutable schema/profile and canonical decoder contracts. The statement
is not restricted to the finite examples or one coordinate per shard. Complete
ordered coverage and parent/current identity remain mandatory. No additional
native admission restriction is introduced here.

The production TLC scopes are finite. The limit127 scalar full-state examples,
ordinal/decimal aliases, SamePlanParents restriction and the diagnostic witness's
size limits are explicit scopes of particular checkers. Their successful checks
do not imply full native-width admission or arbitrary-vector correspondence.
Discharging that correspondence is R2; it may not be relabeled as an assumption
or removed from scope in order to complete R1.

## Admissible assumptions and what must actually be derived

The existing spec section 2.2, FR-033, PO-AB1 and refinement contract permit named
hash/canonical-encoding/signature abstractions and independently authenticated
source observations. The safety domain retains enrolled epoch identities,
`3f+1` validators and at most `f` Byzantine validators. Liveness assumptions stay
exactly those of each registered configuration.

The trusted boundary may supply primitive configuration/metadata, authenticated
artifact identity, certificate authentication and a faithful observation of the
original durable bytes. These must be independently anchored and consistently
used. A synthetic fixture pin or self-consistent hash is not authentication.

The boundary must **not** supply the desired whole translated body, acceptance
Boolean, recovery equality or final refinement theorem as an assumption. Exact
decoding, field/parent/context/configuration agreement, representability and the
recomputed operation graph still have to follow from the checked inputs. Alias
injectivity may be a named identity abstraction only with its domain and source
binding explicit; changing aliases cannot collapse protocol-distinct states.

Physical cryptographic implementations, filesystem fsync correctness and an
arbitrary production runtime are not proved by formal helper lemmas. The required
claim is the existing formal refinement under its named abstractions, plus the
source-linked decoding/serialization/arithmetic obligations of PO-AB1. This does
not create a prerequisite to implement a new production exporter before GO.

## R2 and R3: finite statement boundaries

R2 covers the existing formal action vocabulary and all observable fields needed
by that vocabulary: original actor/kind/context/parents/body, admitted arithmetic
and its entire result, immutable configuration, certificate identity and state
projection. Complete state-root preimages cannot be replaced by opaque labels.
The projection must preserve distinctions that affect an existing invariant.

Correct ABORT projection must retain its certificate lineage, context, terminal
outcome and unchanged current checkpoint (FR-038, PO-R1/R2). An independent,
universal `full public ABORT body` constructor is not an extra deliverable.
Content-ID abstraction with exact metadata predicates is permitted by the
original refinement contract, provided its sufficiency is proved. Empty ancestor
substitution or an assumed whole-body mapping is not such a proof.

R3 proves that the R2 relation is preserved by the existing admission, persistence,
exposure, send/delivery/QC/current and crash/recovery/replay transitions. Its prior
state includes the full relevant all-actor durable journal and certified/current
state, not just a record count. Initial snapshots must meet the existing Init or
verified reachable-history relation; an empty-only helper is not the whole claim.

Known durable but unexposed records, unknown append outcome, verified absence,
surviving complete records and corrupt/ambiguous scans remain distinct. Missing
responses do not prove absence. Recovery preserves original bytes/effect/sequence,
does not allocate another vote, and cannot enable READY from an incomplete scan.
Exact retry is historical lookup rather than fresh admission against a new current
parent. No new repair operation, failure terminal or quorum shortcut is added.

These are decompositions of PO-AB1 and the existing PO-R1/R2/refinement contract,
not an unbounded request for more helper layers. The mandatory remaining conjunct
is `nativeArithmeticRecoveryRefines`; its statement must establish the relation,
not assume it. Component lemmas alone cannot discharge it.

## Baseline consistency evidence and non-claims

`baseline-inputs.json` pins this contract, the accepted residual document, the
existing amendment and normative inputs. `verify_phase0.py` checks the pinned
1.1.0 registry, required input inventory, exact hashes and derived compatibility
identity. The four existing harness invariants are retained with their bounded
scope: NoStaleArithmeticVotes, HeterogeneousExpected, PersistenceRecordSound and
PersistenceRecoverySound. They are not new universal invariants or proof claims.

Phase-0 PASS means that this contract snapshot is internally bound and complete
as an input inventory. It does not mean R2/R3, a full formal gate, independent
reproduction/review, native runtime qualification or Formal GO has passed.
The pre-freeze NO_GO report is historical evidence for its recorded source tree;
it must not be reused as an exact-source report after these metadata changes.
