import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LiveExecutionSurface } from "./LiveExecutionSurface";
import type {
  LiveExecutionPort,
  LiveExecutionReceipt,
  LiveExecutionStatus,
} from "./live-execution-port";
import { MockLiveExecutionAdapter } from "./mock-live-execution-adapter";

const LIVE_EXECUTION_ID = "55555555-5555-4555-8555-555555555555";

function liveStatus(state: LiveExecutionStatus["state"]): LiveExecutionStatus {
  return {
    statusId: LIVE_EXECUTION_ID,
    state,
    operation: "TRAIN_TICKET",
    updatedAt: "2026-09-20T08:00:00.000Z",
    terminal: state === "COMPLETED" || state === "CANCELLED",
    authority: "CONTROLLER_HTTP_STATUS",
    trustBadge: "UNATTESTED_CONTROLLER_STATUS",
    summary: `Controller HTTP status is ${state}. This is not a consensus claim.`,
    lineage: {
      intentId: "11111111-1111-4111-8111-111111111111",
      intentDigest: `sha256:${"1".repeat(64)}`,
      admissionId: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      admissionDigest: `sha256:${"2".repeat(64)}`,
      executionId: LIVE_EXECUTION_ID,
    },
  };
}

function livePort(initialState: LiveExecutionStatus["state"]): LiveExecutionPort {
  let current = liveStatus(initialState);
  return {
    describeLiveSource: async () => ({
      adapterId: "test-http-live",
      label: "Test same-origin Controller",
      mode: "HTTP_LIVE",
      transportProfile: "HTTP_SAME_ORIGIN_LOOPBACK",
      capabilities: [
        "live.intent.preview",
        "live.intent.submit",
        "live.status.read",
        "live.receipt.read",
        "live.execution.cancel",
      ],
      contractFreezeSha: "66e3e7e5bb07a48aadbee8d9c4683144b812d229",
    }),
    previewDraft: async (operation, workload) => ({
      state: "DRAFT",
      operation,
      workload,
      digestState: "COMPUTED_INFORMATIONAL",
      authority: "PRESENTATION_MOCK",
    }),
    listStatuses: async () => [current],
    getStatus: vi.fn(async () => current),
    submitIntent: vi.fn(async () => current),
    cancelExecution: vi.fn(async () => {
      current = liveStatus("CANCELLED");
      return current;
    }),
    getReceipt: vi.fn(async () =>
      ({
        schema_version: "1.0.0",
        receipt_type: "DELTAREDUCE_EXECUTION_RECEIPT",
        provenance: {
          repository: "chartjs333/delta",
          backend_commit: "670b58f6458fe84620f4f9f46401f855d04ae05d",
          producer_commit: "c3de2e17cc304c9558030ddb2b8f0d5f34157155",
          produced_at: "2026-09-20T08:00:00.000Z",
          intent_id: "11111111-1111-4111-8111-111111111111",
          intent_digest: `sha256:${"1".repeat(64)}`,
          admission_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          admission_digest: `sha256:${"2".repeat(64)}`,
          execution_id: LIVE_EXECUTION_ID,
        },
        workload: {
          model_plugin_id: "tabular-10gene-phenotype-v1",
          dataset_id: "synthetic-10gene-cohort-v1",
          executed_scope: "PLUGIN_BOUNDARY",
          workload_config_digest: `sha256:${"3".repeat(64)}`,
        },
        execution: { verdict: "SUCCESS", terminal_status: "COMPLETED" },
      }) as LiveExecutionReceipt,
    ),
  };
}

describe("LiveExecutionSurface", () => {
  it("renders mock-only status state without execution authority language", async () => {
    render(<LiveExecutionSurface />);

    expect(
      await screen.findByRole("heading", { name: "Live execution" }),
    ).toBeTruthy();
    expect(screen.getByText("MOCK ONLY")).toBeTruthy();
    expect(screen.getByText("NONE_PHASE_4")).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/STAGE_C_REAL_DRQ1/u);
    expect(document.body.textContent).not.toMatch(/Authorization granted/iu);
  });

  it("shows completed lineage as unattested plugin boundary status", async () => {
    const user = userEvent.setup();
    render(<LiveExecutionSurface />);

    await user.click(await screen.findByRole("button", { name: /Completed/u }));
    const detail = screen
      .getByRole("heading", { name: "Completed" })
      .closest("section");

    expect(detail).toBeTruthy();
    expect(
      within(detail as HTMLElement).getByText("UNATTESTED_PLUGIN_BOUNDARY_RECORD"),
    ).toBeTruthy();
    expect(
      within(detail as HTMLElement).getByText(
        "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      ),
    ).toBeTruthy();
  });

  it("navigates through all 10 product states explicitly", async () => {
    const user = userEvent.setup();
    render(<LiveExecutionSurface />);

    const expectedStates = [
      { name: /Draft/u, badge: "UNATTESTED_MOCK_STATUS" },
      { name: /Rejected/u, badge: "UNATTESTED_MOCK_STATUS" },
      { name: /Admitted/u, badge: "UNATTESTED_MOCK_STATUS" },
      { name: /Queued/u, badge: "UNATTESTED_MOCK_STATUS" },
      { name: /Running/u, badge: "UNATTESTED_MOCK_STATUS" },
      { name: /Completed/u, badge: "UNATTESTED_PLUGIN_BOUNDARY_RECORD" },
      { name: /Failed/u, badge: "UNATTESTED_MOCK_STATUS" },
      { name: /Timed out/u, badge: "UNATTESTED_MOCK_STATUS" },
      { name: /Cancelled/u, badge: "UNATTESTED_MOCK_STATUS" },
      { name: /Stale\/unavailable/u, badge: "UNATTESTED_MOCK_STATUS" },
    ];

    for (const { name, badge } of expectedStates) {
      const button = await screen.findByRole("button", { name });
      await user.click(button);
      expect(screen.getByText(badge)).toBeTruthy();
    }
  });

  it("switches to Intent Builder tab and drafts a canonical TRAIN_TICKET intent", async () => {
    const user = userEvent.setup();
    render(<LiveExecutionSurface initialTab="BUILDER" />);

    expect(
      await screen.findByRole("heading", { name: "ExecutionIntent builder" }),
    ).toBeTruthy();
    expect(screen.getByText("INFORMATIONAL ONLY")).toBeTruthy();

    // Check default digest preview is visible and has sha256 prefix
    const digestEl = screen.getByText(/^sha256:[0-9a-f]{64}$/u);
    expect(digestEl).toBeTruthy();

    // Change ticket ID
    const ticketInput = screen.getByLabelText("Ticket ID");
    await user.clear(ticketInput);
    await user.type(ticketInput, "ticket_B-9999");

    // Digest should update
    expect(screen.getByText(/^sha256:[0-9a-f]{64}$/u)).toBeTruthy();

    // View canonical JSON
    const jsonToggle = screen.getByRole("button", {
      name: "View Canonical JSON",
    });
    await user.click(jsonToggle);
    expect(screen.getByText(/RFC 8785 Canonical JSON/u)).toBeTruthy();
    expect(screen.getByText(/ticket_B-9999/u)).toBeTruthy();
  });

  it("locks requested scope to PLUGIN_BOUNDARY for TRAIN_TICKET and enforces it in form", async () => {
    render(<LiveExecutionSurface initialTab="BUILDER" />);

    const scopeSelect = screen.getByLabelText("Requested scope") as HTMLSelectElement;
    expect(scopeSelect.disabled).toBe(true);
    expect(scopeSelect.value).toBe("PLUGIN_BOUNDARY");
    expect(
      screen.getByText("TRAIN_TICKET requires scope ‘PLUGIN_BOUNDARY’."),
    ).toBeTruthy();
  });

  it("allows switching operations to EVALUATE_CHECKPOINT and unlocks scope", async () => {
    const user = userEvent.setup();
    render(<LiveExecutionSurface initialTab="BUILDER" />);

    const evalRadio = screen.getByLabelText("EVALUATE_CHECKPOINT");
    await user.click(evalRadio);

    expect(
      screen.getByLabelText("Checkpoint coordinates (integers)"),
    ).toBeTruthy();

    const scopeSelect = screen.getByLabelText("Requested scope") as HTMLSelectElement;
    expect(scopeSelect.disabled).toBe(false);
  });

  it("submits drafted intent to mock gate and switches to status list", async () => {
    const user = userEvent.setup();
    const adapter = new MockLiveExecutionAdapter();
    const submitSpy = vi.spyOn(adapter, "submitIntent");

    render(<LiveExecutionSurface port={adapter} initialTab="BUILDER" />);

    const submitButton = screen.getByRole("button", {
      name: "Submit to Mock Gate",
    });
    await user.click(submitButton);

    expect(submitSpy).toHaveBeenCalledOnce();
    expect(
      await screen.findByText(/Intent submitted to mock gate/u),
    ).toBeTruthy();

    // Check we switched back to statuses view
    expect(
      screen.getByRole("heading", { name: "Product states" }),
    ).toBeTruthy();
  });

  it("supports local export of canonical intent without network calls", async () => {
    const user = userEvent.setup();
    render(<LiveExecutionSurface initialTab="BUILDER" />);

    // Mock createObjectURL & revokeObjectURL
    const createObjectURL = vi.fn().mockReturnValue("blob:mock-url");
    const revokeObjectURL = vi.fn();
    window.URL.createObjectURL = createObjectURL;
    window.URL.revokeObjectURL = revokeObjectURL;

    const exportBtn = screen.getByRole("button", {
      name: "Export Intent JSON",
    });
    await user.click(exportBtn);

    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledOnce();
    expect(screen.getByText(/Exported intent-.*\.json locally\./u)).toBeTruthy();
  });

  it("marks the real HTTP mode as unattested and exposes refresh and cancel actions", async () => {
    const user = userEvent.setup();
    const port = livePort("RUNNING");
    render(<LiveExecutionSurface port={port} />);

    expect(await screen.findByText("HTTP LIVE")).toBeTruthy();
    expect(screen.getByText("UNATTESTED_CONTROLLER_STATUS")).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/Consensus verified/iu);

    await user.click(screen.getByRole("button", { name: "Refresh status" }));
    expect(port.getStatus).toHaveBeenCalledWith(LIVE_EXECUTION_ID);

    await user.click(screen.getByRole("button", { name: "Cancel execution" }));
    expect(port.cancelExecution).toHaveBeenCalledWith(LIVE_EXECUTION_ID);
    expect(await screen.findByRole("heading", { name: "Cancelled" })).toBeTruthy();
  });

  it("loads a completed live receipt and labels it as non-consensus", async () => {
    const user = userEvent.setup();
    const port = livePort("COMPLETED");
    render(<LiveExecutionSurface port={port} />);

    await user.click(
      await screen.findByRole("button", { name: "Load terminal receipt" }),
    );
    expect(port.getReceipt).toHaveBeenCalledWith(LIVE_EXECUTION_ID);
    expect(
      screen.getByRole("heading", { name: "Terminal receipt" }),
    ).toBeTruthy();
    expect(screen.getByText("UNATTESTED PLUGIN RECORD")).toBeTruthy();
    expect(screen.getByText(/not a consensus certificate/iu)).toBeTruthy();
  });
});
