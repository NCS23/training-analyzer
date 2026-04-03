import { defineConfig } from "@playwright/test";
import { AUTH_STATE_PATH } from "./auth-setup";
import fs from "fs";

const PRODUCTION_URL =
  process.env.BASE_URL || "https://training.nordliggrad.com";

// storageState nur nutzen wenn die Datei existiert (auth-setup erfolgreich)
const storageState = fs.existsSync(AUTH_STATE_PATH)
  ? AUTH_STATE_PATH
  : undefined;

export default defineConfig({
  globalSetup: "./global-setup.ts",
  testDir: "./smoke",
  timeout: 30_000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  retries: 2,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL: PRODUCTION_URL,
    storageState,
    screenshot: "only-on-failure",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "mobile",
      use: {
        viewport: { width: 375, height: 812 },
        userAgent:
          "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
      },
    },
    {
      name: "desktop",
      use: {
        viewport: { width: 1280, height: 800 },
      },
    },
  ],
});
