import type {
  Capability,
  DocumentEnvelope,
  ExportReceipt,
  JsonValue,
  SchemaDescriptor,
  SchemaEnvelope,
  SourceDescriptor,
  SourcedResult,
  StructuralValidationResult,
  SubjectReference,
} from "../core/contracts";
import { AdminUiError } from "../core/errors";
import { editDocumentText } from "../editor/document-draft";
import {
  CONTROLLER_REGISTER_SCHEMA,
  controllerRegisterSchemaText,
} from "../schemas/controller-register";
import { parseUntrustedJson } from "../security/input-guards";
import type { LocalFileGateway } from "./browser-file-gateway";
import type { DataSourcePort } from "./data-source-port";
import {
  inferDocumentType,
  StructuralValidator,
} from "../validation/structural-validator";

const INITIAL_CAPABILITIES: readonly Capability[] = [
  "document.read",
  "document.export",
  "schema.enumerate",
  "schema.validate.structure",
];

export { CONTROLLER_REGISTER_SCHEMA };

export class LocalJsonAdapter implements DataSourcePort {
  private readonly structuralValidator = new StructuralValidator();
  private controllerListAvailable = false;

  constructor(private readonly files: LocalFileGateway) {}

  async describeSource(): Promise<SourceDescriptor> {
    return {
      adapterId: "local-json",
      label: "Local JSON",
      authorityClass: "LOCAL_DRAFT",
      connectionState: "LOCAL_READY",
      entityTypes: ["controller"],
      capabilities: this.controllerListAvailable
        ? [...INITIAL_CAPABILITIES, "controller.list"]
        : INITIAL_CAPABILITIES,
    };
  }

  async openDocument(): Promise<DocumentEnvelope> {
    const selected = await this.files.selectJsonFile();
    const parsed = parseUntrustedJson(selected.bytes);
    const envelope: DocumentEnvelope = {
      ...parsed,
      documentType: inferDocumentType(parsed.value),
      authorityClass: "LOCAL_DRAFT",
      origin: {
        kind: "USER_SELECTED_LOCAL",
        displayName: selected.name,
        byteLength: selected.bytes.byteLength,
      },
    };
    this.controllerListAvailable = false;
    return envelope;
  }

  createDocument(value: JsonValue = defaultControllerRegister()): DocumentEnvelope {
    this.controllerListAvailable = false;
    const text = `${JSON.stringify(value, null, 2)}\n`;
    return {
      text,
      value,
      documentType: "CONTROLLER_GOVERNANCE_REGISTER",
      authorityClass: "LOCAL_DRAFT",
      origin: {
        kind: "NEW_LOCAL_DRAFT",
        displayName: "controller-register.new.json",
        byteLength: new TextEncoder().encode(text).byteLength,
      },
    };
  }

  updateDocumentText(
    previous: DocumentEnvelope,
    text: string,
  ): DocumentEnvelope {
    this.controllerListAvailable = false;
    return editDocumentText(previous, text);
  }

  async listSchemas(): Promise<readonly SchemaDescriptor[]> {
    return [CONTROLLER_REGISTER_SCHEMA];
  }

  async loadSchema(descriptor: SchemaDescriptor): Promise<SchemaEnvelope> {
    if (descriptor.schemaId !== CONTROLLER_REGISTER_SCHEMA.schemaId) {
      throw new AdminUiError("SCHEMA_NOT_FOUND", "The selected schema was not found.");
    }
    if (descriptor.version !== CONTROLLER_REGISTER_SCHEMA.version) {
      throw new AdminUiError(
        "SCHEMA_VERSION_UNSUPPORTED",
        "The selected schema version is unsupported.",
      );
    }
    if (!sameSchemaDescriptor(descriptor, CONTROLLER_REGISTER_SCHEMA)) {
      throw new AdminUiError(
        "SCHEMA_DESCRIPTOR_MISMATCH",
        "The selected schema descriptor does not match its frozen source.",
      );
    }
    const parsed = parseUntrustedJson(new TextEncoder().encode(controllerRegisterSchemaText));
    return {
      descriptor: CONTROLLER_REGISTER_SCHEMA,
      text: controllerRegisterSchemaText,
      value: parsed.value,
    };
  }

  async validateStructure(
    document: DocumentEnvelope,
    schema: SchemaDescriptor,
  ): Promise<StructuralValidationResult> {
    const schemaEnvelope = await this.loadSchema(schema);
    const result = this.structuralValidator.validate(document, schemaEnvelope);
    this.controllerListAvailable = result.status === "VALID";
    return result;
  }

  async exportDocument(
    document: DocumentEnvelope,
    suggestedName: string,
  ): Promise<ExportReceipt> {
    const bytes = new TextEncoder().encode(document.text);
    parseUntrustedJson(bytes);
    const fileName = exportedFileName(suggestedName);
    await this.files.downloadNewFile(bytes, fileName);
    return {
      fileName,
      byteLength: bytes.byteLength,
      sha256: await sha256Hex(bytes),
      triggeredByUser: true,
      destination: "NEW_DOWNLOAD",
    };
  }

  async listSourcedResults(
    _subject: SubjectReference,
  ): Promise<readonly SourcedResult[]> {
    throw unsupported("sourced results");
  }
}

function exportedFileName(suggestedName: string): string {
  const leaf = suggestedName.split(/[\\/]/u).at(-1) ?? "delta-document";
  const safe = leaf.replace(/[^a-z0-9._-]+/giu, "-").replace(/^-+|-+$/gu, "");
  const base = safe.replace(/(?:\.export)?\.json$/iu, "") || "delta-document";
  return `${base}.export.json`;
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", copy.buffer);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

export function schemaDescriptorKey(descriptor: SchemaDescriptor): string {
  return [
    descriptor.schemaId,
    descriptor.version,
    descriptor.authorityClass,
    descriptor.documentType,
    descriptor.source.sha256,
  ].join("|");
}

function sameSchemaDescriptor(
  left: SchemaDescriptor,
  right: SchemaDescriptor,
): boolean {
  return (
    schemaDescriptorKey(left) === schemaDescriptorKey(right) &&
    left.source.kind === right.source.kind &&
    left.source.repository === right.source.repository &&
    left.source.revision === right.source.revision &&
    left.source.path === right.source.path &&
    left.source.gitBlobSha === right.source.gitBlobSha
  );
}

function defaultControllerRegister(): JsonValue {
  return {
    document_type: "CONTROLLER_GOVERNANCE_REGISTER",
    document_version: "1.0.0",
    controllers: [],
  };
}

function unsupported(operation: string): AdminUiError {
  return new AdminUiError(
    "OPERATION_UNSUPPORTED",
    `The local adapter does not support ${operation} yet.`,
  );
}
