import { defineConfig } from "@playwright/test";

const port = 4175;

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  fullyParallel: false,
  reporter: "line",
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    channel: "chrome",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `npm run preview -- --host 127.0.0.1 --port ${port} --strictPort`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: false,
    timeout: 30_000,
  },
  projects: [
    {
      name: "desktop-chrome",
      use: { viewport: { width: 1440, height: 900 } },
    },
    {
      name: "mobile-chrome",
      use: { viewport: { width: 390, height: 844 } },
    },
  ],
});
