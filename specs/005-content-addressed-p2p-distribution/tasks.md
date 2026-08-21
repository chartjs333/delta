# Tasks: Content-addressed P2P-раздача глобальных объектов

**Input**: `spec.md`, `plan.md`, constitution и завершённые `001–004`.

## Phase 1: Distribution contracts

- [ ] T001 Определить object/piece/swarm/journal models в `src/deltatorrent/domain/distribution.py`.
- [ ] T002 Определить immutable media allowlist/denylist policy в `src/deltatorrent/distribution/policy.py`.
- [ ] T003 Реализовать canonical piece layout и tree algorithm contract в `src/deltatorrent/distribution/manifest.py` и `merkle.py`.
- [ ] T004 Создать protobuf peer/tracker API в `proto/deltatorrent/swarm/v1/swarm.proto`.
- [ ] T005 [P] Добавить canonical manifest/tree fixtures в `tests/fixtures/contracts/swarm/`.
- [ ] T006 Добавить contract tests в `tests/contract/test_swarm_protocol.py`.

## Phase 2: CAS and safe publication foundation

- [ ] T007 Реализовать quota-aware piece/object filesystem CAS в `src/deltatorrent/artifacts/cas.py`.
- [ ] T008 Реализовать safe atomic materializer в `src/deltatorrent/distribution/materializer.py`.
- [ ] T009 Реализовать idempotent `ObjectPublisher` в `src/deltatorrent/distribution/publisher.py`.
- [ ] T010 Добавить hard local/regional-update denial в publisher API.
- [ ] T011 [P] Добавить empty/boundary/property piece tests в `tests/unit/test_piece_layout.py`.
- [ ] T012 Добавить allowlist/type-confusion/path tests в `tests/security/test_distribution_allowlist.py`.

## Phase 3: US1 — Publish global object

- [ ] T013 [US1] Интегрировать round-result/global artifacts с publisher в `src/deltatorrent/coordinator/publisher.py`.
- [ ] T014 [US1] Реализовать publish/inspect/verify CLI в `src/deltatorrent/cli/swarm.py`.
- [ ] T015 [US1] Добавить idempotent publication/content mutation tests в `tests/integration/test_swarm_publication.py`.

## Phase 4: Discovery and peer serving

- [ ] T016 Реализовать lease-based tracker service в `src/deltatorrent/distribution/tracker.py`.
- [ ] T017 Реализовать verified-only peer piece service в `src/deltatorrent/distribution/peer.py`.
- [ ] T018 [P] Реализовать gRPC tracker/peer/client adapters в `src/deltatorrent/adapters/grpc/swarm_tracker_server.py`, `swarm_peer_server.py` и `swarm_client.py`.
- [ ] T019 Реализовать bind/resource/deadline guards в `src/deltatorrent/adapters/grpc/swarm_security_mode.py`.
- [ ] T020 Добавить lease/advertisement/stream parser tests в `tests/security/test_swarm_parsers.py`.

## Phase 5: US2 — Multi-peer resumable download

- [ ] T021 [US2] Реализовать atomic `DownloadJournal` в `src/deltatorrent/distribution/journal.py`.
- [ ] T022 [US2] Реализовать deterministic bounded piece scheduler в `src/deltatorrent/distribution/scheduler.py`.
- [ ] T023 [US2] Реализовать downloader verification/retry/finalize flow в `src/deltatorrent/distribution/downloader.py`.
- [ ] T024 [US2] Реализовать partial verified-piece seeding в `src/deltatorrent/distribution/peer.py`.
- [ ] T025 [P] [US2] Добавить scheduler tests в `tests/unit/test_piece_scheduler.py`.
- [ ] T026 [US2] Добавить corrupt/slow/reordered multi-peer test в `tests/integration/test_multipeer_download.py`.
- [ ] T027 [US2] Добавить restart/bit-rot/quota tests в `tests/integration/test_download_resume.py`.

## Phase 6: US3 — Seed-loss resilience

- [ ] T028 [US3] Добавить lease expiry/tracker outage behavior в `src/deltatorrent/distribution/tracker.py` и `downloader.py`.
- [ ] T029 [US3] Создать deterministic initial-seed-loss scenario в `tests/integration/test_seed_loss.py`.
- [ ] T030 [US3] Добавить missing-piece bounded failure scenario в `tests/integration/test_piece_unavailable.py`.

## Final Phase: Validation and documentation

- [ ] T031 Добавить CLI `swarm seed/fetch` и smoke config в `configs/swarm/`.
- [ ] T032 Документировать protocol, trust boundary и non-goals в `docs/distribution-protocol.md`.
- [ ] T033 Добавить architecture test reduce/distribution boundary в `tests/architecture/test_distribution_boundary.py`.
- [ ] T034 Записать functional evidence в `specs/005-content-addressed-p2p-distribution/evidence.md`.
- [ ] T035 Выполнить cross-artifact analysis, full quality gate и final Constitution Check.

## Dependencies

- T001–T006 блокируют persisted/network contract.
- T007–T012 блокируют publication и downloader.
- T016–T020 блокируют multi-peer integration.
- T021–T027 формируют US2 vertical slice.
- T028–T030 зависят от verified partial seeding.
- T031–T035 выполняются после всех scenarios.

## Implementation Strategy

Сначала доказать immutable CAS и запрет неправильных media types. Затем один peer, resumability и только после этого multi-peer/seed-loss. Не добавлять DHT, NAT traversal или trust reputation в текущую ветку.

## Exit Gate

Все T001–T035 выполнены; canonical, security, exact multi-peer, resume и seed-loss tests зелёные; local/regional updates не публикуются; central fallback работает; evidence и Constitution Check завершены.
