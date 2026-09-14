import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  DocumentEnvelope,
  JsonValue,
  SchemaAuthorityClass,
  SchemaEnvelope,
} from "../core/contracts";
import { AdminUiError } from "../core/errors";
import {
  CONTROLLER_REGISTER_SCHEMA,
  controllerRegisterSchemaText,
} from "../schemas/controller-register";
import { StructuralValidator } from "./structural-validator";

const sha256 = "0".repeat(64);

function document(value: JsonValue, documentType?: string): DocumentEnvelope {
  return {
    text: JSON.stringify(value),
    value,
    documentType,
    authorityClass: "LOCAL_DRAFT",
    origin: {
      kind: "USER_SELECTED_LOCAL",
      displayName: "untrusted.json",
      byteLength: JSON.stringify(value).length,
    },
  };
}

function schema(
  documentType: string,
  authorityClass: SchemaAuthorityClass,
  value: JsonValue = { type: "object" },
): SchemaEnvelope {
  return {
    descriptor: {
      schemaId: `urn:test:${documentType}`,
      version: "1.0.0",
      authorityClass,
      documentType,
      source: { kind: "BUNDLED_FIXTURE", sha256 },
    },
    text: JSON.stringify(value),
    value,
  };
}

function expectMismatch(action: () => unknown): void {
  try {
    action();
    throw new Error("Expected mismatch");
  } catch (error) {
    expect(error).toBeInstanceOf(AdminUiError);
    expect((error as AdminUiError).code).toBe("SCHEMA_DESCRIPTOR_MISMATCH");
  }
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("schema authority and document-type separation", () => {
  it("rejects the PR #29 worksheet against the canonical bootstrap schema", () => {
    const validator = new StructuralValidator();
    const worksheet = document({
      document_type: "CAMPAIGN02_CONTROLLER_APPOINTMENT_WORKSHEET",
      controllers: [],
    });
    expectMismatch(() =>
      validator.validate(
        worksheet,
        schema(
          "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET",
          "DELTA_CANONICAL",
        ),
      ),
    );
  });

  it("rejects a bootstrap validator set against a governance fixture schema", () => {
    const validator = new StructuralValidator();
    const bootstrap = document({
      document_type: "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET",
      validators: [],
    });
    expectMismatch(() =>
      validator.validate(
        bootstrap,
        schema("CONTROLLER_GOVERNANCE_REGISTER", "LOCAL_FIXTURE"),
      ),
    );
  });

  it("rejects a Delta-canonical authority label for a governance schema", () => {
    const validator = new StructuralValidator();
    const register = document(
      { document_type: "CONTROLLER_GOVERNANCE_REGISTER", controllers: [] },
      "CONTROLLER_GOVERNANCE_REGISTER",
    );
    expectMismatch(() =>
      validator.validate(
        register,
        schema("CONTROLLER_GOVERNANCE_REGISTER", "DELTA_CANONICAL"),
      ),
    );
  });
});

describe("local-only schema references", () => {
  it("rejects external refs before compilation and never calls fetch", () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const validator = new StructuralValidator();
    const register = document(
      { document_type: "CONTROLLER_GOVERNANCE_REGISTER", controllers: [] },
      "CONTROLLER_GOVERNANCE_REGISTER",
    );
    const external = schema("CONTROLLER_GOVERNANCE_REGISTER", "LOCAL_FIXTURE", {
      $ref: "https://schemas.example.test/controller.json",
    });

    expectMismatch(() => validator.validate(register, external));
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("allows internal fragment refs without network resolution", () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const validator = new StructuralValidator();
    const register = document(
      {
        document_type: "CONTROLLER_GOVERNANCE_REGISTER",
        document_version: "1.0.0",
        controllers: [],
      },
      "CONTROLLER_GOVERNANCE_REGISTER",
    );
    const local: SchemaEnvelope = {
      descriptor: CONTROLLER_REGISTER_SCHEMA,
      text: controllerRegisterSchemaText,
      value: JSON.parse(controllerRegisterSchemaText) as JsonValue,
    };

    expect(validator.validate(register, local).status).toBe("VALID");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("validates with the Function constructor blocked by CSP", () => {
    vi.stubGlobal(
      "Function",
      function blockedFunctionConstructor() {
        throw new Error("unsafe-eval blocked");
      },
    );
    const validator = new StructuralValidator();
    const register = document(
      {
        document_type: "CONTROLLER_GOVERNANCE_REGISTER",
        document_version: "1.0.0",
        controllers: [],
      },
      "CONTROLLER_GOVERNANCE_REGISTER",
    );
    const local: SchemaEnvelope = {
      descriptor: CONTROLLER_REGISTER_SCHEMA,
      text: controllerRegisterSchemaText,
      value: JSON.parse(controllerRegisterSchemaText) as JsonValue,
    };

    expect(validator.validate(register, local).status).toBe("VALID");
  });
});
