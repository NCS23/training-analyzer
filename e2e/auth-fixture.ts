/**
 * E2E Auth Fixture: Gibt jedem Test frische Tokens per API-Login.
 *
 * Löst das Token-Rotation-Problem: Die deployed Frontend-App ruft bei
 * jedem Seitenaufruf refresh() auf, was das Refresh-Token rotiert
 * (altes wird revoked). Deshalb braucht JEDER Test ein eigenes
 * frisches Token-Paar — kein Caching, kein Sharing.
 */
import { test as base, expect } from "@playwright/test";

const E2E_EMAIL = "e2e-smoke@training-analyzer.app";
const E2E_PASSWORD = "e2e-smoke-test-2026!";

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

/** Holt ein frisches Token-Paar per API-Login (kein Cache!). */
async function getFreshTokens(baseURL: string): Promise<TokenPair> {
  const response = await fetch(`${baseURL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: E2E_EMAIL, password: E2E_PASSWORD }),
    signal: AbortSignal.timeout(10_000),
  });

  if (!response.ok) {
    throw new Error(
      `E2E Login fehlgeschlagen: HTTP ${response.status} ${await response.text()}`,
    );
  }

  return (await response.json()) as TokenPair;
}

/**
 * Erweitert den Playwright-Test mit automatischer Auth-Injection.
 * Jede Page bekommt ein eigenes frisches Token-Paar in localStorage
 * gesetzt BEVOR die App lädt (via addInitScript).
 */
export const test = base.extend({
  page: async ({ page, baseURL }, use) => {
    const url = baseURL ?? "https://training.nordliggrad.com";
    const tokens = await getFreshTokens(url);

    // Tokens in localStorage setzen BEVOR irgendeine Seite laedt.
    // addInitScript laeuft vor jedem page.goto() im Document-Context.
    await page.addInitScript(
      ({ access, refresh }) => {
        localStorage.setItem("ta_access_token", access);
        localStorage.setItem("ta_refresh_token", refresh);
        localStorage.setItem(
          "training-analyzer-auth",
          JSON.stringify({
            state: { accessToken: access, refreshToken: refresh },
            version: 0,
          }),
        );
      },
      { access: tokens.access_token, refresh: tokens.refresh_token },
    );

    await use(page);
  },
});

export { expect };
