"use client";

import { useEffect, useMemo, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { PlanningViewer } from "@/components/planning-viewer";
import { exportPlanningMarkdown, getLatestPlanning, getProject, getRun } from "@/lib/api-client";
import { PlanningArtifact, Project } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 180000;

function sleep(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export function PlanningResult({ projectId, runId }: { projectId: string; runId?: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [artifact, setArtifact] = useState<PlanningArtifact | null>(null);
  const [status, setStatus] = useState("准备中...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        setProject(await getProject(projectId));

        if (!runId) {
          setArtifact(await getLatestPlanning(projectId));
          setStatus("已加载最新开发规划");
          return;
        }

        setStatus("正在生成开发规划...");
        const deadline = Date.now() + POLL_TIMEOUT_MS;

        while (Date.now() < deadline) {
          const run = await getRun(runId);
          if (run.status === "completed") {
            try {
              setArtifact(await getLatestPlanning(projectId));
              setStatus("开发规划生成完成");
              return;
            } catch {
              setStatus("开发规划已完成，正在同步产物...");
            }
          }

          if (run.status === "failed") {
            throw new Error(run.error_message ?? "开发规划生成失败");
          }

          await sleep(POLL_INTERVAL_MS);
        }

        try {
          setArtifact(await getLatestPlanning(projectId));
          setStatus("开发规划已生成，页面已同步最新结果");
        } catch {
          setStatus("后台任务耗时较长，请稍后刷新页面查看结果。");
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "加载开发规划失败");
      }
    }

    void bootstrap();
  }, [projectId, runId]);

  const markdown = useMemo(() => artifact?.content_markdown ?? "", [artifact]);

  async function handleExport() {
    const content = await exportPlanningMarkdown(projectId);
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${projectId}-planning.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <PageShell title={`开发规划${project ? ` · ${project.name}` : ""}`} description="Planning Agent 基于最新 PRD 输出里程碑、任务拆解和测试关注点。">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-950/50 px-4 py-3">
        <div>
          <p className="text-sm font-medium text-white">当前状态</p>
          <p className="text-sm text-slate-300" data-testid="planning-status">{error ?? status}</p>
        </div>
        <button
          type="button"
          onClick={handleExport}
          disabled={!artifact}
          data-testid="planning-export-markdown"
          className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-300"
        >
          导出 Markdown
        </button>
      </div>

      {artifact ? (
        <>
          <PlanningViewer document={artifact.content_json} />
          <div className="mt-8 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <h2 className="mb-3 text-lg font-semibold text-white">Markdown 预览</h2>
            <pre className="overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-300">{markdown}</pre>
          </div>
        </>
      ) : (
        <p className="text-sm text-slate-300">当前还没有可展示的开发规划结果。</p>
      )}
    </PageShell>
  );
}
