import {
  CANONICAL_DESCRIPTOR_CATALOG,
  type CompatibilityMatrixEntry,
} from "../../data/descriptors-catalog";
import {
  computeIntentDigestSync,
  jcsCanonicalize,
} from "./canonical-jcs";
import type {
  LiveExecutionOperation,
  LiveExecutionScope,
} from "./live-execution-port";

export interface TrainTicketPayload {
  readonly ticket_id: string;
  readonly partition_id: string;
}

export interface EvaluateCheckpointPayload {
  readonly checkpoint_coordinates: readonly number[];
}

export interface MaterializeDatasetPayload {
  readonly cache_key?: string;
}

export type OperationPayload =
  | TrainTicketPayload
  | EvaluateCheckpointPayload
  | MaterializeDatasetPayload;

export type OperatorRole = "OPERATOR" | "RESEARCHER" | "AUDITOR";

export interface DeclaredOperator {
  readonly role: OperatorRole;
  readonly subject_id: string;
}

export interface ExecutionConstraints {
  readonly timeout_seconds: number;
  readonly requested_allow_downloads: boolean;
  readonly retry_of_intent_id?: string;
}

export interface WorkloadSelectionState {
  readonly model_plugin_id: string;
  readonly dataset_id: string;
  readonly requested_scope: LiveExecutionScope;
  readonly catalog_backend_ref: string;
}

export interface ExecutionIntentDraft {
  readonly operation: LiveExecutionOperation;
  readonly declared_operator: DeclaredOperator;
  readonly workload: WorkloadSelectionState;
  readonly execution_constraints: ExecutionConstraints;
  readonly operation_payload: OperationPayload;
}

export interface ExecutionIntentDocument {
  readonly schema_version: "1.0.0";
  readonly intent_id: string;
  readonly created_at: string;
  readonly expires_at: string;
  readonly declared_operator: DeclaredOperator;
  readonly workload: WorkloadSelectionState;
  readonly operation: LiveExecutionOperation;
  readonly operation_payload: OperationPayload;
  readonly execution_constraints: ExecutionConstraints;
  readonly intent_digest: string;
}

export interface IntentValidationIssue {
  readonly field: string;
  readonly message: string;
}

const IDENTIFIER_PATTERN = /^[A-Za-z0-9_-]+$/u;
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/iu;

export function getDefaultWorkload(): WorkloadSelectionState {
  return {
    model_plugin_id: "tabular-10gene-phenotype-v1",
    dataset_id: "synthetic-10gene-cohort-v1",
    requested_scope: "PLUGIN_BOUNDARY",
    catalog_backend_ref: CANONICAL_DESCRIPTOR_CATALOG.source.backend_ref,
  };
}

export function createDefaultIntentDraft(
  operation: LiveExecutionOperation = "TRAIN_TICKET",
): ExecutionIntentDraft {
  const workload = getDefaultWorkload();
  return {
    operation,
    declared_operator: {
      role: "OPERATOR",
      subject_id: "operator.alpha",
    },
    workload,
    execution_constraints: {
      timeout_seconds: 900,
      requested_allow_downloads: false,
    },
    operation_payload: getDefaultPayloadForOperation(operation),
  };
}

export function getDefaultPayloadForOperation(
  operation: LiveExecutionOperation,
): OperationPayload {
  switch (operation) {
    case "TRAIN_TICKET":
      return {
        ticket_id: "ticket_A-0001",
        partition_id: "partition_00",
      };
    case "EVALUATE_CHECKPOINT":
      return {
        checkpoint_coordinates: [100, 200, 300, 400],
      };
    case "MATERIALIZE_DATASET":
      return {
        cache_key: "cache_synth_01",
      };
  }
}

export function validateIntentDraft(
  draft: ExecutionIntentDraft,
): readonly IntentValidationIssue[] {
  const issues: IntentValidationIssue[] = [];

  // Operator checks
  if (
    !draft.declared_operator.subject_id ||
    draft.declared_operator.subject_id.trim().length === 0
  ) {
    issues.push({
      field: "declared_operator.subject_id",
      message: "Subject ID is required.",
    });
  } else if (draft.declared_operator.subject_id.length > 128) {
    issues.push({
      field: "declared_operator.subject_id",
      message: "Subject ID must be at most 128 characters.",
    });
  }

  // Workload model & dataset in catalog
  const model = CANONICAL_DESCRIPTOR_CATALOG.model_plugins.find(
    (m) => m.plugin_id === draft.workload.model_plugin_id,
  );
  if (!model) {
    issues.push({
      field: "workload.model_plugin_id",
      message: `Model plugin '${draft.workload.model_plugin_id}' is not in frozen catalog.`,
    });
  }

  const dataset = CANONICAL_DESCRIPTOR_CATALOG.datasets.find(
    (d) => d.dataset_id === draft.workload.dataset_id,
  );
  if (!dataset) {
    issues.push({
      field: "workload.dataset_id",
      message: `Dataset '${draft.workload.dataset_id}' is not in frozen catalog.`,
    });
  }

  // Compatibility
  if (model && dataset) {
    const comp: CompatibilityMatrixEntry | undefined =
      CANONICAL_DESCRIPTOR_CATALOG.compatibility.find(
        (c) =>
          c.model_plugin_id === draft.workload.model_plugin_id &&
          c.dataset_id === draft.workload.dataset_id,
      );
    if (!comp || !comp.contract_compatible) {
      issues.push({
        field: "workload",
        message: `Pair '${draft.workload.model_plugin_id}' and '${draft.workload.dataset_id}' is not contract compatible.`,
      });
    } else {
      const allowed = comp.requested_scope_allowed[draft.workload.requested_scope];
      if (!allowed) {
        issues.push({
          field: "workload.requested_scope",
          message: `Scope '${draft.workload.requested_scope}' is not permitted for this workload in catalog.`,
        });
      }
    }
  }

  // TRAIN_TICKET must have requested_scope === "PLUGIN_BOUNDARY"
  if (
    draft.operation === "TRAIN_TICKET" &&
    draft.workload.requested_scope !== "PLUGIN_BOUNDARY"
  ) {
    issues.push({
      field: "workload.requested_scope",
      message: "TRAIN_TICKET operation requires scope 'PLUGIN_BOUNDARY'.",
    });
  }

  // Catalog backend ref check
  if (
    draft.workload.catalog_backend_ref !==
    CANONICAL_DESCRIPTOR_CATALOG.source.backend_ref
  ) {
    issues.push({
      field: "workload.catalog_backend_ref",
      message: `Catalog backend ref must match active catalog '${CANONICAL_DESCRIPTOR_CATALOG.source.backend_ref}'.`,
    });
  }

  // Constraints checks
  if (
    typeof draft.execution_constraints.timeout_seconds !== "number" ||
    !Number.isInteger(draft.execution_constraints.timeout_seconds) ||
    draft.execution_constraints.timeout_seconds < 1 ||
    draft.execution_constraints.timeout_seconds > 3600
  ) {
    issues.push({
      field: "execution_constraints.timeout_seconds",
      message: "Timeout must be an integer between 1 and 3600 seconds.",
    });
  }

  if (draft.execution_constraints.retry_of_intent_id) {
    if (!UUID_PATTERN.test(draft.execution_constraints.retry_of_intent_id)) {
      issues.push({
        field: "execution_constraints.retry_of_intent_id",
        message: "retry_of_intent_id must be a valid UUID.",
      });
    }
  }

  // Operation payload checks
  switch (draft.operation) {
    case "TRAIN_TICKET": {
      const payload = draft.operation_payload as Partial<TrainTicketPayload>;
      if (!payload.ticket_id || !IDENTIFIER_PATTERN.test(payload.ticket_id)) {
        issues.push({
          field: "operation_payload.ticket_id",
          message: "ticket_id must match ^[A-Za-z0-9_-]+$ (max 64 chars).",
        });
      } else if (payload.ticket_id.length > 64) {
        issues.push({
          field: "operation_payload.ticket_id",
          message: "ticket_id must not exceed 64 characters.",
        });
      }

      if (
        !payload.partition_id ||
        !IDENTIFIER_PATTERN.test(payload.partition_id)
      ) {
        issues.push({
          field: "operation_payload.partition_id",
          message: "partition_id must match ^[A-Za-z0-9_-]+$ (max 64 chars).",
        });
      } else if (payload.partition_id.length > 64) {
        issues.push({
          field: "operation_payload.partition_id",
          message: "partition_id must not exceed 64 characters.",
        });
      }
      break;
    }
    case "EVALUATE_CHECKPOINT": {
      const payload =
        draft.operation_payload as Partial<EvaluateCheckpointPayload>;
      if (
        !Array.isArray(payload.checkpoint_coordinates) ||
        payload.checkpoint_coordinates.length === 0
      ) {
        issues.push({
          field: "operation_payload.checkpoint_coordinates",
          message: "checkpoint_coordinates must be a non-empty array of integers.",
        });
      } else if (payload.checkpoint_coordinates.length > 4096) {
        issues.push({
          field: "operation_payload.checkpoint_coordinates",
          message: "checkpoint_coordinates must not exceed 4096 elements.",
        });
      } else {
        for (let i = 0; i < payload.checkpoint_coordinates.length; i++) {
          const val = payload.checkpoint_coordinates[i];
          if (
            typeof val !== "number" ||
            !Number.isInteger(val) ||
            val < -2147483648 ||
            val > 2147483647
          ) {
            issues.push({
              field: `operation_payload.checkpoint_coordinates[${i}]`,
              message: "Coordinate must be a 32-bit signed integer.",
            });
            break;
          }
        }
      }
      break;
    }
    case "MATERIALIZE_DATASET": {
      const payload =
        draft.operation_payload as Partial<MaterializeDatasetPayload>;
      if (payload.cache_key !== undefined && payload.cache_key.length > 0) {
        if (!IDENTIFIER_PATTERN.test(payload.cache_key)) {
          issues.push({
            field: "operation_payload.cache_key",
            message: "cache_key must match ^[A-Za-z0-9_-]+$ (max 64 chars).",
          });
        } else if (payload.cache_key.length > 64) {
          issues.push({
            field: "operation_payload.cache_key",
            message: "cache_key must not exceed 64 characters.",
          });
        }
      }
      break;
    }
  }

  return issues;
}

export function buildExecutionIntentDocument(
  draft: ExecutionIntentDraft,
  options?: {
    readonly intentId?: string;
    readonly createdAt?: string;
    readonly expiresAt?: string;
  },
): {
  readonly document: ExecutionIntentDocument;
  readonly canonicalJson: string;
  readonly issues: readonly IntentValidationIssue[];
} {
  const issues = validateIntentDraft(draft);

  const createdAtDate = options?.createdAt ? new Date(options.createdAt) : new Date();
  const expiresAtDate = options?.expiresAt
    ? new Date(options.expiresAt)
    : new Date(createdAtDate.getTime() + 10 * 60 * 1000);

  const createdAt = createdAtDate.toISOString();
  const expiresAt = expiresAtDate.toISOString();
  const intentId =
    options?.intentId ??
    (typeof globalThis.crypto?.randomUUID === "function"
      ? globalThis.crypto.randomUUID()
      : "10000000-0000-4000-8000-000000000001");

  // Clean operation payload according to operation
  let operationPayload: OperationPayload;
  if (draft.operation === "TRAIN_TICKET") {
    const p = draft.operation_payload as TrainTicketPayload;
    operationPayload = {
      ticket_id: p.ticket_id,
      partition_id: p.partition_id,
    };
  } else if (draft.operation === "EVALUATE_CHECKPOINT") {
    const p = draft.operation_payload as EvaluateCheckpointPayload;
    operationPayload = {
      checkpoint_coordinates: [...p.checkpoint_coordinates],
    };
  } else {
    const p = draft.operation_payload as MaterializeDatasetPayload;
    operationPayload = p.cache_key ? { cache_key: p.cache_key } : {};
  }

  const executionConstraints: ExecutionConstraints = {
    timeout_seconds: draft.execution_constraints.timeout_seconds,
    requested_allow_downloads: draft.execution_constraints.requested_allow_downloads,
    ...(draft.execution_constraints.retry_of_intent_id
      ? { retry_of_intent_id: draft.execution_constraints.retry_of_intent_id }
      : {}),
  };

  const intentWithoutDigest: Omit<ExecutionIntentDocument, "intent_digest"> = {
    schema_version: "1.0.0",
    intent_id: intentId,
    created_at: createdAt,
    expires_at: expiresAt,
    declared_operator: {
      role: draft.declared_operator.role,
      subject_id: draft.declared_operator.subject_id,
    },
    workload: {
      model_plugin_id: draft.workload.model_plugin_id,
      dataset_id: draft.workload.dataset_id,
      requested_scope: draft.workload.requested_scope,
      catalog_backend_ref: draft.workload.catalog_backend_ref,
    },
    operation: draft.operation,
    operation_payload: operationPayload,
    execution_constraints: executionConstraints,
  };

  const intentDigest = computeIntentDigestSync(
    intentWithoutDigest as Record<string, unknown>,
  );

  const document: ExecutionIntentDocument = {
    ...intentWithoutDigest,
    intent_digest: intentDigest,
  };

  const canonicalJson = jcsCanonicalize(document);

  return {
    document,
    canonicalJson,
    issues,
  };
}
