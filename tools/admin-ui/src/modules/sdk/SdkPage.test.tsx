import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { setLanguage } from "../../i18n";
import { SdkPage } from "./SdkPage";
import example from "./sdk_plugin_example.py?raw";

afterEach(() => { act(() => setLanguage("en")); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it("translates descriptions without resetting the selected SDK contract or code", async () => {
  const user = userEvent.setup();
  render(<SdkPage />);
  await user.click(screen.getByRole("button", { name: "Model plugin" }));
  const code = screen.getByLabelText("sdk_plugin_example.py · ModelPlugin").textContent;
  act(() => setLanguage("ru"));
  expect(screen.getByRole("heading", { name: "Реализуйте ModelPlugin" })).toBeDefined();
  expect(screen.getByLabelText("sdk_plugin_example.py · ModelPlugin").textContent).toBe(code);
  expect(screen.getByRole("button", { name: "Плагин модели" }).getAttribute("aria-pressed")).toBe("true");
});

it("downloads the same complete Python example that the executable checks use", async () => {
  const user = userEvent.setup();
  const create = vi.fn((_blob: Blob) => "blob:example");
  vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: create, revokeObjectURL: vi.fn() }));
  const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  render(<SdkPage />);
  await user.click(screen.getByRole("button", { name: /Download full example/ }));
  expect(create.mock.calls).toHaveLength(1);
  const reader = new FileReader();
  const text = new Promise(resolve => { reader.onload = () => resolve(reader.result); });
  reader.readAsText(create.mock.calls[0][0]);
  expect(await text).toBe(example);
  expect((click.mock.instances[0] as HTMLAnchorElement).download).toBe("sdk_plugin_example.py");
});
