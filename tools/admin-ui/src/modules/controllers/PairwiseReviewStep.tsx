import { useEffect, useMemo, useState } from "react";

import { InertText } from "../../components/InertText";
import type { ControllerFormState } from "./ControllerRegistryForm";
import {
  acceptCurrentControllerIds,
  pairwiseQuestions,
  type PairwiseAnswer,
  type PairwiseReviewDraft,
  updatePairwiseAnswer,
  updatePairwiseEvidence,
} from "./pairwise-review-draft";

export interface PairwiseReviewStepProps {
  readonly controllers: readonly ControllerFormState[];
  readonly records: readonly PairwiseReviewDraft[];
  readonly onChange: (records: readonly PairwiseReviewDraft[]) => void;
}

const answers: readonly Exclude<PairwiseAnswer, "UNANSWERED">[] = [
  "YES",
  "NO",
  "UNKNOWN",
];

function displayId(value: string | null): string {
  return value?.trim() ? value : "ID not provided";
}

export function PairwiseReviewStep({
  controllers,
  records,
  onChange,
}: PairwiseReviewStepProps) {
  const [recordIndex, setRecordIndex] = useState(0);
  const current = records[recordIndex];
  const controllerByKey = useMemo(
    () =>
      new Map(
        controllers.map((controller) => [
          controller.draftControllerKey,
          controller,
        ]),
      ),
    [controllers],
  );

  useEffect(() => {
    setRecordIndex((index) => Math.min(index, Math.max(0, records.length - 1)));
  }, [records.length]);

  function replaceCurrent(next: PairwiseReviewDraft): void {
    onChange(
      records.map((record, index) => (index === recordIndex ? next : record)),
    );
  }

  return (
    <section className="pairwise-step" aria-labelledby="pairwise-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Local answer worksheet</p>
          <h2 id="pairwise-heading">Pairwise records</h2>
        </div>
        <span className="count-badge" aria-label="Pairwise record count">
          {records.length}
        </span>
      </div>
      <p>
        Record answers and evidence references only. The UI does not calculate an
        independence conclusion, approval, or protocol result.
      </p>

      {!current ? (
        <div className="empty-state" role="status">
          Add at least two controllers to create a pairwise record.
        </div>
      ) : (
        <div className="pairwise-wizard">
          <div className="pairwise-progress" aria-live="polite">
            Record {recordIndex + 1} of {records.length}
          </div>
          <article className={`pairwise-card pairwise-${current.state.toLowerCase()}`}>
            <header>
              <h3>
                <InertText value={displayId(current.controllerIdSnapshots[0])} />
                {" ↔ "}
                <InertText value={displayId(current.controllerIdSnapshots[1])} />
              </h3>
              <span className="lifecycle-badge">{current.state}</span>
            </header>

            {current.state === "STALE" ? (
              <div className="attention-box" role="alert">
                A controller ID changed. Existing answers and evidence remain bound
                to the original draft keys.
                <span>
                  Current IDs: {" "}
                  <InertText
                    value={displayId(
                      controllerByKey.get(current.memberKeys[0])?.controllerId ?? null,
                    )}
                  />
                  {" ↔ "}
                  <InertText
                    value={displayId(
                      controllerByKey.get(current.memberKeys[1])?.controllerId ?? null,
                    )}
                  />
                </span>
                <button
                  type="button"
                  onClick={() =>
                    replaceCurrent(
                      acceptCurrentControllerIds(current, controllers),
                    )
                  }
                >
                  Review and accept current IDs
                </button>
              </div>
            ) : null}
            {current.state === "ORPHANED" ? (
              <div className="attention-box" role="alert">
                A referenced controller was removed. This record is retained and is
                not included as an active export record.
                <button
                  type="button"
                  onClick={() =>
                    onChange(records.filter((_, index) => index !== recordIndex))
                  }
                >
                  Explicitly discard orphaned record
                </button>
              </div>
            ) : null}

            <div className="pairwise-questions">
              {pairwiseQuestions.map((question) => (
                <fieldset key={question.id}>
                  <legend>{question.label}</legend>
                  <div className="answer-options">
                    {answers.map((answer) => (
                      <label key={answer}>
                        <input
                          checked={current.answers[question.id] === answer}
                          disabled={current.state !== "ACTIVE"}
                          name={`${current.pairKey}-${question.id}`}
                          type="radio"
                          value={answer}
                          onChange={() =>
                            replaceCurrent(
                              updatePairwiseAnswer(current, question.id, answer),
                            )
                          }
                        />
                        {answer === "YES"
                          ? "Yes"
                          : answer === "NO"
                            ? "No"
                            : "Unknown"}
                      </label>
                    ))}
                  </div>
                </fieldset>
              ))}
            </div>

            <label className="form-field">
              <span>Evidence references, one per line</span>
              <textarea
                aria-label="Evidence references"
                disabled={current.state !== "ACTIVE"}
                rows={3}
                value={current.evidenceReferences.join("\n")}
                onChange={(event) =>
                  replaceCurrent(
                    updatePairwiseEvidence(current, event.currentTarget.value),
                  )
                }
              />
            </label>

            <p className="field-help">
              Session-local worksheet data is not added to exported JSON without a
              reviewed mapping supported by the selected schema.
            </p>
          </article>

          <div className="wizard-navigation" aria-label="Pairwise record navigation">
            <button
              disabled={recordIndex === 0}
              type="button"
              onClick={() => setRecordIndex((index) => index - 1)}
            >
              Previous pair
            </button>
            <button
              disabled={recordIndex >= records.length - 1}
              type="button"
              onClick={() => setRecordIndex((index) => index + 1)}
            >
              Next pair
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
