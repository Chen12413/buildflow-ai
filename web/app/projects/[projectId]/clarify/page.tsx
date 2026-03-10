import { ClarificationFlow } from "@/components/clarification-flow";

export default async function ClarifyRoute({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <ClarificationFlow projectId={projectId} />;
}
