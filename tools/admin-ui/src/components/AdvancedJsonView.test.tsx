import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LocalJsonAdapter } from "../data/local-json-adapter";
import type { LocalFileGateway } from "../data/browser-file-gateway";
import { patchDocumentAtPath } from "../editor/document-draft";
import { AdvancedJsonView } from "./AdvancedJsonView";

const unusedGateway: LocalFileGateway = {
  selectJsonFile: async () => {
    throw new Error("not used");
  },
  downloadNewFile: async () => {
    throw new Error("not used");
  },
};

describe("AdvancedJsonView", () => {
  it("is closed by default, read-only, and projects the current draft", () => {
    const adapter = new LocalJsonAdapter(unusedGateway);
    const draft = patchDocumentAtPath(
      adapter.createDocument(),
      ["document_version"],
      "2.0.0-local",
    );
    render(<AdvancedJsonView draft={draft} />);

    const details = screen.getByText("Advanced JSON (read-only)").closest("details");
    const projection = screen.getByLabelText(
      "Read-only JSON document",
    ) as HTMLTextAreaElement;
    expect(details?.hasAttribute("open")).toBe(false);
    expect(projection.readOnly).toBe(true);
    expect(projection.value).toContain('"document_version": "2.0.0-local"');
  });
});
