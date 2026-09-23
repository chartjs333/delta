import { message, t } from "../../i18n";
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

const safeAutofillFields = ["controller_id", "signer_id", "status"] as const;

export type SafeAutofillField = (typeof safeAutofillFields)[number];

export interface SafeControllerAutofillResult {
  readonly draft: DocumentEnvelope;
  readonly autofilledFields: readonly SafeAutofillField[];
}

const safeAutofillLabels: Readonly<Record<SafeAutofillField, string>> = {
  controller_id: "Controller ID",
  signer_id: "Signer ID",
  status: "Status",
};

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

function isBlank(value: JsonValue | undefined): boolean {
  return (
    value === null ||
    value === undefined ||
    (typeof value === "string" && value.trim() === "")
  );
}

function stableDraftIdentifier(
  kind: "controller" | "signer",
  draftControllerKey: string,
): string {
  return `draft-${kind}:${encodeURIComponent(draftControllerKey)}`;
}

/**
 * Fills only the explicitly whitelisted, non-authoritative technical fields.
 * Every other controller property is retained without changing its JSON value.
 */
export function autofillSafeControllerDraft(
  draft: DocumentEnvelope,
  controllerIndex: number,
  draftControllerKey: string,
): SafeControllerAutofillResult {
  if (!draftControllerKey) {
    throw new RangeError(
      "A stable draft controller key is required for autofill.",
    );
  }
  const root = asRecord(draft.value);
  const controllers = root?.controllers;
  const controller = Array.isArray(controllers)
    ? asRecord(controllers[controllerIndex])
    : undefined;
  if (!controller) {
    throw new RangeError(`Controller index ${controllerIndex} is unavailable.`);
  }

  const nextController: Record<string, JsonValue> = { ...controller };
  const autofilledFields: SafeAutofillField[] = [];
  const fill = (field: SafeAutofillField, value: string): void => {
    if (isBlank(controller[field])) {
      nextController[field] = value;
      autofilledFields.push(field);
    }
  };

  fill(
    "controller_id",
    stableDraftIdentifier("controller", draftControllerKey),
  );
  fill("signer_id", stableDraftIdentifier("signer", draftControllerKey));
  fill("status", "DRAFT");

  return {
    draft:
      autofilledFields.length === 0
        ? draft
        : patchDocumentAtPath(
            draft,
            ["controllers", controllerIndex],
            nextController,
          ),
    autofilledFields,
  };
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
  const [autofillNotices, setAutofillNotices] = useState<
    Readonly<Record<string, string>>
  >({});
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
    <section
      className="controller-form"
      aria-labelledby="controller-form-heading"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("Guided local draft")}</p>
          <h2 id="controller-form-heading">{t("Controller registry")}</h2>
        </div>
        <span aria-label={t("Controller draft count")} className="count-badge">
          {controllers.length}
        </span>
      </div>
      <p className="field-help">
        {t(
          "Edit known fields here. Unknown fields remain in the document and are preserved when you download a new file.",
        )}
      </p>

      <label className="form-field">
        <span>{t("Document version")}</span>
        <input
          aria-label={t("Document version")}
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
        {visibleControllers.map(({ controller, arrayIndex, keyIndex }) => {
          const draftControllerKey = controllerKeys[keyIndex];
          return (
            <fieldset
              className="controller-form-card"
              key={draftControllerKey ?? arrayIndex}
            >
              <legend>
                {t("Controller ")}
                {arrayIndex + 1}
              </legend>
              <div className="controller-fields">
                {controllerFields.map(([field, label]) => (
                  <label className="form-field" key={field}>
                    <span>{t(label)}</span>
                    <input
                      aria-label={t("Controller {number} {field}", {
                        number: arrayIndex + 1,
                        field: t(label),
                      })}
                      value={inputValue(controller[field])}
                      onChange={(event) =>
                        patch(
                          ["controllers", arrayIndex, field],
                          event.currentTarget.value ||
                            (field === "status" ? "" : null),
                        )
                      }
                    />
                  </label>
                ))}
              </div>
              <div className="safe-autofill-actions">
                <button
                  type="button"
                  disabled={!draftControllerKey}
                  onClick={() => {
                    if (!draftControllerKey) return;
                    const result = autofillSafeControllerDraft(
                      draft,
                      arrayIndex,
                      draftControllerKey,
                    );
                    const message =
                      result.autofilledFields.length > 0
                        ? `Auto-filled: ${result.autofilledFields
                            .map((field) => safeAutofillLabels[field])
                            .join(", ")}.`
                        : "No safe fields were changed; the draft IDs and status already have values.";
                    setAutofillNotices((current) => ({
                      ...current,
                      [draftControllerKey]: message,
                    }));
                    if (result.autofilledFields.length > 0) {
                      onChange(result.draft, controllerKeys);
                    }
                  }}
                >
                  {t("Autofill safe fields for controller ")}
                  {arrayIndex + 1}
                </button>
                <p className="field-help">
                  {t(
                    "Fills only blank draft Controller ID, Signer ID, and Status fields. It does not infer identity, custody, independence, governance, or protocol data.",
                  )}
                </p>
                {draftControllerKey && autofillNotices[draftControllerKey] ? (
                  <p
                    className="autofill-notice"
                    role="status"
                    aria-live="polite"
                  >
                    {message(autofillNotices[draftControllerKey])}
                  </p>
                ) : null}
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
                {t("Remove controller ")}
                {arrayIndex + 1}
              </button>
            </fieldset>
          );
        })}
      </div>

      {pageCount > 1 ? (
        <div className="pagination" aria-label={t("Controller form pages")}>
          <button
            disabled={page === 0}
            type="button"
            onClick={() => setPage((current) => current - 1)}
          >
            {t("Previous controller page")}
          </button>
          <span aria-live="polite">
            {t("Page ")}
            {page + 1}
            {t(" of ")}
            {pageCount}
          </span>
          <button
            disabled={page >= pageCount - 1}
            type="button"
            onClick={() => setPage((current) => current + 1)}
          >
            {t("Next controller page")}
          </button>
        </div>
      ) : null}

      {!controllersFieldAvailable ? (
        <div className="attention-box" role="alert">
          {t(
            "The controllers field is not an array. Run structural validation for technical details before using the guided controller controls.",
          )}
        </div>
      ) : controllers.length === 0 ? (
        <div className="empty-state" role="status">
          {t(
            "No controllers yet. Add the first controller to begin the register.",
          )}
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
        {t("Add controller")}
      </button>
    </section>
  );
}
