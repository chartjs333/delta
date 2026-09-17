import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { JsonValue } from "../../core/contracts";
import type { LocalFileGateway } from "../../data/browser-file-gateway";
import {
  CONTROLLER_REGISTER_SCHEMA,
  LocalJsonAdapter,
} from "../../data/local-json-adapter";
import { parseUntrustedJson } from "../../security/input-guards";
import frozenWorksheetText from "../../../test-data/pr29/campaign02-controller-register.template.json?raw";
import { ControllerExplorer } from "./ControllerExplorer";
import { controllersFromDocument } from "./controller-model";

const unusedFiles: LocalFileGateway = {
  selectJsonFile: async () => {
    throw new Error("not used");
  },
  downloadNewFile: async () => {
    throw new Error("not used");
  },
};

function register(count: number): JsonValue {
  return {
    document_type: "CONTROLLER_GOVERNANCE_REGISTER",
    document_version: "1.0.0",
    controllers: Array.from({ length: count }, (_, index) => ({
      controller_id: `controller-${index + 1}`,
      status: "LOCAL_DRAFT",
    })),
  };
}

describe("controller document acceptance matrix", () => {
  it.each([0, 1, 4, 101])(
    "validates and extracts a dynamic collection of %i controllers",
    async (count) => {
      const adapter = new LocalJsonAdapter(unusedFiles);
      const draft = adapter.createDocument(register(count));
      const result = await adapter.validateStructure(
        draft,
        CONTROLLER_REGISTER_SCHEMA,
      );

      expect(result.status).toBe("VALID");
      expect(controllersFromDocument(draft.value)).toHaveLength(count);
      expect((await adapter.describeSource()).capabilities).toContain(
        "controller.list",
      );
    },
  );

  it("does not render every controller in a 100+ collection", () => {
    const controllers = controllersFromDocument(register(101));
    render(<ControllerExplorer controllers={controllers} />);
    expect(
      within(screen.getByRole("list", { name: "Controller list" })).getAllByRole(
        "button",
      ),
    ).toHaveLength(25);
    expect(screen.getByText("Page 1 of 5")).toBeTruthy();
  });

  it("returns a precise path and constraint for an invalid controller", async () => {
    const adapter = new LocalJsonAdapter(unusedFiles);
    const draft = adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      controllers: [{ controller_id: { unexpected: true } }],
    });
    const result = await adapter.validateStructure(
      draft,
      CONTROLLER_REGISTER_SCHEMA,
    );
    expect(result).toMatchObject({
      status: "INVALID",
      issues: [
        expect.objectContaining({
          instancePath: "/controllers/0/controller_id",
          constraint: "type",
        }),
      ],
    });
  });

  it("accepts and preserves forward-compatible fields allowed by the schema", async () => {
    const adapter = new LocalJsonAdapter(unusedFiles);
    const draft = adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      future_revision_hint: { edition: 2 },
      controllers: [
        {
          controller_id: "controller-future",
          future_controller_field: ["opaque", 42],
        },
      ],
    });
    const result = await adapter.validateStructure(
      draft,
      CONTROLLER_REGISTER_SCHEMA,
    );
    expect(result.status).toBe("VALID");
    expect(JSON.parse(draft.text)).toMatchObject({
      future_revision_hint: { edition: 2 },
      controllers: [{ future_controller_field: ["opaque", 42] }],
    });
  });

  it("validates the exact frozen PR #29 worksheet only as a LOCAL_FIXTURE", async () => {
    const adapter = new LocalJsonAdapter(unusedFiles);
    const parsed = parseUntrustedJson(new TextEncoder().encode(frozenWorksheetText));
    const worksheet = {
      ...parsed,
      documentType: "CONTROLLER_GOVERNANCE_REGISTER",
      authorityClass: "LOCAL_DRAFT" as const,
      origin: {
        kind: "BUNDLED_FIXTURE" as const,
        displayName: "campaign02-controller-register.template.json",
        byteLength: new TextEncoder().encode(frozenWorksheetText).byteLength,
      },
    };
    const result = await adapter.validateStructure(
      worksheet,
      CONTROLLER_REGISTER_SCHEMA,
    );

    expect(result.status).toBe("VALID");
    expect(result.schema.authorityClass).toBe("LOCAL_FIXTURE");
    expect(controllersFromDocument(worksheet.value)).toHaveLength(4);
  });
});
