import { t } from "../i18n";
import type { Capability, SourceDescriptor } from "../core/contracts";
import type { CapabilityState } from "../sources/capability-state";
import { InertText } from "./InertText";

const stateMessage: Readonly<Record<CapabilityState, string>> = {
  AVAILABLE: "Available from the active source.",
  UNAVAILABLE:
    "Unavailable: the active source does not provide this capability.",
  LOADING: "Loading source capability information.",
  DEGRADED: "Degraded: the source cannot currently provide this capability.",
  STALE:
    "Stale: the source advertises this capability, but its data may be old.",
  ACCESS_DENIED: "Access denied by the source.",
};

export interface CapabilityStateViewProps {
  readonly capability: Capability;
  readonly state: CapabilityState;
}

export function CapabilityStateView({
  capability,
  state,
}: CapabilityStateViewProps) {
  return (
    <div
      className={`capability-state state-${state.toLowerCase()}`}
      role="status"
    >
      <strong>
        <InertText value={capability} />
      </strong>
      <span>{t(stateMessage[state])}</span>
    </div>
  );
}

export function SourceSummary({
  source,
}: {
  readonly source: SourceDescriptor;
}) {
  return (
    <section aria-labelledby="source-heading">
      <p className="eyebrow">{t("Active source")}</p>
      <h2 id="source-heading">
        <InertText value={t(source.label)} />
      </h2>
      <dl className="source-summary">
        <div>
          <dt>{t("Adapter")}</dt>
          <dd>
            <InertText value={source.adapterId} />
          </dd>
        </div>
        <div>
          <dt>{t("Authority")}</dt>
          <dd>
            <InertText value={source.authorityClass} />
          </dd>
        </div>
        <div>
          <dt>{t("State")}</dt>
          <dd>
            <InertText value={source.connectionState} />
          </dd>
        </div>
      </dl>
      <div aria-label={t("Source capabilities")} className="capability-list">
        {source.capabilities.length === 0 ? (
          <span>{t("None declared")}</span>
        ) : (
          source.capabilities.map((capability) => (
            <span className="capability-chip" key={capability}>
              <InertText value={capability} />
            </span>
          ))
        )}
      </div>
    </section>
  );
}
