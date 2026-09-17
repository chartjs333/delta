import type { ExtensionRegistration } from "../../app/extensions";
import { WorkloadSelector } from "./WorkloadSelector";

export const workloadModuleRegistration: ExtensionRegistration = {
  navigation: {
    id: "workloads",
    label: "Workloads",
    route: "/workloads",
    permission: "PUBLIC_LOCAL",
  },
  domainModule: {
    id: "workloads",
    routes: [{ path: "/workloads", component: WorkloadSelector }],
    views: ["workload-selector"],
    requiredCapabilities: ["schema.enumerate"],
  },
};
