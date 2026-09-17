import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  CANONICAL_DESCRIPTOR_CATALOG,
  CatalogValidationError,
  validateCatalogSnapshot,
  type DescriptorCatalogSnapshot,
} from "../../data/descriptors-catalog";
import sampleMnistReceipt from "../../data/samples/sample-mnist-stage-c-receipt.json";
import { WorkloadSelector } from "./WorkloadSelector";

describe("WorkloadSelector", () => {
  it("renders 3 model plugins and 3 datasets from the canonical snapshot", () => {
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin") as HTMLSelectElement;
    const datasetSelect = screen.getByLabelText("Dataset Provider") as HTMLSelectElement;

    expect(modelSelect.options).toHaveLength(
      CANONICAL_DESCRIPTOR_CATALOG.model_plugins.length
    );
    expect(Array.from(modelSelect.options).map((o) => o.value)).toEqual(
      CANONICAL_DESCRIPTOR_CATALOG.model_plugins.map((p) => p.plugin_id)
    );
    expect(Array.from(modelSelect.options).map((o) => o.value)).toContain(
      "tabular-10gene-phenotype-v1"
    );

    expect(datasetSelect.options).toHaveLength(
      CANONICAL_DESCRIPTOR_CATALOG.datasets.length
    );
    expect(Array.from(datasetSelect.options).map((o) => o.value)).toEqual(
      CANONICAL_DESCRIPTOR_CATALOG.datasets.map((d) => d.dataset_id)
    );
    expect(Array.from(datasetSelect.options).map((o) => o.value)).toContain(
      "synthetic-10gene-cohort-v1"
    );
  });

  it("evaluates MNIST + MNIST + STAGE_C_REAL_DRQ1 as ALLOWED", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");
    const scopeSelect = screen.getByLabelText("Requested Execution Scope");

    await user.selectOptions(modelSelect, "mnist-centroid-v1");
    await user.selectOptions(datasetSelect, "mnist-v1");
    await user.selectOptions(scopeSelect, "STAGE_C_REAL_DRQ1");

    const statusEl = screen.getByRole("status");
    expect(statusEl.textContent).toContain("Status:ALLOWED");
    expect(screen.getByText("compatible")).toBeTruthy();
    expect(screen.getByText("Stage C capable")).toBeTruthy();
  });

  it("evaluates QLoRA + QLoRA + STAGE_C_REAL_DRQ1 as ALLOWED", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");
    const scopeSelect = screen.getByLabelText("Requested Execution Scope");

    await user.selectOptions(modelSelect, "qlora-tiny-adapter-v1");
    await user.selectOptions(datasetSelect, "tiny-qlora-regression-v1");
    await user.selectOptions(scopeSelect, "STAGE_C_REAL_DRQ1");

    const statusEl = screen.getByRole("status");
    expect(statusEl.textContent).toContain("Status:ALLOWED");
    expect(screen.getByText("compatible")).toBeTruthy();
    expect(screen.getByText("Stage C capable")).toBeTruthy();
  });

  it("evaluates EEG + EEG + MODEL_DATASET_BINDING_ONLY as ALLOWED", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");
    const scopeSelect = screen.getByLabelText("Requested Execution Scope");

    await user.selectOptions(modelSelect, "eeg-bandpower-centroid-v1");
    await user.selectOptions(datasetSelect, "eeg-synthetic-bci-v1");
    await user.selectOptions(scopeSelect, "MODEL_DATASET_BINDING_ONLY");

    const statusEl = screen.getByRole("status");
    expect(statusEl.textContent).toContain("Status:ALLOWED");
    expect(screen.getByText("compatible")).toBeTruthy();
    expect(screen.getByText("Observation only")).toBeTruthy();
  });

  it("evaluates EEG + EEG + STAGE_C_REAL_DRQ1 as REJECTED due to capability restriction", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");
    const scopeSelect = screen.getByLabelText("Requested Execution Scope");

    await user.selectOptions(modelSelect, "eeg-bandpower-centroid-v1");
    await user.selectOptions(datasetSelect, "eeg-synthetic-bci-v1");
    await user.selectOptions(scopeSelect, "STAGE_C_REAL_DRQ1");

    const statusEl = screen.getByRole("status");
    expect(statusEl.textContent).toContain("Status:REJECTED");
    expect(statusEl.textContent).toContain(
      "Reason: requested scope not allowed by catalog"
    );
    expect(screen.getByText("Observation only")).toBeTruthy();
  });

  it("evaluates MNIST + QLoRA dataset as REJECTED due to contract mismatch", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");

    await user.selectOptions(modelSelect, "mnist-centroid-v1");
    await user.selectOptions(datasetSelect, "tiny-qlora-regression-v1");

    const statusEl = screen.getByRole("status");
    expect(statusEl.textContent).toContain("Status:REJECTED");
    expect(statusEl.textContent).toContain(
      "Reason: contract incompatible: sample/target kind mismatch"
    );
    expect(screen.getByText("incompatible")).toBeTruthy();
  });

  it("evaluates Synthetic 10-Gene Phenotype + Synthetic 10-Gene Cohort as ALLOWED with Stage C capability", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");
    const scopeSelect = screen.getByLabelText("Requested Execution Scope");

    await user.selectOptions(modelSelect, "tabular-10gene-phenotype-v1");
    await user.selectOptions(datasetSelect, "synthetic-10gene-cohort-v1");
    await user.selectOptions(scopeSelect, "STAGE_C_REAL_DRQ1");

    const statusEl = screen.getByRole("status");
    expect(statusEl.textContent).toContain("Status:ALLOWED");
    expect(screen.getByText("compatible")).toBeTruthy();
    expect(screen.getByText("Stage C capable")).toBeTruthy();
  });

  it("evaluates Synthetic 10-Gene Phenotype + MNIST dataset as REJECTED due to cross-domain contract mismatch", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");

    await user.selectOptions(modelSelect, "tabular-10gene-phenotype-v1");
    await user.selectOptions(datasetSelect, "mnist-v1");

    const statusEl = screen.getByRole("status");
    expect(statusEl.textContent).toContain("Status:REJECTED");
    expect(statusEl.textContent).toContain(
      "Reason: contract incompatible: sample/target kind mismatch"
    );
    expect(screen.getByText("incompatible")).toBeTruthy();
  });

  it("strictly isolates execution evidence and does NOT claim live APPLIED, WAL or checkpoint", () => {
    const { container } = render(<WorkloadSelector />);

    const evidencePanel = screen.getByLabelText("Execution evidence");
    expect(evidencePanel.textContent).toContain("No live execution evidence loaded.");

    // Ensure no false claims in container text
    const allText = container.textContent ?? "";
    expect(allText).not.toMatch(/\bAPPLIED\b/u);
    expect(allText).not.toMatch(/WAL committed/iu);
    expect(allText).not.toMatch(/checkpoint advanced/iu);
  });

  it("displays provenance noting repository and 40-character commit SHA", () => {
    render(<WorkloadSelector />);

    expect(screen.getByText(/Catalog provenance:/u)).toBeTruthy();
    expect(
      screen.getByText(
        new RegExp(
          `${CANONICAL_DESCRIPTOR_CATALOG.source.repository}@${CANONICAL_DESCRIPTOR_CATALOG.source.backend_ref.slice(0, 7)}`,
          "u"
        )
      )
    ).toBeTruthy();
  });

  it("explicitly clarifies header copy that capabilities are verified from frozen snapshot", () => {
    render(<WorkloadSelector />);
    expect(
      screen.getByText(
        /Pre-flight capabilities are verified from frozen catalog snapshot derived from registry descriptors/u
      )
    ).toBeTruthy();
  });

  it("loads MNIST Stage C sample and displays STRUCTURALLY_VALID_BOUND_RECEIPT with unattested consensus details", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    // Selector defaults to mnist-centroid-v1 + mnist-v1 + STAGE_C_REAL_DRQ1
    const sampleBtn = screen.getByRole("button", { name: "MNIST Stage C" });
    await user.click(sampleBtn);

    expect(screen.getByText("STRUCTURALLY_VALID_BOUND_RECEIPT")).toBeTruthy();
    expect(screen.getByText("Recorded Consensus Record")).toBeTruthy();
    expect(screen.getByText("UNATTESTED_CONSENSUS_RECORD")).toBeTruthy();
    expect(
      screen.getByText(
        /Self-consistent local receipt bound to the active catalog configuration/u
      )
    ).toBeTruthy();
    expect(screen.getByText("APPLIED")).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy(); // WAL Sequence
    expect(
      screen.getByText("delta://checkpoints/mnist-centroid-v1/round-0001.bin")
    ).toBeTruthy();
  });

  it("loads 10-Gene Plugin Boundary sample and displays STRUCTURALLY_VALID_BOUND_RECEIPT with unattested plugin boundary details", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");
    const scopeSelect = screen.getByLabelText("Requested Execution Scope");

    await user.selectOptions(modelSelect, "tabular-10gene-phenotype-v1");
    await user.selectOptions(datasetSelect, "synthetic-10gene-cohort-v1");
    await user.selectOptions(scopeSelect, "PLUGIN_BOUNDARY");

    const sampleBtn = screen.getByRole("button", { name: "10-Gene Plugin Boundary" });
    await user.click(sampleBtn);

    expect(screen.getByText("STRUCTURALLY_VALID_BOUND_RECEIPT")).toBeTruthy();
    expect(screen.getByText("Recorded Plugin Boundary Record")).toBeTruthy();
    expect(screen.getByText("UNATTESTED_PLUGIN_BOUNDARY_RECORD")).toBeTruthy();
    expect(
      screen.getByText(
        /Plugin boundary record self-consistent without consensus round or WAL commits/u
      )
    ).toBeTruthy();
    expect(screen.getByText("COMPLETED")).toBeTruthy();

    // STRICT: consensus fields must not exist
    expect(screen.queryByText("Recorded Consensus Record")).toBeNull();
    expect(screen.queryByText("APPLIED")).toBeNull();
  });

  it("transitions to RECEIPT_LOADED_UNBOUND when selector changes away from loaded receipt config", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    // Load MNIST Stage C
    await user.click(screen.getByRole("button", { name: "MNIST Stage C" }));
    expect(screen.getByText("STRUCTURALLY_VALID_BOUND_RECEIPT")).toBeTruthy();

    // Switch model to QLoRA
    const modelSelect = screen.getByLabelText("Model Plugin");
    await user.selectOptions(modelSelect, "qlora-tiny-adapter-v1");

    expect(screen.getByText("RECEIPT_LOADED_UNBOUND")).toBeTruthy();
    expect(
      screen.getByText(
        /Receipt model 'mnist-centroid-v1' does not match selected model 'qlora-tiny-adapter-v1'/u
      )
    ).toBeTruthy();
  });

  it("clears receipt when clicking Clear Receipt button", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    await user.click(screen.getByRole("button", { name: "MNIST Stage C" }));
    expect(screen.getByText("STRUCTURALLY_VALID_BOUND_RECEIPT")).toBeTruthy();

    const clearBtn = screen.getByRole("button", { name: "Clear Receipt" });
    await user.click(clearBtn);

    expect(screen.getByText("No live execution evidence loaded.")).toBeTruthy();
  });

  it("loads EEG observation receipt and displays metrics without consensus fields", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    // Select EEG + EEG + MODEL_DATASET_BINDING_ONLY
    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");
    const scopeSelect = screen.getByLabelText("Requested Execution Scope");

    await user.selectOptions(modelSelect, "eeg-bandpower-centroid-v1");
    await user.selectOptions(datasetSelect, "eeg-synthetic-bci-v1");
    await user.selectOptions(scopeSelect, "MODEL_DATASET_BINDING_ONLY");

    // Load EEG sample
    await user.click(screen.getByRole("button", { name: "EEG Observation" }));

    expect(screen.getByText("STRUCTURALLY_VALID_BOUND_RECEIPT")).toBeTruthy();
    expect(
      screen.getByText(
        /Self-consistent local receipt bound to the active catalog configuration/u
      )
    ).toBeTruthy();
    expect(screen.getByText("Observation Record")).toBeTruthy();
    expect(screen.getByText("OBSERVATION_RECORD")).toBeTruthy();
    expect(
      screen.getByText(/Synthetic EEG 4-channel bandpower feature extraction/u)
    ).toBeTruthy();
    expect(screen.getByText("classification_accuracy")).toBeTruthy();

    // Consensus-specific fields must strictly not exist
    expect(screen.queryByText("Recorded Consensus Record")).toBeNull();
    expect(screen.queryByText("Applied Status")).toBeNull();
  });

  it("loads QLoRA receipt and displays consensus evidence alongside distinct reference anchor", async () => {
    const user = userEvent.setup();
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin");
    const datasetSelect = screen.getByLabelText("Dataset Provider");
    const scopeSelect = screen.getByLabelText("Requested Execution Scope");

    await user.selectOptions(modelSelect, "qlora-tiny-adapter-v1");
    await user.selectOptions(datasetSelect, "tiny-qlora-regression-v1");
    await user.selectOptions(scopeSelect, "STAGE_C_REAL_DRQ1");

    await user.click(screen.getByRole("button", { name: "QLoRA Stage C" }));

    expect(screen.getByText("STRUCTURALLY_VALID_BOUND_RECEIPT")).toBeTruthy();
    expect(
      screen.getByText(
        /Self-consistent local receipt bound to the active catalog configuration/u
      )
    ).toBeTruthy();
    expect(screen.getByText("Recorded Consensus Record")).toBeTruthy();
    expect(screen.getByText("UNATTESTED_CONSENSUS_RECORD")).toBeTruthy();
    expect(screen.getByText("Declared Reference Anchor")).toBeTruthy();
    expect(
      screen.getByText(
        /Baseline reference for comparison only; does not define live consensus proof/u
      )
    ).toBeTruthy();
    expect(
      screen.getByText(
        /Reference conformance baseline against PyTorch tiny QLoRA adapter/u
      )
    ).toBeTruthy();
  });

  it("rejects uploaded receipt exceeding safety file size limit (>5 MiB)", async () => {
    const { container } = render(<WorkloadSelector />);
    const fileInput = container.querySelector("#receipt-file-input") as HTMLInputElement;

    const oversizedBuffer = new Uint8Array(5_242_881);
    const oversizedFile = new File([oversizedBuffer], "oversized-receipt.json", {
      type: "application/json",
    });

    fireEvent.change(fileInput, { target: { files: [oversizedFile] } });

    await waitFor(() => {
      expect(screen.getByText("REJECTED")).toBeTruthy();
      expect(
        screen.getByText(/The selected JSON exceeds the JSON or schema file size safety limit/u)
      ).toBeTruthy();
    });
  });

  it("rejects uploaded receipt with excessive nesting depth (>64 levels)", async () => {
    const { container } = render(<WorkloadSelector />);
    const fileInput = container.querySelector("#receipt-file-input") as HTMLInputElement;

    const nestedJson = `${"[".repeat(65)}0${"]".repeat(65)}`;
    const nestedFile = new File([nestedJson], "deeply-nested-receipt.json", {
      type: "application/json",
    });

    fireEvent.change(fileInput, { target: { files: [nestedFile] } });

    await waitFor(() => {
      expect(screen.getByText("REJECTED")).toBeTruthy();
      expect(
        screen.getByText(/The selected JSON exceeds the JSON nesting depth safety limit/u)
      ).toBeTruthy();
    });
  });

  it("rejects uploaded receipt containing archive/compressed signature", async () => {
    const { container } = render(<WorkloadSelector />);
    const fileInput = container.querySelector("#receipt-file-input") as HTMLInputElement;

    const zipBytes = new Uint8Array([0x50, 0x4b, 0x03, 0x04, 0x00, 0x00]);
    const zipFile = new File([zipBytes], "receipt.zip", {
      type: "application/zip",
    });

    fireEvent.change(fileInput, { target: { files: [zipFile] } });

    await waitFor(() => {
      expect(screen.getByText("REJECTED")).toBeTruthy();
      expect(
        screen.getByText(/Archive and compressed input is not accepted/u)
      ).toBeTruthy();
    });
  });

  it("rejects uploaded receipt with invalid UTF-8 bytes", async () => {
    const { container } = render(<WorkloadSelector />);
    const fileInput = container.querySelector("#receipt-file-input") as HTMLInputElement;

    const invalidUtf8Bytes = new Uint8Array([0xc3, 0x28]);
    const badFile = new File([invalidUtf8Bytes], "bad-utf8.json", {
      type: "application/json",
    });

    fireEvent.change(fileInput, { target: { files: [badFile] } });

    await waitFor(() => {
      expect(screen.getByText("REJECTED")).toBeTruthy();
      expect(
        screen.getByText(/The selected file is not well-formed UTF-8 JSON/u)
      ).toBeTruthy();
    });
  });

  it("successfully parses and loads a valid uploaded receipt via bounded parser", async () => {
    const { container } = render(<WorkloadSelector />);
    const fileInput = container.querySelector("#receipt-file-input") as HTMLInputElement;

    const validJsonText = JSON.stringify(sampleMnistReceipt);
    const validFile = new File([validJsonText], "valid-mnist-receipt.json", {
      type: "application/json",
    });

    fireEvent.change(fileInput, { target: { files: [validFile] } });

    await waitFor(() => {
      expect(screen.getByText("STRUCTURALLY_VALID_BOUND_RECEIPT")).toBeTruthy();
      expect(screen.getByText("Recorded Consensus Record")).toBeTruthy();
      expect(screen.getByText("UNATTESTED_CONSENSUS_RECORD")).toBeTruthy();
    });
  });
});

describe("validateCatalogSnapshot", () => {
  it("validates the canonical snapshot successfully", () => {
    const validated = validateCatalogSnapshot(CANONICAL_DESCRIPTOR_CATALOG);
    expect(validated.type_name).toBe("DELTAREDUCE_DESCRIPTOR_CATALOG_SNAPSHOT");
    expect(validated.schema_version).toBe("1.0.0");
    expect(validated.compatibility).toHaveLength(
      validated.model_plugins.length * validated.datasets.length
    );
  });

  it("fails closed on non-40-character backend_ref SHA", () => {
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      source: {
        ...CANONICAL_DESCRIPTOR_CATALOG.source,
        backend_ref: "short_sha",
      },
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(CatalogValidationError);
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /backend_ref must be a full 40-character git SHA/u
    );
  });

  it("fails closed on duplicate model plugin IDs", () => {
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      model_plugins: [
        CANONICAL_DESCRIPTOR_CATALOG.model_plugins[0],
        CANONICAL_DESCRIPTOR_CATALOG.model_plugins[0],
      ],
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /Duplicate model_plugin_id/u
    );
  });

  it("fails closed on duplicate dataset IDs", () => {
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      datasets: [
        CANONICAL_DESCRIPTOR_CATALOG.datasets[0],
        CANONICAL_DESCRIPTOR_CATALOG.datasets[0],
      ],
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /Duplicate dataset_id/u
    );
  });

  it("fails closed on incomplete matrix coverage (less than models * datasets pairs)", () => {
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      compatibility: CANONICAL_DESCRIPTOR_CATALOG.compatibility.slice(0, -1),
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /Full matrix coverage violation/u
    );
  });

  it("fails closed when compatibility references an undeclared model", () => {
    const invalid: DescriptorCatalogSnapshot = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      compatibility: [
        {
          model_plugin_id: "unknown-plugin-v99",
          dataset_id: "mnist-v1",
          contract_compatible: true,
          supports_stage_c_real_drq1: true,
          requested_scope_allowed: {
            STAGE_C_REAL_DRQ1: true,
            PLUGIN_BOUNDARY: true,
            MODEL_DATASET_BINDING_ONLY: true,
          },
        },
        ...CANONICAL_DESCRIPTOR_CATALOG.compatibility.slice(1),
      ],
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /references undeclared model_plugin_id/u
    );
  });

  it("fails closed when a compatibility entry is missing a valid scope boolean", () => {
    const badEntry = {
      ...CANONICAL_DESCRIPTOR_CATALOG.compatibility[0],
      requested_scope_allowed: {
        PLUGIN_BOUNDARY: true,
        MODEL_DATASET_BINDING_ONLY: true,
        // STAGE_C_REAL_DRQ1 missing
      },
    };
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      compatibility: [badEntry, ...CANONICAL_DESCRIPTOR_CATALOG.compatibility.slice(1)],
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /missing boolean scope allowance/u
    );
  });

  it("fails closed on contradictory model capability vs compatibility row", () => {
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      compatibility: CANONICAL_DESCRIPTOR_CATALOG.compatibility.map((c) => {
        if (c.model_plugin_id === "eeg-bandpower-centroid-v1") {
          return {
            ...c,
            supports_stage_c_real_drq1: true,
          };
        }
        return c;
      }),
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(CatalogValidationError);
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /Contradictory Stage C capability: model 'eeg-bandpower-centroid-v1'/u
    );
  });

  it("fails closed when STAGE_C_REAL_DRQ1 is allowed but contract_compatible is false", () => {
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      compatibility: CANONICAL_DESCRIPTOR_CATALOG.compatibility.map((c) => {
        if (c.model_plugin_id === "mnist-centroid-v1" && c.dataset_id === "mnist-v1") {
          return {
            ...c,
            contract_compatible: false,
            requested_scope_allowed: {
              ...c.requested_scope_allowed,
              STAGE_C_REAL_DRQ1: true,
            },
          };
        }
        return c;
      }),
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(CatalogValidationError);
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /allows STAGE_C_REAL_DRQ1 but contract_compatible is false/u
    );
  });

  it("fails closed when STAGE_C_REAL_DRQ1 is allowed but supports_stage_c_real_drq1 is false", () => {
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      compatibility: CANONICAL_DESCRIPTOR_CATALOG.compatibility.map((c) => {
        if (
          c.model_plugin_id === "eeg-bandpower-centroid-v1" &&
          c.dataset_id === "eeg-synthetic-bci-v1"
        ) {
          return {
            ...c,
            requested_scope_allowed: {
              ...c.requested_scope_allowed,
              STAGE_C_REAL_DRQ1: true,
            },
          };
        }
        return c;
      }),
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(CatalogValidationError);
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /allows STAGE_C_REAL_DRQ1 but supports_stage_c_real_drq1 is false/u
    );
  });

  it("fails closed when requested_scope_allowed contains an unknown scope key", () => {
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      compatibility: CANONICAL_DESCRIPTOR_CATALOG.compatibility.map((c, idx) => {
        if (idx === 0) {
          return {
            ...c,
            requested_scope_allowed: {
              ...c.requested_scope_allowed,
              FUTURE_UNKNOWN_SCOPE: true,
            },
          };
        }
        return c;
      }),
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(CatalogValidationError);
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /contains unknown scope key: 'FUTURE_UNKNOWN_SCOPE'/u
    );
  });

  it("fails closed when a model descriptor is missing required metadata", () => {
    const badModel = {
      ...CANONICAL_DESCRIPTOR_CATALOG.model_plugins[0],
      model_family: "",
    };
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      model_plugins: [badModel, ...CANONICAL_DESCRIPTOR_CATALOG.model_plugins.slice(1)],
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(CatalogValidationError);
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /Invalid model_plugin entry in catalog/u
    );
  });

  it("fails closed when a dataset descriptor is missing required metadata", () => {
    const badDataset = {
      ...CANONICAL_DESCRIPTOR_CATALOG.datasets[0],
      description: "",
    };
    const invalid = {
      ...CANONICAL_DESCRIPTOR_CATALOG,
      datasets: [badDataset, ...CANONICAL_DESCRIPTOR_CATALOG.datasets.slice(1)],
    };
    expect(() => validateCatalogSnapshot(invalid)).toThrow(CatalogValidationError);
    expect(() => validateCatalogSnapshot(invalid)).toThrow(
      /Invalid dataset entry in catalog/u
    );
  });
});
