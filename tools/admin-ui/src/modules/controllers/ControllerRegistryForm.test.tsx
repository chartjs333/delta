import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { LocalJsonAdapter } from "../../data/local-json-adapter";
import type { LocalFileGateway } from "../../data/browser-file-gateway";
import type { DocumentEnvelope } from "../../core/contracts";
import {
  autofillSafeControllerDraft,
  ControllerRegistryForm,
} from "./ControllerRegistryForm";

const unusedGateway: LocalFileGateway = {
  selectJsonFile: async () => {
    throw new Error("not used");
  },
  downloadNewFile: async () => {
    throw new Error("not used");
  },
};

function Harness() {
  const adapter = new LocalJsonAdapter(unusedGateway);
  const [draft, setDraft] = useState<DocumentEnvelope>(() =>
    adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      future_root: { retained: true },
      controllers: [
        {
          controller_id: "controller-a",
          status: "DRAFT",
          future_controller: "retained",
        },
      ],
    }),
  );
  const [keys, setKeys] = useState<readonly string[]>(["draft-a"]);
  let nextKey = keys.length;
  return (
    <ControllerRegistryForm
      draft={draft}
      controllerKeys={keys}
      createControllerKey={() => `draft-${++nextKey}`}
      onChange={(nextDraft, nextKeys) => {
        setDraft(nextDraft);
        setKeys(nextKeys);
      }}
    />
  );
}

function AutofillHarness() {
  const adapter = new LocalJsonAdapter(unusedGateway);
  const [draft, setDraft] = useState<DocumentEnvelope>(() =>
    adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      controllers: [
        {
          controller_id: null,
          signer_id: null,
          status: "",
          identity_type: null,
          accountable_owner_id: null,
          administrative_domain_id: null,
          custody_boundary_id: null,
          custody_kind: null,
          custody_evidence_refs: null,
          public_keys: null,
          independence_answers: null,
          governance_approval: null,
          signing_readiness: null,
          protocol_results: null,
        },
      ],
    }),
  );

  return (
    <>
      <ControllerRegistryForm
        draft={draft}
        controllerKeys={["draft-safe-1"]}
        createControllerKey={() => "unused"}
        onChange={(nextDraft) => setDraft(nextDraft)}
      />
      <output aria-label="Autofill document JSON">
        {JSON.stringify(draft.value)}
      </output>
    </>
  );
}

function autofillDocument(): {
  readonly controllers: readonly Readonly<Record<string, unknown>>[];
} {
  return JSON.parse(
    screen.getByLabelText("Autofill document JSON").textContent ?? "{}",
  ) as {
    readonly controllers: readonly Readonly<Record<string, unknown>>[];
  };
}

describe("ControllerRegistryForm", () => {
  it("edits known paths and manages a dynamic controller collection", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.clear(screen.getByLabelText("Controller 1 Controller ID"));
    await user.type(screen.getByLabelText("Controller 1 Controller ID"), "controller-updated");
    expect(
      (screen.getByLabelText("Controller 1 Controller ID") as HTMLInputElement)
        .value,
    ).toBe("controller-updated");

    await user.click(screen.getByRole("button", { name: "Add controller" }));
    expect(screen.getByLabelText("Controller draft count").textContent).toBe("2");
    expect(
      (screen.getByLabelText("Controller 2 Status") as HTMLInputElement).value,
    ).toBe("DRAFT");

    await user.click(
      screen.getByRole("button", { name: "Remove controller 2" }),
    );
    expect(screen.getByLabelText("Controller draft count").textContent).toBe("1");
  });

  it("bounds a large controller form to one page", () => {
    const adapter = new LocalJsonAdapter(unusedGateway);
    const draft = adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      controllers: Array.from({ length: 101 }, (_, index) => ({
        controller_id: `controller-${index}`,
      })),
    });
    render(
      <ControllerRegistryForm
        draft={draft}
        controllerKeys={Array.from({ length: 101 }, (_, index) => `draft-${index}`)}
        createControllerKey={() => "unused"}
        onChange={() => undefined}
      />,
    );

    expect(screen.getAllByRole("group", { name: /Controller \d+/u })).toHaveLength(10);
    expect(screen.getByText("Page 1 of 11")).toBeTruthy();
  });

  it("autofills only blank whitelisted draft fields after an explicit action", async () => {
    const user = userEvent.setup();
    render(<AutofillHarness />);

    expect(
      (screen.getByLabelText("Controller 1 Controller ID") as HTMLInputElement)
        .value,
    ).toBe("");
    expect(autofillDocument().controllers[0]?.governance_approval).toBeNull();

    await user.click(
      screen.getByRole("button", {
        name: "Autofill safe fields for controller 1",
      }),
    );

    const controller = autofillDocument().controllers[0];
    expect(controller?.controller_id).toBe("draft-controller:draft-safe-1");
    expect(controller?.signer_id).toBe("draft-signer:draft-safe-1");
    expect(controller?.status).toBe("DRAFT");
    expect(
      screen.getByText("Auto-filled: Controller ID, Signer ID, Status."),
    ).toBeTruthy();

    for (const prohibitedField of [
      "identity_type",
      "accountable_owner_id",
      "administrative_domain_id",
      "custody_boundary_id",
      "custody_kind",
      "custody_evidence_refs",
      "public_keys",
      "independence_answers",
      "governance_approval",
      "signing_readiness",
      "protocol_results",
    ]) {
      expect(controller?.[prohibitedField]).toBeNull();
    }

    const editableValues = [
      ["Controller 1 Controller ID", "manual-controller"],
      ["Controller 1 Signer ID", "manual-signer"],
      ["Controller 1 Status", "REVIEW"],
    ] as const;
    for (const [label, value] of editableValues) {
      const input = screen.getByLabelText(label);
      await user.clear(input);
      await user.type(input, value);
    }
    expect(autofillDocument().controllers[0]).toMatchObject({
      controller_id: "manual-controller",
      signer_id: "manual-signer",
      status: "REVIEW",
    });
  });

  it("does not overwrite existing technical values", () => {
    const adapter = new LocalJsonAdapter(unusedGateway);
    const draft = adapter.createDocument({
      document_type: "CONTROLLER_GOVERNANCE_REGISTER",
      document_version: "1.0.0",
      controllers: [
        {
          controller_id: "manual-controller",
          signer_id: "manual-signer",
          status: "ACTIVE",
        },
      ],
    });

    const result = autofillSafeControllerDraft(draft, 0, "draft-safe-1");

    expect(result.autofilledFields).toEqual([]);
    expect(result.draft).toBe(draft);
  });
});
