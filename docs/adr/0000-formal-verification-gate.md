# ADR-0000: Require formal verification before implementation

**Status**: Accepted  
**Date**: 2026-08-23  
**Decision owners**: project specification authority

## Context

DeltaReduce v1 defines a Byzantine fault tolerant state machine, certificate hierarchy, fixed-point accumulator, hierarchical reduction and atomic outer-optimizer application. Natural-language requirements and unit tests are necessary but cannot exhaustively cover all message interleavings, crash points, partitions, duplicate/replayed commands or conflicting quorum proposals.

Several key claims are also parametric rather than finite-state:

- two `2f+1` quorums in a `3f+1` validator set intersect in at least `f+1` validators;
- a configured accumulator cannot overflow for any permitted vector/weight/count combination;
- an exact regional partition produces the same integer sum as flat aggregation;
- two conflicting ApplyQCs cannot finalize when honest validators persist and obey no-double-vote.

Implementing even unrelated-looking baseline code before fixing these semantics risks encoding incompatible state, artifact and recovery abstractions that later require invasive rewrites.

## Decision

Introduce `000-formal-tla-spec` as the mandatory predecessor of every code-bearing branch.

The formal baseline has two complementary layers:

1. **TLA+/TLC executable model** for state transitions, certificate parentage, asynchronous message delivery, Byzantine proposals, crash/restart, durable vote recovery, storage availability/repair, view change, hard abort and current-pointer recovery. TLC validates finite models and expected counterexamples.
2. **Machine-checked theorem layer** (reference implementation: Lean 4) for parametric quorum, fixed-point, hierarchical composition and Apply uniqueness results that finite model checking alone cannot establish generally.

The branch also defines a stable formal trace vocabulary. Later implementations must project externally visible executions into this vocabulary and demonstrate refinement/conformance for the affected actions.

A content-addressed `FormalVerificationReport` has deterministic decision:

- `GO`: every mandatory model, theorem, mutant and review gate passes;
- `NO_GO`: any mandatory obligation fails or evidence is missing/incompatible.

No branch `001–011` may begin implementation without an exact compatible GO report.

## Failure semantics fixed by this decision

- Soft deadline without quorum causes deterministic view/leader change; hard deadline causes certified abort.
- Network partition never permits two finalized values; progress is claimed only with eventual synchrony and honest quorum.
- Validator restart first restores the durable vote journal; conflicting re-vote is impossible.
- Before ISC, missing AC follows the fixed close policy. After ISC, loss/corruption of required bytes triggers bounded repair/retrieval and then abort; membership cannot be rewritten.
- Missing parameter/apply quorum retries only within the declared view/deadline policy; there is no single-node fallback.
- ApplyQC may be replayed to repair a crashed current-pointer update, but a failed apply cannot change the parent checkpoint.
- Finalized certificates and history are never rolled back or reinterpreted by a newer implementation.

## Consequences

### Positive

- Safety and recovery semantics become reviewable before code structure hardens.
- Deliberately weakened protocol variants must produce counterexamples, proving that checks are non-vacuous.
- Arithmetic and hierarchy claims become explicit proof obligations rather than confidence from test vectors.
- Implementation branches receive stable action/state/trace contracts.

### Costs

- The project adds TLA+/TLC and theorem-prover toolchains, CI time and specialist review.
- Liveness claims must be scoped carefully; model checking cannot manufacture progress under permanent partition or quorum/storage loss.
- Refinement traces add implementation instrumentation and maintenance work.
- A semantic protocol change now requires synchronized edits across specs, models, proofs and code.

## Non-claims

The formal model abstracts cryptographic primitives as unforgeable identities/signatures/hashes and assumes enrolled identities. It does not prove cryptographic implementations, permissionless Sybil resistance, honest local ML computation, poisoning resistance, model convergence or statistical quality.

## Migration

- Constitution increments from 2.0.0 to 2.1.0.
- `000-formal-tla-spec` becomes the base of `001-reproducible-training-baseline`.
- All authoritative feature branches are restacked above 000.
- Existing legacy central/adaptive refs remain historical only.
- Feature plans must classify formal impact and rerun the applicable gate.

## Reversal criteria

Removing or weakening this gate requires a constitutional amendment explaining an equivalent method for exhaustive interleaving/failure validation, parametric arithmetic/quorum proofs and implementation refinement. Schedule pressure or passing unit tests is not sufficient.
