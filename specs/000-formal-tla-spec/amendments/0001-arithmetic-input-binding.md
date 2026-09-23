# Candidate amendment 0001: native arithmetic input binding

Status: `DRAFT_NOT_AUTHORITY`. Formal impact: `SEMANTIC`. This document is a
concrete candidate for T029, T031, T044, T047 and T053–T066, not a completed task
or Formal GO. The merged `cc98f15a...` report remains authority only for its
unchanged artifact set. This draft does not authorize removal of PR50's arithmetic
input guard or a qualifying benchmark in either deployment mode.

Candidate progress is tracked in `docs/feature010-progress.md`. Initial production
TLA+ integration, a concrete draft byte-graph oracle, C++ arithmetic comparison
and standalone Lean helpers now exist. They do not complete the obligations below.

## Observed gap

At main `c8aea64972f741060d1e527ebbb6f9a5a168a075`,
`formal/tla/DeltaReduceReduceApply.tla` validates parameter arithmetic against
`ExpectedParameterValue` and Apply against `ExpectedNextModelHash` and
`ExpectedNextOptimizerHash`. Those constants abstract an expected result; they
do not define recovery of that result from canonical native input artifacts.
`formal/scripts/check-refinement.py` checks parent/context/coverage but has no
arithmetic artifact witness on `ACT-PARAM-VOTE` or `ACT-APPLY-VOTE`.

PR50 `60c692f6e391f839829dfc64e93380db54cd507b`, inherited by recovery candidate
`e94fb08ad75d0693d566f1761cac8cc992bb4e42`, therefore rejects PARAMETER and APPLY
in `delta-core-cpp/src/certificates/vote_admission.cpp` before durability. Removing
that rejection based solely on self-consistent caller-supplied result hashes
would admit unverified arithmetic.

## Authority graph

Native durable round state must hold the exact authority root, independent of the
vote command. The command cannot select another authority root, current state,
arithmetic profile, context or sequence. That root binds:

- certified RoundConfig, height, view, epoch, parent checkpoint and committee role;
- parameter schema (including QLoRA frozen-base/schema identity where applicable),
  complete domain×shard assignment, parameter offsets and lengths;
- ISC/EC/APC canonical bytes and IDs, ordered eligible ticket/commitment/AC leaves,
  verified q-shard payloads, per-shard quantum and common-denominator proof;
- current model artifact bytes/ID and current optimizer artifact bytes/ID;
- current model and optimizer value hashes and their schema/order;
- domain mixture, apply quantum, checked intermediate/output widths, rounding,
  momentum, learning rate, decay and Nesterov profile.

Every artifact is read by its expected ID, length and type, then its exact
canonical bytes are hashed again. An ID plus caller-provided matching metadata is
insufficient. Native recovery revalidates this graph before enabling votes.
Java carries opaque canonical bytes and cannot fill missing graph nodes.

## Candidate PARAMETER computation

For one required `(domain, shard)` key, let `J` be the exact ordered eligible
ticket set selected by the certified ISC/EC/APC. Its q-shards must match the
commitment/AC leaf, ticket/domain, schema, range, scale and profile. No observed
subset may define `J`.

Each weight is a reduced non-negative fraction `a_j/b_j`, `b_j > 0`. Let `L` be
the **specific** common denominator bound by the accumulator proof. Check that
every `b_j` divides `L`; do not choose another common multiple at admission.
In ticket-ID order, for each coordinate compute:

```text
c_j = checked(a_j * (L / b_j))
N[k] = checked_sum_j(checked(c_j * q_j[k]))
```

Every product and prefix sum must fit the frozen signed accumulator width, as
must the coefficient sum/count metadata. The expected PARAMETER body binds
exact parents, leaf IDs, domain/shard and `(N, L)` including all metadata.
Do not reduce `(N, L)` after the sum: `L` is already a uniquely bound plan value.
Equivalent fractions with different canonical bytes conflict in the same formal
uniqueness context; they are not retries.

## Candidate rational QC to domain vector conversion

Verify AggregateRootQC and exactly one ParameterShardQC per required key before
conversion. Each QC's canonical numerators/denominator must equal the native
PARAMETER computation. Place values by the immutable schema offsets, never by
arrival order or only the leaves that appeared.

Let q quantum be `u/v` and apply/model/optimizer quantum be `x/y`, all positive
and reduced. For each certified coordinate, in the shown checked operation order:

```text
p = checked(checked(N[k] * u) * y)
d = checked(checked(L * v) * x)
G_domain[k] = R(p, d)
```

`R(n,d)` uses Euclidean `n = q*d + r`, `0 <= r < d`: return `q` if
`r < d-r`, otherwise `q+1`. It therefore rounds half toward positive infinity
without overflowing `2*r`. Bounds apply to the indicated products even if an
alternative algebraic cancellation could fit. Conversion rounds **once per
domain coordinate before domain mixture**. It cannot be moved across mixture,
clipping or optimizer operations. For example, rounding domain values `1/2`
and `-1/2` before equal mixture yields `R((1+0)/2)=1`; mixing the exact
rationals first yields `R(0)=0`. The two choices are distinct semantics.

The executable proposal oracle covers unit and non-unit quantum cases. Binding
that ratio to canonical artifact bytes and discharging its width/proof instances
remain mandatory integration work; the ratio must not be inferred from a tensor
dtype or framework layout.

## Candidate APPLY computation

First reconstruct and verify current model and momentum vectors from native-bound
artifacts. Recompute their hashes and compare against the current state, not
merely the hashes named by the candidate. Their lengths/order must equal schema.

Preserve the existing engine's explicit rounding placement for this candidate:

```text
g[k]     = R(sum_domain pi_num * G_domain[k] * (P / pi_den), P)
m'[k]    = checked(R(mu_num * m[k], mu_den) + g[k])
dir[k]   = checked(R(mu_num * m'[k], mu_den) + g[k])
decay[k] = R(wd_num * theta[k], wd_den)
step[k]  = R(lr_num * checked(dir[k] + decay[k]), lr_den)
theta'[k] = checked(theta[k] - step[k])
```

Here `P` is the canonical least common multiple of the immutable domain-weight
denominators; domain weights sum exactly to one. Every operation is integer,
ordered and checked. The existing domain-separated model/optimizer value hash
encoding (`deltareduce.008.model.v1` / `deltareduce.008.optimizer.v1`, NUL, canonical
decimal coordinates each followed by `;`) is reproduced by the oracle.
The candidate hash additionally binds the full parent/context/profile/aggregate
tuple. Hash abstraction does not replace canonical artifact decoding.

## Vote preconditions and failure

`ACT-PARAM-VOTE` and `ACT-APPLY-VOTE` must independently require complete native
authority, exact current context/role/deadline/recovery readiness and exact
canonical equality with the recomputed expected body **before WAL append**.

Candidate creation is not a lease on the current checkpoint. Both vote actions
must compare `body.parent` with the recovered native `currentCheckpoint` again
at the persist boundary. After an ApplyQC advances current, a delayed first vote
for the old parent is disabled, including after crash/restart/journal recovery.
Historical durable votes and exact persisted retry receipts remain valid history;
this rule does not delete them or allocate a new sequence for a retry. A failed
current-parent check stutters/rejects without a new receipt, vote or terminal.

The focused `DeltaReduceCurrentBindingHarness` starts with certified Phase 6
parents, executes production 3-of-4 PARAMETER/AGGREGATE/APPLY quorums and advances
current, then probes the fourth validator. Separate configurations probe before
and after recovery; production guard-removal mutants must fail in both. This
serialized suffix does not establish arbitrary interleavings, heterogeneous
arithmetic, public arithmetic-witness refinement or complete crash-cut coverage.

Missing bytes, a wrong artifact/schema/scale/domain/profile/current optimizer,
unsafe bound, arithmetic overflow or result mismatch disables the vote. It maps
to the existing rejection/stutter boundary: no new durable vote, sendable effect,
receipt, current pointer or terminal result. Repair can restore only the exact
missing artifact. Existing logical deadline and certified-abort rules still apply.
No local mismatch fabricates AbortQC or terminal ABORTED.

Retry handling first authenticates the formal uniqueness context and canonical
request. Exact retry returns the same durable receipt/effect bytes/sequence. Any
different bytes for that same context conflict before a new append. Recovery
must reproduce these identities under the same authority graph. FFM/sidecar and
inline/SHM cannot alter this rule.

## Required closure before implementation

1. Integrate the authority graph and expected-result functions into production
   TLA+ actions and invariants, not a detached toy model. Include stale parent
   model/optimizer and hash/bytes/context substitutions at persist/restart cuts.
2. Extend the trace schema/refinement checker with independently resolved native
   authority/artifact witnesses on both vote actions. Regenerate legal/illegal
   traces and cross-language canonical vectors under the new schema/semantics ID.
3. Instantiate existing rounding, accumulator, hierarchy and Apply proofs for
   conversion products, output range, coverage, serialization and recovery.
   The candidate selects `FULL_SIGNED_INT64`, including exact `INT64_MIN / 1`;
   the existing Apply implementation rejects that case. This difference must be
   represented in the new authority before runtime changes, with no silent
   precondition widening under the historical report.
4. Add production-source mutants for omitted recomputation, wrong rounding
   placement, substituted parent model/optimizer, swapped domains/shards,
   mismatched scale/profile, and arithmetic-result changes with rehashed bodies.
5. Run the complete pinned parser/TLC/liveness/Lean/mutant/refinement/compatibility
   and clean-reproduction gate. Publish an honestly scoped self-review; do not
   manufacture independent reviewer attestations.
6. Obtain the required formal review decision, derive the new semantics hash,
   produce/verify a new FormalVerificationReport and merge the exact authority.
   Only then update native runtime and recover PR50's best source.

The current proposal oracle and its tests are design evidence only. They do not
discharge items 1–6, satisfy native/cross-language conformance, or establish GO.
