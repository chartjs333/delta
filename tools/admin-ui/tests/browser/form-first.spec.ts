import { expect, test, type Page } from "@playwright/test";

function captureBoundaryFailures(page: Page) {
  const consoleErrors: string[] = [];
  const externalRequests: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.hostname !== "127.0.0.1" || url.port !== "4175") {
      externalRequests.push(request.url());
    }
  });
  return { consoleErrors, externalRequests };
}

test("non-technical form creates four controllers, fills six records, validates, and exports", async ({
  page,
}) => {
  const boundary = captureBoundaryFailures(page);
  await page.goto("/");
  await page.getByRole("button", { name: "New document" }).click();

  for (let index = 1; index <= 4; index += 1) {
    await page.getByRole("button", { name: "Add controller" }).click();
    await page
      .getByLabel(`Controller ${index} Controller ID`)
      .fill(`controller-${index}`);
  }

  const pairwise = page.getByRole("region", { name: "Pairwise records" });
  await expect(pairwise.getByLabel("Pairwise record count")).toHaveText("6");
  for (let pair = 0; pair < 6; pair += 1) {
    const acceptIds = pairwise.getByRole("button", {
      name: "Review and accept current IDs",
    });
    if (await acceptIds.isVisible()) await acceptIds.click();
    const questions = pairwise.getByRole("group");
    await questions.nth(0).getByLabel("Yes", { exact: true }).check();
    await questions.nth(1).getByLabel("No", { exact: true }).check();
    await questions.nth(2).getByLabel("Unknown", { exact: true }).check();
    if (pair === 0) {
      await pairwise
        .getByLabel("Evidence references")
        .fill("evidence://local-review/one");
    }
    if (pair < 5) {
      await pairwise.getByRole("button", { name: "Next pair" }).click();
    }
  }

  const summary = page.getByRole("region", { name: "Worksheet summary" });
  await expect(summary).toContainText("6 of 6");
  await expect(summary).toContainText("pairwise records filled");
  await expect(summary).not.toContainText(/\b(?:PASS|FAIL|approved|verified)\b/iu);

  const advanced = page.getByRole("region", { name: "Advanced JSON view" });
  await expect(advanced.locator("details")).not.toHaveAttribute("open", "");
  await expect(advanced.getByLabel("Read-only JSON document")).toHaveAttribute(
    "readonly",
    "",
  );

  await page.getByRole("button", { name: "Validate structure" }).click();
  await expect(page.getByRole("heading", { name: "VALID" })).toBeVisible();

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download new file" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("controller-register.new.export.json");
  expect(boundary.consoleErrors).toEqual([]);
  expect(boundary.externalRequests).toEqual([]);
});

test("mobile menu keeps navigation and the form reachable", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chrome", "Mobile-only navigation check");
  const boundary = captureBoundaryFailures(page);
  await page.goto("/");

  const menu = page.getByRole("button", { name: "Menu" });
  await expect(menu).toHaveAttribute("aria-expanded", "false");
  await menu.click();
  await expect(menu).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByRole("link", { name: /Controllers/u })).toBeVisible();
  await expect(page.getByRole("link", { name: /Campaigns/u })).toBeVisible();
  await page.getByRole("link", { name: /Controllers/u }).click();
  await expect(menu).toHaveAttribute("aria-expanded", "false");

  await page.getByRole("button", { name: "New document" }).click();
  await expect(page.getByRole("region", { name: "Controller registry" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Add controller" })).toBeVisible();
  expect(boundary.consoleErrors).toEqual([]);
  expect(boundary.externalRequests).toEqual([]);
});
