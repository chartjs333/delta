import type { ErrorObject, ValidateFunction } from "ajv";

import type {
  DocumentEnvelope,
  JsonValue,
  SchemaAuthorityClass,
  SchemaDescriptor,
  SchemaEnvelope,
  StructuralValidationIssue,
  StructuralValidationResult,
} from "../core/contracts";
import { AdminUiError } from "../core/errors";
import { CONTROLLER_REGISTER_SCHEMA } from "../schemas/controller-register";
import { validateControllerRegister } from "./generated/controller-register-validator.mjs";

const GOVERNANCE_REGISTER = "CONTROLLER_GOVERNANCE_REGISTER";
const BOOTSTRAP_VALIDATOR_SET =
  "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET";

const allowedSchemaAuthorities: Readonly<
  Record<string, readonly SchemaAuthorityClass[]>
> = {
  [GOVERNANCE_REGISTER]: ["GOVERNANCE_DOCUMENT", "LOCAL_FIXTURE"],
  [BOOTSTRAP_VALIDATOR_SET]: ["DELTA_CANONICAL"],
};

function objectRecord(value: JsonValue): Readonly<Record<string, JsonValue>> | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Readonly<Record<string, JsonValue>>)
    : undefined;
}

export function inferDocumentType(value: JsonValue): string | undefined {
  const rawType = objectRecord(value)?.document_type;
  if (rawType === "CAMPAIGN02_CONTROLLER_APPOINTMENT_WORKSHEET") {
    return GOVERNANCE_REGISTER;
  }
  return typeof rawType === "string" ? rawType : undefined;
}

export function assertSchemaDocumentMatch(
  document: DocumentEnvelope,
  descriptor: SchemaDescriptor,
): void {
  const documentType = document.documentType ?? inferDocumentType(document.value);
  if (!documentType || documentType !== descriptor.documentType) {
    throw new AdminUiError(
      "SCHEMA_DESCRIPTOR_MISMATCH",
      "The selected schema document type does not match the open document.",
      {
        field: "documentType",
        expected: documentType ?? "DECLARED_DOCUMENT_TYPE",
        actual: descriptor.documentType,
      },
    );
  }

  const allowedAuthorities = allowedSchemaAuthorities[documentType];
  if (
    allowedAuthorities &&
    !allowedAuthorities.includes(descriptor.authorityClass)
  ) {
    throw new AdminUiError(
      "SCHEMA_DESCRIPTOR_MISMATCH",
      "The selected schema authority does not match this document type.",
      {
        field: "authorityClass",
        expected: allowedAuthorities.join("|"),
        actual: descriptor.authorityClass,
      },
    );
  }
}

export function assertNoExternalSchemaReferences(schema: JsonValue): void {
  const stack: JsonValue[] = [schema];
  while (stack.length > 0) {
    const current = stack.pop();
    if (current === undefined || current === null || typeof current !== "object") {
      continue;
    }
    if (Array.isArray(current)) {
      stack.push(...current);
      continue;
    }
    for (const [key, value] of Object.entries(current)) {
      if (
        (key === "$ref" || key === "$dynamicRef") &&
        typeof value === "string" &&
        !value.startsWith("#")
      ) {
        throw new AdminUiError(
          "SCHEMA_DESCRIPTOR_MISMATCH",
          "External schema references are disabled in the browser-local MVP.",
          { field: key, expected: "LOCAL_FRAGMENT_REFERENCE" },
        );
      }
      stack.push(value);
    }
  }
}

function issueFromAjv(error: ErrorObject): StructuralValidationIssue {
  return {
    instancePath: error.instancePath || "",
    schemaPath: error.schemaPath,
    constraint: error.keyword,
    message: error.message ?? "Schema constraint was not satisfied.",
    params: error.params as Readonly<Record<string, JsonValue>>,
  };
}

export class StructuralValidator {
  validate(
    document: DocumentEnvelope,
    schema: SchemaEnvelope,
  ): StructuralValidationResult {
    assertSchemaDocumentMatch(document, schema.descriptor);
    assertNoExternalSchemaReferences(schema.value);
    if (!objectRecord(schema.value)) {
      throw new AdminUiError(
        "CAPABILITY_CONTRACT_VIOLATED",
        "The selected schema root must be a JSON object.",
      );
    }

    const validate = standaloneValidatorFor(schema.descriptor);

    const valid = validate(document.value);
    return {
      authorityClass: "STRUCTURAL_VALIDATION",
      status: valid ? "VALID" : "INVALID",
      schema: schema.descriptor,
      issues: valid ? [] : (validate.errors ?? []).map(issueFromAjv),
    };
  }
}

function standaloneValidatorFor(descriptor: SchemaDescriptor): ValidateFunction {
  if (
    descriptor.schemaId === CONTROLLER_REGISTER_SCHEMA.schemaId &&
    descriptor.version === CONTROLLER_REGISTER_SCHEMA.version &&
    descriptor.authorityClass === CONTROLLER_REGISTER_SCHEMA.authorityClass &&
    descriptor.documentType === CONTROLLER_REGISTER_SCHEMA.documentType &&
    descriptor.source.sha256 === CONTROLLER_REGISTER_SCHEMA.source.sha256
  ) {
    return validateControllerRegister;
  }
  throw new AdminUiError(
    "CAPABILITY_CONTRACT_VIOLATED",
    "No CSP-safe standalone validator is bundled for the selected schema.",
  );
}
