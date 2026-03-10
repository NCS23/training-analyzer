import { test, expect } from "@playwright/test";

const pages = [
  { path: "/dashboard", name: "Dashboard" },
  { path: "/sessions", name: "Sessions" },
  { path: "/analyse", name: "Analyse" },
  { path: "/plan", name: "Plan" },
  { path: "/profile", name: "Profil" },
];

test.describe("Navigation", () => {
  for (const { path, name } of pages) {
    test(`${name} (${path}) ist erreichbar`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");

      // Richtige URL
      await expect(page).toHaveURL(new RegExp(path));

      // Kein Error-Boundary
      await expect(
        page.getByText("Etwas ist schiefgelaufen"),
      ).not.toBeVisible();

      // Seite hat Content
      await expect(page.locator("main")).toBeVisible();
    });
  }

  test("404-Seite bei unbekannter Route", async ({ page }) => {
    await page.goto("/diese-seite-gibt-es-nicht");
    await page.waitForLoadState("networkidle");

    // Sollte eine 404-Anzeige haben (oder Redirect)
    // Mindestens: kein weißer Screen
    await expect(page.locator("body")).not.toBeEmpty();
  });
});
