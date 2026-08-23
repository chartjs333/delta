# Agent execution contract

## Required reading order

Before changing any implementation or protocol artifact, read:

1. `.specify/memory/constitution.md`;
2. `docs/adr/0000-formal-verification-gate.md`;
3. `docs/adr/0001-deltareduce-v1.md`;
4. `specs/ROADMAP.md`;
5. `specs/000-formal-tla-spec/failure-semantics.md` and `proof-obligations.md` when present in the current stacked branch;
6. the current branch's `spec.md`;
7. the current branch's `plan.md`;
8. the current branch's `tasks.md`.

The current authoritative branch is the implementation boundary. Do not implement later branches opportunistically and do not base work on a superseded legacy ref.

## Formal-first STOP rule

- `000-formal-tla-spec` is the only branch allowed to begin without a prior Formal GO.
- No implementation task in `001–011` may start until the exact compatible `FormalVerificationReport(decision=GO)` has been verified.
- Any change to state transitions, vote/QC semantics, deadlines, failure/recovery, availability, certificate parentage, fixed-point bounds, hierarchical composition or Apply current-state behavior MUST update the TLA+/proof artifacts first and rerun the affected formal gate.
- A failed invariant, liveness assumption, theorem, counterexample regression or refinement check is an unconditional STOP. Tests or operational work in a later branch cannot waive it.
- TLC finite-state success is not a substitute for parametric arithmetic/quorum proofs; theorem-prover success is not a substitute for failure/interleaving model checking. Both are required where declared.

## Branch discipline

- Feature branches are stacked in numeric order as declared in `specs/ROADMAP.md`.
- A branch may rely only on `main` and its declared predecessor.
- Each implementation commit references one or more task IDs.
- Mark a task `[x]` only after its tests and acceptance evidence pass.
- A deliberate protocol change requires an ADR and updates to every affected spec, formal model, proof, task list, fixture, compatibility contract and traceability entry.

## DeltaReduce v1 non-negotiable invariants

- There is no single authoritative round coordinator; consensus state is replicated across `3f+1` validators.
- A finalized certificate or state transition requires at least `2f+1` valid votes from the configured validator set.
- Every work ticket is domain-pure and fixes `domain_id`, `B`, `H`, parent checkpoint, parameter schema and arithmetic profile.
- Adaptive `H_i`, device-speed weighting, stale-update weighting and post-open mutation of ticket budgets are forbidden.
- Workers normalize by the effective optimizer-step count `A_j` before quantization.
- Consensus reduction uses canonical integer fixed-point arithmetic only. FP16/BF16/FP32/FP64 addition is forbidden in parameter reduce and certified clipping/weight application.
- The round must prove accumulator headroom before ticketing opens; saturation, wraparound and platform-dependent overflow behavior are forbidden.
- The exact input tuple set `{T_j, C_j, AC_j}` is frozen before seed `ρ_t` exists.
- `InputSetCertificate → EligibilityCertificate/AggregationPlanCertificate → ParameterShardQC → AggregateRootQC → ApplyQC` lineage is immutable and context-bound.
- A model/checkpoint becomes current only through one valid `ApplyQC` for its parent `AggregateRootQC`.
- Keep reduce and distribution planes separate. Never P2P-broadcast worker-local shards, commitments or regional partials.
- Every model, dataset shard, ticket, commitment, availability proof, certificate, delta shard and manifest is versioned, canonically serialized and content-addressed.
- Reject wrong-parent/schema/config/domain, duplicate ticket commitment, unavailable data, mixed-view shard roots, replayed votes and unsafe serialization before semantic use.
- Never use Python pickle for data received from another process or machine.
- Permissioned validator/worker identities are mandatory through the pilot.

## Failure and recovery contract

- Loss of proposer or signatures triggers deterministic view/leader change while the soft deadline permits it; failure to obtain quorum by the hard deadline yields certified abort, never arrival-order fallback.
- A commitment lacking `AC_j` may be omitted only before ISC according to the frozen close policy. After ISC, loss of required shard availability triggers repair/retrieval attempts and then round abort if bytes cannot be recovered; the input set cannot be rewritten.
- Restarted validators recover their durable vote journal before processing new proposals and cannot sign a conflicting body for the same context.
- Network partitions preserve safety. Liveness is claimed only under the exact eventual-synchrony and honest-quorum assumptions in the formal model.
- Apply failure or insufficient quorum preserves the parent current checkpoint. Existing ApplyQC can be replayed to repair the pointer idempotently.

## Quality gates

```text
# Formal branch / formal-impact changes
make formal-check

# Python implementation branches
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

Mandatory formal gates include:

- TLA+ syntax and TLC safety models;
- liveness checks under declared fairness/availability assumptions;
- theorem-prover builds for parametric quorum, fixed-point, hierarchy and apply claims;
- expected counterexamples for intentionally weakened mutants;
- implementation-trace projection/refinement checks for code-bearing protocol branches.

Additional implementation gates include deterministic serialization fixtures, bit-for-bit independent aggregation, seed-after-ISC properties, Frankenstein rejection, ApplyQC uniqueness and restart/replay tests.

Network tests must be deterministic, timeout-bounded and runnable without public internet. GPU-only tests require a CPU or mocked smoke path. Scientific comparisons use the same token budget, domain ticket counts, seeds, data manifest and evaluation protocol.

## Evidence

Formal, performance, quality, BFT tolerance and 8 GB claims require content-addressed machine-readable manifests and measured/proved evidence. Targets and unexecuted proof obligations must not be presented as achieved results.
