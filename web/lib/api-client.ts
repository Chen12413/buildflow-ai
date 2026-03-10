import { ApiEnvelope, ClarificationQuestion, PlanningArtifact, Project, PrdArtifact, Run } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: { message: "Request failed" } }));
    const message = error?.detail?.message ?? "Request failed";
    throw new Error(message);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("text/markdown")) {
    return (await response.text()) as T;
  }

  const payload = (await response.json()) as ApiEnvelope<T>;
  return payload.data;
}

export async function createProject(payload: {
  name: string;
  idea: string;
  target_user: string;
  platform: Project["platform"];
  constraints?: string;
}) {
  return request<Project>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getProject(projectId: string) {
  return request<Project>(`/api/v1/projects/${projectId}`);
}

export async function generateClarifications(projectId: string) {
  return request<{ run: Run; questions: ClarificationQuestion[] }>(`/api/v1/projects/${projectId}/clarifications/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function saveClarificationAnswers(projectId: string, answers: Array<{ question_id: string; answer: string }>) {
  return request<{ project_id: string; saved_count: number }>(`/api/v1/projects/${projectId}/clarifications/answers`, {
    method: "PUT",
    body: JSON.stringify({ answers }),
  });
}

export async function generatePrd(projectId: string) {
  return request<{ run: Run }>(`/api/v1/projects/${projectId}/prd/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function generatePlanning(projectId: string) {
  return request<{ run: Run }>(`/api/v1/projects/${projectId}/planning/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getRun(runId: string) {
  return request<Run>(`/api/v1/runs/${runId}`);
}

export async function getLatestPrd(projectId: string) {
  return request<PrdArtifact>(`/api/v1/projects/${projectId}/artifacts/prd/latest`);
}

export async function getLatestPlanning(projectId: string) {
  return request<PlanningArtifact>(`/api/v1/projects/${projectId}/artifacts/planning/latest`);
}

export async function exportMarkdown(projectId: string) {
  return request<string>(`/api/v1/projects/${projectId}/export/markdown`);
}

export async function exportPlanningMarkdown(projectId: string) {
  return request<string>(`/api/v1/projects/${projectId}/export/planning/markdown`);
}
