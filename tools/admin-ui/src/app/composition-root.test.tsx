import { describe, expect, it } from "vitest";

import { composeExtensions } from "./composition-root";

const Empty = () => null;

describe("extension composition root", () => {
  it("registers every documented extension class", () => {
    const registry = composeExtensions([
      {
        navigation: {
          id: "controllers-nav",
          label: "Controllers",
          route: "/controllers",
          permission: "PUBLIC_LOCAL",
        },
        domainModule: {
          id: "controllers",
          routes: [{ path: "/controllers", component: Empty }],
          views: ["controller-list"],
          requiredCapabilities: ["controller.list"],
        },
        entityView: {
          entityType: "controller",
          viewId: "list",
          inputContract: "controller.list",
          component: Empty,
          fallback: Empty,
        },
        dashboardWidget: {
          id: "document-summary",
          requiredCapabilities: ["document.read"],
          component: Empty,
          emptyState: Empty,
          errorState: Empty,
        },
        dataAdapter: {
          id: "local-json",
          authorityClass: "LOCAL_DRAFT",
          capabilities: ["document.read"],
          create: () => ({ id: "local-json" }),
        },
        visualization: {
          rendererId: "controller-table",
          inputContract: "controller.list",
          component: Empty,
          unsupportedFallback: Empty,
        },
      },
    ]);

    expect(registry.navigation).toHaveLength(1);
    expect(registry.domainModules).toHaveLength(1);
    expect(registry.entityViews).toHaveLength(1);
    expect(registry.dashboardWidgets).toHaveLength(1);
    expect(registry.dataAdapters).toHaveLength(1);
    expect(registry.visualizations).toHaveLength(1);
  });

  it("rejects duplicate extension identities", () => {
    expect(() =>
      composeExtensions([
        {
          navigation: {
            id: "controllers",
            label: "One",
            route: "/one",
            permission: "PUBLIC_LOCAL",
          },
        },
        {
          navigation: {
            id: "controllers",
            label: "Two",
            route: "/two",
            permission: "PUBLIC_LOCAL",
          },
        },
      ]),
    ).toThrow("Duplicate navigation extension id");
  });
});
