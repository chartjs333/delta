import type { DocumentEnvelope } from "../core/contracts";
import { parseUntrustedJson } from "../security/input-guards";
import { inferDocumentType } from "../validation/structural-validator";

export function editDocumentText(
  previous: DocumentEnvelope,
  text: string,
): DocumentEnvelope {
  const parsed = parseUntrustedJson(new TextEncoder().encode(text));
  return {
    ...previous,
    ...parsed,
    documentType: inferDocumentType(parsed.value),
  };
}
