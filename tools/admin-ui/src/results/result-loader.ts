import type {
  Capability,
  JsonValue,
  SourcedResult,
  SubjectReference,
} from "../core/contracts";
import { AdminUiError, asAdminUiError } from "../core/errors";
import type { DataSourcePort } from "../data/data-source-port";
import { discoverCapability } from "../sources/capability-state";

export type ResultCapability =
  | "governance.controller-independence.read"
  | "governance.signing-readiness.read"
  | "protocol.validation-result.read";

export type ResultQueryState =
  | "READY"
  | "EMPTY"
  | "UNAVAILABLE"
  | "LOADING"
  | "DEGRADED"
  | "STALE"
  | "UNSUPPORTED"
  | "ACCESS_DENIED"
  | "INVALID"
  | "ERROR";

export interface ResultQuery {
  readonly state: ResultQueryState;
  readonly results: readonly SourcedResult[];
  readonly error?: AdminUiError;
}

function record(value: unknown): Record<string, unknown> | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function isJsonValue(value: unknown): value is JsonValue {
  const stack: unknown[] = [value];
  let nodes = 0;
  while (stack.length) {
    const current = stack.pop();
    nodes += 1;
    if (nodes > 100_000) {
      return false;
    }
    if (
      current === null ||
      typeof current === "string" ||
      typeof current === "boolean" ||
      (typeof current === "number" && Number.isFinite(current))
    ) {
      continue;
    }
    if (Array.isArray(current)) {
      stack.push(...current);
      continue;
    }
    const object = record(current);
    if (object) {
      stack.push(...Object.values(object));
      continue;
    }
    return false;
  }
  return true;
}

function expectedAuthority(
  capability: ResultCapability,
): SourcedResult["authorityClass"] {
  return capability === "protocol.validation-result.read"
    ? "PROTOCOL_RESULT"
    : "GOVERNANCE_ASSESSMENT";
}

function sameSubject(actual: Record<string, unknown>, expected: SubjectReference): boolean {
  return (
    actual.type === expected.type &&
    actual.id === expected.id &&
    (expected.revision === undefined || actual.revision === expected.revision) &&
    (expected.sha256 === undefined || actual.sha256 === expected.sha256)
  );
}

function optionalString(value: unknown): boolean {
  return value === undefined || typeof value === "string";
}

function optionalStringArray(value: unknown): boolean {
  return (
    value === undefined ||
    (Array.isArray(value) && value.every((item) => typeof item === "string"))
  );
}

function validateResultEnvelope(
  candidate: unknown,
  capability: ResultCapability,
  expectedSubject: SubjectReference,
): SourcedResult {
  const result = record(candidate);
  const subject = record(result?.subject);
  const source = record(result?.sourceReference);
  if (
    !result ||
    typeof result.resultType !== "string" ||
    !isJsonValue(result.outcome) ||
    !subject ||
    typeof subject.type !== "string" ||
    typeof subject.id !== "string" ||
    !optionalString(subject.revision) ||
    !optionalString(subject.sha256) ||
    !source ||
    !["BUNDLED_FIXTURE", "PUBLIC_CONTRACT", "USER_SELECTED_LOCAL"].includes(
      String(source.kind),
    ) ||
    typeof source.sha256 !== "string" ||
    !/^(?:sha256:)?[a-f0-9]{64}$/iu.test(source.sha256) ||
    !optionalString(source.repository) ||
    !optionalString(source.revision) ||
    !optionalString(source.path) ||
    !optionalString(source.gitBlobSha) ||
    typeof result.retrievedAt !== "string" ||
    !optionalString(result.issuedAt) ||
    !optionalString(result.verifierRevision) ||
    !optionalString(result.policyRevision) ||
    !optionalStringArray(result.evidenceReferences) ||
    !optionalStringArray(result.signatureReferences) ||
    result.authorityClass !== expectedAuthority(capability)
  ) {
    throw new AdminUiError(
      "CAPABILITY_CONTRACT_VIOLATED",
      "The source returned a malformed or incorrectly classified result envelope.",
    );
  }
  if (!sameSubject(subject, expectedSubject)) {
    throw new AdminUiError(
      "SUBJECT_PROVENANCE_MISMATCH",
      "The sourced result does not bind the displayed document revision.",
    );
  }
  return candidate as SourcedResult;
}

function errorState(error: AdminUiError): ResultQueryState {
  switch (error.presentationState) {
    case "UNSUPPORTED":
      return "UNSUPPORTED";
    case "ACCESS_DENIED":
      return "ACCESS_DENIED";
    case "STALE":
      return "STALE";
    case "DEGRADED":
      return "DEGRADED";
    case "INVALID":
      return "INVALID";
    case "ERROR":
      return "ERROR";
  }
}

export async function querySourcedResults(
  sourcePort: DataSourcePort,
  capability: ResultCapability,
  subject: SubjectReference,
): Promise<ResultQuery> {
  const discovery = await discoverCapability(sourcePort, capability as Capability);
  if (
    discovery.state !== "AVAILABLE" &&
    discovery.state !== "STALE"
  ) {
    return { state: discovery.state, results: [] };
  }

  try {
    const candidates: readonly unknown[] = await sourcePort.listSourcedResults(subject);
    const results = candidates.map((candidate) =>
      validateResultEnvelope(candidate, capability, subject),
    );
    if (discovery.state === "STALE") {
      return { state: "STALE", results };
    }
    return { state: results.length ? "READY" : "EMPTY", results };
  } catch (error) {
    const typed = asAdminUiError(error);
    return { state: errorState(typed), results: [], error: typed };
  }
}
