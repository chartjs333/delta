import type {
  ExtensionRegistration,
  ExtensionRegistry,
} from "./extensions";

function assertUnique(ids: readonly string[], extensionType: string): void {
  const seen = new Set<string>();
  for (const id of ids) {
    if (seen.has(id)) {
      throw new Error(`Duplicate ${extensionType} extension id: ${id}`);
    }
    seen.add(id);
  }
}

export function composeExtensions<TAdapter = unknown>(
  registrations: readonly ExtensionRegistration<TAdapter>[],
): ExtensionRegistry<TAdapter> {
  const registry: ExtensionRegistry<TAdapter> = {
    navigation: registrations.flatMap((item) =>
      item.navigation ? [item.navigation] : [],
    ),
    domainModules: registrations.flatMap((item) =>
      item.domainModule ? [item.domainModule] : [],
    ),
    entityViews: registrations.flatMap((item) =>
      item.entityView ? [item.entityView] : [],
    ),
    dashboardWidgets: registrations.flatMap((item) =>
      item.dashboardWidget ? [item.dashboardWidget] : [],
    ),
    dataAdapters: registrations.flatMap((item) =>
      item.dataAdapter ? [item.dataAdapter] : [],
    ),
    visualizations: registrations.flatMap((item) =>
      item.visualization ? [item.visualization] : [],
    ),
  };

  assertUnique(
    registry.navigation.map((item) => item.id),
    "navigation",
  );
  assertUnique(
    registry.domainModules.map((item) => item.id),
    "domain-module",
  );
  assertUnique(
    registry.entityViews.map((item) => `${item.entityType}:${item.viewId}`),
    "entity-view",
  );
  assertUnique(
    registry.dashboardWidgets.map((item) => item.id),
    "dashboard-widget",
  );
  assertUnique(
    registry.dataAdapters.map((item) => item.id),
    "data-adapter",
  );
  assertUnique(
    registry.visualizations.map((item) => item.rendererId),
    "visualization",
  );

  return Object.freeze(registry);
}
