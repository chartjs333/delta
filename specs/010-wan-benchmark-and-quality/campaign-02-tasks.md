# Campaign 02 remediation and staged execution tasks

**Remediation authority**: `APPROVED_FOR_NEW_CAMPAIGN_REMEDIATION_ONLY`

**Execution-binding remediation authority**: PR #16 governance review `CHANGES_REQUIRED`

**Source branch**: `010e-primary-campaign-remediation` from
`661494c84cfcdb365c21542b46a5ebfe3a91cd8d`

**Execution-binding branch**: `010g-campaign02-execution-binding` from remediation merge
`8e945ac9713de5898d3abdb10ad2474079a87260`

**Formal impact**: `REGRESSION_ONLY` against
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

The Campaign 01 `T028`/`T029` results remain historical diagnostic evidence only. They do not
satisfy any Campaign 02 gate. No task in this file authorizes primary execution.

## Remediation source branch

- [x] **C2-001** Seal Campaign 01 closure as
  `TERMINATED_NO_GO_AFTER_STAGE_A_BEFORE_SCIENTIFIC_EXECUTION` and record zero scientific runs.
- [x] **C2-002** Define explicit optimizer-step, per-ticket and per-arm token accounting.
- [x] **C2-003** Implement an immutable GPU environment lock, pinned OCI base, SBOM and
  identity verifier.
- [x] **C2-004** Implement and fixture the measured WikiText evaluator.
- [x] **C2-005** Implement and fixture the measured LAMBADA evaluator.
- [x] **C2-006** Implement and fixture the measured HellaSwag evaluator.
- [x] **C2-007** Implement exact-plan `PrimaryScientificRunner` and `PrimaryEvaluationRunner`,
  including explicit run-level reference/certified finalization and Feature 008 chain admission.
- [x] **C2-008** Implement create-only `PrimaryObservationWriter` with immutable receipts and a
  required `run_result` union that cannot confuse a local ticket artifact with the applied
  checkpoint.
- [x] **C2-009** Run the remediation portable positive/negative test suite, including the
  run-level finalization rejection matrix.
- [x] **C2-010** Reissue exact GPU environment and designated-hardware qualification for the new
  source commit/tree.
- [x] **C2-011** Run exact-source remediation CI for the replacement source seal.
- [x] **C2-012** Freeze the replacement Campaign 02 remediation source commit/tree and derived
  component IDs.

Machine-readable evidence:

- `evidence/campaign-02-hardware-qualification.json` — designated GPU, exact runtime and
  non-primary QLoRA/NF4 qualification;
- `evidence/campaign-02-exact-source-qualification.json` — source commit/tree, portable test
  manifest, evaluator implementation IDs and runner/writer IDs.
- `evidence/campaign-02-exact-source-ci-receipt.json` — passing dedicated workflow run and
  immutable artifact digests.

Completion of `C2-011` does not authorize primary execution.

The source/evidence chain ending at `2157d81abd3543a3b3c4ba8655797c1a363c036f` is retained as
audit history and is superseded by
`reports/benchmark/campaigns/campaign-02/qualification-supersession.json`. It cannot satisfy any
Campaign 02 Definition or execution prerequisite.

The replacement source/evidence chain ending at
`55187704e7310edb71e53f4114726b25cd659dc8` is also retained as audit history and is superseded by
`reports/benchmark/campaigns/campaign-02/qualification-supersession-native-chain.json` because its
primary admission path did not invoke the authoritative native Feature 008 `ChainVerifier` over
the complete bundle.

## Definition branch and governance STOP

The remaining tasks begin only after remediation is merged into
`010-wan-benchmark-and-quality` and branch `010f-primary-campaign-definition` is created.

- [ ] **C2-013** Create a new immutable `BenchmarkDefinition`; never edit or reuse Campaign 01.
- [ ] **C2-014** Create the methodology diff, definition attestation and readiness record.
- [ ] **C2-015** Verify no scientific observation predates the new attestation.
- [ ] **C2-016** Obtain a separate governance authorization before any new Stage A execution.

## Execution-binding remediation after PR #16 review

The Definition `sha256:a4160af58ba310135bd86d03b2427c5034ae231f481e6229314e0e61d12b97af`
and its quorum-shaped unsigned record are superseded before execution. They remain immutable audit
history and cannot satisfy the tasks below.

- [x] **C2-017** Publish the pre-execution supersession record with zero observations and no
  execution authorization.
- [x] **C2-018** Source-seal distinct workload-contract, domain-manifest and exact ordered
  ticket-plan identities.
- [x] **C2-019** Implement the only Campaign 02 Definition-to-plan-catalog compiler, centrally
  reject every superseded primary Definition, and enforce exact Stage A/B/C authorization scope.
- [x] **C2-020** Bind the compiler to detached Ed25519 quorum verification and sign every
  security-relevant vote field, including signer/key identity and `submitted_at`.
- [x] **C2-021** Reissue source, designated-GPU, portable and current-head qualification for the
  corrected execution-binding and signed stage-governance source. The earlier `d9b8230...` and
  `b870c8a...` source qualifications are superseded and cannot complete this task. Replacement
  source `90f4b46...` / tree `e188e33...`, evidence overlay `67d0383...` and terminal workflow
  `33617322382` (48 success, 4 policy skips) complete this task without primary execution.
- [ ] **C2-022** Construct a new immutable Definition only after C2-021 passes; bind the distinct
  workload/domain/ticket IDs and qualified runtime lineage.
- [ ] **C2-023** Obtain independent detached signatures and verify temporal closure at the actual
  terminal reviewed HEAD.
- [ ] **C2-024** Obtain a new separate governance decision before any Stage A execution. This task
  replaces, but does not retroactively complete, C2-016 for the superseded Definition.
- [x] **C2-025** Require a detached Ed25519 quorum proof for every stage authorization; reject raw,
  unsigned, forged, wrong-validator-set and caller-constructed authorization documents.
- [x] **C2-026** Verify canonical typed predecessor gate receipts with exact PASS, Definition,
  catalog, source, analyzer, temporal and complete plan-set lineage; require `runner_role`.
- [x] **C2-027** Declare independent Stage A/B/C BFT runs, bind `gate_stage` into every round ID,
  source-seal 36 unique certified contexts and scope ticket templates by round ID.

Execution-binding qualification evidence:

- `reports/benchmark/campaigns/campaign-02/qualification-supersession-stage-authorization.json`
  — records that the prior `d9b8230...` source/evidence chain is historical only;
- `reports/benchmark/campaigns/campaign-02/qualification-supersession-signed-stage-governance.json`
  — records that the `b870c8a...` source/evidence chain is historical only;
- `specs/010-wan-benchmark-and-quality/evidence/campaign-02-signed-stage-governance-hardware-qualification.json`,
  `campaign-02-signed-stage-governance-exact-source-qualification.json` and
  `campaign-02-signed-stage-governance-exact-source-ci-receipt.json` — bind the corrected source,
  designated GPU, 96-case portable corpus, reproducible join and terminal current-head CI;
- `evidence/campaign-02-stage-authorization-hardware-qualification.json` — passing designated-GPU
  qualification for the corrected immutable source;
- `evidence/campaign-02-stage-authorization-exact-source-qualification.json` — passing portable
  exact-source qualification for the corrected immutable source;
- `evidence/campaign-02-stage-authorization-exact-source-ci-receipt.json` — passing dedicated
  workflow artifacts and terminal current-head control for the now-superseded qualification
  overlay; the replacement chain is source `90f4b46...`, evidence overlay `67d0383...` and workflow
  `33617322382`, with zero primary observations and no execution authorization.

## Unconditional STOP conditions

- No old Definition or Stage A artifact may be edited, overwritten or linked as a new gate result.
- No primary observation, Stage A/B/C, real-WAN run or `BenchmarkResultQC` may be produced here.
- Seeds, arms, thresholds, metric direction, missing/outlier policy, model/tokenizer, data revisions,
  domain mixture, network/fault profiles and the decision function remain unchanged.
- A mutable dependency, unbound evaluator/runner/writer, manually supplied observation JSON or
  token-plan mismatch fails closed.
