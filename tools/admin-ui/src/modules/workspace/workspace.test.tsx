import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { readWorkspace, WorkspaceProvider, type WorkspaceStorage, useWorkspace } from "./workspace-context";
import { CampaignWorkspace } from "./WorkspaceViews";
import { GuidedRun } from "../live-execution/GuidedRun";
import { createDefaultIntentDraft } from "../live-execution/intent-builder";
import { setLanguage, useLanguage } from "../../i18n";
import type { LiveExecutionPort, LiveExecutionStatus } from "../live-execution/live-execution-port";

function memoryStorage(): WorkspaceStorage {
  let data: unknown = null;
  let revision = 0;
  return { load: vi.fn(async () => ({ data, revision })), save: vi.fn(async (next, expected) => {
    if (expected !== revision) throw new Error("Conflict");
    data = structuredClone(next); return { revision: ++revision };
  }) };
}
function Setup() {
  useLanguage();
  const workspace = useWorkspace();
  return <><CampaignWorkspace /><output>{workspace?.workload.model_plugin_id}</output></>;
}
afterEach(() => { act(() => setLanguage("en")); });
describe("shared disk profile workflow", () => {
  it("restores campaigns after remount and keeps the same selections across languages", async () => {
    const user = userEvent.setup();
    const storage = memoryStorage();
    const view = render(<WorkspaceProvider storage={storage}><Setup /></WorkspaceProvider>);
    await user.type(await screen.findByLabelText("New campaign name"), "Morning presentation");
    await user.click(screen.getByRole("button", { name: "Create campaign" }));
    await screen.findByRole("option", { name: "Morning presentation" });
    view.unmount();
    render(<WorkspaceProvider storage={storage}><Setup /></WorkspaceProvider>);
    await screen.findByRole("option", { name: "Morning presentation" });
    act(() => setLanguage("ru"));
    expect((screen.getByLabelText("Текущая кампания") as HTMLSelectElement).selectedOptions[0].textContent).toBe("Morning presentation");
  });
  it("persists the actual submitted intent and execution ID in the selected campaign", async () => {
    const user = userEvent.setup();
    const storage = memoryStorage();
    const id = "55555555-5555-4555-8555-555555555555";
    const adapter: LiveExecutionPort = { describeLiveSource: vi.fn(), previewDraft: vi.fn(), listStatuses: vi.fn(),
      getStatus: vi.fn(), submitIntent: vi.fn(async (value: unknown) => {
        const intent = value as { intent_id: string; intent_digest: string };
        return { statusId: id, state: "FAILED", operation: "TRAIN_TICKET", updatedAt: new Date().toISOString(), terminal: true,
          authority: "CONTROLLER_HTTP_STATUS", trustBadge: "UNATTESTED_CONTROLLER_STATUS", summary: "failed",
          lineage: { executionId: id, intentId: intent.intent_id, intentDigest: intent.intent_digest } } as LiveExecutionStatus;
      }) };
    render(<WorkspaceProvider storage={storage}><GuidedRun port={adapter} enabled onStatus={() => {}} /></WorkspaceProvider>);
    await user.click(await screen.findByRole("button", { name: "Start training" }));
    await screen.findByText("Execution failed");
    const saved = readWorkspace(JSON.stringify((await storage.load()).data));
    expect(saved.runs).toHaveLength(1);
    expect(saved.runs[0].executionId).toBe(id);
    expect(saved.runs[0].campaignId).toBe(saved.activeCampaignId);
    expect(saved.runs[0].workload).toEqual(createDefaultIntentDraft("TRAIN_TICKET").workload);
    expect(screen.queryByRole("button", { name: "Download receipt" })).toBeNull();
  });
  it("does not submit when profile persistence fails", async () => {
    const user = userEvent.setup();
    const storage = memoryStorage(); storage.save = vi.fn(async () => { throw new Error("Conflict"); });
    const submit = vi.fn();
    const port = { submitIntent: submit } as unknown as LiveExecutionPort;
    render(<WorkspaceProvider storage={storage}><GuidedRun port={port} enabled onStatus={() => {}} /></WorkspaceProvider>);
    await user.click(await screen.findByRole("button", { name: "Start training" }));
    await screen.findByText("Unable to confirm the result");
    expect(submit).not.toHaveBeenCalled();
  });
  it("rejects corrupt profile data instead of asserting a saved result", () => {
    expect(() => readWorkspace('{"version":1}')).toThrow();
    const data = readWorkspace(null); data.runs = [{ executionId: "fake" } as never];
    expect(() => readWorkspace(JSON.stringify(data))).toThrow();
  });
});
