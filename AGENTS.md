# Agent execution contract

## Required reading order

Before changing code, read:

1. `.specify/memory/constitution.md`;
2. `specs/ROADMAP.md`;
3. `docs/adr/0001-deltareduce-v1.md`;
4. the current branch's `spec.md`;
5. the current branch's `plan.md`;
6. the current branch's `tasks.md`.

The current authoritative branch is the implementation boundary. Do not implement later branches opportunistically and do not base work on a superseded legacy ref.

## Branch discipline

- Feature branches are stacked in numeric order as declared in `specs/ROADMAP.md`.
- A branch may rely only on `main` and its declared predecessor.
- Each implementation commit references one or more task IDs.
- Mark a task `[x]` only after its tests and acceptance evidence pass.
- A deliberate protocol change requires an ADR and updates to every affected spec, plan, task list, fixture and compatibility contract.

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

## Quality gates

```text
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

Additional mandatory gates:

- deterministic serialization golden fixtures;
- state-machine transition and quorum-intersection tests;
- fixed-point overflow proofs and boundary vectors;
- bit-for-bit equality across independent aggregator processes;
- no-seed-before-input-freeze property tests;
- mixed-view/Frankenstein aggregate rejection;
- ApplyQC uniqueness and restart/replay tests.

Network tests must be deterministic, timeout-bounded and runnable without public internet. GPU-only tests require a CPU or mocked smoke path. Scientific comparisons use the same token budget, domain ticket counts, seeds, data manifest and evaluation protocol.

## Evidence

Performance, quality, BFT tolerance and 8 GB claims require machine-readable run manifests and measured evidence. Targets must not be presented as achieved results before their designated benchmark or pilot gate passes.
