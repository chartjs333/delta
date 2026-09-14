import { AdminUiError } from "../core/errors";
import { INPUT_LIMITS } from "./input-guards";

export function allowExplicitHttpsUrl(
  value: string,
  explicitUserAction: boolean,
): URL {
  if (!explicitUserAction) {
    throw new AdminUiError(
      "OPERATION_UNSUPPORTED",
      "URLs remain inert until an explicit user action.",
    );
  }
  if (value.length > INPUT_LIMITS.urlCharacters) {
    throw new AdminUiError(
      "INPUT_LIMIT_EXCEEDED",
      "The URL exceeds the actionable URL safety limit.",
      { field: "actionable URL", limit: INPUT_LIMITS.urlCharacters },
    );
  }

  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new AdminUiError("DOCUMENT_MALFORMED", "The URL is malformed.");
  }
  if (parsed.protocol !== "https:" || parsed.username || parsed.password) {
    throw new AdminUiError(
      "OPERATION_UNSUPPORTED",
      "Only credential-free HTTPS URLs can be opened explicitly.",
    );
  }
  return parsed;
}
