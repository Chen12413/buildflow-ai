"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { PrdViewer } from "@/components/prd-viewer";
import { exportMarkdown, generatePlanning, getLatestPrd, getProject, getRun } from "@/lib/api-client";
import { Project, PrdArtifact } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 180000;

function sleep(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export function PrdResult({ projectId, runId }: { projectId: string; runId?: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [artifact, setArtifact] = useState<PrdArtifact | null>(null);
  const [status, setStatus] = useState("准备中...");
  const [error, setError] = useState<string | null>(null);
  const [planningLoading, setPlanningLoading] = useState(false);

  useEffect(() => {
    async function bootstrap() {
      try {
        setProject(await getProject(projectId));

        if (!runId) {
          setArtifact(await getLatestPrd(projectId));
          setStatus("已加载最新 PRD");
          return;
        }

        setStatus("正在生成 PRD...");
        const deadline = Date.now() + POLL_TIMEOUT_MS;

        while (Date.now() < deadline) {
          const run = await getRun(runId);
          if (run.status === "completed") {
            try {
              setArtifact(await getLatestPrd(projectId));
              setStatus("PRD 生成完成");
              return;
            } catch {
              setStatus("PRD 已完成，正在同步产物...");
            }
          }

          if (run.status === "failed") {
            throw new Error(run.error_message ?? "PRD 生成失败");
          }

          await sleep(POLL_INTERVAL_MS);
        }

        try {
          setArtifact(await getLatestPrd(projectId));
          setStatus("PRD 已生成，页面已同步最新结果");
        } catch {
          setStatus("后台任务耗时较长，请稍后刷新页面查看结果。");
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "加载 PRD 失败");
      }
    }

    void bootstrap();
  }, [projectId, runId]);

  const markdown = useMemo(() => artifact?.content_markdown ?? "", [artifact]);

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
    <PageShell title={`PRD 结果${project ? ` · ${project.name}` : ""}`} description="系统输出固定结构的 PRD，并同步保留 Markdown 导出版。">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-950/50 px-4 py-3">
        <div>
          <p className="text-sm font-medium text-white">当前状态</p>
          <p className="text-sm text-slate-300" data-testid="prd-status">{error ?? status}</p>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleGeneratePlanning}
            disabled={!artifact || planningLoading}
            data-testid="prd-generate-planning"
            className="rounded-lg border border-sky-400 px-4 py-2 text-sm font-medium text-sky-300 hover:bg-sky-500/10 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500"
          >
            {planningLoading ? "生成中..." : "生成开发规划"}
          </button>
          <button
            type="button"
            onClick={handleExport}
            disabled={!artifact}
            data-testid="prd-export-markdown"
            className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-300"
          >
            导出 Markdown
          </button>
        </div>
      </div>

      {artifact ? (
        <>
          <PrdViewer document={artifact.content_json} />
          <div className="mt-8 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <h2 className="mb-3 text-lg font-semibold text-white">Markdown 预览</h2>
            <pre className="overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-300">{markdown}</pre>
          </div>
        </>
      ) : (
        <p className="text-sm text-slate-300">当前还没有可展示的 PRD 结果。</p>
      )}
    </PageShell>
  );
}
