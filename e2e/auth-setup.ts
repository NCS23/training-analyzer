/**
 * E2E Auth Setup: Erstellt einen Test-User und speichert den Auth-State.
 * Wird von global-setup.ts aufgerufen nachdem der Server gesund ist.
 */
import { chromium } from "@playwright/test";
import path from "path";

// Playwright's tsx-Loader stellt __dirname bereit (CJS-Kompatibilitaet)
export const AUTH_STATE_PATH = path.join(__dirname, ".auth-state.json");

const E2E_EMAIL = "e2e-smoke@training-analyzer.app";
const E2E_PASSWORD = "e2e-smoke-test-2026!";

export async function setupAuth(baseURL: string): Promise<void> {
  console.log("[auth-setup] Erstelle E2E Test-User...");

  // 1. Registrieren (oder Login falls User schon existiert)
  let tokens: { access_token: string; refresh_token: string } | null = null;

  try {
    const registerResp = await fetch(`${baseURL}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: E2E_EMAIL,
        password: E2E_PASSWORD,
        name: "E2E Smoke Test",
      }),
      signal: AbortSignal.timeout(10_000),
    });

    if (registerResp.ok) {
      tokens = (await registerResp.json()) as typeof tokens;
      console.log("[auth-setup] Neuer E2E-User registriert");
    } else if (registerResp.status === 409) {
      // User existiert schon → einloggen
      console.log("[auth-setup] E2E-User existiert, logge ein...");
    } else {
      const body = await registerResp.text();
      console.warn(
        `[auth-setup] Register HTTP ${registerResp.status}: ${body}`,
      );
    }
  } catch (err) {
    console.warn("[auth-setup] Register fehlgeschlagen:", err);
  }

  // Fallback: Login
  if (!tokens) {
    try {
      const loginResp = await fetch(`${baseURL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: E2E_EMAIL, password: E2E_PASSWORD }),
        signal: AbortSignal.timeout(10_000),
      });

      if (loginResp.ok) {
        tokens = (await loginResp.json()) as typeof tokens;
        console.log("[auth-setup] E2E-User eingeloggt");
      } else {
        const body = await loginResp.text();
        console.warn(`[auth-setup] Login HTTP ${loginResp.status}: ${body}`);
      }
    } catch (err) {
      console.warn("[auth-setup] Login fehlgeschlagen:", err);
    }
  }

  if (!tokens) {
    console.warn(
      "[auth-setup] Konnte keinen Auth-Token erhalten — Tests laufen ohne Auth",
    );
    return;
  }

  // 2. Browser starten, Token in localStorage setzen, storageState speichern
  const browser = await chromium.launch();
  const context = await browser.newContext({ baseURL });
  const page = await context.newPage();

  await page.goto("/");
  await page.evaluate(
    ({ access, refresh }) => {
      localStorage.setItem("ta_access_token", access);
      localStorage.setItem("ta_refresh_token", refresh);
      localStorage.setItem(
        "training-analyzer-auth",
        JSON.stringify({
          state: { refreshToken: refresh },
          version: 0,
        }),
      );
    },
    { access: tokens.access_token, refresh: tokens.refresh_token },
  );

  await context.storageState({ path: AUTH_STATE_PATH });
  await browser.close();

  console.log(`[auth-setup] Auth-State gespeichert: ${AUTH_STATE_PATH}`);
}
