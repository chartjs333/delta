# Feature Specification: Content-Addressed P2P Distribution of Certified Global Objects

**Feature Branch**: `005-content-addressed-p2p-distribution`  
**Created**: 2026-08-23  
**Status**: GO — implementation and content-addressed execution evidence complete
**Depends on**: merged `004-compressed-delta-protocol`

**Exact predecessor**: merge `bd31efaa6d521bbfc3362ad9aac39455bd29a098`, source
`22dd996b5d169763bfde49f32c1b1b18f2656493`, evidence overlay
`29fb4138499a348f90d6bbc44e77fe6d1914e25f`.

## Summary

After BFT aggregation, all workers and validators must retrieve the same immutable global object without relying on one bandwidth source. This feature provides canonical object manifests, piece hashing/Merkle roots, resumable multi-peer transfer and permissioned discovery.

The distribution plane never decides mathematical correctness. A trusted object identity originates from the replicated DeltaReduce state and its required certification policy. Peers may advertise locations, but they cannot redefine object bytes, lineage or certification.

The swarm accepts only identical global artifacts such as datasets, tokenizer/base-model objects, certified aggregate bundles, certificate bundles and certified checkpoints. Worker q-shards, commitments, availability fragments, input candidates and regional/parameter partials are permanently forbidden distribution media types.

## User Scenarios & Testing

### US1 — Publish one certified immutable object (Priority: P1)

A publisher receives bytes referenced by a finalized DeltaReduce state transition and creates a deterministic piece/object manifest.

**Independent Test**: identical source bytes, semantic lineage, certificate root and piece profile yield the same object ID and Merkle tree; a byte or lineage change yields a different identity.

**Acceptance Scenarios**:

1. **Given** an allowlisted global artifact and valid certification root, **When** publish runs, **Then** the object manifest binds media type, source state root, certificate policy/root, length, piece table and object ID.
2. **Given** worker-local/partial media type, **When** publish is attempted, **Then** it is rejected before chunking or advertisement regardless of caller role.
3. **Given** an object whose referenced QC/state root is missing or invalid, **When** validation runs, **Then** it cannot enter the swarm.
4. **Given** an already published object ID, **When** publish repeats, **Then** the same immutable manifest/CAS refs are returned idempotently.

### US2 — Download and verify from multiple peers (Priority: P1)

A worker obtains a trusted manifest root from replicated state, downloads pieces from several peers, validates each piece and resumes after interruption.

**Independent Test**: three peers with reordered, slow and corrupt responses reconstruct exact source bytes; restart reuses only hash-verified local pieces.

**Acceptance Scenarios**:

1. **Given** trusted manifest bytes/root and peer advertisements, **When** fetch starts, **Then** only missing pieces are requested under bounded concurrency/deadlines.
2. **Given** wrong length/hash or stream limit violation, **When** a piece is checked, **Then** it is discarded and retried elsewhere without altering trusted manifest state.
3. **Given** a partial verified journal, **When** the process restarts, **Then** referenced local pieces are rechecked and valid ones are not downloaded again.
4. **Given** all pieces, **When** materialization runs, **Then** full bytes, semantic lineage and certification references are reverified before atomic CAS visibility.

### US3 — Continue after loss of the initial publisher (Priority: P1)

Once peers have verified pieces, the original publisher disconnects and remaining peers complete the swarm.

**Independent Test**: after the verified union of remaining peers covers every piece, the initial seed is removed and a new downloader still reconstructs the exact object.

**Acceptance Scenarios**:

1. **Given** replicated verified pieces, **When** the initial seed lease expires, **Then** peer transfer continues without changing object identity.
2. **Given** a peer owns only a subset, **When** it advertises/serves, **Then** only locally verified pieces are exposed.
3. **Given** one required piece absent from all reachable peers, **When** deadline expires, **Then** fetch returns stable `PIECE_UNAVAILABLE` and preserves resumable state.

### US4 — Upgrade certification policy without reinterpreting bytes (Priority: P2)

Feature 008 introduces AggregateRootQC and ApplyQC. Existing distribution code must verify the policy named by the manifest rather than assuming a central signer.

**Independent Test**: development `aggregated-transition-qc-v1` and later `apply-qc-v1` fixtures are both verified by registered immutable policy implementations; unknown/downgraded policy IDs fail closed.

**Acceptance Scenarios**:

1. **Given** a manifest created before feature 008, **When** its exact registered development policy is used, **Then** verification is deterministic and no stronger claim is inferred.
2. **Given** a certified checkpoint requiring `apply-qc-v1`, **When** only a weaker aggregate QC is supplied, **Then** publication/download-as-current fails.
3. **Given** unknown or mutable policy mapping, **When** verification runs, **Then** it fails closed.

## Edge Cases

- Empty object, exact piece boundary and short last piece.
- Duplicate/overlapping piece descriptors or integer overflow in offsets/counts.
- Same payload bytes under different media type, state root or certificate root.
- Object manifest itself larger than configured limit.
- Peer claims a piece it no longer has or sends an endless stream.
- Tracker/registry unavailable after a peer snapshot is obtained.
- Disk full, quota exceeded, bit rot or crash between verification and journal commit.
- Symlink/path traversal during materialization.
- Newer checkpoint appears while an older immutable object is downloading.
- Downgrade from ApplyQC-certified checkpoint to aggregate-only object.
- Advertisement replay from another project/round/object.

## Requirements

### Functional Requirements

- **FR-001**: Distribution MUST accept only registered immutable global media types and MUST hard-deny worker q-shards, commitments, availability fragments and reduce partials.
- **FR-002**: `ObjectManifest` MUST bind schema version, media type, source lineage/state root, certification-policy ID, certificate root/ref, total length, piece profile, ordered descriptors, piece-tree root and canonical object ID.
- **FR-003**: Object identity MUST bind semantic lineage/certification as well as payload bytes; equal bytes with different trusted context are distinct objects.
- **FR-004**: Publication MUST verify the required finalized BFT state/certificate policy before chunking/advertising.
- **FR-005**: Feature-005 development aggregate objects MUST require the finalized feature-003 `AGGREGATED` transition/QC bundle; no single signer is authoritative.
- **FR-006**: Certification policy registry MUST be versioned, immutable by ID and fail closed on unknown or weaker-than-media-type policy.
- **FR-007**: Piece layout and Merkle construction MUST be deterministic, with explicit leaf/node prefixes and odd-node behavior.
- **FR-008**: Each piece descriptor MUST contain ordinal, offset, length and SHA-256; received pieces are invisible until exact verification.
- **FR-009**: CAS MUST store immutable manifests/pieces by content ID and atomically expose fully materialized objects.
- **FR-010**: Discovery advertisements MUST be non-authoritative hints bound to project/object/peer identity, verified-piece bitfield, endpoint, lease and resource limits.
- **FR-011**: Discovery MAY be replicated or multi-endpoint but MUST NOT define the trusted object manifest/root.
- **FR-012**: Peer protocol MUST support bounded manifest retrieval, availability query and piece streaming with cancellation/backpressure.
- **FR-013**: A peer MUST advertise and serve only pieces reverified against the trusted manifest.
- **FR-014**: Downloader MUST support multiple peers, bounded parallelism, retry/backoff, per-peer deadlines and deterministic seeded scheduling.
- **FR-015**: Every received piece and final object MUST pass length/hash/lineage/certificate-policy verification before CAS visibility.
- **FR-016**: Download journal MUST atomically record manifest ID, verified piece refs and attempt state; restart MUST reverify local bytes.
- **FR-017**: A verified piece MAY be seeded before the full object completes, subject to quotas.
- **FR-018**: Publisher/fetch/seed operations MUST be idempotent by object ID and request ID.
- **FR-019**: Resource policy MUST bound object/manifest/piece sizes, piece count, streams, bandwidth, disk, idle time and peer retries before allocation.
- **FR-020**: Materialization MUST use CAS-owned paths and prevent traversal, symlink overwrite and executable auto-load.
- **FR-021**: CLI/API MUST expose `swarm publish`, `seed`, `fetch`, `inspect` and `verify` with certification details.
- **FR-022**: Metrics MUST include source/peer bytes, corrupt/duplicate bytes, peer throughput, piece availability, retries, completion time and certification failures.
- **FR-023**: Current-checkpoint consumers MUST require the exact policy declared for that checkpoint class; aggregate-only objects cannot be silently treated as applied models.
- **FR-024**: No transfer/parser path may deserialize pickle or execute model/code payloads.

### Non-Functional Requirements

- **NFR-001**: Mandatory integration tests run offline without public tracker, DHT or internet.
- **NFR-002**: Download result is byte-identical; numerical tolerances never apply to distribution.
- **NFR-003**: All streams and discovery operations are timeout-bounded, cancellable and backpressure-aware.
- **NFR-004**: Initial-seed-loss succeeds when the verified remaining union is complete.
- **NFR-005**: P2P does not claim to reduce the minimum bytes each full replica downloads; it removes one egress bottleneck.
- **NFR-006**: Certification downgrade and forbidden-media tests are mandatory architecture/security gates.

### Key Entities

- **ObjectManifest / PieceDescriptor**: semantic/certified object identity and exact byte partition.
- **CertificationPolicy**: immutable verifier mapping media type to required BFT certificate lineage.
- **SwarmRecord / PeerAdvertisement**: non-authoritative location/availability hints.
- **DownloadJournal**: durable resumable verified-piece state.
- **CASObject**: fully verified immutable materialization.
- **DistributionPolicy**: allowlist/denylist, quotas and retry/deadline controls.

## Success Criteria

- **SC-001**: Canonical object/piece fixtures have stable IDs and detect any byte or lineage change.
- **SC-002**: Three-peer corrupt/slow/reordered transfer completes exact reconstruction in bounded time.
- **SC-003**: Restart reuses verified pieces and detects local bit rot.
- **SC-004**: Initial publisher loss does not prevent completion when remaining union is complete.
- **SC-005**: Every worker-local and partial artifact media type is rejected even with valid caller credentials.
- **SC-006**: Missing/invalid/unknown/downgraded certification policy blocks publication or current-checkpoint use.
- **SC-007**: Aggregate-QC and future ApplyQC policy fixtures coexist without reinterpretation.

## Assumptions

- Peers are permissioned in v1; discovery is not a permissionless DHT.
- Trusted object root/certificate reference is obtained from replicated DeltaReduce state, not peer gossip.
- Feature 008 registers the full AggregateRootQC/ApplyQC policies.
- Dataset/model licensing and access control remain deployment responsibilities.

## Out of Scope

- Public DHT, anonymous peers, NAT economics and Sybil resistance.
- P2P aggregation or mixing of distinct worker updates.
- Erasure coding/CDN integration.
- Making aggregate-only objects current before ApplyQC.
- WAN throughput claims before feature 010.
