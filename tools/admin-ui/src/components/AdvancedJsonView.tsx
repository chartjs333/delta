import { FieldHelp } from "./FieldHelp";
import { t } from "../i18n";
import type { DocumentEnvelope } from "../core/contracts";

export function AdvancedJsonView({
  draft,
}: {
  readonly draft: DocumentEnvelope;
}) {
  return (
    <section className="advanced-json" aria-label={t("Advanced JSON view")}>
      <details>
        <summary>{t("Advanced JSON (read-only)")}</summary>
        <p className="field-help">
          {t(
            "This is a read-only projection of the same local draft used by the form, structural validation, and explicit export.",
          )}
        </p>
        <FieldHelp field="Read-only JSON document" />
        <textarea
          aria-label={t("Read-only JSON document")}
          readOnly
          rows={18}
          spellCheck={false}
          value={draft.text}
        />
      </details>
    </section>
  );
}
