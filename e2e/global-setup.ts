import type { FullConfig } from "@playwright/test";

const POLL_INTERVAL_MS = 5_000;
const MAX_WAIT_MS = 60_000;

/**
 * Wartet bis der Production-Server gesund ist, bevor Tests starten.
 * Verhindert flaky Tests durch transiente Downtime nach Coolify-Deploy.
 */
export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL =
    config.projects[0]?.use?.baseURL ?? "http://training.89.167.78.223.sslip.io";
  const healthURL = `${baseURL}/health`;

  console.log(`[global-setup] Warte auf Health Check: ${healthURL}`);

  const start = Date.now();

  while (Date.now() - start < MAX_WAIT_MS) {
    try {
      const response = await fetch(healthURL, {
        signal: AbortSignal.timeout(5_000),
      });

      if (response.ok) {
        const body = (await response.json()) as { status?: string };
        if (body.status === "ok") {
          const elapsed = ((Date.now() - start) / 1000).toFixed(1);
          console.log(
            `[global-setup] Server gesund nach ${elapsed}s`,
          );
          return;
        }
        console.log(
          `[global-setup] HTTP 200 aber status="${body.status}" — retry...`,
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
