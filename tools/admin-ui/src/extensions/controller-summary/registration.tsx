import { t } from "../../i18n";
import type { ExtensionRegistration } from "../../app/extensions";

export function ControllerSummaryView() {
  return (
    <section aria-labelledby="controller-summary-heading">
      <p className="eyebrow">{t("Alternate entity view")}</p>
      <h2 id="controller-summary-heading">{t("Controller summary")}</h2>
      <p>
        {t(
          "This presentation consumes the registered controller-list contract and does not infer governance or protocol meaning from local fields.",
        )}
      </p>
    </section>
  );
}

export function ControllerSummaryUnavailable() {
  return (
    <p role="status">
      {t("Controller summary unavailable for the active source.")}
    </p>
  );
}

export const controllerSummaryRegistration: ExtensionRegistration = {
  entityView: {
    entityType: "controller",
    viewId: "summary",
    inputContract: "controller.list",
    component: ControllerSummaryView,
    fallback: ControllerSummaryUnavailable,
  },
};
