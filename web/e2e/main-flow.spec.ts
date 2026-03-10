import { expect, test } from "@playwright/test";

test.describe("BuildFlow main flow", () => {
  test("user can go from idea to PRD and planning", async ({ page }) => {
    const projectName = `E2E Project ${Date.now()}`;

    await page.goto("/");
    await expect(page).toHaveURL(/\/$/);

    await page.goto("/projects/new");
    await expect(page).toHaveURL(/\/projects\/new$/);
    await expect(page.getByTestId("project-form")).toBeVisible();

    await page.getByTestId("project-name").fill(projectName);
    await page.getByTestId("project-idea").fill("Generate a PRD and implementation plan for independent builders.");
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
      await answers
        .nth(index)
        .fill(`Answer ${index + 1}: prioritize frequent scenarios, structured output, testing coverage, and iteration speed.`);
    }

    await page.getByTestId("clarification-submit").click();

    await expect(page).toHaveURL(/\/projects\/[^/]+\/prd\?runId=/);
    await expect(page.getByTestId("prd-status")).toBeVisible();
    await expect(page.getByTestId("prd-viewer")).toBeVisible({ timeout: 60_000 });
    await expect(page.getByTestId("prd-section-product_summary")).toBeVisible();
    await expect(page.getByTestId("prd-section-success_metrics")).toBeVisible();

    const prdDownloadPromise = page.waitForEvent("download");
    await page.getByTestId("prd-export-markdown").click();
    const prdDownload = await prdDownloadPromise;
    expect(prdDownload.suggestedFilename()).toMatch(/-prd\.md$/);

    await page.getByTestId("prd-generate-planning").click();

    await expect(page).toHaveURL(/\/projects\/[^/]+\/planning\?runId=/);
    await expect(page.getByTestId("planning-status")).toBeVisible();
    await expect(page.getByTestId("planning-viewer")).toBeVisible({ timeout: 60_000 });

    const milestoneCount = await page.getByTestId("planning-milestone").count();
    expect(milestoneCount).toBeGreaterThan(0);

    const planningDownloadPromise = page.waitForEvent("download");
    await page.getByTestId("planning-export-markdown").click();
    const planningDownload = await planningDownloadPromise;
    expect(planningDownload.suggestedFilename()).toMatch(/-planning\.md$/);
  });
});
