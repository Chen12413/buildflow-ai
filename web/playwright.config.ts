import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3010";
const apiBaseURL = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8010";
const apiPythonBin =
  process.env.E2E_PYTHON_BIN ??
  (process.platform === "win32" ? ".\\.venv\\Scripts\\python.exe" : "./.venv/bin/python");

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: {
    timeout: 20_000,
  },
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  outputDir: "test-results",
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL,
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: [
    {
      command: `${apiPythonBin} -m uvicorn app.main:app --host 127.0.0.1 --port 8010`,
      cwd: "../api",
      url: `${apiBaseURL}/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...process.env,
        LLM_PROVIDER: "mock",
        DATABASE_URL: "sqlite+pysqlite:///./buildflow.e2e.db",
        CORS_ALLOW_ORIGINS: JSON.stringify([baseURL]),
      },
    },
    {
      command: "npm run dev -- --hostname 127.0.0.1 --port 3010",
      cwd: ".",
      url: baseURL,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_BASE_URL: apiBaseURL,
      },
    },
  ],
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
});
