import { t } from "../i18n";
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
      ? t("Controller {number} · ", { number: controllerIndex + 1 })
      : "";
  const field = issueField(issue);
  return `${prefix}${t(field ? (fieldLabels[field] ?? field.replaceAll("_", " ")) : "Document")}`;
}

function friendlyMessage(issue: StructuralValidationIssue): string {
  const field = issueField(issue);
  const label = field
    ? (fieldLabels[field] ?? field.replaceAll("_", " "))
    : "value";
  switch (issue.constraint) {
    case "required":
      return t("Add {field}.", { field: t(label).toLowerCase() });
    case "type":
      return t("Use the expected value type for {field}.", {
        field: t(label).toLowerCase(),
      });
    case "minLength":
      return t("{field} cannot be empty.", { field: t(label) });
    case "enum":
      return t("Choose one of the accepted values for {field}.", {
        field: t(label).toLowerCase(),
      });
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
          <p className="eyebrow">{t("Structural validation only")}</p>
          <h2 id="validation-heading">{result.status}</h2>
        </div>
        <span className="authority-badge">STRUCTURAL_VALIDATION</span>
      </div>
      <p>
        {t(
          "This checks JSON Schema structure only. Authority outcomes remain external to this form.",
        )}
      </p>
      {result.issues.length ? (
        <ol
          className="friendly-issue-list"
          aria-label={t("Structural validation issues")}
        >
          {result.issues.map((issue, index) => (
            <li key={`${issue.instancePath}:${issue.schemaPath}:${index}`}>
              <strong>
                <InertText value={friendlyLocation(issue)} />
              </strong>
              <p>
                <InertText value={friendlyMessage(issue)} />
              </p>
              <details>
                <summary>{t("Technical schema details")}</summary>
                <dl>
                  <div>
                    <dt>{t("Document path")}</dt>
                    <dd>
                      <code>
                        <InertText value={issue.instancePath || "/"} />
                      </code>
                    </dd>
                  </div>
                  <div>
                    <dt>{t("Schema path")}</dt>
                    <dd>
                      <code>
                        <InertText value={issue.schemaPath} />
                      </code>
                    </dd>
                  </div>
                  <div>
                    <dt>{t("Constraint")}</dt>
                    <dd>
                      <code>
                        <InertText value={issue.constraint} />
                      </code>
                    </dd>
                  </div>
                </dl>
              </details>
            </li>
          ))}
        </ol>
      ) : (
        <p className="validation-success">{t("No structural issues found.")}</p>
      )}
    </section>
  );
}
