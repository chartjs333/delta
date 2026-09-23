import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { setLanguage } from "../../i18n";
import { GuidePage } from "./GuidePage";

afterEach(() => {
  act(() => setLanguage("en"));
  window.history.replaceState(null, "", "/");
  vi.restoreAllMocks();
});

it("navigates all seven slides by keyboard with bounded ends and preserves link context", async () => {
  window.history.replaceState(null, "", "/admin/?lang=en&execution=example#/guide");
  const user = userEvent.setup();
  render(<GuidePage />);
  expect((screen.getByRole("button", { name: /Previous/ }) as HTMLButtonElement).disabled).toBe(true);
  await user.keyboard("{ArrowRight}");
  expect(screen.getByRole("status").textContent).toContain("Slide 2 of 7");
  await user.keyboard("{End}{ArrowRight}");
  expect(screen.getByRole("status").textContent).toContain("Slide 7 of 7");
  expect((screen.getByRole("button", { name: /^Next/ }) as HTMLButtonElement).disabled).toBe(true);
  expect(window.location.search).toBe("?lang=en&execution=example&slide=7");
  expect(window.location.hash).toBe("#/guide");
  await user.keyboard("{Home}{ArrowLeft}");
  expect(screen.getByRole("status").textContent).toContain("Slide 1 of 7");
});

it("restores a shared slide, switches language in place and shows arithmetic corrections", async () => {
  window.history.replaceState(null, "", "/admin/?lang=en&slide=5#/guide");
  const user = userEvent.setup();
  render(<GuidePage />);
  const image = screen.getByRole("img").getAttribute("src");
  expect(screen.getByRole("status").textContent).toContain("Slide 5 of 7");
  expect(screen.getByText(/Correct values: shard 1/).textContent).toContain("130/6");
  act(() => setLanguage("ru"));
  expect(screen.getByRole("heading", { name: "Как работает DeltaReduce" })).toBeDefined();
  expect(screen.getByRole("status").textContent).toContain("Слайд 5 из 7");
  expect(screen.getByRole("img").getAttribute("src")).toBe(image);
  expect(screen.getByText(/В исходном рисунке три арифметические ошибки/)).toBeDefined();
  await user.click(screen.getByRole("button", { name: /^Слайд 3:/ }));
  expect(screen.getByRole("status").textContent).toContain("Слайд 3 из 7");
  expect(screen.getByRole("link", { name: /Открыть исходное/ }).getAttribute("href")).toBe(screen.getByRole("img").getAttribute("src"));
});

it("recovers from a failed image and explains unavailable fullscreen without losing navigation", async () => {
  const user = userEvent.setup();
  render(<GuidePage />);
  fireEvent.error(screen.getByRole("img"));
  expect(screen.getByRole("alert").textContent).toContain("could not be loaded");
  await user.click(screen.getByRole("button", { name: "Retry image" }));
  expect(screen.getByRole("img")).toBeDefined();
  await user.click(screen.getByRole("button", { name: /Full screen/ }));
  expect(screen.getByText(/Full screen is unavailable/)).toBeDefined();
  await user.click(screen.getByRole("button", { name: /^Next/ }));
  expect(screen.getByRole("img").getAttribute("alt")).toContain("Slide 2");
});

it("rejects invalid slide parameters and does not steal modified shortcuts", async () => {
  window.history.replaceState(null, "", "/admin/?slide=999#/guide");
  const user = userEvent.setup();
  render(<GuidePage />);
  await user.keyboard("{Control>}{ArrowRight}{/Control}");
  expect(screen.getByRole("status").textContent).toContain("Slide 1 of 7");
});
