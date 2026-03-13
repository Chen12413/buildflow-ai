import { ReactNode } from "react";

import { ProgressBar } from "@/components/progress-bar";

function inferProgress(status: string, artifactReady: boolean, hasError: boolean) {
  if (hasError || artifactReady) {
    return 100;
  }

  if (status.includes("同步")) {
    return 92;
  }

  if (status.includes("自动刷新") || status.includes("耗时较长")) {
    return 86;
  }

  if (status.includes("生成")) {
    return 68;
  }

  if (status.includes("加载")) {
    return 52;
  }

  return 24;
}

function inferTone(status: string, artifactReady: boolean, hasError: boolean): "sky" | "emerald" | "amber" | "rose" {
  if (hasError) {
    return "rose";
  }

  if (artifactReady) {
    return "emerald";
  }

  if (status.includes("自动刷新") || status.includes("耗时较长")) {
    return "amber";
  }

  return "sky";
}

function inferBadge(status: string, artifactReady: boolean, hasError: boolean) {
  if (hasError) {
    return { text: "需处理", className: "border-rose-400/30 bg-rose-400/10 text-rose-200" };
  }

  if (artifactReady) {
    return { text: "已完成", className: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200" };
  }

  if (status.includes("自动刷新") || status.includes("耗时较长")) {
    return { text: "持续刷新中", className: "border-amber-400/30 bg-amber-400/10 text-amber-100" };
  }

  if (status.includes("同步")) {
    return { text: "同步中", className: "border-sky-400/30 bg-sky-400/10 text-sky-100" };
  }

  return { text: "运行中", className: "border-sky-400/30 bg-sky-400/10 text-sky-100" };
}

function inferHelper(status: string, artifactReady: boolean, hasError: boolean) {
  if (hasError) {
    return "请检查 Provider、网络或额度配置后重试。";
  }

  if (artifactReady) {
    return "结果已经准备好，可以继续下一阶段或导出 Markdown。";
  }

  if (status.includes("自动刷新") || status.includes("耗时较长")) {
    return "任务耗时偏长时，页面仍会继续自动刷新，无需手动刷新页面。";
  }

  return "页面会自动轮询后端状态，通常 1-5 分钟内可以看到结果。";
}

export function StatusPanel({
  title = "当前状态",
  phaseLabel,
  status,
  error,
  artifactReady,
  testId,
  actions,
  progress,
  helper,
}: {
  title?: string;
  phaseLabel: string;
  status: string;
  error?: string | null;
  artifactReady: boolean;
  testId?: string;
  actions?: ReactNode;
  progress?: number;
  helper?: string;
}) {
  const message = error ?? status;
  const hasError = Boolean(error);
  const tone = inferTone(status, artifactReady, hasError);
  const badge = inferBadge(status, artifactReady, hasError);
  const resolvedProgress = progress ?? inferProgress(status, artifactReady, hasError);
  const resolvedHelper = helper ?? inferHelper(status, artifactReady, hasError);

  return (
    <div className="glass-card relative overflow-hidden px-5 py-5 md:px-6 md:py-6">
      <div className="absolute -right-10 -top-10 h-28 w-28 rounded-full bg-sky-400/10 blur-3xl" />
      <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 flex-1 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="section-label">{phaseLabel}</span>
            <span className={`stage-pill ${badge.className}`}>{badge.text}</span>
          </div>

          <div>
            <p className="text-sm font-semibold text-white">{title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-300" data-testid={testId}>
              {message}
            </p>
          </div>

          <ProgressBar value={resolvedProgress} tone={tone} helper={resolvedHelper} />
        </div>

        {actions ? <div className="flex flex-wrap gap-3 lg:justify-end">{actions}</div> : null}
      </div>
    </div>
  );
}