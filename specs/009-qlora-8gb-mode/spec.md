# Feature Specification: Certified Fixed-Ticket QLoRA Mode for 8 GiB GPUs

**Feature Branch**: `009-qlora-8gb-mode`  
**Created**: 2026-08-23  
**Status**: SpecKit reconciled — exact preflight and hardware readiness gate implementation
**Depends on**: feature-008 merge `62124e58062d876dc4c2fd903b57cfc7d89872d7`
**Feature-008 source**: `4ef4daead4e3fcdf19d6947cf8120c4974af09fe`
**Feature-008 evidence**: `d86473a3f864b4e61d2312584afa080c8fd4fbab`
**Feature-008 report SHA-256**: `fb7b9f572923e3d8a8e24195f630474ed836ff0a7ef6454b7d31d3f930a4cc9c`
**Formal semantics**: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`
**Formal impact**: `REFINEMENT_ONLY`
**Semantic completeness claimed**: `false`

## Summary

A full optimizer state for a large dense model does not fit on a single 8 GiB GPU. DeltaReduce v1 therefore introduces a certified `QLORA_ADAPTER` training mode in which an immutable quantized base model is distributed once, remains frozen, and only LoRA adapter parameters participate in local training, fixed-point aggregation, robust certification and outer application.

QLoRA does not relax any DeltaReduce invariant:

- every unit of work is a domain-pure ticket with fixed `B` and `H`;
- worker-local floating-point training ends before consensus;
- the normalized adapter pseudo-gradient is quantized under the round's canonical `int16-fixed-v1` profile;
- adapter shards advance only through `ISC → EC → APC → ParameterShardQC → AggregateRootQC → ApplyQC`;
- domain mixture and the outer optimizer are applied inside consensus;
- base parameters, buffers and quantization metadata are immutable and never enter adapter deltas, residuals or outer optimizer state.

The statement “runs on an 8 GiB GPU” is valid only for an exact committed hardware/model/configuration profile backed by measured peak-memory evidence. It is not a general claim for every model, sequence length, kernel or operating system.

Feature 009 specializes the existing feature-008 certificate graph through
`TrainingMode=QLORA_ADAPTER`, immutable base/tokenizer/quantization/schema fingerprints and a parent
adapter hash. It MUST NOT create parallel `QLoRAInputSetCertificate`, `QLoRAAggregateRootQC`,
`QLoRAApplyQC` or equivalent certificate types. Discovery of a new protocol-visible state, failure
terminal, durability outcome or partial-apply transition reclassifies the work as `SEMANTIC` and is
an unconditional STOP pending a new feature-000 Formal GO.

## User Scenarios & Testing

### US1 — Qualify an immutable base and adapter schema (Priority: P1)

An operator imports a legally usable base model, tokenizer and quantization configuration into the CAS, resolves the LoRA target modules, and finalizes one QLoRA mode manifest before ticketing.

**Independent Test**: a tiny offline fixture resolves one immutable base, quantization profile and ordered adapter schema; any base/tokenizer/module/rank mismatch changes the mode fingerprint and is rejected by round validation.

**Acceptance Scenarios**:

1. **Given** imported base weights, tokenizer and configuration, **When** the mode manifest is built, **Then** it contains immutable content hashes, provenance/license metadata, exact source revision and redistribution policy.
2. **Given** a QLoRA profile, **When** target modules are resolved, **Then** the exact ordered adapter names, shapes, ranks, dtypes and initialization rules form one content-addressed `AdapterParameterSchema`.
3. **Given** a different base revision, tokenizer, quantization backend, LoRA rank or target-module resolution, **When** compatibility is checked, **Then** the fingerprint differs and mixed updates cannot enter the same round.
4. **Given** a profile requiring unsupported kernels or compute dtype, **When** worker admission runs, **Then** the worker is excluded before receiving a ticket.

### US2 — Execute one fixed domain-pure QLoRA ticket within the memory budget (Priority: P1)

A compatible worker downloads or reuses the base object, installs the exact adapter parent, and completes exactly the ticket's fixed local work.

**Independent Test**: a tiny CPU/mock path and a designated physical 8 GiB CUDA qualification path prove that only adapter parameters receive gradients/optimizer state, `A_j=H`, the base logical hash is unchanged, and no update is published after an OOM or incomplete ticket.

**Acceptance Scenarios**:

1. **Given** a valid `DomainPureWorkTicket`, **When** local training starts, **Then** its domain, data range, `B`, `H`, base hash, parent-adapter hash and arithmetic profile are immutable.
2. **Given** an initialized QLoRA model, **When** optimizer groups are inspected, **Then** they contain only adapter parameters and every base parameter has `requires_grad=false`.
3. **Given** a complete ticket, **When** local training ends, **Then** `A_j=H`, processed data matches the ticket, and the adapter pseudo-gradient is normalized by `A_j` before quantization.
4. **Given** OOM, cancellation, data exhaustion or `A_j≠H`, **When** the ticket terminates, **Then** no eligible commitment is created; partial adapter state may be diagnostic only.
5. **Given** the designated qualification profile, **When** it executes on the physical card, **Then** evidence records device identity, nominal/available VRAM, driver/runtime, kernels, peak allocated/reserved memory and configured headroom.

### US3 — Commit and aggregate adapter-only fixed-point vectors (Priority: P1)

Workers encode only adapter tensors and submit them through the existing commitment, availability and certificate chain.

**Independent Test**: multiple workers with one base/schema produce the same certified adapter aggregate as the direct fixed-point reference; a base/schema/training-mode mismatch is rejected before norm or parameter arithmetic.

**Acceptance Scenarios**:

1. **Given** a complete local adapter ticket, **When** the contribution is encoded, **Then** the manifest contains exactly the ordered adapter tensors and no base tensor, buffer or base optimizer state.
2. **Given** a contribution with another base/tokenizer/quantization/adapter-schema hash, **When** ISC validation runs, **Then** it is rejected as incompatible with `RoundConfig`.
3. **Given** accepted adapter q-vectors, **When** EC/APC and parameter committees execute, **Then** all robust and accumulation arithmetic remains canonical fixed-point/integer.
4. **Given** complete adapter ParameterShardQCs, **When** AggregateRootQC is assembled, **Then** coverage is exact for the adapter schema and does not claim coverage of the frozen base.
5. **Given** a base tensor accidentally present in the payload, **When** the schema verifier runs, **Then** the contribution is rejected before availability or aggregation.

### US4 — Apply and distribute one certified global adapter checkpoint (Priority: P1)

Apply validators combine per-domain adapter aggregates using the fixed `pi_d`, execute the adapter outer optimizer, and certify a new adapter checkpoint while keeping the base unchanged.

**Independent Test**: four apply validators produce byte-identical adapter/outer-state hashes and one ApplyQC; the base hash remains identical and the P2P layer transfers only the new adapter/certificate object when the base is already cached.

**Acceptance Scenarios**:

1. **Given** an adapter AggregateRootQC and parent adapter state, **When** apply executes, **Then** the exact domain mixture and outer profile from `RoundConfig` are applied only to adapter tensors.
2. **Given** identical inputs, **When** independent validators execute, **Then** adapter checkpoint and optimizer-state bytes/hashes are identical.
3. **Given** one valid ApplyQC, **When** publication runs, **Then** the new adapter checkpoint becomes current once and is accepted under `apply-qc-v1`.
4. **Given** the base object already exists locally, **When** the next adapter checkpoint is fetched, **Then** unchanged base bytes are not downloaded again.
5. **Given** a proposal that mutates or substitutes the base hash, **When** apply/certificate verification runs, **Then** it is rejected and the parent adapter remains current.

### US5 — Resume and evaluate an exact base-plus-adapter composition (Priority: P2)

A researcher resumes training or evaluates one certified adapter against its immutable base.

**Independent Test**: base + adapter + tokenizer + evaluation configuration reconstruct one exact model view; resume from the certified adapter/optimizer state matches the uninterrupted reference within the worker-local reproducibility contract, while all consensus-visible hashes remain exact.

**Acceptance Scenarios**:

1. **Given** a certified adapter checkpoint, **When** composition is materialized, **Then** the base/tokenizer/quantization/schema/adapter/ApplyQC lineage is verified first.
2. **Given** compatible local optimizer, residual and cursor state, **When** resume occurs, **Then** the next fixed ticket starts from the exact certified parent adapter.
3. **Given** incompatible library/profile/base/schema state, **When** resume is requested, **Then** it hard-fails unless a separately certified migration exists.
4. **Given** an optional merged export, **When** it is created, **Then** it becomes a new derived immutable artifact with explicit provenance/license and never replaces the authoritative frozen base or adapter lineage.

## Edge Cases

- Physical card reports 8 GiB nominal memory but less available due to display/system use.
- BF16 unsupported and FP16 fallback not declared by the profile.
- Quantization kernel/library version differs while source model hash is identical.
- Target-module expression resolves zero, duplicate or unexpected modules.
- Tied embeddings/output head and adapter placement.
- Base buffers change despite frozen parameters.
- Base tensor accidentally appears in optimizer groups, gradients, local delta or residual state.
- Adapter rank/alpha/dropout/bias differs across workers.
- Gradient checkpointing or paged optimizer changes the reproducibility class.
- Runtime OOM occurs before peak-memory telemetry is flushed.
- Adapter q-vector is all zero or reaches quantization bounds.
- One domain has no eligible certified adapter ticket.
- ApplyQC references correct adapter but wrong base or tokenizer.
- Optional merged weights violate source license or redistribution policy.

## Requirements

### Mode, base and schema requirements

- **FR-001**: The system MUST define a versioned `TrainingMode=QLORA_ADAPTER` distinct from full-model mode.
- **FR-002**: `BaseModelManifest` MUST bind model source/revision, immutable weight/config/tokenizer hashes, provenance, license and approved access/redistribution policy.
- **FR-003**: `QuantizedBaseProfile` MUST fix storage format/bit width (reference profile: NF4-compatible 4-bit storage), double-quantization setting, compute dtype, backend/kernel/library versions, device requirements and fallback policy.
- **FR-004**: `AdapterConfig` MUST fix LoRA rank, alpha, dropout, bias policy, initialization, target-module resolution algorithm and trainable dtype.
- **FR-005**: `AdapterParameterSchema` MUST contain the exact ordered adapter names, shapes, logical dtypes, aliases and hashes of the base, tokenizer, quantization profile and adapter config.
- **FR-006**: Every QLoRA `RoundConfig` and ticket MUST bind the exact mode/base/tokenizer/quantization/adapter-schema fingerprints.
- **FR-007**: Base parameters and non-approved base buffers MUST be immutable; any base-hash mutation is a protocol failure.
- **FR-008**: No base parameter MAY appear in local optimizer groups, gradient set, pseudo-gradient, fixed-point contribution, quantization residual, robust plan, outer optimizer state or adapter checkpoint.
- **FR-009**: Base omission from adapter payloads MUST be explicit in the schema; implicit missing tensors are forbidden.

### Fixed-ticket worker requirements

- **FR-010**: QLoRA work MUST use feature-007 domain-pure tickets with fixed `B`, fixed `H`, immutable data range and parent adapter.
- **FR-011**: Worker admission MUST validate accelerator capability, quantization kernels, compute dtype, sequence length, batch/accumulation configuration, checkpointing/offload flags and estimated memory against the exact profile.
- **FR-012**: A valid contribution requires completion of the full ticket with `A_j=H`; partial, stale or adaptively shortened work cannot be committed for eligibility.
- **FR-013**: Local training MUST count optimizer steps and ticket data deterministically and MUST not modify `B/H` in response to speed or memory pressure.
- **FR-014**: Runtime MUST measure peak allocated/reserved memory where supported and fail without an eligible commitment if the hard budget is exceeded.
- **FR-015**: Worker MUST compute `Delta_adapter = parent_adapter - final_adapter`, normalize by `A_j`, and quantize under the round's shared fixed-point profile before commitment.
- **FR-016**: `AdapterContributionManifest` MUST bind ticket/domain, actual `A_j`, base/tokenizer/quantization/schema hashes, memory evidence, ordered adapter shard table and commitment root.
- **FR-017**: Worker-local floating arithmetic and its tolerance-based reproducibility evidence MUST end before canonical q bytes are committed; consensus never aggregates floating adapter tensors.

### Certificate, aggregation and apply requirements

- **FR-018**: ISC verification MUST reject any adapter contribution with mismatched training mode, base, tokenizer, quantization profile, adapter schema, parent adapter or fixed-point profile.
- **FR-019**: EC/APC robust filtering MUST operate over canonical adapter q-vectors under feature-008 exact arithmetic and certificate rules.
- **FR-020**: Parameter committees MUST cover exactly the adapter schema; base tensors are neither expected nor inferred.
- **FR-021**: Regional/global adapter aggregation MUST remain checked integer/fixed-point and must satisfy the APC-specific accumulator proof.
- **FR-022**: AggregateRootQC MUST bind exact adapter-domain/shard coverage and the immutable base/mode fingerprints.
- **FR-023**: Apply validators MUST execute the configured domain mixture, momentum, weight decay and Nesterov transition only over adapter state using the exact apply profile.
- **FR-024**: ApplyQC tuple MUST bind parent/next adapter hashes, parent/next outer state, immutable base/tokenizer/quantization/schema hashes and AggregateRootQC.
- **FR-025**: `ApplyUniqueness` and current-pointer compare-and-set semantics from feature 008 apply unchanged to adapter checkpoints.
- **FR-026**: A conflicting base/mode/schema or a base mutation MUST prevent ApplyQC and leave the parent adapter current.

### Distribution, resume and qualification requirements

- **FR-027**: Distribution MUST allow signed/certified immutable base objects and ApplyQC-certified global adapter checkpoints/certificate bundles.
- **FR-028**: Worker-local adapter contributions, commitments and regional/parameter partials remain permanently forbidden distribution objects.
- **FR-029**: Base retrieval MUST be content-addressed and reusable; a new adapter round MUST not require retransmission of unchanged base bytes.
- **FR-030**: Adapter checkpoint MUST contain adapter tensors, exact outer state, schema/profile/certificate refs and parent lineage without duplicating base weights.
- **FR-031**: Resume MUST verify exact base/tokenizer/quantization/schema/profile and certified parent state; incompatible resume fails closed absent an explicit migration certificate.
- **FR-032**: Evaluation composition MUST bind base, tokenizer, quantization, adapter, ApplyQC and evaluation/generation configuration hashes.
- **FR-033**: Optional merge/export MUST create a separate derived object with provenance/license and must not alter authoritative base or adapter artifacts.
- **FR-034**: Repository history MUST not contain third-party model weights, access tokens, license-acceptance credentials or private signing keys.
- **FR-035**: CI MUST provide an offline tiny/mock QLoRA path; hardware qualification MUST use a committed `configs/qlora/8gb-reference.*` profile.
- **FR-036**: The qualification profile MUST be frozen before the hardware run and contain exact external model revision, approved license, batch/sequence/accumulation, fixed `B/H`, LoRA config, backend versions, memory limit/headroom and success threshold.
- **FR-037**: An 8 GiB claim MAY be published only with measured evidence from the exact physical GPU/runtime/profile.
- **FR-038**: Metrics MUST include base/adapter/trainable parameter counts and bytes, cache hit, ticket steps/tokens, q/shard bytes, peak memory, kernel/offload/checkpointing flags, certificate latency and ApplyQC result.
- **FR-039**: The physical qualification runner and frozen execution profile MUST be identified before a physical 8 GiB claim is attempted; without them the feature exit decision is `BLOCKED_HARDWARE`, never `PASS`.
- **FR-040**: Feature 009 MUST reuse the feature-008 ISC, SeedTranscript, EC, APC, ParameterShardQC, AggregateRootQC, ApplyQC and current-pointer types without a parallel QLoRA certificate hierarchy.

### Non-Functional Requirements

- **NFR-001**: Mandatory CI runs without CUDA or a remote model registry through local fixtures/mocks.
- **NFR-002**: The designated physical profile MUST complete at least one full fixed ticket and certified adapter path on a nominal 8 GiB GPU without OOM and within the declared hard budget/headroom.
- **NFR-003**: For the committed profile, trainable adapter parameter bytes SHOULD be at most 5% of logical base parameter bytes; the measured value is evidence rather than an assumption.
- **NFR-004**: Frozen-base and adapter-only optimizer/delta/shard invariants MUST be checked before and after every qualification run.
- **NFR-005**: All certificate, fixed-point, P2P and ApplyQC safety gates from features 003–008 remain mandatory.
- **NFR-006**: This feature does not establish quality parity; token/domain-matched quality is decided by feature 010.

### Key Entities

- **BaseModelManifest / QuantizedBaseProfile**: immutable base, tokenizer, legal/provenance and execution contract.
- **AdapterConfig / AdapterParameterSchema**: exact trainable LoRA topology.
- **QLoRATicket / AdapterContributionManifest**: fixed local work and canonical q-vector lineage.
- **CertifiedAdapterAggregate / GlobalAdapterCheckpoint**: AggregateRootQC/ApplyQC-bound adapter state.
- **MemoryQualificationProfile / Evidence**: exact physical hardware, software, workload and peak-memory result.
- **ModelCompositionManifest**: verified base-plus-adapter evaluation/resume view.

## Success Criteria

- **SC-001**: Tiny offline fixture proves frozen base, adapter-only optimizer/gradient/delta/shards/checkpoint and exact fingerprints.
- **SC-002**: Fixed QLoRA ticket completes only with `A_j=H`; incomplete/OOM paths create no eligible commitment.
- **SC-003**: Multi-worker adapter certificate chain matches the direct fixed-point reference and rejects every base/schema/mode mismatch.
- **SC-004**: Four apply validators produce identical adapter/outer-state hashes and one ApplyQC while the base hash remains unchanged.
- **SC-005**: Base cache test shows subsequent adapter rounds transfer no unchanged base bytes.
- **SC-006**: Resume/evaluation verifies exact composition and rejects incompatible lineage.
- **SC-007**: The committed physical 8 GiB profile completes without OOM with full peak-memory and safety evidence.
- **SC-008**: The measured adapter/base ratio meets the declared target or the branch stops with a documented redesign decision.

## Assumptions

- A specific external base is selected by an implementation research/license task and pinned before qualification.
- A physical 8 GiB qualification runner is available as a dedicated gate, not every CI run.
- Quantization backends may be platform-limited; unsupported workers are excluded rather than given modified tickets.
- The immutable base is normally downloaded once and retained in local CAS.

## Out of Scope

- Full dense multi-billion-parameter pretraining on one 8 GiB GPU.
- WAN pipeline/tensor parallelism for one base model.
- Adaptive local steps or memory-driven ticket mutation.
- IA3, prefix tuning, MoE adapters or automatic LoRA architecture search.
- Downstream-quality claims before feature 010.
