import { execFile } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

import { describe, expect, it } from "vitest";

import {
  generateCatalogSnapshot,
  validateGeneratedSnapshot,
  writeCatalogSnapshotAtomically,
} from "../../scripts/generate-catalog-snapshot.mjs";
import { validateCatalogSnapshot } from "./descriptors-catalog";
import rawSnapshot from "./descriptors-catalog.snapshot.json";

const execFileAsync = promisify(execFile);

describe("catalog snapshot generator and drift gate", () => {
  it("passes --check against current tools/registry with exit code 0", async () => {
    const { stdout } = await execFileAsync(
      process.execPath,
      ["scripts/generate-catalog-snapshot.mjs", "--check"],
      { cwd: process.cwd() }
    );
    expect(stdout).toContain("Catalog snapshot is in sync with tools/registry.");
  });

  it("produces a canonical snapshot passing strict validateCatalogSnapshot", () => {
    const validated = validateCatalogSnapshot(rawSnapshot);
    expect(validated.type_name).toBe("DELTAREDUCE_DESCRIPTOR_CATALOG_SNAPSHOT");
    expect(validated.model_plugins.length).toBeGreaterThanOrEqual(3);
    expect(validated.datasets.length).toBeGreaterThanOrEqual(3);
    expect(validated.compatibility.length).toBe(
      validated.model_plugins.length * validated.datasets.length
    );
  });

  it("enforces canonical sorting strictly by plugin_id and dataset_id", async () => {
    const rawJson = await generateCatalogSnapshot();
    const parsed = JSON.parse(rawJson);

    const modelIds = parsed.model_plugins.map((m: any) => m.plugin_id);
    const sortedModelIds = [...modelIds].sort((a, b) => a.localeCompare(b));
    expect(modelIds).toEqual(sortedModelIds);

    const datasetIds = parsed.datasets.map((d: any) => d.dataset_id);
    const sortedDatasetIds = [...datasetIds].sort((a, b) => a.localeCompare(b));
    expect(datasetIds).toEqual(sortedDatasetIds);
  });

  it("enforces fail-closed compatibility invariants on every entry in catalog", () => {
    const modelMap = new Map(rawSnapshot.model_plugins.map((m: any) => [m.plugin_id, m]));
    const datasetMap = new Map(rawSnapshot.datasets.map((d: any) => [d.dataset_id, d]));

    for (const entry of rawSnapshot.compatibility) {
      const model: any = modelMap.get(entry.model_plugin_id);
      const dataset: any = datasetMap.get(entry.dataset_id);

      expect(model).toBeDefined();
      expect(dataset).toBeDefined();

      const expectedCompatible =
        model.sample_kind === dataset.sample_kind && model.target_kind === dataset.target_kind;

      expect(entry.contract_compatible).toBe(expectedCompatible);
      expect(entry.supports_stage_c_real_drq1).toBe(model.supports_stage_c_real_drq1);

      expect(entry.requested_scope_allowed.STAGE_C_REAL_DRQ1).toBe(
        expectedCompatible && model.supports_stage_c_real_drq1
      );
      expect(entry.requested_scope_allowed.PLUGIN_BOUNDARY).toBe(expectedCompatible);
      expect(entry.requested_scope_allowed.MODEL_DATASET_BINDING_ONLY).toBe(expectedCompatible);
    }
  });

  it("maintains observation-only status for EEG model in generated matrix", () => {
    const eegEntries = rawSnapshot.compatibility.filter(
      (c: any) => c.model_plugin_id === "eeg-bandpower-centroid-v1"
    );

    expect(eegEntries.length).toBeGreaterThanOrEqual(3);
    for (const eeg of eegEntries) {
      expect(eeg.supports_stage_c_real_drq1).toBe(false);
      expect(eeg.requested_scope_allowed.STAGE_C_REAL_DRQ1).toBe(false);
    }
  });

  it("validates valid snapshot and rejects malformed snapshots fail-closed in validateGeneratedSnapshot", () => {
    expect(validateGeneratedSnapshot(rawSnapshot)).toBeDefined();

    expect(() =>
      validateGeneratedSnapshot({ ...rawSnapshot, type_name: "WRONG_TYPE" })
    ).toThrow(/Invalid type_name/u);

    expect(() =>
      validateGeneratedSnapshot({ ...rawSnapshot, schema_version: "2.0.0" })
    ).toThrow(/Invalid schema_version/u);

    expect(() =>
      validateGeneratedSnapshot({
        ...rawSnapshot,
        source: { ...rawSnapshot.source, backend_ref: "short" },
      })
    ).toThrow(/Invalid source.backend_ref/u);

    expect(() =>
      validateGeneratedSnapshot({
        ...rawSnapshot,
        compatibility: rawSnapshot.compatibility.slice(0, 2),
      })
    ).toThrow(/compatibility matrix must contain exactly/u);
  });

  it("writes snapshots atomically via temp file replacement", async () => {
    const tempDir = await mkdtemp(join(tmpdir(), "catalog-test-"));
    const targetFile = join(tempDir, "snapshot.json");

    try {
      await writeCatalogSnapshotAtomically(targetFile, '{"test": true}\n');
      const content = await readFile(targetFile, "utf8");
      expect(content).toBe('{"test": true}\n');
    } finally {
      await rm(tempDir, { recursive: true, force: true });
    }
  });

  it("detects drift and exits 1 when CLI --backend-ref differs from committed snapshot", async () => {
    const overrideRef = "1111111111111111111111111111111111111111";
    let failed = false;
    try {
      await execFileAsync(
        process.execPath,
        ["scripts/generate-catalog-snapshot.mjs", "--backend-ref", overrideRef, "--check"],
        { cwd: process.cwd() }
      );
    } catch (err: any) {
      failed = true;
      expect(err.code).toBe(1);
      expect(err.stderr).toContain("is stale or drifted from tools/registry");
    }
    expect(failed).toBe(true);
  });

  it("strictly rejects 64-character SHA or non-40-hex backend_ref fail-closed", async () => {
    const sha64 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

    await expect(generateCatalogSnapshot({ backendRef: sha64 })).rejects.toThrow(
      /must be a 40-character hex commit SHA/u
    );

    await expect(generateCatalogSnapshot({ backendRef: "not-a-sha" })).rejects.toThrow(
      /must be a 40-character hex commit SHA/u
    );

    expect(() =>
      validateGeneratedSnapshot({
        ...rawSnapshot,
        source: { ...rawSnapshot.source, backend_ref: sha64 },
      })
    ).toThrow(/must be 40 hex characters/u);
  });
});
