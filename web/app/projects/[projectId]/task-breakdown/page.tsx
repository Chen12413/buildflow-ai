import { TaskBreakdownResult } from "@/components/task-breakdown-result";

export default async function TaskBreakdownRoute({
  params,
  searchParams,
}: {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ runId?: string }>;
}) {
  const { projectId } = await params;
  const { runId } = await searchParams;
  return <TaskBreakdownResult projectId={projectId} runId={runId} />;
}
