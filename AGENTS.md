# Agent execution contract

## Required reading order

Before changing code, read:

1. `.specify/memory/constitution.md`;
2. `specs/ROADMAP.md`;
3. the current branch's `spec.md`;
4. the current branch's `plan.md`;
5. the current branch's `tasks.md`.

The current branch is the implementation boundary. Do not implement later branches opportunistically.

## Branch discipline

- Feature branches are stacked in numeric order.
- A branch may rely only on `main` and its declared predecessor.
- Each implementation commit references one or more task IDs.
- Mark a task `[x]` only after its tests and acceptance evidence pass.
- A deliberate contract change requires an ADR and updates to all affected artifacts.

## Non-negotiable invariants

- Keep reduce and distribution planes separate.
- Never torrent-broadcast unaggregated worker updates.
- Every model, dataset shard, delta shard and manifest is versioned and content-addressed.
- Aggregate decoded updates in FP32 unless a later approved specification changes the accumulator contract.
- Count contribution weight from verified processed tokens, not node count.
- Reject non-finite tensors, parent/schema mismatches, replayed updates and unsafe serialization.
- Never use Python pickle for data received from another process or machine.
- Permissioned identity is the default through the pilot.

## Quality gates

```text
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

Network tests must be deterministic, timeout-bounded and runnable without public internet. GPU-only tests require a CPU or mocked smoke path and an explicit marker. Scientific comparisons use the same token budget, seeds, data manifest and evaluation protocol.

## Evidence

Performance and quality claims require machine-readable run manifests and measured evidence. Targets must not be presented as achieved results before the benchmark phase produces them.
