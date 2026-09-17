import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ControllerExplorer } from "./ControllerExplorer";

describe("dynamic controller list/detail", () => {
  it("paginates arbitrary controller collections with no slot field", async () => {
    const user = userEvent.setup();
    const controllers = Array.from({ length: 31 }, (_, index) => ({
      controller_id: `controller-${index + 1}`,
      status: index % 2 ? "LOCAL_NOTE" : "UNASSIGNED",
      future_field: `<value-${index + 1}>`,
    }));
    render(<ControllerExplorer controllers={controllers} pageSize={25} />);

    const list = screen.getByRole("list", { name: "Controller list" });
    expect(within(list).getAllByRole("button")).toHaveLength(25);
    expect(screen.getByLabelText("Controller count").textContent).toBe("31");
    expect(screen.queryByText("controller-26")).toBeNull();

    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(within(list).getAllByRole("button")).toHaveLength(6);
    await user.click(screen.getByRole("button", { name: /controller-26/u }));

    const detail = screen.getByRole("complementary", { name: "Controller detail" });
    expect(within(detail).getByText("future_field")).toBeTruthy();
    expect(within(detail).getByText("<value-26>")).toBeTruthy();
    expect(detail.querySelector("value-26")).toBeNull();
  });
});
