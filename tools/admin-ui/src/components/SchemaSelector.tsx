import { HelpLabel } from "./FieldHelp";
import { t } from "../i18n";
import type { SchemaDescriptor } from "../core/contracts";
import { schemaDescriptorKey } from "../data/local-json-adapter";
import { InertText } from "./InertText";

export interface SchemaSelectorProps {
  readonly schemas: readonly SchemaDescriptor[];
  readonly selected?: SchemaDescriptor;
  readonly onSelect: (schema: SchemaDescriptor) => void;
}

export function SchemaSelector({
  schemas,
  selected,
  onSelect,
}: SchemaSelectorProps) {
  const selectedKey = selected ? schemaDescriptorKey(selected) : "";
  return (
    <section aria-labelledby="schema-heading">
      <h2 id="schema-heading">{t("Structural schema")}</h2>
      <HelpLabel htmlFor="schema-select">{t("Schema descriptor")}</HelpLabel>
      <select
        id="schema-select"
        value={selectedKey}
        onChange={(event) => {
          const next = schemas.find(
            (schema) => schemaDescriptorKey(schema) === event.target.value,
          );
          if (next) {
            onSelect(next);
          }
        }}
      >
        <option value="" disabled>
          {t("Select a schema")}
        </option>
        {schemas.map((schema) => (
          <option
            key={schemaDescriptorKey(schema)}
            value={schemaDescriptorKey(schema)}
          >
            {schema.documentType} · {schema.authorityClass} · {schema.version}
          </option>
        ))}
      </select>
      {selected ? (
        <dl aria-label={t("Selected schema provenance")}>
          <dt>{t("Schema ID")}</dt>
          <dd>
            <InertText value={selected.schemaId} />
          </dd>
          <dt>{t("Version")}</dt>
          <dd>
            <InertText value={selected.version} />
          </dd>
          <dt>{t("Authority")}</dt>
          <dd>
            <InertText value={selected.authorityClass} />
          </dd>
          <dt>{t("Document type")}</dt>
          <dd>
            <InertText value={selected.documentType} />
          </dd>
          <dt>{t("Source SHA-256")}</dt>
          <dd>
            <InertText value={selected.source.sha256} />
          </dd>
        </dl>
      ) : null}
    </section>
  );
}
