import type { FullConfig } from "@playwright/test";

const POLL_INTERVAL_MS = 5_000;
const MAX_WAIT_MS = 90_000;

/**
 * Wartet bis der Production-Server vollständig bereit ist, bevor Tests starten.
 * Prüft sowohl /health (inkl. DB-Ping) als auch einen API-Endpoint.
 */
export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL =
    config.projects[0]?.use?.baseURL ?? "http://training.89.167.78.223.sslip.io";

  await waitForHealth(baseURL);
  await waitForAPI(baseURL);
}

async function waitForHealth(baseURL: string): Promise<void> {
  const healthURL = `${baseURL}/health`;
  console.log(`[global-setup] Warte auf Health Check: ${healthURL}`);

  const start = Date.now();

  while (Date.now() - start < MAX_WAIT_MS) {
    try {
      const response = await fetch(healthURL, {
        signal: AbortSignal.timeout(5_000),
      });

      if (response.ok) {
        const body = (await response.json()) as {
          status?: string;
          db?: boolean;
        };
        if (body.status === "ok" && body.db === true) {
          const elapsed = ((Date.now() - start) / 1000).toFixed(1);
          console.log(
            `[global-setup] Server gesund (inkl. DB) nach ${elapsed}s`,
          );
          return;
        }
        console.log(
          `[global-setup] status="${body.status}", db=${body.db} — retry...`,
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

    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }

  throw new Error(
    `[global-setup] Server nicht gesund nach ${MAX_WAIT_MS / 1000}s — Tests abgebrochen`,
  );
}

async function waitForAPI(baseURL: string): Promise<void> {
  const apiURL = `${baseURL}/api/v1/health`;
  console.log(`[global-setup] Prüfe API-Readiness: ${apiURL}`);

  const start = Date.now();
  const apiTimeout = 30_000;

  while (Date.now() - start < apiTimeout) {
    try {
      const response = await fetch(apiURL, {
        signal: AbortSignal.timeout(5_000),
      });

      if (response.ok) {
        const body = (await response.json()) as { status?: string };
        if (body.status === "healthy") {
          const elapsed = ((Date.now() - start) / 1000).toFixed(1);
          console.log(`[global-setup] API bereit nach ${elapsed}s`);
          return;
        }
      }
    } catch {
      // retry
    }

    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }

  throw new Error(
    `[global-setup] API nicht bereit nach ${apiTimeout / 1000}s — Tests abgebrochen`,
  );
}
