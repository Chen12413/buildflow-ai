from app.llm.provider import get_llm_provider
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.schemas.artifact import ArtifactType
from app.schemas.planning import PlanningDocument
from app.schemas.prd import PRDDocument
from app.schemas.project import ProjectRead
from app.schemas.run import RunStatus


def render_planning_markdown(document: PlanningDocument) -> str:
    lines: list[str] = ["# BuildFlow AI Planning", "", "## 目标", document.objective, "", "## 交付策略", document.delivery_strategy, ""]
    lines.extend(["## 里程碑", ""])
    for index, milestone in enumerate(document.milestones, start=1):
        lines.append(f"### {index}. {milestone.title}")
        lines.append(milestone.goal)
        lines.append("")
        for task in milestone.tasks:
            lines.append(f"- {task.title}（{task.owner_focus}）")
            lines.append(f"  - 说明：{task.description}")
            for criterion in task.acceptance_criteria:
                lines.append(f"  - 验收：{criterion}")
        lines.append("")

    for title, values in [("依赖项", document.dependencies), ("测试重点", document.testing_focus), ("发布说明", document.rollout_notes)]:
        lines.append(f"## {title}")
        lines.extend(f"- {item}" for item in values)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


class PlanningWorkflow:
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

            project_read = ProjectRead.model_validate(project)
            prd_document = PRDDocument.model_validate(latest_prd.content_json)
            answers = [item.answer for item in self.clarification_repository.list_answers(project_id)]
            provider = get_llm_provider()
            document = provider.generate_planning_document(project_read, prd_document, answers)
            markdown = render_planning_markdown(document)
            artifact = self.artifact_repository.create(
                project_id=project_id,
                run_id=run_id,
                artifact_type=ArtifactType.PLANNING.value,
                content_json=document.model_dump(),
                content_markdown=markdown,
            )
            self.run_repository.update_status(run, RunStatus.COMPLETED)
            return artifact
        except Exception as exc:
            self.run_repository.update_status(run, RunStatus.FAILED, str(exc))
            raise