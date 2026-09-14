import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { LocalJsonAdapter } from "../../data/local-json-adapter";
import type { LocalFileGateway } from "../../data/browser-file-gateway";
import type { DocumentEnvelope } from "../../core/contracts";
import { ControllerRegistryForm } from "./ControllerRegistryForm";

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
});
