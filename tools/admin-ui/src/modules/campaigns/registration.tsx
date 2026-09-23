import { t } from "../../i18n";
import type { ExtensionRegistration } from "../../app/extensions";
import { CapabilityStateView } from "../../components/CapabilityStateView";

export function CampaignsPlaceholderRoute() {
  return (
    <section aria-labelledby="campaigns-heading">
      <p className="eyebrow">{t("Placeholder domain module")}</p>
      <h2 id="campaigns-heading">{t("Campaigns")}</h2>
      <p>
        {t(
          "This browser-local source does not expose campaign data. No runtime or network fallback is attempted.",
        )}
      </p>
      <CapabilityStateView capability="campaign.read" state="UNAVAILABLE" />
    </section>
  );
}

export const campaignPlaceholderRegistration: ExtensionRegistration = {
  navigation: {
    id: "campaigns",
    label: "Campaigns",
    route: "/campaigns",
    permission: "PUBLIC_LOCAL",
  },
  domainModule: {
    id: "campaigns-placeholder",
    routes: [{ path: "/campaigns", component: CampaignsPlaceholderRoute }],
    views: ["campaign-unavailable"],
    requiredCapabilities: ["campaign.read"],
  },
};
