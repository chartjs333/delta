# Implementation Plan: Certified Content-Addressed P2P Distribution

**Branch**: `005-content-addressed-p2p-distribution` | **Date**: 2026-08-28 | **Spec**: `spec.md`

**Constitution**: 2.1.0

**Formal impact**: `REFINEMENT_ONLY` against
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

## Summary

Implement runtime-neutral object/piece/certification contracts, an authoritative native C++
manifest and certification-policy verifier exposed through the C ABI, and a Java JDK 25 data plane
for deterministic publication, CAS, bounded peer transfer, resumption and repair. Java executes a
typed native allow/reject decision and cannot decide certification strength or advance current
state. Peer authentication in this feature protects the data plane only; it is not the complete
certificate/consensus transport owned by feature 008.

No production source may be created until Phase 0 emits a passing content-addressed
`evidence/preflight.json` binding the exact feature-004 merge/source/evidence/report, accepted
Formal GO, protocol identities, current SpecKit tree and zero forbidden distribution/policy paths.

## Exact predecessor boundary

- feature-004 merge: `bd31efaa6d521bbfc3362ad9aac39455bd29a098`;
- feature-004 non-evidence source: `22dd996b5d169763bfde49f32c1b1b18f2656493`;
- feature-004 evidence overlay: `29fb4138499a348f90d6bbc44e77fe6d1914e25f`;
- feature-004 final report SHA-256:
  `9dbd9c7bda30d6ebe9b70f33a1a16d49a2b837b140d24f87becd433f05e3dccb`;
- feature-004 profile:
  `sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61`;
- feature-004 fixed-point config:
  `sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629`;
- feature-004 commitment root:
  `sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d`.

Any mismatch is an unconditional STOP.

## Constitution check

| Principle | Design response | Gate |
| --- | --- | --- |
| II — formal first | Exact Formal GO and refinement vocabulary are preflight inputs | preflight/refinement evidence |
| VI — lineage | Object ID binds source state, certificate root and immutable policy | canonical fixtures |
| VIII — plane separation | Native denylist rejects worker/local/partial media before Java publication | policy mutants/architecture scan |
| IX — safe boundaries | Bounded native parsing, authenticated peers, path-safe CAS and no pickle | fuzz/security matrix |
| X — failure/recovery | Identity-preserving repair and resumable incomplete-union outcome | journal/seed-loss traces |
| XI — observability | Bounded operations and deterministic evidence; no WAN claim | execution manifest |
| XII — replaceability | Native and Java direct/copy paths agree on bytes/status/effects | cross-runtime fixtures |

**Pre-implementation result**: pending `evidence/preflight.json`.

## Formal boundary

Feature 005 refines accepted `PublishCertifiedObject`, artifact loss/repair and plane-separation
behavior. Discovery, peer selection and piece ordering stutter unless verified availability changes.
Legal publication binds the exact immutable object and certificate lineage. Repair may restore only
the same content ID. Seed loss or incomplete union may return `PIECE_UNAVAILABLE` but cannot revoke
or rewrite certified current state. Any alternate publication authority, downgrade fallback or
current-state transition is `SEMANTIC` and returns to feature 000 before code.

## Runtime ownership

- Native C++ validates canonical manifest structure, media allowlist/denylist, source-state and
  certificate lineage, immutable policy strength and downgrade rules.
- The C ABI accepts bounded opaque bytes and returns a typed status/effect. It never retains Java
  pointers.
- Java JDK 25 owns CAS orchestration, deterministic chunking, peer framing, discovery hints,
  backpressure, cancellation, journals, scheduling, materialization and telemetry.
- Retained direct contiguous buffers use a synchronous borrowed fast path. Heap/composite input
  uses a bounded direct-copy fallback with identical status/effect/hash results.
- FFM, hashing and filesystem durability never run on a Netty event loop.

## Project structure

```text
delta-protocol/schemas/005/
  object-manifest-v1.json
  piece-descriptor-v1.json
  piece-profile-v1.json
  certification-policy-v1.json
  peer-advertisement-v1.json
  download-journal-v1.json
  transport-envelope-v1.json
delta-protocol/fixtures/005/{valid,invalid,cross-language}/

delta-core-cpp/include/delta/distribution/{certification_policy,manifest_verifier}.hpp
delta-core-cpp/src/distribution/
delta-ffi/src/distribution_abi.cpp

delta-node-java/src/main/java/io/deltareduce/node/distribution/
  manifest/ policy/ cas/ publisher/ peer/ discovery/ scheduler/
  downloader/ journal/ materialize/ telemetry/ ffi/
delta-node-java/src/test/java/io/deltareduce/node/distribution/
```

## Implementation sequence

1. Reconcile SpecKit and pass the exact feature-004/Formal/architecture preflight.
2. Freeze canonical object, piece, Merkle, policy, journal and transport bytes plus bounds.
3. Implement native fail-closed policy/manifest verification and C ABI direct/copy parity.
4. Implement Java deterministic CAS publication only after native acceptance.
5. Implement bounded peer framing, permissioned identity, non-authoritative discovery and verified
   piece seeding with event-loop protection.
6. Implement deterministic downloader, atomic journal, restart/bit-rot repair and path-safe final
   visibility.
7. Run three-peer corrupt/slow/reordered, seed-loss complete/incomplete union, leak/lifetime,
   parser/fuzz/mutant and formal-refinement gates.
8. Publish content-addressed execution and final compatibility evidence.

## Certification policy boundary

Feature 005 activates `aggregated-transition-qc-v1` only for immutable aggregate bundles bound to
the existing feature-003/004 state. `apply-qc-v1` may be registered solely as an inactive future
fixture and cannot make an object current. A current checkpoint without a real feature-008 ApplyQC
must be rejected.

## Rollout and rollback

Rollout begins with offline loopback peers and exact aggregate fixtures. Rollback stops new
advertisements/transfers while retaining verified immutable CAS bytes and resumable journals. It
never weakens policy, rewrites object identity or changes current state.

## Out of scope

Public DHT/NAT economics, permissionless identities, full consensus/certificate transport,
regional hierarchy, robust certificates, Apply semantics, erasure coding, CDN and WAN performance
claims remain later-feature work.

## Exit gate

All T000–T032 and HR005-001–HR005-013 obligations pass. Canonical object identity, native policy
acceptance, Java direct/copy lifetime, CAS/journal recovery, bounded peer protocol and three-peer
seed-loss behaviors have content-addressed evidence. Forbidden media and downgrade mutants produce
counterexamples, refinement traces preserve current state, and the final Constitution 2.1.0 check
passes without claiming later-feature semantics.
