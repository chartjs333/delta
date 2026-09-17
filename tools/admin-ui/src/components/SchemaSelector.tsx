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
      <h2 id="schema-heading">Structural schema</h2>
      <label htmlFor="schema-select">Schema descriptor</label>
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
          Select a schema
        </option>
        {schemas.map((schema) => (
          <option key={schemaDescriptorKey(schema)} value={schemaDescriptorKey(schema)}>
            {schema.documentType} · {schema.authorityClass} · {schema.version}
          </option>
        ))}
      </select>
      {selected ? (
        <dl aria-label="Selected schema provenance">
          <dt>Schema ID</dt>
          <dd><InertText value={selected.schemaId} /></dd>
          <dt>Version</dt>
          <dd><InertText value={selected.version} /></dd>
          <dt>Authority</dt>
          <dd><InertText value={selected.authorityClass} /></dd>
          <dt>Document type</dt>
          <dd><InertText value={selected.documentType} /></dd>
          <dt>Source SHA-256</dt>
          <dd><InertText value={selected.source.sha256} /></dd>
        </dl>
      ) : null}
    </section>
  );
}
