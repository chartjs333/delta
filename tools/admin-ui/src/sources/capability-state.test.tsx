import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CapabilityStateView } from "../components/CapabilityStateView";
import type { SourceDescriptor } from "../core/contracts";
import type { DataSourcePort } from "../data/data-source-port";
import { discoverCapability } from "./capability-state";

function sourcePort(source: SourceDescriptor): DataSourcePort {
  return {
    describeSource: async () => source,
    listSchemas: async () => [],
    loadSchema: async () => {
      throw new Error("not used");
    },
    openDocument: async () => {
      throw new Error("not used");
    },
    validateStructure: async () => {
      throw new Error("not used");
    },
    exportDocument: async () => {
      throw new Error("not used");
    },
    listSourcedResults: async () => [],
  };
}

const localSource: SourceDescriptor = {
  adapterId: "local-json",
  label: "Local JSON",
  authorityClass: "LOCAL_DRAFT",
  connectionState: "LOCAL_READY",
  entityTypes: ["controller"],
  capabilities: ["document.read"],
};

describe("source capability discovery", () => {
  it("reports a missing assessment capability as unavailable", async () => {
    const discovery = await discoverCapability(
      sourcePort(localSource),
      "governance.controller-independence.read",
    );
    expect(discovery.state).toBe("UNAVAILABLE");

    render(
      <CapabilityStateView
        capability={discovery.capability}
        state={discovery.state}
      />,
    );
    const status = screen.getByRole("status");
    expect(status.textContent).toContain("Unavailable");
    expect(status.textContent).not.toMatch(/\b(?:PASS|FAIL)\b/u);
  });

  it.each([
    ["LOADING", "LOADING"],
    ["DEGRADED", "DEGRADED"],
    ["UNAVAILABLE", "DEGRADED"],
    ["STALE", "STALE"],
    ["ACCESS_DENIED", "ACCESS_DENIED"],
    ["LOCAL_READY", "AVAILABLE"],
  ] as const)("maps source state %s to %s", async (connectionState, expected) => {
    const discovery = await discoverCapability(
      sourcePort({
        ...localSource,
        connectionState,
        capabilities: ["governance.controller-independence.read"],
      }),
      "governance.controller-independence.read",
    );
    expect(discovery.state).toBe(expected);
  });
});
