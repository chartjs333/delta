import Ajv2020, {
  type AnySchemaObject,
  type ErrorObject,
  type ValidateFunction,
} from "ajv/dist/2020.js";

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
  private readonly compiled = new Map<string, ValidateFunction>();

  validate(
    document: DocumentEnvelope,
    schema: SchemaEnvelope,
  ): StructuralValidationResult {
    assertSchemaDocumentMatch(document, schema.descriptor);
    assertNoExternalSchemaReferences(schema.value);
    const schemaObject = objectRecord(schema.value);
    if (!schemaObject) {
      throw new AdminUiError(
        "CAPABILITY_CONTRACT_VIOLATED",
        "The selected schema root must be a JSON object.",
      );
    }

    const cacheKey = `${schema.descriptor.schemaId}@${schema.descriptor.version}:${schema.descriptor.source.sha256}`;
    let validate = this.compiled.get(cacheKey);
    if (!validate) {
      try {
        const ajv = new Ajv2020({
          allErrors: true,
          strict: true,
          validateFormats: false,
        });
        validate = ajv.compile(schemaObject as AnySchemaObject);
      } catch {
        throw new AdminUiError(
          "CAPABILITY_CONTRACT_VIOLATED",
          "The selected schema could not be compiled safely.",
        );
      }
      this.compiled.set(cacheKey, validate);
    }

    const valid = validate(document.value);
    return {
      authorityClass: "STRUCTURAL_VALIDATION",
      status: valid ? "VALID" : "INVALID",
      schema: schema.descriptor,
      issues: valid ? [] : (validate.errors ?? []).map(issueFromAjv),
    };
  }
}
