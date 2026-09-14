import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReadinessSummary } from "./ReadinessSummary";
import {
  pairwiseQuestions,
  syncPairwiseReviewDrafts,
  updatePairwiseAnswer,
} from "./pairwise-review-draft";

const controllers = Array.from({ length: 4 }, (_, index) => ({
  draftControllerKey: `draft-${index}`,
  controllerId: `controller-${index}`,
}));

describe("ReadinessSummary", () => {
  it("reports filled records without turning completion into a verdict", () => {
    const records = syncPairwiseReviewDrafts(controllers, []).map((record) =>
      pairwiseQuestions.reduce(
        (current, question) =>
          updatePairwiseAnswer(current, question.id, "UNKNOWN"),
        record,
      ),
    );

    render(
      <ReadinessSummary
        controllers={controllers}
        records={records}
        resultQuery={{ state: "UNAVAILABLE", results: [] }}
      />,
    );

    const summary = screen.getByRole("region", { name: "Worksheet summary" });
    expect(summary.textContent).toContain("6 of 6pairwise records filled");
    expect(summary.textContent).toContain("Not provided by active source");
    expect(summary.textContent).not.toMatch(
      /\b(?:verified|confirmed|approved|pass|fail)\b/iu,
    );
  });
});
