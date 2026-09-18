# Feature Specification: Preregistered WAN, BFT Safety and Model-Quality Benchmark

**Feature Branch**: `010-wan-benchmark-and-quality`  
**Created**: 2026-08-23  
**Status**: Reconciled — implementation in progress
**Depends on**: `009-qlora-8gb-mode`

## Authoritative baseline

Feature 010 is based on the exact merged Feature 009 lineage:

- merge commit: `007eb08aa3aaee849128ba428274a9fbda561bf8`;
- verified source: `f43e39fa1c60d256bab5d7e37e0756f28438d5e4`;
- evidence overlay: `a5e73b41feb2dad73aa11d810d0c700c548e11ba`;
- final compatibility report SHA-256:
  `95b312b45f3c2df4293ceaa0cbb16dd1e89c5d12a86c890211353a45798516ef`;
- inherited formal semantics:
  `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

The formal-impact classification is `REGRESSION_ONLY`. A benchmark must not add a protocol action,
certificate-parent edge, failure terminal, durability outcome or current-state transition. Discovery
of any such behavior is a semantic STOP and requires a new Feature 000 Formal GO before implementation
continues.

## Summary

Before a real multi-region pilot, DeltaReduce v1 must prove more than training loss or one successful distributed run. This feature defines a preregistered, token- and domain-matched benchmark that evaluates:

- bit-for-bit protocol determinism;
- BFT safety and bounded liveness under the declared fault/network model;
- model quality relative to an agreed reference at equal data/token exposure;
- fixed-point and robust-aggregation quality impact;
- WAN communication, GPU utilization and synchronization overhead;
- content-addressed P2P behavior and seed-loss resilience;
- QLoRA 8 GiB qualification where that mode is selected;
- recovery, auditability and reproducibility of all evidence.

The benchmark configuration, hypotheses, comparison arms, thresholds, exclusions and decision rule are frozen and certified before execution. Thresholds cannot be relaxed after results are observed. Performance targets are reported as measured outcomes, not assumed capabilities.

A successful benchmark yields a `BenchmarkResultQC` with decision `GO`. Any failed mandatory gate yields `NO_GO`; there is no partial or operator-overridden GO for feature 011.

`BenchmarkDefinitionQC` and `BenchmarkResultQC` are benchmark-governance attestations. They authorize
experiment execution and Feature 011 admission respectively; they are not DeltaReduce runtime
certificates, do not extend the
`ISC → EC → APC → ParameterShardQC → AggregateRootQC → ApplyQC` lineage, and cannot change the
current checkpoint.

## Benchmark Arms

Each applicable experiment uses the same parent model, tokenizer, dataset/domain manifest, domain mixture, total eligible ticket/token budget, fixed `B/H`, optimizer policy, evaluation set and seed policy.

1. **Single-process scientific reference**: direct local training/evaluation used to establish the quality comparison, with its arithmetic/reproducibility class declared explicitly.
2. **Flat DeltaReduce reference**: feature-003 integer aggregation over the exact certified input and APC plan.
3. **Hierarchical DeltaReduce**: feature-006 regional/parameter committees over the same inputs and coefficients; protocol output must equal the flat integer result exactly.
4. **Certified full-model mode** or **certified QLoRA adapter mode**: selected before the run according to the benchmark definition and hardware feasibility.
5. Optional ablation arms may vary fixed-point scale, robust policy or topology only when preregistered as separate immutable configurations; they cannot replace the mandatory primary arm after execution begins.

## Gate Classes

### Gate A — Protocol determinism and certificate safety

All honest validators/aggregators/apply validators must produce identical canonical bytes and hashes. This gate has no numerical tolerance.

Mandatory attacks include:

- conflicting `RoundConfig`, commitment and validator votes;
- seed request/reveal before ISC;
- commitment/availability mutation and replay;
- mixed ISC/EC/APC parameter shard (Frankenstein update);
- missing/duplicate/overlapping domain×parameter shards;
- unsafe coefficient/accumulator bounds and runtime overflow attempts;
- conflicting ApplyQC/current-checkpoint proposal;
- certification downgrade in P2P publication.

### Gate B — Scientific quality

Quality is evaluated at equal preregistered token and domain exposure, not equal wall-clock time or worker count.

Mandatory measurements include:

- validation loss and perplexity;
- downstream task metrics selected and frozen in the benchmark definition;
- quality after any preregistered instruction-tuning or post-training phase;
- local/aggregate update norm and direction diagnostics;
- per-domain quality and contribution coverage;
- fixed-point quantization and robust-filtering ablations where required.

The exact acceptable deltas, confidence method, number of seeds/runs and missing-run policy are part of `BenchmarkDefinition`. The specification does not claim parity before measured evidence exists.

### Gate C — WAN efficiency and P2P distribution

Under deterministic network profiles and then the approved real-WAN pre-pilot environment, measure:

- wall-clock time and time-to-quality;
- useful training compute time;
- GPU utilization;
- bytes per eligible ticket and per training token;
- worker upload/download, intra-region and inter-region bytes;
- p50/p95/p99 ticket, commitment, availability, certificate, reduce, apply and object-distribution latency;
- BFT vote/QC and robust-plan overhead;
- initial publisher egress and peer-contributed bytes;
- completion after initial seed loss;
- retransmitted, duplicate, corrupt and unavailable bytes.

Engineering targets such as network share below 10–15% and GPU utilization above 75–80% may be preregistered as goals for an exact profile. They are not treated as achieved until the report contains measurements.

### Gate D — Resilience and BFT fault model

The benchmark distinguishes safety from liveness:

- safety must hold under up to `f` Byzantine validators and arbitrary tested message ordering/duplication/replay;
- liveness is evaluated only under the preregistered eventual-synchrony, quorum, storage-availability and deadline assumptions;
- worker loss, storage-peer loss, validator/process crash, regional delay/partition and restart are injected deterministically;
- approximately 10% worker loss is a mandatory scenario, but success is conditioned on declared per-domain ticket/quorum capacity;
- when assumptions are not met, the expected outcome is a deterministic abort with unchanged current checkpoint, not a guessed result.

### Gate E — Operational reproducibility and evidence integrity

Every run emits immutable configuration, environment, image, source, data, certificate, telemetry and result manifests. Independent replay must verify hashes and reproduce every deterministic decision from recorded inputs.

## User Scenarios & Testing

### US1 — Preregister the complete benchmark before observing primary results (Priority: P1)

A research operator submits one benchmark definition and evidence policy to a review/validator committee.

**Independent Test**: after `BenchmarkDefinitionQC`, any change to workload, thresholds, exclusions, seed count, domain mixture, fault profile or decision logic produces a new identity and cannot be used to judge the existing run set.

**Acceptance Scenarios**:

1. **Given** complete workload, arms, thresholds and evidence policy, **When** `2f_b+1` benchmark validators sign the canonical definition, **Then** one `BenchmarkDefinitionQC` finalizes.
2. **Given** a missing quality threshold, undefined metric direction, mutable external dataset revision or unbounded retry/exclusion rule, **When** validation runs, **Then** preregistration fails.
3. **Given** a finalized definition, **When** any evaluation threshold or primary-arm setting changes, **Then** a new benchmark version/QC is required and prior results remain attached to the old definition.
4. **Given** a proposed adaptive `H`, stale-update arm or FP consensus fallback as the primary implementation, **When** the definition is validated, **Then** it is rejected as incompatible with DeltaReduce v1.

### US2 — Reproduce exact protocol results under WAN and message permutations (Priority: P1)

The harness runs the primary fixed-ticket workload through flat and hierarchical BFT paths with deterministic network/failure traces.

**Independent Test**: repeated runs and independent validator processes produce the same ticket, certificate, parameter, aggregate, apply and checkpoint hashes; hierarchy equals flat integer reference bit-for-bit.

**Acceptance Scenarios**:

1. **Given** identical immutable inputs and fault trace, **When** the run is repeated, **Then** every consensus-visible hash and terminal decision matches.
2. **Given** different network arrival order, **When** quorum/liveness assumptions still hold, **Then** the finalized result remains identical.
3. **Given** a failed liveness assumption, **When** the deadline resolves, **Then** the run aborts with the parent checkpoint unchanged and auditable reason.
4. **Given** flat and hierarchical runs over the same ISC/EC/APC, **When** compared, **Then** every domain/parameter integer aggregate byte matches exactly.

### US3 — Measure model quality at equal token/domain exposure (Priority: P1)

Researchers compare the scientific reference with the certified DeltaReduce primary arm.

**Independent Test**: the report joins only runs matching the preregistered workload/evaluation identity, checks token/domain equality, computes the specified statistics and determines pass/fail without manual metric reinterpretation.

**Acceptance Scenarios**:

1. **Given** unequal total eligible tokens or domain ticket counts, **When** comparison is attempted, **Then** it is rejected or handled only by the preregistered normalization/exclusion rule.
2. **Given** complete matched runs, **When** quality analysis runs, **Then** validation, downstream, post-training and per-domain metrics use exact declared direction/threshold/statistics.
3. **Given** normal pretraining loss but failed downstream/post-training threshold, **When** decision is computed, **Then** Gate B fails.
4. **Given** missing required seed/evaluation artifact, **When** decision is computed, **Then** the missing-run policy applies automatically; it cannot be silently omitted.

### US4 — Demonstrate Byzantine and Frankenstein rejection (Priority: P1)

The fault harness actively proposes malformed/conflicting certificate and parameter views.

**Independent Test**: every mandatory attack fails at the expected parentage/quorum/arithmetic boundary and no invalid ApplyQC or current checkpoint is created.

**Acceptance Scenarios**:

1. **Given** one parameter shard QC from another APC/view, **When** AggregateRootQC assembly runs, **Then** it is rejected as a mixed-view shard.
2. **Given** up to `f` equivocating validators, **When** conflicting proposals are delivered, **Then** at most one value can finalize for each certificate/height.
3. **Given** unsafe fixed-point coefficients or runtime overflow input, **When** APC/reduce/apply validation runs, **Then** the run aborts without saturation or current-pointer change.
4. **Given** a seed transcript not bound to the finalized ISC, **When** EC/APC verification runs, **Then** the chain is invalid.
5. **Given** a weaker certificate attached to a current-checkpoint object, **When** P2P policy verification runs, **Then** publication/use is rejected.

### US5 — Measure WAN/P2P efficiency and controlled churn (Priority: P1)

The harness executes preregistered latency, bandwidth, jitter, loss, reordering, disconnect, region-delay and seed-loss profiles.

**Independent Test**: metrics reconstruct all bytes and phase durations, the initial-seed-loss object still completes when remaining verified piece union is complete, and the 10% worker-loss scenario produces the predeclared complete-or-abort result.

**Acceptance Scenarios**:

1. **Given** the network profile, **When** the run completes, **Then** useful compute, communication, consensus, robust, distribution and idle time are accounted without overlap double-counting under the declared method.
2. **Given** initial publisher loss after sufficient replication, **When** a new peer fetches, **Then** it reconstructs exact certified bytes from remaining peers.
3. **Given** 10% worker loss with sufficient per-domain completion/quorum, **When** input freeze occurs, **Then** the run follows its exact ticket/missing-work policy and completes safely.
4. **Given** concentrated loss that violates a mandatory domain/quorum rule, **When** deadline resolves, **Then** the run aborts rather than renormalizing `pi_d` or fabricating updates.

### US6 — Produce an immutable GO/NO_GO decision (Priority: P1)

After all mandatory run manifests are sealed, evaluator validators execute the deterministic decision function.

**Independent Test**: independent evaluators over the same evidence root produce the same gate table, report bytes and decision; `GO` requires every mandatory gate to pass.

**Acceptance Scenarios**:

1. **Given** complete verified evidence and all mandatory gates passing, **When** `2f_b+1` evaluators sign the result body, **Then** `BenchmarkResultQC(decision=GO)` finalizes.
2. **Given** any mandatory gate failure, missing evidence or unverifiable artifact, **When** decision runs, **Then** the only valid decision is `NO_GO` with exact failed gates.
3. **Given** an operator annotation or exception, **When** report is built, **Then** it may be attached as commentary but cannot change the deterministic decision.
4. **Given** a GO report from another definition, code/image/data root or expired compatibility policy, **When** feature 011 checks it, **Then** it is rejected.

## Edge Cases

- Reference and distributed runs process equal total tokens but different domain counts.
- Early aborted ticket appears in worker telemetry but not ISC.
- One seed/run is missing, duplicated or uses another evaluation version.
- Metric direction is inverted or threshold unit differs.
- Confidence interval straddles a preregistered boundary.
- Hardware thermal throttling or unrelated load changes utilization.
- Network and compute intervals overlap; accounting method must avoid double counting.
- BFT safety passes but liveness fails due to fewer than `2f+1` validators.
- Validator process restarts with stale vote journal.
- Storage AC was valid but shard becomes unavailable during aggregation.
- P2P union loses one piece after initial seed failure.
- One region loses all tickets for a mandatory domain.
- Byzantine update passes robust policy but degrades quality within/outside threshold.
- Benchmark software/image changes between arms.
- Report evaluator has incomplete telemetry but complete model metrics, or vice versa.
- GO report is validly signed but outside the pilot compatibility window.

## Requirements

### Preregistration and run identity

- **FR-001**: `BenchmarkDefinition` MUST bind source commit/tree, build/image/SBOM, protocol versions, model/mode, base/tokenizer/schema, dataset/domain manifest, fixed ticket plan, `B/H`, `pi_d`, optimizer/fixed-point/robust/apply profiles, topology, validator/storage/peer sets, network/fault profiles, seeds, metrics, thresholds, statistics, exclusions, retry policy, evidence retention and decision function.
- **FR-002**: Every external dataset/model/evaluation dependency MUST resolve to immutable content/revision hashes and approved license/access policy before definition certification.
- **FR-003**: `BenchmarkDefinitionQC` MUST require `2f_b+1` unique signatures from a declared `3f_b+1` benchmark-review validator set.
- **FR-004**: Definition validation MUST reject missing metric direction/threshold, mutable dependencies, undefined missing-run policy, adaptive/stale primary behavior and any float consensus fallback.
- **FR-005**: Any post-QC change creates a new definition identity; results cannot migrate between definitions without an explicit immutable compatibility rule.
- **FR-006**: Each run MUST have a deterministic `RunManifest` binding definition, arm, repetition/seed, environment, actual worker/validator/storage/peer inventory, trace, start parent, tickets and all output/evidence roots.
- **FR-007**: Run admission MUST fail if code/image/config/data/model/profile identity differs from the certified definition beyond a declared compatibility allowance.

### Determinism and safety gates

- **FR-008**: Mandatory protocol comparisons MUST use byte/hash equality for tickets, certificates, parameter results, AggregateRootQC, ApplyQC and checkpoints; tolerances are forbidden.
- **FR-009**: Flat and hierarchical reducers MUST process the same ISC/EC/APC and produce identical domain/parameter integer outputs.
- **FR-010**: The benchmark MUST repeat the four-independent-validator/aggregator determinism gate from feature 003 at the primary workload scale.
- **FR-011**: Mandatory attack corpus MUST include conflicting config/commit/votes, seed-before-ISC, mutated AC, mixed-view shard, incomplete/duplicate aggregate, unsafe accumulator, conflicting apply and distribution certificate downgrade.
- **FR-012**: No mandatory attack may produce a valid descendant certificate, ApplyQC or current-pointer mutation.
- **FR-013**: Safety evaluation MUST distinguish Byzantine threshold, validator-set epoch, signature uniqueness and quorum intersection.
- **FR-014**: Liveness success MUST be judged only under the exact preregistered eventual-synchrony, quorum, availability and deadline assumptions.
- **FR-015**: When liveness assumptions fail, expected safe abort/current-parent preservation MUST be tested and considered distinct from safety failure.

### Scientific quality gates

- **FR-016**: Primary quality comparison MUST match total eligible token exposure and exact per-domain ticket/data policy, unless the definition preregisters a mathematically explicit alternative comparison.
- **FR-017**: Reference and DeltaReduce arms MUST share parent model/tokenizer/data/evaluation/optimizer intent and differ only in the declared distributed/fixed-point/robust mechanisms.
- **FR-018**: Required quality metrics MUST include validation loss/perplexity, preregistered downstream metrics, per-domain results and any required post-training/instruction-tuning evaluation.
- **FR-019**: Metric implementation/version, direction, aggregation, confidence/statistical method, number of runs/seeds and pass threshold MUST be fixed by the definition.
- **FR-020**: Training loss alone MUST NOT satisfy Gate B when downstream or post-training metrics are mandatory.
- **FR-021**: Missing, crashed, invalid or outlier runs MUST be handled only by the certified missing/exclusion policy; manual silent omission is forbidden.
- **FR-022**: Fixed-point and robust-filtering effects MUST be attributable through preregistered diagnostics/ablations when required by the definition.
- **FR-023**: Quality evidence MUST preserve raw metric artifacts, evaluator config/hash and exact join to run/certificate/checkpoint identity.

### WAN, P2P and resilience gates

- **FR-024**: Network simulator profiles MUST define RTT, bandwidth, jitter, loss, reordering, duplication, disconnect, region partition and duration/seed; tests MUST run without public internet.
- **FR-025**: Real-WAN pre-pilot runs MUST record measured path conditions and preserve the same workload/gate identity or a certified environment variant.
- **FR-026**: Telemetry MUST separately account for local compute, encode/upload, commitment/availability, ISC/seed/EC/APC, regional/global reduce, ApplyQC, P2P download and idle/wait phases.
- **FR-027**: Byte accounting MUST include worker, storage, regional, global, validator-vote/certificate and P2P traffic and define treatment of retries/duplicates.
- **FR-028**: GPU utilization, wall-clock, time-to-quality, bytes/token and p50/p95/p99 phase latencies MUST be reported for applicable arms.
- **FR-029**: Engineering targets such as network-share/GPU-utilization MUST be configuration-bound and reported as pass/fail only after measurement.
- **FR-030**: Initial-seed-loss scenario MUST prove exact reconstruction when remaining verified piece union is complete and deterministic `PIECE_UNAVAILABLE` otherwise.
- **FR-031**: Mandatory churn MUST include approximately 10% worker loss, validator/process crash/restart, storage-peer loss and region delay/partition at declared concentrations.
- **FR-032**: Worker loss MUST never cause adaptive `H`, speed weighting, post-freeze input mutation, implicit `pi_d` renormalization or fabricated updates.
- **FR-033**: Recovery/retry MUST preserve vote, certificate, commitment, residual and current-pointer idempotency.

### Evidence and decision requirements

- **FR-034**: Every configuration, artifact, certificate, metric stream, log summary and report MUST be content-addressed and connected through an immutable evidence manifest.
- **FR-035**: Evidence collection MUST record source commit/tree, build/image digest, SBOM, dependency lock, environment, hardware, time-sync status and secret-redacted configuration.
- **FR-036**: Independent offline verification MUST check all hashes/signatures/QCs, run identities, gate inputs and report calculations without network dependency.
- **FR-037**: `BenchmarkResult` MUST contain definition/evidence roots, run inventory, gate table, measured values, failed/missing evidence, limitations and deterministic `GO` or `NO_GO`.
- **FR-038**: Decision function MUST return `GO` only if every mandatory gate passes and all required evidence verifies.
- **FR-039**: `BenchmarkResultQC` MUST require `2f_b+1` unique evaluator signatures over the exact result body.
- **FR-040**: An operator exception, narrative or threshold change cannot convert `NO_GO` to `GO`; it requires a new definition and rerun.
- **FR-041**: Feature 011 prerequisite verification MUST bind the exact expected definition/result/evidence compatibility and accept only `decision=GO`.
- **FR-042**: CLI MUST provide benchmark define/validate/run/collect/verify/report/decision commands.
- **FR-043**: Metrics/report generation MUST be reproducible and must not query mutable external dashboards as the sole source of evidence.

### Non-Functional Requirements

- **NFR-001**: Mandatory safety/determinism benchmark is deterministic, offline-capable and timeout-bounded.
- **NFR-002**: Primary quality evidence includes the preregistered number of independent repetitions/seeds; a single favorable run cannot substitute.
- **NFR-003**: Evidence verifier MUST fail closed on missing, altered, unsigned or incompatible artifacts.
- **NFR-004**: Reported targets and measured outcomes MUST be clearly distinguished.
- **NFR-005**: No benchmark task may weaken Constitution 2.1.0 to improve performance.
- **NFR-006**: BenchmarkResultQC certifies evidence evaluation, not a universal convergence or security guarantee beyond the tested definition.

### Key Entities

- **BenchmarkDefinition / BenchmarkDefinitionQC**: immutable hypotheses, workload, thresholds, fault profiles and decision policy.
- **RunManifest / EnvironmentManifest / NetworkTrace**: exact execution identity and conditions.
- **QualityEvidence / SafetyEvidence / EfficiencyEvidence / ResilienceEvidence**: content-addressed gate inputs.
- **EvidenceManifest**: complete immutable evidence graph.
- **BenchmarkResult / BenchmarkResultQC**: deterministic gate table and GO/NO_GO certification.
- **CompatibilityPolicy**: exact rule allowing feature-011 prerequisite use.

## Success Criteria

- **SC-001**: Definition is complete, immutable and certified before primary results are observed.
- **SC-002**: Repeated independent validators produce identical protocol/checkpoint hashes; hierarchy equals flat reference bit-for-bit.
- **SC-003**: Every mandatory Byzantine/Frankenstein/overflow/downgrade attack is rejected without invalid ApplyQC/current mutation.
- **SC-004**: Quality analysis uses equal token/domain exposure and passes every preregistered validation/downstream/post-training threshold.
- **SC-005**: WAN/P2P report contains complete byte/time/utilization/latency accounting and passes the definition's mandatory targets.
- **SC-006**: Initial-seed-loss and declared churn/failure scenarios yield exact expected complete-or-safe-abort outcomes.
- **SC-007**: Independent evidence verification reproduces all gate values and the same decision.
- **SC-008**: `BenchmarkResultQC(decision=GO)` exists only when every mandatory gate passes; otherwise the authoritative result is `NO_GO`.

## Assumptions

- Benchmark validator/evaluator membership is permissioned and independently reviewable.
- Exact models, datasets, downstream tasks and numeric thresholds are chosen during implementation preregistration, not invented by this generic architecture spec.
- Eventual-synchrony and availability assumptions are explicit per scenario.
- Scientific reference arithmetic may differ from consensus arithmetic, but comparison identity and reproducibility class are declared.

## Out of Scope

- Changing architecture or thresholds after observing results.
- Claiming universal Byzantine robustness, convergence or quality beyond tested profiles.
- Permissionless validators, economics or Sybil resistance.
- Production-scale pilot operations; those begin only in feature 011 after GO.
- Adaptive/stale training as a fallback for failed efficiency gates.
