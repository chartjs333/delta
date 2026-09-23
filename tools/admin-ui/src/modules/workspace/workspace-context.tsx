import { createContext, useCallback, useContext, useEffect, useRef, useState, type PropsWithChildren } from "react";
import { setLanguage, t } from "../../i18n";
import { getDefaultWorkload, type ExecutionIntentDocument, type WorkloadSelectionState } from "../live-execution/intent-builder";
import type { LiveExecutionStatus } from "../live-execution/live-execution-port";

export const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
interface Campaign { id: string; name: string }
export interface WorkspaceRun {
  intentId: string; intentDigest: string; campaignId: string; name: string;
  workload: WorkloadSelectionState; operation: string; createdAt: string; executionId?: string;
}
export interface WorkspaceData {
  version: 1; profileName: string; language: "en" | "ru"; controllerDocument: string | null; campaigns: Campaign[]; activeCampaignId: string;
  workload: WorkloadSelectionState; runs: WorkspaceRun[];
}
// This presentation stack enables only this baseline's actual catalog subset.
// The broader frozen catalog remains browsable, but cannot silently replace it.
export function locallyRunnable(workload: WorkloadSelectionState): boolean {
  return (
    workload.model_plugin_id === getDefaultWorkload().model_plugin_id &&
    workload.dataset_id === getDefaultWorkload().dataset_id &&
    workload.requested_scope === "PLUGIN_BOUNDARY" &&
    workload.catalog_backend_ref === getDefaultWorkload().catalog_backend_ref
  );
}
function initialData(): WorkspaceData {
  return { version: 1, profileName: "Local presentation", language: "en", controllerDocument: null, campaigns: [{ id: "presentation", name: "Presentation" }],
    activeCampaignId: "presentation", workload: getDefaultWorkload(), runs: [] };
}
function isWorkload(value: unknown): value is WorkloadSelectionState {
  if (!value || typeof value !== "object") return false;
  const item = value as WorkloadSelectionState;
  return locallyRunnable(item);
}
export function readWorkspace(raw: string | null): WorkspaceData {
  if (!raw) return initialData();
  if (raw.length > 250_000) throw new Error("Workspace data is invalid.");
  const data = JSON.parse(raw) as WorkspaceData;
  if (!data || data.version !== 1 || typeof data.profileName !== "string" || !data.profileName.trim() || data.profileName.length > 80 || !["en", "ru"].includes(data.language) || (data.controllerDocument !== null && (typeof data.controllerDocument !== "string" || data.controllerDocument.length > 100_000)) || !Array.isArray(data.campaigns) ||
      data.campaigns.length < 1 || data.campaigns.length > 30 || !Array.isArray(data.runs) ||
      data.runs.length > 100 || !isWorkload(data.workload)) throw new Error("Workspace data is invalid.");
  const ids = new Set<string>();
  for (const campaign of data.campaigns) {
    if (!campaign || typeof campaign.id !== "string" || !/^[a-zA-Z0-9-]{1,64}$/.test(campaign.id) ||
        typeof campaign.name !== "string" || !campaign.name.trim() || campaign.name.length > 80 || ids.has(campaign.id))
      throw new Error("Workspace data is invalid.");
    ids.add(campaign.id);
  }
  if (!ids.has(data.activeCampaignId)) throw new Error("Workspace data is invalid.");
  const intents = new Set<string>();
  for (const run of data.runs) {
    if (!run || !uuidPattern.test(run.intentId) || intents.has(run.intentId) ||
        !/^sha256:[0-9a-f]{64}$/.test(run.intentDigest) || !ids.has(run.campaignId) ||
        typeof run.name !== "string" || run.name.length > 80 || !isWorkload(run.workload) ||
        !["TRAIN_TICKET", "EVALUATE_CHECKPOINT", "MATERIALIZE_DATASET"].includes(run.operation) ||
        typeof run.createdAt !== "string" || Number.isNaN(Date.parse(run.createdAt)) ||
        (run.executionId !== undefined && !uuidPattern.test(run.executionId)))
      throw new Error("Workspace data is invalid.");
    intents.add(run.intentId);
  }
  return data;
}
export interface WorkspaceStorage {
  load(): Promise<{ revision: number; data: unknown }>;
  save(data: WorkspaceData, revision: number): Promise<{ revision: number }>;
}
interface Workspace extends WorkspaceData {
  warning?: string;
  saving: boolean;
  selectWorkload(workload: WorkloadSelectionState): Promise<void>;
  selectCampaign(id: string): Promise<void>;
  createCampaign(name: string): Promise<void>;
  beginRun(intent: ExecutionIntentDocument, name: string): Promise<void>;
  bindStatus(intent: ExecutionIntentDocument, status: LiveExecutionStatus): Promise<void>;
  saveDocument(text: string): Promise<void>;
  savePreferences(profileName: string, language: "en" | "ru"): Promise<void>;
}
const Context = createContext<Workspace | undefined>(undefined);
export function useWorkspace() { return useContext(Context); }
export function WorkspaceProvider({ children, storage }: PropsWithChildren<{ storage: WorkspaceStorage }>) {
  const [warning, setWarning] = useState<string>();
  const [data, setData] = useState<WorkspaceData>();
  const [saving, setSaving] = useState(false);
  const [retry, setRetry] = useState(0);
  const current = useRef<{ data: WorkspaceData; revision: number } | undefined>(undefined);
  const queue = useRef(Promise.resolve());
  useEffect(() => {
    let active = true;
    void storage.load().then(result => {
      if (!active) return;
      const next = readWorkspace(result.data === null ? null : JSON.stringify(result.data));
      if (!new URLSearchParams(window.location.search).has("lang")) setLanguage(next.language);
      current.current = { data: next, revision: result.revision }; setData(next); setWarning(undefined);
    }).catch(() => { if (active) setWarning("The local profile could not be loaded. Retry without overwriting saved definitions."); });
    return () => { active = false; };
  }, [storage, retry]);
  const commit = useCallback((change: (value: WorkspaceData) => WorkspaceData): Promise<void> => {
    const operation = queue.current.then(async () => {
      if (!current.current) throw new Error("Profile is not loaded.");
      const previous = current.current;
      const next = change(previous.data);
      if (next === previous.data) return;
      readWorkspace(JSON.stringify(next));
      setSaving(true);
      try {
        const saved = await storage.save(next, previous.revision);
        current.current = { data: next, revision: saved.revision }; setData(next); setWarning(undefined);
      } catch (reason) {
        setWarning("Profile save failed or another tab changed it. Reload to read the saved profile.");
        throw reason;
      } finally { setSaving(false); }
    });
    queue.current = operation.catch(() => {});
    return operation;
  }, [storage]);
  if (!data) return <section className="guided-card"><p role="status">{t(warning ?? "Loading local profile…")}</p>
    {warning ? <button onClick={() => setRetry(value => value + 1)}>{t("Retry")}</button> : null}</section>;
  return <Context.Provider value={{ ...data, warning, saving,
    selectWorkload(workload) { return commit(value => {
      if (!locallyRunnable(workload)) throw new Error("This workload is not enabled on the local Controller.");
      return { ...value, workload };
    }); },
    selectCampaign(id) { return commit(value => value.campaigns.some(item => item.id === id)
      ? { ...value, activeCampaignId: id } : value); },
    createCampaign(name) { return commit(value => {
      const trimmed = name.trim();
      if (!trimmed || trimmed.length > 80 || value.campaigns.length >= 30) return value;
      const campaign = { id: crypto.randomUUID(), name: trimmed };
      return { ...value, activeCampaignId: campaign.id, campaigns: [...value.campaigns, campaign] };
    }); },
    beginRun(intent, name) { return commit(value => {
      if (value.runs.some(run => run.intentId === intent.intent_id)) return value;
      return { ...value, runs: [...value.runs, { intentId: intent.intent_id,
        intentDigest: intent.intent_digest, campaignId: value.activeCampaignId,
        name: name.slice(0, 80), workload: intent.workload, operation: intent.operation,
        createdAt: intent.created_at }].slice(-100) };
    }); },
    bindStatus(intent, status) { return commit(value => {
      if (status.lineage.intentId !== intent.intent_id || status.lineage.intentDigest !== intent.intent_digest ||
          (status.lineage.executionId && !uuidPattern.test(status.lineage.executionId)))
        throw new Error("Status does not match the campaign request.");
      const run = value.runs.find(item => item.intentId === intent.intent_id);
      if (!run || run.executionId === status.lineage.executionId) return value;
      return { ...value, runs: value.runs.map(item => item.intentId === intent.intent_id
        ? { ...item, executionId: status.lineage.executionId } : item) };
    }); },
    saveDocument(controllerDocument) { return commit(value => ({ ...value, controllerDocument })); },
    savePreferences(profileName, language) { return commit(value => ({ ...value, profileName: profileName.trim(), language })); },
  }}>{children}</Context.Provider>;
}
