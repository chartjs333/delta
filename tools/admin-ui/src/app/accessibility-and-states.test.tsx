import axe from "axe-core";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { CapabilityStateView } from "../components/CapabilityStateView";
import type { LocalFileGateway } from "../data/browser-file-gateway";
import { LocalJsonAdapter } from "../data/local-json-adapter";
import { SourcedResultsPanel } from "../results/SourcedResultsPanel";
import { App } from "./App";

const memoryFiles: LocalFileGateway = {
  selectJsonFile: async () => {
    throw new Error("not used");
  },
  downloadNewFile: async () => {
    throw new Error("not used");
  },
};

async function expectNoAutomatableAccessibilityViolations(
  container: HTMLElement,
): Promise<void> {
  const report = await axe.run(container, {
    rules: {
      // jsdom has no layout/canvas implementation; visual contrast remains a
      // browser/manual gate while every DOM-semantic rule still runs here.
      "color-contrast": { enabled: false },
    },
  });
  expect(report.violations).toEqual([]);
}

describe("accessibility and primary states", () => {
  it("passes automated DOM accessibility checks before and after document creation", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <App adapter={new LocalJsonAdapter(memoryFiles)} />,
    );
    await screen.findByText("Local JSON");
    await expectNoAutomatableAccessibilityViolations(container);

    await user.click(screen.getByRole("button", { name: "New document" }));
    await expectNoAutomatableAccessibilityViolations(container);
  });

  it("keeps primary navigation and actions keyboard reachable with names", async () => {
    const user = userEvent.setup();
    render(<App adapter={new LocalJsonAdapter(memoryFiles)} />);
    await screen.findByText("Local JSON");

    const expectedTabOrder = [
      screen.getByRole("link", { name: "Delta Admin UI home" }),
      screen.getByRole("button", { name: "Menu" }),
      screen.getByRole("link", { name: /Controllers/u }),
      screen.getByRole("link", { name: /Campaigns/u }),
      screen.getByRole("link", { name: /Workloads/u }),
      screen.getByRole("button", { name: "Open JSON" }),
      screen.getByRole("button", { name: "New document" }),
    ];

    for (const control of expectedTabOrder) {
      await user.tab();
      expect(document.activeElement).toBe(control);
    }
  });

  it.each([
    ["loading", <CapabilityStateView capability="campaign.read" state="LOADING" />, "status", /Loading/u],
    ["empty", <SourcedResultsPanel query={{ state: "EMPTY", results: [] }} />, "status", /No sourced results/u],
    ["invalid", <SourcedResultsPanel query={{ state: "INVALID", results: [] }} />, "alert", /Result rejected: subject/u],
    ["error", <SourcedResultsPanel query={{ state: "ERROR", results: [] }} />, "alert", /source response is malformed/u],
    ["degraded", <CapabilityStateView capability="campaign.read" state="DEGRADED" />, "status", /Degraded:/u],
    ["stale", <SourcedResultsPanel query={{ state: "STALE", results: [] }} />, "status", /Stale sourced data/u],
    ["unsupported", <SourcedResultsPanel query={{ state: "UNSUPPORTED", results: [] }} />, "status", /Unsupported:/u],
    ["access denied", <CapabilityStateView capability="campaign.read" state="ACCESS_DENIED" />, "status", /Access denied/u],
  ] as const)(
    "exposes the %s state with a semantic %s",
    (_state, component, role, message) => {
      render(component);
      const status = screen.getByRole(role);
      expect(status.textContent).toMatch(message);
      expect(status.textContent).not.toMatch(/\b(?:PASS|FAIL)\b/u);
    },
  );
});
