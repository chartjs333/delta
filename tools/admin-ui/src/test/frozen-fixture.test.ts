import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import provenance from "../../test-data/pr29/provenance.json";

const fixturePath = resolve(
  process.cwd(),
  "test-data/pr29/campaign02-controller-register.template.json",
);

describe("frozen PR #29 worksheet fixture", () => {
  it("matches its exact source byte identity", async () => {
    const bytes = await readFile(fixturePath);
    expect(bytes.byteLength).toBe(provenance.source.byte_length);
    expect(createHash("sha256").update(bytes).digest("hex")).toBe(
      provenance.source.sha256,
    );
    expect(provenance.source.git_blob_sha).toBe(
      "496ea3a9b081040e2670c7d027a63069516496f6",
    );
  });

  it("is explicitly non-normative, test-only, and offline", () => {
    expect(provenance.authority).toBe("NON_NORMATIVE_FIXTURE_INPUT");
    expect(provenance.runtime_policy).toEqual({
      live_pull_request_access: false,
      network_fetch: false,
      test_data_only: true,
    });
  });
});
