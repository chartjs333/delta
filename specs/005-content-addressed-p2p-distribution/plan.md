# Implementation Plan: Content-addressed P2P-раздача глобальных объектов

**Branch**: `005-content-addressed-p2p-distribution` | **Date**: 2026-08-21 | **Spec**: `spec.md`

## Summary

Добавить generic immutable-object CAS и distribution application layer. Publisher строит canonical fixed-piece manifest/tree; tracker хранит leased peer advertisements; downloader планирует bounded parallel piece requests, commits только verified bytes и ведёт restart-safe journal. Reference peer/tracker transport реализуется через versioned gRPC на local test network, не проникая в domain.

## Technical Context

- Hash: SHA-256; canonical binary leaf/node encoding документируется golden fixtures.
- Piece profile: fixed-size pieces с bounded final piece; профиль версионирован.
- CAS: filesystem reference implementation с per-object/piece atomic files и quota accounting.
- Transport: protobuf/gRPC streaming, deadlines/backpressure; in-process fake для deterministic tests.
- Async runtime: `asyncio` application scheduling; clocks/randomness injected.
- Discovery: central tracker lease + optional peer-supplied endpoints; no DHT.
- Security posture: hashes verify integrity, но не publisher identity; external bind guarded.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Reduce/distribution split | Hard media-type allow/deny gate before publication | Architecture/security tests |
| Content-addressed state | Manifest, pieces и assembled object immutable/hash-verified | Golden/corruption tests |
| WAN realism | Loss/latency/disconnect profiles reused offline | Multi-peer fault suite |
| Bounded operations | Quotas, deadlines, leases, backpressure, cancellation | Resource/failure tests |
| Permissioned default | No DHT/public exposure; non-loopback guarded | Bind-policy test |
| Observable/reversible | Download journal, metrics, central fallback | Resume/rollback gate |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
Global artifact ─▶ ObjectPublisher ─▶ ObjectManifest + piece CAS
                                         │
                                      announce
                                         ▼
                                  Tracker (leases)
                                         │ peer snapshot
                                         ▼
Worker Downloader ── requests ──▶ Peer PieceServers
       │                               ▲
       ├─ verify piece ─▶ local CAS ───┘ seed verified pieces
       └─ journal ─▶ final verify ─▶ atomic object materialization
```

## Project Structure

```text
src/deltatorrent/
  domain/distribution.py
  distribution/
    manifest.py
    merkle.py
    policy.py
    publisher.py
    tracker.py
    peer.py
    scheduler.py
    downloader.py
    journal.py
    materializer.py
  artifacts/cas.py
  adapters/grpc/
    swarm_tracker_server.py
    swarm_peer_server.py
    swarm_client.py
  cli/swarm.py
proto/deltatorrent/swarm/v1/swarm.proto
tests/
  unit/test_piece_layout.py
  unit/test_piece_scheduler.py
  contract/test_swarm_protocol.py
  security/test_distribution_allowlist.py
  security/test_swarm_parsers.py
  integration/test_multipeer_download.py
  integration/test_download_resume.py
  integration/test_seed_loss.py
configs/swarm/
docs/distribution-protocol.md
```

## Implementation Sequence

1. Зафиксировать media-type policy, manifest/piece/tree schemas и golden fixtures.
2. Реализовать filesystem CAS, quotas и safe materialization.
3. Реализовать publisher и hard reduce/distribution boundary.
4. Реализовать tracker leases и peer piece server ports.
5. Реализовать download journal, scheduler, verifier и partial seeding.
6. Добавить gRPC adapters с bind/deadline/limit guards.
7. Прогнать corruption, resume, tracker outage и seed-loss scenarios под netem simulator.
8. Подтвердить central fallback/object identity и final Constitution Check.

## Test Strategy

- **Golden**: exact manifest/object ID/piece-tree roots для empty/boundary/multi-piece fixtures.
- **Property**: arbitrary bytes chunk→assemble identity, any mutation rejected.
- **Security**: media type confusion, oversized counts, path traversal, slow/infinite streams.
- **Integration**: 3–5 peers с partial availability, corrupt peer, reorder/loss/disconnect, tracker outage.
- **Recovery**: crash after piece write/before journal and vice versa; disk bit rot on restart.
- **Architecture**: no dependency from distribution to worker update types except explicit deny classifier.

## Observability

Object/piece IDs, peer lease state, verified/duplicate/corrupt bytes, source breakdown, retries/timeouts, active streams, disk quota, completion and seeding ratio. Logs never include object payload.

## Rollout and Rollback

P2P distribution включается feature flag-ом per object; central artifact fetch остаётся fallback. Rollback прекращает новые announcements/serving, но CAS/manifests сохраняются и проверяются. Старые object IDs/manifest versions остаются readable.

## Risks and Mitigations

- **Нарушение plane boundary**: deny-by-type API и compile/architecture tests.
- **False availability**: serve only verified CAS refs; retry other peers.
- **Disk exhaustion**: reservation/quota before fetch и LRU только для unpinned objects.
- **Tracker bottleneck**: leases/compact bitfields; DHT отложен до evidence.
- **Hash integrity без identity**: trusted coordinator source now, signatures в `008`.

## Exit Gate

Canonical IDs, exact reconstruction, resume, malicious input и seed-loss suites проходят; local/regional updates hard-denied; public bind disabled; central fallback identity совпадает; full quality gate и final Constitution Check зелёные.
