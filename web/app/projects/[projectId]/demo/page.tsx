import { DemoResult } from "@/components/demo-result";

export default async function DemoRoute({
  params,
  searchParams,
}: {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ runId?: string }>;
}) {
  const { projectId } = await params;
  const { runId } = await searchParams;
  return <DemoResult projectId={projectId} runId={runId} />;
}
