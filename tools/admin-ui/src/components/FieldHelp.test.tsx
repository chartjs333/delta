import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { HelpLabel, FieldHelp } from "./FieldHelp";
import { fieldHints } from "./field-help-content";
import { setLanguage, t, useLanguage } from "../i18n";

afterEach(() => { act(() => setLanguage("en")); });
describe("localized field help", () => {
  it("opens by keyboard, shows a format example and never edits the input", async () => {
    const user = userEvent.setup();
    render(<HelpLabel htmlFor="ticket">Ticket ID<input id="ticket" defaultValue="my_run" /></HelpLabel>);
    const input = screen.getByRole("textbox", { name: "Ticket ID" }) as HTMLInputElement;
    const button = screen.getByRole("button", { name: "Help: Ticket ID" });
    button.focus(); await user.keyboard("{Enter}");
    expect(screen.getByRole("note").textContent).toContain("presentation_demo_01");
    expect(button.getAttribute("aria-expanded")).toBe("true");
    expect(input.value).toBe("my_run");
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("note")).toBeNull();
    expect(document.activeElement).toBe(button);
  });
  it("updates an open hint in the selected language and closes on outside click", async () => {
    const user = userEvent.setup();
    function Example() { useLanguage(); return <HelpLabel>{t("Profile name")}<input /></HelpLabel>; }
    render(<><Example /><button>Outside</button></>);
    await user.click(screen.getByRole("button", { name: "Help: Profile name" }));
    act(() => setLanguage("ru"));
    expect(screen.getByRole("note").textContent).toContain("Утренняя демонстрация");
    expect(screen.getByRole("note").textContent).not.toContain("Morning demo");
    await user.click(screen.getByRole("button", { name: "Outside" }));
    expect(screen.queryByRole("note")).toBeNull();
  });
  it("does not toggle a checkbox when help is opened", async () => {
    const user = userEvent.setup();
    render(<HelpLabel><input type="checkbox" />Unknown</HelpLabel>);
    await user.click(screen.getByRole("button", { name: "Help: Unknown" }));
    expect((screen.getByRole("checkbox", { name: "Unknown" }) as HTMLInputElement).checked).toBe(false);
  });
  it("has a localized purpose and example for every documented field alias", () => {
    for (const language of ["en", "ru"] as const) {
      act(() => setLanguage(language));
      for (const hint of fieldHints) {
        expect(hint[language][0].length).toBeGreaterThan(20);
        expect(hint[language][1].length).toBeGreaterThan(0);
        for (const field of hint.labels) {
          const view = render(<FieldHelp field={t(field)} />);
          expect(screen.getByRole("button").getAttribute("aria-expanded")).toBe("false");
          view.unmount();
        }
      }
    }
  });
});
