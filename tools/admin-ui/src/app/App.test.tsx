import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { LocalFileGateway } from "../data/browser-file-gateway";
import { LocalJsonAdapter } from "../data/local-json-adapter";
import { App } from "./App";

const memoryFiles: LocalFileGateway = {
  selectJsonFile: async () => {
    throw new Error("not used");
  },
  downloadNewFile: async () => {
    throw new Error("not used");
  },
};

describe("integrated browser-local MVP", () => {
  it("creates, edits, structurally validates, and presents a dynamic local register", async () => {
    const user = userEvent.setup();
    render(<App adapter={new LocalJsonAdapter(memoryFiles)} />);

    await user.click(screen.getByRole("button", { name: "New document" }));
    await user.click(screen.getByRole("button", { name: "Add controller" }));
    await user.type(
      screen.getByLabelText("Controller 1 Controller ID"),
      "controller-local",
    );

    await user.click(screen.getByRole("button", { name: "Validate structure" }));
    expect(await screen.findByRole("heading", { name: "VALID" })).toBeTruthy();
    expect(screen.getByText("controller-local")).toBeTruthy();

    const results = screen
      .getByRole("heading", { name: "Independence assessment" })
      .closest("section");
    expect(results).toBeTruthy();
    expect(within(results as HTMLElement).getByText(/Unavailable:/u)).toBeTruthy();
    expect((results as HTMLElement).textContent).not.toMatch(/\b(?:PASS|FAIL)\b/u);
  });

  it("keeps a structurally invalid form draft editable and reports the schema issue", async () => {
    const user = userEvent.setup();
    render(<App adapter={new LocalJsonAdapter(memoryFiles)} />);
    await user.click(screen.getByRole("button", { name: "New document" }));
    await user.clear(screen.getByLabelText("Document version"));
    await user.click(screen.getByRole("button", { name: "Validate structure" }));

    expect(await screen.findByRole("heading", { name: "INVALID" })).toBeTruthy();
    expect((screen.getByLabelText("Document version") as HTMLInputElement).value).toBe("");
    expect(
      (screen.getByRole("button", { name: "Download new file" }) as HTMLButtonElement)
        .disabled,
    ).toBe(false);
  });

  it("opens the registered campaign placeholder without a runtime fallback", async () => {
    const user = userEvent.setup();
    render(<App adapter={new LocalJsonAdapter(memoryFiles)} />);

    await user.click(screen.getByRole("link", { name: /Campaigns/u }));
    expect(
      screen.getByRole("heading", { name: "Campaigns" }),
    ).toBeTruthy();
    expect(screen.getByRole("status").textContent).toMatch(/Unavailable:/u);
    expect(window.location.hash).toBe("#/campaigns");
  });

  it("keeps primary navigation reachable through the mobile menu", async () => {
    const user = userEvent.setup();
    render(<App adapter={new LocalJsonAdapter(memoryFiles)} />);

    const toggle = screen.getByRole("button", { name: "Menu" });
    const sidebar = document.getElementById("primary-sidebar");
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(sidebar?.classList.contains("sidebar-open")).toBe(false);

    await user.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    expect(sidebar?.classList.contains("sidebar-open")).toBe(true);

    await user.click(screen.getByRole("link", { name: /Campaigns/u }));
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(sidebar?.classList.contains("sidebar-open")).toBe(false);
  });
});
