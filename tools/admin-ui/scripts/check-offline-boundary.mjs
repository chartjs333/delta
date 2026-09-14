import { readFile, readdir } from "node:fs/promises";
import { extname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const sourceRoot = join(projectRoot, "src");
const distributionRoot = join(projectRoot, "dist");

const forbiddenSourcePatterns = [
  ["automatic-fetch", /\bfetch\s*\(/u],
  ["xml-http-request", /\bXMLHttpRequest\b/u],
  ["web-socket", /\bWebSocket\b/u],
  ["event-source", /\bEventSource\b/u],
  ["beacon", /\bsendBeacon\b/u],
  ["service-worker", /\bserviceWorker\b/u],
  ["browser-credential-store", /\b(?:localStorage|sessionStorage|indexedDB)\b/u],
  ["cookie-access", /\bdocument\.cookie\b/u],
  ["authorization-header", /["']Authorization["']/u],
  ["password-control", /type\s*=\s*["']password["']/iu],
  ["raw-html", /\bdangerouslySetInnerHTML\b/u],
  ["node-network-server", /node:(?:http|https|http2|net|tls)/u],
  ["analytics-sdk", /\b(?:analytics|telemetry|sentry|segment|posthog)\s*\./iu],
  ["live-pr-29", /github\.com\/chartjs333\/delta\/pull\/29/iu],
  ["github-api", /api\.github\.com/iu],
];

const allowedRuntimeDependencies = new Set(["ajv", "react", "react-dom"]);
const backendOrTelemetryPackages = /(?:express|fastify|koa|nestjs|next|socket\.io|axios|sentry|segment|posthog|analytics)/iu;
const forbiddenBundlePattern = /\b(?:fetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon)\b/u;
const dynamicCodePattern = /\b(?:eval\s*\(|new\s+Function\s*\(|Function\s*\(\s*["'`])/u;

async function sourceFiles(
  directory,
  allowedExtensions = new Set([".ts", ".tsx", ".css"]),
) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== "test") {
        files.push(...(await sourceFiles(path, allowedExtensions)));
      }
      continue;
    }
    if (
      allowedExtensions.has(extname(entry.name)) &&
      !entry.name.includes(".test.")
    ) {
      files.push(path);
    }
  }
  return files;
}

const violations = [];
for (const path of await sourceFiles(sourceRoot)) {
  const content = await readFile(path, "utf8");
  for (const [id, pattern] of forbiddenSourcePatterns) {
    if (pattern.test(content)) {
      violations.push({ id, path: relative(projectRoot, path).replaceAll("\\", "/") });
    }
  }
}

const packageDocument = JSON.parse(
  await readFile(join(projectRoot, "package.json"), "utf8"),
);
for (const dependency of Object.keys(packageDocument.dependencies ?? {})) {
  if (!allowedRuntimeDependencies.has(dependency) || backendOrTelemetryPackages.test(dependency)) {
    violations.push({ id: "runtime-dependency-not-allowlisted", path: dependency });
  }
}

const indexHtml = await readFile(join(projectRoot, "index.html"), "utf8");
if (!indexHtml.includes("connect-src 'none'")) {
  violations.push({ id: "csp-allows-network-connections", path: "index.html" });
}
if (indexHtml.includes("'unsafe-eval'")) {
  violations.push({ id: "csp-allows-dynamic-code", path: "index.html" });
}
if (/<(?:script|link|img)\b[^>]*(?:src|href)=["']https?:/iu.test(indexHtml)) {
  violations.push({ id: "external-index-resource", path: "index.html" });
}

let bundleFilesScanned = 0;
try {
  const distributionFiles = await sourceFiles(distributionRoot, new Set([".js"]));
  for (const path of distributionFiles) {
    bundleFilesScanned += 1;
    const bundle = await readFile(path, "utf8");
    if (forbiddenBundlePattern.test(bundle)) {
      violations.push({
        id: "automatic-network-api-in-production-bundle",
        path: relative(projectRoot, path).replaceAll("\\", "/"),
      });
    }
    if (dynamicCodePattern.test(bundle)) {
      violations.push({
        id: "dynamic-code-in-production-bundle",
        path: relative(projectRoot, path).replaceAll("\\", "/"),
      });
    }
  }
} catch (error) {
  if (error?.code !== "ENOENT") {
    throw error;
  }
}

const result = {
  schema_version: "1.0.0",
  status: violations.length === 0 ? "PASS" : "FAIL",
  checks: {
    analytics_payload: false,
    automatic_network_request: false,
    backend_dependency: false,
    credential_flow: false,
    live_pr_read: false,
    login_flow: false,
    static_browser_build: true,
  },
  scanned_product_files: (await sourceFiles(sourceRoot)).length,
  scanned_bundle_files: bundleFilesScanned,
  violations,
};

process.stdout.write(`${JSON.stringify(result)}\n`);
if (violations.length > 0) {
  process.exitCode = 1;
}
