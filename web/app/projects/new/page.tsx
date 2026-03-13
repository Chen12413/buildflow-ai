"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { PageShell } from "@/components/page-shell";
import { createProject } from "@/lib/api-client";
import { normalizeProjectName } from "@/lib/project-name";
import { Platform } from "@/lib/types";

const outcomeItems = [
  "自动生成高价值澄清问题，帮助收敛 MVP 范围。",
  "输出结构化 PRD 与开发规划，支持导出 Markdown。",
  "继续拆到模块任务、验收标准、测试点和用户产品 Demo。",
];

export default function NewProjectPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData(event.currentTarget);
    const payload = {
      name: normalizeProjectName(String(formData.get("name") ?? "")),
      idea: String(formData.get("idea") ?? ""),
      target_user: String(formData.get("target_user") ?? ""),
      platform: String(formData.get("platform") ?? "web") as Platform,
      constraints: String(formData.get("constraints") ?? ""),
    };

    try {
      const project = await createProject(payload);
      router.push(`/projects/${project.id}/clarify`);
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "创建项目失败，请稍后重试。"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell stageKey="create" title="创建项目" description="只输入最少必要信息，快速把你的想法推进到产品实现主链路。">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <form className="space-y-5" onSubmit={handleSubmit} data-testid="project-form">
          <div className="grid gap-5 md:grid-cols-2">
            <label className="grid gap-2 text-sm text-slate-300 md:col-span-2">
              项目名称
              <input
                name="name"
                required
                placeholder="例如：AI 旅游规划助手"
                data-testid="project-name"
                className="input-field"
              />
            </label>

            <label className="grid gap-2 text-sm text-slate-300 md:col-span-2">
              一句话产品想法
              <textarea
                name="idea"
                required
                rows={5}
                placeholder="例如：帮助自由行用户根据预算、天数和偏好，快速生成可执行的旅行行程。"
                data-testid="project-idea"
                className="textarea-field"
              />
            </label>

            <label className="grid gap-2 text-sm text-slate-300">
              目标用户
              <input
                name="target_user"
                required
                placeholder="例如：自由行用户、情侣出游用户、周末短途旅行者"
                data-testid="project-target-user"
                className="input-field"
              />
            </label>

            <label className="grid gap-2 text-sm text-slate-300">
              平台
              <select name="platform" defaultValue="web" data-testid="project-platform" className="select-field">
                <option value="web">Web</option>
                <option value="mobile">Mobile</option>
                <option value="both">Both</option>
              </select>
            </label>

            <label className="grid gap-2 text-sm text-slate-300 md:col-span-2">
              约束条件（可选）
              <textarea
                name="constraints"
                rows={4}
                placeholder="例如：一天内做出 MVP；优先覆盖行程生成、预算控制和每日路线展示。"
                data-testid="project-constraints"
                className="textarea-field"
              />
            </label>
          </div>

          {error ? (
            <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">{error}</div>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
              提交后会立即进入“澄清问题”阶段，帮助你先收敛范围，再开始把想法推进成可实现产品。
            </div>
          )}

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-400">建议先写清目标用户、核心场景与成功标准，后续产出会更像真实产品。</p>
            <button type="submit" disabled={loading} data-testid="project-submit" className="primary-btn">
              {loading ? "创建中..." : "创建项目并进入澄清"}
            </button>
          </div>
        </form>

        <aside className="glass-card soft-grid p-6">
          <p className="section-label">你将获得</p>
          <div className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
            {outcomeItems.map((item) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                {item}
              </div>
            ))}
          </div>

          <div className="mt-6 rounded-2xl border border-sky-400/20 bg-sky-400/8 p-4 text-sm leading-6 text-sky-100">
            小提示：输入越具体，后续的 PRD、开发规划和 Demo 越像一个真的可交付项目。
          </div>
        </aside>
      </div>
    </PageShell>
  );
}
