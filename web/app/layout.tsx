import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "BuildFlow AI",
  description: "Idea to PRD in one focused workflow.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="mx-auto min-h-screen max-w-5xl px-6 py-8">
          <header className="mb-10 flex items-center justify-between border-b border-slate-800 pb-4">
            <Link href="/" className="text-xl font-semibold text-white">
              BuildFlow AI
            </Link>
            <nav className="flex gap-4 text-sm text-slate-300">
              <Link href="/projects/new">创建项目</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
