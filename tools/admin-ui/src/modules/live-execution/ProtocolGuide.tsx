import { useState } from "react";
import { t } from "../../i18n";

const stages = [
  [
    "Workers",
    "Local learning",
    "Each worker trains on its own data under a fixed work ticket.",
  ],
  [
    "Updates + CID",
    "Identify the contribution",
    "Canonical update bytes have a content ID. A CID identifies bytes; it is not a vote.",
  ],
  [
    "Validators",
    "Agree on the inputs",
    "An InputSetCertificate freezes the same eligible input set by quorum before the random seed is revealed.",
  ],
  [
    "Shards",
    "Divide the fixed work",
    "The certified eligibility and aggregation plan defines the deterministic domain and shard assignments.",
  ],
  [
    "Aggregation",
    "Compute, then approve",
    "Exact integer shard results form AggregateRootQC. A separate ApplyQC certifies the next model and optimizer state.",
  ],
  [
    "Checkpoint",
    "Publish one certified state",
    "The current checkpoint advances only through the certified apply path; replay preserves the same result.",
  ],
] as const;

export function ProtocolGuide() {
  const [selected, setSelected] = useState(0);
  return (
    <details className="protocol-guide">
      <summary>
        <span>{t("How DeltaReduce works")}</span>
        <small>{t("Explore the six stages")}</small>
      </summary>
      <p className="guide-note">
        {t(
          "Protocol overview. These are not live progress indicators for the local example below.",
        )}
      </p>
      <div
        className="protocol-stages"
        role="group"
        aria-label={t("Protocol stages")}
      >
        {stages.map(([title, subtitle], index) => (
          <button
            type="button"
              key={title}
              aria-label={`${index + 1}. ${t(title)}: ${t(subtitle)}`}
            aria-pressed={selected === index}
            aria-controls="protocol-explanation"
            onClick={() => setSelected(index)}
          >
            <span className="stage-number" aria-hidden="true">
              {index + 1}
            </span>
            <strong>{t(title)}</strong>
            <small>{t(subtitle)}</small>
          </button>
        ))}
      </div>
      <div
        id="protocol-explanation"
        className="protocol-explanation"
        aria-live="polite"
      >
        <strong>
          {selected + 1}. {t(stages[selected][0])}
        </strong>
        <p>{t(stages[selected][2])}</p>
      </div>
    </details>
  );
}
