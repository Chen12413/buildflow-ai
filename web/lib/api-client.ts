import {
  ApiEnvelope,
  ClarificationQuestion,
  DemoArtifact,
  PlanningArtifact,
  Project,
  PrdArtifact,
  Run,
  TaskBreakdownArtifact,
} from "@/lib/types";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").trim().replace(/\/+$/, "");

function getFallbackErrorMessage(status: number): string {
  if ([502, 503, 504].includes(status)) {
    return `后端服务正在启动或短暂不可用，请等待 30-60 秒后重试（HTTP ${status}）。`;
  }

  if (status >= 500) {
    return `服务端发生异常，请稍后重试（HTTP ${status}）。`;
  }

  if (status >= 400) {
    return `请求失败（HTTP ${status}）。`;
  }

  return "Request failed";
}

async function getErrorMessage(response: Response): Promise<string> {
  const fallbackMessage = getFallbackErrorMessage(response.status);
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    const error = (await response.json().catch(() => null)) as { detail?: { message?: string } } | null;
    return error?.detail?.message?.trim() || fallbackMessage;
  }

  const text = (await response.text().catch(() => "")).trim();
  return text || fallbackMessage;
}

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
    const message = await getErrorMessage(response);
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

export async function generateTaskBreakdown(projectId: string) {
  return request<{ run: Run }>(`/api/v1/projects/${projectId}/task-breakdown/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function generateDemo(projectId: string) {
  return request<{ run: Run }>(`/api/v1/projects/${projectId}/demo/generate`, {
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

export async function getLatestTaskBreakdown(projectId: string) {
  return request<TaskBreakdownArtifact>(`/api/v1/projects/${projectId}/artifacts/task-breakdown/latest`);
}

export async function getLatestDemo(projectId: string) {
  return request<DemoArtifact>(`/api/v1/projects/${projectId}/artifacts/demo/latest`);
}

export async function exportMarkdown(projectId: string) {
  return request<string>(`/api/v1/projects/${projectId}/export/markdown`);
}

export async function exportPlanningMarkdown(projectId: string) {
  return request<string>(`/api/v1/projects/${projectId}/export/planning/markdown`);
}

export async function exportTaskBreakdownMarkdown(projectId: string) {
  return request<string>(`/api/v1/projects/${projectId}/export/task-breakdown/markdown`);
}

export async function exportDemoMarkdown(projectId: string) {
  return request<string>(`/api/v1/projects/${projectId}/export/demo/markdown`);
}
