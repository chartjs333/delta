import { useEffect, useSyncExternalStore } from "react";
import russian from "./ru.json";

export type Language = "en" | "ru";
const messages: Readonly<Record<string, string>> = russian;
const listeners = new Set<() => void>();
export function isLanguage(value: unknown): value is Language {
  return value === "en" || value === "ru";
}
export function languageFromSearch(search: string): Language {
  const query = new URLSearchParams(search).get("lang");
  if (isLanguage(query)) return query;
  return "en";
}
let language = languageFromSearch(window.location.search);
function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
export function setLanguage(next: Language): void {
  if (!isLanguage(next)) return;
  language = next;
  const url = new URL(window.location.href);
  url.searchParams.set("lang", next);
  window.history.replaceState(null, "", url);
  for (const listener of listeners) listener();
}
export function useLanguage(): Language {
  const selected = useSyncExternalStore<Language>(
    subscribe,
    () => language,
    () => "en",
  );
  useEffect(() => {
    document.documentElement.lang = selected;
    document.title =
      selected === "ru"
        ? "Delta Admin UI · Панель управления"
        : "Delta Admin UI";
  }, [selected]);
  return selected;
}

// Display-only lookup. Call at render time, never while constructing canonical
// intent documents, IDs, receipt payloads or downloaded evidence.
export function t(
  text: string,
  values: Readonly<Record<string, string | number>> = {},
): string {
  const template = language === "ru" ? (messages[text] ?? text) : text;
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    String(values[key] ?? match),
  );
}

const messagePatterns = Object.keys(messages)
  .filter((key) => /\{\w+\}/.test(key))
  .sort((a, b) => b.length - a.length)
  .map((key) => {
    const names: string[] = [];
    const parts = key.split(/(\{\w+\})/);
    const pattern = parts
      .map((part) => {
        if (/^\{\w+\}$/.test(part)) {
          const name = part.slice(1, -1);
          names.push(name);
          return name === "number" || name === "count" ? "(\\d+)" : "(.*?)";
        }
        return part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      })
      .join("");
    return { key, names, pattern: new RegExp(`^${pattern}$`, "s") };
  });

// Only known UI messages are translated. Unknown diagnostics remain verbatim.
export function message(text: string): string {
  if (language === "en" || Object.hasOwn(messages, text)) return t(text);
  for (const entry of messagePatterns) {
    const match = entry.pattern.exec(text);
    if (!match) continue;
    const values = Object.fromEntries(
      entry.names.map((name, index) => {
        const value = match[index + 1];
        return [
          name,
          name === "field"
            ? t(value)
            : name === "fields"
              ? value
                  .split(", ")
                  .map((field) => t(field))
                  .join(", ")
              : value,
        ];
      }),
    );
    return t(entry.key, values);
  }
  return text;
}

export function languageLink(address: string, selected: Language): string {
  const url = new URL(address);
  url.searchParams.set("lang", selected);
  return url.href;
}
