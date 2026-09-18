import { AdminUiError } from "../../core/errors";
import type {
  LiveExecutionOperation,
  LiveExecutionPort,
  LiveExecutionSourceDescriptor,
  LiveExecutionStatus,
  LiveWorkloadSelection,
} from "./live-execution-port";

const CONTRACT_FREEZE_SHA = "66e3e7e5bb07a48aadbee8d9c4683144b812d229";

const DEFAULT_WORKLOAD: LiveWorkloadSelection = {
  modelPluginId: "tabular-10gene-phenotype-v1",
  datasetId: "synthetic-10gene-cohort-v1",
  requestedScope: "PLUGIN_BOUNDARY",
};

const INITIAL_MOCK_STATUSES: readonly LiveExecutionStatus[] = [
  {
    statusId: "draft-preview",
    state: "DRAFT",
    operation: "TRAIN_TICKET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:00:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Intent draft is local presentation state only.",
    lineage: {},
  },
  {
    statusId: "rejected-policy",
    state: "REJECTED",
    operation: "TRAIN_TICKET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:01:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Mock gate rejected an expired or incompatible request.",
    lineage: { intentId: "00000000-0000-4000-8000-000000000001" },
  },
  {
    statusId: "admitted",
    state: "ADMITTED",
    operation: "TRAIN_TICKET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:02:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Mock admission exists; no worker has been started from the browser.",
    lineage: {
      intentId: "00000000-0000-4000-8000-000000000002",
      admissionId: "10000000-0000-4000-8000-000000000002",
      executionId: "20000000-0000-4000-8000-000000000002",
    },
  },
  {
    statusId: "queued",
    state: "QUEUED",
    operation: "TRAIN_TICKET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:03:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Mock execution is waiting behind a bounded controller queue.",
    lineage: {
      intentId: "00000000-0000-4000-8000-000000000003",
      admissionId: "10000000-0000-4000-8000-000000000003",
      executionId: "20000000-0000-4000-8000-000000000003",
    },
  },
  {
    statusId: "running",
    state: "RUNNING",
    operation: "TRAIN_TICKET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:04:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Mock worker status is running; browser still holds no worker handle.",
    lineage: {
      intentId: "00000000-0000-4000-8000-000000000004",
      admissionId: "10000000-0000-4000-8000-000000000004",
      executionId: "20000000-0000-4000-8000-000000000004",
    },
  },
  {
    statusId: "completed",
    state: "COMPLETED",
    operation: "EVALUATE_CHECKPOINT",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:05:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_PLUGIN_BOUNDARY_RECORD",
    summary: "Mock terminal receipt is structurally bound and remains unattested.",
    lineage: {
      intentId: "00000000-0000-4000-8000-000000000005",
      intentDigest: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      admissionId: "10000000-0000-4000-8000-000000000005",
      admissionDigest: "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      executionId: "20000000-0000-4000-8000-000000000005",
    },
  },
  {
    statusId: "failed",
    state: "FAILED",
    operation: "TRAIN_TICKET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:06:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Mock execution failed without producing a success receipt.",
    lineage: {
      intentId: "00000000-0000-4000-8000-000000000006",
      admissionId: "10000000-0000-4000-8000-000000000006",
      executionId: "20000000-0000-4000-8000-000000000006",
    },
  },
  {
    statusId: "timed-out",
    state: "TIMED_OUT",
    operation: "TRAIN_TICKET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:07:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Mock timeout is terminal and cannot be displayed as success.",
    lineage: {
      intentId: "00000000-0000-4000-8000-000000000007",
      admissionId: "10000000-0000-4000-8000-000000000007",
      executionId: "20000000-0000-4000-8000-000000000007",
    },
  },
  {
    statusId: "cancelled",
    state: "CANCELLED",
    operation: "MATERIALIZE_DATASET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:08:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Mock materialization was cancelled and has no receipt.",
    lineage: {
      intentId: "00000000-0000-4000-8000-000000000008",
      admissionId: "10000000-0000-4000-8000-000000000008",
      executionId: "20000000-0000-4000-8000-000000000008",
    },
  },
  {
    statusId: "stale-unavailable",
    state: "STALE_UNAVAILABLE",
    operation: "MATERIALIZE_DATASET",
    workload: DEFAULT_WORKLOAD,
    updatedAt: "2026-09-17T09:09:00.000Z",
    authority: "PRESENTATION_MOCK",
    trustBadge: "UNATTESTED_MOCK_STATUS",
    summary: "Mock status is stale because no controller transport is configured.",
    lineage: {
      executionId: "20000000-0000-4000-8000-000000000009",
    },
  },
];

export class MockLiveExecutionAdapter implements LiveExecutionPort {
  private statuses: LiveExecutionStatus[] = [...INITIAL_MOCK_STATUSES];

  async describeLiveSource(): Promise<LiveExecutionSourceDescriptor> {
    return {
      adapterId: "mock-live-execution",
      label: "Mock live execution",
      mode: "MOCK_ONLY",
      transportProfile: "NONE_PHASE_4",
      capabilities: ["live.intent.preview", "live.status.mock"],
      contractFreezeSha: CONTRACT_FREEZE_SHA,
    };
  }

  async previewDraft(
    operation: LiveExecutionOperation,
    workload: LiveWorkloadSelection,
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
    return this.statuses.map(copyStatus);
  }

  async getStatus(statusId: string): Promise<LiveExecutionStatus> {
    const status = this.statuses.find((item) => item.statusId === statusId);
    if (!status) {
      throw new AdminUiError(
        "SOURCE_UNAVAILABLE",
        "The requested mock execution status is unavailable.",
        { statusId },
      );
    }
    return copyStatus(status);
  }

  async submitIntent(rawIntent: unknown): Promise<LiveExecutionStatus> {
    const intent = rawIntent as Record<string, any>;
    const intentId = String(intent.intent_id ?? "00000000-0000-4000-8000-000000000099");
    const op = (intent.operation ?? "TRAIN_TICKET") as LiveExecutionOperation;
    const modelId = String(intent.workload?.model_plugin_id ?? DEFAULT_WORKLOAD.modelPluginId);
    const dsId = String(intent.workload?.dataset_id ?? DEFAULT_WORKLOAD.datasetId);
    const scope = (intent.workload?.requested_scope ?? DEFAULT_WORKLOAD.requestedScope);

    const newStatus: LiveExecutionStatus = {
      statusId: `submitted-${intentId.slice(0, 8)}`,
      state: "ADMITTED",
      operation: op,
      workload: {
        modelPluginId: modelId,
        datasetId: dsId,
        requestedScope: scope,
      },
      updatedAt: new Date().toISOString(),
      authority: "PRESENTATION_MOCK",
      trustBadge: "UNATTESTED_MOCK_STATUS",
      summary: `Mock gate admitted intent ${intentId.slice(0, 8)}; queued in mock state.`,
      lineage: {
        intentId,
        intentDigest: String(intent.intent_digest ?? "sha256:0000000000000000000000000000000000000000000000000000000000000000"),
        admissionId: `adm-${intentId.slice(0, 8)}`,
        admissionDigest: "sha256:1111111111111111111111111111111111111111111111111111111111111111",
        executionId: `exec-${intentId.slice(0, 8)}`,
      },
    };

    this.statuses = [newStatus, ...this.statuses];
    return copyStatus(newStatus);
  }
}

function copyStatus(status: LiveExecutionStatus): LiveExecutionStatus {
  return {
    ...status,
    workload: { ...status.workload },
    lineage: { ...status.lineage },
  };
}
