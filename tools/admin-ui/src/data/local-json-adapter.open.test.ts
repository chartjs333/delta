import { describe, expect, it } from "vitest";

import type {
  LocalFileGateway,
  SelectedLocalFile,
} from "./browser-file-gateway";
import { LocalJsonAdapter } from "./local-json-adapter";

class MemoryFileGateway implements LocalFileGateway {
  constructor(private readonly selected: SelectedLocalFile) {}

  async selectJsonFile(): Promise<SelectedLocalFile> {
    return this.selected;
  }

  async downloadNewFile(): Promise<void> {
    throw new Error("download is not part of open/create");
  }
}

describe("LocalJsonAdapter open/create", () => {
  it("opens only the JSON bytes explicitly selected by the user", async () => {
    const text = '{"document_type":"CONTROLLER_GOVERNANCE_REGISTER","controllers":[]}';
    const adapter = new LocalJsonAdapter(
      new MemoryFileGateway({
        name: "register.json",
        bytes: new TextEncoder().encode(text),
      }),
    );

    const opened = await adapter.openDocument();
    expect(opened.text).toBe(text);
    expect(opened.origin).toEqual({
      kind: "USER_SELECTED_LOCAL",
      displayName: "register.json",
      byteLength: text.length,
    });
    expect(opened.authorityClass).toBe("LOCAL_DRAFT");
  });

  it("creates a new empty, dynamic controller-register draft locally", () => {
    const adapter = new LocalJsonAdapter(
      new MemoryFileGateway({ name: "unused.json", bytes: new Uint8Array() }),
    );
    const created = adapter.createDocument();

    expect(created.origin.kind).toBe("NEW_LOCAL_DRAFT");
    expect(created.value).toMatchObject({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      controllers: [],
    });
    expect(created.text).toContain('"controllers": []');
  });
});
