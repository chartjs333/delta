import { useId, useMemo, useState } from "react";

import { InertText } from "../../components/InertText";
import { CANONICAL_DESCRIPTOR_CATALOG } from "../../data/descriptors-catalog";
import type {
  LiveExecutionOperation,
  LiveExecutionScope,
} from "./live-execution-port";
import {
  buildExecutionIntentDocument,
  createDefaultIntentDraft,
  type DeclaredOperator,
  type EvaluateCheckpointPayload,
  type ExecutionConstraints,
  type ExecutionIntentDocument,
  type ExecutionIntentDraft,
  type MaterializeDatasetPayload,
  type OperatorRole,
  type TrainTicketPayload,
  type WorkloadSelectionState,
} from "./intent-builder";

export interface LiveIntentBuilderProps {
  readonly onIntentBuilt?: (intent: ExecutionIntentDocument) => void;
  readonly onSubmit?: (intent: ExecutionIntentDocument) => void;
  readonly submitLabel?: string;
}

export function LiveIntentBuilder({
  onIntentBuilt,
  onSubmit,
  submitLabel = "Submit to Mock Gate",
}: LiveIntentBuilderProps) {
  const [operation, setOperation] =
    useState<LiveExecutionOperation>("TRAIN_TICKET");
  const [modelPluginId, setModelPluginId] = useState<string>(
    "tabular-10gene-phenotype-v1",
  );
  const [datasetId, setDatasetId] = useState<string>(
    "synthetic-10gene-cohort-v1",
  );
  const [requestedScope, setRequestedScope] =
    useState<LiveExecutionScope>("PLUGIN_BOUNDARY");

  // Operator
  const [operatorRole, setOperatorRole] = useState<OperatorRole>("OPERATOR");
  const [subjectId, setSubjectId] = useState<string>("operator.alpha");

  // Constraints
  const [timeoutSeconds, setTimeoutSeconds] = useState<number>(900);
  const [allowDownloads, setAllowDownloads] = useState<boolean>(false);
  const [retryOfIntentId, setRetryOfIntentId] = useState<string>("");

  // Payload: TRAIN_TICKET
  const [ticketId, setTicketId] = useState<string>("ticket_A-0001");
  const [partitionId, setPartitionId] = useState<string>("partition_00");

  // Payload: EVALUATE_CHECKPOINT
  const [checkpointCoords, setCheckpointCoords] =
    useState<string>("100, 200, 300, 400");

  // Payload: MATERIALIZE_DATASET
  const [cacheKey, setCacheKey] = useState<string>("cache_synth_01");

  // UI view state
  const [showJson, setShowJson] = useState<boolean>(false);
  const [exportedMessage, setExportedMessage] = useState<string>();

  const baseId = useId();

  // Effective scope constraint: TRAIN_TICKET requires PLUGIN_BOUNDARY
  const effectiveScope: LiveExecutionScope =
    operation === "TRAIN_TICKET" ? "PLUGIN_BOUNDARY" : requestedScope;

  const draft: ExecutionIntentDraft = useMemo(() => {
    const workload: WorkloadSelectionState = {
      model_plugin_id: modelPluginId,
      dataset_id: datasetId,
      requested_scope: effectiveScope,
      catalog_backend_ref: CANONICAL_DESCRIPTOR_CATALOG.source.backend_ref,
    };

    const declared_operator: DeclaredOperator = {
      role: operatorRole,
      subject_id: subjectId,
    };

    const execution_constraints: ExecutionConstraints = {
      timeout_seconds: timeoutSeconds,
      requested_allow_downloads: allowDownloads,
      ...(retryOfIntentId.trim()
        ? { retry_of_intent_id: retryOfIntentId.trim() }
        : {}),
    };

    let operation_payload:
      | TrainTicketPayload
      | EvaluateCheckpointPayload
      | MaterializeDatasetPayload;

    if (operation === "TRAIN_TICKET") {
      operation_payload = {
        ticket_id: ticketId.trim(),
        partition_id: partitionId.trim(),
      };
    } else if (operation === "EVALUATE_CHECKPOINT") {
      const coords = checkpointCoords
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
        .map((s) => Number(s));
      operation_payload = {
        checkpoint_coordinates: coords,
      };
    } else {
      operation_payload = cacheKey.trim()
        ? { cache_key: cacheKey.trim() }
        : {};
    }

    return {
      operation,
      workload,
      declared_operator,
      execution_constraints,
      operation_payload,
    };
  }, [
    operation,
    modelPluginId,
    datasetId,
    effectiveScope,
    operatorRole,
    subjectId,
    timeoutSeconds,
    allowDownloads,
    retryOfIntentId,
    ticketId,
    partitionId,
    checkpointCoords,
    cacheKey,
  ]);

  const { document, canonicalJson, issues } = useMemo(
    () => buildExecutionIntentDocument(draft),
    [draft],
  );

  const compatibility = useMemo(() => {
    return CANONICAL_DESCRIPTOR_CATALOG.compatibility.find(
      (c) =>
        c.model_plugin_id === modelPluginId && c.dataset_id === datasetId,
    );
  }, [modelPluginId, datasetId]);

  const handleExport = () => {
    const blob = new Blob([canonicalJson], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement("a");
    a.href = url;
    a.download = `intent-${document.intent_id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setExportedMessage(`Exported ${a.download} locally.`);
  };

  const handleSubmit = () => {
    if (issues.length === 0) {
      onSubmit?.(document);
      onIntentBuilt?.(document);
    }
  };

  return (
    <section
      className="live-intent-builder"
      aria-labelledby={`${baseId}-builder-heading`}
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Zone 1 — Untrusted drafting</p>
          <h2 id={`${baseId}-builder-heading`}>ExecutionIntent builder</h2>
        </div>
        <span className="status-pill pill-smoke">FORM-FIRST DRAFT</span>
      </div>

      <p className="intent-builder-intro">
        Draft canonical Step 5C execution intents from the frozen catalog.
        The browser performs RFC 8785 canonicalization and informational digest
        preview only; gate recomputation remains authoritative.
      </p>

      {exportedMessage ? (
        <div className="capability-state state-available" role="status">
          {exportedMessage}
        </div>
      ) : null}

      <form
        className="intent-form"
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
      >
        <fieldset className="intent-fieldset">
          <legend>Operation selection</legend>
          <div className="form-row radio-group" role="radiogroup">
            <label className="radio-label">
              <input
                checked={operation === "TRAIN_TICKET"}
                name="operation"
                type="radio"
                value="TRAIN_TICKET"
                onChange={() => setOperation("TRAIN_TICKET")}
              />
              <span>TRAIN_TICKET</span>
            </label>
            <label className="radio-label">
              <input
                checked={operation === "EVALUATE_CHECKPOINT"}
                name="operation"
                type="radio"
                value="EVALUATE_CHECKPOINT"
                onChange={() => setOperation("EVALUATE_CHECKPOINT")}
              />
              <span>EVALUATE_CHECKPOINT</span>
            </label>
            <label className="radio-label">
              <input
                checked={operation === "MATERIALIZE_DATASET"}
                name="operation"
                type="radio"
                value="MATERIALIZE_DATASET"
                onChange={() => setOperation("MATERIALIZE_DATASET")}
              />
              <span>MATERIALIZE_DATASET</span>
            </label>
          </div>
        </fieldset>

        <fieldset className="intent-fieldset">
          <legend>Workload catalog binding</legend>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor={`${baseId}-model`}>Model plugin</label>
              <select
                id={`${baseId}-model`}
                value={modelPluginId}
                onChange={(e) => setModelPluginId(e.target.value)}
              >
                {CANONICAL_DESCRIPTOR_CATALOG.model_plugins.map((m) => (
                  <option key={m.plugin_id} value={m.plugin_id}>
                    {m.display_name} ({m.plugin_id})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor={`${baseId}-dataset`}>Dataset</label>
              <select
                id={`${baseId}-dataset`}
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
              >
                {CANONICAL_DESCRIPTOR_CATALOG.datasets.map((d) => (
                  <option key={d.dataset_id} value={d.dataset_id}>
                    {d.display_name} ({d.dataset_id})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor={`${baseId}-scope`}>Requested scope</label>
              <select
                disabled={operation === "TRAIN_TICKET"}
                id={`${baseId}-scope`}
                value={effectiveScope}
                onChange={(e) =>
                  setRequestedScope(e.target.value as LiveExecutionScope)
                }
              >
                <option value="PLUGIN_BOUNDARY">PLUGIN_BOUNDARY</option>
                <option value="MODEL_DATASET_BINDING_ONLY">
                  MODEL_DATASET_BINDING_ONLY
                </option>
              </select>
              {operation === "TRAIN_TICKET" ? (
                <small className="field-hint">
                  TRAIN_TICKET requires scope &lsquo;PLUGIN_BOUNDARY&rsquo;.
                </small>
              ) : null}
            </div>

            <div className="form-group">
              <label>Catalog backend reference</label>
              <input
                readOnly
                type="text"
                value={CANONICAL_DESCRIPTOR_CATALOG.source.backend_ref}
              />
              <small className="field-hint">
                Pinned frozen catalog commit (40-hex)
              </small>
            </div>
          </div>

          <div className="compatibility-indicator">
            <span>Pair contract compatibility:</span>
            {compatibility?.contract_compatible ? (
              <strong className="text-ok">COMPATIBLE</strong>
            ) : (
              <strong className="text-warn">INCOMPATIBLE</strong>
            )}
          </div>
        </fieldset>

        <fieldset className="intent-fieldset">
          <legend>Operation parameters ({operation})</legend>
          {operation === "TRAIN_TICKET" ? (
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor={`${baseId}-ticket-id`}>Ticket ID</label>
                <input
                  id={`${baseId}-ticket-id`}
                  type="text"
                  value={ticketId}
                  onChange={(e) => setTicketId(e.target.value)}
                />
                <small className="field-hint">
                  Pattern: ^[A-Za-z0-9_-]+$ (max 64 chars)
                </small>
              </div>
              <div className="form-group">
                <label htmlFor={`${baseId}-partition-id`}>Partition ID</label>
                <input
                  id={`${baseId}-partition-id`}
                  type="text"
                  value={partitionId}
                  onChange={(e) => setPartitionId(e.target.value)}
                />
                <small className="field-hint">
                  Pattern: ^[A-Za-z0-9_-]+$ (max 64 chars)
                </small>
              </div>
            </div>
          ) : null}

          {operation === "EVALUATE_CHECKPOINT" ? (
            <div className="form-group">
              <label htmlFor={`${baseId}-coords`}>
                Checkpoint coordinates (integers)
              </label>
              <input
                id={`${baseId}-coords`}
                type="text"
                value={checkpointCoords}
                onChange={(e) => setCheckpointCoords(e.target.value)}
              />
              <small className="field-hint">
                Comma-separated 32-bit signed integers (1..4096 elements)
              </small>
            </div>
          ) : null}

          {operation === "MATERIALIZE_DATASET" ? (
            <div className="form-group">
              <label htmlFor={`${baseId}-cache-key`}>
                Cache key (optional)
              </label>
              <input
                id={`${baseId}-cache-key`}
                type="text"
                value={cacheKey}
                onChange={(e) => setCacheKey(e.target.value)}
              />
              <small className="field-hint">
                Optional alphanumeric/underscore identifier (max 64 chars)
              </small>
            </div>
          ) : null}
        </fieldset>

        <fieldset className="intent-fieldset">
          <legend>Declared operator &amp; constraints</legend>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor={`${baseId}-role`}>Operator role</label>
              <select
                id={`${baseId}-role`}
                value={operatorRole}
                onChange={(e) => setOperatorRole(e.target.value as OperatorRole)}
              >
                <option value="OPERATOR">OPERATOR</option>
                <option value="RESEARCHER">RESEARCHER</option>
                <option value="AUDITOR">AUDITOR</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor={`${baseId}-subject`}>Subject ID</label>
              <input
                id={`${baseId}-subject`}
                type="text"
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor={`${baseId}-timeout`}>Timeout (seconds)</label>
              <input
                id={`${baseId}-timeout`}
                max={3600}
                min={1}
                type="number"
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label htmlFor={`${baseId}-retry`}>
                Retry of intent ID (optional)
              </label>
              <input
                id={`${baseId}-retry`}
                placeholder="UUID if retrying a failed intent"
                type="text"
                value={retryOfIntentId}
                onChange={(e) => setRetryOfIntentId(e.target.value)}
              />
            </div>
          </div>

          <div className="form-row checkbox-row">
            <label className="checkbox-label">
              <input
                checked={allowDownloads}
                type="checkbox"
                onChange={(e) => setAllowDownloads(e.target.checked)}
              />
              <span>
                Request external downloads (Informational intent constraint;
                controller policy and AdmissionRecord determine actual authority)
              </span>
            </label>
          </div>
        </fieldset>

        {issues.length > 0 ? (
          <div className="capability-state state-error" role="alert">
            <strong>Validation issues ({issues.length}):</strong>
            <ul>
              {issues.map((iss) => (
                <li key={iss.field}>
                  <code>{iss.field}</code>: {iss.message}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <section
          className="digest-preview-card"
          aria-labelledby={`${baseId}-digest-heading`}
        >
          <div className="digest-header">
            <h3 id={`${baseId}-digest-heading`}>Informational digest preview</h3>
            <span className="status-pill pill-smoke">INFORMATIONAL ONLY</span>
          </div>
          <p className="digest-notice">
            Computed locally via RFC 8785 JCS canonicalization over{" "}
            <code>ExecutionIntent \ &#123;&quot;intent_digest&quot;&#125;</code>.
            Local preview does not constitute admission or authority; gate
            recomputes digest from canonical bytes.
          </p>
          <div className="digest-code-block">
            <code>{document.intent_digest}</code>
          </div>
        </section>

        <div className="builder-actions">
          <button
            className="action-button primary"
            disabled={issues.length > 0}
            type="submit"
          >
            {submitLabel}
          </button>
          <button
            className="action-button secondary"
            type="button"
            onClick={handleExport}
          >
            Export Intent JSON
          </button>
          <button
            aria-expanded={showJson}
            className="action-button tertiary"
            type="button"
            onClick={() => setShowJson(!showJson)}
          >
            {showJson ? "Hide Canonical JSON" : "View Canonical JSON"}
          </button>
        </div>

        {showJson ? (
          <section
            className="canonical-json-preview"
            aria-label="Canonical JSON preview"
          >
            <h4>RFC 8785 Canonical JSON</h4>
            <pre>
              <InertText value={canonicalJson} />
            </pre>
          </section>
        ) : null}
      </form>
    </section>
  );
}
