import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CONTROLLER_REGISTER_SCHEMA } from "../schemas/controller-register";
import { FriendlyValidationPanel } from "./FriendlyValidationPanel";

describe("FriendlyValidationPanel", () => {
  it("maps a field message and retains every machine-readable diagnostic", () => {
    render(
      <FriendlyValidationPanel
        result={{
          authorityClass: "STRUCTURAL_VALIDATION",
          status: "INVALID",
          schema: CONTROLLER_REGISTER_SCHEMA,
          issues: [
            {
              instancePath: "/controllers/0/controller_id",
              schemaPath: "#/$defs/nullableString/type",
              constraint: "type",
              message: "must be string,null",
              params: { type: ["string", "null"] },
            },
          ],
        }}
      />,
    );

    expect(screen.getByText("Controller 1 · Controller ID")).toBeTruthy();
    expect(screen.getByText("Use the expected value type for controller id.")).toBeTruthy();
    const details = screen.getByText("Technical schema details").closest("details");
    expect(details?.hasAttribute("open")).toBe(false);
    expect(details?.textContent).toContain("/controllers/0/controller_id");
    expect(details?.textContent).toContain("#/$defs/nullableString/type");
    expect(details?.textContent).toContain("type");
  });
});
