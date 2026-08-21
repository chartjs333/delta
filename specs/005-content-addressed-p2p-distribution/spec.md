# Feature Specification: Content-addressed P2P-раздача глобальных объектов

**Feature Branch**: `005-content-addressed-p2p-distribution`  
**Created**: 2026-08-21  
**Status**: Planned — ready for implementation  
**Depends on**: `004-compressed-delta-protocol`

## Summary

После reduce все workers должны получить один и тот же global delta/model artifact. Центральная раздача создаёт bandwidth bottleneck, поэтому функция вводит content-addressed object manifests, piece hashes, resumable multi-peer download и coordinator-assisted peer discovery.

Критическая граница: swarm распространяет только идентичные immutable объекты — dataset shards, tokenizer/base model, checkpoint, outer state и уже агрегированный global delta. `LocalUpdateManifest` и иные различные worker payloads никогда не становятся swarm objects.

Первая версия сознательно не использует DHT и не является permissionless BitTorrent-сетью. Discovery централизован, peers доверенные, а криптографическая identity/signature plane добавляется в feature `008`.

## User Scenarios & Testing

### US1 — Опубликовать проверяемый глобальный объект (Priority: P1)

Global publisher преобразует завершённый round artifact в immutable object, делит его на canonical pieces и регистрирует swarm.

**Independent Test**: один и тот же input artifact и piece profile дают одинаковые object ID, piece table и Merkle root; изменение одного байта меняет соответствующий piece hash и object identity.

**Acceptance Scenarios**:

1. **Given** published `RoundResultManifest` и global delta/checkpoint artifact, **When** publisher создаёт swarm object, **Then** media type проходит allowlist, а manifest содержит exact length, piece descriptors, object hash и source lineage.
2. **Given** worker-local update media type, **When** его пытаются опубликовать, **Then** publisher отвергает объект до chunking/announce.
3. **Given** тот же immutable input уже опубликован, **When** publish повторён, **Then** возвращается существующий object/swarm ID без дублирования bytes.

### US2 — Скачать объект у нескольких peers и продолжить после обрыва (Priority: P1)

Worker получает trusted object ID/manifest, загружает разные pieces параллельно, проверяет каждый до публикации и возобновляет незавершённую загрузку.

**Independent Test**: downloader собирает fixture object минимум из трёх peers при reordered/slow/corrupt responses, после restart использует только verified local pieces и получает exact source hash.

**Acceptance Scenarios**:

1. **Given** manifest и несколько peers с разными piece availability, **When** fetch запущен, **Then** scheduler запрашивает только отсутствующие pieces и соблюдает concurrency/deadline limits.
2. **Given** peer вернул bytes с неправильным hash/length, **When** piece проверяется, **Then** он не отмечается available, peer получает локальный failure event, а piece запрашивается у другого peer.
3. **Given** процесс остановлен после части pieces, **When** fetch перезапущен, **Then** journal повторно проверяет локальные pieces и продолжает без загрузки корректных bytes заново.
4. **Given** все pieces проверены, **When** object materialized, **Then** full-object hash/manifest lineage проверяются до atomic publication в CAS.

### US3 — Завершить раздачу после потери исходного seed (Priority: P1)

После передачи pieces нескольким peers initial publisher отключается, но swarm продолжает раздачу.

**Independent Test**: fault scenario гарантирует, что совокупность оставшихся peers имеет все pieces; initial seed отключается, новый downloader завершает exact reconstruction только от peers.

**Acceptance Scenarios**:

1. **Given** verified pieces уже реплицированы по swarm, **When** initial seed исчезает, **Then** tracker/PEX исключает его после lease expiry, а download продолжается.
2. **Given** один peer имеет лишь часть object, **When** его спрашивают availability, **Then** он рекламирует и раздаёт только локально verified pieces.
3. **Given** ни у одного reachable peer нет одного piece, **When** deadline истекает, **Then** fetch завершается диагностируемой `PIECE_UNAVAILABLE`, сохраняя resumable journal.

## Edge Cases

- Empty object и object ровно на границе piece size.
- Последний piece короче остальных.
- Manifest с duplicate ordinal/hash, overlapping offsets или integer overflow.
- Symlink/path traversal при materialization.
- Peer заявляет piece, которого нет, либо отдаёт бесконечный stream.
- Object удалён локально после advertisement.
- Tracker недоступен после получения peer list.
- Все peers имеют одинаковый неполный subset.
- Два manifest с одинаковым payload, но разным media/schema lineage.
- Process crash между piece verification и journal commit.
- Disk full, quota exceeded или hash recheck обнаружил bit rot.
- Позднее появление более свежей model version не должно мутировать текущий object.

## Requirements

### Functional Requirements

- **FR-001**: Distribution plane MUST принимать только allowlisted immutable media types: dataset/tokenizer/base-model/checkpoint/global-delta/outer-state/round-result и явно зарегистрированные будущие global artifacts.
- **FR-002**: `LocalUpdateManifest`, encoded worker update и regional partial reduce MUST быть hard-denied типами независимо от caller.
- **FR-003**: `ObjectManifest` MUST включать schema version, media type, source lineage, total bytes, piece profile, ordered piece descriptors, piece-tree root и canonical object ID.
- **FR-004**: Piece layout MUST быть детерминированным для exact bytes/profile; каждый piece имеет ordinal, offset, length и SHA-256.
- **FR-005**: Merkle/piece-tree construction MUST иметь committed canonical algorithm, включая leaf encoding и odd-node behavior.
- **FR-006**: Object ID MUST связывать payload identity и semantic manifest; два разных media/schema lineage не должны неявно считаться одним объектом даже при равных bytes.
- **FR-007**: CAS MUST хранить manifests/pieces по content ID, проверять bytes до visibility и публиковать assembled object атомарно.
- **FR-008**: Reference discovery MUST быть coordinator-assisted: seeder/peer объявляет object ID, verified piece bitfield, endpoint и bounded lease; expired announcements удаляются.
- **FR-009**: Peer protocol MUST предоставлять manifest retrieval, piece availability и bounded piece streaming с request deadlines/cancellation.
- **FR-010**: Peer MUST рекламировать/раздавать только pieces, которые он локально проверил против trusted manifest.
- **FR-011**: Downloader MUST поддерживать multiple peers, bounded parallelism, retry/backoff, per-peer timeout и deterministic seeded piece selection; rarest-first MAY использоваться при достаточной availability information.
- **FR-012**: Каждый received piece MUST пройти length/hash validation до CAS/journal commit; full object MUST пройти final length/hash/lineage verification.
- **FR-013**: Download journal MUST атомарно хранить manifest ID, verified piece set, local refs и attempt state; restart MUST revalidate referenced local bytes.
- **FR-014**: Corrupt/timeout/unavailable peer response MUST влиять только на локальный scheduling/telemetry; permanent trust/reputation policy отложена до feature `008`.
- **FR-015**: Peer, получивший verified piece, MUST иметь возможность немедленно seed-ить его до завершения всего object, если resource policy разрешает.
- **FR-016**: Tracker outage после получения peer snapshot MUST не ломать уже установленные peer transfers; новые peer discovery попытки bounded.
- **FR-017**: Publisher MUST быть идемпотентным по source artifact/object ID и не мутировать опубликованный manifest.
- **FR-018**: Resource policy MUST ограничивать total object size, piece size/count, concurrent streams, per-peer bandwidth, disk quota и idle timeout до allocation.
- **FR-019**: Materialization MUST защищать от path traversal/symlink overwrite и использовать dedicated CAS-owned paths.
- **FR-020**: CLI/API MUST предоставлять `swarm publish`, `swarm seed`, `swarm fetch`, `swarm inspect` и `swarm verify`.
- **FR-021**: Distribution metrics MUST включать source bytes, peer bytes, duplicate/corrupt bytes, per-peer throughput, piece availability, retries, completion time и seeding ratio.
- **FR-022**: Reference non-loopback peer server MUST требовать explicit trusted-development override до feature `008`; default bind остаётся loopback/private test harness.

### Non-Functional Requirements

- **NFR-001**: Mandatory integration suite MUST работать локально без public tracker/DHT/internet.
- **NFR-002**: Все streams MUST быть timeout-bounded, cancellable и backpressure-aware.
- **NFR-003**: Parser/materializer MUST быть safe against oversized metadata, decompression assumptions и filesystem traversal.
- **NFR-004**: Download result MUST быть byte-identical source artifact; P2P не допускает numerical tolerance.
- **NFR-005**: Initial-seed-loss scenario MUST завершаться при условии, что remaining verified piece union полон.
- **NFR-006**: P2P SHOULD распределять publisher egress по peers; это измеряется в benchmark feature `010`, а не считается достигнутым здесь.
- **NFR-007**: Протокол не обещает уменьшить минимальный download полного replica worker; он устраняет единственную точку раздачи.

### Key Entities

- **ObjectManifest**: semantic/content identity и ordered piece tree.
- **PieceDescriptor**: offset/length/hash/ordinal.
- **SwarmRecord**: object ID, active peer leases и availability snapshots.
- **PeerAdvertisement**: endpoint, verified bitfield, lease и capability limits.
- **DownloadJournal**: durable resumable local state.
- **CASObject**: fully verified atomic materialization.
- **DistributionPolicy**: allowlist, quotas, parallelism, retry/deadline parameters.

## Success Criteria

- **SC-001**: Canonical manifest/piece-tree fixtures дают стабильные IDs и обнаруживают любую piece corruption.
- **SC-002**: Three-peer download с reordering, slowness и одним corrupt peer завершает exact reconstruction в bounded time.
- **SC-003**: Restart/resume не перекачивает уже verified pieces и выявляет локальный bit rot повторной проверкой.
- **SC-004**: Initial seed loss не прерывает download при полном union pieces у оставшихся peers.
- **SC-005**: Architecture/security tests гарантированно отвергают worker-local и regional-partial media types.
- **SC-006**: Tracker-outage, unavailable-piece, quota и cancellation scenarios дают стабильные terminal/recoverable states без зависания.
- **SC-007**: Existing central publication path остаётся fallback и выдаёт тот же trusted object ID.

## Assumptions

- Trusted object ID/manifest поступает из coordinator artifact lineage; signature появится в feature `008`.
- Peers в первой версии принадлежат permissioned development deployment и не считаются враждебной permissionless сетью.
- Coordinator-assisted tracker достаточно для MVP; peer exchange может дополнять, но не заменять authority manifest.
- Dataset/model licensing и access policy задаются deployment-ом, а не P2P protocol.

## Out of Scope

- DHT, public tracker, NAT traversal, relay economics и anonymous participation.
- Cryptographic peer enrollment/signatures/revocation.
- Erasure coding, CDN integration и multi-object dedup optimization.
- P2P-смешивание/агрегация различных worker updates.
- WAN throughput targets и production-scale swarm tuning.
