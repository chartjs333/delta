# DeltaReduce v1 Parametric Proof Obligations

**Status**: Normative theorem plan  
**Reference prover**: Lean 4 (an equivalent machine-checked system requires an ADR)

TLC explores finite behaviors. The obligations below cover claims parameterized by `f`, ticket counts, integer bounds and partitions. Mandatory proofs MUST compile without `sorry`, unreviewed axioms or hidden classical/choice assumptions beyond those explicitly listed.

## PO-AB1 — Native arithmetic artifact binding (pending amendment 0001)

**Status**: OPEN; the standalone `formal/proposals/ArithmeticBinding.lean` helper
statements do not discharge this obligation. New Formal GO is blocked until the
mandatory proof project and its axiom audit cover all conjuncts below.

The mandatory project's `nativeArithmeticGraphUnique` now proves the graph
conjunct conditional on its explicitly parameterized codec and trust boundary.
It compares independent stores, exact bytes and complete ordered paths; it does
not assume graph/result uniqueness. This does not discharge the arithmetic or
recovery conjuncts or additional concrete decoder/refinement obligations below.
See `formal/proposals/native-graph-proof.md` for assumptions and vector scope.

`ParameterKernel.lean` additionally proves coefficient derivation, ordered
vector/prefix safety and per-coordinate conversion for mathematical input rows.
The checked extraction layer in `ArithmeticBinding.lean` now derives eligible
committed rows, validates their metadata/shape, and constructs the full typed
PARAMETER body. `nativeParameterConversionSound` now additionally proves checked
ordered whole-body aggregate comparison, per-domain conversion with INT64 output
under either accumulator width, complete schema placement and no extra cells.
This conjunct is conditional on the named codec/anchor/certificate premises;
concrete native decoder/serialization/authentication and admission refinement
remain additional mandatory obligations. Recovery remains OPEN. Scope:
`formal/proposals/parameter-kernel-proof.md` and
`formal/proposals/native-parameter-body-proof.md`, followed by
`formal/proposals/native-parameter-conversion-proof.md`.

`ApplyKernel.lean` proves checked LCM construction, ordered domain mixture,
optimizer intermediate bounds, complete vector shape and mathematical output
uniqueness from fixed input rows/model/optimizer. It does not derive those inputs
from the native graph or bind full APPLY body bytes and next-state hashes.
Consequently that helper alone does not discharge `nativeApplyResultUnique`.
The checked native bridge now derives those inputs across independently anchored
stores, constructs full typed/canonical APPLY bodies and proves result identity,
output bounds and exact hash preimages under named codec/HashAdapter/trust
premises. This discharges the conditional APPLY conjunct; recovery and concrete
native decoder/admission/WAL refinement remain OPEN. See
`formal/proposals/apply-kernel-proof.md` and `formal/proposals/native-apply-proof.md`.

`RecoveryKernel.lean` now proves checked sequential replay against an independent
history relation, complete record/order preservation, original receipt/sequence
lookup after current advancement, conflict and recovery-mode fencing, and explicit
presence/absence/unresolved scan handling. Admission, receipt encoders and scan/QC
authentication are adapter parameters. The native bridge from independently bound
PARAMETER/APPLY inputs and public witnesses is still missing; these helpers do NOT
discharge `nativeArithmeticRecoveryRefines`. See
`formal/proposals/recovery-kernel-proof.md` for exact example and assumption scope.

The native pre-WAL bridge now derives complete PARAMETER/APPLY records and exact
diagnostic command/envelope/effect/receipt bytes from the authenticated graph,
checks current pointers/role/time/readiness and rejects first-admission conflicts.
Its independent-store PARAMETER identity does not require a later aggregate.
These helpers still do not instantiate the general replay adapter or establish
initial-prefix/native exporter provenance; `nativeArithmeticRecoveryRefines`
remains OPEN. Scope: `formal/proposals/native-prewal-proof.md`.

`NativeReplay.lean` now instantiates arithmetic admission and effect/receipt
encoding from those proof-producing native inputs. Its checked sequential replay
derives a native arithmetic history, complete record retention, computed APPLY
current changes and authenticated presence/absence recovery from an empty
arithmetic journal. Effect/receipt encoding is partial and failure disables a
record. Full public trace/all-vote-prefix projection and exporter provenance are
still missing: this bridge alone does not discharge the recovery conjunct.
See `formal/proposals/native-replay-proof.md` for the exact assumptions and scope.

`PublicJournal.lean` adds the complete ordered per-actor vote-slot projection,
including intervening non-arithmetic envelopes, computed prefix roots and the
original native arithmetic sequences/receipts. It derives native preparation
for arithmetic slots and cannot admit them through its separate non-arithmetic
authorization premise. It does not prove that premise or the full public event
snapshot/exposure/QC/crash/scan lifecycle. Unprojected receipts remain absent.
The recovery conjunct stays OPEN; this journal-only relation cannot replace it.
See `formal/proposals/public-journal-proof.md` for exact scope and assumptions.

`PublicRecovery.lean` checks exact stage-list exposure, required crash/restart,
historical retry and authenticated full-prefix presence/absence scans over that
all-vote journal. Successful readiness derives actual replay/history and original
records, not assumed recovered-state equality. Unknown writes retain the last
known prefix and cannot be inferred absent; incomplete/corrupt/ambiguous scans
do not enable votes. Event/snapshot/state-root binding, other-action phase/QC
admission and production exporter/WAL remain open, so this layer still does not
discharge the full recovery conjunct. Scope: `formal/proposals/public-recovery-proof.md`.

`PublicReachability.lean` now establishes the common live-machine invariant from
empty initialization by induction on successful executable operations. It derives
exact replay/log equality, immutable initial state, original all-vote slots,
checked pending candidates, sent-slot storage and native preparation provenance.
The invariant is a conclusion, not a reachability constructor assumption. Named
scan/metadata/hash/other-action adapters retain their previous scope. Binding to
independently authenticated full public snapshots, canonical public state roots,
phase/QC/global exposure and concrete native execution remains open. This is a
sublayer, not `nativeArithmeticRecoveryRefines`. Scope:
`formal/proposals/public-reachability-proof.md`.

`PublicSnapshot.lean` adds exact existing v1 snapshot byte/preimage encoding and
checks independently resolved snapshot/anchor/metadata against the original
first arithmetic event, all-vote sequence, finalized parent and native arithmetic
record. Successful execution preserves the proved reachable journal relation.
This is not full public state-root verification: existing trace roots are opaque
and fixture roots are hashes of labels. A retained initial-root relabeling
countercheck still passes the adjacency checker. A canonical complete-state
preimage and its full action relation remain mandatory; snapshot hash identity
alone cannot discharge them. See `formal/proposals/public-snapshot-proof.md`.

The separate full-public-state candidate now encodes every one of the 64
`ProtocolVariables` and checks state identities against complete preimages.
Its generated TLC replay evaluates the production Init/TypeOK/Next and named
actions for a finite RoundConfig/persist/send/delivery/crash/recovery/QC path;
seven rehashed invalid paths are rejected. This closes neither the legacy
trace's opaque-root gap nor native exporter provenance. A second, independently
pinned two-shard configuration now checks a 132-state arithmetic path against
the production actions, retaining the 36 original event positions/times and
per-actor vote sequences 5/6/8. Its finite limit 127 is not native INT64 coverage;
legacy snapshot roots are explicitly incompatible with the new state preimages.
Native snapshot/history binding and Lean composition are still open. It is not the remaining
mandatory theorem. See `formal/proposals/public-state-projection.md`.

The separate `full-public-native.v2-candidate` checker now derives nine first-vote
correspondences from complete preimages and independently pinned native fixture
inputs. It checks original actor/time/context/sequence, exact modeled vote changes,
delivered parent-QC support, bound model/optimizer and full recomputed arithmetic
bodies/command/receipt bytes. Old v1 snapshots stay unchanged and cannot masquerade
as v2 complete-state witnesses. The source registry is explicitly synthetic; its
pins are not producer authentication. This is finite executable correspondence,
not a new Lean proof, generic admission rule or the remaining recovery theorem.
See `formal/proposals/public-native-projection.md` for the unresolved exporter,
general identity abstraction and reachable-history composition obligations.

`PublicState.lean` adds a mandatory-project complete tagged finite-value state,
canonical document/preimage loader and checked first arithmetic envelope
extraction. General helpers retain all 64 fields and derive original actor,
parent, fresh context and all-vote sequence. A separately supplied native
identity map binds selected original metadata; it is not native authentication.
Source-linked full-state kernel cases use an explicitly synthetic zero semantic
ID to avoid hashing the generated Lean source into its own literals. Neither
typed loading nor extraction proves all after-state effects or production Next;
a kernel countercheck demonstrates that extraction alone accepts a changed
message set. Byte decoding, the full native graph/body/QC/history connection and
the remaining recovery theorem stay open. See
`formal/proposals/public-state-lean-proof.md` for exact assumptions and scope.

`PublicVoteEffects.lean` derives the four complete first-vote assignments and
preserves the other sixty state fields. The composed checker rejects the prior
message mutation and hidden current/other-actor sequence changes. Kernel examples
reuse all nine original arithmetic votes and three loaded full-state pairs.
This closes the effect-footprint gap, not the full action guards, native
preparation/history composition or `nativeArithmeticRecoveryRefines`.
Scope: `formal/proposals/public-vote-effects-proof.md`.

- An independently authenticated native anchor and canonical typed byte graph
  determine exactly one parameter schema, eligible ordered contribution set,
  domain/shard placement, profile, current model and current optimizer. Hash
  collision resistance, certificate authentication and durable-anchor recovery
  must be named assumptions rather than claims proved by a byte equality check.
- For every allowed width and vector length, each coefficient/product/prefix,
  quantum conversion and ordered rounding step agrees with the frozen PARAMETER
  semantics. Exact coverage and metadata prevent subset or fraction aliases.
- The per-domain conversion, mixture and optimizer operations determine unique
  expected APPLY/model/optimizer bytes, including full signed output bounds.
  Recomputed equality must cover the whole body, not just self-consistent hashes.
- Public trace vote admission and recovered native state refine the same binding
  relation before WAL persistence. Missing/mismatched authority disables admission;
  exact persisted replay preserves the original bytes, effect and sequence.

**Lean artifact target**: `formal/proofs/DeltaReduce/ArithmeticBinding.lean`.
The concrete decoder/refinement and source-linked vector checks are additional
obligations; an abstract pure-function determinism lemma alone is insufficient.

## PO-Q1 — Quorum intersection

**Statement**

Let `V` be a finite validator set with `|V| = 3f + 1`. If `Q1,Q2 ⊆ V`, `|Q1| ≥ 2f+1` and `|Q2| ≥ 2f+1`, then:

`|Q1 ∩ Q2| ≥ f+1`.

**Corollary**

If at most `f` validators are Byzantine, `Q1 ∩ Q2` contains at least one honest validator.

**Used by**: config/ISC/EC/APC/shard/AggregateRoot/Apply/ViewChange/Abort QC uniqueness.

**Lean artifact target**: `formal/proofs/DeltaReduce/Quorum.lean`.

## PO-Q2 — Conflicting QC impossibility

**Assumptions**

- PO-Q1;
- an honest validator emits at most one durable vote body per vote context;
- a QC contains at least `2f+1` unique valid signers from the same epoch/context.

**Statement**

Two QCs with different body hashes cannot both exist for the same vote context.

**Used by**: all certificate uniqueness invariants and split-brain prevention.

**Artifact**: `Quorum.lean` plus TLA trace correspondence for durable vote context.

## PO-A1 — Signed product bound

For integers `a,q`, if `|a|≤A` and `|q|≤Q`, then `|a*q|≤A*Q`. The proof MUST track the selected intermediate width independently from the final sum width.

**Artifact**: `formal/proofs/DeltaReduce/FixedPoint.lean`.

## PO-A2 — Flat accumulator safety

For a finite index set `J` with `|J|≤Nmax`, integer vectors/coordinates `q_j` and coefficients `a_j` satisfying `|q_j|≤Q`, `|a_j|≤A`, prove:

`|Σ_{j∈J} a_j*q_j| ≤ Nmax*A*Q`.

If `Nmax*A*Q ≤ M`, the final sum fits the signed accumulator bound `[-M,M]`.

The implementation profile MUST additionally prove/check that each intermediate multiplication and incremental sum fits its declared width under canonical ordering.

## PO-A3 — Rational/common-denominator safety

For each rational input, prove separately that its denominator is positive and
that `gcd(|n_j|, d_j)=1`. Prove that the constructed common denominator is
positive and divisible by every `d_j`, and that integer numerator accumulation
is safe under the configured bound.

Final integer conversion follows ADR-0002: Euclidean quotient/remainder,
strictly-below-half rounds to the quotient, at-or-above-half rounds to quotient
plus one, and an exact half tie resolves toward positive infinity. Each branch,
the tie rule and determinism MUST be represented by a named checked theorem;
denominator zero or a noncanonical input fraction is not an admissible runtime
precondition.

**Used by**: APC weights, domain mixture and ApplyArithmeticProfile.

## PO-A4 — Ordered checked arithmetic and asymmetric signed bounds

For any ordered list of integer `(coefficient, value)` pairs, initial accumulator
and independent product/accumulator intervals, the checked fold accepts exactly
when each product and each accumulator prefix (including the initial and final
values) fits its declared interval. Acceptance yields the exact mathematical
integer fold. This is parametric in list length, values and asymmetric bounds;
it does not assume that a safe final value makes intermediate values safe.

For rational-to-domain conversion, acceptance requires positive denominator and
quantum components, and every product in `((N*u)*y) / ((L*v)*x)` must fit before
rounding. The accepted result equals the specified Euclidean rounding and fits
the signed output interval. The `r < d-r` comparison must agree with `2*r < d`
over mathematical integers without requiring machine evaluation of `2*r`.

Named kernel-checked counterexamples cover unsafe products/prefixes hidden by a
safe final sum, independent product widths, cancellation around an overflowing
conversion product, signed half ties, exact `INT64_MIN`, and moving per-domain
rounding across mixture. All are mandatory axiom-audited conjuncts.

**Artifact**: `formal/proofs/DeltaReduce/ArithmeticKernel.lean`.

**Scope**: this integer operation graph does not establish input coefficient
derivation, reduced fractions, canonical artifact decoding, native-state binding,
the complete optimizer, or recovery. PO-AB1 still requires that concrete native
admission refines these operations and satisfies all its other conjuncts.

## PO-H1 — Exact partition

Let regional ticket sets `R_1 ... R_k` be pairwise disjoint and have union `J`. Prove each ticket belongs to exactly one region and every required ticket is covered.

**Artifact**: `formal/proofs/DeltaReduce/Hierarchy.lean`.

## PO-H2 — Hierarchical equals flat

Under PO-H1 and exact integer arithmetic:

`Σ_r (Σ_{j∈R_r} a_j*q_j) = Σ_{j∈J} a_j*q_j`.

The theorem MUST be indexed by domain and parameter shard and extend to exact ticket count, coefficient sum and denominator metadata.

**Failure boundary**: overlap or missing membership invalidates the theorem precondition; the protocol must reject topology/assembly rather than invoke the result.

## PO-C1 — Canonical aggregate coverage

Given a finite required key set `K = Domains × Shards` and a leaf table with exactly one entry per key, prove key uniqueness/completeness and canonical sort uniqueness. Merkle-root uniqueness is conditional on the named injective/collision-resistant hash abstraction.

**Artifact**: `formal/proofs/DeltaReduce/Coverage.lean`.

## PO-AP1 — Apply vote uniqueness

Instantiate PO-Q2 for the apply vote context containing `(height, parent, AggregateRootQC, RoundConfig, ApplyProfile)`. Conclude at most one body `(nextModelHash,nextOptimizerHash,...)` can obtain ApplyQC.

**Artifact**: `formal/proofs/DeltaReduce/Apply.lean`.

## PO-AP2 — Current-state uniqueness

Assume:

- PO-AP1;
- `AdvanceCurrent` accepts only a valid ApplyQC whose parent equals the current pointer or exact idempotent replay;
- compare-and-set is atomic in the abstract state machine.

Prove at most one next current checkpoint exists per height and replay cannot apply twice.

The checked theorem set MUST separately cover ApplyQC uniqueness from quorum
intersection, uniqueness of the resulting current state, accepted compare-and-set
advance and exact replay idempotence.

TLA+ checks crash/interleaving behavior; Lean proves the abstract transition relation result.

## PO-D1 — Domain mixture preservation

Let per-domain certified aggregates `g_d` and immutable coefficients `pi_d` be fixed by RoundConfig/ApplyProfile. Prove `g = Σ_d pi_d*g_d` depends only on these values, not worker identity, lease owner, throughput, completion time or message order.

**Artifact**: `Apply.lean`.

## PO-R1 — Abort preserves current

For the abstract state transition relation, prove every `HardAbort` transition leaves `currentCheckpoint` unchanged and no non-ApplyQC action changes it.

**Artifact**: TLA invariant plus optional Lean transition theorem in `Apply.lean`.

## PO-R2 — Recovery idempotence

For idempotent replay keys and durable vote/current transition records, prove
applying the same recovery command zero, one or multiple times yields
observationally equivalent certified state. The checked theorem set MUST
separately prove restoration of the durable vote journal, certificates and
current checkpoint, full recovered-state observational equivalence and
restart/recovery idempotence. Finite crash placements remain a TLC obligation.

## Proof dependency graph

```text
PO-Q1 → PO-Q2 → PO-AP1 → PO-AP2
PO-A1 → PO-A2 → PO-A3
PO-H1 + PO-A2 → PO-H2
PO-C1 → AggregateRoot completeness abstraction
PO-A3 + PO-C1 → deterministic Apply input
PO-AP2 + PO-R1 → current checkpoint safety
```

## Required proof metadata

Each theorem artifact MUST record:

- theorem/proof ID and source location;
- exact statement and assumptions;
- imported lemmas/axioms;
- prover/compiler/toolchain hash;
- build result;
- owning feature(s);
- concrete runtime/config checks required to establish theorem preconditions.

The evidence generator MUST maintain an explicit proof-obligation-to-normative-
conjunct table. A parent proof obligation passes only when every listed conjunct
has a named theorem, a successful kernel/axiom audit entry and no admitted
placeholder. Counting one weak theorem per parent ID is insufficient.

## Runtime precondition rule

A theorem does not make a runtime configuration safe by itself. The implementation MUST validate and content-address the concrete preconditions—validator-set size, unique signers, q/weight/count bounds, exact partition, complete coverage and parent context—before using the theorem-backed transition.
