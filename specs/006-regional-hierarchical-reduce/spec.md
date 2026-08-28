# Feature Specification: Regional and Parameter-Sharded BFT Integer Reduce

**Feature Branch**: `006-regional-hierarchical-reduce`  
**Created**: 2026-08-23  
**Status**: Native/FFI/Java implementation PASS — final evidence publication in progress
**Depends on**: `005-content-addressed-p2p-distribution`

**Exact predecessor**: merge `1e884b4122898a8e0ff17254bc42414a8773830c`, source
`01f200b193733a1b474ad755c5c0c739b3189a96`, evidence overlay
`be5d72305bfd883a5bd99607df6c2788014bfd0a`, final report SHA-256
`7f7f86ad5021107688277ab626b266a61c7e633eb5c401e44c7778b98733dad6`.

**Formal impact**: `REFINEMENT_ONLY` against
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

## Summary

Feature 003 establishes a flat BFT integer reducer. This feature scales the reduce plane across regions and parameter shards without reintroducing a central coordinator or floating-point arithmetic.

Workers are assigned by immutable `ReduceTopology` to regional intake/storage paths. For each domain `d` and parameter shard `s`, a regional BFT committee computes a checked integer partial

`S_{r,d,s} = sum_{j in region r, domain d} a_j * q_{j,s}`

and certifies it with a `RegionalShardQC`. A global parameter committee then computes

`S_{d,s} = sum_r S_{r,d,s}`

in the same checked integer space. It does not average regional averages, divide in floating point or weight regions by worker speed. Counts/denominators and exact coefficient sums remain integer metadata for later certified application.

The hierarchical result must be byte-for-byte equal to the flat feature-003 reference over the same frozen inputs and coefficients.

Feature 006 defines only phase-scoped regional/global committee result bodies and quorum envelopes
needed to refine the already accepted hierarchical parameter-reduction actions. It does not
activate or complete the feature-008 ISC, EC, APC, ParameterShardQC, AggregateRootQC or ApplyQC
certificate lineage and cannot advance the current checkpoint.

## User Scenarios & Testing

### US1 — Reduce one frozen input set through three regions (Priority: P1)

A round freezes available tickets across three regions. Each regional committee retrieves only its assigned worker shards and emits certified integer partials.

**Independent Test**: three regions with unequal worker/ticket counts produce per-domain/per-shard bytes identical to a flat checked-integer reducer.

**Acceptance Scenarios**:

1. **Given** an immutable topology and frozen input root, **When** regional intake begins, **Then** every eligible ticket/shard has exactly one authoritative regional route.
2. **Given** a region's complete assigned inputs, **When** its `3f_r+1` committee executes, **Then** `2f_r+1` matching votes certify one integer partial for each required domain/shard.
3. **Given** unequal region sizes, **When** global combination runs, **Then** it sums regional integer numerators and exact count/coefficient metadata rather than averaging region outputs.
4. **Given** the same inputs in a flat reducer, **When** results are compared, **Then** all bytes and hashes match exactly.

### US2 — Execute parameter-shard committees independently but atomically (Priority: P1)

Large schemas are partitioned into deterministic parameter shards, each handled by its configured committee.

**Independent Test**: shuffled parallel completion still yields one complete aggregate root; missing, overlapping, duplicate or mixed-view shards prevent completion.

**Acceptance Scenarios**:

1. **Given** `ReduceShardPlan`, **When** validated, **Then** every trainable q element is covered exactly once.
2. **Given** regional/global results, **When** validators vote, **Then** every result binds topology, config, frozen input, domain, shard, coefficient-policy and arithmetic-proof roots.
3. **Given** one shard from another view/root, **When** assembly runs, **Then** the aggregate is rejected instead of mixing shards.
4. **Given** all required matching QCs, **When** assembly runs, **Then** one complete canonical root is produced independent of completion order.

### US3 — Recover from reducer failure without changing mathematics (Priority: P1)

Committee members fail or restart while enough validators remain for quorum.

**Independent Test**: message loss, process restart and primary proposer failure either produce the same partial/global bytes or abort without double-counting.

**Acceptance Scenarios**:

1. **Given** an exact partial proposal/QC retry, **When** processed again, **Then** it is idempotent.
2. **Given** conflicting validly signed partial proposals below quorum, **When** observed, **Then** equivocation evidence is recorded and neither changes finalized state.
3. **Given** fewer than `2f+1` live committee validators by deadline, **When** liveness fails, **Then** the required shard/round aborts; post-freeze silent region exclusion is forbidden.
4. **Given** a restarted validator, **When** journal replay completes, **Then** it cannot sign a conflicting partial for the same context.

### US4 — Keep partials out of the distribution swarm (Priority: P1)

Regional and intermediate global sums are reduce-plane evidence, not globally distributable model objects.

**Independent Test**: every regional/global-partial media type is rejected by feature-005 publisher; only the complete certified aggregate bundle may be registered under its certification policy.

## Edge Cases

- Region with zero frozen tickets for one domain.
- One ticket has shards routed to inconsistent regions.
- Same ticket appears in two regional sets.
- Regional committee validator sets overlap unexpectedly with global committee.
- Parameter tensor crosses shard boundaries.
- INT64 regional partial is safe but global sum requires INT128.
- Coefficient sum/count metadata differs across shards of one domain.
- Partial bytes are correct but bind wrong topology/input/proof root.
- Region becomes unavailable after input freeze.
- Committee reconfiguration occurs mid-round.
- Duplicate QC signer or mixed validator-set epoch.
- Partial accidentally enters P2P publisher.

## Requirements

### Functional Requirements

- **FR-001**: Each round MUST bind an immutable `ReduceTopology` containing regions, ticket-to-region mapping, parameter shard plan, regional/global validator sets, storage routes, deadlines and protocol/profile roots.
- **FR-002**: Topology validation MUST reject duplicate ticket membership, unknown IDs, incomplete routes, shard gaps/overlap and invalid `3f+1`/`2f+1` committee definitions before ticketing.
- **FR-003**: Region/domain membership MUST derive only from the frozen input set and immutable ticket metadata; no post-freeze reassignment/exclusion is allowed.
- **FR-004**: Each eligible ticket/shard MUST contribute to exactly one regional partial.
- **FR-005**: Regional reducers MUST verify feature-004 shard bytes, commitment/availability/freeze lineage and coefficient assumptions before arithmetic.
- **FR-006**: Regional arithmetic MUST use checked integer multiply/add under the round's accumulator proof; no float conversion or division is allowed.
- **FR-007**: `RegionalShardResult` MUST contain exact integer sum bytes, ticket count, coefficient sum, domain/shard IDs and all parent roots.
- **FR-008**: `RegionalShardQC` MUST require `2f_r+1` unique valid votes from the exact regional validator-set epoch.
- **FR-009**: A regional validator MUST persist vote intent before transmission and must not sign conflicting partial hashes for one context.
- **FR-010**: Global intake MUST accept exactly one finalized regional result per required `(region,domain,shard)` tuple; exact duplicate is idempotent, conflict fails closed.
- **FR-011**: Global parameter committee MUST sum regional integer partials and exact metadata using checked arithmetic; it MUST NOT average region means.
- **FR-012**: The global accumulator proof MUST cover the composition of all permitted regional bounds and coefficient sums.
- **FR-013**: Hierarchical output MUST be exactly equal to flat canonical integer reduction over the same ordered ticket set and coefficients.
- **FR-014**: Each global parameter result/QC MUST bind one topology/config/input/profile/proof/coefficient view.
- **FR-015**: Assembly MUST require complete exact non-overlapping domain×parameter-shard coverage; missing/duplicate/mixed-view result blocks aggregation.
- **FR-016**: Parallel execution and arrival order MUST NOT change result bytes, QC body or aggregate root.
- **FR-017**: Committee failure with insufficient quorum MUST produce deterministic non-applied/aborted outcome; silent substitution or arrival-order selection is forbidden.
- **FR-018**: Committee reconfiguration MUST occur only between rounds under a new topology/validator-set epoch.
- **FR-019**: Regional/global operations and receipts MUST be idempotent and restart-safe.
- **FR-020**: Complete lineage MUST be queryable from worker commitment to regional QC to global parameter QC and aggregate root.
- **FR-021**: Regional/global partial media types MUST be hard-denied by distribution; only the complete certified aggregate bundle is eligible under a registered policy.
- **FR-022**: Reference transport MUST support bounded streaming per shard and deterministic simulated WAN failure injection.
- **FR-023**: Metrics MUST include intra/inter-region bytes, ticket counts per domain, partial/QC latency, accumulator headroom, retries/equivocations, committee availability and abort reason.
- **FR-024**: Flat feature-003 reducer MUST remain the mandatory mathematical oracle/test path, not a production central authority.

### Non-Functional Requirements

- **NFR-001**: Three-region hierarchical results MUST match flat integer reference bit-for-bit for every domain/shard.
- **NFR-002**: Cross-region fan-in SHOULD scale with regions×shards rather than workers×shards; measured object/message counts are evidence, not an assumed claim.
- **NFR-003**: Reducer processes MUST operate within declared per-shard memory limits.
- **NFR-004**: All committee/transport operations are bounded, cancellable and deterministic under the simulator.
- **NFR-005**: Safety overrides availability; missing quorum or uncertain lineage aborts.
- **NFR-006**: No tolerance-based equality or floating arithmetic is permitted in exit tests.

### Key Entities

- **ReduceTopology**: immutable regions, routing, committee sets and shard plan.
- **RegionalInputSet**: exact frozen tickets assigned to one region/domain.
- **RegionalShardResult / RegionalShardQC**: integer partial and BFT proof.
- **GlobalRegionalSet**: exact required regional QCs for one domain/shard.
- **GlobalParameterResult / QC**: sum of regional partials.
- **HierarchicalAggregateRoot**: complete exact global result root.

## Success Criteria

- **SC-001**: Three unequal regions produce exact flat-reference integer bytes/hashes.
- **SC-002**: Shard/topology property tests prove exact ticket and parameter coverage.
- **SC-003**: Arrival/parallel/retry/restart permutations do not alter partial/global outputs.
- **SC-004**: Wrong input/topology/profile/proof/coefficient view and missing/duplicate shards block QCs/assembly.
- **SC-005**: Committee loss below quorum aborts; with quorum, proposer/member failure still yields the same result.
- **SC-006**: Evidence demonstrates reduced cross-region fan-in on the committed fixture.
- **SC-007**: Distribution boundary rejects every intermediate partial type.

## Assumptions

- Region and committee topology is fixed for one round.
- Membership is permissioned.
- Feature 008 will replace basic freeze/coefficient references with ISC/EC/APC and bind final shard QCs into AggregateRootQC.
- Regional proximity is configured, not adaptively mutated during an open round.

## Out of Scope

- Adaptive placement, adaptive `H`, stale updates or post-freeze region exclusion.
- Floating regional averages.
- Robust filtering and final ApplyQC.
- P2P distribution of partials.
- Permissionless committee selection.
