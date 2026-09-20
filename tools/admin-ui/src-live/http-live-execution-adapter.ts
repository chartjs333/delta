import { AdminUiError } from "../src/core/errors";
import { validateExecutionReceipt } from "../src/data/receipt-schema";
import {
  computeSha256PrefixedSync,
  jcsCanonicalize,
} from "../src/modules/live-execution/canonical-jcs";
import type {
  LiveExecutionPort,
  LiveExecutionReceipt,
  LiveExecutionSourceDescriptor,
  LiveExecutionState,
  LiveExecutionStatus,
  LiveWorkloadSelection,
} from "../src/modules/live-execution/live-execution-port";

const CONTRACT_FREEZE_SHA = "66e3e7e5bb07a48aadbee8d9c4683144b812d229";
const HTTP_PROTOCOL_ID = "deltareduce.step5c.http.v1";
const CONTRACT_SCHEMA_VERSION = "1.0.0";
const FORMAL_SEMANTICS_ID =
  "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
const READINESS_PATH = "/readyz";
const API_PREFIX = "/api/v1";
const MAX_JSON_BYTES = 10_485_760;
const MAX_JSON_DEPTH = 32;
const DEFAULT_TIMEOUT_MS = 30_000;
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;
const HASH_PATTERN = /^sha256:[0-9a-f]{64}$/u;
const BUILD_ID_PATTERN = /^[0-9a-f]{40}$/u;
const STATUS_STATES = new Set<LiveExecutionState>([
  "ADMITTED",
  "QUEUED",
  "RUNNING",
  "COMPLETED",
  "FAILED",
  "TIMED_OUT",
  "CANCELLED",
  "STALE_UNAVAILABLE",
]);
const TERMINAL_STATUS_STATES = new Set<LiveExecutionState>([
  "COMPLETED",
  "FAILED",
  "TIMED_OUT",
  "CANCELLED",
]);
const ERROR_STATUS_STATES = new Set<LiveExecutionState>([
  "FAILED",
  "TIMED_OUT",
  "CANCELLED",
]);

type JsonRecord = Record<string, unknown>;

interface RuntimeCompatibility {
  readonly buildId: string;
}

export interface HttpLiveExecutionAdapterOptions {
  /** Test seam only. Production uses the browser's same-origin fetch. */
  readonly fetchImpl?: typeof fetch;
  /** Test seam only. Production validates window.location. */
  readonly pageUrl?: URL;
  readonly timeoutMs?: number;
}

export class HttpLiveExecutionAdapter implements LiveExecutionPort {
  private readonly fetchImpl: typeof fetch;
  private readonly pageUrl: URL;
  private readonly timeoutMs: number;
  private readonly statuses = new Map<string, LiveExecutionStatus>();
  private readonly statusOrder: string[] = [];
  private readonly workloads = new Map<string, LiveWorkloadSelection>();
  private readonly receipts = new Map<string, LiveExecutionReceipt>();
  private runtimeCompatibility?: Promise<RuntimeCompatibility>;

  constructor(options: HttpLiveExecutionAdapterOptions = {}) {
    this.fetchImpl = options.fetchImpl ?? globalThis.fetch.bind(globalThis);
    this.pageUrl = options.pageUrl ?? new URL(globalThis.location.href);
    this.timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    assertSecurePageOrigin(this.pageUrl);
  }

  async describeLiveSource(): Promise<LiveExecutionSourceDescriptor> {
    await this.ensureRuntimeCompatibility();
    return {
      adapterId: "same-origin-http-live-execution",
      label: "Same-origin Controller HTTP",
      mode: "HTTP_LIVE",
      transportProfile:
        this.pageUrl.protocol === "https:"
          ? "HTTPS_SAME_ORIGIN"
          : "HTTP_SAME_ORIGIN_LOOPBACK",
      capabilities: [
        "live.intent.preview",
        "live.intent.submit",
        "live.status.read",
        "live.receipt.read",
        "live.execution.cancel",
      ],
      contractFreezeSha: CONTRACT_FREEZE_SHA,
    };
  }

  async previewDraft(
    operation: Parameters<LiveExecutionPort["previewDraft"]>[0],
    workload: Parameters<LiveExecutionPort["previewDraft"]>[1],
  ) {
    return {
      state: "DRAFT" as const,
      operation,
      workload,
      digestState: "COMPUTED_INFORMATIONAL" as const,
      authority: "PRESENTATION_MOCK" as const,
    };
  }

  async listStatuses(): Promise<readonly LiveExecutionStatus[]> {
    return this.statusOrder
      .map((executionId) => this.statuses.get(executionId))
      .filter((status): status is LiveExecutionStatus => status !== undefined)
      .map(copyStatus);
  }

  async submitIntent(intent: unknown): Promise<LiveExecutionStatus> {
    const intentRecord = requireRecord(intent, "ExecutionIntent");
    assertJsonDepth(intentRecord);
    const requestBody = JSON.stringify(intentRecord);
    if (new TextEncoder().encode(requestBody).byteLength > MAX_JSON_BYTES) {
      throw new AdminUiError(
        "INPUT_LIMIT_EXCEEDED",
        "The execution intent exceeds the 10 MiB transport limit.",
      );
    }

    const runtime = await this.ensureRuntimeCompatibility();
    const response = requireRecord(
      await this.requestJson(`${API_PREFIX}/intent/submit`, {
        method: "POST",
        body: requestBody,
      }),
      "intent submission response",
    );
    if (response.action !== "ADMITTED" && response.action !== "ALREADY_ADMITTED") {
      throw contractError("Controller returned an invalid submission action.");
    }

    const rawStatus = requireRecord(response.status, "submission status");
    const executionId = requireUuid(rawStatus.execution_id, "status.execution_id");
    const workload = readIntentWorkload(intentRecord);
    const status = { ...this.decodeStatus(rawStatus), workload };
    validateSubmissionLineage(
      response.admission,
      intentRecord,
      status,
      runtime.buildId,
    );
    this.workloads.set(executionId, workload);
    const cachedStatus = this.cacheStatus(status);

    if (response.receipt !== undefined && response.receipt !== null) {
      this.receipts.set(
        executionId,
        validateLiveReceipt(
          response.receipt,
          executionId,
          cachedStatus,
          runtime.buildId,
        ),
      );
    }
    return copyStatus(cachedStatus);
  }

  async getStatus(executionId: string): Promise<LiveExecutionStatus> {
    const safeExecutionId = requireUuid(executionId, "execution_id");
    const rawStatus = requireRecord(
      await this.requestJson(
        `${API_PREFIX}/execution/${encodeURIComponent(safeExecutionId)}/status`,
        { method: "GET" },
      ),
      "execution status",
    );
    const status = this.decodeStatus(rawStatus);
    if (status.statusId !== safeExecutionId) {
      throw contractError("Status execution lineage does not match the request.");
    }
    return copyStatus(this.cacheStatus(status));
  }

  async getReceipt(executionId: string): Promise<LiveExecutionReceipt> {
    const safeExecutionId = requireUuid(executionId, "execution_id");
    const cached = this.receipts.get(safeExecutionId);
    if (cached) return cloneReceipt(cached);

    const runtime = await this.ensureRuntimeCompatibility();
    const rawReceipt = await this.requestJson(
      `${API_PREFIX}/execution/${encodeURIComponent(safeExecutionId)}/receipt`,
      { method: "GET" },
    );
    const receipt = validateLiveReceipt(
      rawReceipt,
      safeExecutionId,
      this.statuses.get(safeExecutionId),
      runtime.buildId,
    );
    this.receipts.set(safeExecutionId, receipt);
    return cloneReceipt(receipt);
  }

  async cancelExecution(executionId: string): Promise<LiveExecutionStatus> {
    const safeExecutionId = requireUuid(executionId, "execution_id");
    const rawStatus = requireRecord(
      await this.requestJson(
        `${API_PREFIX}/execution/${encodeURIComponent(safeExecutionId)}/cancel`,
        { method: "POST", body: "{}" },
      ),
      "cancellation status",
    );
    const status = this.decodeStatus(rawStatus);
    if (status.statusId !== safeExecutionId) {
      throw contractError("Cancellation lineage does not match the request.");
    }
    const cachedStatus = this.cacheStatus(status);
    this.receipts.delete(safeExecutionId);
    return copyStatus(cachedStatus);
  }

  private decodeStatus(raw: JsonRecord): LiveExecutionStatus {
    requireContractVersion(raw.schema_version, "status.schema_version");
    const executionId = requireUuid(raw.execution_id, "status.execution_id");
    const intentId = requireUuid(raw.intent_id, "status.intent_id");
    const admissionId = requireUuid(raw.admission_id, "status.admission_id");
    const intentDigest = requireHash(raw.intent_digest, "status.intent_digest");
    const admissionDigest = requireHash(
      raw.admission_digest,
      "status.admission_digest",
    );
    const operation = raw.operation;
    if (
      operation !== "TRAIN_TICKET" &&
      operation !== "EVALUATE_CHECKPOINT" &&
      operation !== "MATERIALIZE_DATASET"
    ) {
      throw contractError("Controller returned an invalid execution operation.");
    }
    const state = raw.state;
    if (typeof state !== "string" || !STATUS_STATES.has(state as LiveExecutionState)) {
      throw contractError("Controller returned an invalid execution state.");
    }
    if (typeof raw.updated_at !== "string" || Number.isNaN(Date.parse(raw.updated_at))) {
      throw contractError("Controller returned an invalid status timestamp.");
    }
    const isTerminal = TERMINAL_STATUS_STATES.has(state as LiveExecutionState);
    if (typeof raw.terminal !== "boolean" || raw.terminal !== isTerminal) {
      throw contractError("Controller returned an inconsistent terminal marker.");
    }
    const receiptDigest =
      raw.receipt_digest === undefined
        ? undefined
        : requireHash(raw.receipt_digest, "status.receipt_digest");
    const receiptExpected = state === "COMPLETED" && operation !== "MATERIALIZE_DATASET";
    if (
      (receiptExpected && receiptDigest === undefined) ||
      (!receiptExpected && receiptDigest !== undefined)
    ) {
      throw contractError("Controller returned inconsistent receipt status metadata.");
    }
    const errorExpected = ERROR_STATUS_STATES.has(state as LiveExecutionState);
    if (errorExpected) {
      requireRecord(raw.error, "terminal status error");
    } else if (raw.error !== undefined) {
      throw contractError("Controller returned an error for a non-failure status.");
    }

    return {
      statusId: executionId,
      state: state as LiveExecutionState,
      operation,
      ...(this.workloads.has(executionId)
        ? { workload: this.workloads.get(executionId) }
        : {}),
      updatedAt: raw.updated_at,
      terminal: raw.terminal,
      ...(receiptDigest ? { receiptDigest } : {}),
      authority: "CONTROLLER_HTTP_STATUS",
      trustBadge: "UNATTESTED_CONTROLLER_STATUS",
      summary: statusSummary(state as LiveExecutionState),
      lineage: {
        intentId,
        intentDigest,
        admissionId,
        admissionDigest,
        executionId,
      },
    };
  }

  private cacheStatus(status: LiveExecutionStatus): LiveExecutionStatus {
    const previous = this.statuses.get(status.statusId);
    if (
      previous &&
      (previous.operation !== status.operation ||
        previous.lineage.intentId !== status.lineage.intentId ||
        previous.lineage.intentDigest !== status.lineage.intentDigest ||
        previous.lineage.admissionId !== status.lineage.admissionId ||
        previous.lineage.admissionDigest !== status.lineage.admissionDigest ||
        previous.lineage.executionId !== status.lineage.executionId)
    ) {
      throw contractError(
        "Controller changed immutable execution lineage in a status response.",
      );
    }
    if (!this.statuses.has(status.statusId)) {
      this.statusOrder.unshift(status.statusId);
    }
    this.statuses.set(status.statusId, copyStatus(status));
    return status;
  }

  private async requestJson(
    path: string,
    request: { readonly method: "GET" | "POST"; readonly body?: string },
  ): Promise<unknown> {
    if (!path.startsWith(`${API_PREFIX}/`)) {
      throw contractError("Live adapter refused a non-API request path.");
    }
    await this.ensureRuntimeCompatibility();
    return this.fetchJson(path, request, true);
  }

  private ensureRuntimeCompatibility(): Promise<RuntimeCompatibility> {
    this.runtimeCompatibility ??= this.loadRuntimeCompatibility();
    return this.runtimeCompatibility;
  }

  private async loadRuntimeCompatibility(): Promise<RuntimeCompatibility> {
    const document = requireRecord(
      await this.fetchJson(READINESS_PATH, { method: "GET" }, false),
      "runtime readiness document",
    );
    requireContractVersion(document.schema_version, "readiness.schema_version");
    if (document.status !== "READY") {
      throw contractError("Controller runtime is not ready.");
    }
    if (document.protocol_id !== HTTP_PROTOCOL_ID) {
      throw contractError("Controller HTTP protocol is incompatible with this UI.");
    }
    if (document.contract_schema_version !== CONTRACT_SCHEMA_VERSION) {
      throw contractError("Controller contract schema is incompatible with this UI.");
    }
    if (document.formal_semantics_id !== FORMAL_SEMANTICS_ID) {
      throw contractError("Controller formal semantics identity is incompatible.");
    }
    return {
      buildId: requireBuildId(document.build_id, "readiness.build_id"),
    };
  }

  private async fetchJson(
    path: string,
    request: { readonly method: "GET" | "POST"; readonly body?: string },
    apiRequest: boolean,
  ): Promise<unknown> {
    const abortController = new AbortController();
    const timeout = globalThis.setTimeout(
      () => abortController.abort(),
      this.timeoutMs,
    );
    let response: Response;
    try {
      response = await this.fetchImpl(path, {
        method: request.method,
        headers: {
          Accept: "application/json",
          ...(apiRequest ? { "X-Delta-Request": "1" } : {}),
          ...(request.body === undefined
            ? {}
            : { "Content-Type": "application/json" }),
        },
        ...(request.body === undefined ? {} : { body: request.body }),
        cache: "no-store",
        credentials: "same-origin",
        redirect: "error",
        referrerPolicy: "no-referrer",
        signal: abortController.signal,
      });
    } catch (error: unknown) {
      const timedOut = abortController.signal.aborted;
      throw new AdminUiError(
        "SOURCE_UNAVAILABLE",
        timedOut
          ? "The Controller request timed out."
          : "The same-origin Controller is unavailable.",
        {},
        error instanceof Error ? { cause: error } : undefined,
      );
    } finally {
      globalThis.clearTimeout(timeout);
    }

    const body = await readBoundedJson(response);
    if (!response.ok) {
      throw httpError(response.status, body);
    }
    return body;
  }
}

function assertSecurePageOrigin(pageUrl: URL): void {
  if (pageUrl.protocol === "https:") return;
  if (pageUrl.protocol === "http:" && pageUrl.hostname === "127.0.0.1") return;
  throw new AdminUiError(
    "ACCESS_DENIED",
    "HTTP live mode is allowed only on 127.0.0.1; remote live mode requires HTTPS.",
  );
}

async function readBoundedJson(response: Response): Promise<unknown> {
  const declaredLength = response.headers.get("content-length");
  if (declaredLength !== null && Number(declaredLength) > MAX_JSON_BYTES) {
    throw new AdminUiError(
      "INPUT_LIMIT_EXCEEDED",
      "The Controller response exceeds the 10 MiB safety limit.",
    );
  }
  const text = await response.text();
  if (new TextEncoder().encode(text).byteLength > MAX_JSON_BYTES) {
    throw new AdminUiError(
      "INPUT_LIMIT_EXCEEDED",
      "The Controller response exceeds the 10 MiB safety limit.",
    );
  }
  if (!text.trim()) return {};
  let value: unknown;
  try {
    value = JSON.parse(text) as unknown;
  } catch {
    throw contractError("Controller returned malformed JSON.");
  }
  assertJsonDepth(value);
  return value;
}

function assertJsonDepth(root: unknown): void {
  const stack: Array<{ readonly value: unknown; readonly depth: number }> = [
    { value: root, depth: 1 },
  ];
  while (stack.length > 0) {
    const current = stack.pop();
    if (!current) break;
    if (current.depth > MAX_JSON_DEPTH) {
      throw new AdminUiError(
        "INPUT_LIMIT_EXCEEDED",
        "JSON exceeds the live transport nesting depth limit of 32.",
      );
    }
    if (Array.isArray(current.value)) {
      for (const child of current.value) {
        stack.push({ value: child, depth: current.depth + 1 });
      }
    } else if (typeof current.value === "object" && current.value !== null) {
      for (const child of Object.values(current.value)) {
        stack.push({ value: child, depth: current.depth + 1 });
      }
    }
  }
}

function requireRecord(value: unknown, label: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw contractError(`Controller returned an invalid ${label}.`);
  }
  return value as JsonRecord;
}

function requireUuid(value: unknown, field: string): string {
  if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
    throw contractError(`Invalid ${field}.`);
  }
  return value;
}

function requireHash(value: unknown, field: string): string {
  if (typeof value !== "string" || !HASH_PATTERN.test(value)) {
    throw contractError(`Invalid ${field}.`);
  }
  return value;
}

function requireBuildId(value: unknown, field: string): string {
  if (typeof value !== "string" || !BUILD_ID_PATTERN.test(value)) {
    throw contractError(`Invalid ${field}.`);
  }
  return value;
}

function requireContractVersion(value: unknown, field: string): void {
  if (value !== CONTRACT_SCHEMA_VERSION) {
    throw contractError(`Invalid ${field}.`);
  }
}

function readIntentWorkload(intent: JsonRecord): LiveWorkloadSelection {
  const workload = requireRecord(intent.workload, "intent workload");
  const modelPluginId = workload.model_plugin_id;
  const datasetId = workload.dataset_id;
  const requestedScope = workload.requested_scope;
  if (
    typeof modelPluginId !== "string" ||
    typeof datasetId !== "string" ||
    (requestedScope !== "PLUGIN_BOUNDARY" &&
      requestedScope !== "MODEL_DATASET_BINDING_ONLY")
  ) {
    throw contractError("ExecutionIntent contains an invalid workload binding.");
  }
  return { modelPluginId, datasetId, requestedScope };
}

function validateSubmissionLineage(
  value: unknown,
  intent: JsonRecord,
  status: LiveExecutionStatus,
  buildId: string,
): void {
  const admission = requireRecord(value, "submission admission");
  requireContractVersion(admission.schema_version, "admission.schema_version");
  const intentId = requireUuid(intent.intent_id, "intent.intent_id");
  const intentDigest = requireHash(intent.intent_digest, "intent.intent_digest");
  const admissionId = requireUuid(admission.admission_id, "admission.admission_id");
  const admissionDigest = requireHash(
    admission.admission_digest,
    "admission.admission_digest",
  );
  const executionId = requireUuid(
    admission.execution_id,
    "admission.execution_id",
  );
  const policyContext = requireRecord(
    admission.policy_context,
    "admission policy context",
  );
  const controllerCommit = requireBuildId(
    policyContext.controller_commit,
    "admission.policy_context.controller_commit",
  );
  if (policyContext.verdict !== "ADMITTED" || controllerCommit !== buildId) {
    throw contractError("Admission policy context does not match the runtime.");
  }
  if (
    requireUuid(admission.intent_id, "admission.intent_id") !== intentId ||
    requireHash(admission.intent_digest, "admission.intent_digest") !== intentDigest ||
    status.lineage.intentId !== intentId ||
    status.lineage.intentDigest !== intentDigest ||
    status.lineage.admissionId !== admissionId ||
    status.lineage.admissionDigest !== admissionDigest ||
    status.lineage.executionId !== executionId ||
    status.operation !== intent.operation
  ) {
    throw contractError(
      "Submission admission, intent, and status lineage do not match.",
    );
  }
}

function validateLiveReceipt(
  value: unknown,
  executionId: string,
  status: LiveExecutionStatus | undefined,
  buildId: string,
): LiveExecutionReceipt {
  assertNoConsensusClaims(value);
  let receipt;
  try {
    receipt = validateExecutionReceipt(value);
  } catch (error: unknown) {
    throw contractError(
      "Controller returned a receipt that failed structural validation.",
      error,
    );
  }
  const provenance = requireRecord(receipt.provenance, "receipt provenance");
  if (
    requireBuildId(
      provenance.controller_commit,
      "receipt.provenance.controller_commit",
    ) !== buildId ||
    requireBuildId(provenance.producer_commit, "receipt.provenance.producer_commit") !==
      buildId
  ) {
    throw contractError("Receipt build provenance does not match the runtime.");
  }
  if (
    receipt.execution.verdict !== "SUCCESS" ||
    receipt.execution.terminal_status !== "COMPLETED"
  ) {
    throw contractError("Controller returned a non-success terminal receipt.");
  }
  const lineage = {
    intent_id: requireUuid(provenance.intent_id, "receipt.provenance.intent_id"),
    intent_digest: requireHash(
      provenance.intent_digest,
      "receipt.provenance.intent_digest",
    ),
    admission_id: requireUuid(
      provenance.admission_id,
      "receipt.provenance.admission_id",
    ),
    admission_digest: requireHash(
      provenance.admission_digest,
      "receipt.provenance.admission_digest",
    ),
    execution_id: requireUuid(
      provenance.execution_id,
      "receipt.provenance.execution_id",
    ),
  };
  if (lineage.execution_id !== executionId) {
    throw contractError("Receipt execution lineage does not match the request.");
  }
  if (
    status &&
    (lineage.intent_id !== status.lineage.intentId ||
      lineage.intent_digest !== status.lineage.intentDigest ||
      lineage.admission_id !== status.lineage.admissionId ||
      lineage.admission_digest !== status.lineage.admissionDigest)
  ) {
    throw contractError("Receipt lineage does not match the Controller status.");
  }
  if (!status?.receiptDigest) {
    throw contractError("Receipt status digest is unavailable.");
  }
  let computedReceiptDigest: string;
  try {
    computedReceiptDigest = computeSha256PrefixedSync(jcsCanonicalize(receipt));
  } catch (error: unknown) {
    throw contractError("Controller receipt could not be canonicalized.", error);
  }
  if (computedReceiptDigest !== status.receiptDigest) {
    throw contractError("Receipt digest does not match the Controller status.");
  }
  return receipt as LiveExecutionReceipt;
}

function assertNoConsensusClaims(root: unknown): void {
  const forbiddenKeys = new Set([
    "round_id",
    "state_root",
    "wal_sequence",
    "qc",
    "apply_qc",
    "stage_c_proposal",
    "consensus_round",
    "consensus_view",
  ]);
  const stack: unknown[] = [root];
  while (stack.length > 0) {
    const value = stack.pop();
    if (Array.isArray(value)) {
      stack.push(...value);
      continue;
    }
    if (typeof value !== "object" || value === null) continue;
    for (const [key, child] of Object.entries(value)) {
      if (forbiddenKeys.has(key)) {
        throw contractError("Controller receipt contains a forbidden consensus claim.");
      }
      stack.push(child);
    }
  }
}

function statusSummary(state: LiveExecutionState): string {
  return `Controller HTTP status is ${state}. This local execution status is not a consensus claim.`;
}

function copyStatus(status: LiveExecutionStatus): LiveExecutionStatus {
  return {
    ...status,
    ...(status.workload ? { workload: { ...status.workload } } : {}),
    lineage: { ...status.lineage },
  };
}

function cloneReceipt(receipt: LiveExecutionReceipt): LiveExecutionReceipt {
  return JSON.parse(JSON.stringify(receipt)) as LiveExecutionReceipt;
}

function contractError(message: string, cause?: unknown): AdminUiError {
  return new AdminUiError(
    "CAPABILITY_CONTRACT_VIOLATED",
    message,
    {},
    cause instanceof Error ? { cause } : undefined,
  );
}

function httpError(status: number, body: unknown): AdminUiError {
  const bodyRecord =
    typeof body === "object" && body !== null && !Array.isArray(body)
      ? (body as JsonRecord)
      : {};
  const nestedError =
    typeof bodyRecord.error === "object" &&
    bodyRecord.error !== null &&
    !Array.isArray(bodyRecord.error)
      ? (bodyRecord.error as JsonRecord)
      : bodyRecord;
  const codeCandidate = nestedError.code ?? nestedError.error_code;
  const serverCode =
    typeof codeCandidate === "string" && /^ERR_[A-Z0-9_]+$/u.test(codeCandidate)
      ? codeCandidate
      : "ERR_HTTP_REQUEST_REJECTED";
  const suffix = ` (${serverCode})`;
  switch (status) {
    case 400:
      return new AdminUiError(
        "DOCUMENT_STRUCTURALLY_INVALID",
        `Controller rejected the request as malformed${suffix}.`,
        { status, serverCode },
      );
    case 401:
      return new AdminUiError(
        "ACCESS_DENIED",
        `Controller authentication is required${suffix}.`,
        { status, serverCode },
      );
    case 403:
      return new AdminUiError(
        "ACCESS_DENIED",
        `Controller policy denied the request${suffix}.`,
        { status, serverCode },
      );
    case 404:
      return new AdminUiError(
        "SOURCE_UNAVAILABLE",
        `The requested execution artifact is unavailable${suffix}.`,
        { status, serverCode },
      );
    case 409:
      return new AdminUiError(
        "CAPABILITY_CONTRACT_VIOLATED",
        `Controller reported an execution conflict${suffix}.`,
        { status, serverCode },
      );
    case 413:
      return new AdminUiError(
        "INPUT_LIMIT_EXCEEDED",
        `Controller rejected a payload larger than 10 MiB${suffix}.`,
        { status, serverCode },
      );
    case 429:
      return new AdminUiError(
        "SOURCE_UNAVAILABLE",
        `Controller backpressure limit is active${suffix}.`,
        { status, serverCode },
      );
    default:
      return new AdminUiError(
        "SOURCE_UNAVAILABLE",
        `Controller request failed with HTTP ${status}${suffix}.`,
        { status, serverCode },
      );
  }
}
