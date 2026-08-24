# DeltaReduce v1 Parametric Proof Obligations

**Status**: Normative theorem plan  
**Reference prover**: Lean 4 (an equivalent machine-checked system requires an ADR)

TLC explores finite behaviors. The obligations below cover claims parameterized by `f`, ticket counts, integer bounds and partitions. Mandatory proofs MUST compile without `sorry`, unreviewed axioms or hidden classical/choice assumptions beyond those explicitly listed.

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

For coefficients represented as reduced rationals `n_j / D` with common positive denominator `D`, prove that integer numerator accumulation is safe under the configured bound and that final canonical reduction/rounding is deterministic. Denominator zero and noncanonical fractions are excluded by preconditions.

**Used by**: APC weights, domain mixture and ApplyArithmeticProfile.

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

TLA+ checks crash/interleaving behavior; Lean proves the abstract transition relation result.

## PO-D1 — Domain mixture preservation

Let per-domain certified aggregates `g_d` and immutable coefficients `pi_d` be fixed by RoundConfig/ApplyProfile. Prove `g = Σ_d pi_d*g_d` depends only on these values, not worker identity, lease owner, throughput, completion time or message order.

**Artifact**: `Apply.lean`.

## PO-R1 — Abort preserves current

For the abstract state transition relation, prove every `HardAbort` transition leaves `currentCheckpoint` unchanged and no non-ApplyQC action changes it.

**Artifact**: TLA invariant plus optional Lean transition theorem in `Apply.lean`.

## PO-R2 — Recovery idempotence

For idempotent replay keys and durable vote/current transition records, prove applying the same recovery command zero, one or multiple times yields observationally equivalent certified state. Finite crash placements are explored by TLC; algebraic/idempotent state-update lemmas are proved where practical.

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

## Runtime precondition rule

A theorem does not make a runtime configuration safe by itself. The implementation MUST validate and content-address the concrete preconditions—validator-set size, unique signers, q/weight/count bounds, exact partition, complete coverage and parent context—before using the theorem-backed transition.
