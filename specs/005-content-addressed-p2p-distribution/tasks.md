# Tasks: Certified Content-Addressed P2P Distribution

**Input**: `spec.md`, `plan.md`, Constitution 2.1.0, accepted Formal GO and merged feature 004
`bd31efaa6d521bbfc3362ad9aac39455bd29a098`.

The authoritative certification boundary is native C++/C ABI. Java JDK 25 owns the bounded data
plane and executes native decisions. `task-map.md` is normative.

## Phase 0: Mandatory predecessor/formal STOP

- [x] T000 [HR005-012] Verify exact feature-004 merge/source/evidence/report ancestry and hashes.
- [x] T001 [HR005-012] Reverify accepted Formal GO, `PublishCertifiedObject`, repair,
  plane-separation and current-state preservation semantics.
- [x] T002 [HR005-003] Scan for Java-side certification authority, coordinator signer fallback,
  policy downgrade and accepted local/partial distribution paths; require zero findings.
- [x] T003 Classify the design as `REFINEMENT_ONLY`, bind the exact registry/trace boundary and stop
  on any new publication/current-state/failure outcome.
- [x] T004 Emit content-addressed `evidence/preflight.json` binding T000–T003 and the reconciled
  SpecKit source tree; block all production-source tasks until it passes.

## Phase 1: Runtime-neutral canonical contracts

- [ ] T005 Define bounded canonical object-manifest, piece-descriptor and piece-profile schemas.
- [ ] T006 Define immutable certification-policy registry with media strength and hard denylist.
- [ ] T007 Define peer-advertisement, download-journal and bounded transport-envelope schemas.
- [ ] T008 Freeze object identity, Merkle domains/odd-leaf rule, empty/short-final-piece behavior and
  all allocation limits before implementation.
- [ ] T009 Create valid, invalid and cross-language fixtures covering lineage, policy, bounds,
  overlap/gap/duplicate, forbidden media and future inactive Apply policy.
- [ ] T010 Register every schema/media/policy ID and publish deterministic golden hashes.

## Phase 2: Toolchains and native certification boundary

- [ ] T011 [HR005-001] Bind pinned JDK 25, JDK 26 compatibility, native compilers and offline
  dependency/tool execution manifests.
- [ ] T012 [HR005-003] Implement native canonical manifest and certification-policy verifier.
- [ ] T013 [HR005-012] Reject unknown/weaker policy, wrong source/certificate root, forbidden media
  and current checkpoint without ApplyQC before semantic use.
- [ ] T014 [HR005-003] [HR005-004] [HR005-005] [HR005-006] Add bounded C ABI plus synchronous
  borrowed-direct and owned-copy
  FFM commands returning identical typed status/effect/hash results.
- [ ] T015 [HR005-010, HR005-012] Add production parser/policy mutants, allocation corpus and exact
  legal/rejected refinement traces.

## Phase 3: Java CAS and deterministic publication

- [ ] T016 [HR005-008] Implement immutable piece/manifest CAS with quota checks, atomic visibility
  and path/symlink safety.
- [ ] T017 Implement deterministic Java chunking, piece tree and object ID matching frozen fixtures.
- [ ] T018 [HR005-003] Require native policy acceptance before chunking, CAS publication or
  advertisement; Java cannot construct an allow decision.
- [ ] T019 Add idempotent publication, same-bytes/different-lineage identity, crash and quota tests.

## Phase 4: Bounded permissioned peer plane and memory lifetime

- [ ] T020 [HR005-002] [HR005-007] Implement authenticated bounded manifest/bitfield/piece framing,
  cancellation, rate limits and backpressure.
- [ ] T021 [HR005-007] Implement non-authoritative leased discovery snapshots and replay rejection.
- [ ] T022 Implement verified-piece-only advertisement and seeding with immutable object context.
- [ ] T023 [HR005-004] [HR005-005] [HR005-006] Implement retained direct fast path and bounded
  staging-copy
  fallback with exact parity and no retained native pointer.
- [ ] T024 [HR005-009] [HR005-010] Add leak/lifetime/event-loop-blocking and
  corrupt/oversized/endless/truncated stream matrices.

## Phase 5: Resumable download, repair and seed loss

- [ ] T025 [HR005-008] Implement atomic journal, deterministic missing-piece schedule, bounded
  parallel retry/cancellation and verified-piece reuse.
- [ ] T026 Implement final full-object/lineage/policy revalidation and atomic CAS materialization.
- [ ] T027 [HR005-011] Add three-peer corrupt/slow/reordered, restart, bit-rot, registry-outage and
  initial-seed-loss complete-union scenario.
- [ ] T028 [HR005-011] Add incomplete-union `PIECE_UNAVAILABLE`, quota/cancellation and resumable
  state preservation with certified current state unchanged.

## Finalization

- [ ] T029 Add inspect/publish/seed/fetch/verify service commands and structured telemetry without
  logging payloads or claiming WAN performance.
- [ ] T030 Document object, policy, C ABI/FFM, peer, CAS/journal and recovery protocols plus claim
  boundaries.
- [ ] T031 [HR005-013] Publish content-addressed contracts, policy, compiler/JDK, memory lifetime,
  backpressure, seed-loss and refinement evidence.
- [ ] T032 Run cross-artifact consistency, complete offline quality gate and final Constitution
  2.1.0 check; emit deterministic compatibility evidence.

## Dependencies

- T000–T004 are sequential and block all production source.
- T005–T010 freeze bytes, limits and IDs before native or Java code consumes them.
- T011–T015 make native policy acceptance available before publication or networking.
- T016–T019 block advertisement/seeding.
- T020–T024 block multi-peer recovery tests.
- T025–T028 form the primary resilience and seed-loss gate.
- T029–T032 close documentation, execution and evidence.

## Exit gate

All T000–T032 and HR005-001–HR005-013 obligations pass; canonical IDs are stable; native policy
and Java direct/copy outcomes agree; three-peer/restart/seed-loss scenarios reconstruct exact bytes;
incomplete union preserves the resumable journal and current state; unknown/weaker policy and every
forbidden artifact class fail closed.
