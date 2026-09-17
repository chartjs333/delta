import { describe, expect, it, vi } from "vitest";

import type { LocalFileGateway } from "../data/browser-file-gateway";
import { LocalJsonAdapter } from "../data/local-json-adapter";
import { querySourcedResults } from "./result-loader";

const unusedFiles: LocalFileGateway = {
  selectJsonFile: async () => {
    throw new Error("not used");
  },
  downloadNewFile: async () => {
    throw new Error("not used");
  },
};

describe("local result-looking fields", () => {
  it("never promotes arbitrary PASS strings to a sourced verdict", async () => {
    const adapter = new LocalJsonAdapter(unusedFiles);
    const draft = adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      controllers: [],
      independence_assessment: "PASS",
      signing_readiness: { outcome: "PASS" },
      protocol_result: "PASS",
    });
    const resultMethod = vi.spyOn(adapter, "listSourcedResults");

    expect(draft.text.match(/PASS/gu)).toHaveLength(3);
    const query = await querySourcedResults(
      adapter,
      "governance.controller-independence.read",
      { type: "document", id: "local-draft" },
    );

    expect(query).toEqual({ state: "UNAVAILABLE", results: [] });
    expect(resultMethod).not.toHaveBeenCalled();
  });
});
