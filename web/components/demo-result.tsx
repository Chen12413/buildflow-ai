"use client";

import { useEffect, useMemo, useState } from "react";

import { DemoViewer } from "@/components/demo-viewer";
import { PageShell } from "@/components/page-shell";
import { StatusPanel } from "@/components/status-panel";
import { exportDemoMarkdown, getLatestDemo, getProject, getRun } from "@/lib/api-client";
import { loadArtifactWithPolling } from "@/lib/run-artifact-polling";
import { DemoArtifact, Project } from "@/lib/types";

export function DemoResult({ projectId, runId }: { projectId: string; runId?: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [artifact, setArtifact] = useState<DemoArtifact | null>(null);
  const [status, setStatus] = useState("准备中...");
  const [error, setError] = useState<string | null>(null);

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
          loadArtifact: () => getLatestDemo(projectId),
          loadRun: getRun,
          setArtifact,
          setStatus,
          isCancelled: () => cancelled,
          labels: {
            latestLoadedStatus: "已加载最新产品 Demo",
            initialLoadingStatus: "正在生成产品 Demo...",
            completedStatus: "产品 Demo 生成完成",
            syncingStatus: "产品 Demo 已完成，正在同步产物...",
            slowLoadingStatus: "后台任务耗时较长，仍在自动刷新最新结果...",
            failedStatus: "产品 Demo 生成失败",
          },
        });
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        setError(loadError instanceof Error ? loadError.message : "加载产品 Demo 失败");
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [projectId, runId]);

  const markdown = useMemo(() => artifact?.content_markdown ?? "", [artifact]);

  async function handleExport() {
    const content = await exportDemoMarkdown(projectId);
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${projectId}-demo.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <PageShell stageKey="demo" title={`产品 Demo${project ? ` · ${project.name}` : ""}`} description="Demo Generator 会基于前序产物生成可交互演示区、多 Agent 面板和展示脚本。">
      <div className="space-y-6">
        <StatusPanel
          phaseLabel="产品 Demo"
          status={status}
          error={error}
          artifactReady={Boolean(artifact)}
          testId="demo-status"
          helper="Demo 会在准备好后自动展示，可直接导出 Markdown 或截图用于作品集。"
          actions={
            <button
              type="button"
              onClick={handleExport}
              disabled={!artifact}
              data-testid="demo-export-markdown"
              className="primary-btn"
            >
              导出 Markdown
            </button>
          }
        />

        {artifact ? (
          <div className="space-y-8">
            <div className="glass-card p-6">
              <DemoViewer document={artifact.content_json} />
            </div>
            <div className="glass-card p-5">
              <h2 className="text-lg font-semibold text-white">Markdown 预览</h2>
              <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-300">{markdown}</pre>
            </div>
          </div>
        ) : (
          <div className="glass-card soft-grid p-6 text-sm leading-6 text-slate-300">暂时还没有可展示的产品 Demo，生成完成后会自动出现。</div>
        )}
      </div>
    </PageShell>
  );
}