"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { PageShell } from "@/components/page-shell";
import { generateClarifications, getProject, generatePrd, saveClarificationAnswers } from "@/lib/api-client";
import { ClarificationQuestion, Project } from "@/lib/types";

export function ClarificationFlow({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [questions, setQuestions] = useState<ClarificationQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function bootstrap() {
      try {
        const projectData = await getProject(projectId);
        setProject(projectData);
        const clarificationResult = await generateClarifications(projectId);
        setQuestions(clarificationResult.questions);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "加载澄清问题失败");
      } finally {
        setLoading(false);
      }
    }

    void bootstrap();
  }, [projectId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await saveClarificationAnswers(
        projectId,
        questions.map((question) => ({
          question_id: question.id,
          answer: answers[question.id] || "暂时没有补充。",
        })),
      );
      const result = await generatePrd(projectId);
      router.push(`/projects/${projectId}/prd?runId=${result.run.id}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "提交澄清答案失败");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <PageShell title="澄清问答" description="正在生成高价值澄清问题。">
        <p className="text-sm text-slate-300" data-testid="clarification-loading">
          加载中...
        </p>
      </PageShell>
    );
  }

  return (
    <PageShell
      title={`澄清问答${project ? ` · ${project.name}` : ""}`}
      description="BuildFlow AI 会围绕目标用户、核心场景、MVP 边界和成功标准引导你补齐信息。"
    >
      <form className="space-y-6" onSubmit={handleSubmit} data-testid="clarification-form">
        {questions.map((question) => (
          <label key={question.id} className="grid gap-2 text-sm text-slate-300" data-testid="clarification-question">
            <span className="font-medium text-white">Q{question.order_index}. {question.question}</span>
            <textarea
              rows={4}
              value={answers[question.id] ?? ""}
              onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
              className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
              placeholder="填写回答，或者保留为空让系统生成初版。"
              data-testid="clarification-answer"
            />
          </label>
        ))}

        {error ? <p className="text-sm text-rose-300">{error}</p> : null}

        <button
          type="submit"
          disabled={submitting}
          data-testid="clarification-submit"
          className="rounded-lg bg-sky-500 px-5 py-3 font-medium text-slate-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-300"
        >
          {submitting ? "提交中..." : "保存答案并生成 PRD"}
        </button>
      </form>
    </PageShell>
  );
}
