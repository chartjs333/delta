# Campaign 02 remediation and staged execution tasks

**Remediation authority**: `APPROVED_FOR_NEW_CAMPAIGN_REMEDIATION_ONLY`

**Execution-binding remediation authority**: PR #16 governance review `CHANGES_REQUIRED`

**Definition construction authority**: post-merge governance decision
`APPROVED_FOR_MERGE_AND_C2_022_ONLY`

**Source branch**: `010e-primary-campaign-remediation` from
`661494c84cfcdb365c21542b46a5ebfe3a91cd8d`

**Execution-binding branch**: `010g-campaign02-execution-binding` from remediation merge
`8e945ac9713de5898d3abdb10ad2474079a87260`

**Definition branch**: `010h-campaign02-immutable-definition` from PR #17 merge
`881301d8443c667a478617cc663d1450aee9777a`

**Stage-runner remediation branch**: `010i-campaign02-runner-remediation` from the immutable
PR #18 construction head `9a4d0d8062ac432d7104284c75dc4b24773dadb0`

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
history in closed PR #16 and cannot satisfy the tasks below.

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
  source `90f4b46...` / tree `e188e33...`, evidence overlay `67d0383...` and workflow
  `33617322382` passed their exact-source chain, but receipt-head workflow `33618187137` exposed a
  required TSan lifetime race. They are superseded and cannot complete this task. Final replacement
  source `f323ae1...` / tree `6cb86a3...`, evidence overlay `8936015...`, designated-GPU report,
  96-case portable corpus and workflow `33620734265` passed; current-head control recorded 48
  successful checks, four policy skips and no failures or pending checks.
- [x] **C2-022** Construct a new immutable Definition only after C2-021 passes; bind the distinct
  workload/domain/ticket IDs, the qualified runtime lineage and content-addressed exactness,
  scientific, evaluation, observation, network/fault, gate-analyzer, stage-authorization,
  typed-receipt and native Feature 008 implementation identities. The Definition is
  `sha256:b263e77766599426dbf13574b05f2104ace1acf2d866e6ca5d9a3abef66f5dd5`;
  it creates no validator set, vote, attestation, plan catalog or execution authority.
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
- `reports/benchmark/campaigns/campaign-02/qualification-supersession-tsan-exception-lifetime.json`
  — records the required TSan failure on receipt-head `1620d6b...` and supersedes source
  `90f4b46...` before execution;
- `specs/010-wan-benchmark-and-quality/evidence/campaign-02-signed-stage-governance-hardware-qualification.json`,
  `campaign-02-signed-stage-governance-exact-source-qualification.json` and
  `campaign-02-signed-stage-governance-exact-source-ci-receipt.json` — preserve the superseded
  pre-TSan source, designated-GPU, portable and CI chain for audit;
- `specs/010-wan-benchmark-and-quality/evidence/campaign-02-signed-stage-tsan-lifetime-hardware-qualification.json`,
  `campaign-02-signed-stage-tsan-lifetime-exact-source-qualification.json` and
  `campaign-02-signed-stage-tsan-lifetime-exact-source-ci-receipt.json` — bind the final corrected
  source, designated GPU, 96-case portable corpus, reproducible join and terminal current-head CI;
- `evidence/campaign-02-stage-authorization-hardware-qualification.json` — passing designated-GPU
  qualification for the corrected immutable source;
- `evidence/campaign-02-stage-authorization-exact-source-qualification.json` — passing portable
  exact-source qualification for the corrected immutable source;
- `evidence/campaign-02-stage-authorization-exact-source-ci-receipt.json` — passing dedicated
  workflow artifacts and terminal current-head control for the now-superseded qualification
  overlay; source `90f4b46...` and evidence overlay `67d0383...` are also historical after the
  terminal receipt-head TSan failure. The replacement chain retains zero primary observations and
  no execution authorization.
- `configs/benchmark/campaign-02/definition-v2.json` and
  `qualified-runtime-lineage-v2.json` — the new immutable C2-022 Definition and its 36 independent
  certified stage contexts, bound to qualified source `f323ae1...` / tree `6cb86a3...`;
- `configs/benchmark/campaign-02/stage-execution-identities-v1.json` — content-addressed bindings
  for every Stage A/B/C runner/verifier role; every execution flag remains false;
- `reports/benchmark/campaigns/campaign-02/definition-readiness-v2.json` — records zero independent
  votes, absent attestation/catalog/execution authorization and C2-023 as the only next gate.

## Stage-runner remediation after PR #18 review

Definition `sha256:b263e77766599426dbf13574b05f2104ace1acf2d866e6ca5d9a3abef66f5dd5`
is immutable audit history with status `SUPERSEDED_BEFORE_ATTESTATION`, zero votes, absent
attestation and zero observations. It must not be signed, used to compile an executable catalog or
edited in place. PR #18 remains Draft and is not authorized for merge.

- [x] **C2-028** Replace the composite plan runner binding with exact stage-specific exactness,
  scientific and network/fault runner IDs, and recursively verify the complete stage identity
  manifest directly bound by runtime lineage and Definition.
- [x] **C2-029** Implement the source-bound Campaign 02 Stage A executor and manual-only workflow;
  require a verified Definition attestation, authoritative catalog, detached signed Stage A
  authorization, exact runtime lineage and exact identity manifest, then close exactly 15 plans.
- [x] **C2-030** Emit a canonical create-only typed Stage A receipt only after the complete native,
  JDK 25/JDK 26 and cross-component exactness matrix passes; bind its exact plan set, evidence root,
  runner, source, authorization attestation and gate result/QC identities.
- [x] **C2-031** Implement the Campaign 02 Stage C executor with the network/fault runner identity,
  exact 15-plan closure and exact Stage A plus Stage B predecessor receipt verification.
- [x] **C2-032** Run the cross-component positive/negative regression matrix for stage-specific
  runner IDs, actual `PrimaryScientificRunner` compatibility, non-executable composite metadata,
  Campaign 01 rejection, signed authorization, exact plan cardinality and complete evidence.
- [ ] **C2-033** Reissue the immutable source commit/tree, designated-GPU report, portable corpus,
  TSan qualification and terminal-head CI receipt; only then construct new stage identities,
  runtime lineage and a replacement immutable Definition with a new content ID.

Completion of C2-028 through C2-032 is source remediation only. It does not create Definition
votes, attestation, stage authorization, gate receipt, primary observation or execution authority.

Machine-readable source qualification evidence:

- `evidence/campaign-02-runner-remediation-hardware-qualification.json` — designated GPU,
  pinned CUDA 12.4/PyTorch/bitsandbytes environment and non-primary QLoRA/NF4 probe for source
  `287a1ce...` / tree `aa1ecb4...`;
- `evidence/campaign-02-runner-remediation-exact-source-qualification.json` — 116-case portable
  corpus, recursive source/component identities and C2-028 through C2-032 checks for that exact
  source, with zero primary scientific executions and observations.

## Unconditional STOP conditions

- No old Definition or Stage A artifact may be edited, overwritten or linked as a new gate result.
- No primary observation, Stage A/B/C, real-WAN run or `BenchmarkResultQC` may be produced here.
- Seeds, arms, thresholds, metric direction, missing/outlier policy, model/tokenizer, data revisions,
  domain mixture, network/fault profiles and the decision function remain unchanged.
- A mutable dependency, unbound evaluator/runner/writer, manually supplied observation JSON or
  token-plan mismatch fails closed.
