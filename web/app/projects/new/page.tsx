"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { PageShell } from "@/components/page-shell";
import { createProject } from "@/lib/api-client";
import { Platform } from "@/lib/types";

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
      name: String(formData.get("name") ?? ""),
      idea: String(formData.get("idea") ?? ""),
      target_user: String(formData.get("target_user") ?? ""),
      platform: String(formData.get("platform") ?? "web") as Platform,
      constraints: String(formData.get("constraints") ?? ""),
    };

    try {
      const project = await createProject(payload);
      router.push(`/projects/${project.id}/clarify`);
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "创建项目失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell title="创建项目" description="输入最少必要信息，启动 BuildFlow AI 的唯一主链路。">
      <form className="grid gap-5" onSubmit={handleSubmit} data-testid="project-form">
        <label className="grid gap-2 text-sm text-slate-300">
          项目名称
          <input
            name="name"
            required
            data-testid="project-name"
            className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none ring-0"
          />
        </label>

        <label className="grid gap-2 text-sm text-slate-300">
          一句话产品想法
          <textarea
            name="idea"
            required
            rows={4}
            data-testid="project-idea"
            className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
          />
        </label>

        <label className="grid gap-2 text-sm text-slate-300">
          目标用户
          <input
            name="target_user"
            required
            data-testid="project-target-user"
            className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
          />
        </label>

        <label className="grid gap-2 text-sm text-slate-300">
          平台
          <select
            name="platform"
            defaultValue="web"
            data-testid="project-platform"
            className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
          >
            <option value="web">Web</option>
            <option value="mobile">Mobile</option>
            <option value="both">Both</option>
          </select>
        </label>

        <label className="grid gap-2 text-sm text-slate-300">
          约束条件（可选）
          <textarea
            name="constraints"
            rows={3}
            data-testid="project-constraints"
            className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
          />
        </label>

        {error ? <p className="text-sm text-rose-300">{error}</p> : null}

        <button
          type="submit"
          disabled={loading}
          data-testid="project-submit"
          className="rounded-lg bg-sky-500 px-5 py-3 font-medium text-slate-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-300"
        >
          {loading ? "创建中..." : "创建项目并进入澄清"}
        </button>
      </form>
    </PageShell>
  );
}
