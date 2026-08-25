# Implementation Plan: Regional and Parameter-Sharded BFT Integer Reduce

**Branch**: `006-regional-hierarchical-reduce` | **Date**: 2026-08-23 | **Spec**: `spec.md`

**Constitution**: 2.1.0

**Formal impact**: `REFINEMENT_ONLY` against
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

**Exact predecessor**: feature-005 merge `1e884b4122898a8e0ff17254bc42414a8773830c`,
verified source `01f200b193733a1b474ad755c5c0c739b3189a96`, evidence overlay
`be5d72305bfd883a5bd99607df6c2788014bfd0a` and final report SHA-256
`7f7f86ad5021107688277ab626b266a61c7e633eb5c401e44c7778b98733dad6`.

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

## Mandatory preflight

No production source may be added until a content-addressed preflight has rederived the exact
feature-005 merge/source/evidence/report chain, accepted Formal GO, PO-H1/PO-H2 and PO-A1–PO-A3
artifacts, feature-004 arithmetic identities, feature-005 distribution policies and a zero-finding
architecture scan for float reduction, average-of-averages, post-freeze region exclusion and
partial-object P2P publication.

## Project Structure

```text
delta-protocol/
  schemas/006/{reduce-topology,regional-input-set,regional-shard-result,
               regional-shard-qc,global-regional-set,global-parameter-result,
               global-parameter-qc,hierarchical-aggregate-root}-v1.json
  fixtures/006/{valid,invalid,cross-language}/
delta-core-cpp/
  include/delta/reduce/{topology,routing,regional,regional_qc,global,
                        global_qc,assembly,flat_oracle}.hpp
  src/reduce/
  tests/
  fuzz/
delta-ffi/
  src/hierarchy_abi.cpp
  tests/hierarchy_abi_test.cpp
delta-node-java/src/main/java/io/deltareduce/node/reduce/
  {TopologyTransport,CommitteeRouter,RegionalStream,GlobalStream,
   ReduceDeadline,ReduceTelemetry,NativeHierarchy}.java
```

## Implementation Sequence

1. Pass the exact predecessor/formal/architecture preflight.
2. Freeze topology/routing/result/QC canonical contracts and theorem-precondition bytes.
3. Implement the authoritative C++ topology validator and exact routing table.
4. Implement C++ regional integer reduction and basic committee QC bodies.
5. Implement C++ global regional-set validation, integer combination and complete assembly.
6. Prove byte-for-byte equality against the flat C++ oracle before Java routing.
7. Expose bounded C ABI commands and add Java routing/FFM orchestration only.
8. Add failure/refinement, distribution-boundary, telemetry and final evidence gates.

## Test Strategy

Property tests for topology coverage; exact flat/hierarchical equality; mixed-view/wrong-epoch/duplicate signer; INT64→INT128 composition boundaries; parallel/arrival permutations; committee loss/restart; partial-media denylist.

## Observability

Record topology/input/profile/proof roots, domain/region ticket counts, regional/global sum/QC timings, bytes, accumulator headroom, retry/equivocation and quorum/abort state.

## Rollout and Rollback

Run flat and hierarchy in shadow comparison first. Enable hierarchical result only after byte equality. Rollback selects the flat BFT oracle for future rounds; it does not reinterpret existing partials or introduce a central writer.

## Exit Gate

Three-region result equals flat integer reference bit-for-bit; topology and mixed-view safety suites pass; committee failure is deterministic; no partial can enter P2P; final quality/Constitution checks pass.
