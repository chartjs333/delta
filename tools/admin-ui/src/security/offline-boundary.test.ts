import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { describe, expect, it } from "vitest";

const execFileAsync = promisify(execFile);

describe("browser-local product boundary", () => {
  it("passes the executable offline/static audit", async () => {
    const { stdout } = await execFileAsync(
      process.execPath,
      ["scripts/check-offline-boundary.mjs"],
      { cwd: process.cwd() },
    );
    const result = JSON.parse(stdout) as {
      status: string;
      checks: Record<string, boolean>;
      violations: unknown[];
    };

    expect(result.status).toBe("PASS");
    expect(result.violations).toEqual([]);
    expect(result.checks).toEqual({
      analytics_payload: false,
      automatic_network_request: false,
      backend_dependency: false,
      credential_flow: false,
      live_pr_read: false,
      login_flow: false,
      static_browser_build: true,
    });
  });
});
