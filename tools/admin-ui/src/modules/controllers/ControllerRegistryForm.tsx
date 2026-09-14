import { useEffect, useMemo, useState } from "react";

import type { DocumentEnvelope, JsonValue } from "../../core/contracts";
import {
  appendControllerDraft,
  patchDocumentAtPath,
  removeControllerDraft,
} from "../../editor/document-draft";
import { controllersFromDocument } from "./controller-model";

export interface ControllerFormState {
  readonly draftControllerKey: string;
  readonly controllerId?: string;
}

export interface ControllerRegistryFormProps {
  readonly draft: DocumentEnvelope;
  readonly controllerKeys: readonly string[];
  readonly createControllerKey: () => string;
  readonly pageSize?: number;
  readonly onChange: (
    nextDraft: DocumentEnvelope,
    nextControllerKeys: readonly string[],
  ) => void;
}

const controllerFields = [
  ["controller_id", "Controller ID"],
  ["status", "Status"],
  ["signer_id", "Signer ID"],
  ["identity_type", "Identity type"],
  ["accountable_owner_id", "Accountable owner ID"],
  ["administrative_domain_id", "Administrative domain ID"],
  ["custody_boundary_id", "Custody boundary ID"],
  ["custody_kind", "Custody kind"],
] as const;

function asRecord(
  value: JsonValue,
): Readonly<Record<string, JsonValue>> | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Readonly<Record<string, JsonValue>>)
    : undefined;
}

function inputValue(value: JsonValue | undefined): string {
  return typeof value === "string" ? value : "";
}

export function controllerFormStates(
  draft: DocumentEnvelope,
  controllerKeys: readonly string[],
): readonly ControllerFormState[] {
  return controllersFromDocument(draft.value).map((controller, index) => ({
    draftControllerKey: controllerKeys[index] ?? `missing-draft-key-${index}`,
    controllerId:
      typeof controller.controller_id === "string"
        ? controller.controller_id
        : undefined,
  }));
}

export function ControllerRegistryForm({
  draft,
  controllerKeys,
  createControllerKey,
  pageSize = 10,
  onChange,
}: ControllerRegistryFormProps) {
  const [page, setPage] = useState(0);
  const root = asRecord(draft.value);
  const rawControllers = root?.controllers;
  const controllers = Array.isArray(rawControllers)
    ? rawControllers.flatMap((value, arrayIndex) => {
        const controller = asRecord(value);
        return controller ? [{ controller, arrayIndex }] : [];
      })
    : [];
  const controllersFieldAvailable = Array.isArray(rawControllers);
  const pageCount = Math.max(1, Math.ceil(controllers.length / pageSize));
  useEffect(() => {
    setPage((current) => Math.min(current, pageCount - 1));
  }, [pageCount]);
  const visibleControllers = useMemo(() => {
    const start = page * pageSize;
    return controllers.slice(start, start + pageSize).map((entry, offset) => ({
      ...entry,
      keyIndex: start + offset,
    }));
  }, [controllers, page, pageSize]);

  function patch(path: readonly (string | number)[], value: JsonValue): void {
    onChange(patchDocumentAtPath(draft, path, value), controllerKeys);
  }

  return (
    <section className="controller-form" aria-labelledby="controller-form-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Guided local draft</p>
          <h2 id="controller-form-heading">Controller registry</h2>
        </div>
        <span aria-label="Controller draft count" className="count-badge">
          {controllers.length}
        </span>
      </div>
      <p className="field-help">
        Edit known fields here. Unknown fields remain in the document and are
        preserved when you download a new file.
      </p>

      <label className="form-field">
        <span>Document version</span>
        <input
          aria-label="Document version"
          value={
            typeof root?.document_version === "string"
              ? root.document_version
              : ""
          }
          disabled={!root}
          onChange={(event) =>
            patch(["document_version"], event.currentTarget.value)
          }
        />
      </label>

      <div className="controller-form-list">
        {visibleControllers.map(({ controller, arrayIndex, keyIndex }) => (
          <fieldset className="controller-form-card" key={controllerKeys[keyIndex] ?? arrayIndex}>
            <legend>Controller {arrayIndex + 1}</legend>
            <div className="controller-fields">
              {controllerFields.map(([field, label]) => (
                <label className="form-field" key={field}>
                  <span>{label}</span>
                  <input
                    aria-label={`Controller ${arrayIndex + 1} ${label}`}
                    value={inputValue(controller[field])}
                    onChange={(event) =>
                      patch(
                        ["controllers", arrayIndex, field],
                        event.currentTarget.value || (field === "status" ? "" : null),
                      )
                    }
                  />
                </label>
              ))}
            </div>
            <button
              className="danger-secondary"
              type="button"
              onClick={() =>
                onChange(
                  removeControllerDraft(draft, arrayIndex),
                  controllerKeys.filter((_, index) => index !== keyIndex),
                )
              }
            >
              Remove controller {arrayIndex + 1}
            </button>
          </fieldset>
        ))}
      </div>

      {pageCount > 1 ? (
        <div className="pagination" aria-label="Controller form pages">
          <button
            disabled={page === 0}
            type="button"
            onClick={() => setPage((current) => current - 1)}
          >
            Previous controller page
          </button>
          <span aria-live="polite">Page {page + 1} of {pageCount}</span>
          <button
            disabled={page >= pageCount - 1}
            type="button"
            onClick={() => setPage((current) => current + 1)}
          >
            Next controller page
          </button>
        </div>
      ) : null}

      {!controllersFieldAvailable ? (
        <div className="attention-box" role="alert">
          The controllers field is not an array. Run structural validation for
          technical details before using the guided controller controls.
        </div>
      ) : controllers.length === 0 ? (
        <div className="empty-state" role="status">
          No controllers yet. Add the first controller to begin the register.
        </div>
      ) : null}

      <button
        className="add-controller"
        disabled={!controllersFieldAvailable}
        type="button"
        onClick={() => {
          const nextCount = controllers.length + 1;
          setPage(Math.floor((nextCount - 1) / pageSize));
          onChange(appendControllerDraft(draft), [
            ...controllerKeys,
            createControllerKey(),
          ]);
        }}
      >
        Add controller
      </button>
    </section>
  );
}
