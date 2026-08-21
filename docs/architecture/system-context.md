# DeltaTorrent system context

## Source-derived architecture

The concept memo in `docs/source/deltatorrent-concept.ru.md` defines the core direction:

- workers perform many local optimizer steps against independent data;
- each worker emits one pseudo-gradient relative to a named parent model;
- updates are reduced hierarchically and weighted by processed tokens;
- a global aggregated delta is split into immutable shards and distributed P2P;
- local-step duration, compression, regional hierarchy and bounded staleness amortize WAN cost;
- primary practical targets are a 100–300M full-training prototype and LoRA/QLoRA for 8 GB GPUs.

## Project decisions introduced by this specification set

These are implementation choices rather than claims from the concept memo:

- typed Python 3.12 and PyTorch form the reference codebase;
- control-plane contracts are transport-independent with a gRPC reference adapter;
- tensor artifacts use safe canonical formats, never pickle across trust boundaries;
- the first P2P version uses coordinator-assisted discovery and peer exchange; DHT is deferred;
- the first security model is permissioned;
- feature branches are stacked and pass independent exit gates.

## Logical components

```text
Dataset/model CAS
      │
      ▼
Round coordinator ── assignments ──▶ Worker round engine
      ▲                                  │
      │          local update shards     │
      └──────── Regional reduce ◀────────┘
                     │
                     ▼
             Global publisher
                     │
          signed immutable manifest
                     │
                     ▼
             P2P distribution swarm
```

## Round state machine

```text
CREATED → OPEN → SEALED → AGGREGATING → PUBLISHED
    └────────────────────────────────────→ ABORTED
```

A published round is immutable. A worker update is accepted at most once for one round and one parent model hash.

## Dependency direction

- `domain` has no transport, storage or deployment dependencies.
- `training`, `compression`, `reduce` and `scheduling` implement mathematical/domain interfaces.
- `worker`, `coordinator` and `distribution` orchestrate through ports.
- `adapters` contain gRPC, filesystem CAS, network emulation, accelerator and deployment integrations.
- `cli` composes adapters and contains no business logic.

Architecture tests must reject any path that sends a worker-local update into the global P2P publisher.
