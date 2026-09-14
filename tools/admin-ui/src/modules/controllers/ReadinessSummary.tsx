import type { StructuralValidationResult } from "../../core/contracts";
import type { ResultQuery } from "../../results/result-loader";
import type { ControllerFormState } from "./ControllerRegistryForm";
import {
  isPairwiseRecordFilled,
  type PairwiseReviewDraft,
} from "./pairwise-review-draft";

export interface StructuralSummary {
  readonly controllerCount: number;
  readonly filledPairCount: number;
  readonly currentPairCount: number;
  readonly attentionCount: number;
}

export function structuralSummary(
  controllers: readonly ControllerFormState[],
  records: readonly PairwiseReviewDraft[],
  validation?: StructuralValidationResult,
): StructuralSummary {
  const ids = controllers.map((controller) => controller.controllerId?.trim() ?? "");
  const duplicateIds = new Set(
    ids.filter(
      (id, index) => id !== "" && ids.indexOf(id) !== index,
    ),
  );
  const controllerAttention = ids.filter(
    (id) => id === "" || duplicateIds.has(id),
  ).length;
  const currentRecords = records.filter((record) => record.state !== "ORPHANED");
  const filledPairCount = currentRecords.filter(
    (record) => record.state === "ACTIVE" && isPairwiseRecordFilled(record),
  ).length;
  const recordAttention = records.filter(
    (record) => record.state !== "ACTIVE" || !isPairwiseRecordFilled(record),
  ).length;
  const validationAttention =
    validation?.status === "INVALID" ? validation.issues.length : 0;

  return {
    controllerCount: controllers.length,
    filledPairCount,
    currentPairCount: currentRecords.length,
    attentionCount:
      controllerAttention + recordAttention + validationAttention,
  };
}

function sourcedResultText(resultQuery: ResultQuery): string {
  if (resultQuery.state === "READY") {
    return `${resultQuery.results.length} sourced result${resultQuery.results.length === 1 ? "" : "s"}`;
  }
  if (resultQuery.state === "LOADING") {
    return "Checking active source";
  }
  return "Not provided by active source";
}

export interface ReadinessSummaryProps {
  readonly controllers: readonly ControllerFormState[];
  readonly records: readonly PairwiseReviewDraft[];
  readonly validation?: StructuralValidationResult;
  readonly resultQuery: ResultQuery;
}

export function ReadinessSummary({
  controllers,
  records,
  validation,
  resultQuery,
}: ReadinessSummaryProps) {
  const summary = structuralSummary(controllers, records, validation);
  const validationText = validation
    ? validation.status === "VALID"
      ? "Valid structure"
      : `${validation.issues.length} structural issue${validation.issues.length === 1 ? "" : "s"}`
    : "Not run";

  return (
    <section className="readiness-summary" aria-labelledby="summary-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Structural completeness only</p>
          <h2 id="summary-heading">Worksheet summary</h2>
        </div>
      </div>
      <div className="summary-grid">
        <div>
          <strong>{summary.controllerCount}</strong>
          <span>controllers in draft</span>
        </div>
        <div>
          <strong>
            {summary.filledPairCount} of {summary.currentPairCount}
          </strong>
          <span>pairwise records filled</span>
        </div>
        <div>
          <strong>{summary.attentionCount}</strong>
          <span>attention items</span>
        </div>
        <div>
          <strong>{validationText}</strong>
          <span>JSON Schema check</span>
        </div>
        <div>
          <strong>{sourcedResultText(resultQuery)}</strong>
          <span>external authority result</span>
        </div>
      </div>
      <p className="summary-boundary">
        Counts describe this local worksheet. No authority outcome is derived here.
      </p>
    </section>
  );
}
