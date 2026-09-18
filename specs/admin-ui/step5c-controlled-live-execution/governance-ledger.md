# Step 5C Architecture Governance Ledger and Remediation Record

**Document Type**: `STEP5C_GOVERNANCE_LEDGER`  
**Status**: `REWORK_CYCLE_ACTIVE`  
**Authority**: ADR 0002, SpecKit `specs/admin-ui/step5c-controlled-live-execution/`, Constitution 2.1.0  
**Coordinator**: ChatGPT / Архитектор-координатор (`phone=2107`, `id=chatgpt-architecture-governance`)  
**Assigned Task**: `TEAM-GATE-001` / `COORD-001`–`COORD-003` / `GOVERNANCE CORRECTION`  

---

## 1. Pinned Governance Baseline and Ledger

| Parameter | Identifier / SHA | Status |
| :--- | :--- | :--- |
| **ADR 0002 Acceptance** | PR `#33` (`4cf2aa8`) | Accepted |
| **CONTRACT_FREEZE_SHA** | `66e3e7e5bb07a48aadbee8d9c4683144b812d229` | Frozen |
| **ORIGINAL_CONTRACTS_SHA** | `9fd11f9fb8b17e0029ab97eaa7fa13d8689b9404` (PR `#34`) | Merged with remediation findings |
| **CONTRACTS_CANDIDATE_SHA** | `b7afddb5e95d26dd46c10d36ad958ec418e7fee6` | **REWORK REQUIRED** (Branch: `feature/step5c-contracts-remediation`) |
| **CORRECTED_CONTRACTS_SHA** | *(None)* | **NOT SET** (Requires PR merge into `main`) |
| **PR #35 (Controller)** | `6d62dda` / WIP `f8884fb` | **STOP / HOLD** (WIP preserved locally; not authoritative) |
| **PR #36 (Worker Adapter)** | `fdff678` (`feature/step5c-worker-adapter`) | Open with blocking findings (awaiting contracts gate) |
| **PR #37 (Admin UI Live)** | `8690c94` (`feature/step5c-admin-ui-live`) | Open with blocking findings (awaiting contracts gate) |
| **PR #38 (Security Hardening)** | `2c43abb` (`feature/step5c-security`) | Open with blocking findings (awaiting contracts gate) |
| **PR #39 (E2E Integration)** | `11712f1` (`feature/step5c-e2e`) | **ON HOLD** (Premature integration candidate) |

---

## 2. No-Duplicate Rule and Architecture Mandate

1. **Preserve Existing Work**: Do not recreate original task ranges from scratch. Each PR author must inspect existing branches, preserve completed functionality, and implement only remediation deltas.
2. **Reviewer-Gated Sequential Flow**:
   $$\text{A (Rework)} \longrightarrow \text{Follow-up PR} \longrightarrow \text{Exact-Head Review} \longrightarrow \text{2 Reviewer APPROVE} \longrightarrow \text{CI} \longrightarrow \text{Merge to main} \longrightarrow \text{CORRECTED\_CONTRACTS\_SHA} \longrightarrow \text{B} \dots$$
3. **No Premature Ratification**: No branch commit can be designated `CORRECTED_CONTRACTS_SHA` prior to passing the two independent sequential graph reviewer approvals, green CI, and official merge into `main`. The merge commit SHA in `main` is the sole legitimate `CORRECTED_CONTRACTS_SHA`.
4. **Protected Spine Zero-Diff**: Native C++ consensus core, Java consensus reactor, and formal TLA+ specifications are strictly out of scope for Step 5C live execution. Any touch to protected paths is an unconditional STOP.

---

## 3. Governance Correction: Annulment of Premature Ratification

The prior declaration designating `b7afddb...` as `CORRECTED_CONTRACTS_SHA` is **formally annulled**.
- Remote commit `b7afddb5e95d26dd46c10d36ad958ec418e7fee6` on `feature/step5c-contracts-remediation` is classified strictly as `CONTRACTS_REMEDIATION_CANDIDATE_SHA`.
- Programmer B (`2102`) is placed on **STOP / HOLD**. Local controller changes are preserved in commit `f8884fb` on `feature/step5c-controller`, but are non-authoritative and will not be dispatched or merged until contracts are fully approved and merged.
- No downstream implementation handoffs to B, C, D, E, or F may occur until the contracts gate is officially closed.

---

## 4. Specific Contracts Rework Package for Programmer A (`2101`)

Programmer A must execute the following remediation on `feature/step5c-contracts-remediation`:

1. **T008 Independent RFC 8785 (JCS) Reference Corpus & Number Parity**:
   - Eliminate circular self-testing where Python generates vectors and verifies itself.
   - Introduce an independent ECMAScript / TypeScript reference generation script / corpus.
   - Include genuine IEEE-754 boundary cases, exponential representations (`1e20`, `1e-6`, etc.), max/min safe integers, zero edge cases (`0`, `-0`).
   - Eliminate `f"{value:.16g}"` in `_number_to_jcs()` in favor of the exact ECMAScript Number-to-string canonical specification.
   - Add automated cross-language verification (`Python <-> TypeScript`).

2. **Recursive Receipt Lineage Trust Inflation Guard**:
   - Address the bypass where nested arbitrary objects under `additionalProperties: true` (e.g. `metadata: {"state_root": ...}`) evade root-level property checks.
   - Implement recursive or deep property name validation to ensure no consensus trust claims (`round_id`, `state_root`, `qc`, `wal_sequence`, `proposal_hash`, etc.) can appear at any nesting level.

3. **Manifest Byte Hashing Semantics & Cleanup**:
   - Compute `artifact_manifest_file_sha256` directly over the actual raw UTF-8 bytes of the formatted `artifact-manifest.json` file on disk, rather than an in-memory compact serialization.
   - Explicitly separate raw file byte hash (`file_sha256`) and canonical JCS digest (`canonical_digest`).
   - Deprecate / remove ambiguous legacy `sha256` and `bytes` fields.

4. **ExecutionStatus Operation & Parity**:
   - Maintain the valid status-only fix for `MATERIALIZE_DATASET` without `receipt_digest`.
   - Enforce parity of `operation` between intent and status documents.

---

## 5. Next Steps and Legitimate Delivery Chain

1. Programmer A pushes rework commits to `feature/step5c-contracts-remediation`.
2. Verify exact remote HEAD on GitHub (`git ls-remote origin feature/step5c-contracts-remediation`).
3. Open a dedicated follow-up PR targeting `main`.
4. Submit completion to sequential graph `/whoami` endpoint.
5. Obtain **two independent sequential reviewer `APPROVE` verdicts**.
6. Verify green CI and merge follow-up PR into `main`.
7. Pinned merge commit from `main` is designated as `CORRECTED_CONTRACTS_SHA`.
8. Authorize Programmer B (`2102`) to unfreeze and rebase `feature/step5c-controller`.
