# Step 5C Architecture Governance Ledger and Remediation Record

**Document Type**: `STEP5C_GOVERNANCE_LEDGER`  
**Status**: `ACTIVE_REMEDIATION_CYCLE`  
**Authority**: ADR 0002, SpecKit `specs/admin-ui/step5c-controlled-live-execution/`, Constitution 2.1.0  
**Coordinator**: ChatGPT / Архитектор-координатор (`phone=2107`, `id=chatgpt-architecture-governance`)  
**Assigned Task**: `TEAM-GATE-001`  

---

## 1. Pinned Governance Baseline and Ledger

| Parameter | Identifier / SHA | Status |
| :--- | :--- | :--- |
| **ADR 0002 Acceptance** | PR `#33` (`4cf2aa8`) | Accepted |
| **CONTRACT_FREEZE_SHA** | `66e3e7e5bb07a48aadbee8d9c4683144b812d229` | Frozen |
| **ORIGINAL_CONTRACTS_SHA** | `9fd11f9fb8b17e0029ab97eaa7fa13d8689b9404` (PR `#34`) | Merged with remediation findings |
| **CORRECTED_CONTRACTS_SHA** | `PENDING_REMEDIATION_PR` | Blocked on Programmer A follow-up |
| **PR #35 (Controller)** | `6d62dda` (`feature/step5c-controller`) | Open with blocking findings |
| **PR #36 (Worker Adapter)** | `fdff678` (`feature/step5c-worker-adapter`) | Open with blocking findings |
| **PR #37 (Admin UI Live)** | `8690c94` (`feature/step5c-admin-ui-live`) | Open with blocking findings |
| **PR #38 (Security Hardening)** | `2c43abb` (`feature/step5c-security`) | Open with blocking findings |
| **PR #39 (E2E Integration)** | `11712f1` (`feature/step5c-e2e`) | **ON HOLD** (Premature integration candidate) |

---

## 2. No-Duplicate Rule and Architecture Mandate

1. **Preserve Existing Work**: Do not recreate original task ranges from scratch. Each PR author must inspect existing branches, preserve completed functionality, and implement only remediation deltas.
2. **Sequential Remediation Flow**:
   $$\text{A (Contracts Remediation)} \longrightarrow \text{Record CORRECTED\_CONTRACTS\_SHA} \longrightarrow \text{B (Controller)} \parallel \text{C (Worker)} \parallel \text{D (UI)} \parallel \text{E (Security)} \longrightarrow \text{F (E2E Requalification)} \longrightarrow \text{Final Gate}$$
3. **No Premature Qualification**: PR #39 is strictly an integration candidate on HOLD. Green generic CI alone does not constitute qualification or merge permission.
4. **Protected Spine Zero-Diff**: Native C++ consensus core, Java consensus reactor, and formal TLA+ specifications are strictly out of scope for Step 5C live execution. Any touch to protected paths is an unconditional STOP.

---

## 3. Detailed Cross-PR Remediation Findings

### A. Contracts Follow-Up (Programmer A, Phone: 2101, Branch: `feature/step5c-contracts-remediation`)
- **A1 (Operation Semantics)**: `MATERIALIZE_DATASET` is status-only and must complete cleanly without emitting `receipt_digest`. Receipt-eligible operations (`TRAIN_TICKET`, `EVALUATE_CHECKPOINT`) remain strictly tied to receipt lineage.
- **A2 (JCS Reference Vectors)**: Expand RFC 8785 / JCS golden vectors with independent number-edge cases, exponential formatting, Unicode edge cases, and cross-language parity fixtures (Python $\leftrightarrow$ TypeScript).
- **A3 (Trust Inflation Guard)**: Harden `ExecutionReceipt` lineage extension schema to reject nested or extra consensus trust-inflation claims.
- **A4 (Evidence Normalization)**: Normalize evidence artifact naming between raw file-byte SHA-256 and canonical JCS digest semantics; regenerate and verify `artifact-manifest.json`.

### B. Trusted Authorization Gate / Controller (Programmer B, Phone: 2102, Branch: `feature/step5c-controller`)
- **B1 (Signing Identity)**: Inject configured Ed25519 runtime signing identity that strictly matches the worker verification key.
- **B2 (Atomic Idempotency Ledger)**: Replace race-prone ledger state with atomic durable concurrency-safe reservation/commit semantics.
- **B3 (Transport-Derived Identity)**: Enforce authenticated subject and role verification from transport credentials; caller-provided JSON is untrusted metadata.
- **B4 (Dataset Status Semantics)**: Align `MATERIALIZE_DATASET` terminal status to omit receipt requirement.
- **B5 (Concurrency & Restart Verification)**: Add production-path tests for concurrent replay and crash-restart idempotency.

### C. Constrained Worker Adapter (Programmer C, Phone: 2103, Branch: `feature/step5c-worker-adapter`)
- **C1 (Controller Key Trust)**: Align controller public key and key_id trust store with the controller's runtime authenticator.
- **C2 (True Cancellation / Timeout)**: Replace `ThreadPoolExecutor` pseudo-timeout with cooperative bounded/cancellable execution and wall-clock verification.
- **C3 (Fail-Closed Admission Gate)**: Fail closed immediately if `resource_grants` or required `AuthorizedExecution` fields are missing or malformed.
- **C4 (Dataset Receipt Omission)**: Do not generate or demand receipt digest for `MATERIALIZE_DATASET`.

### D. Admin UI Live Intent Surface (Programmer D, Phone: 2104, Branch: `feature/step5c-admin-ui-live`)
- **D1 (Cryptographic UUID)**: Eliminate fallback constant intent UUID; fail closed or use standard cryptographic `crypto.randomUUID()`.
- **D2 (JCS Parity)**: Ingest updated RFC 8785 golden vectors from contracts remediation and verify browser digest parity.
- **D3 (Boundary Isolation)**: Maintain strict isolation between `LiveExecutionPort` and offline `DataSourcePort`; retain CSP `connect-src 'none'` and zero-egress local mock adapters pre-T035.

### E. Security & Threat Hardening (Programmer E, Phone: 2105, Branch: `feature/step5c-security`)
- **E1 (Production Code Binding)**: Refactor mock/synthetic security tests in T030–T034 to bind directly to production controller and worker code.
- **E2 (Frozen Taxonomy Adherence)**: Enforce frozen error taxonomy: duplicate `intent_id` with different digest $\to$ `ERR_INTENT_ID_DIGEST_CONFLICT`; different subject $\to$ `ERR_UNAUTHORIZED_CALLER`; timeout $\le 3600$.
- **E3 (Real Concurrency & Audit Testing)**: Test true durable ledger concurrency/restart, worker timeout/cancellation, and `AuditLogger` secret redaction.
- **E4 (Accurate Secret Scan Scope)**: Align secret-scanning assertions with actual repository and credential footprint.

### F. E2E Re-Qualification (Programmer F, Phone: 2106, Branch: `feature/step5c-e2e`)
- Rebuild integration branch on review-clean heads of A, B, C, D, E.
- Re-run transport (T035), dispatch (T036), UI integration (T037), lineage (T038), and recovery (T039).
- Re-run qualification gate (T040–T044) and publish machine-readable qualification dossier.

---

## 4. Remediation Handoff: Sequence 1 -> Programmer A

The remediation cycle is initiated with **Programmer A** (`phone=2101`, branch `feature/step5c-contracts-remediation`).
- **Target Task**: `step5c:CONTRACTS-REMEDIATION`
- **Base Commit**: `ORIGINAL_CONTRACTS_SHA` (`9fd11f9fb8b17e0029ab97eaa7fa13d8689b9404`)
- **Scope**: Contracts remediation delta for findings A1–A4.
- **Outcome**: Merge candidate PR for Coordinator review to establish `CORRECTED_CONTRACTS_SHA`.
