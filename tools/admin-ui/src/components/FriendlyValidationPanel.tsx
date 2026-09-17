import type {
  StructuralValidationIssue,
  StructuralValidationResult,
} from "../core/contracts";
import { InertText } from "./InertText";

const fieldLabels: Readonly<Record<string, string>> = {
  document_type: "Document type",
  document_version: "Document version",
  controllers: "Controllers",
  controller_id: "Controller ID",
  status: "Status",
  signer_id: "Signer ID",
  identity_type: "Identity type",
  accountable_owner_id: "Accountable owner ID",
  administrative_domain_id: "Administrative domain ID",
  custody_boundary_id: "Custody boundary ID",
  custody_kind: "Custody kind",
};

function issueField(issue: StructuralValidationIssue): string | undefined {
  const missingProperty = issue.params.missingProperty;
  if (typeof missingProperty === "string") {
    return missingProperty;
  }
  return issue.instancePath.split("/").filter(Boolean).at(-1);
}

function friendlyLocation(issue: StructuralValidationIssue): string {
  const segments = issue.instancePath.split("/").filter(Boolean);
  const controllerOffset = segments.indexOf("controllers");
  const controllerIndex = Number(segments[controllerOffset + 1]);
  const prefix =
    controllerOffset >= 0 && Number.isInteger(controllerIndex)
      ? `Controller ${controllerIndex + 1} · `
      : "";
  const field = issueField(issue);
  return `${prefix}${field ? fieldLabels[field] ?? field.replaceAll("_", " ") : "Document"}`;
}

function friendlyMessage(issue: StructuralValidationIssue): string {
  const field = issueField(issue);
  const label = field ? fieldLabels[field] ?? field.replaceAll("_", " ") : "value";
  switch (issue.constraint) {
    case "required":
      return `Add ${label.toLowerCase()}.`;
    case "type":
      return `Use the expected value type for ${label.toLowerCase()}.`;
    case "minLength":
      return `${label} cannot be empty.`;
    case "enum":
      return `Choose one of the accepted values for ${label.toLowerCase()}.`;
    default:
      return issue.message;
  }
}

export function FriendlyValidationPanel({
  result,
}: {
  readonly result: StructuralValidationResult;
}) {
  return (
    <section
      className={`validation-panel validation-${result.status.toLowerCase()}`}
      aria-labelledby="validation-heading"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Structural validation only</p>
          <h2 id="validation-heading">{result.status}</h2>
        </div>
        <span className="authority-badge">STRUCTURAL_VALIDATION</span>
      </div>
      <p>
        This checks JSON Schema structure only. Authority outcomes remain external
        to this form.
      </p>
      {result.issues.length ? (
        <ol className="friendly-issue-list" aria-label="Structural validation issues">
          {result.issues.map((issue, index) => (
            <li key={`${issue.instancePath}:${issue.schemaPath}:${index}`}>
              <strong><InertText value={friendlyLocation(issue)} /></strong>
              <p><InertText value={friendlyMessage(issue)} /></p>
              <details>
                <summary>Technical schema details</summary>
                <dl>
                  <div>
                    <dt>Document path</dt>
                    <dd><code><InertText value={issue.instancePath || "/"} /></code></dd>
                  </div>
                  <div>
                    <dt>Schema path</dt>
                    <dd><code><InertText value={issue.schemaPath} /></code></dd>
                  </div>
                  <div>
                    <dt>Constraint</dt>
                    <dd><code><InertText value={issue.constraint} /></code></dd>
                  </div>
                </dl>
              </details>
            </li>
          ))}
        </ol>
      ) : (
        <p className="validation-success">No structural issues found.</p>
      )}
    </section>
  );
}
