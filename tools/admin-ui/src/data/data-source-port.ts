import type {
  DocumentEnvelope,
  ExportReceipt,
  SchemaDescriptor,
  SchemaEnvelope,
  SourceDescriptor,
  SourcedResult,
  StructuralValidationResult,
  SubjectReference,
} from "../core/contracts";

/**
 * The only data boundary visible to domain modules. Implementations may adapt
 * local files or future public APIs, but views never depend on either transport.
 */
export interface DataSourcePort {
  describeSource(): Promise<SourceDescriptor>;
  listSchemas(): Promise<readonly SchemaDescriptor[]>;
  loadSchema(descriptor: SchemaDescriptor): Promise<SchemaEnvelope>;
  openDocument(): Promise<DocumentEnvelope>;
  validateStructure(
    document: DocumentEnvelope,
    schema: SchemaDescriptor,
  ): Promise<StructuralValidationResult>;
  exportDocument(
    document: DocumentEnvelope,
    suggestedName: string,
  ): Promise<ExportReceipt>;
  listSourcedResults(subject: SubjectReference): Promise<readonly SourcedResult[]>;
}
