"use client";

import { TaskBreakdownDocument } from "@/lib/types";

export function TaskBreakdownViewer({ document }: { document: TaskBreakdownDocument }) {
  const sections: Array<{ title: string; items: string[] }> = [
    { title: "集成风险", items: document.integration_risks },
    { title: "QA 策略", items: document.qa_strategy },
    { title: "发布检查清单", items: document.release_checklist },
  ];

  return (
    <div className="space-y-8" data-testid="task-breakdown-viewer">
      <section className="space-y-2">
        <h2 className="text-lg font-semibold text-white">交付目标</h2>
        <p className="text-sm leading-6 text-slate-300">{document.delivery_goal}</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold text-white">排期策略</h2>
        <p className="text-sm leading-6 text-slate-300">{document.sequencing_strategy}</p>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-white">模块任务拆解</h2>
        {document.modules.map((module) => (
          <div key={module.module_name} className="rounded-xl border border-slate-800 bg-slate-950/40 p-4" data-testid="task-breakdown-module">
            <div className="space-y-2">
              <h3 className="text-base font-semibold text-white">{module.module_name}</h3>
              <p className="text-sm text-slate-300">模块目标：{module.goal}</p>
              <p className="text-sm text-slate-400">用户价值：{module.user_value}</p>
            </div>
            <div className="mt-4 space-y-4">
              {module.tasks.map((task) => (
                <div key={task.title} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4" data-testid="task-breakdown-task">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-white">{task.title}</p>
                    <span className="text-xs text-sky-300">{task.owner_focus}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{task.description}</p>
                  <p className="mt-2 text-xs text-slate-400">依赖：{task.dependencies.length ? task.dependencies.join("、") : "无"}</p>
                  <div className="mt-3 grid gap-4 md:grid-cols-2">
                    <div>
                      <h4 className="text-sm font-medium text-white">验收标准</h4>
                      <ul className="mt-2 space-y-2 text-sm text-slate-300">
                        {task.acceptance_criteria.map((criterion) => (
                          <li key={criterion} className="list-inside list-disc">{criterion}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white">测试用例</h4>
                      <ul className="mt-2 space-y-2 text-sm text-slate-300">
                        {task.test_cases.map((testCase) => (
                          <li key={testCase} className="list-inside list-disc">{testCase}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      {sections.map((section) => (
        <section key={section.title} className="space-y-2">
          <h2 className="text-lg font-semibold text-white">{section.title}</h2>
          <ul className="space-y-2 text-sm leading-6 text-slate-300">
            {section.items.map((item) => (
              <li key={item} className="rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-3">{item}</li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
