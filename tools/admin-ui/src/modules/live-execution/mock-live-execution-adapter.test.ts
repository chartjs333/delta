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
});
