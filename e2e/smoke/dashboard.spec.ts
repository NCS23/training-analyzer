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

    // Zwei Logos: Sidebar (Desktop) + TopBar (Mobile) — je nach Viewport ist nur eines sichtbar
    const logos = page.locator('img[alt="Training Analyzer"]');
    const count = await logos.count();
    expect(count).toBeGreaterThan(0);

    let anyVisible = false;
    for (let i = 0; i < count; i++) {
      if (await logos.nth(i).isVisible()) {
        anyVisible = true;
        break;
      }
    }
    expect(anyVisible).toBeTruthy();
  });
});
