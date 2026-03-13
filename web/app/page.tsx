import Link from "next/link";

const mainFlow = [
  {
    step: "01 · Create",
    title: "录入项目背景",
    description: "输入项目名、目标用户、平台和约束，建立统一上下文。",
  },
  {
    step: "02 · Clarify",
    title: "补齐关键问题",
    description: "自动追问边界、成功标准和 MVP 取舍，避免一开始就写歪。",
  },
  {
    step: "03 · PRD / Planning",
    title: "生成文档与规划",
    description: "连续产出 PRD、开发规划和测试重点，沉淀长期可维护文档。",
  },
  {
    step: "04 · Tasks / Demo",
    title: "拆任务并展示 Demo",
    description: "继续输出模块任务拆解、Agent 运行面板和可展示的产品 Demo。",
  },
];

const highlights = [
  "一条主链路串起 Idea → 澄清 → PRD → Planning → Task Breakdown → Demo。",
  "支持 Mock 与真实百炼 Provider，兼顾本地开发、在线演示和长期迭代。",
  "内置测试、CI、部署与作品集素材，更适合写进简历和个人主页。",
];

const portfolioValue = [
  "体现你对 AI 产品规划、技术协作和可维护交付的理解。",
  "能直观看到多 Agent 分工、Prompt 可视化和产物链路。",
  "适合面试时现场演示，从业务输入一路走到 Demo 成品。",
];

export default function HomePage() {
  return (
    <main className="space-y-8">
      <section className="hero-panel px-6 py-8 md:px-8 md:py-10">
        <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-300">
          <span className="stage-pill border-sky-400/30 bg-sky-400/10 text-sky-100">BuildFlow AI v0.2</span>
          <span className="stage-pill border-white/10 bg-white/5 text-slate-300">Next.js + FastAPI</span>
          <span className="stage-pill border-white/10 bg-white/5 text-slate-300">单主链路 Agent Workflow</span>
          <span className="stage-pill border-white/10 bg-white/5 text-slate-300">Mock / 百炼</span>
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px] lg:items-end">
          <div>
            <h1 className="max-w-4xl text-4xl font-bold leading-tight text-white md:text-5xl">
              把一个产品想法，稳定推进到 PRD、开发规划、任务拆解与可展示 Demo
            </h1>
            <p className="mt-5 max-w-3xl text-base leading-7 text-slate-300 md:text-lg">
              BuildFlow AI 面向 AI 产品经理、独立开发者和小团队，重点解决“功能能跑，但代码与文档难以长期维护”的问题，
              让你用更专业的方式做出一个能写进简历与作品集的项目。
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <Link href="/projects/new" className="primary-btn">
                开始创建项目
              </Link>
              <Link href="/projects/new" className="ghost-btn">
                体验完整主链路
              </Link>
            </div>
          </div>

          <div className="glass-card soft-grid p-6">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-500">为什么适合展示</p>
            <div className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
              <p>你不是只展示一个原型，而是在展示一套“从需求到交付”的 AI 工作流产品。</p>
              <p>这类项目更容易体现产品思维、交付能力、Prompt 工程意识和工程化意识。</p>
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-3 md:grid-cols-3">
          {highlights.map((item) => (
            <div key={item} className="glass-card p-4 text-sm leading-6 text-slate-300 transition hover:-translate-y-0.5 hover:border-sky-400/20">
              {item}
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {mainFlow.map((item) => (
          <div key={item.step} className="glass-card p-5 transition hover:-translate-y-1 hover:border-sky-400/20">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-200">{item.step}</p>
            <h2 className="mt-3 text-lg font-semibold text-white">{item.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">{item.description}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
        <div className="glass-card p-6">
          <p className="section-label">简历 / 作品集加分点</p>
          <div className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
            {portfolioValue.map((item) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-6">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">推荐使用方式</p>
          <div className="mt-4 space-y-4 text-sm leading-6 text-slate-300">
            <p>先用真实业务场景走通一遍，再导出 Markdown 和截图，整理成 GitHub README 与作品集页面。</p>
            <p>如果你正在准备 AI 产品经理面试，这个项目既能展示产品思考，也能展示你如何借助大模型提升研发效率。</p>
          </div>
          <Link href="/projects/new" className="primary-btn mt-6 w-full">
            现在开始
          </Link>
        </div>
      </section>
    </main>
  );
}