import type { ExtensionRegistration } from "../../app/extensions";
import { SdkPage } from "./SdkPage";

export const sdkModuleRegistration: ExtensionRegistration = {
  navigation: { id: "sdk", label: "SDK", route: "/sdk", permission: "PUBLIC_LOCAL" },
  domainModule: { id: "sdk", routes: [{ path: "/sdk", component: SdkPage }], views: ["sdk-guide"], requiredCapabilities: [] },
};
