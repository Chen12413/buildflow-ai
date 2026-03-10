import { expect, test } from "@playwright/test";

test.describe("BuildFlow 主链路", () => {
  test("用户可以从想法走到 PRD 与 Planning", async ({ page }) => {
    const projectName = `E2E 项目 ${Date.now()}`;

    await page.goto("/");
    await expect(page.getByRole("heading", { name: /用一条主链路/ })).toBeVisible();

    await page.getByRole("link", { name: "开始创建项目" }).click();
    await expect(page).toHaveURL(/\/projects\/new$/);

    await page.getByTestId("project-name").fill(projectName);
    await page.getByTestId("project-idea").fill("为独立开发者和 AI 产品经理提供从想法到 PRD 与开发规划的一站式生成能力。");
    await page.getByTestId("project-target-user").fill("独立开发者、AI 产品经理、创业团队");
    await page.getByTestId("project-platform").selectOption("web");
    await page.getByTestId("project-constraints").fill("一天内完成 MVP，优先保证可维护性、可测试性和演示效果。");
    await page.getByTestId("project-submit").click();

    await expect(page).toHaveURL(/\/projects\/[^/]+\/clarify$/);
    await expect(page.getByRole("heading", { name: /澄清问答/ })).toBeVisible();

    const answers = page.getByTestId("clarification-answer");
    await expect(answers.first()).toBeVisible();
    const answerCount = await answers.count();
    expect(answerCount).toBeGreaterThanOrEqual(3);

    for (let index = 0; index < answerCount; index += 1) {
      await answers
        .nth(index)
        .fill(`第 ${index + 1} 个回答：优先覆盖高频场景，突出结构化输出、测试闭环和版本迭代能力。`);
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
