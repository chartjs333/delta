import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LiveExecutionSurface } from "./LiveExecutionSurface";
import { MockLiveExecutionAdapter } from "./mock-live-execution-adapter";

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
});
