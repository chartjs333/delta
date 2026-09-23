import { composeExtensions } from "./composition-root";
import { controllerSummaryRegistration } from "../extensions/controller-summary/registration";
import { campaignPlaceholderRegistration } from "../modules/campaigns/registration";
import { controllerModuleRegistration } from "../modules/controllers/registration";
import { liveExecutionModuleRegistration } from "../modules/live-execution/registration";
import { workloadModuleRegistration } from "../modules/workloads/registration";
import { sdkModuleRegistration } from "../modules/sdk/registration";

// All product extensions are registered here. Domain modules never mutate this
// registry themselves, which keeps extension wiring localized and auditable.
export const extensionRegistry = composeExtensions([
  controllerModuleRegistration,
  campaignPlaceholderRegistration,
  controllerSummaryRegistration,
  workloadModuleRegistration,
  liveExecutionModuleRegistration,
  sdkModuleRegistration,
]);
