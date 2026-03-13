"use client";

import { useEffect, useMemo, useState } from "react";

import { AgentRunPanel } from "@/components/agent-run-panel";
import { DemoBlueprintDocument } from "@/lib/types";

function getLinkedScreenIndex(currentIndex: number, screenCount: number) {
  if (screenCount <= 0) {
    return 0;
  }

  return currentIndex % screenCount;
}

export function DemoViewer({ document }: { document: DemoBlueprintDocument }) {
  const [activeScreenIndex, setActiveScreenIndex] = useState(0);
  const [activeActionIndex, setActiveActionIndex] = useState(0);
  const [expandPrompts, setExpandPrompts] = useState(false);

  const activeScreen = document.screens[activeScreenIndex] ?? document.screens[0] ?? null;

  useEffect(() => {
    setActiveActionIndex(0);
  }, [activeScreenIndex]);

  const activeAction = useMemo(() => {
    if (!activeScreen) {
      return null;
    }

    return activeScreen.actions[activeActionIndex] ?? activeScreen.actions[0] ?? null;
  }, [activeActionIndex, activeScreen]);

  const sampleInputs = activeScreen?.sample_inputs ?? [];
  const sampleOutputs = activeScreen?.sample_outputs ?? [];
  const successSignal = activeScreen?.success_signal ?? "当前未提供成功信号。";
  const actionFeedback = activeAction?.result_preview ?? activeAction?.detail ?? "点击一个动作后，这里会显示模拟结果。";

  return (
    <div className="space-y-8" data-testid="demo-viewer">
      <section className="hero-panel px-6 py-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="section-label">产品 Demo Studio</span>
          <span className="stage-pill border-white/10 bg-white/5 text-slate-300">{document.product_name}</span>
        </div>

        <div className="mt-6 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div className="space-y-3">
            <h2 className="text-2xl font-semibold text-white">{document.hero_title}</h2>
            <p className="max-w-3xl text-sm leading-6 text-slate-300">{document.hero_subtitle}</p>
            <div className="flex flex-wrap gap-2 text-xs text-slate-300">
              <span className="stage-pill border-white/10 bg-white/5 text-slate-300">目标用户：{document.target_persona}</span>
              <span className="stage-pill border-white/10 bg-white/5 text-slate-300">当前屏幕：{activeScreen?.name ?? "未就绪"}</span>
              <span className="stage-pill border-white/10 bg-white/5 text-slate-300">Agent 数量：{document.agent_cards.length}</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => {
                setActiveScreenIndex(0);
                setActiveActionIndex(0);
              }}
              className="primary-btn"
            >
              {document.primary_cta}
            </button>
            {document.secondary_cta ? (
              <button type="button" onClick={() => setExpandPrompts((current) => !current)} className="ghost-btn">
                {document.secondary_cta}
              </button>
            ) : null}
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {document.key_metrics.map((metric) => (
            <div key={metric} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm leading-6 text-slate-300">
              {metric}
            </div>
          ))}
        </div>
      </section>

      <section className="glass-card p-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">演示流程</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">点击任一步骤，左侧屏幕与中间交互区会同步切换，方便你现场演示完整链路。</p>
          </div>
          <span className="stage-pill border-white/10 bg-white/5 text-slate-300">流程步骤：{document.flow_steps.length}</span>
        </div>

        <div className="mt-5 grid gap-3 lg:grid-cols-4">
          {document.flow_steps.map((step, index) => {
            const linkedScreenIndex = getLinkedScreenIndex(index, document.screens.length);
            const isActive = linkedScreenIndex === activeScreenIndex;

            return (
              <button
                key={`${step.step_title}-${index}`}
                type="button"
                onClick={() => setActiveScreenIndex(linkedScreenIndex)}
                className={`rounded-2xl border px-4 py-4 text-left transition ${
                  isActive ? "border-sky-400/40 bg-sky-400/10" : "border-white/10 bg-white/5 hover:border-sky-400/20"
                }`}
              >
                <p className="text-sm font-semibold text-white">{step.step_title}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">用户目标</p>
                <p className="mt-1 text-sm leading-6 text-slate-300">{step.user_goal}</p>
                <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">系统响应</p>
                <p className="mt-1 text-sm leading-6 text-slate-300">{step.system_response}</p>
              </button>
            );
          })}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)_320px]">
        <aside className="glass-card p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-white">屏幕导航</h2>
              <p className="mt-2 text-sm leading-6 text-slate-300">选择当前要展示的核心界面。</p>
            </div>
            <span className="stage-pill border-white/10 bg-white/5 text-slate-300">{document.screens.length} 屏</span>
          </div>

          <div className="mt-5 space-y-3">
            {document.screens.map((screen, index) => {
              const isActive = index === activeScreenIndex;
              return (
                <button
                  key={screen.name}
                  type="button"
                  onClick={() => setActiveScreenIndex(index)}
                  data-testid="demo-screen"
                  className={`block w-full rounded-2xl border px-4 py-4 text-left transition ${
                    isActive ? "border-sky-400/40 bg-sky-400/10" : "border-white/10 bg-white/5 hover:border-sky-400/20"
                  }`}
                >
                  <p className="text-sm font-semibold text-white">{screen.name}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{screen.purpose}</p>
                </button>
              );
            })}
          </div>
        </aside>

        <div className="glass-card p-6">
          {activeScreen ? (
            <>
              <span className="section-label">{activeScreen.name}</span>
              <h3 className="mt-4 text-2xl font-semibold text-white">{activeScreen.headline}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-300">{activeScreen.description}</p>

              <div className="mt-6 grid gap-5 lg:grid-cols-2">
                <div>
                  <h4 className="text-sm font-semibold text-white">亮点</h4>
                  <ul className="mt-3 space-y-2 text-sm text-slate-300">
                    {activeScreen.highlights.map((highlight) => (
                      <li key={highlight} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 leading-6">
                        {highlight}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <div className="flex items-center justify-between gap-3">
                    <h4 className="text-sm font-semibold text-white">可点击动作</h4>
                    <span className="text-xs text-slate-500">点击后会更新右侧结果台</span>
                  </div>
                  <div className="mt-3 space-y-2">
                    {activeScreen.actions.map((action, index) => {
                      const isActive = index === activeActionIndex;
                      return (
                        <button
                          key={`${activeScreen.name}-${action.label}`}
                          type="button"
                          onClick={() => {
                            setActiveActionIndex(index);
                            if (action.result_preview) {
                              setExpandPrompts(true);
                            }
                          }}
                          className={`block w-full rounded-2xl border px-4 py-3 text-left transition ${
                            isActive ? "border-sky-400/40 bg-sky-400/10" : "border-white/10 bg-white/5 hover:border-sky-400/20"
                          }`}
                        >
                          <p className="font-medium text-white">{action.label}</p>
                          <p className="mt-1 text-sm leading-6 text-slate-300">{action.detail}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-sm leading-6 text-slate-300">当前没有可展示的屏幕内容。</div>
          )}
        </div>

        <aside className="glass-card p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Result Console</p>
            <h3 className="mt-3 text-lg font-semibold text-white">{activeAction?.label ?? "请选择一个动作"}</h3>
            <p className="mt-3 text-sm leading-6 text-slate-300">{actionFeedback}</p>
          </div>

          <div className="mt-6 space-y-5 text-sm">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Sample Inputs</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {sampleInputs.length ? (
                  sampleInputs.map((item) => (
                    <span key={item} className="stage-pill border-white/10 bg-white/5 text-slate-300">
                      {item}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-500">暂无示例输入</span>
                )}
              </div>
            </div>

            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Sample Outputs</p>
              <div className="mt-3 space-y-2">
                {sampleOutputs.length ? (
                  sampleOutputs.map((item) => (
                    <div key={item} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 leading-6 text-slate-300">
                      {item}
                    </div>
                  ))
                ) : (
                  <span className="text-slate-500">暂无示例输出</span>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4">
              <p className="text-xs uppercase tracking-[0.22em] text-emerald-200">Success Signal</p>
              <p className="mt-2 leading-6 text-slate-100">{successSignal}</p>
            </div>
          </div>
        </aside>
      </section>

      <AgentRunPanel agents={document.agent_cards} expandPrompts={expandPrompts} />

      <section className="glass-card p-6">
        <h2 className="text-xl font-semibold text-white">演示话术</h2>
        <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-300">
          {document.demo_script.map((item) => (
            <li key={item} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              {item}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}