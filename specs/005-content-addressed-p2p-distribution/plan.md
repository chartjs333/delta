# Implementation Plan: Content-Addressed P2P Distribution of Certified Objects

**Branch**: `005-content-addressed-p2p-distribution` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Build a deterministic CAS/object-manifest layer, pluggable certification-policy verifier, bounded peer protocol and resumable multi-peer downloader. Replace coordinator-assisted authority with BFT state/certificate roots; discovery remains only a location hint.

## Technical Context

- Canonical hashing/Merkle rules reuse features 003–004.
- Reference storage is filesystem CAS with atomic rename and quota checks.
- Reference transport is loopback gRPC/HTTP-like bounded byte streaming behind ports.
- Discovery is an in-memory/file-backed multi-endpoint registry for tests; it is never trusted for object identity.
- Certification verifier initially supports feature-003 aggregate transition QC; feature 008 adds stronger immutable policy IDs.
- No public network dependency or DHT.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Certified state | Publish verifies BFT root/policy, no central signer | Certificate-policy tests |
| Plane separation | Hard media denylist before chunking | Architecture tests |
| Content identity | Bytes + semantic lineage + certificate root | Golden manifests |
| Safe boundaries | Bounded parsing/streaming and CAS paths | Malicious corpus |
| WAN realism | Retry/loss/seed-failure simulator | Integration suite |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
Finalized BFT state/certificate root
              │
              ▼
CertificationPolicyVerifier
              │
Global artifact ──▶ ObjectPublisher ──▶ CAS pieces/manifest
                                         │
                              non-authoritative advertisements
                                         │
             MultiPeerDownloader ◀──── peer servers
                     │
             DownloadJournal
                     │
          verified atomic CAS object
```

## Project Structure

```text
src/deltatorrent/distribution/
  manifests.py
  policies.py
  publisher.py
  downloader.py
  scheduler.py
  journal.py
  registry.py
  peer.py
  materialize.py
  telemetry.py
src/deltatorrent/adapters/storage/filesystem_cas.py
src/deltatorrent/adapters/grpc/peer_server.py
src/deltatorrent/cli/swarm.py
tests/contract/test_object_manifest_bytes.py
tests/integration/test_multi_peer_download.py
tests/integration/test_seed_loss.py
tests/security/test_distribution_parser_paths.py
tests/architecture/test_distribution_media_boundary.py
```

## Implementation Sequence

1. Freeze object/piece/certification-policy canonical contracts and media registry.
2. Implement CAS and deterministic publisher with policy verification.
3. Implement bounded peer server and non-authoritative discovery.
4. Implement journal, scheduler, multi-peer transfer and materialization.
5. Add corruption/restart/registry-outage/initial-seed-loss tests.
6. Add policy upgrade/downgrade fixtures and architecture boundary tests.
7. Add CLI, metrics and documentation.

## Test Strategy

Golden manifest/Merkle fixtures; malicious metadata/path corpus; three-peer timing/corruption permutations; restart/bit-rot; seed loss; registry outage; aggregate-QC validity; unknown/weaker policy rejection; forbidden media types.

## Observability

Record object/certificate IDs, peer/piece availability, verified/corrupt/duplicate bytes, retries/timeouts, CAS quota, completion/seed ratios and policy verification failures. Do not log object payloads, tokens or private credentials.

## Rollout and Rollback

Start with local peers and aggregate-QC-certified development objects. Protocol IDs are immutable. Rollback stops advertisements/transfers but preserves verified CAS bytes; it never weakens a required certification policy.

## Exit Gate

Canonical manifests, policy verification, bounded parser/materializer, restart and initial-seed-loss suites pass; local/partial artifacts remain impossible to publish; full quality and Constitution checks pass.
