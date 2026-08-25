# Implementation Plan: DeltaReduce v1 BFT Round State Machine

**Branch**: `003-bft-round-state-machine` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Implement a transport-independent deterministic transition core, fixed domain-pure ticket generator, commitment/availability lifecycle and checked integer parameter reducer. A four-node (`f=1`) deterministic BFT harness provides the mandatory reference. Production BFT/storage adapters remain replaceable and cannot redefine canonical bytes or arithmetic.

## Technical Context

- Python 3.12 reference implementation using typed immutable dataclasses/models.
- Worker-local training remains PyTorch from features 001–002; no PyTorch tensor reduction is used inside consensus.
- Reference fixed-point arithmetic uses Python integers plus explicit INT64/INT128 range checks; optimized native kernels may be added only after conformance.
- Hashing: SHA-256 over domain-separated canonical binary encodings.
- Merkle trees: explicit leaf/node prefixes, ordered leaves and defined odd-node behavior.
- Signatures: deterministic test keys in fixtures; production validator keys arrive through a signing-port interface.
- Durable state: append-only vote/transition journal plus content-addressed artifacts.
- Networking: injected deterministic message bus first, loopback gRPC adapter second.
- Time: logical consensus height/view and injected monotonic deadlines; wall clock never influences arithmetic or ordering.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Replicated state | `3f+1` validator harness, `2f+1` QCs, no authoritative singleton | Conflicting-config/vote tests |
| Fixed work | One-domain tickets with immutable `B/H` | Ticket golden fixtures |
| Integer arithmetic | Checked INT64/INT128 reference reducer | Boundary and overflow corpus |
| Input freeze | Seed service requires finalized input root | State/property tests |
| Certificate lineage | Every vote/result binds exact parent roots | Wrong-view rejection tests |
| Plane separation | Local/partial media types absent from distribution allowlist | Architecture tests |
| Reversibility | Journal replay and deterministic abort | Crash matrix |

**Pre-implementation result**: PASS. Any implementation proposal containing central authoritative state, adaptive `H_i` or floating reduction is an automatic STOP.

## Architecture and Data Flow

```text
RoundConfig command
       │
       ▼
DeterministicTransitionCore
  ├─ ValidatorSet / VoteGuard / QCVerifier
  ├─ FixedTicketGenerator
  ├─ CommitmentRegistry
  ├─ AvailabilityVerifier
  ├─ InputFreezer ──▶ SeedDeriver
  ├─ IntegerShardReducer
  ├─ ParameterQCAssembler
  └─ StateJournal / StateRoot
       │
       ▼
BFT engine adapter / loopback transport / storage peers
```

The transition core accepts only canonical commands plus prior certified state and returns deterministic events/state bytes. It performs no network I/O, file enumeration, random calls or floating arithmetic.

## Project Structure

```text
src/deltatorrent/
  domain/
    round_config.py
    tickets.py
    commitments.py
    availability.py
    consensus.py
    aggregates.py
  fixedpoint/
    profile.py
    quantize.py
    checked.py
    bounds.py
  consensus/
    transition.py
    validator_set.py
    vote_guard.py
    qc.py
    state_store.py
    bft_harness.py
  reduce/
    integer_shard.py
    assembly.py
  availability/
    storage_peer.py
    verifier.py
  adapters/grpc/
    consensus_server.py
    consensus_client.py
  cli/round.py
proto/deltareduce/consensus/v1/consensus.proto
tests/
  contract/test_round_config_bytes.py
  contract/test_ticket_bytes.py
  contract/test_vote_qc_bytes.py
  unit/test_checked_accumulator.py
  unit/test_commit_uniqueness.py
  unit/test_input_freeze.py
  unit/test_transition_model.py
  integration/test_four_validator_round.py
  integration/test_100_ticket_bit_identity.py
  integration/test_consensus_recovery.py
  property/test_seed_after_freeze.py
  architecture/test_no_central_or_float_reduce.py
```

## Implementation Sequence

1. Freeze canonical schemas, hash domains, Merkle rules and validator-set/QC contracts.
2. Implement checked INT64/INT128 primitives and pre-round overflow proof before any BFT orchestration.
3. Implement deterministic fixed ticket generation and golden fixtures.
4. Implement pure transition/state-root function and exhaustive model-based state tests.
5. Implement durable vote guard, QC verifier and four-validator deterministic harness.
6. Add commitment uniqueness, shard Merkle verification and availability certificates.
7. Add input freeze and seed gate; prove seed-order property.
8. Implement canonical integer shard reduce and complete ParameterQC assembly.
9. Add restart/replay journal, loopback adapter, CLI and structured telemetry.
10. Run 100-ticket/four-aggregator exit gate and final Constitution Check.

## Test Strategy

- **Golden contracts**: round/ticket/commitment/AC/vote/QC/state bytes and hashes.
- **Model-based state**: all legal and illegal transitions, including late/racing messages.
- **BFT safety**: conflicting proposals, duplicate signers, wrong epochs, equivocation and quorum intersection.
- **Arithmetic**: signed boundaries, multiplication bounds, exact rounding, zero values and first-overflow vectors.
- **Availability**: missing/corrupt shards, duplicate attestations, wrong retention epoch and restart.
- **Order properties**: message/shard arrival permutations produce identical canonical outputs.
- **Seed property**: no seed can be constructed without the finalized input-freeze root.
- **Recovery**: crash before/after vote journal, QC persist, state root and aggregate artifact.
- **Architecture**: no coordinator singleton, no floating add in reduce modules, no distribution of local artifacts.

## Observability

Expose round height/view/state root, validator votes/QCs, ticket and availability counts, late/rejected/equivocation reasons, accumulator type/headroom, shard progress, logical deadlines and abort reason. Logs contain IDs/hashes only, never full vectors, private keys or dataset content.

## Rollout and Rollback

Roll out first as an in-process four-validator harness, then as loopback processes with injected storage peers. A failed or partitioned round deterministically enters/stays non-applied/aborted and retains the parent checkpoint. Protocol identifiers are immutable; rollback disables the new round version rather than reinterpreting existing bytes.

## Risks and Mitigations

- **Consensus implementation risk**: keep a pure transition core and independent BFT adapter; validate against model traces.
- **Integer overflow**: prove conservative bounds before open and check every runtime operation.
- **Quantization ambiguity**: golden vectors fix rounding, scale, endianness and zero encoding.
- **Vote after crash**: persist vote intent before send and key by full context.
- **Seed manipulation**: make seed derivation structurally impossible without input-freeze QC.
- **Unavailable committed shards**: require AC coverage before freeze.
- **Hidden central authority**: architecture tests reject singleton current-state mutation APIs.

## Exit Gate

- All canonical schema and state-machine tests pass.
- Four validators (`f=1`) finalize a 100-ticket round under message permutations.
- Four independent aggregators produce byte-identical shard bytes, QCs and state root.
- Accumulator boundary suite proves safe maximum and rejects unsafe configuration/runtime operations.
- Commit equivocation, wrong-view shard and seed-before-freeze attempts are rejected.
- Crash/replay matrix shows no double vote or divergent transition.
- Full quality gate and final Constitution Check pass.
