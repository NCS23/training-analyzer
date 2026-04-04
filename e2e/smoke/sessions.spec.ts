import { test, expect } from "../auth-fixture";

test.describe("Sessions", () => {
  test("Sessions-Seite lädt", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("domcontentloaded");

    // Kein Error-Boundary
    await expect(
      page.getByText("Etwas ist schiefgelaufen"),
    ).not.toBeVisible();

    // Main-Content ist vorhanden
    const main = page.locator("main");
    await expect(main).toBeVisible();
    await expect(main).not.toBeEmpty();
  });
});
