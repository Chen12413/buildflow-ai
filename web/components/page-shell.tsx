import { ReactNode } from "react";

const FLOW_STEPS = [
  { key: "create", label: "Create", title: "录入项目", description: "收集产品想法、目标用户、平台与约束。" },
  { key: "clarify", label: "Clarify", title: "澄清问题", description: "补齐边界、成功标准和 MVP 约束。" },
  { key: "prd", label: "PRD", title: "生成 PRD", description: "沉淀结构化产品文档与 Markdown。" },
  { key: "planning", label: "Planning", title: "开发规划", description: "输出里程碑、任务与测试重点。" },
  { key: "task-breakdown", label: "Tasks", title: "模块拆解", description: "拆成可执行模块、任务与验收项。" },
  { key: "demo", label: "Demo", title: "生成 Demo", description: "产出可展示 Demo 与多 Agent 面板。" },
] as const;

type PageStageKey = (typeof FLOW_STEPS)[number]["key"];

export function PageShell({
  title,
  description,
  children,
  stageKey,
  badge = "单主链路 Agent Workflow",
  contentClassName = "",
}: {
  title: string;
  description: string;
  children: ReactNode;
  stageKey?: PageStageKey;
  badge?: string;
  contentClassName?: string;
}) {
  const currentIndex = stageKey ? FLOW_STEPS.findIndex((step) => step.key === stageKey) : -1;
  const currentStep = currentIndex >= 0 ? FLOW_STEPS[currentIndex] : null;

  return (
    <main className="space-y-6">
      <section className="hero-panel px-6 py-6 md:px-8 md:py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="section-label">{badge}</span>
          {currentStep ? (
            <span className="stage-pill border-white/10 bg-white/5 text-slate-200">
              Step {currentIndex + 1} / {FLOW_STEPS.length}
            </span>
          ) : null}
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px] lg:items-end">
          <div>
            <h1 className="max-w-4xl text-3xl font-bold leading-tight text-white md:text-4xl" data-testid="page-title">
              {title}
            </h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 md:text-base">{description}</p>
          </div>

          {currentStep ? (
            <div className="glass-card soft-grid p-5">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">当前阶段</p>
              <p className="mt-2 text-xl font-semibold text-white">{currentStep.title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-300">{currentStep.description}</p>
            </div>
          ) : null}
        </div>

        {currentStep ? (
          <div className="mt-6 grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
            {FLOW_STEPS.map((step, index) => {
              const isActive = step.key === stageKey;
              const isCompleted = index < currentIndex;

              return (
                <div
                  key={step.key}
                  className={`rounded-2xl border px-4 py-3 transition ${
                    isActive
                      ? "border-sky-400/40 bg-sky-400/12 shadow-[0_16px_40px_-24px_rgba(56,189,248,0.8)]"
                      : isCompleted
                        ? "border-emerald-400/20 bg-emerald-400/8"
                        : "border-white/10 bg-white/5"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">{step.label}</span>
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${
                        isActive ? "bg-sky-300 shadow-[0_0_14px_rgba(125,211,252,0.9)]" : isCompleted ? "bg-emerald-300" : "bg-slate-600"
                      }`}
                    />
                  </div>
                  <p className="mt-2 text-sm font-medium text-white">{step.title}</p>
                </div>
              );
            })}
          </div>
        ) : null}
      </section>

      <section className={`glass-card px-5 py-5 md:px-6 md:py-6 ${contentClassName}`}>{children}</section>
    </main>
  );
}