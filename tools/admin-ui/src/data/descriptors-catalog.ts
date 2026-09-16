import catalogJson from "./descriptors-catalog.snapshot.json";

export const VALID_SCOPES = [
  "PLUGIN_BOUNDARY",
  "STAGE_C_REAL_DRQ1",
  "MODEL_DATASET_BINDING_ONLY",
] as const;

export type ExecutionScopeName = (typeof VALID_SCOPES)[number];

export interface ModelPluginDescriptorEntry {
  readonly plugin_id: string;
  readonly display_name: string;
  readonly model_family: string;
  readonly task_type: string;
  readonly sample_kind: string;
  readonly target_kind: string;
  readonly deterministic: boolean;
  readonly supports_stage_c_real_drq1: boolean;
  readonly parameter_schema_id: string | null;
}

export interface DatasetDescriptorEntry {
  readonly dataset_id: string;
  readonly display_name: string;
  readonly sample_kind: string;
  readonly target_kind: string;
  readonly deterministic: boolean;
  readonly supports_offline_cache: boolean;
  readonly description: string;
  readonly version: string;
}

export interface CompatibilityMatrixEntry {
  readonly model_plugin_id: string;
  readonly dataset_id: string;
  readonly contract_compatible: boolean;
  readonly supports_stage_c_real_drq1: boolean;
  readonly requested_scope_allowed: Readonly<Record<ExecutionScopeName, boolean>>;
}

export interface CatalogSourceProvenance {
  readonly repository: string;
  readonly backend_ref: string;
  readonly generator_contract: string;
}

export interface DescriptorCatalogSnapshot {
  readonly type_name: "DELTAREDUCE_DESCRIPTOR_CATALOG_SNAPSHOT";
  readonly schema_version: "1.0.0";
  readonly source: CatalogSourceProvenance;
  readonly model_plugins: readonly ModelPluginDescriptorEntry[];
  readonly datasets: readonly DatasetDescriptorEntry[];
  readonly compatibility: readonly CompatibilityMatrixEntry[];
}

export class CatalogValidationError extends Error {
  constructor(message: string) {
    super(`CATALOG_VALIDATION_ERROR: ${message}`);
    this.name = "CatalogValidationError";
  }
}

export function validateCatalogSnapshot(raw: unknown): DescriptorCatalogSnapshot {
  if (typeof raw !== "object" || raw === null) {
    throw new CatalogValidationError("Catalog snapshot must be an object");
  }
  const obj = raw as Record<string, unknown>;

  if (obj.type_name !== "DELTAREDUCE_DESCRIPTOR_CATALOG_SNAPSHOT") {
    throw new CatalogValidationError(`Invalid type_name: ${String(obj.type_name)}`);
  }
  if (obj.schema_version !== "1.0.0") {
    throw new CatalogValidationError(`Invalid schema_version: ${String(obj.schema_version)}`);
  }

  // 1. Source Provenance Validation
  if (typeof obj.source !== "object" || obj.source === null) {
    throw new CatalogValidationError("Missing source provenance object");
  }
  const source = obj.source as Record<string, unknown>;
  if (
    typeof source.repository !== "string" ||
    !source.repository.trim() ||
    typeof source.generator_contract !== "string" ||
    !source.generator_contract.trim()
  ) {
    throw new CatalogValidationError("Invalid repository or generator_contract in source provenance");
  }
  if (
    typeof source.backend_ref !== "string" ||
    !/^[0-9a-f]{40}$/u.test(source.backend_ref)
  ) {
    throw new CatalogValidationError(
      `backend_ref must be a full 40-character git SHA hex string, got: ${String(source.backend_ref)}`
    );
  }

  // 2. Model Plugins Validation & Unique IDs
  if (!Array.isArray(obj.model_plugins) || obj.model_plugins.length === 0) {
    throw new CatalogValidationError("model_plugins must be a non-empty array");
  }
  const modelMap = new Map<string, ModelPluginDescriptorEntry>();
  for (const m of obj.model_plugins) {
    if (
      typeof m !== "object" ||
      m === null ||
      typeof m.plugin_id !== "string" ||
      !m.plugin_id.trim() ||
      typeof m.display_name !== "string" ||
      !m.display_name.trim() ||
      typeof m.model_family !== "string" ||
      !m.model_family.trim() ||
      typeof m.task_type !== "string" ||
      !m.task_type.trim() ||
      typeof m.sample_kind !== "string" ||
      !m.sample_kind.trim() ||
      typeof m.target_kind !== "string" ||
      !m.target_kind.trim() ||
      typeof m.deterministic !== "boolean" ||
      typeof m.supports_stage_c_real_drq1 !== "boolean" ||
      !(
        m.parameter_schema_id === null ||
        (typeof m.parameter_schema_id === "string" && m.parameter_schema_id.trim().length > 0)
      )
    ) {
      throw new CatalogValidationError("Invalid model_plugin entry in catalog");
    }
    if (modelMap.has(m.plugin_id)) {
      throw new CatalogValidationError(`Duplicate model_plugin_id: ${m.plugin_id}`);
    }
    modelMap.set(m.plugin_id, m as unknown as ModelPluginDescriptorEntry);
  }

  // 3. Datasets Validation & Unique IDs
  if (!Array.isArray(obj.datasets) || obj.datasets.length === 0) {
    throw new CatalogValidationError("datasets must be a non-empty array");
  }
  const datasetIds = new Set<string>();
  for (const d of obj.datasets) {
    if (
      typeof d !== "object" ||
      d === null ||
      typeof d.dataset_id !== "string" ||
      !d.dataset_id.trim() ||
      typeof d.display_name !== "string" ||
      !d.display_name.trim() ||
      typeof d.sample_kind !== "string" ||
      !d.sample_kind.trim() ||
      typeof d.target_kind !== "string" ||
      !d.target_kind.trim() ||
      typeof d.deterministic !== "boolean" ||
      typeof d.supports_offline_cache !== "boolean" ||
      typeof d.description !== "string" ||
      !d.description.trim() ||
      typeof d.version !== "string" ||
      !d.version.trim()
    ) {
      throw new CatalogValidationError("Invalid dataset entry in catalog");
    }
    if (datasetIds.has(d.dataset_id)) {
      throw new CatalogValidationError(`Duplicate dataset_id: ${d.dataset_id}`);
    }
    datasetIds.add(d.dataset_id);
  }

  // 4. Compatibility Matrix Validation & Full Matrix Coverage
  if (!Array.isArray(obj.compatibility)) {
    throw new CatalogValidationError("compatibility must be an array");
  }
  const expectedPairsCount = modelMap.size * datasetIds.size;
  if (obj.compatibility.length !== expectedPairsCount) {
    throw new CatalogValidationError(
      `Full matrix coverage violation: expected exactly ${expectedPairsCount} compatibility pairs (${modelMap.size} models * ${datasetIds.size} datasets), got ${obj.compatibility.length}`
    );
  }

  const seenPairs = new Set<string>();
  for (const c of obj.compatibility) {
    if (
      typeof c !== "object" ||
      c === null ||
      typeof c.model_plugin_id !== "string" ||
      typeof c.dataset_id !== "string" ||
      typeof c.contract_compatible !== "boolean" ||
      typeof c.supports_stage_c_real_drq1 !== "boolean" ||
      typeof c.requested_scope_allowed !== "object" ||
      c.requested_scope_allowed === null
    ) {
      throw new CatalogValidationError("Invalid compatibility matrix entry in catalog");
    }

    const model = modelMap.get(c.model_plugin_id);
    if (!model) {
      throw new CatalogValidationError(
        `Compatibility matrix references undeclared model_plugin_id: ${c.model_plugin_id}`
      );
    }
    if (!datasetIds.has(c.dataset_id)) {
      throw new CatalogValidationError(
        `Compatibility matrix references undeclared dataset_id: ${c.dataset_id}`
      );
    }

    // Fail-closed invariant: compatibility row must strictly match model descriptor Stage C capability
    if (c.supports_stage_c_real_drq1 !== model.supports_stage_c_real_drq1) {
      throw new CatalogValidationError(
        `Contradictory Stage C capability: model '${c.model_plugin_id}' declares supports_stage_c_real_drq1=${model.supports_stage_c_real_drq1}, but compatibility entry declares ${c.supports_stage_c_real_drq1}`
      );
    }

    const pairKey = `${c.model_plugin_id}::${c.dataset_id}`;
    if (seenPairs.has(pairKey)) {
      throw new CatalogValidationError(`Duplicate compatibility pair: ${pairKey}`);
    }
    seenPairs.add(pairKey);

    const scopesAllowed = c.requested_scope_allowed as Record<string, unknown>;
    const scopeKeys = Object.keys(scopesAllowed);
    for (const key of scopeKeys) {
      if (!VALID_SCOPES.includes(key as ExecutionScopeName)) {
        throw new CatalogValidationError(
          `Compatibility pair ${pairKey} contains unknown scope key: '${key}'`
        );
      }
    }
    for (const scope of VALID_SCOPES) {
      if (typeof scopesAllowed[scope] !== "boolean") {
        throw new CatalogValidationError(
          `Compatibility pair ${pairKey} missing boolean scope allowance for '${scope}'`
        );
      }
    }

    // Fail-closed invariant: if STAGE_C_REAL_DRQ1 is allowed, contract must be compatible and model must support Stage C
    if (scopesAllowed.STAGE_C_REAL_DRQ1 === true) {
      if (c.contract_compatible !== true) {
        throw new CatalogValidationError(
          `Contradictory Stage C allowance: pair ${pairKey} allows STAGE_C_REAL_DRQ1 but contract_compatible is false`
        );
      }
      if (c.supports_stage_c_real_drq1 !== true) {
        throw new CatalogValidationError(
          `Contradictory Stage C allowance: pair ${pairKey} allows STAGE_C_REAL_DRQ1 but supports_stage_c_real_drq1 is false`
        );
      }
    }
  }

  // Ensure all Cartesian product pairs are covered
  for (const mId of modelMap.keys()) {
    for (const dId of datasetIds) {
      const pairKey = `${mId}::${dId}`;
      if (!seenPairs.has(pairKey)) {
        throw new CatalogValidationError(`Missing compatibility entry for pair: ${pairKey}`);
      }
    }
  }

  return raw as DescriptorCatalogSnapshot;
}

export const CANONICAL_DESCRIPTOR_CATALOG: DescriptorCatalogSnapshot =
  validateCatalogSnapshot(catalogJson);
