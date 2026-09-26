# DeltaReduce Research Report

**Author:** Student Researcher  
**Date and Time, Timezone:** September 25, 2026, 13:20 CEST  
**External Application URL:** `https://expansion-raised-ends-directed.trycloudflare.com/?lang=en#overview`  
**Guide & Demo Version:** September 25, 2026 (Git commit: `a974135e00150c1865b0cef80cbdbe89bdd2cac7`, Controller commit: `c8aea64972f741060d1e527ebbb6f9a5a168a075`)  

---

## 1. Objective
Investigate the operational mechanics of deterministic distributed machine learning in DeltaReduce, empirically evaluate protocol resilience against Byzantine faults and data tampering, verify bit-for-bit computational reproducibility, and formulate a formal thesis proposal for custom plugin development.

---

## 2. System Architecture
- **Worker:** Autonomous compute process. Trains models on local private data, generates binary update artifacts, and submits a Ticket descriptor. Holds zero voting authority in BFT consensus.
- **Controller:** Local orchestration service. Receives training requests via HTTP API, coordinates worker processes, and returns structured execution receipts (`receipt-*.json`). It is an execution harness, not a consensus validator.
- **Validator:** Byzantine fault-tolerant consensus node. Verifies ticket context against round rules, signs quorum certificates (`ISC`, `AggregateRootQC`, `ApplyQC`), and persists state transitions to an append-only Write-Ahead Log (WAL).
- **Core Data Structures:**
  - `Artifact`: Serialized binary blob of weights/optimizer states in content-addressed storage;
  - `CID`: Content identifier digest (SHA-256);
  - `Ticket`: Compact metadata descriptor (`CID`, `domain`, `weight`, `parent`, `config`, `nonce`);
  - `Parent Checkpoint`: Baseline model state from which gradients were derived;
  - `RoundConfig`: Immutable round specification (trainable layers, tensor schemas, validator roster, aggregation scheme);
  - `ISC (InputSetCertificate)`: Quorum certificate freezing the canonical, ordered ticket roster;
  - `ApplyQC`: Quorum certificate authorizing application of the deterministic reduction delta.
- **Separation of Contexts:**
  - In Admin UI: *Campaign &rarr; Workload Selection &rarr; Live Execution &rarr; Receipt &rarr; Presentation* form a unified local execution trace;
  - The Verification Lab (`/verification/`), Node Training suite (`/node-training/`), and Docker Quorum testbed operate as **independent empirical demonstrations** verifying specific isolated properties of the protocol.

---

## 3. Empirical Experiments

| Scenario | Execution Mode | ID / Timestamp | Empirical Outcome | Evidence Artifact |
|---|---|---|---|---|
| **Controller Training** | Live Execution | `presentation_demo` / Sept 25, 2026 | `COMPLETED` (CPU, `PLUGIN_BOUNDARY`) | `admin_live_execution.png`, `receipt-*.json` |
| **Verification Lab: Run 1** | Live Execution | Sept 25, 2026, 13:00 | 7 of 7 checks passed successfully | `lab_verification_7_of_7.png` |
| **Verification Lab: Repeat** | Live Execution | Sept 25, 2026, 13:01 | 100% bit-for-bit identical bytes | `lab_verification_7_of_7.png` |
| **MNIST 4-Node Training** | Live Execution | Sept 25, 2026, 13:02 | 82.05% Accuracy, `BYTE-EXACT`, WAL Replay | `node_training_mnist_byte_exact.png`, `node_training_recovery_contracts.png` |
| **Docker Quorum Simulation** | Empirical Evaluation | Sept 25, 2026, 13:04 | 4/4 &rarr; 3/4 (quorum) &rarr; 2/4 (block) &rarr; restart | `system_overview_dashboard.png` |

---

## 4. Reproducibility and Adversarial Defenses
- **Verification Lab Output Hashes:** Re-evaluating the pipeline (Baseline Model `[20, -20]` &rarr; PARAMETER `[1, -2]` &rarr; APPLY `[19, -19]`) yielded 100% identical SHA-256 hashes (`BYTE-EXACT`).
- **Adversarial Tampering Scenarios (5 Rejection Invariants):**
  1. *Payload Modification:* Tampering with coordinate $Q$ while preserving the original CID immediately triggered an `ARTIFACT_BYTES` abort.
  2. *PARAMETER Tampering:* Numerator alteration triggered `ARITHMETIC_RESULT_MISMATCH`.
  3. *Optimizer Tampering:* State alteration in APPLY triggered `ARITHMETIC_RESULT_MISMATCH`.
  4. *Missing Artifact:* Dangling reference triggered `ARTIFACT_MISSING`.
  5. *Stale Parent:* Baseline model mismatch triggered `PARENT_MODEL`.
- **Receipt vs. QC vs. BenchmarkResultQC:**
  - `Receipt`: Local execution evidence emitted by Controller;
  - `QC (Quorum Certificate)`: Cryptographic multi-signature attestation from $\ge 2f + 1$ validators;
  - `BenchmarkResultQC`: Official multi-party qualification certificate under Feature010 (not present in current build: `gate_eligible=false`).

---

## 5. Training Observations
- **Workload Models & Datasets:**
  - Controller scenario: Nearest centroid classifier (`tabular-10gene-phenotype-v1`) on synthetic cohort (`synthetic-10gene-cohort-v1`).
  - Node training scenario: MNIST centroid classifier (`mnist-centroid-v1`) on partitioned digits (`mnist-v1`).
- **Observed Metrics:**
  - Centralized Test Accuracy: `82.05%`;
  - Distributed 4-Node Accuracy: `82.05%`;
  - Model Tensor Parity: `BYTE-EXACT`.
- **CPU vs. GPU Compute:** Training ran strictly on CPU via the Python Worker process. The visible RTX 3070 Laptop GPU (8192 MiB) represents host hardware telemetry and was not engaged by the CPU plugin.
- **BYTE-EXACT Significance:** Denotes exact binary equality of all serialized model weight buffers between centralized reference and distributed DeltaReduce outputs.

---

## 6. System Boundaries & Limitations
- The running demonstration operates in `SIMULATED_LOCAL` and `LOCAL_DEMO_ONLY` modes.
- All processes execute on a single physical host under unified administrative control. This does not replicate sovereign multi-region validator authorities or Real WAN network latencies (Gate D).
- Ed25519 signing keys reside in the local demo profile rather than Hardware Security Modules (HSM).
- While proving algorithmic soundness, these empirical runs do not constitute Feature010 GO production qualification.

---

## 7. Research Proposal for the Professor
- **Research Question:** «Evaluating Byzantine Resilience of DeltaReduce Deterministic Consensus Under Coordinated Gradient Poisoning Attacks (Sign-Flip and Gaussian Noise) on Heterogeneous Biomedical Cohorts».
- **Dataset:** Public cancer genomics expression profiles (TCGA) partitioned into 4–8 clinic domains.
- **Model:** Multilayer perceptron / linear classifier with fixed-point INT64 parameter representations.
- **Partitioning:** 70% domain-partitioned local training, 30% centralized evaluation set.
- **Implementation Plan:**
  1. Develop `DatasetProvider` enforcing strict data validation;
  2. Implement `ModelPlugin` with INT64 quantized gradient exports;
  3. Simulate $f \ge 1$ colluding Byzantine workers;
  4. Measure F1-score retention and consensus overhead.
- **Required Resources:** Python 3.12, local DeltaReduce Controller, 3 weeks development timeline.
