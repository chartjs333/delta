import {
  createContext,
  type PropsWithChildren,
  useContext,
} from "react";

import type { LiveExecutionPort } from "./live-execution-port";
import { MockLiveExecutionAdapter } from "./mock-live-execution-adapter";

export type LiveExecutionRuntimeMode = "OFFLINE_MOCK" | "HTTP_LIVE";

export interface LiveExecutionRuntime {
  readonly mode: LiveExecutionRuntimeMode;
  readonly port: LiveExecutionPort;
}

const offlineRuntime: LiveExecutionRuntime = Object.freeze({
  mode: "OFFLINE_MOCK",
  port: new MockLiveExecutionAdapter(),
});

const LiveExecutionRuntimeContext =
  createContext<LiveExecutionRuntime>(offlineRuntime);

export interface LiveExecutionProviderProps extends PropsWithChildren {
  readonly mode: LiveExecutionRuntimeMode;
  readonly port: LiveExecutionPort;
}

export function LiveExecutionProvider({
  children,
  mode,
  port,
}: LiveExecutionProviderProps) {
  return (
    <LiveExecutionRuntimeContext.Provider value={{ mode, port }}>
      {children}
    </LiveExecutionRuntimeContext.Provider>
  );
}

export function useLiveExecutionRuntime(): LiveExecutionRuntime {
  return useContext(LiveExecutionRuntimeContext);
}
