import type { ExecutionReceipt } from "../../data/receipt-schema";

export type LiveExecutionOperation =
  | "TRAIN_TICKET"
  | "EVALUATE_CHECKPOINT"
  | "MATERIALIZE_DATASET";

export type LiveExecutionScope =
  | "PLUGIN_BOUNDARY"
  | "MODEL_DATASET_BINDING_ONLY";

export type LiveExecutionState =
  | "DRAFT"
  | "REJECTED"
  | "ADMITTED"
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "TIMED_OUT"
  | "CANCELLED"
  | "STALE_UNAVAILABLE";

export type LiveExecutionCapability =
  | "live.intent.preview"
  | "live.intent.submit"
  | "live.status.mock"
  | "live.status.read"
  | "live.receipt.read"
  | "live.execution.cancel";

export interface LiveExecutionSourceDescriptor {
  readonly adapterId: string;
  readonly label: string;
  readonly mode: "MOCK_ONLY" | "HTTP_LIVE";
  readonly transportProfile:
    | "NONE_PHASE_4"
    | "HTTP_SAME_ORIGIN_LOOPBACK"
    | "HTTPS_SAME_ORIGIN";
  readonly capabilities: readonly LiveExecutionCapability[];
  readonly contractFreezeSha: string;
}

export interface LiveWorkloadSelection {
  readonly modelPluginId: string;
  readonly datasetId: string;
  readonly requestedScope: LiveExecutionScope;
}

export interface LiveIntentDraftPreview {
  readonly state: "DRAFT";
  readonly operation: LiveExecutionOperation;
  readonly workload: LiveWorkloadSelection;
  readonly digestState: "COMPUTED_INFORMATIONAL" | "AWAITING_CONTRACT_ARTIFACTS";
  readonly intentDigest?: string;
  readonly authority: "PRESENTATION_MOCK";
}

export interface LiveExecutionLineageView {
  readonly intentId?: string;
  readonly intentDigest?: string;
  readonly admissionId?: string;
  readonly admissionDigest?: string;
  readonly executionId?: string;
}

export interface LiveExecutionStatus {
  readonly statusId: string;
  readonly state: LiveExecutionState;
  readonly operation: LiveExecutionOperation;
  readonly workload?: LiveWorkloadSelection;
  readonly updatedAt: string;
  readonly terminal?: boolean;
  readonly receiptDigest?: string;
  readonly authority: "PRESENTATION_MOCK" | "CONTROLLER_HTTP_STATUS";
  readonly trustBadge:
    | "UNATTESTED_MOCK_STATUS"
    | "UNATTESTED_CONTROLLER_STATUS"
    | "UNATTESTED_PLUGIN_BOUNDARY_RECORD";
  readonly summary: string;
  readonly lineage: LiveExecutionLineageView;
}

export interface LiveExecutionReceipt extends ExecutionReceipt {
  readonly provenance: ExecutionReceipt["provenance"] & {
    readonly intent_id: string;
    readonly intent_digest: string;
    readonly admission_id: string;
    readonly admission_digest: string;
    readonly execution_id: string;
  };
}

export interface LiveExecutionPort {
  describeLiveSource(): Promise<LiveExecutionSourceDescriptor>;
  previewDraft(
    operation: LiveExecutionOperation,
    workload: LiveWorkloadSelection,
  ): Promise<LiveIntentDraftPreview>;
  listStatuses(): Promise<readonly LiveExecutionStatus[]>;
  getStatus(statusId: string): Promise<LiveExecutionStatus>;
  submitIntent(intent: unknown): Promise<LiveExecutionStatus>;
  getReceipt?(executionId: string): Promise<LiveExecutionReceipt>;
  cancelExecution?(executionId: string): Promise<LiveExecutionStatus>;
}
