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
  → authoritative native Feature 008 ChainVerifier admission receipt
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

## Stage and BFT context model

Campaign 02 uses three independent benchmark executions for each arm/seed/repetition coordinate,
not three analyses of one underlying run. `gate_stage` is therefore part of the source-generated
`round_id`, and certified runtime lineage contains exactly:

```text
3 stages × 4 certified arms × 3 seeds = 36 unique certified round contexts
```

No two independent stage plans may share `(round_id, height, view, validator_epoch_id)`. The 32
IDs in `CampaignTicketPlan` are immutable ticket templates. Their protocol instance identity is
the pair `(round_id, ticket_template_id)`; a template ID alone is never a cross-round vote,
commitment or replay key. This is an instantiation of the accepted formal `round_contract`, not a
new action, certificate edge or failure outcome.

Stage execution authority is a separate detached Ed25519 quorum proof over the exact stage,
catalog, plan IDs, predecessor receipt IDs, source commit/tree and issue time. Stage B consumes
exactly one typed Stage A PASS receipt; Stage C consumes exactly one Stage A and one Stage B PASS
receipt. Receipt bytes are canonical and content-addressed, and their complete Definition,
catalog, source, analyzer and plan-set lineage is reverified before runner admission.

Primary publication uses observation schema v3. The create-only store persists the canonical
authorization, validator set, quorum attestation and every detached vote (including signature
bytes) as separate raw artifacts. The observation binds their artifact IDs, semantic content IDs,
quorum threshold and signature-set root; an attestation hash alone is not execution evidence.

Python structural checks are preflight only. Every certified result that may enter an observation
must carry a content-addressed native admission receipt produced by the versioned C ABI after the
authoritative C++ `delta::certificates::ChainVerifier` accepts the complete typed bundle. A missing
native verifier or receipt is a fail-closed admission error; there is no Python-only primary path.

## Governance

All earlier source/evidence chains remain immutable audit history. The latest supersession records
the unsigned StageAuthorization, untyped predecessor IDs, optional runner role and cross-stage BFT
context reuse found at `04aad0c530aa8c83a76315f737e5caa36fe9b14e`; it authorizes no execution.
The first two chains remain marked
`SUPERSEDED_BEFORE_CAMPAIGN02_DEFINITION`: the first had an incomplete run-level finalization
contract; the second ended at `55187704e7310edb71e53f4114726b25cd659dc8` and lacked the
authoritative native complete-chain verifier in its admission path. No Campaign 02 Definition,
primary observation, Stage A/B/C run, real-WAN run, `BenchmarkResultQC` or Feature 011 artifact is
created by this remediation.
