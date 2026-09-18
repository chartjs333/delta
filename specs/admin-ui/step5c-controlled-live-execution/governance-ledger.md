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
| **CONTRACTS_CANDIDATE_SHA** | `6898bc131f7c4b6d49fb40131ea0cced0f5d2f26` (PR `#40`) | **REWORK COMPLETED — IN REVIEW** (Target: `main`) |
| **CORRECTED_CONTRACTS_SHA** | *(None)* | **NOT SET** (Requires PR #40 merge into `main`) |
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
- Remote commit `b7afddb5e95d26dd46c10d36ad958ec418e7fee6` on `feature/step5c-contracts-remediation` was classified strictly as `CONTRACTS_REMEDIATION_CANDIDATE_SHA`.
- Programmer B (`2102`) was placed on **STOP / HOLD**. Local controller changes are preserved in commit `f8884fb` on `feature/step5c-controller`, but are non-authoritative and will not be dispatched or merged until contracts are fully approved and merged.
- **STOP/HOLD Acknowledgment Received**: Programmer B confirmed receipt via message `59081385-b411-4c1b-b20d-0bad0eead41f`. Controller work remains frozen until contracts are merged into `main`.
- No downstream implementation handoffs to B, C, D, E, or F may occur until the contracts gate is officially closed.

---

## 4. Specific Contracts Rework Package for Programmer A (`2101`)

Programmer A executed the following remediation on `feature/step5c-contracts-remediation`:

1. **T008 Independent RFC 8785 (JCS) Reference Corpus & Number Parity**:
   - Independent ECMAScript reference generator `specs/admin-ui/step5c-controlled-live-execution/contracts/scripts/generate_jcs_vectors.mjs` generates 21 golden vectors in `jcs-golden-vectors.json`.
   - Replaced `f"{value:.16g}"` in Python `contract_tools.py` with exact ECMA-262 ToString(Number) IEEE-754 decimal decomposition. 100% verified across 10,207 values against Node.js.
   - Added automated cross-verification `test_independent_ecmascript_cross_verification`.

2. **Recursive Receipt Lineage Trust Inflation Guard**:
   - Hardened `execution-receipt-lineage-extension.schema.json` and `receipt_lineage_extension_schema()` with recursive `$defs.safeExtensionValue`.
   - Deeply inspects all nested objects and array items at arbitrary depths, rejecting consensus claims (`round_id`, `state_root`, `wal_sequence`, `qc`, `apply_qc`, `consensus_round`, `validator_signatures`, `bft_quorum`, `stage_c_claim`, `consensus_view`, `proposal_hash`, `commit_certificate`).
   - Added invalid test cases `receipt-lineage.nested-arbitrary-state-root.json` and `receipt-lineage.deep-array-wal-sequence.json`.

3. **Manifest Byte Hashing Semantics & Cleanup**:
   - Computed `artifact_manifest_file_sha256` directly from file bytes of `artifact-manifest.json` on disk.
   - Removed deprecated `sha256` and `bytes` legacy keys.

4. **ExecutionStatus Operation & Parity**:
   - Made `"operation"` a required property in `execution-status.schema.json` and `execution_status_schema()`.

---

## 5. Legitimate Delivery Chain and Reviewer Gate

1. Programmer A pushed rework commit `6898bc131f7c4b6d49fb40131ea0cced0f5d2f26` to `origin/feature/step5c-contracts-remediation`.
2. Opened follow-up PR `#40` targeting `main`: [PR #40](https://github.com/chartjs333/delta/pull/40).
3. **Current Gate**: Awaiting two independent sequential reviewer `APPROVE` verdicts on PR #40.
4. Once two independent `APPROVE` verdicts and green CI are achieved:
   - Merge PR #40 into `main`.
   - Designate resulting merge commit in `main` as authoritative `CORRECTED_CONTRACTS_SHA`.
   - Authorize Programmer B (`2102`) to unfreeze and rebase `feature/step5c-controller`.

---

## 6. Official Submission Record: PR #40

| Field | Value |
| :--- | :--- |
| **Pull Request** | `#40` (`https://github.com/chartjs333/delta/pull/40`) |
| **Target Branch** | `main` |
| **Source Branch** | `feature/step5c-contracts-remediation` |
| **Remote HEAD SHA** | `6898bc131f7c4b6d49fb40131ea0cced0f5d2f26` |
| **Test Suite** | 13/13 passing (`pytest specs/admin-ui/step5c-controlled-live-execution/contracts/tests`) |
| **Linter & Format** | `uv run ruff check` & `uv run ruff format --check` (100% clean) |
| **Protected Spine Diff** | Zero diff against `9fd11f9` (`delta-core-cpp/`, `delta-runtime-cpp/`, `delta-node-java/`, `specs/000-formal-tla-spec/`) |
| **Status** | **AWAITING 2 REVIEWER APPROVALS** |
