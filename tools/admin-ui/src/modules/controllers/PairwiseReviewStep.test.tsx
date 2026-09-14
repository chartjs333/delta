import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { PairwiseReviewStep } from "./PairwiseReviewStep";
import {
  syncPairwiseReviewDrafts,
  type PairwiseReviewDraft,
} from "./pairwise-review-draft";

const controllers = [
  { draftControllerKey: "draft-a", controllerId: "controller-a" },
  { draftControllerKey: "draft-b", controllerId: "controller-b" },
] as const;

function Harness() {
  const [records, setRecords] = useState<readonly PairwiseReviewDraft[]>(() =>
    syncPairwiseReviewDrafts(controllers, []),
  );
  return (
    <PairwiseReviewStep
      controllers={controllers}
      records={records}
      onChange={setRecords}
    />
  );
}

describe("PairwiseReviewStep", () => {
  it("records tri-state answers and inert evidence without a local verdict", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const questions = screen.getAllByRole("group");
    await user.click(within(questions[0]).getByLabelText("Yes"));
    await user.click(within(questions[1]).getByLabelText("No"));
    await user.click(within(questions[2]).getByLabelText("Unknown"));
    await user.type(
      screen.getByLabelText("Evidence references"),
      "evidence://review/one",
    );

    expect((screen.getByLabelText("Evidence references") as HTMLTextAreaElement).value)
      .toBe("evidence://review/one");
    expect(screen.getByRole("region", { name: "Pairwise records" }).textContent)
      .not.toMatch(/\b(?:PASS|FAIL|approved)\b/iu);
  });
});
