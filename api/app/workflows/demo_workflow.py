from app.llm.provider import MockLLMProvider, get_llm_provider
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.schemas.artifact import ArtifactType
from app.schemas.demo import DemoBlueprintDocument
from app.schemas.planning import PlanningDocument
from app.schemas.prd import PRDDocument
from app.schemas.project import ProjectRead
from app.schemas.run import RunStatus
from app.schemas.task_breakdown import TaskBreakdownDocument


TRANSIENT_DEMO_ERROR_CODES = {
    "bailian_timeout",
    "bailian_request_failed",
    "bailian_responses_unavailable",
    "bailian_parse_failed",
    "bailian_rate_limited",
}


def render_demo_markdown(document: DemoBlueprintDocument) -> str:
    lines: list[str] = [
        "# BuildFlow AI Demo Blueprint",
        "",
        "## Demo 目标",
        document.demo_goal,
        "",
        "## Hero",
        f"- 标题：{document.hero_title}",
        f"- 副标题：{document.hero_subtitle}",
        f"- 目标用户：{document.target_persona}",
        f"- 主 CTA：{document.primary_cta}",
    ]
    if document.secondary_cta:
        lines.append(f"- 次 CTA：{document.secondary_cta}")
    lines.extend(["", "## 关键指标"])
    lines.extend(f"- {item}" for item in document.key_metrics)
    lines.extend(["", "## Multi-Agent 分工"])
    for agent in document.agent_cards:
        lines.extend(
            [
                f"- {agent.agent_name}",
                f"  - 负责：{agent.responsibility}",
                f"  - Prompt 关注点：{agent.prompt_focus}",
                f"  - 产出摘要：{agent.output_summary}",
            ]
        )
    lines.extend(["", "## Demo Screens"])
    for index, screen in enumerate(document.screens, start=1):
        lines.extend(
            [
                f"### {index}. {screen.name}",
                f"- 用途：{screen.purpose}",
                f"- 标题：{screen.headline}",
                f"- 描述：{screen.description}",
            ]
        )
        for highlight in screen.highlights:
            lines.append(f"- 亮点：{highlight}")
        for action in screen.actions:
            lines.append(f"- 操作：{action.label} -> {action.detail}")
        lines.append("")

    lines.append("## 演示流程")
    for step in document.flow_steps:
        lines.extend(
            [
                f"- {step.step_title}",
                f"  - 用户目标：{step.user_goal}",
                f"  - 系统反馈：{step.system_response}",
            ]
        )
    lines.extend(["", "## 演示话术"])
    lines.extend(f"- {item}" for item in document.demo_script)
    lines.append("")
    return "\n".join(lines).strip() + "\n"


class DemoWorkflow:
    def __init__(self, project_repository: ProjectRepository, clarification_repository: ClarificationRepository, artifact_repository: ArtifactRepository, run_repository: RunRepository) -> None:
        self.project_repository = project_repository
        self.clarification_repository = clarification_repository
        self.artifact_repository = artifact_repository
        self.run_repository = run_repository

    def run(self, run_id: str, project_id: str):
        project = self.project_repository.get_by_id(project_id)
        run = self.run_repository.get_by_id(run_id)
        if project is None:
            raise ValueError("project_not_found")
        if run is None:
            raise ValueError("run_not_found")

        try:
            self.run_repository.update_status(run, RunStatus.RUNNING)
            latest_prd = self.artifact_repository.get_latest(project_id, ArtifactType.PRD.value)
            if latest_prd is None:
                raise ValueError("prd_artifact_required")
            latest_planning = self.artifact_repository.get_latest(project_id, ArtifactType.PLANNING.value)
            if latest_planning is None:
                raise ValueError("planning_artifact_required")
            latest_task_breakdown = self.artifact_repository.get_latest(project_id, ArtifactType.TASK_BREAKDOWN.value)
            if latest_task_breakdown is None:
                raise ValueError("task_breakdown_artifact_required")

            project_read = ProjectRead.model_validate(project)
            prd_document = PRDDocument.model_validate(latest_prd.content_json)
            planning_document = PlanningDocument.model_validate(latest_planning.content_json)
            task_breakdown_document = TaskBreakdownDocument.model_validate(latest_task_breakdown.content_json)
            answers = [item.answer for item in self.clarification_repository.list_answers(project_id)]
            provider = get_llm_provider()

            try:
                document = provider.generate_demo_blueprint_document(
                    project_read,
                    prd_document,
                    planning_document,
                    task_breakdown_document,
                    answers,
                )
            except ValueError as exc:
                if str(exc) not in TRANSIENT_DEMO_ERROR_CODES:
                    raise
                document = self._build_fallback_demo_document(
                    project_read,
                    prd_document,
                    planning_document,
                    task_breakdown_document,
                    answers,
                )

            markdown = render_demo_markdown(document)
            artifact = self.artifact_repository.create(
                project_id=project_id,
                run_id=run_id,
                artifact_type=ArtifactType.DEMO.value,
                content_json=document.model_dump(),
                content_markdown=markdown,
            )
            self.run_repository.update_status(run, RunStatus.COMPLETED)
            return artifact
        except Exception as exc:
            self.run_repository.update_status(run, RunStatus.FAILED, str(exc))
            raise

    def _build_fallback_demo_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        task_breakdown_document: TaskBreakdownDocument,
        answers: list[str],
    ) -> DemoBlueprintDocument:
        document = MockLLMProvider().generate_demo_blueprint_document(
            project,
            prd_document,
            planning_document,
            task_breakdown_document,
            answers,
        )
        for agent_card in document.agent_cards:
            agent_card.model_used = "local-fallback"
        return document