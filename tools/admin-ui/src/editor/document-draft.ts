import type { DocumentEnvelope, JsonValue } from "../core/contracts";
import { parseUntrustedJson } from "../security/input-guards";
import { inferDocumentType } from "../validation/structural-validator";

export type DocumentDraft = DocumentEnvelope;
export type DocumentPathSegment = string | number;

function asRecord(
  value: JsonValue,
): Readonly<Record<string, JsonValue>> | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Readonly<Record<string, JsonValue>>)
    : undefined;
}

function materializeDraft(
  previous: DocumentEnvelope,
  value: JsonValue,
): DocumentEnvelope {
  const text = `${JSON.stringify(value, null, 2)}\n`;
  return {
    ...previous,
    text,
    value,
    documentType: inferDocumentType(value),
    origin: {
      ...previous.origin,
      byteLength: new TextEncoder().encode(text).byteLength,
    },
  };
}

function patchValue(
  current: JsonValue,
  path: readonly DocumentPathSegment[],
  offset: number,
  replacement: JsonValue,
): JsonValue {
  if (offset === path.length) {
    return replacement;
  }

  const segment = path[offset];
  if (typeof segment === "number") {
    if (!Array.isArray(current) || segment < 0 || segment >= current.length) {
      throw new RangeError(`Document path index ${segment} is unavailable.`);
    }
    const next = [...current];
    next[segment] = patchValue(next[segment], path, offset + 1, replacement);
    return next;
  }

  const record = asRecord(current);
  if (!record) {
    throw new TypeError(`Document path field ${segment} is unavailable.`);
  }
  return {
    ...record,
    [segment]: patchValue(record[segment] ?? null, path, offset + 1, replacement),
  };
}

/**
 * Patches one known presentation path while retaining every other JSON value.
 * This is the only form-to-document mutation primitive.
 */
export function patchDocumentAtPath(
  previous: DocumentEnvelope,
  path: readonly DocumentPathSegment[],
  replacement: JsonValue,
): DocumentEnvelope {
  if (path.length === 0) {
    return materializeDraft(previous, replacement);
  }
  return materializeDraft(
    previous,
    patchValue(previous.value, path, 0, replacement),
  );
}

export function appendControllerDraft(
  previous: DocumentEnvelope,
): DocumentEnvelope {
  const root = asRecord(previous.value);
  const controllers = root?.controllers;
  if (!root || !Array.isArray(controllers)) {
    throw new TypeError("The document controllers field must be an array.");
  }
  return patchDocumentAtPath(previous, ["controllers"], [
    ...controllers,
    { controller_id: null, status: "DRAFT" },
  ]);
}

export function removeControllerDraft(
  previous: DocumentEnvelope,
  index: number,
): DocumentEnvelope {
  const root = asRecord(previous.value);
  const controllers = root?.controllers;
  if (!Array.isArray(controllers) || index < 0 || index >= controllers.length) {
    throw new RangeError(`Controller index ${index} is unavailable.`);
  }
  return patchDocumentAtPath(
    previous,
    ["controllers"],
    controllers.filter((_, controllerIndex) => controllerIndex !== index),
  );
}

export function editDocumentText(
  previous: DocumentEnvelope,
  text: string,
): DocumentEnvelope {
  const parsed = parseUntrustedJson(new TextEncoder().encode(text));
  return {
    ...previous,
    ...parsed,
    documentType: inferDocumentType(parsed.value),
    origin: {
      ...previous.origin,
      byteLength: new TextEncoder().encode(text).byteLength,
    },
  };
}
