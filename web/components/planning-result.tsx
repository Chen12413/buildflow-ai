"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { PlanningViewer } from "@/components/planning-viewer";
import { StatusPanel } from "@/components/status-panel";
import { exportPlanningMarkdown, generateTaskBreakdown, getLatestPlanning, getProject, getRun } from "@/lib/api-client";
import { normalizeProjectName } from "@/lib/project-name";
import { loadArtifactWithPolling } from "@/lib/run-artifact-polling";
import { PlanningArtifact, Project } from "@/lib/types";

export function PlanningResult({ projectId, runId }: { projectId: string; runId?: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [artifact, setArtifact] = useState<PlanningArtifact | null>(null);
  const [status, setStatus] = useState("准备中...");
  const [error, setError] = useState<string | null>(null);
  const [taskBreakdownLoading, setTaskBreakdownLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        setError(null);
        const nextProject = await getProject(projectId);
        if (cancelled) {
          return;
        }

        setProject(nextProject);
        await loadArtifactWithPolling({
          runId,
          loadArtifact: () => getLatestPlanning(projectId),
          loadRun: getRun,
          setArtifact,
          setStatus,
          isCancelled: () => cancelled,
          labels: {
            latestLoadedStatus: "已加载最新开发规划",
            initialLoadingStatus: "正在生成开发规划...",
            completedStatus: "开发规划生成完成",
            syncingStatus: "开发规划已完成，正在同步产物...",
            slowLoadingStatus: "后台任务耗时较长，仍在自动刷新最新结果...",
            failedStatus: "开发规划生成失败",
          },
        });
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        setError(loadError instanceof Error ? loadError.message : "加载开发规划失败");
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [projectId, runId]);

  const markdown = useMemo(() => artifact?.content_markdown ?? "", [artifact]);
  const normalizedProjectName = useMemo(() => normalizeProjectName(project?.name), [project?.name]);

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

  async function handleGenerateTaskBreakdown() {
    setTaskBreakdownLoading(true);
    setError(null);
    try {
      const result = await generateTaskBreakdown(projectId);
      router.push(`/projects/${projectId}/task-breakdown?runId=${result.run.id}`);
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "生成模块任务拆解失败");
      setTaskBreakdownLoading(false);
    }
  }

  return (
    <PageShell
      stageKey="planning"
      title={`开发规划${normalizedProjectName ? ` · ${normalizedProjectName}` : ""}`}
      description="Planning Agent 会基于最新 PRD 输出里程碑、任务与测试重点。"
    >
      <div className="space-y-6">
        <StatusPanel
          phaseLabel="开发规划"
          status={status}
          error={error}
          artifactReady={Boolean(artifact)}
          testId="planning-status"
          helper="规划完成后建议继续生成模块任务拆解，形成更细的交付清单。"
          actions={
            <>
              <button
                type="button"
                onClick={handleGenerateTaskBreakdown}
                disabled={!artifact || taskBreakdownLoading}
                data-testid="planning-generate-task-breakdown"
                className="secondary-btn"
              >
                {taskBreakdownLoading ? "生成中..." : "继续生成模块任务拆解"}
              </button>
              <button
                type="button"
                onClick={handleExport}
                disabled={!artifact}
                data-testid="planning-export-markdown"
                className="primary-btn"
              >
                导出 Markdown
              </button>
            </>
          }
        />

        {artifact ? (
          <div className="space-y-8">
            <div className="glass-card p-6">
              <PlanningViewer document={artifact.content_json} />
            </div>
            <div className="glass-card p-5">
              <h2 className="text-lg font-semibold text-white">Markdown 预览</h2>
              <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-300">{markdown}</pre>
            </div>
          </div>
        ) : (
          <div className="glass-card soft-grid p-6 text-sm leading-6 text-slate-300">暂时还没有可展示的开发规划，生成完成后会自动出现。</div>
        )}
      </div>
    </PageShell>
  );
}
