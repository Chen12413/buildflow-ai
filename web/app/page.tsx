import Link from "next/link";

export default function HomePage() {
  return (
    <main className="space-y-8">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8">
        <p className="mb-3 text-sm uppercase tracking-[0.3em] text-sky-300">BuildFlow AI v0.1</p>
        <h1 className="mb-4 text-4xl font-bold text-white">用一条主链路，把产品想法变成结构化 PRD</h1>
        <p className="max-w-3xl text-base leading-7 text-slate-300">
          当前版本只做一件事：Idea Input → Clarification → PRD Generation → Review & Export。
          目标是在 10 分钟内，把模糊想法沉淀成可导出的 Markdown PRD。
        </p>
        <div className="mt-8 flex gap-4">
          <Link href="/projects/new" className="rounded-lg bg-sky-500 px-5 py-3 font-medium text-slate-950 hover:bg-sky-400">
            开始创建项目
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {[
          ["1. 输入想法", "填写项目名称、目标用户、平台和约束。"],
          ["2. 回答澄清", "系统生成高价值问题，帮助你补齐信息。"],
          ["3. 导出 PRD", "查看结构化 PRD，并导出 Markdown。"],
        ].map(([title, description]) => (
          <div key={title} className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <h2 className="mb-2 text-lg font-semibold text-white">{title}</h2>
            <p className="text-sm leading-6 text-slate-300">{description}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
