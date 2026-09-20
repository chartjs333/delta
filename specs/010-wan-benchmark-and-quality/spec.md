# Feature Specification: Reconciled WAN Benchmark and Quality Gate

**Feature branch**: `feature/overnight-010-011-requalification`
**Reconciled**: 2026-09-20
**Status**: `STOPPED_BEFORE_PRIMARY_EXECUTION` / local working version remains ready
**Exact base**: `7a9faf852e0ccae4d25fdc363fbf39ecf1719341`
**Base tree**: `2ae9ad2ad0064cfb65c956464dc737c2ab03034a`
**Formal semantics**: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

## Authority and boundary

This directory is the proposed current-lineage SpecKit authority for Feature 010.
It becomes current-main authority only if this candidate is reviewed and merged.
Historical draft PRs are audit inputs only. They are not merged, cherry-picked, or
treated as a composite release. The immutable inventory and current gate state are
recorded in `evidence/historical-input-inventory.md` and
`evidence/reconciliation-status.json`.

The accepted formal report is `formal/reports/formal-verification-report.json`
(SHA-256 `3e2e2344a038b2c902b06d275fb3e3820f95e5a780c2750e5c1a367dd82936d7`).
This reconciliation has formal-impact classification `NONE`: it adds no protocol action, vote
context, certificate parent edge, failure terminal, durability outcome, availability
rule, arithmetic precondition, or current-state transition. Discovery of any such
change is an unconditional STOP and returns the work to Feature 000.

`BenchmarkDefinitionQC` and `BenchmarkResultQC` are experiment-governance
attestations. They never enter the runtime certificate lineage and cannot advance
the current checkpoint.

## Current decision

The single-host working version at the exact base remains qualified. It does not
establish Campaign 02 governance, a primary scientific observation, physical-CUDA
qualification for a current-lineage Campaign 02 environment, real-WAN evidence, or
multi-region pilot readiness.

Feature 010 therefore has no GO checkpoint:

- `FEATURE010_GO_CHECKPOINT_SHA = null`;
- primary scientific observations: `0`;
- approved real-WAN runs: `0`;
- `BenchmarkResultQC(decision=GO)`: absent;
- Feature 011 admission: blocked.

Historical NO_GO/STOP records remain immutable. This specification does not convert
them into PASS and does not synthesize a replacement result.

The current base also does not contain a current-lineage Feature 010 contract set,
campaign runner, stage-receipt chain, gate analyzers or ResultQC implementation.
Those existing T002–T034/T037–T049 and HR010 task identities are restored as open
work in `tasks.md`, `runtime-tasks.md` and `task-map.md`. The implementation may be
rebuilt or selectively reimplemented only through reviewed current-lineage work;
this reconciliation imports none of the historical draft implementation.

## Historical inputs

| Input | Preserved status | Permitted use |
| --- | --- | --- |
| PR #11 `881301d8443c667a478617cc663d1450aee9777a` | NO_GO; stopped before primary scientific execution | Audit of failed preregistration and exactness work only |
| PR #19 `b2af7b926f3525494bb5634dbedcca3fe97051e1` | Governance STOP | Design and qualification lessons only |
| PR #28 `84b337892cb70d0ce9823ef2d64fab572752b145` | Unsigned zero-execution registration | Historical provenance only; no authority |
| PR #29 `de3348fdcbd527046d5b66bc6d8c90df098d5aa8` | Proposed custody policy; not adopted | Requirements source only |
| PR #30 `670b58f4c400f5c8904ca40ba9cf3a2072e98d78` | Non-authoritative demo | No primary, WAN, governance, or pilot evidence |

The current base already contains the manual registration/Stage-A caller
`.github/workflows/campaign02-stage-a-bootstrap.yml` with blob
`a60fd3fc44e33c5abcce27586fd7c67e7d16abe9`. Its default `REGISTER_ONLY` mode
performs no experiment execution, but its explicit `EXECUTE_STAGE_A` mode is not
inert. The workflow remains non-authoritative and that execution mode must not be
invoked without every gate below. Generic model/data
plugin files that independently reached `main` are ordinary working-version code;
their presence does not import PR #30's demo claims.

## Mandatory pre-execution gates

No primary, Stage A/B/C, quality, emulated-WAN, or real-WAN execution may start
until all of the following are frozen and independently reviewed on the current
lineage.

1. **Exact lineage**: source commit/tree, build, protocol/schema, formal report,
   runtime profile, model/data/evaluator identities, and evidence policy are bound
   to one reviewed candidate.
2. **Independent governance**: for `f_b=1`, four real controller authorities have
   independently generated Ed25519 keys and separate signing, administration,
   deployment, backup, and recovery control. Four authenticated owner/key bindings,
   all six pairwise independence reviews, a named governance authority, and an
   independent custody reviewer are required.
3. **Bootstrap quorum**: one canonical four-member validator set with quorum three,
   exactly three mapping votes, and exactly three registration votes sign the
   canonical message bytes. Artifact availability, expiry, and actual submission
   times are checked at admission. Private keys remain inside their custody
   boundaries.
4. **Separate authorities**: bootstrap registration is zero-execution only. A
   current-lineage Benchmark Definition attestation and a separate execution
   authorization are still required. Merge approval or verifier PASS cannot create
   either authority.
5. **Physical scientific environment**: the pinned CUDA/PyTorch/driver/runtime,
   supported physical GPU, immutable model/data/evaluator content and licenses, and
   exact ticket/token/domain plan are available. A CPU-only environment, mock,
   estimate, or historical GPU result cannot satisfy this gate.
6. **WAN authority**: approved real endpoints in distinct network/administrative
   regions, credentials, TLS identities, routing/failure-domain inventory, and
   evidence collection are available. Localhost, VM networks, VPN labels, or
   `tc/netem` are not real-WAN evidence.

Every eligible primary DeltaReduce observation must traverse the one frozen
polyglot path: Python training and normalization, Java/Netty opaque transport and
backpressure, and native C++ validation/state/WAL with persist-before-expose. Its
stage receipts must bind ticket, commitment, certificate, effect, checkpoint,
model/evaluator and run identities. A Python-only observation plus a separate
conformance run is ineligible.

## Frozen benchmark gates

### Gate A — exactness and safety

- Python, C++, and Java agree on canonical bytes, hashes, status codes, and negative
  parsing outcomes.
- GCC/Clang, direct/copy FFM, flat/hierarchical integer reduction, and honest
  validator state/effect roots agree exactly.
- ASan/UBSan, a separate TSan lane, fuzzing, durability/replay, Netty
  lifetime/backpressure, and embedded/sidecar policy all pass.
- Conflicting, replayed, incomplete, mixed-view, overflow, downgrade, and
  conflicting-apply attacks never create a descendant QC or current mutation.

### Gate B — scientific quality

- Reference and DeltaReduce arms use the same parent model, tokenizer, immutable
  data/domain manifest, optimizer intent, ticket plan, total eligible tokens, fixed
  `B/H`, seeds, evaluators, thresholds, statistics, and missing-run policy.
- Validation loss/perplexity, downstream/post-training, per-domain, fixed-point,
  and robust-filter diagnostics all use the preregistered direction and threshold.
- Synthetic, fixture, dry-run, caller-supplied, or post-hoc observations are
  ineligible.

### Gate C — simulated WAN, P2P, and resilience

- Every network profile is immutable and every result is labeled `SIMULATED`.
- Phase timing, byte accounting, GPU utilization, P2P seed loss, approximately 10%
  dispersed/concentrated worker loss, validator/storage restart, partition, and
  safe-abort outcomes are measured and independently verified.
- Simulation cannot satisfy Gate D.

### Gate D — approved real WAN

- The exact workload and compatible environment run on approved real endpoints in
  distinct regions with measured path conditions.
- TLS identity, endpoint, clock, routing, failure-domain, credential, and source
  provenance are captured without exposing secrets.
- Required real-WAN quality, efficiency, resilience, recovery, and evidence gates
  pass under the frozen decision policy.

### Gate E — immutable decision

The complete content-addressed evidence graph must verify offline. A
`BenchmarkResultQC(decision=GO)` requires every mandatory gate and `2f_b+1`
evaluator signatures over the exact result body. Missing evidence or any failed
mandatory gate is never operator-waivable.

## Success criteria

Feature 010 is GO only when all gates above pass and the reconciled candidate commit
containing the verified ResultQC is published as `FEATURE010_GO_CHECKPOINT_SHA`.
Until then the honest project-level outcome is `WORKING_VERSION_READY`: the local
working version remains usable, while Feature 010 and Feature 011 execution stay
closed.

## Atomic acceptance scenarios

These existing scenario identities are preserved from the historical design, but
none is marked executed on the current lineage.

### US1 — Freeze the experiment before primary results

1. **Given** a complete definition, **When** `2f_b+1` reviewers sign its canonical
   bytes, **Then** exactly one `BenchmarkDefinitionQC` finalizes.
2. **Given** a missing threshold/direction, mutable dependency or unbounded
   exclusion rule, **When** validation runs, **Then** preregistration fails.
3. **Given** a finalized definition, **When** a threshold or primary-arm setting
   changes, **Then** a new definition/QC is required and old results remain bound.
4. **Given** adaptive `H`, stale work or floating-point consensus fallback,
   **When** definition validation runs, **Then** the primary arm is rejected.

### US2 — Reproduce exact protocol results

1. **Given** identical inputs and fault trace, **When** the run repeats, **Then**
   every consensus-visible hash and terminal decision matches.
2. **Given** reordered delivery with liveness assumptions intact, **When** the run
   finalizes, **Then** its certified result remains identical.
3. **Given** a failed liveness assumption, **When** the deadline resolves, **Then**
   the run aborts with the parent current unchanged and an auditable reason.
4. **Given** flat and hierarchical paths over one ISC/EC/APC, **When** compared,
   **Then** every domain/parameter integer aggregate byte matches exactly.

### US3 — Measure quality at equal exposure

1. **Given** unequal eligible tokens/domain counts, **When** comparison is
   attempted, **Then** it is rejected unless the frozen rule explicitly permits it.
2. **Given** complete matched runs, **When** analysis executes, **Then** every
   metric uses its declared direction, threshold and statistical method.
3. **Given** normal loss but failed downstream/post-training threshold, **When**
   decision runs, **Then** the scientific gate fails.
4. **Given** a missing required seed/evaluation artifact, **When** decision runs,
   **Then** the frozen missing-run rule applies; silent omission is impossible.

### US4 — Reject Byzantine and mixed-view inputs

1. **Given** a parameter shard from another APC/view, **When** root assembly runs,
   **Then** it is rejected as mixed-view.
2. **Given** up to `f` equivocating validators, **When** conflicting proposals are
   delivered, **Then** at most one value finalizes per certificate/height.
3. **Given** unsafe coefficients or overflow input, **When** validation executes,
   **Then** it aborts without saturation or current-pointer change.
4. **Given** a seed transcript not bound to finalized ISC, **When** EC/APC verifies,
   **Then** the chain is invalid.
5. **Given** a weaker certificate on a checkpoint object, **When** P2P policy
   verifies, **Then** publication/use is rejected.

### US5 — Measure WAN/P2P and churn

1. **Given** a frozen network profile, **When** a run completes, **Then** compute,
   communication, consensus, robust, distribution and idle time are accounted
   without overlap double-counting.
2. **Given** initial-publisher loss after sufficient replication, **When** a peer
   fetches, **Then** it reconstructs the exact certified bytes.
3. **Given** approximately 10% worker loss with sufficient domain capacity,
   **When** freeze resolves, **Then** only exact certified inputs are used.
4. **Given** concentrated insufficient-domain loss, **When** deadline resolves,
   **Then** the run aborts without `pi_d` rewrite or synthetic updates.

### US6 — Produce an immutable decision

1. **Given** complete verified evidence and every mandatory gate passing, **When**
   `2f_b+1` evaluators sign, **Then** `BenchmarkResultQC(decision=GO)` finalizes.
2. **Given** any gate failure or missing/unverifiable evidence, **When** decision
   runs, **Then** it returns `NO_GO` with exact failed gates.
3. **Given** operator commentary, **When** the report is built, **Then** commentary
   cannot alter the deterministic decision.
4. **Given** GO for another identity or expired compatibility window, **When**
   Feature 011 checks it, **Then** admission rejects it.

## Numbered requirements

### Preregistration and identity

- **FR-001**: Definition MUST bind source/tree, builds/images/SBOM, protocol,
  model/data/ticket/arithmetic/topology/network, metrics, thresholds and decision.
- **FR-002**: External model/data/evaluator dependencies MUST use immutable content
  identities and approved license/access policy.
- **FR-003**: DefinitionQC MUST require `2f_b+1` unique signatures from a declared
  `3f_b+1` review set.
- **FR-004**: Validation MUST reject missing directions/thresholds, mutable inputs,
  undefined missing-run policy and adaptive/stale/float-consensus behavior.
- **FR-005**: Any post-QC material change MUST create a new definition identity.
- **FR-006**: Every run MUST bind arm, repetition/seed, environment, actual
  inventory, trace, parent, tickets and all output/evidence roots.
- **FR-007**: Admission MUST reject identities outside the certified compatibility
  allowance.

### Determinism and safety

- **FR-008**: Protocol comparisons MUST use byte/hash equality without tolerance.
- **FR-009**: Flat and hierarchical reducers MUST process one ISC/EC/APC and emit
  identical domain/parameter integers.
- **FR-010**: The four-independent-validator determinism gate MUST run at primary
  workload scale.
- **FR-011**: The attack corpus MUST cover conflicting votes/config, early seed,
  mutated AC, mixed views, incomplete aggregates, overflow, apply conflict and
  certificate downgrade.
- **FR-012**: No attack may create a valid descendant QC, ApplyQC or current change.
- **FR-013**: Safety MUST evaluate Byzantine threshold, epoch, signer uniqueness
  and quorum intersection.
- **FR-014**: Liveness success MUST use only the frozen synchrony/quorum/
  availability/deadline assumptions.
- **FR-015**: Assumption failure MUST test safe abort/parent preservation separately
  from a safety failure.

### Scientific quality

- **FR-016**: Primary comparisons MUST match total eligible tokens and domain
  policy unless a frozen mathematical alternative exists.
- **FR-017**: Reference and DeltaReduce arms MUST share scientific identity; every
  DeltaReduce primary observation MUST additionally carry its full Python →
  Java/Netty → native/WAL stage-receipt lineage.
- **FR-018**: Metrics MUST include validation/perplexity, frozen downstream,
  per-domain and required post-training results.
- **FR-019**: Metric version/direction/aggregation/statistics/seeds/threshold MUST be
  frozen.
- **FR-020**: Training loss alone MUST NOT satisfy Gate B when other metrics are
  mandatory.
- **FR-021**: Missing/crashed/invalid/outlier runs MUST follow only the certified
  policy.
- **FR-022**: Fixed-point and robust effects MUST be attributable through frozen
  diagnostics/ablations.
- **FR-023**: Quality evidence MUST preserve raw artifacts, evaluator identity and
  exact join to run/certificate/checkpoint/stage receipts.

### WAN, P2P and resilience

- **FR-024**: Simulation profiles MUST freeze RTT/bandwidth/jitter/loss/reorder/
  duplicate/disconnect/partition/duration/seed and remain labeled `SIMULATED`.
- **FR-025**: Real-WAN runs MUST record measured path conditions and compatible
  workload/gate identity.
- **FR-026**: Telemetry MUST separately account for compute, upload, availability,
  certificate, reduce, apply, P2P and wait phases.
- **FR-027**: Byte accounting MUST include all worker/storage/regional/global/
  validator/P2P traffic and retries/duplicates.
- **FR-028**: Applicable arms MUST report utilization, wall-clock, time-to-quality,
  bytes/token and p50/p95/p99 phase latency.
- **FR-029**: Engineering targets MUST be definition-bound and pass only after
  measurement.
- **FR-030**: Seed-loss MUST reconstruct exact bytes for a complete remaining union
  and deterministically fail for an incomplete union.
- **FR-031**: Churn MUST cover approximately 10% worker loss, validator restart,
  storage loss and region delay/partition.
- **FR-032**: Loss MUST never cause adaptive `H`, speed weighting, post-freeze
  mutation, implicit `pi_d` rewrite or fabricated work.
- **FR-033**: Recovery MUST preserve vote/certificate/commit/residual/current
  idempotency.

### Evidence and decision

- **FR-034**: Configuration, artifacts, QCs, metrics and reports MUST form one
  immutable content-addressed evidence graph.
- **FR-035**: Evidence MUST bind source/build/image/SBOM/locks/environment/hardware/
  time and redacted configuration.
- **FR-036**: Offline verification MUST check hashes, signatures, QCs, identities,
  gate inputs and calculations without network dependency.
- **FR-037**: BenchmarkResult MUST contain roots, runs, gate table, measured values,
  failed/missing evidence, limitations and deterministic decision.
- **FR-038**: GO MUST require every mandatory gate and evidence item.
- **FR-039**: ResultQC MUST require `2f_b+1` unique evaluator signatures over exact
  result bytes.
- **FR-040**: Commentary or threshold change cannot convert NO_GO to GO.
- **FR-041**: Feature 011 admission MUST bind exact compatibility and accept only
  genuine GO.
- **FR-042**: CLI MUST provide define/validate/run/collect/verify/report/decision.
- **FR-043**: Report generation MUST be reproducible and not depend solely on a
  mutable dashboard.

## Numbered success criteria

- **SC-001**: Definition is complete and certified before primary observation.
- **SC-002**: Honest processes agree exactly and hierarchy equals flat bytes.
- **SC-003**: Every mandatory attack rejects without invalid current mutation.
- **SC-004**: Matched quality passes every frozen mandatory threshold.
- **SC-005**: WAN/P2P accounting is complete and passes frozen targets.
- **SC-006**: Seed-loss/churn produce their exact complete-or-safe-abort outcomes.
- **SC-007**: Offline verification reproduces every gate and the decision.
- **SC-008**: ResultQC GO exists only when all mandatory gates pass.

## Prohibited substitutions

- fabricated controller identities, keys, votes, owner acceptance, custody evidence,
  signing time, GPU evidence, endpoints, TLS identities, or regions;
- four aliases, processes, bots, or keys controlled by one authority;
- old/superseded receipts, mappings, definitions, signatures, or evidence promoted
  to the current lineage;
- netem/local/VM results labeled real WAN;
- demo results labeled primary or governance-eligible;
- post-hoc threshold, seed, exclusion, metric-direction, or missing-run changes;
- Python-only certificate admission, manual QC/current edits, adaptive `H`, stale
  updates, floating-point consensus fallback, or implicit `pi_d` renormalization.
