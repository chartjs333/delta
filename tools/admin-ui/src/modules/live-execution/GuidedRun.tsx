import { HelpLabel } from "../../components/FieldHelp";
import { useEffect, useRef, useState } from "react";
import { message, t } from "../../i18n";
import { asAdminUiError } from "../../core/errors";
import {
  buildExecutionIntentDocument,
  createDefaultIntentDraft,
  type ExecutionIntentDocument,
} from "./intent-builder";
import { jcsCanonicalize } from "./canonical-jcs";
import type {
  LiveExecutionPort,
  LiveExecutionReceipt,
  LiveExecutionStatus,
} from "./live-execution-port";
import { ProtocolGuide } from "./ProtocolGuide";
import { useWorkspace } from "../workspace/workspace-context";
import { PresentationLink, WorkspaceSummary } from "../workspace/WorkspaceViews";
import "./guided-run.css";

const terminalStates = new Set([
  "COMPLETED",
  "FAILED",
  "CANCELLED",
  "TIMED_OUT",
  "REJECTED",
]);
const stateLabels: Record<string, string> = {
  ADMITTED: "Accepted by Controller",
  QUEUED: "Waiting for the worker",
  RUNNING: "Worker is running",
  COMPLETED: "Execution completed",
  FAILED: "Execution failed",
  TIMED_OUT: "Execution timed out",
  CANCELLED: "Execution cancelled",
  REJECTED: "Request rejected",
  STALE_UNAVAILABLE: "Status unavailable",
};

export function GuidedRun({
  port,
  enabled,
  onStatus,
}: {
  readonly port: LiveExecutionPort;
  readonly enabled: boolean;
  readonly onStatus: (status: LiveExecutionStatus) => void;
}) {
  const workspace = useWorkspace();
  const activeIntent = useRef<ExecutionIntentDocument | undefined>(undefined);
  const [ticket, setTicket] = useState("presentation_demo");
  const [intent, setIntent] = useState<ExecutionIntentDocument>();
  const [status, setStatus] = useState<LiveExecutionStatus>();
  const [receipt, setReceipt] = useState<LiveExecutionReceipt>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [paused, setPaused] = useState(false);
  const request = useRef(0);
  const running = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const notify = useRef(onStatus);
  notify.current = onStatus;
  useEffect(
    () => () => {
      request.current += 1;
      clearTimeout(timer.current);
    },
    [port],
  );

  const terminal = status ? terminalStates.has(status.state) : false;
  const validTicket = /^[A-Za-z0-9_-]{1,64}$/.test(ticket);

  async function readResult(
    next: LiveExecutionStatus,
    generation: number,
    reads: number,
  ) {
    if (generation !== request.current) return;
    if (workspace && activeIntent.current) await workspace.bindStatus(activeIntent.current, next);
    if (generation !== request.current) return;
    setStatus(next);
    notify.current(next);
    if (next.state === "COMPLETED") {
      if (!port.getReceipt || !next.lineage.executionId)
        throw new Error("Receipt is unavailable. No verified result is shown.");
      // The existing transport validates schema, digest and intent/admission lineage.
      const verified = await port.getReceipt(next.lineage.executionId);
      if (generation !== request.current) return;
      setReceipt(verified);
      setBusy(false);
      running.current = false;
    } else if (terminalStates.has(next.state)) {
      setBusy(false);
      running.current = false;
    } else if (next.state === "STALE_UNAVAILABLE") {
      throw new Error(
        "Status is unavailable. Check again before starting another run.",
      );
    } else if (reads >= 90) {
      setPaused(true);
      setBusy(false);
      running.current = false;
    } else {
      timer.current = setTimeout(() => {
        void refresh(next.statusId, generation, reads + 1);
      }, 1000);
    }
  }

  function fail(reason: unknown, generation: number) {
    if (generation !== request.current) return;
    setError(asAdminUiError(reason).message);
    setReceipt(undefined);
    setBusy(false);
    running.current = false;
  }

  async function refresh(id: string, generation: number, reads = 0) {
    try {
      await readResult(await port.getStatus(id), generation, reads);
    } catch (reason) {
      fail(reason, generation);
    }
  }

  async function start() {
    if (!enabled || running.current || intent || !validTicket) return;
    const draft = createDefaultIntentDraft("TRAIN_TICKET");
    const built = buildExecutionIntentDocument({
      ...draft,
      workload: workspace?.workload ?? draft.workload,
      operation_payload: { ticket_id: ticket, partition_id: "partition_00" },
    });
    if (built.issues.length) {
      setError("Review the run name before continuing.");
      return;
    }
    running.current = true;
    const generation = ++request.current;
    setIntent(built.document);
    activeIntent.current = built.document;
    setBusy(true);
    setError(undefined);
    setPaused(false);
    try {
      await workspace?.beginRun(built.document, ticket);
      if (generation !== request.current) return;
      await readResult(await port.submitIntent(built.document), generation, 0);
    } catch (reason) {
      fail(reason, generation);
    }
  }

  function checkAgain() {
    if (!status || running.current) return;
    clearTimeout(timer.current);
    running.current = true;
    setBusy(true);
    setError(undefined);
    setPaused(false);
    void refresh(status.statusId, ++request.current);
  }

  function reset() {
    if (running.current || !terminal) return;
    request.current += 1;
    clearTimeout(timer.current);
    setIntent(undefined);
    activeIntent.current = undefined;
    setStatus(undefined);
    setReceipt(undefined);
    setError(undefined);
    setPaused(false);
  }

  function download() {
    if (!receipt) return;
    const url = URL.createObjectURL(
      new Blob([jcsCanonicalize(receipt)], { type: "application/json" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `receipt-${receipt.provenance.execution_id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const steps = [
    "Choose an example",
    "Send to Controller",
    "Run the worker",
    "Inspect the result",
  ];
  const currentStep = receipt ? 3 : status ? 2 : intent ? 1 : 0;
  return (
    <div className="guided-run">
      <WorkspaceSummary />
      <div className="guided-intro">
        <p>
          {t(
            "Start with a small, real training run. Follow its progress and download the result.",
          )}
        </p>
      </div>
      <ol className="run-steps" aria-label={t("Run steps")}>
        {steps.map((step, index) => (
          <li
            key={step}
            aria-current={currentStep === index ? "step" : undefined}
            className={currentStep === index ? "current" : ""}
          >
            <span>{index + 1}</span>
            {t(step)}
          </li>
        ))}
      </ol>
      <div className="guided-grid">
        <section
          className="guided-card example-card"
          aria-labelledby="example-heading"
        >
          <p className="eyebrow">{t("Ready to run")}</p>
          <h2 id="example-heading">{t("Train on sample data")}</h2>
          <p>
            {t(
              "A small classifier learns from a synthetic dataset with ten features. Everything runs locally.",
            )}
          </p>
          <HelpLabel className="run-name" htmlFor="guided-ticket">
            {t("Run name")}
            <input
              id="guided-ticket"
              value={ticket}
              disabled={!!intent}
              maxLength={64}
              onChange={(event) => setTicket(event.target.value)}
              aria-describedby="guided-name-help"
            />
          </HelpLabel>
          <small id="guided-name-help">
            {t("Use letters, numbers, underscores or hyphens.")}
          </small>
          <button
            type="button"
            className="primary guided-start"
            onClick={() => void start()}
            disabled={!enabled || !!intent || busy || !validTicket}
          >
            {t(busy ? "Working…" : "Start training")}{" "}
            <span aria-hidden="true">→</span>
          </button>
          <dl className="example-facts">
            <div>
              <dt>{t("Data")}</dt>
              <dd>{t("Synthetic · 10 features")}</dd>
            </div>
            <div>
              <dt>{t("Compute")}</dt>
              <dd>{t("Python Worker · CPU")}</dd>
            </div>
            <div>
              <dt>{t("Output")}</dt>
              <dd>{t("Execution receipt")}</dd>
            </div>
          </dl>
          {!enabled ? (
            <p>
              {t(
                "Guided execution needs the live Controller. Use the technical views for offline examples.",
              )}
            </p>
          ) : null}
          <p className="guide-note">
            {t(
              "This example produces a local execution receipt. It does not create a consensus checkpoint or qualify Feature010.",
            )}
          </p>
        </section>
        <section
          className="guided-card result-card"
          aria-labelledby="guided-result-heading"
        >
          <p className="eyebrow">{t("Your run")}</p>
          <h2 id="guided-result-heading">
            {t(
              receipt
                ? "Result ready"
                : status
                  ? (stateLabels[status.state] ?? "Status unavailable")
                  : intent
                    ? "Sending your request"
                    : "Ready when you are",
            )}
          </h2>
          <div className="guided-status" role="status" aria-live="polite">
            {receipt ? (
              <>
                <span className="result-symbol" aria-hidden="true">
                  ✓
                </span>
                <p>
                  {t(
                    "The Controller returned a receipt. Its hash and connection to this request were checked.",
                  )}
                </p>
              </>
            ) : (
              <>
                <span
                  className={`result-symbol ${busy ? "pending" : "idle"}`}
                  aria-hidden="true"
                >
                  {busy ? "…" : "→"}
                </span>
                <p>
                  {t(
                    !intent
                      ? "Choose a name and start training. Progress will appear here automatically."
                      : status
                        ? "The state shown here comes from the Controller."
                        : "Waiting for the Controller to confirm admission.",
                  )}
                </p>
              </>
            )}
          </div>
          {status ? (
            <p className="run-identity">
              {t("Execution ID")}
              <code>{status.lineage.executionId ?? status.statusId}</code>
            </p>
          ) : null}
          {error ? (
            <div className="guided-error" role="alert">
              <strong>{t("Unable to confirm the result")}</strong>
              <p>{message(error)}</p>
              {!status && intent ? (
                <p>
                  {t(
                    "Admission is uncertain. Do not resubmit blindly; inspect the request in the technical views.",
                  )}
                </p>
              ) : null}
            </div>
          ) : null}
          {paused ? (
            <p>
              {t(
                "Automatic updates paused after 90 checks. The run may still be active; check its status again.",
              )}
            </p>
          ) : null}
          <div className="guided-actions">
            {status?.lineage.executionId ? <PresentationLink executionId={status.lineage.executionId} /> : null}
            {workspace && status ? <a href="#/campaigns">{t("Back to campaign")}</a> : null}
            {receipt ? (
              <button className="primary" type="button" onClick={download}>
                {t("Download receipt")}
              </button>
            ) : status && !busy ? (
              <button type="button" onClick={checkAgain}>
                {t("Check status again")}
              </button>
            ) : null}
            {terminal && !busy ? (
              <button type="button" onClick={reset}>
                {t("Prepare another run")}
              </button>
            ) : null}
          </div>
          <details className="guided-technical">
            <summary>{t("Technical details & original JSON")}</summary>
            <p>
              {t(
                "The receipt confirms this local plugin execution, not a validator quorum.",
              )}
            </p>
            <pre>
              {JSON.stringify(
                {
                  intent: intent ?? null,
                  status: status ?? null,
                  receipt: receipt ?? null,
                },
                null,
                2,
              )}
            </pre>
          </details>
        </section>
      </div>
      <ProtocolGuide />
      <p className="guide-note">
        {t(
          workspace
            ? "The campaign and workload come from your shared local profile. Controller registry entries document governance; the existing local Controller executes this run."
            : "Controller registry entries are local drafts. They do not configure this run. Presentation and Admin use the same Controller, with separate run lists.",
        )}
      </p>
    </div>
  );
}
