import { describe, expect, it } from "vitest";

import type {
  Capability,
  DocumentEnvelope,
  SchemaDescriptor,
  SourceDescriptor,
  SourcedResult,
} from "./contracts";

describe("admin UI contracts", () => {
  it("keeps local documents untrusted", () => {
    const document: DocumentEnvelope = {
      text: "{}",
      value: {},
      authorityClass: "LOCAL_DRAFT",
      origin: { kind: "NEW_LOCAL_DRAFT", displayName: "new.json", byteLength: 2 },
    };
    expect(document.authorityClass).toBe("LOCAL_DRAFT");
  });

  it("binds schemas to authority, document type, and immutable source", () => {
    const schema: SchemaDescriptor = {
      schemaId: "urn:test:schema",
      version: "1.0.0",
      authorityClass: "LOCAL_FIXTURE",
      documentType: "CONTROLLER_GOVERNANCE_REGISTER",
      source: { kind: "BUNDLED_FIXTURE", sha256: "0".repeat(64) },
    };
    expect(schema.source.sha256).toHaveLength(64);
  });

  it("keeps source capabilities explicit", () => {
    const capability: Capability = "schema.validate.structure";
    const source: SourceDescriptor = {
      adapterId: "local",
      label: "Local",
      authorityClass: "LOCAL_DRAFT",
      connectionState: "LOCAL_READY",
      entityTypes: ["controller"],
      capabilities: [capability],
    };
    expect(source.capabilities).toContain(capability);
  });

  it("requires sourced results to retain provenance", () => {
    const result: SourcedResult = {
      resultType: "review",
      outcome: "UNKNOWN",
      subject: { type: "register", id: "one" },
      authorityClass: "GOVERNANCE_ASSESSMENT",
      sourceReference: { kind: "PUBLIC_CONTRACT", sha256: "a".repeat(64) },
      retrievedAt: "2026-09-14T00:00:00Z",
    };
    expect(result.sourceReference.sha256).toHaveLength(64);
  });

  it("does not define a state-changing capability", () => {
    const capabilities: readonly Capability[] = ["document.read", "document.export"];
    expect(capabilities.some((value) => /write|sign|approve/u.test(value))).toBe(false);
  });
});
