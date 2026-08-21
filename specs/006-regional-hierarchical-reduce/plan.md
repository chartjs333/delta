# Implementation Plan: Региональная и шардированная иерархическая редукция

**Branch**: `006-regional-hierarchical-reduce` | **Date**: 2026-08-21 | **Spec**: `spec.md`

## Summary

Расширить coordinator decomposition отдельными topology, regional sealing, numerator-reducer и global-assembly services. Schema-driven shard plan создаётся до round open. Каждый регион получает один accepted-set; reducers обрабатывают свои segments и публикуют FP32 numerator shards. Global layer проверяет полную consistency matrix и только затем вызывает существующий outer publisher.

## Technical Context

- Math: decode local INT8/FP16/raw → FP32 weighted numerator; sum regional numerators → divide once by global tokens.
- Shards: logical parameter segments, versioned plan; bounded safetensors numerator artifacts.
- State: regional/global records с CAS/journal pattern feature `003`.
- Transport: extension/versioned reduce gRPC service; local in-process path authoritative for tests.
- Parallelism: independent shard reducers, deterministic canonical input ordering.
- Baseline: flat reducer остаётся reference oracle и runtime fallback.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Scientific correctness | Numerator/denominator contract исключает average-of-averages | Flat-equivalence suite |
| Plane separation | Regional partials reduce-only/hard-denied by P2P | Architecture tests |
| Versioned state | Topology, accepted sets, partials и assembly hashed | Lineage tests |
| WAN realism | Region/global links проходят netem profiles | Fault suite |
| Bounded heterogeneity | Static membership/deadlines; adaptivity later | Seal/abort tests |
| Reversible | Flat fallback и immutable topology per round | Rollback test |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
Coordinator seals RegionalAcceptedSet[r]
                 │
 local encoded shards from accepted workers
                 ▼
 RegionalReducer[r,j]: N[r,j] = Σ n_i * decode(Δ[i,j])
                 │  RegionalPartial(r,j,T_r,set_hash)
                 ▼
 GlobalIntake consistency matrix [regions × shards]
                 │
 GlobalReducer[j]: N[j] = Σ_r N[r,j]
                 │
 Assembler: Δ̄[j] = N[j] / Σ_r T_r
                 │
 existing outer optimizer + global P2P publisher
```

## Project Structure

```text
src/deltatorrent/
  domain/hierarchy.py
  reduce/
    topology.py
    shard_plan.py
    regional_sealing.py
    regional_reducer.py
    partials.py
    global_intake.py
    global_reducer.py
    assembler.py
    repository.py
  adapters/grpc/hierarchical_reduce.py
  cli/reduce.py
proto/deltatorrent/reduce/v1/reduce.proto
tests/
  unit/test_shard_plan.py
  unit/test_regional_numerator.py
  contract/test_reduce_protocol.py
  integration/test_hierarchical_equivalence.py
  integration/test_hierarchical_faults.py
  architecture/test_regional_partial_boundary.py
configs/topology/
docs/hierarchical-reduce.md
```

## Implementation Sequence

1. Утвердить topology/shard/partial schemas и exact consistency rules.
2. Реализовать shard-plan validator/property tests.
3. Реализовать regional accepted-set sealing и local-shard intake.
4. Реализовать FP32 weighted numerator и partial publication.
5. Реализовать global matrix intake, denominator validation и assembly.
6. Интегрировать existing outer optimizer/publication и flat fallback.
7. Добавить transport adapter и netem fault/retry tests.
8. Снять fan-in evidence и final constitution review.

## Test Strategy

- **Property**: arbitrary schema partition exact coverage, no overlaps/gaps.
- **Numerical**: regions/tokens/codecs imbalance against flat decoded FP32 reference.
- **Consistency**: mismatch set/token/topology/schema and incomplete matrix.
- **Concurrency**: arbitrary shard completion/retry order.
- **Recovery**: crash around partial/global set/assembly/current publish.
- **WAN**: delayed/lost region links with bounded retry/abort.
- **Architecture**: partials denied by distribution; flat reducer retained.

## Observability

Per region/shard: accepted workers/tokens, input/partial bytes, decode/reduce duration, accumulator norms, retry/status. Global: matrix completeness, regions/tokens, inter-region bytes, fan-in objects, assembly/outer/publish timings.

## Rollout and Rollback

Feature flag selects `flat` or `hierarchical` per round. First rollout uses fixed local topology fixtures, then controlled multi-process regions. Rollback creates subsequent rounds in flat mode; published hierarchical lineage remains readable and immutable.

## Risks and Mitigations

- **Average-of-averages**: store numerator+denominator, no regional averaged-only API.
- **Shard accepted-set divergence**: regional seal object is prerequisite shared by all shards.
- **Partial double count**: tuple identity/CAS and canonical global matrix.
- **Schema gaps**: property validation before round open.
- **Reducer loss**: bounded retry/abort now; redundancy in `008`.

## Exit Gate

Flat-equivalence, shard coverage, consistency, retry/crash и WAN abort suites зелёные; fan-in evidence recorded; regional partial P2P denial and flat fallback pass; quality gates and final Constitution Check complete.
