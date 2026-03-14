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

    // Warten bis React gemountet hat und mindestens ein Logo im DOM ist
    const logo = page.locator('img[alt="Training Analyzer"]');
    await logo.first().waitFor({ state: "attached", timeout: 15_000 });

    // Mindestens ein Logo muss sichtbar sein (Sidebar auf Desktop, TopBar auf Mobile)
    const count = await logo.count();
    let anyVisible = false;
    for (let i = 0; i < count; i++) {
      if (await logo.nth(i).isVisible()) {
        anyVisible = true;
        break;
      }
    }
    expect(anyVisible).toBeTruthy();
  });
});
