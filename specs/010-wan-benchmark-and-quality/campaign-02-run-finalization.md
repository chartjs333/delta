# Campaign 02 run-level finalization remediation

**Status**: source remediation in progress

**Formal impact**: `REGRESSION_ONLY`
**Formal semantics**:
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

## Boundary

This remediation changes only Feature 010 benchmark admission and evidence shape. It adds no
protocol action, vote context, certificate type, parent edge, failure terminal, durability outcome
or current-state transition. Certified admission consumes the already accepted Feature 008 chain:

```text
ticket contributions/commitments/ACs
  → one ISC → one seed/EC/APC context
  → complete required ParameterShardQC matrix
  → one AggregateRootQC → one ApplyQC/current command
  → one run-bound state/effect/WAL finalization receipt
```

The final checkpoint is taken only from this run-level finalization. A ticket contribution has no
global checkpoint or global certificate list.

## Result classes

- `REFERENCE` requires a reference round result with exact ticket/data exposure, total processed
  tokens, parent/final checkpoint and training artifacts. Feature 008 chain fields are forbidden.
- `CERTIFIED_DELTAREDUCE` requires the full run-level chain, exact planned ISC membership, the
  plan-bound required shard matrix, ApplyQC/final-checkpoint equality and run-bound runtime/WAL
  evidence.

The execution plan binds the result class. Certified plans additionally bind the Feature 008
context, validator/quorum policy, accumulator/apply profiles and required shard matrix.

## Governance

The earlier source/evidence chain remains immutable audit history and is marked
`SUPERSEDED_BEFORE_CAMPAIGN02_DEFINITION` because its run-level certified finalization contract was
incomplete. No Campaign 02 Definition, primary observation, Stage A/B/C run, real-WAN run,
`BenchmarkResultQC` or Feature 011 artifact is created by this remediation.
