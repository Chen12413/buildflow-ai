from app.llm.provider import get_llm_provider
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.schemas.artifact import ArtifactType
from app.schemas.prd import PRDDocument
from app.schemas.project import ProjectRead
from app.schemas.run import RunStatus


def render_prd_markdown(document: PRDDocument) -> str:
    sections = [
        ("产品概述", document.product_summary),
        ("问题陈述", document.problem_statement),
        ("目标用户", document.target_users),
        ("核心场景", document.core_scenarios),
        ("MVP 目标", document.mvp_goal),
        ("功能范围", document.in_scope),
        ("非目标", document.out_of_scope),
        ("用户故事", document.user_stories),
        ("成功指标", document.success_metrics),
        ("风险", document.risks),
    ]
    lines: list[str] = ["# BuildFlow AI PRD", ""]
    for title, value in sections:
        lines.append(f"## {title}")
        if isinstance(value, list):
            lines.extend(f"- {item}" for item in value)
        else:
            lines.append(value)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


class PRDWorkflow:
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
            project_read = ProjectRead.model_validate(project)
            answers = [item.answer for item in self.clarification_repository.list_answers(project_id)]
            provider = get_llm_provider()
            document = provider.generate_prd_document(project_read, answers)
            markdown = render_prd_markdown(document)
            artifact = self.artifact_repository.create(
                project_id=project_id,
                run_id=run_id,
                artifact_type=ArtifactType.PRD.value,
                content_json=document.model_dump(),
                content_markdown=markdown,
            )
            self.run_repository.update_status(run, RunStatus.COMPLETED)
            return artifact
        except Exception as exc:
            self.run_repository.update_status(run, RunStatus.FAILED, str(exc))
            raise