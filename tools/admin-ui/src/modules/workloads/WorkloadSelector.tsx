import { useId, useState } from "react";
import {
  CANONICAL_DESCRIPTOR_CATALOG,
  VALID_SCOPES,
  type DescriptorCatalogSnapshot,
  type ExecutionScopeName,
} from "../../data/descriptors-catalog";
import { InertText } from "../../components/InertText";

export interface WorkloadSelectorProps {
  readonly catalog?: DescriptorCatalogSnapshot;
}

export function WorkloadSelector({
  catalog = CANONICAL_DESCRIPTOR_CATALOG,
}: WorkloadSelectorProps) {
  const modelSelectId = useId();
  const datasetSelectId = useId();
  const scopeSelectId = useId();

  const [selectedModelId, setSelectedModelId] = useState<string>(
    catalog.model_plugins[0]?.plugin_id ?? ""
  );
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(
    catalog.datasets[0]?.dataset_id ?? ""
  );
  const [selectedScope, setSelectedScope] = useState<ExecutionScopeName>(
    "STAGE_C_REAL_DRQ1"
  );

  const selectedModel = catalog.model_plugins.find(
    (m) => m.plugin_id === selectedModelId
  );
  const selectedDataset = catalog.datasets.find(
    (d) => d.dataset_id === selectedDatasetId
  );

  const compatibilityEntry = catalog.compatibility.find(
    (c) =>
      c.model_plugin_id === selectedModelId &&
      c.dataset_id === selectedDatasetId
  );

  const contractCompatible = compatibilityEntry?.contract_compatible ?? false;
  const supportsStageC = compatibilityEntry?.supports_stage_c_real_drq1 ?? false;
  const isScopeAllowed =
    compatibilityEntry?.requested_scope_allowed[selectedScope] ?? false;

  let statusText = "ALLOWED";
  let rejectionReason: string | undefined;

  if (!compatibilityEntry) {
    statusText = "REJECTED";
    rejectionReason = "combination not registered in catalog";
  } else if (!contractCompatible) {
    statusText = "REJECTED";
    rejectionReason = "contract incompatible: sample/target kind mismatch";
  } else if (!isScopeAllowed) {
    statusText = "REJECTED";
    rejectionReason = "requested scope not allowed by catalog";
  }

  const isAllowed = statusText === "ALLOWED";

  return (
    <section className="workloads-container" aria-labelledby="workloads-heading">
      <header className="workloads-header">
        <p className="eyebrow">Descriptor-Driven Execution Selector</p>
        <h1 id="workloads-heading">Workloads</h1>
        <p>
          Configure and inspect candidate model and dataset combinations against
          the frozen descriptor catalog. Pre-flight capabilities are verified directly
          from registry descriptors; execution evidence is strictly isolated.
        </p>
      </header>

      <div className="workload-controls-grid">
        <div className="control-group">
          <label htmlFor={modelSelectId}>Model Plugin</label>
          <select
            id={modelSelectId}
            value={selectedModelId}
            onChange={(e) => setSelectedModelId(e.target.value)}
          >
            {catalog.model_plugins.map((m) => (
              <option key={m.plugin_id} value={m.plugin_id}>
                {m.display_name} ({m.plugin_id})
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor={datasetSelectId}>Dataset Provider</label>
          <select
            id={datasetSelectId}
            value={selectedDatasetId}
            onChange={(e) => setSelectedDatasetId(e.target.value)}
          >
            {catalog.datasets.map((d) => (
              <option key={d.dataset_id} value={d.dataset_id}>
                {d.display_name} ({d.dataset_id})
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor={scopeSelectId}>Requested Execution Scope</label>
          <select
            id={scopeSelectId}
            value={selectedScope}
            onChange={(e) => setSelectedScope(e.target.value as ExecutionScopeName)}
          >
            {VALID_SCOPES.map((scope) => {
              const allowed =
                compatibilityEntry?.requested_scope_allowed[scope] ?? false;
              return (
                <option key={scope} value={scope}>
                  {scope} {allowed ? "" : "(not allowed)"}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      <div className="workload-panels-grid">
        {/* Panel 1: Pre-flight capability */}
        <article
          className="panel workload-panel preflight-panel"
          aria-labelledby="preflight-heading"
        >
          <div className="panel-header">
            <p className="eyebrow">Catalog Verification</p>
            <h2 id="preflight-heading">Pre-flight capability</h2>
          </div>

          <dl className="property-list">
            <div>
              <dt>Model</dt>
              <dd>
                <strong>
                  <InertText value={selectedModel?.display_name ?? selectedModelId} />
                </strong>
                <span className="code-subtext">
                  <InertText value={selectedModelId} /> · sample:{" "}
                  <InertText value={selectedModel?.sample_kind ?? "unknown"} />
                </span>
              </dd>
            </div>

            <div>
              <dt>Dataset</dt>
              <dd>
                <strong>
                  <InertText value={selectedDataset?.display_name ?? selectedDatasetId} />
                </strong>
                <span className="code-subtext">
                  <InertText value={selectedDatasetId} /> · sample:{" "}
                  <InertText value={selectedDataset?.sample_kind ?? "unknown"} />
                </span>
              </dd>
            </div>

            <div>
              <dt>Requested Scope</dt>
              <dd>
                <code>{selectedScope}</code>
              </dd>
            </div>

            <div>
              <dt>Contract</dt>
              <dd>
                <span
                  className={`status-pill ${
                    contractCompatible ? "pill-ok" : "pill-warn"
                  }`}
                >
                  {contractCompatible ? "compatible" : "incompatible"}
                </span>
              </dd>
            </div>

            <div>
              <dt>Capability</dt>
              <dd>
                <span
                  className={`status-pill ${
                    supportsStageC ? "pill-capable" : "pill-smoke"
                  }`}
                >
                  {supportsStageC ? "Stage C capable" : "Observation only"}
                </span>
              </dd>
            </div>
          </dl>

          <div
            className={`verdict-box ${
              isAllowed ? "verdict-allowed" : "verdict-rejected"
            }`}
            role="status"
          >
            <div className="verdict-status">
              <span>Status:</span>
              <strong className="verdict-label">{statusText}</strong>
            </div>
            {rejectionReason ? (
              <div className="verdict-reason">
                <span>Reason:</span> {rejectionReason}
              </div>
            ) : null}
          </div>

          <footer className="panel-provenance">
            <span>
              Catalog provenance:{" "}
              <code>
                {catalog.source.repository}@
                {catalog.source.backend_ref.slice(0, 7)}
              </code>{" "}
              · contract: <code>{catalog.source.generator_contract}</code>
            </span>
          </footer>
        </article>

        {/* Panel 2: Execution evidence */}
        <article
          className="panel workload-panel evidence-panel"
          aria-labelledby="evidence-heading"
        >
          <div className="panel-header">
            <p className="eyebrow">Runtime Boundary</p>
            <h2 id="evidence-heading">Execution evidence</h2>
          </div>

          <div className="empty-evidence-box">
            <p className="empty-evidence-title">No live execution evidence loaded.</p>
            <p className="empty-evidence-desc">
              Terminal consensus outcomes, write-ahead log (WAL) durability receipts,
              and consensus checkpoint state roots are only displayed from verified
              run receipts.
            </p>
            <p className="empty-evidence-desc">
              This browser-local descriptor interface performs read-only pre-flight
              validation and does not trigger live consensus execution.
            </p>
          </div>
        </article>
      </div>
    </section>
  );
}
