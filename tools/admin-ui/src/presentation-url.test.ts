import { expect, it } from "vitest";
import { presentationUrl } from "./presentation-url";

it("keeps shared Admin links on the external origin, excluding query and hash", () => {
  expect(presentationUrl(new URL("https://example.trycloudflare.com/admin/?lang=ru#/sdk"), "http://127.0.0.1:8870/"))
    .toBe("https://example.trycloudflare.com/");
});
it("redirects the legacy Controller mount to the configured shared app", () => {
  expect(presentationUrl(new URL("http://127.0.0.1:8865/?lang=en#/sdk"), "http://127.0.0.1:8870/"))
    .toBe("http://127.0.0.1:8870/");
});
it("leaves the offline build without a live Presentation link", () => {
  expect(presentationUrl(new URL("https://example.invalid/admin/"))).toBeUndefined();
});
