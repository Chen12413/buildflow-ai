import { PrdResult } from "@/components/prd-result";

export default async function PrdRoute({
  params,
  searchParams,
}: {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ runId?: string }>;
}) {
  const { projectId } = await params;
  const { runId } = await searchParams;
  return <PrdResult projectId={projectId} runId={runId} />;
}
