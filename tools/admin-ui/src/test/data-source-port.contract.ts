import { createHash } from "node:crypto";

import { describe, expect, it } from "vitest";

import type { DataSourcePort } from "../data/data-source-port";

export type DataSourcePortFactory = () => DataSourcePort;

/** The same behavioral contract is invoked unchanged for every adapter. */
export function runDataSourcePortContract(
  adapterName: string,
  createAdapter: DataSourcePortFactory,
): void {
  describe(`${adapterName} DataSourcePort contract`, () => {
    it("describes a local-ready source and opens the equivalent document", async () => {
      const adapter = createAdapter();
      const source = await adapter.describeSource();
      const document = await adapter.openDocument();

      expect(source.connectionState).toBe("LOCAL_READY");
      expect(source.authorityClass).toBe("LOCAL_DRAFT");
      expect(source.capabilities).toEqual(
        expect.arrayContaining([
          "document.read",
          "document.export",
          "schema.enumerate",
          "schema.validate.structure",
        ]),
      );
      expect(document.authorityClass).toBe("LOCAL_DRAFT");
      expect(document.documentType).toBe("CONTROLLER_GOVERNANCE_REGISTER");
      expect(document.value).toMatchObject({
        controllers: [{ controller_id: "contract-controller" }],
      });
    });

    it("loads the exact authority-bound schema and rejects substitution", async () => {
      const adapter = createAdapter();
      const [descriptor] = await adapter.listSchemas();
      expect(descriptor).toMatchObject({
        version: "1.0.0",
        authorityClass: "LOCAL_FIXTURE",
        documentType: "CONTROLLER_GOVERNANCE_REGISTER",
      });
      expect(descriptor.source.sha256).toMatch(/^[a-f0-9]{64}$/u);
      const loaded = await adapter.loadSchema(descriptor);
      expect(
        createHash("sha256").update(loaded.text, "utf8").digest("hex"),
      ).toBe(descriptor.source.sha256);

      await expect(
        adapter.loadSchema({
          ...descriptor,
          authorityClass: "DELTA_CANONICAL",
        }),
      ).rejects.toMatchObject({ code: "SCHEMA_DESCRIPTOR_MISMATCH" });
    });

    it("performs structural validation and exposes controller.list only after success", async () => {
      const adapter = createAdapter();
      expect((await adapter.describeSource()).capabilities).not.toContain(
        "controller.list",
      );
      const [descriptor] = await adapter.listSchemas();
      const document = await adapter.openDocument();
      const result = await adapter.validateStructure(document, descriptor);

      expect(result).toMatchObject({
        authorityClass: "STRUCTURAL_VALIDATION",
        status: "VALID",
        issues: [],
      });
      expect((await adapter.describeSource()).capabilities).toContain(
        "controller.list",
      );
    });

    it("exports a distinct file only on invocation and reports sourced results unsupported", async () => {
      const adapter = createAdapter();
      const document = await adapter.openDocument();
      const receipt = await adapter.exportDocument(document, "contract-register.json");

      expect(receipt).toEqual({
        fileName: "contract-register.export.json",
        byteLength: new TextEncoder().encode(document.text).byteLength,
        sha256: createHash("sha256").update(document.text).digest("hex"),
        triggeredByUser: true,
        destination: "NEW_DOWNLOAD",
      });
      await expect(
        adapter.listSourcedResults({
          type: "CONTROLLER_GOVERNANCE_REGISTER",
          id: "contract-register.json",
        }),
      ).rejects.toMatchObject({ code: "OPERATION_UNSUPPORTED" });
    });
  });
}
