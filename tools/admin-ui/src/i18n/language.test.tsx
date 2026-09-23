import { act, cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../app/App";
import { LocalJsonAdapter } from "../data/local-json-adapter";
import { LiveIntentBuilder } from "../modules/live-execution/LiveIntentBuilder";
import {
  languageFromSearch,
  languageLink,
  message,
  setLanguage,
  t,
  useLanguage,
} from ".";

afterEach(() => {
  cleanup();
  act(() => setLanguage("en"));
  window.history.replaceState(null, "", "/");
});

function Builder() {
  const language = useLanguage();
  return (
    <>
      <button onClick={() => setLanguage(language === "en" ? "ru" : "en")}>
        Switch
      </button>
      <LiveIntentBuilder />
    </>
  );
}

describe("English/Russian display boundary", () => {
  it("preserves edited intent bytes, digest and expanded preview across language changes", async () => {
    const user = userEvent.setup();
    render(<Builder />);
    await user.clear(screen.getByLabelText("Ticket ID"));
    await user.type(screen.getByLabelText("Ticket ID"), "presentation_ticket");
    await user.click(
      screen.getByRole("button", { name: "View Canonical JSON" }),
    );
    const before = within(
      screen.getByRole("region", { name: "Canonical JSON preview" }),
    ).getByText(/"intent_digest"/).textContent;
    expect(before).toContain("presentation_ticket");
    await user.click(screen.getByRole("button", { name: "Switch" }));
    expect((screen.getByLabelText("ID билета") as HTMLInputElement).value).toBe(
      "presentation_ticket",
    );
    const after = within(
      screen.getByRole("region", { name: "Просмотр канонического JSON" }),
    ).getByText(/"intent_digest"/).textContent;
    expect(after).toBe(before);
    expect(document.documentElement.lang).toBe("ru");
    await user.click(screen.getByRole("button", { name: "Switch" }));
    expect(
      within(
        screen.getByRole("region", { name: "Canonical JSON preview" }),
      ).getByText(/"intent_digest"/).textContent,
    ).toBe(before);
  });

  it("retains controller input and exports identical JSON after switching", async () => {
    const downloads: Uint8Array[] = [];
    const adapter = new LocalJsonAdapter({
      selectJsonFile: vi.fn(),
      downloadNewFile: async (bytes) => {
        downloads.push(bytes);
      },
    });
    const user = userEvent.setup();
    render(<App adapter={adapter} />);
    await user.click(screen.getByRole("button", { name: "New document" }));
    await user.click(screen.getByRole("button", { name: "Add controller" }));
    await user.type(
      screen.getByLabelText("Controller 1 Controller ID"),
      "controller-local",
    );
    await user.click(screen.getByRole("button", { name: "Download new file" }));
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Interface language" }),
      "ru",
    );
    expect(
      (
        screen.getByLabelText(
          "Контроллер 1: ID контроллера",
        ) as HTMLInputElement
      ).value,
    ).toBe("controller-local");
    expect(
      screen.getByRole("heading", { name: "Реестр контроллеров" }),
    ).toBeTruthy();
    await user.click(
      screen.getByRole("button", { name: "Скачать новый файл" }),
    );
    expect(downloads).toHaveLength(2);
    expect(downloads[1]).toEqual(downloads[0]);
  });

  it("carries only supported language choices in links while retaining route and query", () => {
    expect(languageFromSearch("?lang=ru")).toBe("ru");
    expect(languageFromSearch("?lang=de")).toBe("en");
    const link = new URL(
      languageLink("http://127.0.0.1:8865/?x=1#/live-execution", "ru"),
    );
    expect(link.searchParams.get("lang")).toBe("ru");
    expect(link.searchParams.get("x")).toBe("1");
    expect(link.hash).toBe("#/live-execution");
    window.history.replaceState(null, "", "/?x=1#/controllers");
    setLanguage("ru");
    expect(window.location.hash).toBe("#/controllers");
    expect(new URLSearchParams(window.location.search).get("x")).toBe("1");
  });

  it("translates known diagnostics without translating IDs or unknown evidence", () => {
    setLanguage("ru");
    expect(message("Status refreshed: COMPLETED")).toBe(
      "Статус обновлён: COMPLETED",
    );
    expect(
      message(
        "Controller HTTP status is COMPLETED. This local execution status is not a consensus claim.",
      ),
    ).toBe(
      "Статус Controller HTTP: COMPLETED. Это локальное состояние выполнения, а не подтверждение консенсуса.",
    );
    expect(t("Subject ID is required.")).toBe("Укажите ID субъекта.");
    expect(message("unknown diagnostic <script>alert(1)</script>")).toBe(
      "unknown diagnostic <script>alert(1)</script>",
    );
    expect(t("sha256:" + "a".repeat(64))).toBe("sha256:" + "a".repeat(64));
    expect(t('{"state":"COMPLETED"}')).toBe('{"state":"COMPLETED"}');
  });
});
