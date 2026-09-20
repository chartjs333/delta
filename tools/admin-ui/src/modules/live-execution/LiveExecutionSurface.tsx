import { useEffect, useMemo, useState } from "react";

import { InertText } from "../../components/InertText";
import { asAdminUiError } from "../../core/errors";
import "./live-execution.css";
import type {
  LiveExecutionPort,
  LiveExecutionReceipt,
  LiveExecutionSourceDescriptor,
  LiveExecutionState,
  LiveExecutionStatus,
} from "./live-execution-port";
import { useLiveExecutionRuntime } from "./live-execution-context";
import { LiveIntentBuilder } from "./LiveIntentBuilder";
import type { ExecutionIntentDocument } from "./intent-builder";

const STATE_LABELS: Readonly<Record<LiveExecutionState, string>> = {
  DRAFT: "Draft",
  REJECTED: "Rejected",
  ADMITTED: "Admitted",
  QUEUED: "Queued",
  RUNNING: "Running",
  COMPLETED: "Completed",
  FAILED: "Failed",
  TIMED_OUT: "Timed out",
  CANCELLED: "Cancelled",
  STALE_UNAVAILABLE: "Stale/unavailable",
};

export type LiveExecutionTab = "STATUSES" | "BUILDER";

export interface LiveExecutionSurfaceProps {
  readonly port?: LiveExecutionPort;
  readonly initialTab?: LiveExecutionTab;
}

export function LiveExecutionSurface({
  port,
  initialTab = "STATUSES",
}: LiveExecutionSurfaceProps) {
  const runtime = useLiveExecutionRuntime();
  const activePort = port ?? runtime.port;
  const [source, setSource] = useState<LiveExecutionSourceDescriptor>();
  const [statuses, setStatuses] = useState<readonly LiveExecutionStatus[]>([]);
  const [selectedStatusId, setSelectedStatusId] = useState<string>();
  const [notice, setNotice] = useState<string>();
  const [receipt, setReceipt] = useState<LiveExecutionReceipt>();
  const [activeTab, setActiveTab] = useState<LiveExecutionTab>(initialTab);

  const loadStatuses = (preferredStatusId?: string) => {
    Promise.all([activePort.describeLiveSource(), activePort.listStatuses()])
      .then(([nextSource, nextStatuses]) => {
        setSource(nextSource);
        setStatuses(nextStatuses);
        setSelectedStatusId((current) => {
          if (preferredStatusId) return preferredStatusId;
          if (current && nextStatuses.some((item) => item.statusId === current)) {
            return current;
          }
          return nextStatuses[0]?.statusId;
        });
      })
      .catch((error: unknown) => {
        setNotice(asAdminUiError(error).message);
      });
  };

  useEffect(() => {
    let active = true;
    Promise.all([activePort.describeLiveSource(), activePort.listStatuses()])
      .then(([nextSource, nextStatuses]) => {
        if (!active) return;
        setSource(nextSource);
        setStatuses(nextStatuses);
        setSelectedStatusId(nextStatuses[0]?.statusId);
      })
      .catch((error: unknown) => {
        if (active) setNotice(asAdminUiError(error).message);
      });
    return () => {
      active = false;
    };
  }, [activePort]);

  const selectedStatus = useMemo(
    () => statuses.find((status) => status.statusId === selectedStatusId),
    [selectedStatusId, statuses],
  );

  const handleSubmit = async (intent: ExecutionIntentDocument) => {
    try {
      const newStatus = await activePort.submitIntent(intent);
      const target = source?.mode === "HTTP_LIVE" ? "controller" : "mock gate";
      setNotice(`Intent submitted to ${target}: ${newStatus.statusId}`);
      setReceipt(undefined);
      loadStatuses(newStatus.statusId);
      setActiveTab("STATUSES");
    } catch (err: unknown) {
      setNotice(asAdminUiError(err).message);
    }
  };

  const refreshSelectedStatus = async () => {
    if (!selectedStatus) return;
    try {
      const refreshed = await activePort.getStatus(selectedStatus.statusId);
      setStatuses((current) =>
        current.map((item) =>
          item.statusId === refreshed.statusId ? refreshed : item,
        ),
      );
      setNotice(`Status refreshed: ${refreshed.state}`);
    } catch (error: unknown) {
      setNotice(asAdminUiError(error).message);
    }
  };

  const cancelSelectedExecution = async () => {
    const executionId = selectedStatus?.lineage.executionId;
    if (!executionId || !activePort.cancelExecution) return;
    try {
      const cancelled = await activePort.cancelExecution(executionId);
      setStatuses((current) =>
        current.map((item) =>
          item.statusId === cancelled.statusId ? cancelled : item,
        ),
      );
      setReceipt(undefined);
      setNotice(`Cancellation requested: ${cancelled.state}`);
    } catch (error: unknown) {
      setNotice(asAdminUiError(error).message);
    }
  };

  const loadSelectedReceipt = async () => {
    const executionId = selectedStatus?.lineage.executionId;
    if (!executionId || !activePort.getReceipt) return;
    try {
      const nextReceipt = await activePort.getReceipt(executionId);
      setReceipt(nextReceipt);
      setNotice("Terminal receipt loaded from the controller.");
    } catch (error: unknown) {
      setReceipt(undefined);
      setNotice(asAdminUiError(error).message);
    }
  };

  return (
    <section
      className="live-execution-container"
      aria-labelledby="live-execution-heading"
    >
      <header className="live-execution-header">
        <div>
          <p className="eyebrow">Controlled execution boundary</p>
          <h1 id="live-execution-heading">Live execution</h1>
        </div>
        <div className="live-mode-panel" aria-label="Live execution source">
          <span
            className={
              source?.mode === "HTTP_LIVE"
                ? "status-pill pill-capable"
                : "status-pill pill-smoke"
            }
          >
            {source?.mode === "HTTP_LIVE" ? "HTTP LIVE" : "MOCK ONLY"}
          </span>
          <span>{source?.label ?? "Loading source"}</span>
          <code>{source?.contractFreezeSha.slice(0, 12) ?? "pending"}</code>
        </div>
      </header>

      <nav className="live-tab-nav" aria-label="Live execution views">
        <button
          aria-current={activeTab === "STATUSES" ? "page" : undefined}
          className={activeTab === "STATUSES" ? "tab-button active" : "tab-button"}
          type="button"
          onClick={() => setActiveTab("STATUSES")}
        >
          Product states &amp; read model
        </button>
        <button
          aria-current={activeTab === "BUILDER" ? "page" : undefined}
          className={activeTab === "BUILDER" ? "tab-button active" : "tab-button"}
          type="button"
          onClick={() => setActiveTab("BUILDER")}
        >
          ExecutionIntent builder
        </button>
      </nav>

      {notice ? (
        <div className="capability-state state-available" role="status">
          {notice}
        </div>
      ) : null}

      {activeTab === "BUILDER" ? (
        <LiveIntentBuilder
          onSubmit={handleSubmit}
          submitLabel={
            source?.mode === "HTTP_LIVE"
              ? "Submit to Controller"
              : "Submit to Mock Gate"
          }
        />
      ) : (
        <div className="live-boundary-grid">
          <section
            className="live-status-list"
            aria-labelledby="live-status-list-heading"
          >
            <div className="section-heading">
              <div>
                <p className="eyebrow">Read model</p>
                <h2 id="live-status-list-heading">Product states</h2>
              </div>
            </div>
            <div className="live-status-buttons" role="list">
              {statuses.map((status) => (
                <button
                  aria-pressed={status.statusId === selectedStatusId}
                  className={
                    status.statusId === selectedStatusId
                      ? "live-status-button selected"
                      : "live-status-button"
                  }
                  key={status.statusId}
                  type="button"
                  onClick={() => {
                    setSelectedStatusId(status.statusId);
                    setReceipt(undefined);
                  }}
                >
                  <span>{STATE_LABELS[status.state]}</span>
                  <small>{status.operation}</small>
                </button>
              ))}
            </div>
          </section>

          <section
            className="live-status-detail"
            aria-labelledby="live-status-detail-heading"
          >
            {selectedStatus ? (
              <>
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Selected state</p>
                    <h2 id="live-status-detail-heading">
                      {STATE_LABELS[selectedStatus.state]}
                    </h2>
                  </div>
                  <span className={statusPillClass(selectedStatus.state)}>
                    <InertText value={selectedStatus.state} />
                  </span>
                </div>

                <p className="live-status-summary">
                  <InertText value={selectedStatus.summary} />
                </p>

                <dl className="live-status-grid">
                  <div>
                    <dt>Status ID</dt>
                    <dd>
                      <code>{selectedStatus.statusId}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>Operation</dt>
                    <dd>
                      <code>{selectedStatus.operation}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>Model plugin</dt>
                    <dd>
                      {selectedStatus.workload ? (
                        <code>{selectedStatus.workload.modelPluginId}</code>
                      ) : (
                        <span className="muted-value">Not in status response</span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Dataset</dt>
                    <dd>
                      {selectedStatus.workload ? (
                        <code>{selectedStatus.workload.datasetId}</code>
                      ) : (
                        <span className="muted-value">Not in status response</span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Scope</dt>
                    <dd>
                      {selectedStatus.workload ? (
                        <code>{selectedStatus.workload.requestedScope}</code>
                      ) : (
                        <span className="muted-value">Not in status response</span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Trust badge</dt>
                    <dd>
                      <code>{selectedStatus.trustBadge}</code>
                    </dd>
                  </div>
                </dl>

                {source?.mode === "HTTP_LIVE" ? (
                  <div className="builder-actions" aria-label="Execution actions">
                    <button
                      className="action-button secondary"
                      type="button"
                      onClick={() => void refreshSelectedStatus()}
                    >
                      Refresh status
                    </button>
                    {activePort.cancelExecution &&
                    !isTerminalState(selectedStatus) ? (
                      <button
                        className="action-button secondary"
                        type="button"
                        onClick={() => void cancelSelectedExecution()}
                      >
                        Cancel execution
                      </button>
                    ) : null}
                    {activePort.getReceipt &&
                    selectedStatus.state === "COMPLETED" &&
                    selectedStatus.operation !== "MATERIALIZE_DATASET" ? (
                      <button
                        className="action-button secondary"
                        type="button"
                        onClick={() => void loadSelectedReceipt()}
                      >
                        Load terminal receipt
                      </button>
                    ) : null}
                  </div>
                ) : null}

                <section
                  className="live-lineage-panel"
                  aria-labelledby="live-lineage-heading"
                >
                  <h3 id="live-lineage-heading">Lineage view</h3>
                  <dl className="live-lineage-grid">
                    <LineageRow
                      label="Intent ID"
                      value={selectedStatus.lineage.intentId}
                    />
                    <LineageRow
                      label="Intent digest"
                      value={selectedStatus.lineage.intentDigest}
                    />
                    <LineageRow
                      label="Admission ID"
                      value={selectedStatus.lineage.admissionId}
                    />
                    <LineageRow
                      label="Admission digest"
                      value={selectedStatus.lineage.admissionDigest}
                    />
                    <LineageRow
                      label="Execution ID"
                      value={selectedStatus.lineage.executionId}
                    />
                  </dl>
                </section>

                {receipt ? (
                  <section
                    className="live-lineage-panel"
                    aria-labelledby="live-receipt-heading"
                  >
                    <div className="section-heading">
                      <h3 id="live-receipt-heading">Terminal receipt</h3>
                      <span className="status-pill pill-smoke">
                        UNATTESTED PLUGIN RECORD
                      </span>
                    </div>
                    <p>
                      Controller-returned receipt with structural and lineage
                      checks. It is not a consensus certificate.
                    </p>
                    <dl className="live-lineage-grid">
                      <LineageRow
                        label="Intent ID"
                        value={receipt.provenance.intent_id}
                      />
                      <LineageRow
                        label="Admission ID"
                        value={receipt.provenance.admission_id}
                      />
                      <LineageRow
                        label="Execution ID"
                        value={receipt.provenance.execution_id}
                      />
                      <LineageRow
                        label="Producer commit"
                        value={receipt.provenance.producer_commit}
                      />
                    </dl>
                  </section>
                ) : null}
              </>
            ) : (
              <div className="capability-state state-unavailable" role="status">
                {source?.mode === "HTTP_LIVE"
                  ? "No live execution has been submitted in this browser session."
                  : "No mock execution status selected."}
              </div>
            )}
          </section>
        </div>
      )}

      <footer className="live-boundary-note">
        <span>Transport profile</span>
        <strong>{source?.transportProfile ?? "NONE_PHASE_4"}</strong>
        <span>
          {source?.mode === "HTTP_LIVE"
            ? "Same-origin controller status is unattested and never a consensus claim."
            : "Offline CSP connect-src 'none' remains authoritative."}
        </span>
      </footer>
    </section>
  );
}

function LineageRow({
  label,
  value,
}: {
  readonly label: string;
  readonly value?: string;
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        {value ? <code>{value}</code> : <span className="muted-value">Absent</span>}
      </dd>
    </div>
  );
}

function statusPillClass(state: LiveExecutionState): string {
  switch (state) {
    case "COMPLETED":
      return "status-pill pill-ok";
    case "FAILED":
    case "REJECTED":
    case "TIMED_OUT":
    case "CANCELLED":
      return "status-pill pill-warn";
    case "STALE_UNAVAILABLE":
      return "status-pill pill-smoke";
    default:
      return "status-pill pill-capable";
  }
}

function isTerminalState(status: LiveExecutionStatus): boolean {
  return (
    status.terminal === true ||
    status.state === "COMPLETED" ||
    status.state === "FAILED" ||
    status.state === "TIMED_OUT" ||
    status.state === "CANCELLED"
  );
}
