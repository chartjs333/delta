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
  | "live.status.mock";

export interface LiveExecutionSourceDescriptor {
  readonly adapterId: string;
  readonly label: string;
  readonly mode: "MOCK_ONLY";
  readonly transportProfile: "NONE_PHASE_4";
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
  readonly digestState: "AWAITING_CONTRACT_ARTIFACTS";
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
  readonly workload: LiveWorkloadSelection;
  readonly updatedAt: string;
  readonly authority: "PRESENTATION_MOCK";
  readonly trustBadge: "UNATTESTED_MOCK_STATUS" | "UNATTESTED_PLUGIN_BOUNDARY_RECORD";
  readonly summary: string;
  readonly lineage: LiveExecutionLineageView;
}

export interface LiveExecutionPort {
  describeLiveSource(): Promise<LiveExecutionSourceDescriptor>;
  previewDraft(
    operation: LiveExecutionOperation,
    workload: LiveWorkloadSelection,
  ): Promise<LiveIntentDraftPreview>;
  listStatuses(): Promise<readonly LiveExecutionStatus[]>;
  getStatus(statusId: string): Promise<LiveExecutionStatus>;
}
