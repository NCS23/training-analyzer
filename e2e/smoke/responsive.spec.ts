import { test, expect } from "@playwright/test";

test.describe("Responsive Layout", () => {
  test("Mobile: BottomNav sichtbar", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === "desktop", "Nur Mobile");

    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    // BottomNav enthält die 5 Navigations-Links
    const bottomNav = page.locator("nav").filter({
      has: page.getByRole("link", { name: "Home" }),
    });
    await expect(bottomNav).toBeVisible();

    // Alle 5 Nav-Items sichtbar
    await expect(page.getByRole("link", { name: "Home" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Sessions" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Plan" })).toBeVisible();
  });

  test("Mobile: Sidebar versteckt", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === "desktop", "Nur Mobile");

    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    // Sidebar hat class "hidden lg:flex" — auf Mobile nicht sichtbar
    // Prüfen über den Sidebar-spezifischen User-Chip "NC"
    const sidebarUserChip = page.locator("nav").filter({
      hasText: "Nils-Christian",
    });
    await expect(sidebarUserChip).not.toBeVisible();
  });

  test("Desktop: Sidebar sichtbar", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === "mobile", "Nur Desktop");

    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    // Sidebar mit "Training Analyzer" Branding und User-Chip
    const sidebar = page.locator("nav").filter({
      hasText: "Nils-Christian",
    });
    await expect(sidebar).toBeVisible();

    // Sidebar Nav-Items sichtbar
    await expect(
      sidebar.getByRole("button", { name: /Dashboard/ }),
    ).toBeVisible();
    await expect(
      sidebar.getByRole("button", { name: /Sessions/ }),
    ).toBeVisible();
  });

  test("Desktop: BottomNav versteckt", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === "mobile", "Nur Desktop");

    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    // BottomNav hat class "lg:hidden" — auf Desktop nicht sichtbar
    const bottomNav = page.locator("nav").filter({
      has: page.getByRole("link", { name: "Home" }),
    });
    await expect(bottomNav).not.toBeVisible();
  });
});
