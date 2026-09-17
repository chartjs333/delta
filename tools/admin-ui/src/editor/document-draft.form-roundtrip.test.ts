// @vitest-environment node

import { describe, expect, it } from "vitest";

import type { LocalFileGateway } from "../data/browser-file-gateway";
import { LocalJsonAdapter } from "../data/local-json-adapter";
import { patchDocumentAtPath } from "./document-draft";

describe("form patch round trip", () => {
  it("preserves unknown values and creates a new file only after explicit export", async () => {
    const downloads: { bytes: Uint8Array; name: string }[] = [];
    const gateway: LocalFileGateway = {
      selectJsonFile: async () => {
        throw new Error("not used");
      },
      downloadNewFile: async (bytes, name) => {
        downloads.push({ bytes, name });
      },
    };
    const adapter = new LocalJsonAdapter(gateway);
    const source = adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      controllers: [
        {
          controller_id: "controller-before",
          status: "DRAFT",
          future_controller_data: {
            flags: [true, false, null],
            exact_number: 17,
          },
        },
      ],
      future_root_data: {
        nested: { text: "preserve exactly as a JSON value" },
        list: [1, "two", { three: 3 }],
      },
    });
    const originalText = source.text;

    const edited = patchDocumentAtPath(
      source,
      ["controllers", 0, "controller_id"],
      "controller-after",
    );

    expect(source.text).toBe(originalText);
    expect(downloads).toEqual([]);
    expect(
      (edited.value as Record<string, unknown>).future_root_data,
    ).toEqual((source.value as Record<string, unknown>).future_root_data);
    expect(
      ((edited.value as { controllers: Record<string, unknown>[] }).controllers[0])
        .future_controller_data,
    ).toEqual(
      ((source.value as { controllers: Record<string, unknown>[] }).controllers[0])
        .future_controller_data,
    );

    const receipt = await adapter.exportDocument(edited, "source.json");
    expect(receipt.destination).toBe("NEW_DOWNLOAD");
    expect(receipt.triggeredByUser).toBe(true);
    expect(receipt.fileName).toBe("source.export.json");
    expect(downloads).toHaveLength(1);

    const exported = JSON.parse(new TextDecoder().decode(downloads[0].bytes)) as {
      controllers: Record<string, unknown>[];
      future_root_data: unknown;
    };
    expect(exported.future_root_data).toEqual(
      (source.value as Record<string, unknown>).future_root_data,
    );
    expect(exported.controllers[0].future_controller_data).toEqual(
      ((source.value as { controllers: Record<string, unknown>[] }).controllers[0])
        .future_controller_data,
    );
    expect(exported.controllers[0].controller_id).toBe("controller-after");
  });
});
