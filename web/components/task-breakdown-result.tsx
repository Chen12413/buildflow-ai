"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { StatusPanel } from "@/components/status-panel";
import { TaskBreakdownViewer } from "@/components/task-breakdown-viewer";
import { exportTaskBreakdownMarkdown, generateDemo, getLatestTaskBreakdown, getProject, getRun } from "@/lib/api-client";
import { loadArtifactWithPolling } from "@/lib/run-artifact-polling";
import { Project, TaskBreakdownArtifact } from "@/lib/types";

export function TaskBreakdownResult({ projectId, runId }: { projectId: string; runId?: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [artifact, setArtifact] = useState<TaskBreakdownArtifact | null>(null);
  const [status, setStatus] = useState("准备中...");
  const [error, setError] = useState<string | null>(null);
  const [demoLoading, setDemoLoading] = useState(false);

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
          loadArtifact: () => getLatestTaskBreakdown(projectId),
          loadRun: getRun,
          setArtifact,
          setStatus,
          isCancelled: () => cancelled,
          labels: {
            latestLoadedStatus: "已加载最新模块任务拆解",
            initialLoadingStatus: "正在生成模块任务拆解...",
            completedStatus: "模块任务拆解生成完成",
            syncingStatus: "模块任务拆解已完成，正在同步产物...",
            slowLoadingStatus: "后台任务耗时较长，仍在自动刷新最新结果...",
            failedStatus: "模块任务拆解生成失败",
          },
        });
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        setError(loadError instanceof Error ? loadError.message : "加载模块任务拆解失败");
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [projectId, runId]);

  const markdown = useMemo(() => artifact?.content_markdown ?? "", [artifact]);

  async function handleExport() {
    const content = await exportTaskBreakdownMarkdown(projectId);
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${projectId}-task-breakdown.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function handleGenerateDemo() {
    setDemoLoading(true);
    setError(null);
    try {
      const result = await generateDemo(projectId);
      router.push(`/projects/${projectId}/demo?runId=${result.run.id}`);
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "生成产品 Demo 失败");
      setDemoLoading(false);
    }
  }

  return (
    <PageShell
      stageKey="task-breakdown"
      title={`模块任务拆解${project ? ` · ${project.name}` : ""}`}
      description="Task Breakdown Agent 会把 PRD 和开发规划继续拆到模块、任务、验收标准和测试清单。"
    >
      <div className="space-y-6">
        <StatusPanel
          phaseLabel="模块任务拆解"
          status={status}
          error={error}
          artifactReady={Boolean(artifact)}
          testId="task-breakdown-status"
          helper="拆解完成后可以直接继续生成产品 Demo，形成更强的演示闭环。"
          actions={
            <>
              <button
                type="button"
                onClick={handleGenerateDemo}
                disabled={!artifact || demoLoading}
                data-testid="task-breakdown-generate-demo"
                className="secondary-btn"
              >
                {demoLoading ? "生成中..." : "继续生成产品 Demo"}
              </button>
              <button
                type="button"
                onClick={handleExport}
                disabled={!artifact}
                data-testid="task-breakdown-export-markdown"
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
              <TaskBreakdownViewer document={artifact.content_json} />
            </div>
            <div className="glass-card p-5">
              <h2 className="text-lg font-semibold text-white">Markdown 预览</h2>
              <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-300">{markdown}</pre>
            </div>
          </div>
        ) : (
          <div className="glass-card soft-grid p-6 text-sm leading-6 text-slate-300">暂时还没有可展示的模块任务拆解，生成完成后会自动出现。</div>
        )}
      </div>
    </PageShell>
  );
}