import { createHash } from "node:crypto";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SchemaSelector } from "../components/SchemaSelector";
import type { LocalFileGateway } from "./browser-file-gateway";
import {
  CONTROLLER_REGISTER_SCHEMA,
  LocalJsonAdapter,
} from "./local-json-adapter";

const unusedFiles: LocalFileGateway = {
  selectJsonFile: async () => {
    throw new Error("not used");
  },
  downloadNewFile: async () => {
    throw new Error("not used");
  },
};

describe("authority-classed structural schema workflow", () => {
  it("lists and loads an exact digest-bound descriptor", async () => {
    const adapter = new LocalJsonAdapter(unusedFiles);
    const schemas = await adapter.listSchemas();
    expect(schemas).toEqual([CONTROLLER_REGISTER_SCHEMA]);

    const loaded = await adapter.loadSchema(schemas[0]);
    expect(loaded.descriptor).toBe(CONTROLLER_REGISTER_SCHEMA);
    expect(loaded.text).toContain('"additionalProperties": true');
    expect(createHash("sha256").update(loaded.text, "utf8").digest("hex")).toBe(
      CONTROLLER_REGISTER_SCHEMA.source.sha256,
    );
  });

  it("rejects descriptor authority substitution", async () => {
    const adapter = new LocalJsonAdapter(unusedFiles);
    const substituted = {
      ...CONTROLLER_REGISTER_SCHEMA,
      authorityClass: "DELTA_CANONICAL" as const,
    };
    await expect(adapter.loadSchema(substituted)).rejects.toMatchObject({
      code: "SCHEMA_DESCRIPTOR_MISMATCH",
    });
  });

  it("returns machine document paths and violated constraints", async () => {
    const adapter = new LocalJsonAdapter(unusedFiles);
    const invalid = adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      controllers: [{ controller_id: 42 }],
    });
    const result = await adapter.validateStructure(
      invalid,
      CONTROLLER_REGISTER_SCHEMA,
    );

    expect(result.status).toBe("INVALID");
    expect(result.issues).toContainEqual(
      expect.objectContaining({
        instancePath: "/controllers/0/controller_id",
        constraint: "type",
      }),
    );
  });

  it("renders every descriptor authority dimension in schema selection", () => {
    const onSelect = vi.fn();
    render(
      <SchemaSelector
        schemas={[CONTROLLER_REGISTER_SCHEMA]}
        selected={CONTROLLER_REGISTER_SCHEMA}
        onSelect={onSelect}
      />,
    );

    expect(screen.getByText("LOCAL_FIXTURE", { selector: "span" })).toBeTruthy();
    expect(
      screen.getByText("CONTROLLER_GOVERNANCE_REGISTER", { selector: "span" }),
    ).toBeTruthy();
    expect(screen.getByText(CONTROLLER_REGISTER_SCHEMA.source.sha256)).toBeTruthy();
  });
});
