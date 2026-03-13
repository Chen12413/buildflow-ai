"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { PageShell } from "@/components/page-shell";
import { ProgressBar } from "@/components/progress-bar";
import { StatusPanel } from "@/components/status-panel";
import { generateClarifications, getProject, generatePrd, saveClarificationAnswers } from "@/lib/api-client";
import { ClarificationQuestion, Project } from "@/lib/types";

function getAnsweredCount(questions: ClarificationQuestion[], answers: Record<string, string>) {
  return questions.filter((question) => (answers[question.id] ?? "").trim().length > 0).length;
}

export function ClarificationFlow({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [questions, setQuestions] = useState<ClarificationQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const projectData = await getProject(projectId);
        if (cancelled) {
          return;
        }

        setProject(projectData);
        const clarificationResult = await generateClarifications(projectId);
        if (cancelled) {
          return;
        }

        setQuestions(clarificationResult.questions);
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        setError(loadError instanceof Error ? loadError.message : "加载澄清问题失败");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
    };
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
          answer: answers[question.id] || "未填写答案",
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

  const answeredCount = useMemo(() => getAnsweredCount(questions, answers), [questions, answers]);
  const completionRatio = questions.length ? (answeredCount / questions.length) * 100 : 0;

  if (loading) {
    return (
      <PageShell
        stageKey="clarify"
        title="澄清问题"
        description="系统会根据你的项目信息生成高价值澄清问题，帮助收敛 MVP 范围。"
      >
        <StatusPanel
          phaseLabel="澄清问题"
          title="正在准备问题"
          status="正在生成澄清问题..."
          artifactReady={false}
          progress={36}
          helper="通常只需十几秒；若后端冷启动或模型较慢，会自动继续等待。"
          testId="clarification-loading"
        />
      </PageShell>
    );
  }

  return (
    <PageShell
      stageKey="clarify"
      title={`澄清问题${project ? ` · ${project.name}` : ""}`}
      description="回答这些关键问题后，系统会基于更完整的边界信息自动生成 PRD。"
    >
      <div className="space-y-6">
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
          <div className="glass-card p-5">
            <p className="section-label">回答建议</p>
            <h2 className="mt-4 text-xl font-semibold text-white">尽量短、具体、可执行</h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              优先写清目标用户、核心场景、成功标准和明显约束。如果暂时不确定，也可以先写一个当前判断。
            </p>
          </div>

          <div className="glass-card p-5">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-500">进度概览</p>
            <div className="mt-4 space-y-4 text-sm text-slate-300">
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-slate-400">问题数量</p>
                <p className="mt-1 text-2xl font-semibold text-white">{questions.length}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-slate-400">已填写</p>
                <p className="mt-1 text-2xl font-semibold text-white">
                  {answeredCount} / {questions.length}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <ProgressBar
                  value={Math.max(12, completionRatio)}
                  label="回答完成度"
                  helper="保存后会自动进入 PRD 生成阶段。"
                />
              </div>
            </div>
          </div>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit} data-testid="clarification-form">
          <div className="space-y-4">
            {questions.map((question) => (
              <section
                key={question.id}
                className="glass-card p-5 transition hover:-translate-y-0.5 hover:border-sky-400/20"
                data-testid="clarification-question"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <span className="section-label">问题 {question.order_index}</span>
                    <p className="mt-3 text-base font-semibold leading-7 text-white">{question.question}</p>
                  </div>
                  <span className="stage-pill border-white/10 bg-white/5 text-slate-300">建议 1-3 句</span>
                </div>

                <textarea
                  rows={5}
                  value={answers[question.id] ?? ""}
                  onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                  className="textarea-field mt-4"
                  placeholder="尽量写清目标用户、业务边界、数据来源和成功标准。"
                  data-testid="clarification-answer"
                />
              </section>
            ))}
          </div>

          {error ? (
            <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">{error}</div>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
              页面会在下一步自动刷新生成结果，无需手动刷新。
            </div>
          )}

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-400">当前主链路：澄清问题 → PRD。回答越具体，后续 PRD 越稳定。</p>
            <button type="submit" disabled={submitting} data-testid="clarification-submit" className="primary-btn">
              {submitting ? "正在提交并启动 PRD..." : "保存回答并生成 PRD"}
            </button>
          </div>
        </form>
      </div>
    </PageShell>
  );
}