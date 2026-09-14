import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { SourcedResult } from "../core/contracts";
import { SourcedResultCard } from "./SourcedResultCard";

describe("sourced result provenance presentation", () => {
  it("shows authority, exact subject, source, times, and verification metadata", () => {
    const result: SourcedResult = {
      resultType: "controller-independence",
      outcome: "PASS",
      subject: {
        type: "controller-register",
        id: "register-7",
        revision: "rev-3",
        sha256: "a".repeat(64),
      },
      authorityClass: "GOVERNANCE_ASSESSMENT",
      sourceReference: {
        kind: "PUBLIC_CONTRACT",
        repository: "governance/example",
        revision: "assessment-9",
        path: "public/assessment.json",
        sha256: "b".repeat(64),
      },
      issuedAt: "2026-09-13T12:00:00Z",
      retrievedAt: "2026-09-14T08:00:00Z",
      verifierRevision: "verifier-2",
      policyRevision: "policy-5",
      evidenceReferences: ["https://evidence.example.test/item-1"],
      signatureReferences: ["signature:sha256:1234"],
    };
    render(<SourcedResultCard result={result} />);

    const card = screen.getByRole("article", {
      name: "Sourced result controller-independence",
    });
    for (const expected of [
      "GOVERNANCE_ASSESSMENT",
      "register-7",
      "rev-3",
      "assessment-9",
      "2026-09-13T12:00:00Z",
      "2026-09-14T08:00:00Z",
      "verifier-2",
      "policy-5",
      "PASS",
    ]) {
      expect(within(card).getByText(expected)).toBeTruthy();
    }
    expect(card.textContent).toContain("Outcome (as supplied)");
    expect(card.textContent).toContain("not recomputed by this UI");
    expect(card.querySelector("a")).toBeNull();
  });
});
