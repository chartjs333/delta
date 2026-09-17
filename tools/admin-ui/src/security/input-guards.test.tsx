import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InertText } from "../components/InertText";
import { AdminUiError } from "../core/errors";
import { INPUT_LIMITS, parseUntrustedJson } from "./input-guards";
import { allowExplicitHttpsUrl } from "./safe-url";

const encode = (value: string) => new TextEncoder().encode(value);

function expectCode(action: () => unknown, code: AdminUiError["code"]): void {
  try {
    action();
    throw new Error("Expected a typed error");
  } catch (error) {
    expect(error).toBeInstanceOf(AdminUiError);
    expect((error as AdminUiError).code).toBe(code);
  }
}

describe("hostile JSON input limits", () => {
  it("accepts exactly 5 MiB and rejects one byte more before parsing", () => {
    const atLimit = encode(`{}${" ".repeat(INPUT_LIMITS.fileBytes - 2)}`);
    expect(parseUntrustedJson(atLimit).value).toEqual({});
    const overLimit = new Uint8Array(INPUT_LIMITS.fileBytes + 1);
    expectCode(() => parseUntrustedJson(overLimit), "INPUT_LIMIT_EXCEEDED");
  });

  it("accepts 64 container levels and rejects 65", () => {
    const nested = (depth: number) => `${"[".repeat(depth)}0${"]".repeat(depth)}`;
    expect(parseUntrustedJson(encode(nested(64))).value).toBeTruthy();
    expectCode(
      () => parseUntrustedJson(encode(nested(65))),
      "INPUT_LIMIT_EXCEEDED",
    );
  });

  it("accepts 100,000 aggregate nodes and rejects 100,001", () => {
    const arrayJson = (values: number) => `[${"0,".repeat(values - 1)}0]`;
    expect(
      (parseUntrustedJson(encode(arrayJson(INPUT_LIMITS.nodes - 1))).value as
        | readonly unknown[]
        | undefined)?.length,
    ).toBe(INPUT_LIMITS.nodes - 1);
    expectCode(
      () => parseUntrustedJson(encode(arrayJson(INPUT_LIMITS.nodes))),
      "INPUT_LIMIT_EXCEEDED",
    );
  });

  it("enforces the individual UTF-8 string byte limit", () => {
    const atLimit = `"${"a".repeat(INPUT_LIMITS.stringBytes)}"`;
    expect(parseUntrustedJson(encode(atLimit)).value).toHaveLength(
      INPUT_LIMITS.stringBytes,
    );
    const overLimit = `"${"a".repeat(INPUT_LIMITS.stringBytes + 1)}"`;
    expectCode(
      () => parseUntrustedJson(encode(overLimit)),
      "INPUT_LIMIT_EXCEEDED",
    );
  });

  it("enforces the URL character limit", () => {
    const atLimit = `https://${"a".repeat(INPUT_LIMITS.urlCharacters - 8)}`;
    expect(parseUntrustedJson(encode(JSON.stringify(atLimit))).value).toBe(atLimit);
    const overLimit = `${atLimit}a`;
    expectCode(
      () => parseUntrustedJson(encode(JSON.stringify(overLimit))),
      "INPUT_LIMIT_EXCEEDED",
    );
  });

  it("rejects archive signatures and malformed UTF-8 without crashing", () => {
    expectCode(
      () => parseUntrustedJson(new Uint8Array([0x50, 0x4b, 0x03, 0x04])),
      "DOCUMENT_MALFORMED",
    );
    expectCode(
      () => parseUntrustedJson(new Uint8Array([0xc3, 0x28])),
      "DOCUMENT_MALFORMED",
    );
  });

  it("never decodes Base64-looking content", () => {
    const base64 = "PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==";
    expect(parseUntrustedJson(encode(JSON.stringify(base64))).value).toBe(base64);
  });

  it("supports repeated cancellation and clean recovery", () => {
    const controller = new AbortController();
    controller.abort();
    for (let attempt = 0; attempt < 3; attempt += 1) {
      expectCode(
        () => parseUntrustedJson(encode("{}"), controller.signal),
        "VALIDATION_CANCELLED",
      );
    }
    expect(parseUntrustedJson(encode("{}"))).toEqual({ text: "{}", value: {} });
  });
});

describe("inert strings and explicit URL actions", () => {
  it("renders HTML, script, SVG, and event-handler text inertly", () => {
    const hostile = '<script>alert(1)</script><svg onload="alert(2)"></svg>';
    const { container } = render(<InertText value={hostile} />);
    expect(screen.getByText(hostile)).toBeTruthy();
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("svg")).toBeNull();
  });

  it("requires explicit action and allows only credential-free HTTPS", () => {
    expectCode(
      () => allowExplicitHttpsUrl("https://example.test", false),
      "OPERATION_UNSUPPORTED",
    );
    expectCode(
      () => allowExplicitHttpsUrl("javascript:alert(1)", true),
      "OPERATION_UNSUPPORTED",
    );
    expectCode(
      () => allowExplicitHttpsUrl("data:text/html,bad", true),
      "OPERATION_UNSUPPORTED",
    );
    expectCode(
      () => allowExplicitHttpsUrl("https://user:secret@example.test", true),
      "OPERATION_UNSUPPORTED",
    );
    expect(allowExplicitHttpsUrl("https://example.test/path", true).hostname).toBe(
      "example.test",
    );
  });
});
