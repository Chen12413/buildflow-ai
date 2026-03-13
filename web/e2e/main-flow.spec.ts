import { expect, test } from "@playwright/test";

test.describe("BuildFlow main flow", () => {
  test("user can go from idea to PRD, planning, task breakdown, and demo", async ({ page }) => {
    const projectName = `E2E Project ${Date.now()}`;

    await page.goto("/");
    await expect(page).toHaveURL(/\/$/);

    await page.goto("/projects/new");
    await expect(page).toHaveURL(/\/projects\/new$/);
    await expect(page.getByTestId("project-form")).toBeVisible();

    await page.getByTestId("project-name").fill(projectName);
    await page.getByTestId("project-idea").fill("Generate a PRD, execution plan, task breakdown, and product demo for independent builders.");
    await page.getByTestId("project-target-user").fill("indie hackers, AI product managers, startup teams");
    await page.getByTestId("project-platform").selectOption("web");
    await page.getByTestId("project-constraints").fill("Ship an MVP in one day with strong maintainability and testability.");
    await page.getByTestId("project-submit").click();

    await expect(page).toHaveURL(/\/projects\/[^/]+\/clarify$/);
    await expect(page.getByTestId("page-title")).toBeVisible();

    const answers = page.getByTestId("clarification-answer");
    await expect(answers.first()).toBeVisible();
    const answerCount = await answers.count();
    expect(answerCount).toBeGreaterThanOrEqual(3);

    for (let index = 0; index < answerCount; index += 1) {
      await answers.nth(index).fill(`Answer ${index + 1}: prioritize frequent scenarios, structured output, testing coverage, and iteration speed.`);
    }

    await page.getByTestId("clarification-submit").click();

    await expect(page).toHaveURL(/\/projects\/[^/]+\/prd\?runId=/);
    await expect(page.getByTestId("prd-status")).toBeVisible();
    await expect(page.getByTestId("prd-viewer")).toBeVisible({ timeout: 60_000 });

    const prdDownloadPromise = page.waitForEvent("download");
    await page.getByTestId("prd-export-markdown").click();
    const prdDownload = await prdDownloadPromise;
    expect(prdDownload.suggestedFilename()).toMatch(/-prd\.md$/);

    await page.getByTestId("prd-generate-planning").click();

    await expect(page).toHaveURL(/\/projects\/[^/]+\/planning\?runId=/);
    await expect(page.getByTestId("planning-status")).toBeVisible();
    await expect(page.getByTestId("planning-viewer")).toBeVisible({ timeout: 60_000 });

    const planningDownloadPromise = page.waitForEvent("download");
    await page.getByTestId("planning-export-markdown").click();
    const planningDownload = await planningDownloadPromise;
    expect(planningDownload.suggestedFilename()).toMatch(/-planning\.md$/);

    await page.getByTestId("planning-generate-task-breakdown").click();

    await expect(page).toHaveURL(/\/projects\/[^/]+\/task-breakdown\?runId=/);
    await expect(page.getByTestId("task-breakdown-status")).toBeVisible();
    await expect(page.getByTestId("task-breakdown-viewer")).toBeVisible({ timeout: 60_000 });
    expect(await page.getByTestId("task-breakdown-module").count()).toBeGreaterThan(0);

    const taskDownloadPromise = page.waitForEvent("download");
    await page.getByTestId("task-breakdown-export-markdown").click();
    const taskDownload = await taskDownloadPromise;
    expect(taskDownload.suggestedFilename()).toMatch(/-task-breakdown\.md$/);

    await page.getByTestId("task-breakdown-generate-demo").click();

    await expect(page).toHaveURL(/\/projects\/[^/]+\/demo\?runId=/);
    await expect(page.getByTestId("demo-status")).toBeVisible();
    await expect(page.getByTestId("demo-viewer")).toBeVisible({ timeout: 60_000 });
    expect(await page.getByTestId("demo-screen").count()).toBeGreaterThan(0);
    expect(await page.getByTestId("demo-agent-card").count()).toBeGreaterThan(1);

    const demoDownloadPromise = page.waitForEvent("download");
    await page.getByTestId("demo-export-markdown").click();
    const demoDownload = await demoDownloadPromise;
    expect(demoDownload.suggestedFilename()).toMatch(/-demo\.md$/);
  });
});
