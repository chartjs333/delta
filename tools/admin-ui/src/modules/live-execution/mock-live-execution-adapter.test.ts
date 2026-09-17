import { describe, expect, it } from "vitest";

import { MockLiveExecutionAdapter } from "./mock-live-execution-adapter";

describe("MockLiveExecutionAdapter", () => {
  it("describes a mock-only live boundary with no transport profile", async () => {
    const adapter = new MockLiveExecutionAdapter();
    const source = await adapter.describeLiveSource();

    expect(source).toMatchObject({
      adapterId: "mock-live-execution",
      mode: "MOCK_ONLY",
      transportProfile: "NONE_PHASE_4",
      contractFreezeSha: "66e3e7e5bb07a48aadbee8d9c4683144b812d229",
    });
    expect(source.capabilities).toEqual([
      "live.intent.preview",
      "live.status.mock",
    ]);
  });

  it("covers every Step 5C product state without claiming controller authority", async () => {
    const adapter = new MockLiveExecutionAdapter();
    const statuses = await adapter.listStatuses();

    expect(statuses.map((status) => status.state)).toEqual([
      "DRAFT",
      "REJECTED",
      "ADMITTED",
      "QUEUED",
      "RUNNING",
      "COMPLETED",
      "FAILED",
      "TIMED_OUT",
      "CANCELLED",
      "STALE_UNAVAILABLE",
    ]);
    expect(statuses.every((status) => status.authority === "PRESENTATION_MOCK"))
      .toBe(true);
    expect(statuses.map((status) => status.trustBadge)).toContain(
      "UNATTESTED_PLUGIN_BOUNDARY_RECORD",
    );
  });

  it("returns defensive status copies", async () => {
    const adapter = new MockLiveExecutionAdapter();
    const status = await adapter.getStatus("completed");

    expect(status.state).toBe("COMPLETED");
    expect(status.lineage.intentDigest).toMatch(/^sha256:/u);
    expect(status).not.toBe(await adapter.getStatus("completed"));
  });

  it("admits submitted intent and prepends new mock execution status", async () => {
    const adapter = new MockLiveExecutionAdapter();
    const beforeCount = (await adapter.listStatuses()).length;

    const mockIntent = {
      schema_version: "1.0.0",
      intent_id: "99999999-9999-4999-8999-999999999999",
      created_at: "2026-09-17T12:00:00.000Z",
      expires_at: "2026-09-17T12:10:00.000Z",
      operation: "TRAIN_TICKET",
      declared_operator: { role: "OPERATOR", subject_id: "operator.beta" },
      workload: {
        model_plugin_id: "tabular-10gene-phenotype-v1",
        dataset_id: "synthetic-10gene-cohort-v1",
        requested_scope: "PLUGIN_BOUNDARY",
        catalog_backend_ref: "670b58f6458fe84620f4f9f46401f855d04ae05d",
      },
      operation_payload: {
        ticket_id: "ticket_test_01",
        partition_id: "part_01",
      },
      execution_constraints: {
        timeout_seconds: 600,
        requested_allow_downloads: false,
      },
      intent_digest: "sha256:9999999999999999999999999999999999999999999999999999999999999999",
    };

    const status = await adapter.submitIntent(mockIntent);
    expect(status.state).toBe("ADMITTED");
    expect(status.lineage.intentId).toBe("99999999-9999-4999-8999-999999999999");
    expect(status.lineage.intentDigest).toBe(
      "sha256:9999999999999999999999999999999999999999999999999999999999999999",
    );

    const statusesAfter = await adapter.listStatuses();
    expect(statusesAfter.length).toBe(beforeCount + 1);
    expect(statusesAfter[0].statusId).toBe(status.statusId);
  });
});
