// @vitest-environment node

import { createHash } from "node:crypto";

import { describe, expect, it } from "vitest";

import type { DocumentEnvelope, SchemaEnvelope } from "../core/contracts";
import type { DataSourcePort } from "../data/data-source-port";
import { CONTROLLER_REGISTER_SCHEMA } from "../data/local-json-adapter";
import schemaText from "../schemas/controller-register.schema.json?raw";
import { InMemoryDataSourceAdapter } from "./in-memory-data-source-adapter";

const documentText = `${JSON.stringify({
  document_type: "CONTROLLER_GOVERNANCE_REGISTER",
  document_version: "1.0.0",
  controllers: [{ controller_id: "memory-controller" }],
}, null, 2)}\n`;

const document: DocumentEnvelope = {
  text: documentText,
  value: JSON.parse(documentText),
  documentType: "CONTROLLER_GOVERNANCE_REGISTER",
  authorityClass: "LOCAL_DRAFT",
  origin: {
    kind: "BUNDLED_FIXTURE",
    displayName: "memory-register.json",
    byteLength: new TextEncoder().encode(documentText).byteLength,
  },
};

const schema: SchemaEnvelope = {
  descriptor: CONTROLLER_REGISTER_SCHEMA,
  text: schemaText,
  value: JSON.parse(schemaText),
};

describe("test-only in-memory DataSourcePort", () => {
  it("implements all DataSourcePort operations without files or transport", async () => {
    const adapter = new InMemoryDataSourceAdapter({ document, schema });
    const port: DataSourcePort = adapter;

    expect((await port.describeSource()).adapterId).toBe("in-memory-test");
    expect(await port.listSchemas()).toEqual([CONTROLLER_REGISTER_SCHEMA]);
    expect((await port.openDocument()).text).toBe(documentText);
    expect(
      (await port.validateStructure(document, CONTROLLER_REGISTER_SCHEMA)).status,
    ).toBe("VALID");
    expect((await port.describeSource()).capabilities).toContain("controller.list");

    const receipt = await port.exportDocument(document, "memory-register.json");
    expect(receipt.sha256).toBe(
      createHash("sha256").update(documentText).digest("hex"),
    );
    expect(adapter.exports).toHaveLength(1);
    await expect(port.listSourcedResults({ type: "controller", id: "one" }))
      .rejects.toMatchObject({ code: "OPERATION_UNSUPPORTED" });
  });

  it("rejects a substituted schema authority", async () => {
    const adapter = new InMemoryDataSourceAdapter({ document, schema });
    await expect(
      adapter.loadSchema({
        ...CONTROLLER_REGISTER_SCHEMA,
        authorityClass: "DELTA_CANONICAL",
      }),
    ).rejects.toMatchObject({ code: "SCHEMA_DESCRIPTOR_MISMATCH" });
  });
});
