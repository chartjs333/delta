# Implementation Plan: Regional and Parameter-Sharded BFT Integer Reduce

**Branch**: `006-regional-hierarchical-reduce` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Extend the feature-003 reducer into deterministic regional and global parameter committees. Regional committees emit certified integer sums; global committees sum those partials. Keep the flat integer reducer as the oracle and forbid average-of-averages, FP arithmetic and post-freeze topology mutation.

## Technical Context

- Reuse canonical q shards, checked arithmetic and QCs from 003–004.
- `ReduceTopology` is content-addressed and included in `RoundConfig`.
- Reference committees use the deterministic BFT harness with separate validator-set epochs.
- Transport uses bounded shard/result streams and WAN simulator profiles.
- Partial artifacts remain local/reduce-plane CAS objects.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| BFT state | Regional/global results require committee QCs | Quorum/equivocation tests |
| Integer arithmetic | Sums and metadata remain checked integers | No-float architecture gate |
| Domain purity | Results are keyed by domain; no speed-based mixture | Domain coverage tests |
| Certificate lineage | Every partial binds one topology/input/profile view | Mixed-view tests |
| Plane separation | Intermediate partials denied by swarm | Distribution regression |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
Frozen eligible q-shards
        │ ticket→region routing
        ▼
Regional committee (per domain/shard)
        │ RegionalShardQC
        ▼
Global parameter committee
        │ GlobalParameterQC
        ▼
Complete hierarchical aggregate root
```

## Project Structure

```text
src/deltatorrent/domain/reduce_topology.py
src/deltatorrent/reduce/
  routing.py
  regional.py
  regional_qc.py
  global_integer.py
  global_qc.py
  hierarchy_assembly.py
  telemetry.py
src/deltatorrent/adapters/grpc/reduce_server.py
proto/deltareduce/reduce/v1/reduce.proto
tests/unit/test_reduce_topology.py
tests/unit/test_regional_integer_reduce.py
tests/integration/test_three_region_flat_equivalence.py
tests/integration/test_committee_failover.py
tests/architecture/test_no_float_or_partial_distribution.py
```

## Implementation Sequence

1. Freeze topology/routing/result/QC canonical contracts.
2. Validate exact ticket and parameter coverage plus composed accumulator bounds.
3. Implement regional integer reducer and committee QC path.
4. Implement global regional-set validation and integer combination.
5. Implement complete assembly and flat-reference comparison.
6. Add committee failure/restart/equivocation and WAN-stream tests.
7. Add distribution boundary, telemetry, CLI and documentation.

## Test Strategy

Property tests for topology coverage; exact flat/hierarchical equality; mixed-view/wrong-epoch/duplicate signer; INT64→INT128 composition boundaries; parallel/arrival permutations; committee loss/restart; partial-media denylist.

## Observability

Record topology/input/profile/proof roots, domain/region ticket counts, regional/global sum/QC timings, bytes, accumulator headroom, retry/equivocation and quorum/abort state.

## Rollout and Rollback

Run flat and hierarchy in shadow comparison first. Enable hierarchical result only after byte equality. Rollback selects the flat BFT oracle for future rounds; it does not reinterpret existing partials or introduce a central writer.

## Exit Gate

Three-region result equals flat integer reference bit-for-bit; topology and mixed-view safety suites pass; committee failure is deterministic; no partial can enter P2P; final quality/Constitution checks pass.
