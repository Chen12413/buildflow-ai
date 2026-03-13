import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "BuildFlow AI",
  description: "从产品想法到 PRD、开发规划、任务拆解与 Demo 的单主链路 Agent 工作台。",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="mx-auto min-h-screen max-w-6xl px-4 py-4 sm:px-6 lg:px-8">
          <header className="sticky top-4 z-20 mb-8 rounded-3xl border border-white/10 bg-slate-950/70 px-4 py-4 shadow-[0_20px_80px_-36px_rgba(15,23,42,0.85)] backdrop-blur-xl">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center gap-4">
                <Link href="/" className="flex items-center gap-3 text-white">
                  <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 via-cyan-300 to-indigo-400 text-lg font-black text-slate-950 shadow-[0_16px_34px_-18px_rgba(56,189,248,0.95)]">
                    B
                  </span>
                  <div>
                    <p className="text-base font-semibold text-white">BuildFlow AI</p>
                    <p className="text-xs text-slate-400">单主链路 Agent 产品工作台</p>
                  </div>
                </Link>

                <div className="hidden flex-wrap gap-2 xl:flex">
                  <span className="stage-pill border-sky-400/25 bg-sky-400/10 text-sky-200">Next.js + FastAPI</span>
                  <span className="stage-pill border-white/10 bg-white/5 text-slate-300">Mock / 百炼 Provider</span>
                  <span className="stage-pill border-white/10 bg-white/5 text-slate-300">可测试 · 可演示 · 可长期迭代</span>
                </div>
              </div>

              <nav className="flex flex-wrap items-center gap-3 text-sm">
                <Link href="/" className="ghost-btn px-4 py-2.5">
                  首页
                </Link>
                <Link href="/projects/new" className="primary-btn px-4 py-2.5">
                  创建项目
                </Link>
              </nav>
            </div>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}