import { t } from "../../i18n";
import { useEffect, useMemo, useState } from "react";

import { InertText } from "../../components/InertText";
import type { JsonValue } from "../../core/contracts";
import { controllerLabel, type ControllerRecord } from "./controller-model";

export interface ControllerExplorerProps {
  readonly controllers: readonly ControllerRecord[];
  readonly pageSize?: number;
}

function displayValue(value: JsonValue): string {
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
}

export function ControllerExplorer({
  controllers,
  pageSize = 25,
}: ControllerExplorerProps) {
  const [page, setPage] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState<number | undefined>();
  const pageCount = Math.max(1, Math.ceil(controllers.length / pageSize));

  useEffect(() => {
    setPage((current) => Math.min(current, pageCount - 1));
    setSelectedIndex((current) =>
      current !== undefined && current < controllers.length
        ? current
        : undefined,
    );
  }, [controllers.length, pageCount]);

  const visible = useMemo(() => {
    const start = page * pageSize;
    return controllers
      .slice(start, start + pageSize)
      .map((controller, offset) => ({
        controller,
        index: start + offset,
      }));
  }, [controllers, page, pageSize]);

  const selected =
    selectedIndex === undefined ? undefined : controllers[selectedIndex];

  return (
    <section
      className="controller-explorer"
      aria-labelledby="controllers-heading"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("Structurally valid collection")}</p>
          <h2 id="controllers-heading">{t("Controllers")}</h2>
        </div>
        <span aria-label={t("Controller count")} className="count-badge">
          {controllers.length}
        </span>
      </div>

      {controllers.length === 0 ? (
        <div className="empty-state" role="status">
          {t("This document contains an empty controller array.")}
        </div>
      ) : (
        <div className="controller-layout">
          <div>
            <ul className="controller-list" aria-label={t("Controller list")}>
              {visible.map(({ controller, index }) => {
                const status = controller.status;
                return (
                  <li key={index}>
                    <button
                      className={selectedIndex === index ? "selected" : ""}
                      type="button"
                      onClick={() => setSelectedIndex(index)}
                    >
                      <span>
                        <small>
                          {t("Presentation row ")}
                          {index + 1}
                        </small>
                        <strong>
                          <InertText
                            value={controllerLabel(controller, index)}
                          />
                        </strong>
                      </span>
                      <span className="raw-status">
                        <InertText
                          value={
                            typeof status === "string" ? status : "Not provided"
                          }
                        />
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
            {pageCount > 1 ? (
              <div className="pagination" aria-label={t("Controller pages")}>
                <button
                  type="button"
                  disabled={page === 0}
                  onClick={() => setPage((current) => current - 1)}
                >
                  {t("Previous")}
                </button>
                <span aria-live="polite">
                  {t("Page ")}
                  {page + 1}
                  {t(" of ")}
                  {pageCount}
                </span>
                <button
                  type="button"
                  disabled={page >= pageCount - 1}
                  onClick={() => setPage((current) => current + 1)}
                >
                  {t("Next")}
                </button>
              </div>
            ) : null}
          </div>

          <aside
            className="controller-detail"
            aria-label={t("Controller detail")}
          >
            {selected ? (
              <>
                <p className="eyebrow">{t("Local document fields")}</p>
                <h3>{controllerLabel(selected, selectedIndex ?? 0)}</h3>
                <dl>
                  {Object.entries(selected).map(([field, value]) => (
                    <div key={field}>
                      <dt>
                        <InertText value={field} />
                      </dt>
                      <dd>
                        <InertText value={displayValue(value)} />
                      </dd>
                    </div>
                  ))}
                </dl>
              </>
            ) : (
              <p>{t("Select a controller to inspect its local fields.")}</p>
            )}
          </aside>
        </div>
      )}
    </section>
  );
}
