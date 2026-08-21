# Implementation Plan: Центральный синхронный round coordinator

**Branch**: `003-central-round-coordinator` | **Date**: 2026-08-21 | **Spec**: `spec.md`

## Summary

Построить authoritative coordinator как application service поверх чистых domain contracts. Сначала реализуются state machine, assignment allocator, receipts и repository CAS; затем canonical FP32 reducer и outer Nesterov; после этого atomic publisher/recovery. gRPC является адаптером того же API и тестируется только на loopback до появления identity plane.

## Technical Context

- Python 3.12/PyTorch stack предыдущих features.
- Persistence reference: transactional filesystem journal/repository; интерфейс допускает SQL/consensus backend позднее.
- RPC: protobuf/gRPC, versioned package `deltatorrent.coordinator.v1`.
- Tensor transport: artifact refs или bounded streaming safe bytes; never pickle.
- Numerical reduce: canonical update ordering, FP32 accumulator, optional compensated-sum helper evaluated by tests.
- Concurrency: optimistic version/CAS на `RoundRecord`; one writer transaction for publish.
- Time: injected monotonic clock для policy, UTC timestamps для evidence.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Scientific correctness | Exact token-weighted math и explicit outer formula | Direct-reference tests |
| Reduce/distribution split | Intake/reducer не экспортируют local updates в distribution API | Architecture tests |
| Versioned state | Parent, set, delta, optimizer и result content-addressed | Lineage verification |
| WAN realism | RPC retries/deadlines моделируются offline; performance позже | Fault-injected loopback suite |
| Bounded coordination | Soft/hard deadlines и abort semantics | Deadline tests |
| Permissioned default | Пока loopback-only insecure adapter; внешний bind запрещён | Bind-policy test |
| Reversible increment | Central sync baseline, journal recovery, immutable publication | Crash matrix |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
CLI/gRPC adapter
      │
      ▼
CoordinatorApplication
  ├─ RoundService ───────────▶ RoundRepository (CAS/journal)
  ├─ AssignmentAllocator ────▶ DatasetManifest
  ├─ UpdateIntake ───────────▶ LocalUpdateValidator/ArtifactStore
  ├─ RoundSealer ────────────▶ AcceptedUpdateSet
  ├─ FP32Reducer ────────────▶ GlobalDelta
  ├─ OuterOptimizer ─────────▶ New model + outer state
  └─ AtomicPublisher ────────▶ RoundResultManifest/current pointer
```

Mutating commands используют command ID и expected record version. Publication transaction воспроизводима: artifact content может быть записан повторно, но current pointer меняется один раз по expected parent.

## Project Structure

```text
src/deltatorrent/
  domain/
    rounds.py
    receipts.py
    optimizer.py
  coordinator/
    service.py
    assignments.py
    intake.py
    sealing.py
    reducer.py
    outer_optimizer.py
    publisher.py
    recovery.py
    repository.py
  adapters/grpc/
    coordinator_server.py
    coordinator_client.py
  cli/coordinator.py
proto/deltatorrent/coordinator/v1/coordinator.proto
tests/
  unit/test_round_state_machine.py
  unit/test_weighted_reduce.py
  unit/test_outer_optimizer.py
  contract/test_coordinator_proto.py
  integration/test_central_round.py
  integration/test_coordinator_recovery.py
  integration/test_grpc_retry_semantics.py
configs/coordinator/
docs/round-protocol.md
```

## Implementation Sequence

1. Утвердить protobuf-neutral domain schemas, state transitions и receipt taxonomy.
2. Реализовать durable repository с CAS и exhaustive state-machine tests.
3. Реализовать deterministic assignment allocation и update intake validation.
4. Реализовать sealing policy и immutable accepted-set hash.
5. Реализовать token-weighted reducer и explicit Nesterov state transition.
6. Реализовать two-phase artifact/current-pointer publisher и restart recovery.
7. Добавить application API, CLI и loopback gRPC adapter.
8. Провести permutation, retry, deadline и injected-crash integration suites.

## Test Strategy

- **State/model-based**: разрешённые/запрещённые transitions и concurrent CAS conflicts.
- **Numerical**: scalar/tensor reference cases, heterogeneous token weights, extreme norms, arrival permutations.
- **Contract**: protobuf golden descriptors/messages, backward-read policy, stable receipt/error codes.
- **Integration**: 4+ in-process workers, loopback gRPC, duplicate/conflicting retry, late update, abort.
- **Recovery**: crash before/after each journal/artifact/pointer boundary.
- **Architecture**: coordinator domain не импортирует gRPC/filesystem; distribution plane не принимает local update.

## Observability

Round gauges/counters: state, assigned/accepted/rejected/late workers, assigned/accepted tokens. Histograms: assignment wait, local duration as reported, intake validation, seal wait, reduce, publish. Events contain IDs/hashes/reasons, но не tensor payload или секреты.

## Rollout and Rollback

Rollout начинается in-process, затем loopback gRPC в development profile. Non-loopback bind требует explicit unsafe flag до feature `008`. Rollback останавливает coordinator, оставляет immutable artifacts и восстанавливает current pointer на последний fully published parent; schema IDs не переиспользуются.

## Risks and Mitigations

- **Double apply после crash**: current-pointer CAS по parent/result, deterministic outer result hash.
- **Arrival-order drift**: canonical sort и fixed accumulator contract.
- **Average-of-averages bug**: reducer принимает weighted numerators/token denominator, тесты с неравными weights.
- **Deadline race**: monotonic timestamp captured в CAS transition; receipt классифицируется по committed seal boundary.
- **Premature external exposure**: loopback default и explicit bind guard.

## Exit Gate

- State machine, weighted reduce и outer optimizer reference suites проходят.
- End-to-end 4-worker round, abort и retry tests зелёные.
- Crash matrix доказывает отсутствие double application.
- Proto compatibility и loopback bind policy проходят.
- Quality gates, evidence и final Constitution Check завершены.
