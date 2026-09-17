import { describe, expect, it } from "vitest";

import goldenVectorsDoc from "../../../../../specs/admin-ui/step5c-controlled-live-execution/contracts/vectors/jcs-golden-vectors.json";
import {
  buildExecutionIntentDocument,
  createDefaultIntentDraft,
  validateIntentDraft,
  type ExecutionIntentDraft,
} from "./intent-builder";

describe("ExecutionIntent Builder & Validation", () => {
  it("builds a default TRAIN_TICKET intent matching catalog and golden vector digest", () => {
    const draft = createDefaultIntentDraft("TRAIN_TICKET");
    expect(draft.operation).toBe("TRAIN_TICKET");
    expect(draft.workload.requested_scope).toBe("PLUGIN_BOUNDARY");

    // Match golden vector options
    const result = buildExecutionIntentDocument(draft, {
      intentId: "11111111-1111-4111-8111-111111111111",
      createdAt: "2026-09-17T14:30:00.000Z",
      expiresAt: "2026-09-17T14:40:00.000Z",
    });

    expect(result.issues).toEqual([]);
    expect(result.document.schema_version).toBe("1.0.0");
    expect(result.document.intent_id).toBe("11111111-1111-4111-8111-111111111111");
    expect(result.document.declared_operator.role).toBe("OPERATOR");
    expect(result.document.declared_operator.subject_id).toBe("operator.alpha");
    expect(result.document.workload.model_plugin_id).toBe("tabular-10gene-phenotype-v1");
    expect(result.document.workload.dataset_id).toBe("synthetic-10gene-cohort-v1");
    expect(result.document.workload.catalog_backend_ref).toBe(
      "670b58f6458fe84620f4f9f46401f855d04ae05d",
    );
    expect(result.document.intent_digest).toBe(
      "sha256:fdd94b40e97a0383e1d8fbf33b3fcd13ab04149f11b30d6e40caa1ae562415a9",
    );
  });

  it("matches exact golden vector when retry_of_intent_id is set", () => {
    const draft: ExecutionIntentDraft = {
      ...createDefaultIntentDraft("TRAIN_TICKET"),
      execution_constraints: {
        timeout_seconds: 900,
        requested_allow_downloads: false,
        retry_of_intent_id: "00000000-0000-4000-8000-000000000001",
      },
    };

    const result = buildExecutionIntentDocument(draft, {
      intentId: "11111111-1111-4111-8111-111111111111",
      createdAt: "2026-09-17T14:30:00.000Z",
      expiresAt: "2026-09-17T14:40:00.000Z",
    });

    const goldenVector = goldenVectorsDoc.vectors.find(
      (v) => v.name === "execution-intent-train-ticket-without-digest",
    );
    expect(goldenVector).toBeDefined();
    expect(result.document.intent_digest).toBe(goldenVector?.sha256);
  });

  it("builds a valid EVALUATE_CHECKPOINT intent", () => {
    const draft = createDefaultIntentDraft("EVALUATE_CHECKPOINT");
    const result = buildExecutionIntentDocument(draft);

    expect(result.issues).toEqual([]);
    expect(result.document.operation).toBe("EVALUATE_CHECKPOINT");
    expect(result.document.operation_payload).toHaveProperty(
      "checkpoint_coordinates",
    );
    expect(result.document.intent_digest).toMatch(/^sha256:[0-9a-f]{64}$/u);
  });

  it("builds a valid MATERIALIZE_DATASET intent", () => {
    const draft = createDefaultIntentDraft("MATERIALIZE_DATASET");
    const result = buildExecutionIntentDocument(draft);

    expect(result.issues).toEqual([]);
    expect(result.document.operation).toBe("MATERIALIZE_DATASET");
    expect(result.document.intent_digest).toMatch(/^sha256:[0-9a-f]{64}$/u);
  });

  it("rejects TRAIN_TICKET with MODEL_DATASET_BINDING_ONLY scope", () => {
    const draft: ExecutionIntentDraft = {
      ...createDefaultIntentDraft("TRAIN_TICKET"),
      workload: {
        ...createDefaultIntentDraft("TRAIN_TICKET").workload,
        requested_scope: "MODEL_DATASET_BINDING_ONLY",
      },
    };

    const issues = validateIntentDraft(draft);
    expect(issues.map((i) => i.message)).toContain(
      "TRAIN_TICKET operation requires scope 'PLUGIN_BOUNDARY'.",
    );
  });

  it("rejects invalid ticket or partition pattern", () => {
    const draft: ExecutionIntentDraft = {
      ...createDefaultIntentDraft("TRAIN_TICKET"),
      operation_payload: {
        ticket_id: "invalid ticket with spaces",
        partition_id: "partition@bad",
      },
    };

    const issues = validateIntentDraft(draft);
    expect(issues.some((i) => i.field.includes("ticket_id"))).toBe(true);
    expect(issues.some((i) => i.field.includes("partition_id"))).toBe(true);
  });

  it("rejects out-of-range timeout_seconds", () => {
    const draft: ExecutionIntentDraft = {
      ...createDefaultIntentDraft("TRAIN_TICKET"),
      execution_constraints: {
        timeout_seconds: 0,
        requested_allow_downloads: false,
      },
    };

    const issues = validateIntentDraft(draft);
    expect(issues.some((i) => i.field.includes("timeout_seconds"))).toBe(true);
  });

  it("rejects unknown model plugin not in catalog", () => {
    const draft: ExecutionIntentDraft = {
      ...createDefaultIntentDraft("TRAIN_TICKET"),
      workload: {
        ...createDefaultIntentDraft("TRAIN_TICKET").workload,
        model_plugin_id: "unknown-plugin-99",
      },
    };

    const issues = validateIntentDraft(draft);
    expect(issues.some((i) => i.field.includes("model_plugin_id"))).toBe(true);
  });
});
