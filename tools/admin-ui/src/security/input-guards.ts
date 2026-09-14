import type { JsonValue } from "../core/contracts";
import { AdminUiError } from "../core/errors";

export const INPUT_LIMITS = Object.freeze({
  fileBytes: 5_242_880,
  nestingDepth: 64,
  nodes: 100_000,
  stringBytes: 1_048_576,
  urlCharacters: 2_048,
});

const textDecoder = new TextDecoder("utf-8", { fatal: true });
const textEncoder = new TextEncoder();
const URL_LIKE = /^[a-z][a-z0-9+.-]*:/iu;

const ARCHIVE_SIGNATURES: readonly Uint8Array[] = [
  new Uint8Array([0x50, 0x4b, 0x03, 0x04]),
  new Uint8Array([0x50, 0x4b, 0x05, 0x06]),
  new Uint8Array([0x1f, 0x8b]),
  new Uint8Array([0x42, 0x5a, 0x68]),
  new Uint8Array([0x37, 0x7a, 0xbc, 0xaf, 0x27, 0x1c]),
  new Uint8Array([0x52, 0x61, 0x72, 0x21]),
];

function limitExceeded(field: string, limit: number): AdminUiError {
  return new AdminUiError(
    "INPUT_LIMIT_EXCEEDED",
    `The selected JSON exceeds the ${field} safety limit.`,
    { field, limit },
  );
}

function throwIfCancelled(signal?: AbortSignal): void {
  if (signal?.aborted) {
    throw new AdminUiError(
      "VALIDATION_CANCELLED",
      "Local input inspection was cancelled.",
    );
  }
}

function hasArchiveSignature(bytes: Uint8Array): boolean {
  return ARCHIVE_SIGNATURES.some(
    (signature) =>
      bytes.byteLength >= signature.byteLength &&
      signature.every((byte, index) => bytes[index] === byte),
  );
}

function inspectString(value: string): void {
  if (textEncoder.encode(value).byteLength > INPUT_LIMITS.stringBytes) {
    throw limitExceeded("individual UTF-8 string", INPUT_LIMITS.stringBytes);
  }
  if (URL_LIKE.test(value) && value.length > INPUT_LIMITS.urlCharacters) {
    throw limitExceeded("displayed or actionable URL", INPUT_LIMITS.urlCharacters);
  }
}

function inspectValue(root: unknown, signal?: AbortSignal): asserts root is JsonValue {
  const stack: Array<{ value: unknown; containerDepth: number }> = [
    { value: root, containerDepth: 0 },
  ];
  let nodes = 0;

  while (stack.length > 0) {
    if ((nodes & 1023) === 0) {
      throwIfCancelled(signal);
    }

    const current = stack.pop();
    if (!current) {
      break;
    }
    nodes += 1;
    if (nodes > INPUT_LIMITS.nodes) {
      throw limitExceeded("aggregate JSON node count", INPUT_LIMITS.nodes);
    }

    if (typeof current.value === "string") {
      inspectString(current.value);
      continue;
    }
    if (
      current.value === null ||
      typeof current.value === "number" ||
      typeof current.value === "boolean"
    ) {
      continue;
    }

    if (Array.isArray(current.value)) {
      const depth = current.containerDepth + 1;
      if (depth > INPUT_LIMITS.nestingDepth) {
        throw limitExceeded("JSON nesting depth", INPUT_LIMITS.nestingDepth);
      }
      for (let index = current.value.length - 1; index >= 0; index -= 1) {
        stack.push({ value: current.value[index], containerDepth: depth });
      }
      continue;
    }

    if (typeof current.value === "object") {
      const depth = current.containerDepth + 1;
      if (depth > INPUT_LIMITS.nestingDepth) {
        throw limitExceeded("JSON nesting depth", INPUT_LIMITS.nestingDepth);
      }
      const entries = Object.entries(current.value);
      for (let index = entries.length - 1; index >= 0; index -= 1) {
        const [key, value] = entries[index];
        inspectString(key);
        stack.push({ value, containerDepth: depth });
      }
      continue;
    }

    throw new AdminUiError(
      "DOCUMENT_MALFORMED",
      "The selected file does not contain a JSON value.",
    );
  }
}

export function parseUntrustedJson(
  bytes: Uint8Array,
  signal?: AbortSignal,
): { readonly text: string; readonly value: JsonValue } {
  throwIfCancelled(signal);
  if (bytes.byteLength > INPUT_LIMITS.fileBytes) {
    throw limitExceeded("JSON or schema file size", INPUT_LIMITS.fileBytes);
  }
  if (hasArchiveSignature(bytes)) {
    throw new AdminUiError(
      "DOCUMENT_MALFORMED",
      "Archive and compressed input is not accepted.",
    );
  }

  let text: string;
  try {
    text = textDecoder.decode(bytes);
  } catch {
    throw new AdminUiError(
      "DOCUMENT_MALFORMED",
      "The selected file is not well-formed UTF-8 JSON.",
    );
  }

  let value: unknown;
  try {
    value = JSON.parse(text) as unknown;
  } catch {
    throw new AdminUiError(
      "DOCUMENT_MALFORMED",
      "The selected file contains malformed JSON.",
    );
  }

  inspectValue(value, signal);
  return { text, value };
}
