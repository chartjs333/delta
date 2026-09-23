import { t } from "../i18n";
import { InertText } from "../components/InertText";
import type { JsonValue, SourcedResult } from "../core/contracts";

function displayJson(value: JsonValue): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}

function optionalValue(value?: string): string {
  return value ?? "Not supplied";
}

export function SourcedResultCard({
  result,
}: {
  readonly result: SourcedResult;
}) {
  return (
    <article
      className="sourced-result-card"
      aria-label={`Sourced result ${result.resultType}`}
    >
      <header>
        <div>
          <p className="eyebrow">
            {t("Sourced result · not recomputed by this UI")}
          </p>
          <h3>
            <InertText value={result.resultType} />
          </h3>
        </div>
        <span className="authority-badge">
          <InertText value={result.authorityClass} />
        </span>
      </header>

      <div className="supplied-outcome">
        <span>{t("Outcome (as supplied)")}</span>
        <strong>
          <InertText value={displayJson(result.outcome)} />
        </strong>
      </div>

      <dl className="provenance-grid">
        <div>
          <dt>{t("Subject type")}</dt>
          <dd>
            <InertText value={result.subject.type} />
          </dd>
        </div>
        <div>
          <dt>{t("Subject ID")}</dt>
          <dd>
            <InertText value={result.subject.id} />
          </dd>
        </div>
        <div>
          <dt>{t("Subject revision")}</dt>
          <dd>
            <InertText value={optionalValue(result.subject.revision)} />
          </dd>
        </div>
        <div>
          <dt>{t("Subject SHA-256")}</dt>
          <dd>
            <InertText value={optionalValue(result.subject.sha256)} />
          </dd>
        </div>
        <div>
          <dt>{t("Source kind")}</dt>
          <dd>
            <InertText value={result.sourceReference.kind} />
          </dd>
        </div>
        <div>
          <dt>{t("Source revision")}</dt>
          <dd>
            <InertText value={optionalValue(result.sourceReference.revision)} />
          </dd>
        </div>
        <div>
          <dt>{t("Source path")}</dt>
          <dd>
            <InertText value={optionalValue(result.sourceReference.path)} />
          </dd>
        </div>
        <div>
          <dt>{t("Source SHA-256")}</dt>
          <dd>
            <InertText value={result.sourceReference.sha256} />
          </dd>
        </div>
        <div>
          <dt>{t("Issued")}</dt>
          <dd>
            <InertText value={optionalValue(result.issuedAt)} />
          </dd>
        </div>
        <div>
          <dt>{t("Retrieved")}</dt>
          <dd>
            <InertText value={result.retrievedAt} />
          </dd>
        </div>
        <div>
          <dt>{t("Verifier revision")}</dt>
          <dd>
            <InertText value={optionalValue(result.verifierRevision)} />
          </dd>
        </div>
        <div>
          <dt>{t("Policy revision")}</dt>
          <dd>
            <InertText value={optionalValue(result.policyRevision)} />
          </dd>
        </div>
      </dl>

      <section aria-label={t("Evidence references")}>
        <h4>{t("Evidence references")}</h4>
        {result.evidenceReferences?.length ? (
          <ul>
            {result.evidenceReferences.map((reference, index) => (
              <li key={index}>
                <InertText value={reference} />
              </li>
            ))}
          </ul>
        ) : (
          <p>{t("Not supplied")}</p>
        )}
      </section>

      <section aria-label={t("Signature references")}>
        <h4>{t("Signature references")}</h4>
        {result.signatureReferences?.length ? (
          <ul>
            {result.signatureReferences.map((reference, index) => (
              <li key={index}>
                <InertText value={reference} />
              </li>
            ))}
          </ul>
        ) : (
          <p>{t("Not supplied")}</p>
        )}
      </section>
    </article>
  );
}
