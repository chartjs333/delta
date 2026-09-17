import { describe, expect, it } from "vitest";

import sampleEegReceipt from "./samples/sample-eeg-observation-receipt.json";
import sampleMnistReceipt from "./samples/sample-mnist-stage-c-receipt.json";
import sampleQloraReceipt from "./samples/sample-qlora-stage-c-receipt.json";
import sample10GeneReceipt from "./samples/sample-10gene-plugin-boundary-receipt.json";
import {
  computeWorkloadConfigDigest,
  evaluateReceiptBinding,
  ReceiptValidationError,
  sha256Sync,
  validateExecutionReceipt,
  type ExecutionReceipt,
} from "./receipt-schema";

const SAMPLE_BACKEND_REF = "670b58f6458fe84620f4f9f46401f855d04ae05d";

describe("sha256Sync and computeWorkloadConfigDigest", () => {
  it("produces deterministic standard sha256 output", () => {
    const raw = "test-payload-123";
    const digest = sha256Sync(raw);
    expect(digest).toBe("8611b96ba75f5a60e6e52ea5708890fed853dec4be883317dfeed2f8048ab47d");
  });

  it("computes canonical workload config digest with sha256: prefix", () => {
    const digest = computeWorkloadConfigDigest(
      "mnist-centroid-v1",
      "mnist-v1",
      "STAGE_C_REAL_DRQ1",
      SAMPLE_BACKEND_REF
    );
    expect(digest).toBe(
      "sha256:69e505282e3b7937ebd2fb198f0ade832e853f3eb07cd543afb2ed1067c844fd"
    );
  });
});

describe("validateExecutionReceipt", () => {
  it("validates valid sample receipts", () => {
    const mnist = validateExecutionReceipt(sampleMnistReceipt);
    expect(mnist.workload.model_plugin_id).toBe("mnist-centroid-v1");
    expect(mnist.consensus_evidence?.applied_status).toBe("APPLIED");

    const qlora = validateExecutionReceipt(sampleQloraReceipt);
    expect(qlora.reference_anchor?.reference_anchor_declared).toBe(true);

    const eeg = validateExecutionReceipt(sampleEegReceipt);
    expect(eeg.observation_summary?.observation_note).toBeTruthy();

    const gene = validateExecutionReceipt(sample10GeneReceipt);
    expect(gene.workload.model_plugin_id).toBe("tabular-10gene-phenotype-v1");
    expect(gene.workload.dataset_id).toBe("synthetic-10gene-cohort-v1");
    expect(gene.workload.executed_scope).toBe("PLUGIN_BOUNDARY");
    expect(gene.consensus_evidence).toBeUndefined();
  });

  it("fails closed on non-object or missing type/version", () => {
    expect(() => validateExecutionReceipt(null)).toThrow(ReceiptValidationError);
    expect(() => validateExecutionReceipt({ schema_version: "2.0.0" })).toThrow(
      /Invalid schema_version/u
    );
    expect(() =>
      validateExecutionReceipt({
        schema_version: "1.0.0",
        receipt_type: "UNKNOWN",
      })
    ).toThrow(/Invalid receipt_type/u);
  });

  it("fails closed on non-40-char backend_commit", () => {
    const invalid = {
      ...sampleMnistReceipt,
      provenance: {
        ...sampleMnistReceipt.provenance,
        backend_commit: "short_commit",
      },
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /backend_commit must be a 40-character git SHA/u
    );
  });

  it("fails closed on non-40-char catalog_backend_ref or mismatch with backend_commit", () => {
    const invalidFormat = {
      ...sample10GeneReceipt,
      provenance: {
        ...sample10GeneReceipt.provenance,
        catalog_backend_ref: "short_ref",
      },
    };
    expect(() => validateExecutionReceipt(invalidFormat)).toThrow(
      /catalog_backend_ref must be a 40-character git SHA/u
    );

    const mismatched = {
      ...sample10GeneReceipt,
      provenance: {
        ...sample10GeneReceipt.provenance,
        catalog_backend_ref: "1111111111111111111111111111111111111111",
      },
    };
    expect(() => validateExecutionReceipt(mismatched)).toThrow(
      /must match backend_commit/u
    );
  });

  it("fails closed on non-40-char producer_commit", () => {
    const invalid = {
      ...sample10GeneReceipt,
      provenance: {
        ...sample10GeneReceipt.provenance,
        producer_commit: "not_a_valid_sha",
      },
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /producer_commit must be a 40-character git SHA/u
    );
  });

  it("fails closed when PLUGIN_BOUNDARY is missing producer_commit", () => {
    const invalid = {
      ...sample10GeneReceipt,
      provenance: {
        repository: sample10GeneReceipt.provenance.repository,
        backend_commit: sample10GeneReceipt.provenance.backend_commit,
        catalog_backend_ref: sample10GeneReceipt.provenance.catalog_backend_ref,
        produced_at: sample10GeneReceipt.provenance.produced_at,
      },
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /PLUGIN_BOUNDARY receipts require a valid 40-character git SHA producer_commit/u
    );
  });

  it("fails closed on tampered workload_config_digest", () => {
    const invalid = {
      ...sampleMnistReceipt,
      workload: {
        ...sampleMnistReceipt.workload,
        workload_config_digest:
          "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      },
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /Tampered workload_config_digest/u
    );
  });

  it("fails closed when STAGE_C_REAL_DRQ1 is missing consensus_evidence", () => {
    const invalid = {
      ...sampleMnistReceipt,
      consensus_evidence: undefined,
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /strictly requires 'consensus_evidence' block/u
    );
  });

  it("fails closed when STAGE_C_REAL_DRQ1 contains observation_summary", () => {
    const invalid = {
      ...sampleMnistReceipt,
      observation_summary: {
        observation_note: "not allowed here",
        metrics: { a: 1 },
      },
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /must not contain 'observation_summary'/u
    );
  });

  it("fails closed when MODEL_DATASET_BINDING_ONLY contains consensus_evidence", () => {
    const invalid = {
      ...sampleEegReceipt,
      consensus_evidence: sampleMnistReceipt.consensus_evidence,
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /strictly forbids 'consensus_evidence' block/u
    );
  });

  it("fails closed when MODEL_DATASET_BINDING_ONLY is missing observation_summary", () => {
    const invalid = {
      ...sampleEegReceipt,
      observation_summary: undefined,
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /strictly requires 'observation_summary' block/u
    );
  });

  it("fails closed when PLUGIN_BOUNDARY contains consensus_evidence", () => {
    const digest = computeWorkloadConfigDigest(
      "mnist-centroid-v1",
      "mnist-v1",
      "PLUGIN_BOUNDARY",
      SAMPLE_BACKEND_REF
    );
    const invalid = {
      ...sampleMnistReceipt,
      workload: {
        ...sampleMnistReceipt.workload,
        executed_scope: "PLUGIN_BOUNDARY",
        workload_config_digest: digest,
      },
      consensus_evidence: sampleMnistReceipt.consensus_evidence,
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /Plugin-boundary receipt strictly forbids 'consensus_evidence' block/u
    );
  });
  it("fails closed on non-sha256 state_root", () => {
    const invalid = {
      ...sampleMnistReceipt,
      consensus_evidence: {
        ...sampleMnistReceipt.consensus_evidence,
        state_root: "not-a-root",
      },
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(ReceiptValidationError);
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /state_root and canonical_model_digest must be formatted as 'sha256:<64 hex chars>'/u
    );
  });

  it("fails closed on non-sha256 canonical_model_digest", () => {
    const invalid = {
      ...sampleMnistReceipt,
      consensus_evidence: {
        ...sampleMnistReceipt.consensus_evidence,
        canonical_model_digest: "banana",
      },
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(ReceiptValidationError);
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /state_root and canonical_model_digest must be formatted as 'sha256:<64 hex chars>'/u
    );
  });

  it("fails closed when consensus_evidence declares APPLIED/COMMITTED but execution.verdict is ABORTED", () => {
    const invalid = {
      ...sampleMnistReceipt,
      execution: {
        verdict: "ABORTED",
        terminal_status: "ABORTED_ON_TIMEOUT",
      },
    };
    expect(() => validateExecutionReceipt(invalid)).toThrow(ReceiptValidationError);
    expect(() => validateExecutionReceipt(invalid)).toThrow(
      /strictly requires execution.verdict to be 'SUCCESS'/u
    );
  });
});

describe("evaluateReceiptBinding", () => {
  const validMnistReceipt = sampleMnistReceipt as unknown as ExecutionReceipt;
  const SAMPLE_REPO = "chartjs333/delta";

  it("returns STRUCTURALLY_VALID_BOUND_RECEIPT with UNATTESTED_CONSENSUS_RECORD when configuration matches", () => {
    const result = evaluateReceiptBinding(
      validMnistReceipt,
      "mnist-centroid-v1",
      "mnist-v1",
      "STAGE_C_REAL_DRQ1",
      SAMPLE_BACKEND_REF,
      SAMPLE_REPO
    );
    expect(result.state).toBe("STRUCTURALLY_VALID_BOUND_RECEIPT");
    expect(result.evidenceType).toBe("UNATTESTED_CONSENSUS_RECORD");
    expect(result.expectedDigest).toBe(validMnistReceipt.workload.workload_config_digest);
  });

  it("returns STRUCTURALLY_VALID_BOUND_RECEIPT with UNATTESTED_PLUGIN_BOUNDARY_RECORD for 10-gene plugin boundary receipt", () => {
    const geneReceipt = sample10GeneReceipt as unknown as ExecutionReceipt;
    const result = evaluateReceiptBinding(
      geneReceipt,
      "tabular-10gene-phenotype-v1",
      "synthetic-10gene-cohort-v1",
      "PLUGIN_BOUNDARY",
      SAMPLE_BACKEND_REF,
      SAMPLE_REPO
    );
    expect(result.state).toBe("STRUCTURALLY_VALID_BOUND_RECEIPT");
    expect(result.evidenceType).toBe("UNATTESTED_PLUGIN_BOUNDARY_RECORD");
    expect(result.expectedDigest).toBe(geneReceipt.workload.workload_config_digest);
  });

  it("returns STRUCTURALLY_VALID_BOUND_RECEIPT with OBSERVATION_RECORD for EEG observation receipt", () => {
    const eegReceipt = sampleEegReceipt as unknown as ExecutionReceipt;
    const result = evaluateReceiptBinding(
      eegReceipt,
      "eeg-bandpower-centroid-v1",
      "eeg-synthetic-bci-v1",
      "MODEL_DATASET_BINDING_ONLY",
      SAMPLE_BACKEND_REF,
      SAMPLE_REPO
    );
    expect(result.state).toBe("STRUCTURALLY_VALID_BOUND_RECEIPT");
    expect(result.evidenceType).toBe("OBSERVATION_RECORD");
  });

  it("returns STRUCTURALLY_VALID_BOUND_RECEIPT with UNATTESTED_PLUGIN_BOUNDARY_RECORD for plugin boundary receipt", () => {
    const digest = computeWorkloadConfigDigest(
      "mnist-centroid-v1",
      "mnist-v1",
      "PLUGIN_BOUNDARY",
      SAMPLE_BACKEND_REF
    );
    const pluginReceipt = {
      ...sampleMnistReceipt,
      workload: {
        ...sampleMnistReceipt.workload,
        executed_scope: "PLUGIN_BOUNDARY",
        workload_config_digest: digest,
      },
      consensus_evidence: undefined,
    } as unknown as ExecutionReceipt;

    const result = evaluateReceiptBinding(
      pluginReceipt,
      "mnist-centroid-v1",
      "mnist-v1",
      "PLUGIN_BOUNDARY",
      SAMPLE_BACKEND_REF,
      SAMPLE_REPO
    );
    expect(result.state).toBe("STRUCTURALLY_VALID_BOUND_RECEIPT");
    expect(result.evidenceType).toBe("UNATTESTED_PLUGIN_BOUNDARY_RECORD");
  });

  it("returns RECEIPT_LOADED_UNBOUND when model differs from active selector", () => {
    const result = evaluateReceiptBinding(
      validMnistReceipt,
      "qlora-tiny-adapter-v1",
      "mnist-v1",
      "STAGE_C_REAL_DRQ1",
      SAMPLE_BACKEND_REF,
      SAMPLE_REPO
    );
    expect(result.state).toBe("RECEIPT_LOADED_UNBOUND");
    expect(result.reason).toContain("does not match selected model");
  });

  it("returns RECEIPT_LOADED_UNBOUND when scope differs from active selector", () => {
    const result = evaluateReceiptBinding(
      validMnistReceipt,
      "mnist-centroid-v1",
      "mnist-v1",
      "MODEL_DATASET_BINDING_ONLY",
      SAMPLE_BACKEND_REF,
      SAMPLE_REPO
    );
    expect(result.state).toBe("RECEIPT_LOADED_UNBOUND");
    expect(result.reason).toContain("does not match selected scope");
  });

  it("returns RECEIPT_LOADED_UNBOUND when backend reference differs", () => {
    const result = evaluateReceiptBinding(
      validMnistReceipt,
      "mnist-centroid-v1",
      "mnist-v1",
      "STAGE_C_REAL_DRQ1",
      "1111111111111111111111111111111111111111",
      SAMPLE_REPO
    );
    expect(result.state).toBe("RECEIPT_LOADED_UNBOUND");
    expect(result.reason).toContain("backend commit does not match");
  });

  it("returns RECEIPT_LOADED_UNBOUND when repository differs from catalog repository", () => {
    const result = evaluateReceiptBinding(
      validMnistReceipt,
      "mnist-centroid-v1",
      "mnist-v1",
      "STAGE_C_REAL_DRQ1",
      SAMPLE_BACKEND_REF,
      "other-org/other-repo"
    );
    expect(result.state).toBe("RECEIPT_LOADED_UNBOUND");
    expect(result.reason).toContain("does not match active catalog repository");
  });
});
