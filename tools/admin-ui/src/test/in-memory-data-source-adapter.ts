import type {
  Capability,
  DocumentEnvelope,
  ExportReceipt,
  SchemaDescriptor,
  SchemaEnvelope,
  SourceDescriptor,
  SourcedResult,
  StructuralValidationResult,
  SubjectReference,
} from "../core/contracts";
import { AdminUiError } from "../core/errors";
import { parseUntrustedJson } from "../security/input-guards";
import { StructuralValidator } from "../validation/structural-validator";
import type { DataSourcePort } from "../data/data-source-port";

export interface CapturedExport {
  readonly bytes: Uint8Array;
  readonly fileName: string;
}

export interface InMemoryDataSourceOptions {
  readonly document: DocumentEnvelope;
  readonly schema: SchemaEnvelope;
  readonly source?: SourceDescriptor;
  readonly sourcedResults?: readonly SourcedResult[];
}

const BASE_CAPABILITIES: readonly Capability[] = [
  "document.read",
  "document.export",
  "schema.enumerate",
  "schema.validate.structure",
];

/**
 * Test-only substitute for transport-backed adapters. It deliberately implements
 * DataSourcePort without browser files, network calls, or Delta runtime types.
 */
export class InMemoryDataSourceAdapter implements DataSourcePort {
  readonly exports: CapturedExport[] = [];
  private readonly validator = new StructuralValidator();
  private readonly source: SourceDescriptor;
  private controllerListAvailable = false;

  constructor(private readonly options: InMemoryDataSourceOptions) {
    this.source = options.source ?? {
      adapterId: "in-memory-test",
      label: "In-memory test source",
      authorityClass: "LOCAL_DRAFT",
      connectionState: "LOCAL_READY",
      entityTypes: ["controller"],
      capabilities: BASE_CAPABILITIES,
    };
  }

  async describeSource(): Promise<SourceDescriptor> {
    const capabilities = this.controllerListAvailable
      ? Array.from(new Set([...this.source.capabilities, "controller.list" as const]))
      : this.source.capabilities;
    return { ...this.source, capabilities };
  }

  async listSchemas(): Promise<readonly SchemaDescriptor[]> {
    return [this.options.schema.descriptor];
  }

  async loadSchema(descriptor: SchemaDescriptor): Promise<SchemaEnvelope> {
    if (!sameDescriptor(descriptor, this.options.schema.descriptor)) {
      throw new AdminUiError(
        "SCHEMA_DESCRIPTOR_MISMATCH",
        "The requested in-memory schema does not match its source binding.",
      );
    }
    return this.options.schema;
  }

  async openDocument(): Promise<DocumentEnvelope> {
    this.controllerListAvailable = false;
    return this.options.document;
  }

  async validateStructure(
    document: DocumentEnvelope,
    schema: SchemaDescriptor,
  ): Promise<StructuralValidationResult> {
    const schemaEnvelope = await this.loadSchema(schema);
    const result = this.validator.validate(document, schemaEnvelope);
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
    this.exports.push({ bytes: bytes.slice(), fileName });
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
    const canReadResults = this.source.capabilities.some((capability) =>
      capability.endsWith(".read") && capability !== "document.read",
    );
    if (!canReadResults) {
      throw new AdminUiError(
        "OPERATION_UNSUPPORTED",
        "The in-memory source does not advertise sourced results.",
      );
    }
    return this.options.sourcedResults ?? [];
  }
}

function sameDescriptor(left: SchemaDescriptor, right: SchemaDescriptor): boolean {
  return (
    left.schemaId === right.schemaId &&
    left.version === right.version &&
    left.authorityClass === right.authorityClass &&
    left.documentType === right.documentType &&
    left.source.kind === right.source.kind &&
    left.source.repository === right.source.repository &&
    left.source.revision === right.source.revision &&
    left.source.path === right.source.path &&
    left.source.gitBlobSha === right.source.gitBlobSha &&
    left.source.sha256 === right.source.sha256
  );
}

function exportedFileName(suggestedName: string): string {
  const leaf = suggestedName.split(/[\\/]/u).at(-1) ?? "delta-document";
  const safe = leaf.replace(/[^a-z0-9._-]+/giu, "-").replace(/^-+|-+$/gu, "");
  const base = safe.replace(/(?:\.export)?\.json$/iu, "") || "delta-document";
  return `${base}.export.json`;
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const copy = bytes.slice();
  const digest = await globalThis.crypto.subtle.digest("SHA-256", copy.buffer);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
