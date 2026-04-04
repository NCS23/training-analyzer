import type { FullConfig } from "@playwright/test";
import { setupAuth } from "./auth-setup";

const POLL_INTERVAL_MS = 5_000;
const MAX_WAIT_MS = 60_000;

/**
 * Wartet bis der Production-Server gesund ist, bevor Tests starten.
 * Prüft Health-Endpoint UND API-Readiness (/api/v1/sessions).
 * Verhindert flaky Tests durch transiente Downtime nach Coolify-Deploy.
 */
export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL =
    config.projects[0]?.use?.baseURL ?? "https://training.nordliggrad.com";
  const healthURL = `${baseURL}/api/v1/health`;
  const apiURL = `${baseURL}/api/v1/auth/status`;

  console.log(`[global-setup] Warte auf Health Check: ${healthURL}`);

  const start = Date.now();

  // Phase 1: Health-Endpoint polling
  while (Date.now() - start < MAX_WAIT_MS) {
    try {
      const response = await fetch(healthURL, {
        signal: AbortSignal.timeout(5_000),
      });

      if (response.ok) {
        const body = (await response.json()) as {
          status?: string;
          database?: boolean;
        };
        if ((body.status === "ok" || body.status === "healthy") && body.database === true) {
          const elapsed = ((Date.now() - start) / 1000).toFixed(1);
          console.log(
            `[global-setup] Server gesund nach ${elapsed}s (DB verbunden)`,
          );
          break;
        }
        console.log(
          `[global-setup] status="${body.status}", database=${body.database} — retry...`,
        );
      } else {
        console.log(
          `[global-setup] HTTP ${response.status} — noch nicht bereit`,
        );
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : String(error);
      console.log(`[global-setup] Fehler: ${message} — retry...`);
    }

    if (Date.now() - start >= MAX_WAIT_MS) {
      throw new Error(
        `[global-setup] Server nicht gesund nach ${MAX_WAIT_MS / 1000}s — Tests abgebrochen`,
      );
    }

    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }

  // Phase 2: Auth-Status prüfen (zeigt ob Backend + Auth korrekt laufen)
  console.log(`[global-setup] Prüfe Auth-Status: ${apiURL}`);
  try {
    const response = await fetch(apiURL, {
      signal: AbortSignal.timeout(10_000),
    });

    if (response.ok) {
      const body = (await response.json()) as { auth_enabled?: boolean };
      console.log(
        `[global-setup] Auth-Status: auth_enabled=${body.auth_enabled}`,
      );
    } else {
      console.warn(
        `[global-setup] Auth-Status HTTP ${response.status}`,
      );
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.warn(
      `[global-setup] Auth-Status-Check fehlgeschlagen: ${message}`,
    );
  }

  // Phase 3: Auth-Setup (E2E Test-User erstellen + Token speichern)
  await setupAuth(baseURL);

  const total = ((Date.now() - start) / 1000).toFixed(1);
  console.log(`[global-setup] Setup abgeschlossen nach ${total}s`);
}
