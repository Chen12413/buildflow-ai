export type Platform = "web" | "mobile" | "both";
export type RunStatus = "pending" | "running" | "completed" | "failed";

export interface ApiEnvelope<T> {
  data: T;
  meta: Record<string, unknown> | null;
}

export interface Project {
  id: string;
  name: string;
  idea: string;
  target_user: string;
  platform: Platform;
  constraints: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClarificationQuestion {
  id: string;
  project_id: string;
  question: string;
  order_index: number;
  created_at: string;
}

export interface Run {
  id: string;
  project_id: string;
  type: string;
  status: RunStatus;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface PRDDocument {
  product_summary: string;
  problem_statement: string;
  target_users: string[];
  core_scenarios: string[];
  mvp_goal: string;
  in_scope: string[];
  out_of_scope: string[];
  user_stories: string[];
  success_metrics: string[];
  risks: string[];
}

export interface PlanningTask {
  title: string;
  description: string;
  owner_focus: string;
  acceptance_criteria: string[];
}

export interface PlanningMilestone {
  title: string;
  goal: string;
  tasks: PlanningTask[];
}

export interface PlanningDocument {
  objective: string;
  delivery_strategy: string;
  milestones: PlanningMilestone[];
  dependencies: string[];
  testing_focus: string[];
  rollout_notes: string[];
}

export interface PrdArtifact {
  id: string;
  project_id: string;
  run_id: string;
  type: "prd";
  version: number;
  content_json: PRDDocument;
  content_markdown: string;
  created_at: string;
}

export interface PlanningArtifact {
  id: string;
  project_id: string;
  run_id: string;
  type: "planning";
  version: number;
  content_json: PlanningDocument;
  content_markdown: string;
  created_at: string;
}
