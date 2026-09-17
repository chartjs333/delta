import type { StructuralValidationResult } from "../core/contracts";
import { InertText } from "./InertText";

export function ValidationPanel({
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
        This result checks JSON Schema structure. It is not governance approval,
        signing readiness, execution authorization, or a Delta protocol verdict.
      </p>
      {result.issues.length ? (
        <ol className="issue-list" aria-label="Structural validation issues">
          {result.issues.map((issue, index) => (
            <li key={`${issue.instancePath}:${issue.schemaPath}:${index}`}>
              <code><InertText value={issue.instancePath || "/"} /></code>
              <span><InertText value={issue.constraint} /></span>
              <p><InertText value={issue.message} /></p>
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
