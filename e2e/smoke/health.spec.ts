import { test, expect } from "@playwright/test";

test.describe("Health Check", () => {
  test("backend /health returns ok", async ({ request }) => {
    const response = await request.get("/health");
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("ok");
  });

  test("API /api/v1/health returns healthy", async ({ request }) => {
    const response = await request.get("/api/v1/health");
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("healthy");
  });

  test("frontend serves HTML at /", async ({ request }) => {
    const response = await request.get("/");
    expect(response.status()).toBe(200);
    const contentType = response.headers()["content-type"] || "";
    expect(contentType).toContain("text/html");
  });
});
