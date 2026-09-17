import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const repositoryRoot = resolve(projectRoot, "../..");

const protectedPaths = [
  "delta-core-cpp",
  "delta-runtime-cpp",
  "delta-protocol",
  "delta-ffi",
  "delta-node-java",
  "delta-worker-python",
  "formal",
];
const rootBuildFiles = [
  "CMakeLists.txt",
  "CMakePresets.json",
  "Makefile",
  "gradlew",
  "gradlew.bat",
  "settings.gradle",
  "settings.gradle.kts",
  "build.gradle",
  "build.gradle.kts",
  "pyproject.toml",
].filter((path) => existsSync(resolve(repositoryRoot, path)));

function git(args, allowNoMatches = false) {
  try {
    return execFileSync("git", args, {
      cwd: repositoryRoot,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    }).trim();
  } catch (error) {
    if (allowNoMatches && error?.status === 1) {
      return "";
    }
    throw error;
  }
}

const protectedWorkingTreeEntries = git([
  "status",
  "--porcelain=v1",
  "--untracked-files=all",
  "--",
  ...protectedPaths,
])
  .split(/\r?\n/u)
  .filter(Boolean);

const dependencyTargets = [...rootBuildFiles, ...protectedPaths];
const reverseDependencyHits = git(
  [
    "grep",
    "-n",
    "-I",
    "-E",
    "tools[/\\\\]admin-ui|@deltareduce/admin-ui",
    "--",
    ...dependencyTargets,
  ],
  true,
)
  .split(/\r?\n/u)
  .filter(Boolean);

const violations = [
  ...protectedWorkingTreeEntries.map((entry) => ({
    id: "protected-component-modified",
    detail: entry,
  })),
  ...reverseDependencyHits.map((entry) => ({
    id: "reverse-dependency-to-admin-ui",
    detail: entry,
  })),
];

const result = {
  schema_version: "1.0.0",
  status: violations.length === 0 ? "PASS" : "FAIL",
  repository_root: repositoryRoot,
  checks: {
    protected_paths: protectedPaths,
    protected_worktree_entries: protectedWorkingTreeEntries.length,
    dependency_targets: dependencyTargets,
    reverse_dependency_hits: reverseDependencyHits.length,
  },
  violations,
};

process.stdout.write(`${JSON.stringify(result)}\n`);
if (violations.length > 0) {
  process.exitCode = 1;
}
