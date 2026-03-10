import { ReactNode } from "react";

export function PageShell({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <main className="space-y-6">
      <section className="space-y-2">
        <h1 className="text-3xl font-bold text-white" data-testid="page-title">{title}</h1>
        <p className="max-w-3xl text-sm leading-6 text-slate-300">{description}</p>
      </section>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">{children}</section>
    </main>
  );
}
