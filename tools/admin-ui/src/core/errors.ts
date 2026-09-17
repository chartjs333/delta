export type AdminUiErrorCode =
  | "SOURCE_UNAVAILABLE"
  | "OPERATION_UNSUPPORTED"
  | "ACCESS_DENIED"
  | "SCHEMA_NOT_FOUND"
  | "SCHEMA_VERSION_UNSUPPORTED"
  | "SCHEMA_DESCRIPTOR_MISMATCH"
  | "DOCUMENT_MALFORMED"
  | "DOCUMENT_STRUCTURALLY_INVALID"
  | "DATA_STALE"
  | "CAPABILITY_CONTRACT_VIOLATED"
  | "SUBJECT_PROVENANCE_MISMATCH"
  | "INPUT_LIMIT_EXCEEDED"
  | "VALIDATION_CANCELLED"
  | "UNEXPECTED_ERROR";

export type ErrorPresentationState =
  | "UNSUPPORTED"
  | "ACCESS_DENIED"
  | "STALE"
  | "DEGRADED"
  | "INVALID"
  | "ERROR";

const presentationByCode: Readonly<Record<AdminUiErrorCode, ErrorPresentationState>> = {
  SOURCE_UNAVAILABLE: "DEGRADED",
  OPERATION_UNSUPPORTED: "UNSUPPORTED",
  ACCESS_DENIED: "ACCESS_DENIED",
  SCHEMA_NOT_FOUND: "INVALID",
  SCHEMA_VERSION_UNSUPPORTED: "INVALID",
  SCHEMA_DESCRIPTOR_MISMATCH: "INVALID",
  DOCUMENT_MALFORMED: "INVALID",
  DOCUMENT_STRUCTURALLY_INVALID: "INVALID",
  DATA_STALE: "STALE",
  CAPABILITY_CONTRACT_VIOLATED: "ERROR",
  SUBJECT_PROVENANCE_MISMATCH: "INVALID",
  INPUT_LIMIT_EXCEEDED: "INVALID",
  VALIDATION_CANCELLED: "INVALID",
  UNEXPECTED_ERROR: "ERROR",
};

export class AdminUiError extends Error {
  readonly presentationState: ErrorPresentationState;

  constructor(
    readonly code: AdminUiErrorCode,
    message: string,
    readonly details: Readonly<Record<string, unknown>> = {},
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = "AdminUiError";
    this.presentationState = presentationByCode[code];
  }
}

export function asAdminUiError(error: unknown): AdminUiError {
  if (error instanceof AdminUiError) {
    return error;
  }
  return new AdminUiError(
    "UNEXPECTED_ERROR",
    error instanceof Error ? error.message : "An unexpected local error occurred.",
    {},
    error instanceof Error ? { cause: error } : undefined,
  );
}
