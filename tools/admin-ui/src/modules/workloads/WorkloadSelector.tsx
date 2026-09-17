import { useId, useState } from "react";
import {
  CANONICAL_DESCRIPTOR_CATALOG,
  VALID_SCOPES,
  type DescriptorCatalogSnapshot,
  type ExecutionScopeName,
} from "../../data/descriptors-catalog";
import {
  evaluateReceiptBinding,
  validateExecutionReceipt,
  type ExecutionReceipt,
  type ReceiptState,
} from "../../data/receipt-schema";
import sampleEegReceipt from "../../data/samples/sample-eeg-observation-receipt.json";
import sampleMnistReceipt from "../../data/samples/sample-mnist-stage-c-receipt.json";
import sampleQloraReceipt from "../../data/samples/sample-qlora-stage-c-receipt.json";
import sample10GeneReceipt from "../../data/samples/sample-10gene-plugin-boundary-receipt.json";
import { InertText } from "../../components/InertText";
import { parseUntrustedJson } from "../../security/input-guards";

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
    () =>
      catalog.model_plugins.find((m) => m.plugin_id === "mnist-centroid-v1")?.plugin_id ??
      catalog.model_plugins[0]?.plugin_id ??
      ""
  );
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(
    () =>
      catalog.datasets.find((d) => d.dataset_id === "mnist-v1")?.dataset_id ??
      catalog.datasets[0]?.dataset_id ??
      ""
  );
  const [selectedScope, setSelectedScope] = useState<ExecutionScopeName>(
    "STAGE_C_REAL_DRQ1"
  );

  const [loadedReceipt, setLoadedReceipt] = useState<ExecutionReceipt | null>(null);
  const [receiptError, setReceiptError] = useState<string | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const buffer = event.target?.result as ArrayBuffer;
        const bytes = new Uint8Array(buffer);
        const { value } = parseUntrustedJson(bytes);
        const receipt = validateExecutionReceipt(value);
        setLoadedReceipt(receipt);
        setReceiptError(null);
      } catch (err) {
        setLoadedReceipt(null);
        setReceiptError(err instanceof Error ? err.message : String(err));
      }
    };
    reader.onerror = () => {
      setLoadedReceipt(null);
      setReceiptError("Failed to read receipt file");
    };
    reader.readAsArrayBuffer(file);
  };

  const loadSample = (sample: unknown) => {
    try {
      const receipt = validateExecutionReceipt(sample);
      setLoadedReceipt(receipt);
      setReceiptError(null);
    } catch (err) {
      setLoadedReceipt(null);
      setReceiptError(err instanceof Error ? err.message : String(err));
    }
  };

  const clearReceipt = () => {
    setLoadedReceipt(null);
    setReceiptError(null);
  };

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

  let receiptState: ReceiptState = "NO_RECEIPT";
  let bindingResult: ReturnType<typeof evaluateReceiptBinding> | undefined;

  if (receiptError) {
    receiptState = "REJECTED";
  } else if (loadedReceipt) {
    bindingResult = evaluateReceiptBinding(
      loadedReceipt,
      selectedModelId,
      selectedDatasetId,
      selectedScope,
      catalog.source.backend_ref,
      catalog.source.repository
    );
    receiptState = bindingResult.state;
  }

  return (
    <section className="workloads-container" aria-labelledby="workloads-heading">
      <header className="workloads-header">
        <p className="eyebrow">Descriptor-Driven Execution Selector</p>
        <h1 id="workloads-heading">Workloads</h1>
        <p>
          Configure and inspect candidate model and dataset combinations against
          the frozen descriptor catalog. Pre-flight capabilities are verified from
          frozen catalog snapshot derived from registry descriptors; execution evidence
          is strictly isolated.
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
            onChange={(e) =>
              setSelectedScope(e.target.value as ExecutionScopeName)
            }
          >
            {VALID_SCOPES.map((scope) => {
              const scopeAllowed =
                compatibilityEntry?.requested_scope_allowed[scope] ?? false;
              return (
                <option key={scope} value={scope}>
                  {scope} {scopeAllowed ? "" : "(not allowed)"}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      <div className="workload-panels-grid">
        {/* Panel 1: Pre-flight capability */}
        <article
          className="panel workload-panel capability-panel"
          aria-labelledby="capability-heading"
        >
          <div className="panel-header">
            <p className="eyebrow">Pre-Flight Policy</p>
            <h2 id="capability-heading">Workload capability</h2>
          </div>

          <div className="summary-list">
            <div className="summary-row">
              <span className="summary-label">Selected Model:</span>
              <span className="summary-value">
                <strong>{selectedModel?.display_name ?? selectedModelId}</strong>
                <span className="code-subtext">{selectedModelId}</span>
              </span>
            </div>

            <div className="summary-row">
              <span className="summary-label">Model Sample Kind:</span>
              <span className="summary-value">
                <code>{selectedModel?.sample_kind ?? "n/a"}</code>
              </span>
            </div>

            <div className="summary-row">
              <span className="summary-label">Model Target Kind:</span>
              <span className="summary-value">
                <code>{selectedModel?.target_kind ?? "n/a"}</code>
              </span>
            </div>

            <div className="summary-row">
              <span className="summary-label">Selected Dataset:</span>
              <span className="summary-value">
                <strong>{selectedDataset?.display_name ?? selectedDatasetId}</strong>
                <span className="code-subtext">{selectedDatasetId}</span>
              </span>
            </div>

            <div className="summary-row">
              <span className="summary-label">Dataset Sample Kind:</span>
              <span className="summary-value">
                <code>{selectedDataset?.sample_kind ?? "n/a"}</code>
              </span>
            </div>

            <div className="summary-row">
              <span className="summary-label">Dataset Target Kind:</span>
              <span className="summary-value">
                <code>{selectedDataset?.target_kind ?? "n/a"}</code>
              </span>
            </div>

            <div className="summary-row">
              <span className="summary-label">Contract Status:</span>
              <span className="summary-value">
                <span
                  className={`status-pill ${
                    contractCompatible ? "pill-ok" : "pill-warn"
                  }`}
                >
                  <InertText
                    value={contractCompatible ? "compatible" : "incompatible"}
                  />
                </span>
              </span>
            </div>

            <div className="summary-row">
              <span className="summary-label">Capability Level:</span>
              <span className="summary-value">
                <span
                  className={`status-pill ${
                    supportsStageC ? "pill-capable" : "pill-smoke"
                  }`}
                >
                  <InertText
                    value={supportsStageC ? "Stage C capable" : "Observation only"}
                  />
                </span>
              </span>
            </div>

            <div className="summary-row">
              <span className="summary-label">Requested Scope:</span>
              <span className="summary-value">
                <code>{selectedScope}</code>
              </span>
            </div>
          </div>

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
          aria-label="Execution evidence"
        >
          <div className="panel-header">
            <p className="eyebrow">Runtime Boundary</p>
            <h2 id="evidence-heading">Execution evidence</h2>
          </div>

          <div className="receipt-toolbar">
            <div className="receipt-upload-row">
              <label htmlFor="receipt-file-input" className="file-input-label">
                Load Receipt JSON
              </label>
              <input
                id="receipt-file-input"
                type="file"
                accept=".json,application/json"
                onChange={handleFileUpload}
                className="sr-only-input"
              />
              {loadedReceipt || receiptError ? (
                <button
                  type="button"
                  onClick={clearReceipt}
                  className="toolbar-btn secondary-btn"
                >
                  Clear Receipt
                </button>
              ) : null}
            </div>

            <div className="sample-receipts-row">
              <span className="sample-label">Or load sample:</span>
              <button
                type="button"
                onClick={() => loadSample(sampleMnistReceipt)}
                className="toolbar-btn text-btn"
              >
                MNIST Stage C
              </button>
              <button
                type="button"
                onClick={() => loadSample(sampleQloraReceipt)}
                className="toolbar-btn text-btn"
              >
                QLoRA Stage C
              </button>
              <button
                type="button"
                onClick={() => loadSample(sampleEegReceipt)}
                className="toolbar-btn text-btn"
              >
                EEG Observation
              </button>
              <button
                type="button"
                onClick={() => loadSample(sample10GeneReceipt)}
                className="toolbar-btn text-btn"
              >
                10-Gene Plugin Boundary
              </button>
            </div>
          </div>

          {receiptState === "NO_RECEIPT" && (
            <div className="empty-evidence-box">
              <p className="empty-evidence-title">No live execution evidence loaded.</p>
              <p className="empty-evidence-desc">
                Terminal consensus outcomes, write-ahead log (WAL) durability receipts,
                and consensus checkpoint state roots are only displayed from verified
                run receipts.
              </p>
              <p className="empty-evidence-desc">
                This browser-local descriptor interface performs read-only pre-flight
                validation and does not trigger live consensus execution. Use the toolbar
                above to load an offline receipt JSON or test fixture.
              </p>
            </div>
          )}

          {receiptState === "REJECTED" && (
            <div className="verdict-box verdict-rejected" role="alert">
              <div className="verdict-status">
                <span>Receipt Status:</span>
                <strong className="verdict-label">REJECTED</strong>
              </div>
              <div className="verdict-reason">
                <span>Rejection Reason:</span> {receiptError}
              </div>
            </div>
          )}

          {receiptState === "RECEIPT_LOADED_UNBOUND" && loadedReceipt && (
            <div className="evidence-unbound-container">
              <div className="verdict-box verdict-unbound" role="status">
                <div className="verdict-status">
                  <span>Receipt Status:</span>
                  <strong className="verdict-label">RECEIPT_LOADED_UNBOUND</strong>
                </div>
                <div className="verdict-reason">
                  <span>Binding Mismatch:</span> {bindingResult?.reason}
                </div>
              </div>

              <div className="digest-comparison-card">
                <div className="digest-row">
                  <span className="digest-label">Loaded Receipt Workload:</span>
                  <span className="digest-value">
                    {loadedReceipt.workload.model_plugin_id} + {loadedReceipt.workload.dataset_id} ({loadedReceipt.workload.executed_scope})
                  </span>
                </div>
                <div className="digest-row">
                  <span className="digest-label">Receipt Workload Digest:</span>
                  <code className="digest-code">{bindingResult?.actualDigest}</code>
                </div>
                <div className="digest-row">
                  <span className="digest-label">Active Selector Digest:</span>
                  <code className="digest-code">{bindingResult?.expectedDigest}</code>
                </div>
                <p className="digest-explanation">
                  Receipt was validated against the schema, but is unbound from the active selector parameters.
                </p>
              </div>
            </div>
          )}

          {receiptState === "STRUCTURALLY_VALID_BOUND_RECEIPT" && loadedReceipt && (
            <div className="verified-evidence-container">
              <div className="verdict-box verdict-allowed" role="status">
                <div className="verdict-status">
                  <span>Receipt Status:</span>
                  <strong className="verdict-label">STRUCTURALLY_VALID_BOUND_RECEIPT</strong>
                </div>
                <div className="verdict-reason">
                  <span>Bound Digest:</span> <code>{loadedReceipt.workload.workload_config_digest}</code>
                </div>
                <p className="unattested-disclaimer">
                  Self-consistent local receipt bound to the active catalog configuration. Not cryptographically attested and not proof of execution by Delta authority.
                </p>
              </div>

              {bindingResult?.evidenceType === "UNATTESTED_CONSENSUS_RECORD" && loadedReceipt.consensus_evidence && (
                <div className="evidence-block consensus-evidence-block">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                    <h3 className="evidence-subtitle" style={{ margin: 0 }}>Recorded Consensus Record</h3>
                    <span className="status-pill pill-unattested">UNATTESTED_CONSENSUS_RECORD</span>
                  </div>
                  <div className="evidence-table-container">
                    <table className="evidence-table">
                      <tbody>
                        <tr>
                          <th>Applied Status</th>
                          <td>
                            <span className="status-pill pill-ok">
                              {loadedReceipt.consensus_evidence.applied_status}
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <th>Consensus Round</th>
                          <td>{loadedReceipt.consensus_evidence.round_id}</td>
                        </tr>
                        <tr>
                          <th>WAL Sequence</th>
                          <td>{loadedReceipt.consensus_evidence.wal_sequence}</td>
                        </tr>
                        <tr>
                          <th>State Root</th>
                          <td>
                            <code className="code-break">{loadedReceipt.consensus_evidence.state_root}</code>
                          </td>
                        </tr>
                        <tr>
                          <th>Canonical Model Digest</th>
                          <td>
                            <code className="code-break">{loadedReceipt.consensus_evidence.canonical_model_digest}</code>
                          </td>
                        </tr>
                        <tr>
                          <th>Checkpoint Ref</th>
                          <td>
                            <code className="code-break">{loadedReceipt.consensus_evidence.checkpoint_ref}</code>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {bindingResult?.evidenceType === "OBSERVATION_RECORD" && loadedReceipt.observation_summary && (
                <div className="evidence-block observation-evidence-block">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                    <h3 className="evidence-subtitle" style={{ margin: 0 }}>Observation Record</h3>
                    <span className="status-pill pill-unattested">OBSERVATION_RECORD</span>
                  </div>
                  <p className="observation-desc">{loadedReceipt.observation_summary.observation_note}</p>
                  <div className="evidence-table-container">
                    <table className="evidence-table">
                      <thead>
                        <tr>
                          <th>Metric</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(loadedReceipt.observation_summary.metrics).map(([key, val]) => (
                          <tr key={key}>
                            <td>{key}</td>
                            <td><strong>{String(val)}</strong></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {bindingResult?.evidenceType === "UNATTESTED_PLUGIN_BOUNDARY_RECORD" && (
                <div className="evidence-block plugin-boundary-evidence-block">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                    <h3 className="evidence-subtitle" style={{ margin: 0 }}>Recorded Plugin Boundary Record</h3>
                    <span className="status-pill pill-unattested">UNATTESTED_PLUGIN_BOUNDARY_RECORD</span>
                  </div>
                  <p className="observation-desc">
                    Plugin boundary record self-consistent without consensus round or WAL commits.
                  </p>
                  <div className="evidence-table-container">
                    <table className="evidence-table">
                      <tbody>
                        <tr>
                          <th>Execution Verdict</th>
                          <td>
                            <span className="status-pill pill-ok">
                              {loadedReceipt.execution.verdict}
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <th>Terminal Status</th>
                          <td>{loadedReceipt.execution.terminal_status}</td>
                        </tr>
                        <tr>
                          <th>Executed Scope</th>
                          <td><code>{loadedReceipt.workload.executed_scope}</code></td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {loadedReceipt.reference_anchor && (
                <div className="evidence-block reference-anchor-block">
                  <h4 className="reference-anchor-title">Declared Reference Anchor</h4>
                  <p className="reference-anchor-disclaimer">
                    Baseline reference for comparison only; does not define live consensus proof.
                  </p>
                  <div className="reference-anchor-details">
                    <div>
                      <strong>Description:</strong> {loadedReceipt.reference_anchor.anchor_description}
                    </div>
                    <div>
                      <strong>Baseline Metric:</strong> <code>{String(loadedReceipt.reference_anchor.declared_baseline_metric)}</code>
                    </div>
                  </div>
                </div>
              )}

              <footer className="panel-provenance">
                <span>
                  Produced at: <code>{loadedReceipt.provenance.produced_at}</code> · catalog: <code>{loadedReceipt.provenance.backend_commit.slice(0, 7)}</code>
                  {loadedReceipt.provenance.producer_commit && (
                    <> · producer: <code>{loadedReceipt.provenance.producer_commit.slice(0, 7)}</code></>
                  )}
                </span>
              </footer>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
