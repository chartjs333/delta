import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { LiveExecutionSurface } from "./LiveExecutionSurface";

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
});
