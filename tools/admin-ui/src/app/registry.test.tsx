import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { extensionRegistry } from "./registry";

describe("product extension registry", () => {
  it("registers the campaign placeholder route and navigation entry", () => {
    const navigation = extensionRegistry.navigation.find(
      (item) => item.id === "campaigns",
    );
    const domain = extensionRegistry.domainModules.find(
      (item) => item.id === "campaigns-placeholder",
    );

    expect(navigation).toMatchObject({
      label: "Campaigns",
      route: "/campaigns",
    });
    expect(domain?.requiredCapabilities).toEqual(["campaign.read"]);
    expect(domain?.routes.map((route) => route.path)).toEqual(["/campaigns"]);

    const CampaignsRoute = domain?.routes[0]?.component;
    expect(CampaignsRoute).toBeDefined();
    render(CampaignsRoute ? <CampaignsRoute /> : null);
    expect(screen.getByRole("heading", { name: "Campaigns" })).toBeTruthy();
    expect(screen.getByRole("status").textContent).toMatch(/Unavailable:/u);
  });

  it("registers an alternate controller entity view outside the controller module", () => {
    const alternate = extensionRegistry.entityViews.find(
      (item) => item.entityType === "controller" && item.viewId === "summary",
    );

    expect(alternate?.inputContract).toBe("controller.list");
    const SummaryView = alternate?.component;
    expect(SummaryView).toBeDefined();
    render(SummaryView ? <SummaryView /> : null);
    expect(
      screen.getByRole("heading", { name: "Controller summary" }),
    ).toBeTruthy();
    expect(screen.getByText(/does not infer governance or protocol meaning/u)).toBeTruthy();
  });
});
