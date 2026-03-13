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

export interface TaskBreakdownTask {
  title: string;
  description: string;
  owner_focus: string;
  dependencies: string[];
  acceptance_criteria: string[];
  test_cases: string[];
}

export interface TaskBreakdownModule {
  module_name: string;
  goal: string;
  user_value: string;
  tasks: TaskBreakdownTask[];
}

export interface TaskBreakdownDocument {
  delivery_goal: string;
  sequencing_strategy: string;
  modules: TaskBreakdownModule[];
  integration_risks: string[];
  qa_strategy: string[];
  release_checklist: string[];
}

export interface DemoScreenAction {
  label: string;
  detail: string;
  result_preview?: string | null;
}

export interface DemoScreen {
  name: string;
  purpose: string;
  headline: string;
  description: string;
  highlights: string[];
  actions: DemoScreenAction[];
  sample_inputs?: string[];
  sample_outputs?: string[];
  success_signal?: string | null;
}

export interface DemoFlowStep {
  step_title: string;
  user_goal: string;
  system_response: string;
}

export interface DemoAgentCard {
  agent_name: string;
  responsibility: string;
  prompt_focus: string;
  output_summary: string;
  status?: string;
  depends_on?: string[];
  system_prompt_preview?: string | null;
  user_prompt_preview?: string | null;
  model_used?: string | null;
}

export interface DemoBlueprintDocument {
  product_name: string;
  demo_goal: string;
  hero_title: string;
  hero_subtitle: string;
  target_persona: string;
  primary_cta: string;
  secondary_cta: string | null;
  key_metrics: string[];
  screens: DemoScreen[];
  flow_steps: DemoFlowStep[];
  agent_cards: DemoAgentCard[];
  demo_script: string[];
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

export interface TaskBreakdownArtifact {
  id: string;
  project_id: string;
  run_id: string;
  type: "task_breakdown";
  version: number;
  content_json: TaskBreakdownDocument;
  content_markdown: string;
  created_at: string;
}

export interface DemoArtifact {
  id: string;
  project_id: string;
  run_id: string;
  type: "demo";
  version: number;
  content_json: DemoBlueprintDocument;
  content_markdown: string;
  created_at: string;
}
