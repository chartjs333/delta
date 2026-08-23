# Implementation Plan: Formal TLA+ and Parametric Proof Baseline

**Branch**: `000-formal-tla-spec` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Create a modular executable TLA+ model for the DeltaReduce v1 round, certificate, availability, failure/recovery and current-state lifecycle; check mandatory finite fault configurations with TLC; prove general quorum/fixed-point/hierarchy/apply theorems in Lean 4; create expected-counterexample mutants; define canonical trace/refinement contracts; and generate a reproducible content-addressed FormalVerificationReport.

No Python/PyTorch production implementation belongs in this feature. Small scripts for invoking tools, normalizing traces and verifying reports are formal-tooling infrastructure only.

## Technical Context

- **State-machine language**: TLA+ modules, TLC model checker and SANY parser.
- **Parametric theorem layer**: Lean 4 with a pinned toolchain and minimal audited dependencies.
- **Invocation**: repository `Makefile`/scripts and pinned container/tool checksums; mandatory path works without public internet after dependencies are cached/vendor-approved.
- **Evidence**: canonical JSON reports/traces, SHA-256 artifact graph and deterministic decision.
- **CI**: fast mandatory safety/proof/mutant suite per change; deeper state spaces as required before Formal GO and optionally nightly.
- **No hidden service**: formal verification runs from checked-in modules/configs/proofs and local tooling, not mutable SaaS dashboards.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Formal before code | Branch 000 blocks 001–011 until GO | prerequisite compatibility check |
| Replicated state | TLA+ models `3f+1`, votes, QCs, views and faults | QCUniqueness invariants |
| Fixed work | tickets/config/freeze are immutable state | Ticket/ISC invariants |
| Integer arithmetic | finite integer model + Lean parametric bounds | TLC boundaries + Lean build |
| Certificate lineage | explicit parent graph/actions | parent mutation/mixed-view mutants |
| Failure semantics | crash/partition/quorum/storage/repair/abort modeled | safety/liveness configs |
| Atomic apply | ApplyQC and pointer recovery actions | uniqueness/replay proofs |
| Plane separation | publication allowlist state | invariant/mutant |

**Pre-implementation result**: PASS for planning. No Formal GO exists until all tasks/evidence complete.

## Module Architecture

```text
formal/
  tla/
    DeltaReduceTypes.tla
    DeltaReduceQuorums.tla
    DeltaReduceTickets.tla
    DeltaReduceAvailability.tla
    DeltaReduceCertificates.tla
    DeltaReduceReduceApply.tla
    DeltaReduceFailures.tla
    DeltaReduceRefinement.tla
    DeltaReduce.tla
    cfg/
      safety-f1.cfg
      vote-crash-recovery.cfg
      availability-loss-repair.cfg
      split-brain-partition.cfg
      certificate-frankenstein.cfg
      apply-recovery.cfg
      liveness-eventual-synchrony.cfg
    mutants/
  proofs/
    lakefile.toml
    lean-toolchain
    DeltaReduce/
      Quorum.lean
      FixedPoint.lean
      Hierarchy.lean
      Coverage.lean
      Apply.lean
  schemas/
    formal-trace.schema.json
    formal-verification-report.schema.json
  fixtures/
    traces/legal/
    traces/illegal/
    counterexamples/
  scripts/
    run-sany.sh
    run-tlc.sh
    run-proofs.sh
    normalize-counterexample.py
    verify-formal-report.py
    check-refinement.py
  reports/
    README.md
Makefile
```

## TLA+ Design

### State factoring

- `Types`: constants, finite domains, canonical context keys and type predicates.
- `Quorums`: signer uniqueness, vote contexts, QC formation abstraction.
- `Tickets`: fixed plan, leases, commitment uniqueness.
- `Availability`: shard content identity, AC coverage, loss/repair.
- `Certificates`: ISC/seed/EC/APC/shard/root parent graph.
- `ReduceApply`: bounded integer results, coverage, ApplyQC/current pointer.
- `Failures`: crash/restart/journal, partition, deadlines, view change, abort.
- `Refinement`: stable action labels and trace-state projection predicates.
- `DeltaReduce`: composition of `Init`, `Next`, invariants and temporal properties.

### Model-check strategy

Use multiple explicit configs rather than one unreviewable state explosion. Each config publishes:

- constants/model values and symmetry declarations;
- enabled faults/actions;
- state constraints and justification;
- invariants/temporal properties checked;
- expected terminal/deadlock policy;
- explored states, distinct states, queue depth and diameter;
- exact module/config/tool hashes.

The coverage matrix must show that every mandatory invariant/failure appears in at least one relevant config. Cross-config assumptions may not contradict one another.

## Theorem-Prover Strategy

1. Prove finite-set cardinality/quorum intersection.
2. Derive conflicting-QC impossibility from honest vote uniqueness.
3. Prove signed product and finite-sum accumulator bounds.
4. Extend to common-denominator rational coefficients and intermediate widths.
5. Prove exact regional partition and hierarchy-flat equality.
6. Prove canonical coverage/key-table uniqueness under hash abstraction.
7. Instantiate quorum result for ApplyQC and prove current transition uniqueness/idempotence.
8. Emit an axiom/dependency report; mandatory results may not contain admitted placeholders.

Concrete feature profiles later supply theorem preconditions as content-addressed runtime proofs/config validation.

## Mutant Strategy

For each critical safeguard, create a minimal altered module/config expected to fail:

- remove persist-before-sign;
- allow two commitments per ticket;
- allow ISC mutation/late input;
- allow seed without ISC;
- omit APC parent from shard QC;
- allow incomplete aggregate coverage;
- remove checked overflow guard;
- allow current update without ApplyQC;
- allow local artifact publication.

CI succeeds only when the correct model passes and every mutant fails with the expected invariant/counterexample class.

## Trace/Refinement Strategy

- Define canonical JSON schema and versioned action IDs.
- Export/normalize representative TLC traces.
- Build a checker that validates projected concrete traces against legal transition/precondition/invariant rules.
- Seed legal/illegal fixtures before implementation branches.
- Later branches add implementation traces and bind `formal_semantics_id`.

A full general refinement proof of an arbitrary Python runtime is not claimed. The mandatory contract is trace refinement plus exact serialization/arithmetic conformance and architecture tests, with gaps documented in the report.

## Implementation Sequence

1. Pin toolchains, offline invocation and evidence schemas.
2. Freeze finite domains, context keys, state/action vocabulary and type invariant.
3. Implement vote/QC, tickets/commitments and durable crash recovery.
4. Implement availability, ISC and seed ordering.
5. Implement EC/APC parent graph, parameter/aggregate/apply/current transitions.
6. Add timeout/view/abort/partition/storage/apply fault actions.
7. Build safety configs and coverage matrix.
8. Add liveness configs with explicit assumptions.
9. Implement theorem project in dependency order.
10. Add mutants and expected counterexamples.
11. Implement trace schema/checker and legal/illegal fixtures.
12. Generate/independently reproduce FormalVerificationReport and final review.

## Test Strategy

- SANY syntax/semantic validation for every normal/mutant module.
- TLC invariants, action constraints, deadlock checks and temporal properties.
- Deliberate mutant failures with expected property names.
- Lean build, no-`sorry`/axiom report and theorem instantiation examples.
- JSON schema/canonicalization/hash/report-verifier tests.
- Legal/illegal refinement fixtures.
- Clean-container/offline reproducibility.
- Review checklist verifying finite scope versus parametric claims.

## State-Explosion Controls

Use symmetry only for genuinely interchangeable identities, abstract payloads to content IDs, bound queues/messages per config, split fault families and use state constraints that preserve the property. Every reduction needs a written soundness rationale. A config that becomes tractable by disabling the bug-causing action does not count as coverage.

## Observability and Evidence

Formal reports include parser/model checker/prover versions, JVM/runtime, module/config/proof hashes, state counts/diameter, property status, theorem dependencies, mutant outcomes, normalized counterexample IDs, refinement fixtures, assumptions, limitations and decision.

## Rollout and Rollback

The formal semantics ID is immutable. A failed new model/proof does not replace the last GO baseline. However no new implementation branch may use the old GO if its semantics changed incompatibly. Rollback means reverting to the last compatible formal baseline and discarding code/spec changes that require the failed semantics.

## Risks and Mitigations

- **State explosion**: modular configs, symmetry and explicit coverage review.
- **Vacuous invariants**: mutant counterexamples and reachability/action-coverage checks.
- **Overstated proof scope**: report finite bounds, assumptions and abstractions explicitly.
- **Mismatch between TLA+ and prose**: traceability IDs and cross-artifact review.
- **Theorem preconditions not enforced at runtime**: later feature tasks must materialize and verify exact precondition evidence.
- **Liveness under impossible faults**: never claim it outside eventual synchrony/quorum/availability assumptions.
- **Toolchain drift**: pinned versions/checksums and clean reproducibility.

## Exit Gate

- All mandatory TLA+ modules/configs parse and complete.
- Every required safety invariant passes relevant configs; no illegal deadlock.
- Every declared liveness property passes only under its documented assumptions.
- Every mutant produces the expected counterexample.
- Mandatory Lean theorems build without admitted placeholders and publish dependencies/axioms.
- Trace/refinement legal/illegal fixtures behave as expected.
- Clean offline-capable environment reproduces evidence hashes.
- FormalVerificationReport verifies and deterministically returns `GO`.
- Two independent reviewers approve scope/assumptions/coverage; final Constitution Check passes.
