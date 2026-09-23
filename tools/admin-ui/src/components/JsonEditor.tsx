import { FieldHelp } from "./FieldHelp";
import { t } from "../i18n";
export interface JsonEditorProps {
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly invalidMessage?: string;
}

export function JsonEditor({
  value,
  onChange,
  invalidMessage,
}: JsonEditorProps) {
  return (
    <section aria-labelledby="json-editor-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("Local draft")}</p>
          <h2 id="json-editor-heading">{t("JSON editor")}</h2>
        </div>
        <span className="local-only-badge">{t("In memory")}</span>
      </div>
      <label className="sr-only" htmlFor="json-editor">
        {t("JSON document text")}
      </label>
      <FieldHelp field="JSON document text" />
      <textarea
        id="json-editor"
        aria-describedby={invalidMessage ? "json-editor-error" : undefined}
        aria-invalid={invalidMessage ? "true" : "false"}
        spellCheck={false}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      {invalidMessage ? (
        <p id="json-editor-error" className="inline-error" role="alert">
          {invalidMessage}
        </p>
      ) : (
        <p className="field-help">
          {t("Changes stay local until Download new file.")}
        </p>
      )}
    </section>
  );
}
