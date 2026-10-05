import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: process.env.CI ? 60000 : 30000,
  workers: 1,
  reporter: [["list"], ["json", { outputFile: "test-results/results.json" }]],
  use: { trace: "retain-on-failure" },
  webServer: {
    command: `"${process.env.E2E_PYTHON || "python3"}" -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
    cwd: "../backend",
    url: "http://127.0.0.1:8000/api/v1/health",
    reuseExistingServer: false,
    env: { LLM_PROVIDER: "mock", ENVIRONMENT: "test" },
  },
});
