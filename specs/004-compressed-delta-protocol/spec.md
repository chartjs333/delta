# Feature Specification: Canonical Fixed-Point Delta and Shard Protocol

**Feature Branch**: `004-compressed-delta-protocol`  
**Created**: 2026-08-23  
**Status**: Planned — ready for implementation  
**Depends on**: `003-bft-round-state-machine`

## Summary

Feature 003 proves a minimal bit-exact integer aggregation path. This feature turns that arithmetic into a scalable, versioned worker-vector and shard protocol suitable for WAN transport and independent implementations.

The mandatory DeltaReduce v1 profile is `int16-fixed-v1`: a worker normalizes its pseudo-gradient by `A_j`, quantizes each canonical parameter segment to signed INT16 using a scale/exponent fixed by `RoundConfig`, and commits immutable shard bytes. Consensus validators and reducers consume integer values directly; they never decode accepted contributions to FP16/FP32 for aggregation.

`raw-fp32`, `fp16` and block-local dynamic-scale profiles are not valid consensus contribution formats in DeltaReduce v1 because they cannot guarantee one shared integer lattice and bit-for-bit accumulator semantics. Additional integer profiles may be introduced only under new identifiers with complete conformance vectors and overflow proofs.

## User Scenarios & Testing

### US1 — Encode one normalized worker vector canonically (Priority: P1)

A worker applies the round's immutable quantization profile to an ordered normalized pseudo-gradient and produces deterministic INT16 bytes.

**Independent Test**: two independent encoders receive identical canonical source values/profile and emit identical metadata, q-values, shard bytes, leaf hashes and commitment root.

**Acceptance Scenarios**:

1. **Given** `hat(Delta)`, schema and `int16-fixed-v1`, **When** encoding runs, **Then** each value uses the profile's exact rational/power-of-two scale, round-to-nearest-ties-to-even rule and signed range.
2. **Given** a value outside the representable predeclared bound, **When** encoding runs, **Then** the ticket fails with `QUANTIZATION_RANGE_EXCEEDED`; silent clipping/saturation is forbidden unless an explicit earlier certified clipping rule produced the value.
3. **Given** zero, signed zero or an exact half-way value, **When** encoded on different supported platforms, **Then** canonical integer and byte results match the golden fixture.
4. **Given** a profile/schema/config mismatch, **When** encoding starts, **Then** it fails before producing a commitment candidate.

### US2 — Split, transfer and verify bounded shards (Priority: P1)

The encoded parameter vector is divided into deterministic bounded shards that can be stored and retrieved independently.

**Independent Test**: randomized delivery order, duplicate/corrupt/missing shards and parser-limit attacks either reconstruct the exact canonical q-vector or fail before unbounded allocation.

**Acceptance Scenarios**:

1. **Given** a schema and shard profile, **When** sharding runs, **Then** every trainable integer element is covered exactly once with no gap or overlap.
2. **Given** a shard envelope, **When** parsed, **Then** version, config/ticket/schema/profile, ordinal, range, length and content hash are checked before payload exposure.
3. **Given** duplicate, oversized, truncated or wrong-context bytes, **When** verification runs, **Then** the contribution cannot become available or eligible.
4. **Given** all valid shards in arbitrary arrival order, **When** canonical iteration runs, **Then** it yields the exact schema order without materializing an unbounded full-model buffer.

### US3 — Prove fixed-point accumulator safety for the encoded set (Priority: P1)

Before ticketing, configuration tooling computes exact worst-case accumulator bounds from integer vector range, maximum eligible ticket count and scalar coefficient range.

**Independent Test**: boundary fixtures for INT64 and INT128 accept the largest safe profile/config combination and reject the next unsafe combination.

**Acceptance Scenarios**:

1. **Given** maximum `|q|`, maximum `|a_j|`, maximum eligible count and headroom, **When** proof is computed, **Then** it records an exact integer upper bound per shard/profile.
2. **Given** a bound equal to the configured maximum, **When** validation runs, **Then** it is accepted only if every intermediate multiply/add is also representable.
3. **Given** any unsafe coefficient/count/profile change, **When** config validation runs, **Then** the previous proof becomes invalid and ticketing remains closed.
4. **Given** a runtime value inconsistent with the proof assumptions, **When** reduction encounters it, **Then** the contribution/round aborts rather than saturating.

### US4 — Preserve optional worker-local quantization residual safely (Priority: P2)

A future-compatible optional profile may retain quantization residual at the worker, but residual state must not weaken ticket or certificate determinism.

**Independent Test**: exact retry uses identical candidate bytes; rejected/unfrozen tickets do not advance residual; schema/profile/ticket-lineage changes require explicit reset/migration.

**Acceptance Scenarios**:

1. **Given** residual mode disabled (DeltaReduce v1 default), **When** a ticket is encoded, **Then** no residual state is read or written.
2. **Given** an enabled approved residual profile, **When** a candidate is created, **Then** prior residual version, normalized input hash, encoded root and candidate next-residual hash are atomically linked.
3. **Given** unknown/rejected/late outcome, **When** retry/recovery runs, **Then** candidate bytes are reused and current residual is unchanged.
4. **Given** the exact protocol-defined inclusion certificate, **When** residual commit runs, **Then** the candidate advances at most once.

## Edge Cases

- Scale numerator/denominator not reduced, zero denominator or exponent outside profile bounds.
- `-32768` handling versus symmetric `[-32767,32767]` profile choice.
- Half-way rounding for positive and negative values.
- Very small values quantizing to zero.
- Huge source value that would overflow intermediate scale multiplication.
- Tensor alias/tied parameter and frozen/omitted segments.
- One tensor split across several shards or several tiny tensors in one shard.
- Duplicate ordinal with same bytes versus conflicting bytes.
- Declared length arithmetic overflow and decompression-bomb metadata.
- Mixed profile versions within one ticket or round.
- INT64 accumulator selected while coefficient multiplication requires INT128.
- Worker crash between candidate write, commitment, availability and inclusion outcome.

## Requirements

### Functional Requirements

- **FR-001**: `FixedPointProfile` MUST be versioned and bind integer width, signed range, scale representation, rounding mode, out-of-range action, endianness, element layout, shard layout and accumulator requirements.
- **FR-002**: DeltaReduce v1 MUST implement `int16-fixed-v1` with one scale/exponent per canonical parameter segment or shard fixed by `RoundConfig`; per-worker dynamic scales are forbidden.
- **FR-003**: Scale values MUST use canonical integer/rational or power-of-two representation; floating serialized scales are forbidden in consensus metadata.
- **FR-004**: Encoding MUST operate on `hat(Delta)_{j,d}` after exact `A_j` normalization and MUST bind the normalization/profile implementation version.
- **FR-005**: Rounding MUST be round-to-nearest, ties-to-even with explicit signed behavior and portable golden vectors.
- **FR-006**: Out-of-range input MUST fail closed. Implicit saturation, wraparound, NaN/Inf coercion and platform casts are forbidden.
- **FR-007**: Consensus contribution formats MUST contain canonical integers; raw FP32, FP16/BF16 and worker-dynamic-scale encodings MUST be rejected by the allowlist.
- **FR-008**: `EncodedContributionManifest` MUST bind round/config/ticket/domain/parent/schema/profile, `A_j`, ordered shard table, total element count, total bytes and commitment root.
- **FR-009**: Each `EncodedShard` MUST include bounded canonical header, ordinal, exact schema segment range, element count, byte length and SHA-256 content ID.
- **FR-010**: Shard planning MUST cover the canonical trainable parameter schema exactly once without overlap/gap and MUST be deterministic for one schema/profile.
- **FR-011**: Parsers MUST validate all counts, lengths, ranges, versions and allocation limits before allocating or exposing payload bytes.
- **FR-012**: Shard verification MUST reject duplicate-conflicting ordinals, wrong config/ticket/schema/profile, non-canonical integers and trailing/unknown critical data.
- **FR-013**: Canonical q-value iteration MUST be independent of network arrival order and support bounded streaming into the integer reducer.
- **FR-014**: Merkle leaves MUST bind exact envelope header and payload bytes so metadata/payload cannot be mixed across tickets.
- **FR-015**: Profile negotiation MUST occur in `RoundConfig`; workers cannot choose a different accepted codec after ticket issuance.
- **FR-016**: Accumulator proof MUST include integer range, coefficient range, maximum eligible count, shard coverage and explicit intermediate-operation bounds.
- **FR-017**: INT64/INT128 proofs MUST be exact integer calculations and content-addressed; a config/profile change invalidates the proof hash.
- **FR-018**: Reducers MUST verify the proof/config hash and every input range assumption before arithmetic.
- **FR-019**: Runtime checked arithmetic failure MUST prevent a ParameterQC and emit deterministic evidence; saturation/wraparound is never a valid result.
- **FR-020**: Independent conformance fixtures MUST include source representation, expected q-values, envelope bytes, shard hashes, Merkle root and accumulator-bound result.
- **FR-021**: Optional residual mode MUST be a separate allowlisted profile and disabled by default in DeltaReduce v1.
- **FR-022**: Residual candidates MUST be keyed by worker, parent, schema, profile, ticket and prior residual version and MUST reuse exact bytes on unknown-outcome retry.
- **FR-023**: Residual state MUST advance only on the exact inclusion certificate named by the profile; rejected/late/aborted/unknown tickets cannot advance it.
- **FR-024**: Schema/profile change MUST require explicit reset or certified migration; silent reuse is forbidden.
- **FR-025**: Metrics MUST include source/q/shard bytes, encode time, zero/range counts, quantization error summaries (worker-local diagnostic only), accumulator headroom and parser failures.
- **FR-026**: Worker-local encoded shards remain reduce-plane artifacts and MUST be rejected by the distribution publisher.

### Non-Functional Requirements

- **NFR-001**: Two independent reference encoders MUST produce byte-identical results for all mandatory golden fixtures.
- **NFR-002**: Mandatory parser tests MUST be bounded and run without GPU or public network.
- **NFR-003**: Streaming verification/reduction MUST not require an unbounded full-model copy in each reducer process.
- **NFR-004**: The fixed-point protocol MUST not claim a particular quality error bound until feature 010 measures it.
- **NFR-005**: Safety takes precedence over compression ratio; any profile lacking a complete overflow/canonicalization proof is unsupported.
- **NFR-006**: No accepted consensus path may convert q-values to float before or during accumulation.

### Key Entities

- **FixedPointProfile**: immutable integer lattice, rounding, layout and accumulator contract.
- **QuantizationScaleTable**: canonical per-segment integer/rational scales fixed by the round.
- **EncodedContributionManifest**: ticket-bound q-vector and shard identity.
- **EncodedShard / ShardPlan**: bounded exact segment bytes and full schema coverage.
- **AccumulatorSafetyProof**: exact maximum intermediate/final bounds and headroom.
- **ResidualCandidate/ResidualState**: optional worker-local two-phase quantization-error state.
- **ConformanceVector**: portable source→q→bytes→hash expected result.

## Success Criteria

- **SC-001**: Independent encoders produce identical `int16-fixed-v1` q-values, bytes, shards and roots for the golden corpus.
- **SC-002**: Half-way, signed-limit, zero and out-of-range cases match the exact profile contract on all supported platforms.
- **SC-003**: Shard property tests prove exact non-overlapping schema coverage and bounded parser behavior.
- **SC-004**: INT64/INT128 safety corpus accepts the maximum safe case and rejects the first unsafe case/config mutation.
- **SC-005**: Integration with feature 003 streams q-values directly into checked integer accumulators and preserves the 100-ticket bit-identity hashes.
- **SC-006**: Float contribution formats, dynamic scales, wrong profiles and malformed envelopes are rejected before consensus arithmetic.
- **SC-007**: Optional residual retry/rejection/crash tests never advance state without the configured inclusion certificate.

## Assumptions

- Worker-local source arithmetic may be floating-point; its output becomes consensus-visible only through canonical q bytes.
- Exact scale-table selection is part of round preparation and is validated before ticketing.
- INT16 is the mandatory worker-vector profile; INT64 or INT128 is selected per safe accumulator proof.
- Advanced robust weights/clipping are introduced by feature 008 as exact integer/rational coefficients.

## Out of Scope

- FP32/FP16 consensus fallback.
- Per-worker dynamic scale aggregation.
- Top-K, PowerSGD, low-rank, entropy and 2-bit codecs.
- Quality-based scale tuning after ticketing opens.
- P2P transfer of worker contributions.
- Robust filtering, AggregateRootQC and ApplyQC.
