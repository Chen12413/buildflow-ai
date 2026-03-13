import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webDir = process.env.BUILD_FLOW_WEB_WORKSPACE?.trim()
  ? path.resolve(process.env.BUILD_FLOW_WEB_WORKSPACE.trim())
  : path.resolve(__dirname, "..");
const repoRoot = process.env.BUILD_FLOW_REPO_ROOT?.trim()
  ? path.resolve(process.env.BUILD_FLOW_REPO_ROOT.trim())
  : path.resolve(webDir, "..");
const apiDir = path.resolve(repoRoot, "api");
const outputDir = process.env.BUILD_FLOW_OUTPUT_DIR?.trim()
  ? path.resolve(process.env.BUILD_FLOW_OUTPUT_DIR.trim())
  : path.resolve(repoRoot, "docs", "assets", "screenshots");

const webPort = Number(process.env.BUILD_FLOW_SHOWCASE_WEB_PORT ?? 3020);
const apiPort = Number(process.env.BUILD_FLOW_SHOWCASE_API_PORT ?? 8020);
const baseURL = `http://127.0.0.1:${webPort}`;
const apiBaseURL = `http://127.0.0.1:${apiPort}`;

const pythonBin =
  process.platform === "win32"
    ? path.resolve(apiDir, ".venv", "Scripts", "python.exe")
    : path.resolve(apiDir, ".venv", "bin", "python");
const npmBin = process.platform === "win32" ? "npm.cmd" : "npm";

function assertExists(targetPath, label) {
  if (!existsSync(targetPath)) {
    throw new Error(`${label} not found: ${targetPath}`);
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForReady(url, label, timeoutMs = 120000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.status >= 200 && response.status < 500) {
        return;
      }
    } catch {}
    await delay(1500);
  }
  throw new Error(`${label} did not become ready in time: ${url}`);
}

async function killProcessTree(child) {
  if (!child || child.exitCode !== null) {
    return;
  }

  if (process.platform === "win32") {
    await new Promise((resolve) => {
      const killer = spawn("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
        stdio: "ignore",
        windowsHide: true,
      });
      killer.on("exit", () => resolve());
      killer.on("error", () => resolve());
    });
    return;
  }

  child.kill("SIGTERM");
  await delay(1000);
  if (child.exitCode === null) {
    child.kill("SIGKILL");
  }
}

function startProcess(command, args, options) {
  const child = spawn(command, args, {
    stdio: "inherit",
    shell: false,
    ...options,
  });

  child.on("error", (error) => {
    console.error(`[showcase] Failed to start ${command}:`, error);
  });

  return child;
}

async function screenshotElement(page, locator, fileName) {
  await locator.waitFor({ state: "visible", timeout: 60000 });
  await locator.screenshot({ path: path.join(outputDir, fileName) });
}

async function main() {
  assertExists(pythonBin, "Python virtual environment");
  assertExists(path.resolve(webDir, "node_modules"), "web/node_modules");

  await mkdir(outputDir, { recursive: true });

  const apiProcess = startProcess(
    pythonBin,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(apiPort)],
    {
      cwd: apiDir,
      env: {
        ...process.env,
        LLM_PROVIDER: "mock",
        DATABASE_URL: "sqlite+pysqlite:///./buildflow.showcase.db",
        CORS_ALLOW_ORIGINS: JSON.stringify([baseURL]),
      },
    },
  );

  const webCommand =
    process.platform === "win32"
      ? ["/c", npmBin, "run", "dev", "--", "--hostname", "127.0.0.1", "--port", String(webPort)]
      : ["run", "dev", "--", "--hostname", "127.0.0.1", "--port", String(webPort)];

  const webProcess = startProcess(
    process.platform === "win32" ? "cmd.exe" : npmBin,
    webCommand,
    {
      cwd: webDir,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_BASE_URL: apiBaseURL,
      },
    },
  );

  try {
    await waitForReady(`${apiBaseURL}/health`, "API");
    await waitForReady(baseURL, "Web");

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

    const projectName = `BuildFlow Showcase ${Date.now()}`;

    await page.goto(baseURL, { waitUntil: "networkidle" });
    await page.screenshot({ path: path.join(outputDir, "home.png"), fullPage: false });

    await page.goto(`${baseURL}/projects/new`, { waitUntil: "networkidle" });
    await page.getByTestId("project-name").fill(projectName);
    await page.getByTestId("project-idea").fill("Turn raw product ideas into PRD, planning, task breakdown, and demo artifacts.");
    await page.getByTestId("project-target-user").fill("Indie hackers, AI product managers, startup teams");
    await page.getByTestId("project-platform").selectOption("web");
    await page.getByTestId("project-constraints").fill("Build an MVP in one day, keep the codebase maintainable, and make it portfolio-ready.");
    await page.screenshot({ path: path.join(outputDir, "new-project.png"), fullPage: false });

    await page.getByTestId("project-submit").click();
    await page.waitForURL(/\/projects\/[^/]+\/clarify$/);
    await page.locator('[data-testid="clarification-answer"]').first().waitFor({ state: "visible" });
    await page.screenshot({ path: path.join(outputDir, "clarification.png"), fullPage: false });

    const answers = page.getByTestId("clarification-answer");
    const answerCount = await answers.count();
    for (let index = 0; index < answerCount; index += 1) {
      await answers
        .nth(index)
        .fill(`Showcase answer ${index + 1}: focus on high-frequency scenarios, structured outputs, testing, long-term iteration, and showcase value.`);
    }

    await page.getByTestId("clarification-submit").click();
    await page.waitForURL(/\/projects\/[^/]+\/prd\?runId=/);
    await page.locator('[data-testid="prd-viewer"]').waitFor({ state: "visible", timeout: 60000 });
    await page.screenshot({ path: path.join(outputDir, "prd.png"), fullPage: false });

    await page.getByTestId("prd-generate-planning").click();
    await page.waitForURL(/\/projects\/[^/]+\/planning\?runId=/);
    await page.locator('[data-testid="planning-viewer"]').waitFor({ state: "visible", timeout: 60000 });
    await page.screenshot({ path: path.join(outputDir, "planning.png"), fullPage: false });

    await page.getByTestId("planning-generate-task-breakdown").click();
    await page.waitForURL(/\/projects\/[^/]+\/task-breakdown\?runId=/);
    await page.locator('[data-testid="task-breakdown-viewer"]').waitFor({ state: "visible", timeout: 60000 });
    await page.screenshot({ path: path.join(outputDir, "task-breakdown.png"), fullPage: false });

    await page.getByTestId("task-breakdown-generate-demo").click();
    await page.waitForURL(/\/projects\/[^/]+\/demo\?runId=/);
    await page.locator('[data-testid="demo-viewer"]').waitFor({ state: "visible", timeout: 60000 });
    await page.screenshot({ path: path.join(outputDir, "demo-overview.png"), fullPage: false });

    await page.getByRole("button", { name: "Demo Studio" }).click();
    await page.locator('[data-testid="demo-screen"]').waitFor({ state: "visible", timeout: 60000 });
    await screenshotElement(page, page.locator('[data-testid="demo-screen"]'), "demo-studio.png");

    await screenshotElement(page, page.locator('[data-testid="demo-agent-card"]').first(), "agent-card.png");
    await screenshotElement(page, page.locator('[data-testid="agent-run-panel"]'), "agent-panel.png");

    await browser.close();
  } finally {
    await killProcessTree(webProcess);
    await killProcessTree(apiProcess);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
