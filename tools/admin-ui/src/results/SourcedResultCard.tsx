import { InertText } from "../components/InertText";
import type { JsonValue, SourcedResult } from "../core/contracts";

function displayJson(value: JsonValue): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}

function optionalValue(value?: string): string {
  return value ?? "Not supplied";
}

export function SourcedResultCard({ result }: { readonly result: SourcedResult }) {
  return (
    <article className="sourced-result-card" aria-label={`Sourced result ${result.resultType}`}>
      <header>
        <div>
          <p className="eyebrow">Sourced result · not recomputed by this UI</p>
          <h3><InertText value={result.resultType} /></h3>
        </div>
        <span className="authority-badge">
          <InertText value={result.authorityClass} />
        </span>
      </header>

      <div className="supplied-outcome">
        <span>Outcome (as supplied)</span>
        <strong><InertText value={displayJson(result.outcome)} /></strong>
      </div>

      <dl className="provenance-grid">
        <div><dt>Subject type</dt><dd><InertText value={result.subject.type} /></dd></div>
        <div><dt>Subject ID</dt><dd><InertText value={result.subject.id} /></dd></div>
        <div><dt>Subject revision</dt><dd><InertText value={optionalValue(result.subject.revision)} /></dd></div>
        <div><dt>Subject SHA-256</dt><dd><InertText value={optionalValue(result.subject.sha256)} /></dd></div>
        <div><dt>Source kind</dt><dd><InertText value={result.sourceReference.kind} /></dd></div>
        <div><dt>Source revision</dt><dd><InertText value={optionalValue(result.sourceReference.revision)} /></dd></div>
        <div><dt>Source path</dt><dd><InertText value={optionalValue(result.sourceReference.path)} /></dd></div>
        <div><dt>Source SHA-256</dt><dd><InertText value={result.sourceReference.sha256} /></dd></div>
        <div><dt>Issued</dt><dd><InertText value={optionalValue(result.issuedAt)} /></dd></div>
        <div><dt>Retrieved</dt><dd><InertText value={result.retrievedAt} /></dd></div>
        <div><dt>Verifier revision</dt><dd><InertText value={optionalValue(result.verifierRevision)} /></dd></div>
        <div><dt>Policy revision</dt><dd><InertText value={optionalValue(result.policyRevision)} /></dd></div>
      </dl>

      <section aria-label="Evidence references">
        <h4>Evidence references</h4>
        {result.evidenceReferences?.length ? (
          <ul>
            {result.evidenceReferences.map((reference, index) => (
              <li key={index}><InertText value={reference} /></li>
            ))}
          </ul>
        ) : (
          <p>Not supplied</p>
        )}
      </section>

      <section aria-label="Signature references">
        <h4>Signature references</h4>
        {result.signatureReferences?.length ? (
          <ul>
            {result.signatureReferences.map((reference, index) => (
              <li key={index}><InertText value={reference} /></li>
            ))}
          </ul>
        ) : (
          <p>Not supplied</p>
        )}
      </section>
    </article>
  );
}
