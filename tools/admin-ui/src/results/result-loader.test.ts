import { describe, expect, it, vi } from "vitest";

import type {
  SourceDescriptor,
  SourcedResult,
  SubjectReference,
} from "../core/contracts";
import { AdminUiError } from "../core/errors";
import type { DataSourcePort } from "../data/data-source-port";
import { querySourcedResults } from "./result-loader";

const subject: SubjectReference = {
  type: "controller-register",
  id: "register-1",
  revision: "rev-1",
};

const readySource: SourceDescriptor = {
  adapterId: "fixture-results",
  label: "Fixture results",
  authorityClass: "GOVERNANCE_ASSESSMENT",
  connectionState: "LOCAL_READY",
  entityTypes: ["controller"],
  capabilities: ["governance.controller-independence.read"],
  retrievedAt: "2026-09-14T08:00:00Z",
};

function validResult(resultSubject: SubjectReference = subject): SourcedResult {
  return {
    resultType: "controller-independence",
    outcome: "PASS",
    subject: resultSubject,
    authorityClass: "GOVERNANCE_ASSESSMENT",
    sourceReference: {
      kind: "PUBLIC_CONTRACT",
      repository: "governance/example",
      revision: "assessment-1",
      sha256: "a".repeat(64),
    },
    issuedAt: "2026-09-14T07:00:00Z",
    retrievedAt: "2026-09-14T08:00:00Z",
  };
}

function port(
  source: SourceDescriptor,
  listSourcedResults: DataSourcePort["listSourcedResults"],
): DataSourcePort {
  return {
    describeSource: async () => source,
    listSourcedResults,
    listSchemas: async () => [],
    loadSchema: async () => {
      throw new Error("not used");
    },
    openDocument: async () => {
      throw new Error("not used");
    },
    validateStructure: async () => {
      throw new Error("not used");
    },
    exportDocument: async () => {
      throw new Error("not used");
    },
  };
}

describe("sourced result state matrix", () => {
  it("reports unavailable when the source does not declare the capability", async () => {
    const list = vi.fn(async () => [validResult()]);
    const query = await querySourcedResults(
      port({ ...readySource, capabilities: [] }, list),
      "governance.controller-independence.read",
      subject,
    );
    expect(query).toEqual({ state: "UNAVAILABLE", results: [] });
    expect(list).not.toHaveBeenCalled();
  });

  it("reports unsupported when an advertised operation rejects as unsupported", async () => {
    const query = await querySourcedResults(
      port(readySource, async () => {
        throw new AdminUiError(
          "OPERATION_UNSUPPORTED",
          "The fixture operation is unsupported.",
        );
      }),
      "governance.controller-independence.read",
      subject,
    );
    expect(query.state).toBe("UNSUPPORTED");
    expect(query.results).toEqual([]);
  });

  it("retains valid sourced results while marking stale source data", async () => {
    const query = await querySourcedResults(
      port({ ...readySource, connectionState: "STALE" }, async () => [validResult()]),
      "governance.controller-independence.read",
      subject,
    );
    expect(query.state).toBe("STALE");
    expect(query.results).toHaveLength(1);
    expect(query.results[0].authorityClass).toBe("GOVERNANCE_ASSESSMENT");
  });

  it("maps a malformed advertised response to an error without displaying it", async () => {
    const malformed = [{ resultType: "controller-independence", outcome: "PASS" }];
    const query = await querySourcedResults(
      port(
        readySource,
        async () => malformed as unknown as readonly SourcedResult[],
      ),
      "governance.controller-independence.read",
      subject,
    );
    expect(query.state).toBe("ERROR");
    expect(query.results).toEqual([]);
    expect(query.error?.code).toBe("CAPABILITY_CONTRACT_VIOLATED");
  });

  it("rejects a valid-looking result bound to another subject", async () => {
    const query = await querySourcedResults(
      port(readySource, async () => [
        validResult({ ...subject, id: "register-other" }),
      ]),
      "governance.controller-independence.read",
      subject,
    );
    expect(query.state).toBe("INVALID");
    expect(query.results).toEqual([]);
    expect(query.error?.code).toBe("SUBJECT_PROVENANCE_MISMATCH");
  });
});
