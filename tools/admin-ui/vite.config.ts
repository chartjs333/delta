import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => {
  const liveBuild = mode === "live";
  return {
    base: "./",
    build: {
      emptyOutDir: true,
      modulePreload: { polyfill: false },
      outDir: liveBuild ? "dist-live" : "dist",
      rollupOptions: {
        input: fileURLToPath(
          new URL(liveBuild ? "./live.html" : "./index.html", import.meta.url),
        ),
      },
    },
    plugins: [react()],
    test: {
      environment: "jsdom",
      include: [
        "src/**/*.test.ts",
        "src/**/*.test.tsx",
        "src-live/**/*.test.ts",
        "src-live/**/*.test.tsx",
      ],
      setupFiles: ["./src/test/setup.ts"],
      testTimeout: 10000,
    },
  };
});
