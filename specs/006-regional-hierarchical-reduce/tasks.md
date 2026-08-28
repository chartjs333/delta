# Tasks: Regional and Parameter-Sharded BFT Integer Reduce

**Input**: `spec.md`, `plan.md`, Constitution 2.1.0, accepted Formal GO and merged feature 005
`1e884b4122898a8e0ff17254bc42414a8773830c`.

The authoritative hierarchy, arithmetic and committee-result boundary is native C++/C ABI. Java
owns bounded routing and executes native effects without making mathematical or quorum decisions.
`task-map.md` is normative.

## Phase 0: Mandatory predecessor/formal STOP

- [x] T000 [HR006-008] Verify exact feature-005 merge/source/evidence/report ancestry and hashes.
- [x] T001 [HR006-001] Reverify Formal GO, PO-H1, PO-H2 and PO-A1–PO-A3 artifacts and required
  runtime preconditions.
- [x] T002 [HR006-008] Reverify feature-004 profile/proof identities and feature-005 object,
  piece-profile, certification-policy and partial-media denylist identities.
- [x] T003 Prove zero authoritative float-reduce, average-of-averages, central fallback,
  post-freeze exclusion and partial-object publication paths; classify `REFINEMENT_ONLY`.
- [x] T004 Emit content-addressed `evidence/preflight.json` binding T000–T003 and block all
  production-source tasks until it passes.

## Phase 1: Runtime-neutral topology and proof contracts

- [ ] T005 [HR006-001] Freeze canonical `ReduceTopology`, ticket-to-region mapping, domain
  ownership, parameter shard ranges, committee epochs, deadlines and topology root schema.
- [ ] T006 Define regional input/result/basic-QC and global regional-set/result/basic-QC schemas.
- [ ] T007 Define complete hierarchical aggregate-root schema without activating feature-008
  certificate hierarchy or Apply/current transitions.
- [ ] T008 [HR006-005] Define content-addressed PO-H1/PO-H2/PO-A theorem-precondition instance.
- [ ] T009 Add valid, invalid and cross-language fixtures for unequal regions, multiple domains,
  multiple shards, overlaps, gaps, duplicates, wrong context and unsafe bounds.
- [ ] T010 Register every schema/media/domain ID and hard-deny every regional/global partial in
  the feature-005 distribution policy.

## Phase 2: Native exact topology boundary

- [ ] T011 [HR006-002] Implement C++ canonical topology parser and immutable context validation.
- [ ] T012 [HR006-002] Implement exact ticket/region/domain partition and parameter-shard coverage
  validation before any committee starts.
- [ ] T013 [HR006-005] Validate concrete coefficient, denominator and regional/global accumulator
  bounds against the frozen theorem instance.
- [ ] T014 [HR006-008] Add topology parser fuzz, allocation limits and production overlap/gap/
  unsafe-bound mutants.

## Phase 3: Native regional committees

- [ ] T015 [HR006-003] Derive each `(region,domain,shard)` input set from the exact frozen routing
  table and verify lineage/profile/proof roots.
- [ ] T016 [HR006-003] Stream checked integer `a_j*q_j` operations into the exact regional
  numerator and metadata totals without q-to-float conversion or division.
- [ ] T017 [HR006-003] Emit canonical regional result/vote/QC bodies through the feature-003
  persist-before-send and no-double-vote lifecycle.
- [ ] T018 [HR006-008, HR006-009] Add unequal-count, duplicate/retry, conflict, restart,
  proposer-failure, quorum-loss and artifact-repair/abort scenarios.

## Phase 4: Native global parameter committees

- [ ] T019 [HR006-004] Require exactly one finalized regional result for every immutable required
  `(region,domain,shard)` key; exact replay is idempotent and conflict fails closed.
- [ ] T020 [HR006-004] Sum regional integer numerators and exact count/coefficient/denominator
  metadata with checked arithmetic and no average-of-averages.
- [ ] T021 [HR006-004] Emit canonical global parameter result/vote/QC bodies with one uniform
  topology/input/profile/proof/epoch context.
- [ ] T022 [HR006-008, HR006-009] Add missing/duplicate/mixed-view/wrong-epoch/overflow/quorum-loss
  and recovery matrices.

## Phase 5: Complete hierarchy and exact flat oracle

- [ ] T023 [HR006-005] Assemble complete exact domain×parameter-shard coverage in canonical order.
- [ ] T024 [HR006-007] Compare three unequal regions, multiple domains and shards against the flat
  checked-integer C++ oracle byte-for-byte across arrival/parallel/retry permutations.
- [ ] T025 [HR006-008] Kill hierarchy, unchecked-overflow, partial-coverage and
  average-of-averages production mutants and export legal/illegal refinement traces.

## Phase 6: C ABI and Java routing only

- [ ] T026 [HR006-006] Add bounded C ABI commands with synchronous borrowed-direct and owned-copy
  parity; native retains no Java pointer.
- [ ] T027 [HR006-006, HR006-007] Implement Java topology delivery, permissioned committee routing,
  bounded streams, deadlines, cancellation, backpressure, retry and telemetry without math/QC authority.
- [ ] T028 [HR006-009] Add direct/copy, shuffled delivery, crash/restart, soft-view-change,
  hard-abort and event-loop/lifetime conformance suites.

## Finalization

- [ ] T029 [HR006-010, HR006-011] Regress the distribution denylist for every partial and measure
  exact flat-versus-hierarchical cross-region objects/bytes without claiming WAN performance.
- [ ] T030 [HR006-011] Publish theorem-instance, flat-equivalence, compiler/JDK, sanitizer,
  transport, failure/refinement and final Constitution 2.1.0 compatibility evidence.

## Dependencies

- T000–T004 are sequential and block every production-source task.
- T005–T010 freeze canonical bytes and theorem preconditions before native code consumes them.
- T011–T014 block committee execution.
- T015–T018 block global combination.
- T019–T022 block complete hierarchy assembly.
- T023–T025 form the mathematical/refinement gate before Java routing.
- T026–T028 precede final measurement and evidence.
- T029–T030 close the phase without claiming feature-008 certificate or Apply completion.

## Exit Gate

All T000–T030 and HR006-001–HR006-011 obligations pass; three unequal regions with multiple
domains/shards produce exact flat bytes and metadata; every overlap/gap/mixed-view/unsafe-bound/
quorum-loss path rejects or deterministically aborts; direct/copy and compiler/runtime matrices
agree; partials remain undistributable; no feature-008 certificate/current-state completion is claimed.
