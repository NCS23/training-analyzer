import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("lädt und zeigt Inhalt", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    // Kein Error-Boundary sichtbar
    await expect(
      page.getByText("Etwas ist schiefgelaufen"),
    ).not.toBeVisible();

    // Main-Content ist vorhanden und nicht leer
    const main = page.locator("main");
    await expect(main).toBeVisible();
    await expect(main).not.toBeEmpty();
  });

  test("zeigt App-Branding", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    // Mindestens ein Logo mit alt="Training Analyzer" muss sichtbar sein
    // (Sidebar auf Desktop, TopBar auf Mobile)
    await expect(
      page.locator('img[alt="Training Analyzer"]').first(),
    ).toBeVisible();
  });
});
