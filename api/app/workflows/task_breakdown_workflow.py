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
from app.schemas.task_breakdown import TaskBreakdownDocument


def render_task_breakdown_markdown(document: TaskBreakdownDocument) -> str:
    lines: list[str] = [
        "# BuildFlow AI Task Breakdown",
        "",
        "## 交付目标",
        document.delivery_goal,
        "",
        "## 排期策略",
        document.sequencing_strategy,
        "",
        "## 模块拆解",
        "",
    ]

    for index, module in enumerate(document.modules, start=1):
        lines.extend(
            [
                f"### {index}. {module.module_name}",
                f"- 模块目标：{module.goal}",
                f"- 用户价值：{module.user_value}",
                "",
            ]
        )
        for task in module.tasks:
            dependencies = "、".join(task.dependencies) if task.dependencies else "无"
            lines.extend(
                [
                    f"- {task.title}（{task.owner_focus}）",
                    f"  - 说明：{task.description}",
                    f"  - 依赖：{dependencies}",
                ]
            )
            for criterion in task.acceptance_criteria:
                lines.append(f"  - 验收：{criterion}")
            for test_case in task.test_cases:
                lines.append(f"  - 测试：{test_case}")
        lines.append("")

    for title, values in [
        ("集成风险", document.integration_risks),
        ("QA 策略", document.qa_strategy),
        ("发布检查清单", document.release_checklist),
    ]:
        lines.append(f"## {title}")
        lines.extend(f"- {item}" for item in values)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


class TaskBreakdownWorkflow:
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

            project_read = ProjectRead.model_validate(project)
            prd_document = PRDDocument.model_validate(latest_prd.content_json)
            planning_document = PlanningDocument.model_validate(latest_planning.content_json)
            answers = [item.answer for item in self.clarification_repository.list_answers(project_id)]
            provider = get_llm_provider()
            document = provider.generate_task_breakdown_document(project_read, prd_document, planning_document, answers)
            markdown = render_task_breakdown_markdown(document)
            artifact = self.artifact_repository.create(
                project_id=project_id,
                run_id=run_id,
                artifact_type=ArtifactType.TASK_BREAKDOWN.value,
                content_json=document.model_dump(),
                content_markdown=markdown,
            )
            self.run_repository.update_status(run, RunStatus.COMPLETED)
            return artifact
        except Exception as exc:
            self.run_repository.update_status(run, RunStatus.FAILED, str(exc))
            raise
