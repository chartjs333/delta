import type { ComponentType } from "react";

export type RouteComponent = ComponentType;

export interface NavigationExtension {
  readonly id: string;
  readonly label: string;
  readonly route: string;
  readonly permission: "PUBLIC_LOCAL";
}

export interface DomainRoute {
  readonly path: string;
  readonly component: RouteComponent;
}

export interface DomainModuleExtension {
  readonly id: string;
  readonly routes: readonly DomainRoute[];
  readonly views: readonly string[];
  readonly requiredCapabilities: readonly string[];
}

export interface EntityViewExtension {
  readonly entityType: string;
  readonly viewId: string;
  readonly inputContract: string;
  readonly component: RouteComponent;
  readonly fallback: RouteComponent;
}

export interface DashboardWidgetExtension {
  readonly id: string;
  readonly requiredCapabilities: readonly string[];
  readonly component: RouteComponent;
  readonly emptyState: RouteComponent;
  readonly errorState: RouteComponent;
}

export interface DataAdapterExtension<TAdapter = unknown> {
  readonly id: string;
  readonly authorityClass: string;
  readonly capabilities: readonly string[];
  readonly create: () => TAdapter;
}

export interface VisualizationExtension {
  readonly rendererId: string;
  readonly inputContract: string;
  readonly component: RouteComponent;
  readonly unsupportedFallback: RouteComponent;
}

export interface ExtensionRegistry<TAdapter = unknown> {
  readonly navigation: readonly NavigationExtension[];
  readonly domainModules: readonly DomainModuleExtension[];
  readonly entityViews: readonly EntityViewExtension[];
  readonly dashboardWidgets: readonly DashboardWidgetExtension[];
  readonly dataAdapters: readonly DataAdapterExtension<TAdapter>[];
  readonly visualizations: readonly VisualizationExtension[];
}

export type ExtensionRegistration<TAdapter = unknown> = {
  readonly navigation?: NavigationExtension;
  readonly domainModule?: DomainModuleExtension;
  readonly entityView?: EntityViewExtension;
  readonly dashboardWidget?: DashboardWidgetExtension;
  readonly dataAdapter?: DataAdapterExtension<TAdapter>;
  readonly visualization?: VisualizationExtension;
};
