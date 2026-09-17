import { describe, expect, it, vi } from "vitest";

import { MockLiveExecutionAdapter } from "./mock-live-execution-adapter";
import { buildExecutionIntentDocument, createDefaultIntentDraft } from "./intent-builder";

describe("Live Execution Offline & Zero-Egress Boundary", () => {
  it("executes intent building and mock operations with zero network calls", async () => {
    // Spy on global network methods
    const fetchSpy = vi.fn();
    (globalThis as unknown as Record<string, unknown>).fetch = fetchSpy;

    const draft = createDefaultIntentDraft("TRAIN_TICKET");
    const { document, canonicalJson } = buildExecutionIntentDocument(draft);

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(document.intent_digest).toMatch(/^sha256:[0-9a-f]{64}$/u);
    expect(canonicalJson).toContain(document.intent_id);

    const adapter = new MockLiveExecutionAdapter();
    const source = await adapter.describeLiveSource();
    expect(source.mode).toBe("MOCK_ONLY");
    expect(source.transportProfile).toBe("NONE_PHASE_4");

    const status = await adapter.submitIntent(document);
    expect(status.state).toBe("ADMITTED");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("fails closed on non-existent mock execution status without fallback", async () => {
    const adapter = new MockLiveExecutionAdapter();
    await expect(adapter.getStatus("non-existent-status-999")).rejects.toMatchObject({
      code: "SOURCE_UNAVAILABLE",
    });
  });

  it("preserves uninflated presentation authority across all statuses", async () => {
    const adapter = new MockLiveExecutionAdapter();
    const statuses = await adapter.listStatuses();

    for (const status of statuses) {
      expect(status.authority).toBe("PRESENTATION_MOCK");
      expect(status.trustBadge).toMatch(/^UNATTESTED_/u);
      expect(status.summary).not.toMatch(/Consensus verified/iu);
      expect(status.summary).not.toMatch(/Authorization granted/iu);
    }
  });
});
