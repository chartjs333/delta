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
- [x] **C2-033** Reissue the immutable source commit/tree, designated-GPU report, portable corpus,
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

The source/evidence chain `287a1ce...` / `aa1ecb4...`, overlay `b4bbb08...` and workflow
`33650130142` passed, but is retained as historical audit evidence only. During replacement
manifest construction it exposed that typed gate receipts still used a legacy global gate-analyzer
ID instead of the recursively verified manifest identity. The chain is superseded before any new
Definition by `reports/benchmark/campaigns/campaign-02/qualification-supersession-runner-gate-analyzer.json`.

The replacement source is `7caad473501a31d95e24408901a6a2236ec03ce6` / tree
`515d65fbf5a18ab872c8f31187b7a0788a33badc`. Its current machine-readable evidence is:

- `evidence/campaign-02-runner-gate-analyzer-hardware-qualification.json` — passing designated-GPU
  probe for the replacement source;
- `evidence/campaign-02-runner-gate-analyzer-exact-source-qualification.json` — passing 116-case
  portable corpus and recursively bound stage-runner/gate-analyzer source identities.

Both records retain zero primary scientific executions and observations. The closing TSan,
dedicated exact-source CI, terminal current-head control and Definition package are recorded below.

C2-033 replacement construction is now closed by dedicated workflow `33651585075`, exact TSan,
terminal overlay `5192b38...` with 49 successful checks, seven policy skips and no failures or
pending checks, and `evidence/campaign-02-runner-gate-analyzer-exact-source-ci-receipt.json`.
The replacement stage identity manifest is
`sha256:59d7345a158086e20574eec0a1c3b095f3e8557c1147e422eab71f5ddcd4a56d`, runtime lineage is
`sha256:159db3bc3214bb6039fc5ceaf7770caffbdd261f6b3dd6b178da486e955a8b76`, and immutable Definition is
`sha256:3844edbdcfc402ca3fbd54f9a2e4dfab965a8a7280a6ccd3dad70611e88ee803`.
It has zero votes, absent attestation, no authoritative catalog, no execution authorization and
zero observations. Governance review of this replacement package is required before C2-023.

## Executable-provenance remediation after PR #19 review

Definition `sha256:3844edbdcfc402ca3fbd54f9a2e4dfab965a8a7280a6ccd3dad70611e88ee803`
is immutable audit history with status `SUPERSEDED_BEFORE_ATTESTATION`, zero votes, absent
attestation and zero observations. It must not be signed or edited in place. PR #19 remains Draft;
merge, C2-023, C2-024 and all Stage A/B/C execution remain unauthorized.

- [x] **C2-034** Bind the actual production Stage A/C runner object and gate finalizer to the exact
  manifest identity, role, source commit/tree, environment, source class, implementation ID and
  recursively verified executable bytes before the first plan; reject dry, fixture, synthetic and
  caller-supplied primary runners. Keep admission-only tests unable to create a gate receipt.
- [x] **C2-035** Implement a concrete `Campaign02NetworkFaultRunner` that loads and re-hashes every
  Definition network/fault profile, executes each emulated profile and fault trace for all 15 plans,
  checks expected outcomes and emits typed per-plan counters and resilience evidence.
- [x] **C2-036** Parse the seven retained Stage A native/JDK/Python artifacts, require the exact
  expected test/version/marker sets with zero failures/errors/skips, and bind their raw digests to
  canonical verified summaries before receipt emission.
- [x] **C2-037** Bind Stage A to actual GitHub workflow/dispatch SHA, repository/ref, workflow blob,
  run ID/attempt, authority digest and all retained input/output digests; reject mismatched SHA/ref,
  reruns and fabricated same-named evidence. Registering the immutable workflow on `main` remains a
  separate pre-C2-024 governance/merge operation and is not authorized by this remediation.

Completion requires a new immutable source seal, designated-GPU report, portable corpus, TSan and
terminal-head CI receipt. Only then may a create-only Definition v4 be constructed for another
governance review. These tasks never authorize a benchmark stage or create a primary observation.

C2-034 through C2-037 are closed by source `b97fd541a7ef7f100b8ff1ccf4ced61aa2880de2`
/ tree `354bd4cae74e568b8489b667aeb4e88f36de57e0`, the designated-GPU and exact-source
`campaign-02-runner-provenance-*` evidence records, and dedicated workflow `33662489371` with
portable, TSan and exact-source join jobs all passing. The recursively verified stage identity
manifest is `sha256:e318e753fc1317257973850cb60b6483a768fde66c819c6cfcaf8d136ca87c1b`,
runtime lineage v4 is `sha256:6f45bad28e192b2210854dd6038e81445bb79ccb93d8b21a126838b146ada670`,
and create-only Definition v4 is
`sha256:26830d3199482873832f4030641c20a0758c4f474abebacbc668de35d56dfdf9`.
Definition v4 has zero votes, absent attestation, no authoritative catalog, no execution authority
and zero observations. A new governance review is required before C2-023. Registration of the
immutable Stage A workflow on `main` remains a separate pre-C2-024 operation.

## Measured Stage C and bootstrap source remediation after authoritative PR #19 verdict

The later governance verdict supersedes the closure claim above: PR #19 remains
`DRAFT / CHANGES_REQUIRED / DO NOT MERGE`. Definition v4
`sha256:26830d3199482873832f4030641c20a0758c4f474abebacbc668de35d56dfdf9`
is `SUPERSEDED_BEFORE_ATTESTATION`, has zero votes, absent attestation, no authoritative catalog,
no execution authorization and zero observations. It must not be signed. C2-023, C2-024 and every
Stage A/B/C primary execution remain unauthorized; Feature 010 is `NO_GO` and Feature 011 remains
blocked.

- [x] **C2-034 regression** Preserve source-bound production runner/finalizer construction and all
  dry, fixture, synthetic, caller-supplied and simulated-only rejection paths. Requalification is
  required after the new source seal.
- [x] **C2-035 blocking** Replace production Stage C simulation with a measured Python → Java Netty
  → C++ runtime/WAL → OS-counter path. Bind image, Java executable, native executable, transport
  harness and Netty artifact IDs through stage identity v4, runtime lineage v5 and execution plan
  v6 before the first plan. `simulate()` remains only a non-primary test oracle, and the native
  runtime derives observed outcomes without receiving `expected_outcome`.
- [x] **C2-036 regression** Preserve exact semantic parsing of the seven Stage A artifacts.
  Requalification is required after the new source seal.
- [x] **C2-037 source blocking** Implement the signed immutable default-branch bootstrap mapping,
  zero-execution registration verifier and reusable source workflow provenance. Bind caller and
  called workflow SHAs separately, plus workflow ref/blob/content, run attempt, GitHub artifact ID,
  artifact archive digest and extracted file digest. The routing mapping intentionally excludes a
  Definition ID so that a future Definition can bind the mapping ID without a cryptographic
  self-reference; the separate C2-024 authority must bind both objects before execution.

Only source remediation on `010j-campaign02-measured-stagec-bootstrap` is authorized here. A source
seal and complete requalification come next. The inert bootstrap on `main` requires a separate
post-freeze review and merge, followed by a zero-execution registration receipt. None of these
source tasks creates a replacement Definition, votes, attestation, catalog, stage authorization,
gate receipt, primary observation or `BenchmarkResultQC`.

Source seal `29e0c942ec36102e9e464d10f31a677327cce412` / tree
`3a7a8ba63335f0f3861dcfda524091dda8b5900a` passed the non-primary designated-GPU qualification
recorded in `evidence/campaign-02-measured-stagec-bootstrap-hardware-qualification.json` with the
same pinned environment ID, zero primary executions and zero observations. Terminal portable,
TSan, sanitizer, C++20/C++23 and two independent measured 15-plan Stage C CI runs are required on
the evidence overlay before governance review. This qualification does not close C2-035 or C2-037
and does not authorize the default-branch bootstrap or any benchmark stage.

## Actual-runtime and registration-quorum remediation evidence

The executable source is sealed at `ef502cda94e4e6ccfc7d2266da5600b452a89a84` / tree
`790542c0b496df709553e23a0376edb750fec73d`. The evidence files below are a non-executable overlay;
they do not change that qualified source.

- [x] **C2-038** Replace declarative fault outcomes with actual native runtime transitions, WAL
  durability/recovery, state/effect roots and full canonical traces for worker, validator, storage
  and region failures.
- [x] **C2-039** Compile one exact 15-plan non-primary candidate catalog and execute it twice in both
  push and PR contexts through Python, Java Netty, the native runtime and OS counters. Runs
  `33743852344` and `33743857202` agree on candidate Definition
  `sha256:3d9b4144436c6c91e4bccfa41dbb3b340238c6bef7a86113388f7dbc6dd8d247`, catalog
  `sha256:f7e1128958a8e20bc54456fe3258c910e4470fdb99710fdb20c1547a81a42ded`, all 15 plan IDs,
  stage identities `sha256:381424850a1108a50bcffc5c127d89147581a9e84d733d9970d0784d4c50ce92`
  and semantic root `sha256:f01ce975a044ab596f970f32263ebbeb67a6ba5d65b79889635e81ab401b6df4`.
  Each context retains 30 full raw evidence files. This candidate is explicitly
  `TEST_ONLY_DETERMINISTIC_EPHEMERAL`; it is not an authoritative Definition or catalog.
- [x] **C2-040 source contract** Require raw GitHub API snapshots, artifact archive digests and a
  detached three-controller Ed25519 quorum before constructing a verified zero-execution workflow
  registration object. The actual registration receipt remains absent until the separately reviewed
  inert bootstrap exists on `main`; no source artifact here asserts otherwise.
- [x] **C2-041** Requalify the sealed source with architecture/formal regression, exact-tree GCC
  TSan job `100611747966`, 48 successful current-head checks, two exact-catalog Stage C runs and the
  designated RTX 3070 QLoRA/NF4 probe. The machine-readable chain is:
  `evidence/campaign-02-actual-stagec-registration-hardware-qualification.json`
  (`sha256:0f6bf901e513e87da6d74d23b53210be89b99d23eb60d68f0af05a3246ce8c82`),
  `evidence/campaign-02-actual-stagec-registration-exact-source-qualification.json`
  (`sha256:4039dd555bb2122188e7b9d43ae99aaa28a5283d6d525d3d728f5f82766260b7`) and
  `evidence/campaign-02-actual-stagec-registration-exact-source-ci-receipt.json`
  (`sha256:3abd74b25d04e98687a413cc5a889ade79f4dc67f211c7ef6f1636e06c6bf7e7`).

The independent review of PR #20 reopened the checked C2-038 and C2-040 entries above: they record
the historical `ef502cda...` qualification, not acceptance of the terminal semantics. The corrective
generation is tracked separately so those immutable receipts are not rewritten.

- [x] **C2-042** Complete every successful worker-loss and eventual-synchrony path through an exact
  Feature 003 `AggregateRootQC`, deterministic Feature 008 apply work, persisted 2f+1 apply votes,
  verified `ApplyQC` and durable current-pointer compare-and-set. `APPLIED` is emitted iff the new
  checkpoint is current; missing, foreign or conflicting ApplyQC evidence fails closed.
- [x] **C2-043** Drive native ticket/vote/deadline admission from the measured Netty causal schedule.
  Evidence binds lost workers and tickets, exact ISC membership, per-domain capacity, message ticks,
  GST, quorum ticks and hard-deadline AbortQC. Distributed 10% loss applies without `pi_d`
  renormalization; concentrated mandatory `code`-domain loss certifies abort with the parent pointer
  unchanged.
- [x] **C2-044** Version the workflow registration receipt/signature contract so `completed` status,
  `success` conclusion and run/artifact creation, update, completion and expiry timestamps are bound
  to raw GitHub API bytes and each detached Ed25519 vote. The artifact name also binds the exact
  `run_attempt`; failed, cancelled, timed-out, in-progress, stale, future or prior-attempt artifact
  registrations are rejected.
- [x] **C2-045** Seal this corrective executable source and supersede C2-041 with exact-source,
  repeated 15-plan candidate, designated-GPU, sanitizer, TSan, C++20/C++23, formal regression and
  terminal CI receipts from the same immutable commit/tree.

The corrective executable source is sealed at `afdf1a23bff428a07961beb21132f89fd4e1af76` / tree
`051f7ec7087ae08a8371c7830b827c944b9c58a7`. Evidence overlay `5126517fbabdfb9155693f9f91851370c2618924`
changed only the two then-current qualification files and passed 48 mandatory checks with four
governance-policy skips, zero failures and zero pending checks. Exact 15-plan candidate runs
`33757104390` (`push`) and `33757109568` (`pull_request`) agree on catalog
`sha256:f1253fc8b4a65d6cb706f7a7000cc7a3d6716fafdb211b2505b111bce19c58f4` and semantic root
`sha256:6b2c6f3cd4d58e7e2a050258f177a12c6ec8a28c60251f5fa39792183c7acd01`; each retained 30 raw
evidence files. Workflow `33757123617` binds the 191-case portable corpus, exact-source TSan and
designated-GPU evidence. The separate corrective chain preserves the historical Definition v4
inputs byte-for-byte:

- `evidence/campaign-02-causal-stagec-terminal-registration-hardware-qualification.json`
  (`sha256:7c96c1c5636ff47e76a31eddf184834aee2157d2638c042cd94e1f6061dbbddf`);
- `evidence/campaign-02-causal-stagec-terminal-registration-exact-source-qualification.json`
  (`sha256:639c0bf9180c170c722b1d959c4ac4b2ec244aafc42b4dafe466b53b88088dc6`);
- `evidence/campaign-02-causal-stagec-terminal-registration-exact-source-ci-receipt.json`
  (`sha256:92befa257356504ef00e9549036769d9631db2a442685bf4c72bf2d42972eca1`).

The source-side C2-037 work is complete, but operational default-branch registration remains the
next separate governance operation. Definition votes remain `0`, attestation and execution
authorization remain absent, authoritative catalog construction has not occurred, primary
observations remain `0`, Feature 010 remains `NO_GO`, and Feature 011 remains blocked.

## Concentrated-loss production projection after repeated PR #20 review

The repeated independent review found that the `afdf1a23...` source and `034e37a...` terminal
candidate executed only seven fault events per plan. That lineage is retained as historical
qualification evidence but cannot close C2-043 or C2-045. The following corrective generation
does not authorize a benchmark stage or alter any governance STOP.

- [x] **C2-046** Version the source-bound executable fault trace and execute concentrated mandatory
  `code`-domain worker loss through Python → Java Netty → native sidecar → native AbortQC → typed
  Python evidence. Require loss of workers/tickets `000` and `001`, remaining capacity
  `code=3,text=5`, no aggregate/apply votes, three abort votes at the exact hard deadline and an
  unchanged current pointer.
- [x] **C2-047** Remove the actor/action-only sidecar outcome oracle. Native code derives the
  observed terminal only from the delivered causal schedule, runtime state, quorum and domain
  capacity; the immutable profile expectation remains an external Python assertion.
- [x] **C2-048** Add a full causal projection ID to every candidate plan record and require equal
  causal roots across the two executions in each push and pull-request context. Version the typed
  plan evidence and candidate schemas without rewriting historical schemas.
- [ ] **C2-049** Seal the replacement source, re-run designated-GPU, portable, sanitizer, TSan,
  C++20/C++23 and formal qualification, publish two exact 15-plan/eight-fault executions in both
  push and pull-request contexts, bind the immutable terminal HEAD externally, and update PR #20
  title/body to the exact terminal lineage and governance STOP.

The replacement executable source is sealed at
`188de41c66d4db6335ae9e9145de91f58f1863b4` / tree
`06f3297157f64f7dee63f3420be3475cae705030`. Its non-primary designated-GPU qualification is
`evidence/campaign-02-concentrated-loss-hardware-qualification.json`
(`sha256:797780a95cb6853db958c630b225cb3cc05ffc9db1a1a1e66ec13fa820cfcb7e`), and its 192-case portable
source qualification is `evidence/campaign-02-concentrated-loss-exact-source-qualification.json`
(`sha256:256804475a0b3d25d6e8dd27684af4537f92fb49c6de01ae81631f22b46f971c`). Both retain zero primary
executions and observations. C2-049 remains open pending remote TSan/sanitizer/formal/C++ lanes,
the final push and pull-request candidate artifacts and external terminal-lineage binding.

Until C2-049 is closed, PR #20 remains `DRAFT / CHANGES_REQUIRED / DO NOT MERGE / DO NOT MARK
READY`. C2-023 and C2-024 remain unauthorized, Definition votes remain `0`, attestation and
execution authorization remain absent, authoritative catalog construction has not occurred,
primary observations remain `0`, `BenchmarkResultQC` remains absent, Feature 010 remains `NO_GO`
and Feature 011 remains blocked.

## Unconditional STOP conditions

- No old Definition or Stage A artifact may be edited, overwritten or linked as a new gate result.
- No primary observation, Stage A/B/C, real-WAN run or `BenchmarkResultQC` may be produced here.
- Seeds, arms, thresholds, metric direction, missing/outlier policy, model/tokenizer, data revisions,
  domain mixture, network/fault profiles and the decision function remain unchanged.
- A mutable dependency, unbound evaluator/runner/writer, manually supplied observation JSON or
  token-plan mismatch fails closed.
