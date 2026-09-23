import { HelpLabel } from "../../components/FieldHelp";
import { presentationUrl } from "../../presentation-url";
import { useEffect, useState } from "react";
import { languageLink, message, t, useLanguage } from "../../i18n";
import { useLiveExecutionRuntime } from "../live-execution/live-execution-context";
import type { LiveExecutionReceipt, LiveExecutionStatus } from "../live-execution/live-execution-port";
import { jcsCanonicalize } from "../live-execution/canonical-jcs";
import { useWorkspace, uuidPattern } from "./workspace-context";
import "./workspace.css";

export function executionLink(id: string, language: string) {
  return `?lang=${language}&execution=${encodeURIComponent(id)}#/live-execution`;
}
export function PresentationLink({ executionId }: { executionId: string }) {
  const language = useLanguage();
  const address = presentationUrl(new URL(window.location.href), import.meta.env.VITE_PRESENTATION_URL as string | undefined);
  if (!address || !uuidPattern.test(executionId)) return null;
  const url = new URL(languageLink(address, language));
  url.searchParams.set("execution", executionId);
  url.hash = "overview";
  return <a className="workspace-link" href={url.href}>{t("Present this run")} ↗</a>;
}
export function WorkspaceSummary() {
  const workspace = useWorkspace();
  if (!workspace) return null;
  const campaign = workspace.campaigns.find(item => item.id === workspace.activeCampaignId);
  return <aside className="workspace-summary" aria-label={t("Selected run setup")}>
    <div><small>{t("Execution target")}</small><a href="#/controllers">{t("Local Controller")}</a></div>
    <div><small>{t("Campaign")}</small><a href="#/campaigns">{campaign?.name}</a></div>
    <div><small>{t("Workload")}</small><a href="#/workloads">{t("Synthetic · 10 features")}</a></div>
    {workspace.warning ? <p role="alert">{t(workspace.warning)}</p> : null}
  </aside>;
}
export function ExecutionTarget() {
  const workspace = useWorkspace();
  if (!workspace) return null;
  return <section className="guided-card execution-target">
    <p className="eyebrow">{t("Execution target")}</p><h1>{t("Local Controller")}</h1>
    <p>{t("Live Execution sends requests to the Controller serving this Admin UI.")}</p>
    <code>{t("Same-origin gateway → baseline Controller/Worker")}</code>
    <p>{t("The local controller register below documents governance. Editing it does not switch the execution target.")}</p>
    <a className="workspace-link" href="#/workloads">{t("Choose a workload")} →</a>
  </section>;
}
export function ProfilePanel({ pendingDocument = false }: { pendingDocument?: boolean }) {
  const workspace = useWorkspace();
  const language = useLanguage();
  const [name, setName] = useState(workspace?.profileName ?? "");
  if (!workspace) return null;
  return <details className="workspace-profile"><summary>{t("Local profile")}: {workspace.profileName} · {t(workspace.warning ? "Profile needs attention" : pendingDocument || name !== workspace.profileName ? "Unsaved changes" : workspace.saving ? "Saving…" : "Saved on this computer")}</summary>
    <p>{t("Shared by Admin UI and Presentation. No account or password is required on this computer.")}</p>
    <form onSubmit={event => { event.preventDefault(); void workspace.savePreferences(name, language).catch(() => {}); }}>
      <HelpLabel>{t("Profile name")}<input maxLength={80} value={name} onChange={event => setName(event.target.value)} /></HelpLabel>
      <button disabled={!name.trim() || workspace.saving}>{t("Save profile")}</button>
    </form>{workspace.warning ? <p role="alert">{t(workspace.warning)}</p> : null}</details>;
}
export function CampaignWorkspace() {
  const workspace = useWorkspace();
  const language = useLanguage();
  const [name, setName] = useState("");
  if (!workspace) return <p>{t("Campaigns are available in the live workspace.")}</p>;
  const campaign = workspace.campaigns.find(item => item.id === workspace.activeCampaignId)!;
  const runs = workspace.runs.filter(run => run.campaignId === campaign.id).slice().reverse();
  return <section className="campaign-workspace">
    <p className="eyebrow">{t("Your experiments")}</p><h1>{t("Campaigns")}</h1>
    <p>{t("Group real local runs, then open their status, receipt or presentation.")}</p>
    <p className="guide-note">{t("Definitions are saved in your local profile. Execution results are read from the Controller.")}</p>
    <WorkspaceSummary />
    <div className="campaign-controls">
      <HelpLabel>{t("Active campaign")}<select disabled={workspace.saving} value={campaign.id} onChange={event => { void workspace.selectCampaign(event.target.value).catch(() => {}); }}>
        {workspace.campaigns.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select></HelpLabel>
      <form onSubmit={event => { event.preventDefault(); void workspace.createCampaign(name).then(() => setName("")).catch(() => {}); }}>
        <HelpLabel>{t("New campaign name")}<input value={name} maxLength={80} onChange={event => setName(event.target.value)} /></HelpLabel>
        <button disabled={!name.trim() || workspace.saving || workspace.campaigns.length >= 30}>{t("Create campaign")}</button>
      </form>
    </div>
    <div className="guided-actions"><a className="workspace-link" href="#/workloads">{t("Change workload")}</a>
      <a className="workspace-link" href={`?lang=${language}#/live-execution`}>{t("Prepare a run")} →</a></div>
    <h2>{t("Runs in this campaign")}</h2>
    {!runs.length ? <p>{t("No runs yet. Prepare a run to begin.")}</p> : <ul className="campaign-runs">
      {runs.map(run => <li className="guided-card" key={run.intentId}>
        <strong>{run.name}</strong><small>{new Date(run.createdAt).toLocaleString(language === "ru" ? "ru-RU" : "en-GB")}</small>
        <code>{run.workload.model_plugin_id}</code>
        {run.executionId ? <><code>{run.executionId}</code><div className="guided-actions">
          <a href={executionLink(run.executionId, language)}>{t("Open status and receipt")}</a>
          <PresentationLink executionId={run.executionId} /></div></>
          : <p>{t("Admission is unconfirmed. Do not resubmit this request blindly.")}</p>}
      </li>)}
    </ul>}
  </section>;
}
export function ExecutionDetail({ executionId }: { executionId: string }) {
  const { port } = useLiveExecutionRuntime();
  const workspace = useWorkspace();
  const [status, setStatus] = useState<LiveExecutionStatus>();
  const [receipt, setReceipt] = useState<LiveExecutionReceipt>();
  const [error, setError] = useState<string>();
  const [refresh, setRefresh] = useState(0);
  const run = workspace?.runs.find(item => item.executionId === executionId);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    setStatus(undefined); setReceipt(undefined); setError(undefined);
    async function read(count: number) {
      try {
        if (!uuidPattern.test(executionId)) throw new Error("Invalid execution link.");
        const next = await port.getStatus(executionId);
        if (!active) return;
        if (run && (next.lineage.intentId !== run.intentId || next.lineage.intentDigest !== run.intentDigest))
          throw new Error("Status does not match the campaign request.");
        setStatus(next);
        if (next.state === "COMPLETED" && port.getReceipt && next.operation !== "MATERIALIZE_DATASET") {
          const result = await port.getReceipt(executionId);
          if (active) setReceipt(result);
        } else if (!next.terminal && count < 90) timer = setTimeout(() => void read(count + 1), 1000);
      } catch (reason) {
        if (active) { setReceipt(undefined); setError(reason instanceof Error ? reason.message : String(reason)); }
      }
    }
    void read(0);
    return () => { active = false; clearTimeout(timer); };
  }, [executionId, port, refresh, run?.intentId, run?.intentDigest]);
  function download() {
    if (!receipt) return;
    const url = URL.createObjectURL(new Blob([jcsCanonicalize(receipt)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = `receipt-${executionId}.json`; link.click(); URL.revokeObjectURL(url);
  }
  return <section className="guided-card linked-execution">
    <p className="eyebrow">{t("Linked execution")}</p><h2>{run?.name ?? t("Controller execution")}</h2>
    <code>{executionId}</code>
    <p role="status">{error ? t("Unable to confirm the result") : status ? message(status.summary) : t("Loading source…")}</p>
    {error ? <p role="alert">{message(error)}</p> : null}
    <div className="guided-actions"><button onClick={() => setRefresh(value => value + 1)}>{t("Refresh status")}</button>
      {receipt ? <button className="primary" onClick={download}>{t("Download receipt")}</button> : null}
      <PresentationLink executionId={executionId} /><a href="#/campaigns">{t("Back to campaign")}</a></div>
    {receipt ? <p>{t("The Controller returned a receipt. Its hash and connection to this request were checked.")}</p> : null}
    <details><summary>{t("Technical details & original JSON")}</summary><pre>{JSON.stringify({ status, receipt }, null, 2)}</pre></details>
  </section>;
}
