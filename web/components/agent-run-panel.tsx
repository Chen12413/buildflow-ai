"use client";

import { DemoAgentCard } from "@/lib/types";

function getStatusStyle(status: string) {
  const normalized = status.trim().toLowerCase();
  if (normalized === "completed") {
    return "border-emerald-400/30 bg-emerald-400/10 text-emerald-200";
  }
  if (normalized === "running") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  if (normalized === "failed") {
    return "border-rose-400/30 bg-rose-400/10 text-rose-100";
  }
  return "border-white/10 bg-white/5 text-slate-300";
}

export function AgentRunPanel({ agents, expandPrompts = false }: { agents: DemoAgentCard[]; expandPrompts?: boolean }) {
  const completedCount = agents.filter((agent) => (agent.status ?? "running").trim().toLowerCase() === "completed").length;

  return (
    <section className="glass-card p-6" data-testid="agent-run-panel">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="section-label">多 Agent 协作</p>
          <h2 className="mt-4 text-2xl font-semibold text-white">Agent 运行面板</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">
            查看每个 Agent 的职责、Prompt 关注点、依赖关系和输出摘要，方便你在演示时解释这套系统如何协同工作。
          </p>
        </div>

        <div className="flex flex-wrap gap-2 text-xs">
          <span className="stage-pill border-white/10 bg-white/5 text-slate-300">Agent 数量：{agents.length}</span>
          <span className="stage-pill border-emerald-400/30 bg-emerald-400/10 text-emerald-200">已完成：{completedCount}</span>
          <span className="stage-pill border-white/10 bg-white/5 text-slate-300">含 Prompt 可视化</span>
        </div>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        {agents.map((agent) => {
          const status = agent.status ?? "running";
          const dependsOn = agent.depends_on ?? [];
          const systemPrompt = agent.system_prompt_preview?.trim();
          const userPrompt = agent.user_prompt_preview?.trim();

          return (
            <div
              key={agent.agent_name}
              className="rounded-3xl border border-white/10 bg-white/5 p-5 transition hover:-translate-y-0.5 hover:border-sky-400/20"
              data-testid="demo-agent-card"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">{agent.agent_name}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{agent.responsibility}</p>
                </div>
                <span className={`stage-pill ${getStatusStyle(status)}`}>{status}</span>
              </div>

              <div className="mt-5 space-y-4 text-sm">
                <div>
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Prompt Focus</p>
                  <p className="mt-2 leading-6 text-slate-300">{agent.prompt_focus}</p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Output Summary</p>
                  <p className="mt-2 leading-6 text-sky-100">{agent.output_summary}</p>
                </div>

                <div className="flex flex-wrap gap-2 text-xs text-slate-300">
                  <span className="stage-pill border-white/10 bg-white/5 text-slate-300">模型：{agent.model_used ?? "未标注"}</span>
                  <span className="stage-pill border-white/10 bg-white/5 text-slate-300">依赖：{dependsOn.length ? dependsOn.join(" / ") : "无"}</span>
                </div>
              </div>

              <details open={expandPrompts} className="mt-5 rounded-2xl border border-white/10 bg-slate-950/60">
                <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-white marker:hidden">Prompt 可视化</summary>
                <div className="space-y-4 border-t border-white/10 px-4 py-4 text-sm">
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">System Prompt</p>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-2xl border border-white/10 bg-slate-950/80 p-3 text-xs leading-6 text-slate-300">
                      {systemPrompt ?? "当前未提供 system prompt 预览。"}
                    </pre>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">User Prompt</p>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-2xl border border-white/10 bg-slate-950/80 p-3 text-xs leading-6 text-slate-300">
                      {userPrompt ?? "当前未提供 user prompt 预览。"}
                    </pre>
                  </div>
                </div>
              </details>
            </div>
          );
        })}
      </div>
    </section>
  );
}