import type { WorkspaceData, WorkspaceStorage } from "../src/modules/workspace/workspace-context";

export class HttpWorkspaceStorage implements WorkspaceStorage {
  private async request(method: "GET" | "PUT", payload?: unknown) {
    const response = await fetch("/api/workspace", { method, credentials: "same-origin", cache: "no-store", redirect: "error",
      headers: { "Content-Type": "application/json", "X-Delta-Presentation": "1" },
      ...(payload ? { body: JSON.stringify(payload) } : {}), signal: AbortSignal.timeout(10_000) });
    if (!response.ok) throw new Error(`Profile HTTP ${response.status}`);
    const value = await response.json() as { revision: number; data: unknown };
    if (!Number.isSafeInteger(value.revision) || value.revision < 0) throw new Error("Invalid profile revision.");
    return value;
  }
  load() { return this.request("GET"); }
  save(data: WorkspaceData, revision: number) { return this.request("PUT", { revision, data }); }
}
