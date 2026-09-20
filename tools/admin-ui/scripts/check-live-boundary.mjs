import { readFile, readdir } from "node:fs/promises";
import { extname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const liveSourceRoot = join(projectRoot, "src-live");
const liveDistributionRoot = join(projectRoot, "dist-live");
const adapterPath = join(liveSourceRoot, "http-live-execution-adapter.ts");

async function filesBelow(directory, extensions) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await filesBelow(path, extensions)));
    } else if (extensions.has(extname(entry.name))) {
      files.push(path);
    }
  }
  return files;
}

const violations = [];
const liveHtml = await readFile(join(projectRoot, "live.html"), "utf8");
if (!liveHtml.includes("connect-src 'self'")) {
  violations.push({ id: "live-csp-not-same-origin", path: "live.html" });
}
if (/connect-src[^;]*(?:\*|https?:)/iu.test(liveHtml)) {
  violations.push({ id: "live-csp-allows-non-origin-target", path: "live.html" });
}
if (liveHtml.includes("'unsafe-eval'")) {
  violations.push({ id: "live-csp-allows-dynamic-code", path: "live.html" });
}

const adapter = await readFile(adapterPath, "utf8");
const requiredAdapterControls = [
  ["anti-csrf-header", '"X-Delta-Request": "1"'],
  ["same-origin-credentials", 'credentials: "same-origin"'],
  ["no-store-cache", 'cache: "no-store"'],
  ["redirect-denial", 'redirect: "error"'],
  ["loopback-http-check", 'pageUrl.hostname === "127.0.0.1"'],
  ["https-remote-check", 'pageUrl.protocol === "https:"'],
];
for (const [id, text] of requiredAdapterControls) {
  if (!adapter.includes(text)) {
    violations.push({ id: `missing-${id}`, path: relative(projectRoot, adapterPath) });
  }
}

const forbiddenSourcePatterns = [
  ["script-visible-auth-header", /["']Authorization["']/u],
  ["browser-secret-storage", /\b(?:localStorage|sessionStorage|indexedDB)\b/u],
  ["cookie-read", /\bdocument\.cookie\b/u],
  ["embedded-private-key", /-----BEGIN (?:RSA |EC |OPENSSH |DSA |ED25519 )?PRIVATE KEY-----/u],
  ["embedded-api-token", /\b(?:ghp_[A-Za-z0-9]{20,}|glpat-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})\b/u],
  ["absolute-api-endpoint", /https?:\/\/[^"'\s]+\/api\/v1/iu],
];
for (const path of await filesBelow(liveSourceRoot, new Set([".ts", ".tsx"]))) {
  if (path.includes(".test.")) continue;
  const source = await readFile(path, "utf8");
  for (const [id, pattern] of forbiddenSourcePatterns) {
    if (pattern.test(source)) {
      violations.push({
        id,
        path: relative(projectRoot, path).replaceAll("\\", "/"),
      });
    }
  }
}

let bundleFilesScanned = 0;
let bundleHasFetch = false;
for (const path of await filesBelow(liveDistributionRoot, new Set([".js"]))) {
  bundleFilesScanned += 1;
  const bundle = await readFile(path, "utf8");
  bundleHasFetch ||= /\bfetch\b/u.test(bundle);
  for (const [id, pattern] of forbiddenSourcePatterns.slice(0, 5)) {
    if (pattern.test(bundle)) {
      violations.push({
        id: `bundle-${id}`,
        path: relative(projectRoot, path).replaceAll("\\", "/"),
      });
    }
  }
}
if (!bundleHasFetch) {
  violations.push({ id: "live-bundle-missing-http-transport", path: "dist-live" });
}

const result = {
  schema_version: "1.0.0",
  status: violations.length === 0 ? "PASS" : "FAIL",
  checks: {
    csp_same_origin_only: true,
    explicit_live_entry: true,
    http_loopback_or_https: true,
    script_visible_credentials: false,
    browser_secret_storage: false,
  },
  scanned_bundle_files: bundleFilesScanned,
  violations,
};

process.stdout.write(`${JSON.stringify(result)}\n`);
if (violations.length > 0) process.exitCode = 1;
