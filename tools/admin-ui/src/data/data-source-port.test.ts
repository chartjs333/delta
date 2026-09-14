import { describe, expect, it } from "vitest";

import type { DataSourcePort } from "./data-source-port";

describe("DataSourcePort", () => {
  it("supports the complete MVP contract without exposing runtime internals", async () => {
    const adapter = {
      describeSource: async () => ({
        adapterId: "memory",
        label: "Memory fixture",
        authorityClass: "LOCAL_DRAFT" as const,
        connectionState: "LOCAL_READY" as const,
        entityTypes: ["controller"],
        capabilities: ["document.read" as const],
      }),
      listSchemas: async () => [],
      loadSchema: async () => {
        throw new Error("not used");
      },
      openDocument: async () => ({
        text: "{}",
        value: {},
        authorityClass: "LOCAL_DRAFT" as const,
        origin: {
          kind: "NEW_LOCAL_DRAFT" as const,
          displayName: "untitled.json",
          byteLength: 2,
        },
      }),
      validateStructure: async (_document: never, _schema: never) => {
        throw new Error("not used");
      },
      exportDocument: async (_document: never, _suggestedName: string) => {
        throw new Error("not used");
      },
      listSourcedResults: async () => [],
    } satisfies DataSourcePort;

    const source = await adapter.describeSource();
    const document = await adapter.openDocument();
    expect(source.adapterId).toBe("memory");
    expect(document.authorityClass).toBe("LOCAL_DRAFT");
    expect(await adapter.listSourcedResults()).toEqual([]);
  });
});
