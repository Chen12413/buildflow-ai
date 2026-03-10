import { PlanningDocument } from "@/lib/types";

export function PlanningViewer({ document }: { document: PlanningDocument }) {
  const sections: Array<{ title: string; items: string[] }> = [
    { title: "依赖项", items: document.dependencies },
    { title: "测试重点", items: document.testing_focus },
    { title: "发布说明", items: document.rollout_notes },
  ];

  return (
    <div className="space-y-8" data-testid="planning-viewer">
      <section className="space-y-2" data-testid="planning-objective">
        <h2 className="text-lg font-semibold text-white">目标</h2>
        <p className="text-sm leading-6 text-slate-300">{document.objective}</p>
      </section>

      <section className="space-y-2" data-testid="planning-delivery-strategy">
        <h2 className="text-lg font-semibold text-white">交付策略</h2>
        <p className="text-sm leading-6 text-slate-300">{document.delivery_strategy}</p>
      </section>

      <section className="space-y-4" data-testid="planning-milestones">
        <h2 className="text-lg font-semibold text-white">里程碑</h2>
        {document.milestones.map((milestone) => (
          <div key={milestone.title} className="rounded-xl border border-slate-800 bg-slate-950/40 p-4" data-testid="planning-milestone">
            <h3 className="text-base font-semibold text-white">{milestone.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">{milestone.goal}</p>
            <div className="mt-4 space-y-3">
              {milestone.tasks.map((task) => (
                <div key={task.title} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4" data-testid="planning-task">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-white">{task.title}</p>
                    <span className="text-xs text-sky-300">{task.owner_focus}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{task.description}</p>
                  <ul className="mt-3 space-y-2 text-sm text-slate-300">
                    {task.acceptance_criteria.map((criterion) => (
                      <li key={criterion} className="list-inside list-disc">
                        {criterion}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      {sections.map((section) => (
        <section key={section.title} className="space-y-2" data-testid={`planning-section-${section.title}`}>
          <h2 className="text-lg font-semibold text-white">{section.title}</h2>
          <ul className="space-y-2 text-sm leading-6 text-slate-300">
            {section.items.map((item) => (
              <li key={item} className="rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-3">
                {item}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
