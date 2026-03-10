import { PlanningResult } from "@/components/planning-result";

export default async function PlanningRoute({
  params,
  searchParams,
}: {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ runId?: string }>;
}) {
  const { projectId } = await params;
  const { runId } = await searchParams;
  return <PlanningResult projectId={projectId} runId={runId} />;
}
