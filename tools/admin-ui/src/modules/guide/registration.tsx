import type { ExtensionRegistration } from "../../app/extensions";
import { GuidePage } from "./GuidePage";

export const guideModuleRegistration: ExtensionRegistration = {
  navigation: { id: "guide", label: "How it works", route: "/guide", permission: "PUBLIC_LOCAL" },
  domainModule: { id: "guide", routes: [{ path: "/guide", component: GuidePage }], views: ["visual-guide"], requiredCapabilities: [] },
};
