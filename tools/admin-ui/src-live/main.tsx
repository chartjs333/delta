import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "../src/app/App";
import { LiveExecutionProvider } from "../src/modules/live-execution/live-execution-context";
import "../src/styles.css";
import { HttpLiveExecutionAdapter } from "./http-live-execution-adapter";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Missing #root element");
}

if (!window.location.hash) {
  window.history.replaceState(null, "", "#/live-execution");
}

const liveExecutionPort = new HttpLiveExecutionAdapter();

createRoot(rootElement).render(
  <StrictMode>
    <LiveExecutionProvider mode="HTTP_LIVE" port={liveExecutionPort}>
      <App />
    </LiveExecutionProvider>
  </StrictMode>,
);
