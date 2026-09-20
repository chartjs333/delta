import type { ExtensionRegistration } from "../../app/extensions";
import { LiveExecutionSurface } from "./LiveExecutionSurface";

export const liveExecutionModuleRegistration: ExtensionRegistration = {
  navigation: {
    id: "live-execution",
    label: "Live execution",
    route: "/live-execution",
    permission: "PUBLIC_LOCAL",
  },
  domainModule: {
    id: "live-execution",
    routes: [{ path: "/live-execution", component: LiveExecutionSurface }],
    views: ["live-execution-status"],
    requiredCapabilities: ["live.status.read"],
  },
};
