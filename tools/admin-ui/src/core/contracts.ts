export type JsonPrimitive = string | number | boolean | null;
export type JsonValue =
  | JsonPrimitive
  | readonly JsonValue[]
  | { readonly [key: string]: JsonValue };

export type SchemaAuthorityClass =
  | "GOVERNANCE_DOCUMENT"
  | "DELTA_CANONICAL"
  | "LOCAL_FIXTURE";

export type DataAuthorityClass =
  | "LOCAL_DRAFT"
  | "STRUCTURAL_VALIDATION"
  | "OBSERVATION"
  | "GOVERNANCE_ASSESSMENT"
  | "PROTOCOL_RESULT";

export type Capability =
  | "document.read"
  | "document.export"
  | "schema.enumerate"
  | "schema.validate.structure"
  | "controller.list"
  | "governance.controller-independence.read"
  | "governance.signing-readiness.read"
  | "protocol.validation-result.read"
  | "campaign.read"
  | "node.read"
  | "artifact.read"
  | "audit.read"
  | "events.subscribe";

export type SourceConnectionState =
  | "LOCAL_READY"
  | "LOADING"
  | "DEGRADED"
  | "STALE"
  | "UNAVAILABLE"
  | "ACCESS_DENIED";

export interface ImmutableSourceReference {
  readonly kind: "BUNDLED_FIXTURE" | "PUBLIC_CONTRACT" | "USER_SELECTED_LOCAL";
  readonly repository?: string;
  readonly revision?: string;
  readonly path?: string;
  readonly gitBlobSha?: string;
  readonly sha256: string;
}

export interface DocumentOrigin {
  readonly kind: "BUNDLED_FIXTURE" | "USER_SELECTED_LOCAL" | "NEW_LOCAL_DRAFT";
  readonly displayName: string;
  readonly byteLength: number;
  readonly sha256?: string;
}

export interface DocumentEnvelope {
  readonly text: string;
  readonly value: JsonValue;
  readonly documentType?: string;
  readonly authorityClass: "LOCAL_DRAFT";
  readonly origin: DocumentOrigin;
}

export interface SchemaDescriptor {
  readonly schemaId: string;
  readonly version: string;
  readonly authorityClass: SchemaAuthorityClass;
  readonly documentType: string;
  readonly source: ImmutableSourceReference;
}

export interface SchemaEnvelope {
  readonly descriptor: SchemaDescriptor;
  readonly text: string;
  readonly value: JsonValue;
}

export interface StructuralValidationIssue {
  readonly instancePath: string;
  readonly schemaPath: string;
  readonly constraint: string;
  readonly message: string;
  readonly params: Readonly<Record<string, JsonValue>>;
}

export interface StructuralValidationResult {
  readonly authorityClass: "STRUCTURAL_VALIDATION";
  readonly status: "VALID" | "INVALID";
  readonly schema: SchemaDescriptor;
  readonly issues: readonly StructuralValidationIssue[];
}

export interface SourceDescriptor {
  readonly adapterId: string;
  readonly label: string;
  readonly authorityClass: DataAuthorityClass;
  readonly connectionState: SourceConnectionState;
  readonly entityTypes: readonly string[];
  readonly capabilities: readonly Capability[];
  readonly retrievedAt?: string;
}

export interface SubjectReference {
  readonly type: string;
  readonly id: string;
  readonly revision?: string;
  readonly sha256?: string;
}

export interface SourcedResult {
  readonly resultType: string;
  readonly outcome: JsonValue;
  readonly subject: SubjectReference;
  readonly authorityClass: "GOVERNANCE_ASSESSMENT" | "PROTOCOL_RESULT";
  readonly sourceReference: ImmutableSourceReference;
  readonly issuedAt?: string;
  readonly retrievedAt: string;
  readonly verifierRevision?: string;
  readonly policyRevision?: string;
  readonly evidenceReferences?: readonly string[];
  readonly signatureReferences?: readonly string[];
}

export interface ExportReceipt {
  readonly fileName: string;
  readonly byteLength: number;
  readonly sha256: string;
  readonly triggeredByUser: true;
  readonly destination: "NEW_DOWNLOAD";
}
