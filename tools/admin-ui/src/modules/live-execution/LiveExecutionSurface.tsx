import { useEffect, useMemo, useState } from "react";

import { InertText } from "../../components/InertText";
import { asAdminUiError } from "../../core/errors";
import "./live-execution.css";
import type {
  LiveExecutionPort,
  LiveExecutionSourceDescriptor,
  LiveExecutionState,
  LiveExecutionStatus,
} from "./live-execution-port";
import { MockLiveExecutionAdapter } from "./mock-live-execution-adapter";
import { LiveIntentBuilder } from "./LiveIntentBuilder";
import type { ExecutionIntentDocument } from "./intent-builder";

const defaultPort = new MockLiveExecutionAdapter();

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
  port = defaultPort,
  initialTab = "STATUSES",
}: LiveExecutionSurfaceProps) {
  const [source, setSource] = useState<LiveExecutionSourceDescriptor>();
  const [statuses, setStatuses] = useState<readonly LiveExecutionStatus[]>([]);
  const [selectedStatusId, setSelectedStatusId] = useState<string>();
  const [notice, setNotice] = useState<string>();
  const [activeTab, setActiveTab] = useState<LiveExecutionTab>(initialTab);

  const loadStatuses = () => {
    Promise.all([port.describeLiveSource(), port.listStatuses()])
      .then(([nextSource, nextStatuses]) => {
        setSource(nextSource);
        setStatuses(nextStatuses);
        if (!selectedStatusId && nextStatuses.length > 0) {
          setSelectedStatusId(nextStatuses[0].statusId);
        }
      })
      .catch((error: unknown) => {
        setNotice(asAdminUiError(error).message);
      });
  };

  useEffect(() => {
    let active = true;
    Promise.all([port.describeLiveSource(), port.listStatuses()])
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
  }, [port]);

  const selectedStatus = useMemo(
    () => statuses.find((status) => status.statusId === selectedStatusId),
    [selectedStatusId, statuses],
  );

  const handleMockSubmit = async (intent: ExecutionIntentDocument) => {
    if (typeof port.submitIntent === "function") {
      try {
        const newStatus = await port.submitIntent(intent);
        setNotice(`Intent submitted to mock gate: ${newStatus.statusId}`);
        loadStatuses();
        setSelectedStatusId(newStatus.statusId);
        setActiveTab("STATUSES");
      } catch (err: unknown) {
        setNotice(asAdminUiError(err).message);
      }
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
          <span className="status-pill pill-smoke">MOCK ONLY</span>
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
          onSubmitToMockGate={handleMockSubmit}
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
                  onClick={() => setSelectedStatusId(status.statusId)}
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
                      <code>{selectedStatus.workload.modelPluginId}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>Dataset</dt>
                    <dd>
                      <code>{selectedStatus.workload.datasetId}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>Scope</dt>
                    <dd>
                      <code>{selectedStatus.workload.requestedScope}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>Trust badge</dt>
                    <dd>
                      <code>{selectedStatus.trustBadge}</code>
                    </dd>
                  </div>
                </dl>

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
              </>
            ) : (
              <div className="capability-state state-unavailable" role="status">
                No mock execution status selected.
              </div>
            )}
          </section>
        </div>
      )}

      <footer className="live-boundary-note">
        <span>Transport profile</span>
        <strong>{source?.transportProfile ?? "NONE_PHASE_4"}</strong>
        <span>Offline CSP remains authoritative until T035.</span>
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
