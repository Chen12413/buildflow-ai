"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { PrdViewer } from "@/components/prd-viewer";
import { StatusPanel } from "@/components/status-panel";
import { exportMarkdown, generatePlanning, getLatestPrd, getProject, getRun } from "@/lib/api-client";
import { normalizeProjectName } from "@/lib/project-name";
import { loadArtifactWithPolling } from "@/lib/run-artifact-polling";
import { Project, PrdArtifact } from "@/lib/types";

export function PrdResult({ projectId, runId }: { projectId: string; runId?: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [artifact, setArtifact] = useState<PrdArtifact | null>(null);
  const [status, setStatus] = useState("准备中...");
  const [error, setError] = useState<string | null>(null);
  const [planningLoading, setPlanningLoading] = useState(false);

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
          loadArtifact: () => getLatestPrd(projectId),
          loadRun: getRun,
          setArtifact,
          setStatus,
          isCancelled: () => cancelled,
          labels: {
            latestLoadedStatus: "已加载最新 PRD",
            initialLoadingStatus: "正在生成 PRD...",
            completedStatus: "PRD 生成完成",
            syncingStatus: "PRD 已完成，正在同步产物...",
            slowLoadingStatus: "后台任务耗时较长，仍在自动刷新最新结果...",
            failedStatus: "PRD 生成失败",
          },
        });
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        setError(loadError instanceof Error ? loadError.message : "加载 PRD 失败");
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
    const content = await exportMarkdown(projectId);
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${projectId}-prd.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function handleGeneratePlanning() {
    setPlanningLoading(true);
    setError(null);
    try {
      const result = await generatePlanning(projectId);
      router.push(`/projects/${projectId}/planning?runId=${result.run.id}`);
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "生成开发规划失败");
      setPlanningLoading(false);
    }
  }

  return (
    <PageShell
      stageKey="prd"
      title={`PRD 结果${normalizedProjectName ? ` · ${normalizedProjectName}` : ""}`}
      description="系统会输出结构化 PRD，并保留可导出的 Markdown 版本。"
    >
      <div className="space-y-6">
        <StatusPanel
          phaseLabel="PRD 生成"
          status={status}
          error={error}
          artifactReady={Boolean(artifact)}
          testId="prd-status"
          helper="产物生成后会自动显示在页面中，你可以直接继续下一阶段。"
          actions={
            <>
              <button
                type="button"
                onClick={handleGeneratePlanning}
                disabled={!artifact || planningLoading}
                data-testid="prd-generate-planning"
                className="secondary-btn"
              >
                {planningLoading ? "生成中..." : "继续生成开发规划"}
              </button>
              <button
                type="button"
                onClick={handleExport}
                disabled={!artifact}
                data-testid="prd-export-markdown"
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
              <PrdViewer document={artifact.content_json} />
            </div>
            <div className="glass-card p-5">
              <h2 className="text-lg font-semibold text-white">Markdown 预览</h2>
              <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-300">{markdown}</pre>
            </div>
          </div>
        ) : (
          <div className="glass-card soft-grid p-6 text-sm leading-6 text-slate-300">暂时还没有可展示的 PRD，生成完成后会自动出现。</div>
        )}
      </div>
    </PageShell>
  );
}
