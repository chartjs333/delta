import type {
  Capability,
  SourceDescriptor,
} from "../core/contracts";
import type { DataSourcePort } from "../data/data-source-port";

export type CapabilityState =
  | "AVAILABLE"
  | "UNAVAILABLE"
  | "LOADING"
  | "DEGRADED"
  | "STALE"
  | "ACCESS_DENIED";

export interface CapabilityDiscovery {
  readonly capability: Capability;
  readonly state: CapabilityState;
  readonly source: SourceDescriptor;
}

export async function discoverCapability(
  sourcePort: DataSourcePort,
  capability: Capability,
): Promise<CapabilityDiscovery> {
  const source = await sourcePort.describeSource();
  let state: CapabilityState;
  if (!source.capabilities.includes(capability)) {
    state = "UNAVAILABLE";
  } else {
    switch (source.connectionState) {
      case "LOADING":
        state = "LOADING";
        break;
      case "DEGRADED":
      case "UNAVAILABLE":
        state = "DEGRADED";
        break;
      case "STALE":
        state = "STALE";
        break;
      case "ACCESS_DENIED":
        state = "ACCESS_DENIED";
        break;
      case "LOCAL_READY":
        state = "AVAILABLE";
        break;
    }
  }
  return { capability, state, source };
}
