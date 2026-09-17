import type { ExtensionRegistration } from "../../app/extensions";

function ControllersRoute() {
  return <p>Open or create a local controller document to begin.</p>;
}

function UnsupportedControllers() {
  return <p role="status">Controller view unavailable for the active source.</p>;
}

export const controllerModuleRegistration: ExtensionRegistration = {
  navigation: {
    id: "controllers",
    label: "Controllers",
    route: "/controllers",
    permission: "PUBLIC_LOCAL",
  },
  domainModule: {
    id: "controllers",
    routes: [{ path: "/controllers", component: ControllersRoute }],
    views: ["controller-list", "controller-detail"],
    requiredCapabilities: ["controller.list"],
  },
  entityView: {
    entityType: "controller",
    viewId: "list-detail",
    inputContract: "controller.list",
    component: ControllersRoute,
    fallback: UnsupportedControllers,
  },
};
