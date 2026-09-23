import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "../src/app/App";
import { LiveExecutionProvider } from "../src/modules/live-execution/live-execution-context";
import "../src/styles.css";
import { HttpLiveExecutionAdapter } from "./http-live-execution-adapter";
import { WorkspaceProvider } from "../src/modules/workspace/workspace-context";
import { HttpWorkspaceStorage } from "./http-workspace-storage";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Missing #root element");
}

if (!window.location.hash) {
  window.history.replaceState(
    null,
    "",
    `${window.location.pathname}${window.location.search}#/live-execution`,
  );
}

const liveExecutionPort = new HttpLiveExecutionAdapter();
const profileStorage = new HttpWorkspaceStorage();
const sharedAddress = import.meta.env.VITE_PRESENTATION_URL as string | undefined;
if (sharedAddress && window.location.origin !== new URL(sharedAddress).origin) {
  const destination = new URL("admin/", sharedAddress);
  destination.search = window.location.search;
  destination.hash = window.location.hash;
  window.location.replace(destination.href);
} else createRoot(rootElement).render(
  <StrictMode>
    <LiveExecutionProvider mode="HTTP_LIVE" port={liveExecutionPort}>
      {sharedAddress ? <WorkspaceProvider storage={profileStorage}><App /></WorkspaceProvider> : <App />}
    </LiveExecutionProvider>
  </StrictMode>,
);
