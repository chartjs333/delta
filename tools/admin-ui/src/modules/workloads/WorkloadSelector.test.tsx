import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  CANONICAL_DESCRIPTOR_CATALOG,
  CatalogValidationError,
  validateCatalogSnapshot,
  type DescriptorCatalogSnapshot,
} from "../../data/descriptors-catalog";
import { WorkloadSelector } from "./WorkloadSelector";

describe("WorkloadSelector", () => {
  it("renders 3 model plugins and 3 datasets from the canonical snapshot", () => {
    render(<WorkloadSelector />);

    const modelSelect = screen.getByLabelText("Model Plugin") as HTMLSelectElement;
    const datasetSelect = screen.getByLabelText("Dataset Provider") as HTMLSelectElement;

    expect(modelSelect.options).toHaveLength(3);
    expect(Array.from(modelSelect.options).map((o) => o.value)).toEqual([
      "mnist-centroid-v1",
      "qlora-tiny-adapter-v1",
      "eeg-bandpower-centroid-v1",
    ]);

    expect(datasetSelect.options).toHaveLength(3);
    expect(Array.from(datasetSelect.options).map((o) => o.value)).toEqual([
      "mnist-v1",
      "tiny-qlora-regression-v1",
      "eeg-synthetic-bci-v1",
    ]);
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
});

describe("validateCatalogSnapshot", () => {
  it("validates the canonical snapshot successfully", () => {
    const validated = validateCatalogSnapshot(CANONICAL_DESCRIPTOR_CATALOG);
    expect(validated.type_name).toBe("DELTAREDUCE_DESCRIPTOR_CATALOG_SNAPSHOT");
    expect(validated.schema_version).toBe("1.0.0");
    expect(validated.source.backend_ref).toHaveLength(40);
    expect(validated.compatibility).toHaveLength(9);
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
      compatibility: CANONICAL_DESCRIPTOR_CATALOG.compatibility.slice(0, 8),
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
});
