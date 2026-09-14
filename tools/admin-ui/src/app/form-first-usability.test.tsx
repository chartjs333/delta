import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { LocalFileGateway } from "../data/browser-file-gateway";
import { LocalJsonAdapter } from "../data/local-json-adapter";
import { App } from "./App";

describe("non-technical form-first usability path", () => {
  it("completes controllers, pairwise records, validation, and export without opening JSON", async () => {
    const downloads: { bytes: Uint8Array; name: string }[] = [];
    const gateway: LocalFileGateway = {
      selectJsonFile: async () => {
        throw new Error("not used");
      },
      downloadNewFile: async (bytes, name) => {
        downloads.push({ bytes, name });
      },
    };
    const user = userEvent.setup();
    render(<App adapter={new LocalJsonAdapter(gateway)} />);

    await user.click(screen.getByRole("button", { name: "New document" }));
    for (let index = 1; index <= 4; index += 1) {
      await user.click(screen.getByRole("button", { name: "Add controller" }));
      await user.type(
        screen.getByLabelText(`Controller ${index} Controller ID`),
        `controller-${index}`,
      );
    }

    const pairwise = screen.getByRole("region", { name: "Pairwise records" });
    expect(within(pairwise).getByLabelText("Pairwise record count").textContent).toBe("6");
    for (let pair = 0; pair < 6; pair += 1) {
      const acceptIds = within(pairwise).queryByRole("button", {
        name: "Review and accept current IDs",
      });
      if (acceptIds) await user.click(acceptIds);
      const questions = within(pairwise).getAllByRole("group");
      await user.click(within(questions[0]).getByLabelText("Yes"));
      await user.click(within(questions[1]).getByLabelText("No"));
      await user.click(within(questions[2]).getByLabelText("Unknown"));
      if (pair < 5) {
        await user.click(
          within(pairwise).getByRole("button", { name: "Next pair" }),
        );
      }
    }

    expect(
      screen.getByRole("region", { name: "Worksheet summary" }).textContent,
    ).toContain("6 of 6pairwise records filled");
    const advancedDetails = screen
      .getByText("Advanced JSON (read-only)")
      .closest("details");
    expect(advancedDetails?.hasAttribute("open")).toBe(false);

    await user.click(screen.getByRole("button", { name: "Validate structure" }));
    expect(await screen.findByRole("heading", { name: "VALID" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Download new file" }));

    expect(downloads).toHaveLength(1);
    expect(downloads[0].name).toBe("controller-register.new.export.json");
    const exported = JSON.parse(new TextDecoder().decode(downloads[0].bytes)) as {
      controllers: unknown[];
      pairwise_independence_reviews?: unknown;
    };
    expect(exported.controllers).toHaveLength(4);
    expect(exported.pairwise_independence_reviews).toBeUndefined();
  }, 15_000);
});
