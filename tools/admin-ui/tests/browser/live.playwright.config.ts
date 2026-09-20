import { defineConfig } from "@playwright/test";

const port = 4176;

export default defineConfig({
  testDir: ".",
  testMatch: "*.live.ts",
  fullyParallel: false,
  reporter: "line",
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    channel: "chrome",
    trace: "retain-on-failure",
    viewport: { width: 1440, height: 900 },
  },
  webServer: {
    command: `npm run preview:live -- --host 127.0.0.1 --port ${port} --strictPort`,
    url: `http://127.0.0.1:${port}/live.html`,
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
