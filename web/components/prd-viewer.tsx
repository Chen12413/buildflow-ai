import { PRDDocument } from "@/lib/types";

const sections: Array<[keyof PRDDocument, string]> = [
  ["product_summary", "产品概述"],
  ["problem_statement", "问题陈述"],
  ["target_users", "目标用户"],
  ["core_scenarios", "核心场景"],
  ["mvp_goal", "MVP 目标"],
  ["in_scope", "功能范围"],
  ["out_of_scope", "非目标"],
  ["user_stories", "用户故事"],
  ["success_metrics", "成功指标"],
  ["risks", "风险"],
];

export function PrdViewer({ document }: { document: PRDDocument }) {
  return (
    <div className="space-y-6" data-testid="prd-viewer">
      {sections.map(([key, label]) => {
        const value = document[key];
        return (
          <section key={key} className="space-y-2" data-testid={`prd-section-${key}`}>
            <h2 className="text-lg font-semibold text-white">{label}</h2>
            {Array.isArray(value) ? (
              <ul className="space-y-2 text-sm leading-6 text-slate-300">
                {value.map((item) => (
                  <li key={item} className="rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-3">
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm leading-6 text-slate-300">{value}</p>
            )}
          </section>
        );
      })}
    </div>
  );
}
