# Tasks: Content-Addressed P2P Distribution of Certified Objects

**Input**: `spec.md`, `plan.md`, Constitution 2.0.0 and completed feature `004`.

## Phase 0: Authority/boundary STOP

- [ ] T000 Remove/block coordinator-signer authority and every distribution path for worker/partial artifacts; record preflight evidence.

## Phase 1: Contracts and policies

- [ ] T001 Define canonical `ObjectManifest`, `PieceDescriptor` and object-ID rules in `src/deltatorrent/distribution/manifests.py`.
- [ ] T002 Define immutable `CertificationPolicy` registry and media-type strength requirements in `src/deltatorrent/distribution/policies.py`.
- [ ] T003 Implement feature-003 aggregated-transition-QC verifier adapter.
- [ ] T004 Define peer advertisement, lease and download-journal contracts.
- [ ] T005 Create object/piece/policy golden fixtures in `tests/fixtures/contracts/deltareduce_v1/005/`.
- [ ] T006 Add contract tests in `tests/contract/test_object_manifest_bytes.py`.

## Phase 2: CAS and publication

- [ ] T007 Implement filesystem CAS with atomic verified visibility and quotas in `src/deltatorrent/adapters/storage/filesystem_cas.py`.
- [ ] T008 Implement deterministic piece/Merkle publisher in `src/deltatorrent/distribution/publisher.py`.
- [ ] T009 Enforce media allowlist/denylist before chunking.
- [ ] T010 Enforce certification policy/root verification before publication.
- [ ] T011 Add idempotent publish and semantic-lineage identity tests.

## Phase 3: Peer and discovery plane

- [ ] T012 Implement bounded peer manifest/availability/piece service in `src/deltatorrent/distribution/peer.py`.
- [ ] T013 Implement non-authoritative multi-endpoint registry/lease adapter in `src/deltatorrent/distribution/registry.py`.
- [ ] T014 Implement verified-piece-only advertisement/seeding.
- [ ] T015 Add lease replay, false availability, endless stream and registry-outage tests.

## Phase 4: Resumable multi-peer download

- [ ] T016 Implement atomic `DownloadJournal` in `src/deltatorrent/distribution/journal.py`.
- [ ] T017 Implement deterministic bounded piece scheduler in `src/deltatorrent/distribution/scheduler.py`.
- [ ] T018 Implement multi-peer downloader/retry/backoff/cancellation in `src/deltatorrent/distribution/downloader.py`.
- [ ] T019 Implement safe CAS materialization in `src/deltatorrent/distribution/materialize.py`.
- [ ] T020 Add corrupt/slow/reordered three-peer test in `tests/integration/test_multi_peer_download.py`.
- [ ] T021 Add restart, verified-piece reuse and bit-rot tests.

## Phase 5: Seed loss and policy evolution

- [ ] T022 Add initial-seed-loss scenario in `tests/integration/test_seed_loss.py`.
- [ ] T023 Add unavailable-piece/quota/cancellation terminal-state tests.
- [ ] T024 Add certification-policy unknown/downgrade tests.
- [ ] T025 Add future `apply-qc-v1` fixture/registration seam without implementing feature-008 semantics.
- [ ] T026 Add architecture media-boundary tests in `tests/architecture/test_distribution_media_boundary.py`.
- [ ] T027 Add malicious metadata/path parser corpus in `tests/security/test_distribution_parser_paths.py`.

## Final Phase

- [ ] T028 Implement `swarm publish/seed/fetch/inspect/verify` CLI.
- [ ] T029 Add distribution/certification telemetry.
- [ ] T030 Document object, peer and policy protocol in `docs/deltareduce/distribution.md`.
- [ ] T031 Publish exit evidence and run cross-artifact analysis.
- [ ] T032 Run full quality gate and final Constitution Check.

## Dependencies

T000 is mandatory. T001–T006 block all storage/network work. T007–T011 block seeding. T012–T015 block multi-peer tests. T016–T021 block seed-loss tests. T022–T027 are the primary safety/resilience gate. T028–T032 are final.

## Exit Gate

All tasks pass; certified object IDs are stable; three-peer/restart/seed-loss scenarios reconstruct exact bytes; unknown/weaker certification and forbidden artifact classes fail closed.
