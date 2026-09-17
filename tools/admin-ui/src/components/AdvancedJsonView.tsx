import type { DocumentEnvelope } from "../core/contracts";

export function AdvancedJsonView({
  draft,
}: {
  readonly draft: DocumentEnvelope;
}) {
  return (
    <section className="advanced-json" aria-label="Advanced JSON view">
      <details>
        <summary>Advanced JSON (read-only)</summary>
        <p className="field-help">
          This is a read-only projection of the same local draft used by the form,
          structural validation, and explicit export.
        </p>
        <textarea
          aria-label="Read-only JSON document"
          readOnly
          rows={18}
          spellCheck={false}
          value={draft.text}
        />
      </details>
    </section>
  );
}
