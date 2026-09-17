import { readdir, readFile, rename, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

let scriptsDir;
try {
  scriptsDir = fileURLToPath(new URL(".", import.meta.url));
} catch {
  scriptsDir = resolve(process.cwd(), "scripts");
}
const adminUiRoot = resolve(scriptsDir, "..");
const repoToolsRoot = resolve(adminUiRoot, "..");
const defaultRegistryRoot = resolve(repoToolsRoot, "registry");
const defaultSnapshotPath = resolve(adminUiRoot, "src/data/descriptors-catalog.snapshot.json");

const ALLOWED_SCOPE_KEYS = ["STAGE_C_REAL_DRQ1", "PLUGIN_BOUNDARY", "MODEL_DATASET_BINDING_ONLY"];

export function validateGeneratedSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== "object") {
    throw new Error("Generated snapshot must be an object");
  }
  if (snapshot.type_name !== "DELTAREDUCE_DESCRIPTOR_CATALOG_SNAPSHOT") {
    throw new Error(`Invalid type_name: expected 'DELTAREDUCE_DESCRIPTOR_CATALOG_SNAPSHOT', got '${snapshot.type_name}'`);
  }
  if (snapshot.schema_version !== "1.0.0") {
    throw new Error(`Invalid schema_version: expected '1.0.0', got '${snapshot.schema_version}'`);
  }
  if (!snapshot.source || typeof snapshot.source !== "object") {
    throw new Error("Missing or invalid source object in snapshot");
  }
  if (!snapshot.source.repository || !snapshot.source.repository.trim()) {
    throw new Error("Missing or empty source.repository in snapshot");
  }
  if (!snapshot.source.backend_ref || !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/u.test(snapshot.source.backend_ref)) {
    throw new Error("Invalid source.backend_ref: must be 40 or 64 hex characters");
  }
  if (snapshot.source.generator_contract !== "validate_model_dataset_capability") {
    throw new Error(`Invalid generator_contract: expected 'validate_model_dataset_capability', got '${snapshot.source.generator_contract}'`);
  }

  if (!Array.isArray(snapshot.model_plugins) || snapshot.model_plugins.length === 0) {
    throw new Error("model_plugins must be a non-empty array");
  }
  if (!Array.isArray(snapshot.datasets) || snapshot.datasets.length === 0) {
    throw new Error("datasets must be a non-empty array");
  }

  const modelMap = new Map();
  for (const m of snapshot.model_plugins) {
    if (modelMap.has(m.plugin_id)) {
      throw new Error(`Duplicate plugin_id in model_plugins: '${m.plugin_id}'`);
    }
    modelMap.set(m.plugin_id, m);
  }

  const datasetMap = new Map();
  for (const d of snapshot.datasets) {
    if (datasetMap.has(d.dataset_id)) {
      throw new Error(`Duplicate dataset_id in datasets: '${d.dataset_id}'`);
    }
    datasetMap.set(d.dataset_id, d);
  }

  const expectedPairs = snapshot.model_plugins.length * snapshot.datasets.length;
  if (!Array.isArray(snapshot.compatibility) || snapshot.compatibility.length !== expectedPairs) {
    throw new Error(`compatibility matrix must contain exactly ${expectedPairs} entries, got ${snapshot.compatibility?.length}`);
  }

  const seenPairs = new Set();
  for (const c of snapshot.compatibility) {
    const pairKey = `${c.model_plugin_id}:${c.dataset_id}`;
    if (seenPairs.has(pairKey)) {
      throw new Error(`Duplicate compatibility entry for pair '${pairKey}'`);
    }
    seenPairs.add(pairKey);

    const model = modelMap.get(c.model_plugin_id);
    const dataset = datasetMap.get(c.dataset_id);
    if (!model || !dataset) {
      throw new Error(`Compatibility entry references unknown model or dataset: '${pairKey}'`);
    }

    const expectedCompatible = model.sample_kind === dataset.sample_kind && model.target_kind === dataset.target_kind;
    if (c.contract_compatible !== expectedCompatible) {
      throw new Error(`contract_compatible mismatch for '${pairKey}': expected ${expectedCompatible}, got ${c.contract_compatible}`);
    }
    if (c.supports_stage_c_real_drq1 !== model.supports_stage_c_real_drq1) {
      throw new Error(`supports_stage_c_real_drq1 mismatch for '${pairKey}': expected ${model.supports_stage_c_real_drq1}, got ${c.supports_stage_c_real_drq1}`);
    }

    const scopeKeys = Object.keys(c.requested_scope_allowed || {});
    if (scopeKeys.length !== ALLOWED_SCOPE_KEYS.length || !ALLOWED_SCOPE_KEYS.every((k) => scopeKeys.includes(k))) {
      throw new Error(`Invalid requested_scope_allowed keys for '${pairKey}': expected exactly [${ALLOWED_SCOPE_KEYS.join(", ")}], got [${scopeKeys.join(", ")}]`);
    }

    if (c.requested_scope_allowed.STAGE_C_REAL_DRQ1) {
      if (!c.contract_compatible || !c.supports_stage_c_real_drq1) {
        throw new Error(`Contradictory STAGE_C_REAL_DRQ1 allowance for '${pairKey}'`);
      }
    }
    if (!model.supports_stage_c_real_drq1 && c.requested_scope_allowed.STAGE_C_REAL_DRQ1) {
      throw new Error(`Observation-only model cannot allow STAGE_C_REAL_DRQ1 for '${pairKey}'`);
    }
  }

  return snapshot;
}

export async function generateCatalogSnapshot(options = {}) {
  const registryRoot = options.registryRoot || defaultRegistryRoot;
  const ajv = new Ajv2020({ allErrors: true, strict: true, validateFormats: false });

  const schemasDir = resolve(registryRoot, "schemas");
  const pluginsDir = resolve(registryRoot, "plugins");
  const datasetsDir = resolve(registryRoot, "datasets");
  const provenancePath = resolve(registryRoot, "provenance.json");

  const pluginSchema = JSON.parse(await readFile(resolve(schemasDir, "plugin-descriptor.schema.json"), "utf8"));
  const datasetSchema = JSON.parse(await readFile(resolve(schemasDir, "dataset-descriptor.schema.json"), "utf8"));
  const provenanceSchema = JSON.parse(await readFile(resolve(schemasDir, "provenance.schema.json"), "utf8"));
  const provenance = JSON.parse(await readFile(provenancePath, "utf8"));

  const validatePlugin = ajv.compile(pluginSchema);
  const validateDataset = ajv.compile(datasetSchema);
  const validateProvenance = ajv.compile(provenanceSchema);

  if (!validateProvenance(provenance)) {
    throw new Error(`Invalid provenance.json: ${JSON.stringify(validateProvenance.errors)}`);
  }

  const pluginFiles = (await readdir(pluginsDir)).filter((f) => f.endsWith(".json"));
  const datasetFiles = (await readdir(datasetsDir)).filter((f) => f.endsWith(".json"));

  const modelPlugins = [];
  const seenPluginIds = new Set();
  for (const file of pluginFiles) {
    const raw = JSON.parse(await readFile(resolve(pluginsDir, file), "utf8"));
    const valid = validatePlugin(raw);
    if (!valid) {
      throw new Error(`Invalid plugin manifest '${file}': ${JSON.stringify(validatePlugin.errors)}`);
    }
    if (seenPluginIds.has(raw.plugin_id)) {
      throw new Error(`Duplicate plugin_id '${raw.plugin_id}' found in '${file}'`);
    }
    seenPluginIds.add(raw.plugin_id);
    modelPlugins.push(raw);
  }

  const datasets = [];
  const seenDatasetIds = new Set();
  for (const file of datasetFiles) {
    const raw = JSON.parse(await readFile(resolve(datasetsDir, file), "utf8"));
    const valid = validateDataset(raw);
    if (!valid) {
      throw new Error(`Invalid dataset manifest '${file}': ${JSON.stringify(validateDataset.errors)}`);
    }
    if (seenDatasetIds.has(raw.dataset_id)) {
      throw new Error(`Duplicate dataset_id '${raw.dataset_id}' found in '${file}'`);
    }
    seenDatasetIds.add(raw.dataset_id);
    datasets.push(raw);
  }

  // Canonical sort strictly by descriptor IDs
  modelPlugins.sort((a, b) => a.plugin_id.localeCompare(b.plugin_id));
  datasets.sort((a, b) => a.dataset_id.localeCompare(b.dataset_id));

  // Deterministic Cartesian compatibility matrix
  const compatibility = [];
  for (const model of modelPlugins) {
    for (const dataset of datasets) {
      const contractCompatible =
        model.sample_kind === dataset.sample_kind && model.target_kind === dataset.target_kind;
      const supportsStageC = model.supports_stage_c_real_drq1;

      compatibility.push({
        model_plugin_id: model.plugin_id,
        dataset_id: dataset.dataset_id,
        contract_compatible: contractCompatible,
        supports_stage_c_real_drq1: supportsStageC,
        requested_scope_allowed: {
          STAGE_C_REAL_DRQ1: contractCompatible && supportsStageC,
          PLUGIN_BOUNDARY: contractCompatible,
          MODEL_DATASET_BINDING_ONLY: contractCompatible,
        },
      });
    }
  }

  const backendRef = options.backendRef || provenance.backend_ref;

  const snapshot = {
    type_name: "DELTAREDUCE_DESCRIPTOR_CATALOG_SNAPSHOT",
    schema_version: "1.0.0",
    source: {
      repository: provenance.repository,
      backend_ref: backendRef,
      generator_contract: provenance.generator_contract,
    },
    model_plugins: modelPlugins,
    datasets: datasets,
    compatibility: compatibility,
  };

  // Fail-closed validation before returning
  validateGeneratedSnapshot(snapshot);

  return `${JSON.stringify(snapshot, null, 2)}\n`;
}

export async function writeCatalogSnapshotAtomically(targetPath, content) {
  const tempPath = `${targetPath}.tmp.${Date.now()}`;
  await writeFile(tempPath, content, "utf8");
  await rename(tempPath, targetPath);
}

async function main() {
  const isCheck = process.argv.includes("--check");
  const targetSnapshotPath = defaultSnapshotPath;

  const generated = await generateCatalogSnapshot();

  if (isCheck) {
    const existing = await readFile(targetSnapshotPath, "utf8").catch(() => "");
    const normExisting = existing.replace(/\r\n/gu, "\n");
    const normGenerated = generated.replace(/\r\n/gu, "\n");

    if (normExisting !== normGenerated) {
      process.stderr.write(
        `${targetSnapshotPath} is stale or drifted from tools/registry; run 'npm run generate:catalog'.\n`
      );
      process.exitCode = 1;
    } else {
      process.stdout.write("Catalog snapshot is in sync with tools/registry.\n");
    }
  } else {
    await writeCatalogSnapshotAtomically(targetSnapshotPath, generated);
    process.stdout.write(`Successfully generated ${targetSnapshotPath} from tools/registry (atomic write).\n`);
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  main().catch((err) => {
    process.stderr.write(`${err.stack || err.message || String(err)}\n`);
    process.exitCode = 1;
  });
}
