// @vitest-environment node

import { createHash } from "node:crypto";

import { describe, expect, it } from "vitest";

import { editDocumentText } from "../editor/document-draft";
import type {
  LocalFileGateway,
  SelectedLocalFile,
} from "./browser-file-gateway";
import { LocalJsonAdapter } from "./local-json-adapter";

class RecordingFileGateway implements LocalFileGateway {
  readonly downloads: Array<{ bytes: Uint8Array; name: string }> = [];

  constructor(readonly source: SelectedLocalFile) {}

  async selectJsonFile(): Promise<SelectedLocalFile> {
    return { ...this.source, bytes: this.source.bytes.slice() };
  }

  async downloadNewFile(bytes: Uint8Array, suggestedName: string): Promise<void> {
    this.downloads.push({ bytes: bytes.slice(), name: suggestedName });
  }
}

describe("explicit new-file export", () => {
  it("preserves allowed unknown fields and never overwrites or autosaves the source", async () => {
    const sourceText = JSON.stringify({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      future_top_level: { keep: true },
      controllers: [
        {
          controller_id: "controller-1",
          status: "DRAFT",
          future_nested: ["keep", 7],
        },
      ],
    });
    const sourceBytes = new TextEncoder().encode(sourceText);
    const gateway = new RecordingFileGateway({
      name: "register.json",
      bytes: sourceBytes,
    });
    const adapter = new LocalJsonAdapter(gateway);
    const opened = await adapter.openDocument();
    const editedText = opened.text.replace('"DRAFT"', '"REVIEW"');
    const edited = editDocumentText(opened, editedText);

    expect(gateway.downloads).toHaveLength(0);
    expect(new TextDecoder().decode(gateway.source.bytes)).toBe(sourceText);

    const receipt = await adapter.exportDocument(edited, "register.json");
    expect(gateway.downloads).toHaveLength(1);
    expect(gateway.downloads[0].name).toBe("register.export.json");
    expect(new TextDecoder().decode(gateway.downloads[0].bytes)).toBe(editedText);
    expect(JSON.parse(editedText)).toMatchObject({
      future_top_level: { keep: true },
      controllers: [{ future_nested: ["keep", 7], status: "REVIEW" }],
    });
    expect(receipt).toEqual({
      fileName: "register.export.json",
      byteLength: new TextEncoder().encode(editedText).byteLength,
      sha256: createHash("sha256").update(editedText).digest("hex"),
      triggeredByUser: true,
      destination: "NEW_DOWNLOAD",
    });
    expect(new TextDecoder().decode(gateway.source.bytes)).toBe(sourceText);
  });

  it("sanitizes path-like suggestions into a distinct download name", async () => {
    const gateway = new RecordingFileGateway({
      name: "unused.json",
      bytes: new TextEncoder().encode("{}"),
    });
    const adapter = new LocalJsonAdapter(gateway);
    const draft = adapter.createDocument();
    const receipt = await adapter.exportDocument(draft, "../unsafe name.json");
    expect(receipt.fileName).toBe("unsafe-name.export.json");
  });
});
