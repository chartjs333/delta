import { describe, expect, it } from "vitest";

import {
  acceptCurrentControllerIds,
  pairKeyFor,
  syncPairwiseReviewDrafts,
  updatePairwiseAnswer,
  updatePairwiseEvidence,
} from "./pairwise-review-draft";

function controllers(count: number) {
  return Array.from({ length: count }, (_, index) => ({
    draftControllerKey: `draft-${index}`,
    controllerId: `controller-${index}`,
  }));
}

describe("pairwise review draft identity and lifecycle", () => {
  it.each([
    [0, 0],
    [1, 0],
    [2, 1],
    [4, 6],
    [100, 4_950],
  ])("derives %i controllers into %i unordered records", (count, pairs) => {
    const records = syncPairwiseReviewDrafts(controllers(count), []);
    expect(records).toHaveLength(pairs);
    expect(new Set(records.map((record) => record.pairKey)).size).toBe(pairs);
  });

  it("keeps a stable pair key when controllers reorder", () => {
    const originalControllers = controllers(3);
    const original = syncPairwiseReviewDrafts(originalControllers, []);
    const reordered = syncPairwiseReviewDrafts(
      [originalControllers[2], originalControllers[0], originalControllers[1]],
      original,
    );
    expect(reordered.map((record) => record.pairKey).sort()).toEqual(
      original.map((record) => record.pairKey).sort(),
    );
    expect(reordered.every((record) => record.state === "ACTIVE")).toBe(true);
  });

  it("marks edited identities stale and retains answers and evidence until explicit acceptance", () => {
    const originalControllers = controllers(2);
    const initial = syncPairwiseReviewDrafts(originalControllers, [])[0];
    const answered = updatePairwiseEvidence(
      updatePairwiseAnswer(initial, "sharedPrivateKey", "NO"),
      "evidence://bound-to-original-ids",
    );
    const changedControllers = [
      originalControllers[0],
      { ...originalControllers[1], controllerId: "controller-renamed" },
    ];

    const stale = syncPairwiseReviewDrafts(changedControllers, [answered])[0];
    expect(stale.state).toBe("STALE");
    expect(stale.pairKey).toBe(initial.pairKey);
    expect(stale.controllerIdSnapshots).toEqual([
      "controller-0",
      "controller-1",
    ]);
    expect(stale.answers.sharedPrivateKey).toBe("NO");
    expect(stale.evidenceReferences).toEqual([
      "evidence://bound-to-original-ids",
    ]);

    const accepted = acceptCurrentControllerIds(stale, changedControllers);
    expect(accepted.state).toBe("ACTIVE");
    expect(accepted.controllerIdSnapshots).toEqual([
      "controller-0",
      "controller-renamed",
    ]);
    expect(accepted.evidenceReferences).toEqual(stale.evidenceReferences);
  });

  it("keeps removed evidence orphaned and creates a new pair for a re-added controller", () => {
    const originalControllers = controllers(2);
    const original = updatePairwiseEvidence(
      syncPairwiseReviewDrafts(originalControllers, [])[0],
      "evidence://must-not-retarget",
    );
    const withoutSecond = syncPairwiseReviewDrafts(
      [originalControllers[0]],
      [original],
    );
    expect(withoutSecond).toHaveLength(1);
    expect(withoutSecond[0].state).toBe("ORPHANED");

    const readded = {
      draftControllerKey: "draft-readded",
      controllerId: originalControllers[1].controllerId,
    };
    const synchronized = syncPairwiseReviewDrafts(
      [originalControllers[0], readded],
      withoutSecond,
    );
    const orphan = synchronized.find((record) => record.pairKey === original.pairKey);
    const replacement = synchronized.find(
      (record) =>
        record.pairKey ===
        pairKeyFor(originalControllers[0].draftControllerKey, readded.draftControllerKey),
    );

    expect(synchronized).toHaveLength(2);
    expect(orphan?.state).toBe("ORPHANED");
    expect(orphan?.evidenceReferences).toEqual(["evidence://must-not-retarget"]);
    expect(replacement?.state).toBe("ACTIVE");
    expect(replacement?.evidenceReferences).toEqual([]);
  });

  it("does not merge blank or duplicate controller IDs", () => {
    const records = syncPairwiseReviewDrafts(
      [
        { draftControllerKey: "draft-a", controllerId: "duplicate" },
        { draftControllerKey: "draft-b", controllerId: "duplicate" },
        { draftControllerKey: "draft-c", controllerId: "" },
      ],
      [],
    );
    expect(records).toHaveLength(3);
    expect(new Set(records.map((record) => record.pairKey)).size).toBe(3);
  });
});
